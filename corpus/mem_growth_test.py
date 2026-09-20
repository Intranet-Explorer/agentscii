#!/usr/bin/env python3
"""corpus/mem_growth_test.py -- task 5 investigation: directly measure
MLX's cache memory (mx.get_cache_memory()) alongside active memory
(mx.get_active_memory()) and RSS/swap every iteration, for real
training steps, to test whether mx's internal buffer cache grows
unbounded across iterations (distinct from the already-logged
mx.get_peak_memory(), which is an ACTIVE-memory high-water mark and
does NOT report the separate cache pool that clear_cache()/
set_cache_limit() target -- run 1's mem_logger.py/training_run.log
never captured cache memory at all, only RSS+swap+active peak, so this
is genuinely new data, not a re-read of something already known).

Runs real forward+backward+optimizer steps against the actual model
and lora_config.yaml, WITHOUT touching train_launch.py's guarded
train() loop (to keep this isolated and fast to iterate on), for
--iters steps, logging every iteration to --out. If --clear-every is
set, calls mx.metal.clear_cache() every N iterations to test whether
that caps the cache growth.

Usage:
    python3 corpus/mem_growth_test.py --iters 60 --out corpus/mem_growth_no_clear.jsonl
    python3 corpus/mem_growth_test.py --iters 60 --clear-every 50 --out corpus/mem_growth_clear50.jsonl
"""
import argparse
import json
import subprocess
import re
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def get_swap_used_mb():
    out = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used\s*=\s*([\d.]+)M", out)
    return float(m.group(1)) if m else None


def get_rss_mb():
    import os
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True).stdout.strip()
    return int(out) / 1024.0 if out else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(CORPUS_DIR / "lora_config.yaml"))
    ap.add_argument("--iters", type=int, default=60)
    ap.add_argument("--clear-every", type=int, default=0, help="0 = never clear (baseline growth test)")
    ap.add_argument("--set-cache-limit-gb", type=float, default=0.0, help="0 = no explicit limit")
    ap.add_argument("--out", default=str(CORPUS_DIR / "mem_growth.jsonl"))
    args = ap.parse_args()

    sys.path.insert(0, "/Users/octo/Library/Python/3.9/lib/python/site-packages")
    import yaml
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from mlx.utils import tree_map
    from mlx_lm.utils import load
    from mlx_lm.tuner.utils import linear_to_lora_layers
    from mlx_lm.tuner.datasets import CacheDataset, load_local_dataset
    from mlx_lm.tuner import trainer as trainer_mod
    import types

    cfg = yaml.safe_load(Path(args.config).read_text())

    if args.set_cache_limit_gb > 0:
        mx.set_cache_limit(int(args.set_cache_limit_gb * 1e9))
        print(f"Set explicit cache limit: {args.set_cache_limit_gb} GB")

    print("Loading model...")
    model, tokenizer = load(cfg["model"])
    model.freeze()
    linear_to_lora_layers(model, cfg["num_layers"], cfg["lora_parameters"], use_dora=False)

    ds_config = types.SimpleNamespace(
        mask_prompt=cfg.get("mask_prompt", False), prompt_feature="prompt", text_feature="text",
        completion_feature="completion", chat_feature="messages",
    )
    train_raw, valid_raw, _ = load_local_dataset(Path(cfg["data"]), tokenizer, ds_config)
    train_ds = CacheDataset(train_raw)

    def safe_loss(model, batch, lengths):
        inputs = batch[:, :-1]
        targets = batch[:, 1:]
        logits = model(inputs)
        logits = logits.astype(mx.float32)
        steps = mx.arange(1, targets.shape[1] + 1)
        mask = mx.logical_and(steps >= lengths[:, 0:1], steps <= lengths[:, 1:])
        ce = nn.losses.cross_entropy(logits, targets) * mask
        ntoks = mask.sum()
        ce = ce.astype(mx.float32).sum() / ntoks
        return ce, ntoks

    opt = optim.Adam(learning_rate=cfg["learning_rate"])
    loss_value_and_grad = nn.value_and_grad(model, safe_loss)

    batch_iter = trainer_mod.iterate_batches(
        dataset=train_ds, batch_size=cfg["batch_size"],
        max_seq_length=cfg["max_seq_length"], loop=True,
    )

    print(f"Running {args.iters} real training steps "
          f"(clear_every={args.clear_every or 'never'}, "
          f"cache_limit={'default' if not args.set_cache_limit_gb else str(args.set_cache_limit_gb)+'GB'})...")

    with open(args.out, "w") as f:
        for it in range(1, args.iters + 1):
            batch = next(batch_iter)
            tic = time.time()
            (lvalue, toks), grad = loss_value_and_grad(model, *batch)
            opt.update(model, grad)
            mx.eval(model.state, opt.state, lvalue, toks)
            step_time = time.time() - tic

            if args.clear_every and it % args.clear_every == 0:
                mx.metal.clear_cache()

            entry = {
                "iter": it,
                "loss": lvalue.item(),
                "active_mem_gb": mx.get_active_memory() / 1e9,
                "cache_mem_gb": mx.get_cache_memory() / 1e9,
                "peak_mem_gb": mx.get_peak_memory() / 1e9,
                "rss_mb": get_rss_mb(),
                "swap_used_mb": get_swap_used_mb(),
                "step_time_s": step_time,
                "cleared_this_step": bool(args.clear_every and it % args.clear_every == 0),
            }
            f.write(json.dumps(entry) + "\n")
            f.flush()
            print(f"  it={it} active={entry['active_mem_gb']:.3f}GB cache={entry['cache_mem_gb']:.3f}GB "
                  f"peak={entry['peak_mem_gb']:.3f}GB rss={entry['rss_mb']:.0f}MB "
                  f"swap={entry['swap_used_mb']:.0f}MB {'[CLEARED]' if entry['cleared_this_step'] else ''}")

    print(f"\nDone. Log: {args.out}")


if __name__ == "__main__":
    main()
