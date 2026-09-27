#!/usr/bin/env python3
"""Safe LoRA training launcher around mlx_lm.lora.

Stops the harness first (they share the GPU), spawns the watchdogs, and
runs mlx_lm's trainer with these changes:

1. Loss casts logits to fp32 before cross_entropy. mlx_lm casts after.
   This does not recover an Inf already produced in the fp16 forward pass;
   the NaN guard (3) is the real safety net.
2. train() and evaluate() bind default_loss as a default argument, so
   reassigning the name does nothing. Their __defaults__ are rewritten.
3. Loss is checked for NaN/Inf every iteration, and the run halts with a
   report. Continuing would poison Adam's state and every later checkpoint.
4. Preflight rejects any example over max_seq_length. mlx_lm silently
   truncates, which can drop a target entirely.
5. MLX cache limit of 16GB. Without it the buffer cache plateaus near 45GB
   on this config; periodic clear_cache() just refills to the same level.

Usage:
    python3 corpus/train_launch.py -c corpus/lora_config.yaml
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent


def stop_harness_and_dependents():
    """Stop the harness, dashboard and Ollama models before training; exit if the harness survives.

    Training and the harness compete for the same GPU.
    """
    print("=== Stopping harness + dependents before training ===")

    stop_flag = AGENTSCII_ROOT / "STOP"
    stop_flag.touch()
    print("STOP flag set, waiting for harness to end its current shift...")
    for _ in range(40):  # up to ~10 minutes
        result = subprocess.run(["pgrep", "-f", "agentscii/harness.py"], capture_output=True, text=True)
        if not result.stdout.strip():
            print("Harness process confirmed stopped.")
            break
        time.sleep(15)
    else:
        print("WARNING: harness did not stop within the wait window -- check manually before training.", file=sys.stderr)

    if stop_flag.exists():
        stop_flag.unlink()

    # Dashboard, best effort.
    result = subprocess.run(["pgrep", "-f", "agentscii-dashboard"], capture_output=True, text=True)
    for pid in result.stdout.split():
        print(f"Stopping dashboard process {pid}...")
        subprocess.run(["kill", pid])

    # Unload every Ollama model
    print("Stopping all Ollama models...")
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    for line in result.stdout.splitlines()[1:]:
        name = line.split()[0] if line.split() else None
        if name:
            subprocess.run(["ollama", "stop", name], capture_output=True)

    time.sleep(3)
    ps_result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
    print("ollama ps after stop:")
    print(ps_result.stdout)

    remaining_harness = subprocess.run(["pgrep", "-f", "agentscii/harness.py"], capture_output=True, text=True)
    if remaining_harness.stdout.strip():
        print("ERROR: harness process still resident after stop attempt -- ABORTING launch.", file=sys.stderr)
        sys.exit(1)
    print("Confirmed: harness stopped, dashboard stopped, no Ollama models loaded.\n")


def enforce_max_seq_length(config_path):
    """Exit if any train/valid example exceeds max_seq_length.

    Tokenizes through ChatDataset.process, the same path training uses.
    Loads the model a second time, which costs minutes and can trip
    progress_watchdog's stall check (harmless; it only samples).
    """
    import yaml
    sys.path.insert(0, os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))
    from mlx_lm.utils import load
    from mlx_lm.tuner.datasets import load_local_dataset
    import types as _types

    cfg = yaml.safe_load(Path(config_path).read_text())
    max_seq_length = cfg["max_seq_length"]
    data_dir = Path(cfg["data"])
    mask_prompt = cfg.get("mask_prompt", False)

    print(f"=== max_seq_length preflight: cap={max_seq_length}, data={data_dir} ===")
    _, tokenizer = load(cfg["model"])
    ds_config = _types.SimpleNamespace(
        mask_prompt=mask_prompt, prompt_feature="prompt", text_feature="text",
        completion_feature="completion", chat_feature="messages",
    )
    train_raw, valid_raw, _test_raw = load_local_dataset(data_dir, tokenizer, ds_config)

    over_cap = []
    for split_name, split_raw in [("train", train_raw), ("valid", valid_raw)]:
        for i in range(len(split_raw)):
            tokens, _offset = split_raw.process(split_raw[i])
            if len(tokens) > max_seq_length:
                over_cap.append({"split": split_name, "index": i, "length": len(tokens)})

    if over_cap:
        import json
        report_path = CORPUS_DIR / "max_seq_length_violation_report.json"
        report_path.write_text(json.dumps({
            "max_seq_length": max_seq_length,
            "n_violations": len(over_cap),
            "violations_sample": over_cap[:50],
        }, indent=2))
        print(f"\n!!! {len(over_cap)} example(s) exceed max_seq_length={max_seq_length} !!!",
              file=sys.stderr)
        print(f"Report: {report_path}", file=sys.stderr)
        print("ABORTING before training -- rebuild the dataset (corpus/filter_dataset.py) "
              "or raise max_seq_length deliberately, don't let mlx_lm silently truncate.",
              file=sys.stderr)
        sys.exit(1)

    print(f"Preflight OK: all {len(train_raw)} train + {len(valid_raw)} valid examples "
          f"are <= {max_seq_length} tokens under the real tokenizer.\n")


def patch_loss_and_launch(config_path):
    sys.path.insert(0, os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))
    import mlx.core as mx
    import mlx.nn as nn
    from functools import partial
    from pathlib import Path as P
    from mlx.nn.utils import average_gradients
    from mlx.utils import tree_flatten, tree_map
    from mlx_lm.tuner import trainer as trainer_mod

    def safe_loss(model, batch, lengths):
        """mlx_lm's default loss with the fp32 cast before cross_entropy (module docstring, 1)."""
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

    def train_with_nan_guard(
        model, optimizer, train_dataset, val_dataset,
        args=None, loss=safe_loss, iterate_batches=trainer_mod.iterate_batches,
        training_callback=None,
    ):
        """Copy of mlx_lm.tuner.trainer.train() plus a per-iteration NaN/Inf halt.

        A full copy because step() is @mx.compile'd: Python inside it runs
        once at trace time, so a guard there is dead after iteration 1. The
        check has to live in the plain loop. Will drift if mlx_lm's trainer
        changes.
        """
        if args is None:
            args = trainer_mod.TrainingArgs()
        if mx.metal.is_available():
            mx.set_wired_limit(mx.metal.device_info()["max_recommended_working_set_size"])
        # Cap the MLX buffer cache; see module docstring, point 5.
        mx.set_cache_limit(16 * 10**9)
        print(f"Starting training..., iters: {args.iters}")
        world = mx.distributed.init()
        world_size = world.size()
        rank = world.rank()
        if world_size > 1:
            print(f"Node {rank} of {world_size}")

        if args.grad_checkpoint:
            trainer_mod.grad_checkpoint(model.layers[0])

        loss_value_and_grad = nn.value_and_grad(model, loss)
        grad_accum_steps = args.grad_accumulation_steps
        if grad_accum_steps < 1:
            raise ValueError("grad_accumulation_steps must be at least 1")

        state = [model.state, optimizer.state, mx.random.state]

        @partial(mx.compile, inputs=state, outputs=state)
        def step(batch, prev_grad, do_update):
            (lvalue, toks), grad = loss_value_and_grad(model, *batch)
            if prev_grad is not None:
                grad = tree_map(lambda x, y: x + y, grad, prev_grad)
            if do_update:
                grad = average_gradients(grad)
                if grad_accum_steps > 1:
                    grad = tree_map(lambda x: x / grad_accum_steps, grad)
                optimizer.update(model, grad)
                grad = None
            return lvalue, toks, grad

        model.train()
        losses = 0
        n_tokens = 0
        steps = 0
        trained_tokens = 0
        train_time = 0
        grad_accum = None
        current_batch_holder = [None]  # for the NaN report

        for it, batch in zip(
            range(1, args.iters + 1),
            iterate_batches(
                dataset=train_dataset, batch_size=args.batch_size,
                max_seq_length=args.max_seq_length, loop=True, comm_group=world,
            ),
        ):
            current_batch_holder[0] = batch
            tic = time.time()
            if it == 1 or it % args.steps_per_eval == 0 or it == args.iters:
                tic = time.time()
                val_loss = trainer_mod.evaluate(
                    model=model, dataset=val_dataset, loss=loss,
                    batch_size=args.batch_size, num_batches=args.val_batches,
                    max_seq_length=args.max_seq_length, iterate_batches=iterate_batches,
                )
                model.train()
                val_time = time.time() - tic
                if rank == 0:
                    print(f"Iter {it}: Val loss {val_loss:.3f}, Val took {val_time:.3f}s", flush=True)
                if training_callback is not None:
                    training_callback.on_val_loss_report(
                        {"iteration": it - 1, "val_loss": val_loss, "val_time": val_time}
                    )
                tic = time.time()

            lvalue, toks, grad_accum = step(batch, grad_accum, it % grad_accum_steps == 0)
            losses += lvalue
            n_tokens += toks
            steps += 1
            mx.eval(state, losses, n_tokens, grad_accum)
            train_time += time.time() - tic

            # NaN/Inf guard. Must be here, outside the compiled step(),
            # after mx.eval has materialized the loss.
            this_step_loss = lvalue.item() if hasattr(lvalue, "item") else float(lvalue)
            if this_step_loss != this_step_loss or this_step_loss in (float("inf"), float("-inf")):
                import json
                b = current_batch_holder[0]
                report = {
                    "halted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "iteration": it,
                    "loss_value": str(this_step_loss),
                    "batch_shape": list(b[0].shape) if isinstance(b, tuple) else list(b.shape),
                }
                report_path = P.home() / "agentscii/corpus/nan_halt_report.json"
                report_path.write_text(json.dumps(report, indent=2))
                print(f"\n\n!!! NaN/INF LOSS AT ITERATION {it} -- HALTING IMMEDIATELY !!!", file=sys.stderr)
                print(f"Report written to {report_path}", file=sys.stderr)
                sys.exit(1)
            # End guard.

            if it % args.steps_per_report == 0 or it == args.iters:
                train_loss = mx.distributed.all_sum(losses, stream=mx.cpu).item()
                train_loss /= steps * world_size
                n_tokens_r = mx.distributed.all_sum(n_tokens, stream=mx.cpu).item()
                learning_rate = optimizer.learning_rate.item()
                it_sec = args.steps_per_report / train_time
                tokens_sec = float(n_tokens_r) / train_time
                trained_tokens += n_tokens_r
                peak_mem = mx.get_peak_memory() / 1e9
                cache_mem = mx.get_cache_memory() / 1e9
                if rank == 0:
                    print(
                        f"Iter {it}: Train loss {train_loss:.3f}, "
                        f"Learning Rate {learning_rate:.3e}, It/sec {it_sec:.3f}, "
                        f"Tokens/sec {tokens_sec:.3f}, Trained Tokens {trained_tokens}, "
                        f"Peak mem {peak_mem:.3f} GB, Cache mem {cache_mem:.3f} GB", flush=True,
                    )
                if training_callback is not None:
                    training_callback.on_train_loss_report({
                        "iteration": it, "train_loss": train_loss, "learning_rate": learning_rate,
                        "iterations_per_second": it_sec, "tokens_per_second": tokens_sec,
                        "trained_tokens": trained_tokens, "peak_memory": peak_mem,
                    })
                losses = 0
                n_tokens = 0
                steps = 0
                train_time = 0

            if it % args.steps_per_save == 0 and rank == 0:
                adapter_weights = dict(tree_flatten(model.trainable_parameters()))
                mx.save_safetensors(str(args.adapter_file), adapter_weights)
                checkpoint = P(args.adapter_file).parent / f"{it:07d}_adapters.safetensors"
                mx.save_safetensors(str(checkpoint), adapter_weights)
                print(f"Iter {it}: Saved adapter weights to {args.adapter_file} and {checkpoint}.")

        if rank == 0:
            adapter_weights = dict(tree_flatten(model.trainable_parameters()))
            mx.save_safetensors(str(args.adapter_file), adapter_weights)
            print(f"Saved final weights to {args.adapter_file}.")

    # Bind safe_loss as the default loss and install the guarded train.
    # Reassigning default_loss by name wouldn't work (module docstring, 2).
    train_with_nan_guard.__defaults__ = (
        trainer_mod.TrainingArgs(), safe_loss, trainer_mod.iterate_batches, None,
    )
    trainer_mod.train = train_with_nan_guard
    trainer_mod.evaluate.__defaults__ = tuple(
        (safe_loss if x is trainer_mod.default_loss else x)
        for x in trainer_mod.evaluate.__defaults__
    )

    print("Patched: safe_loss (fp32-before-cross_entropy) + train_with_nan_guard "
          "(real per-iteration NaN/Inf halt, verified to run outside mx.compile).")

    # mlx_lm.lora imports `train` by name, so patch its binding too.
    from mlx_lm import lora as lora_mod
    lora_mod.train = train_with_nan_guard
    sys.argv = ["mlx_lm.lora", "-c", str(config_path)]
    lora_mod.main()


def spawn_watchdogs():
    """Start mem_watchdog, mem_logger and progress_watchdog on this PID at launch.

    Started here so they cover the run from iteration 1.
    """
    import os
    pid = os.getpid()
    log_path = CORPUS_DIR / "training_run.log"
    procs = []
    procs.append(subprocess.Popen(
        [sys.executable, str(CORPUS_DIR / "mem_watchdog.py"), "--pid", str(pid), "--log", str(log_path)],
        stdout=open(CORPUS_DIR / "mem_watchdog_stdout.log", "w"), stderr=subprocess.STDOUT,
    ))
    procs.append(subprocess.Popen(
        [sys.executable, str(CORPUS_DIR / "mem_logger.py"), "--pid", str(pid), "--out", str(CORPUS_DIR / "mem_log.jsonl")],
        stdout=open(CORPUS_DIR / "mem_logger_stdout.log", "w"), stderr=subprocess.STDOUT,
    ))
    procs.append(subprocess.Popen(
        [sys.executable, str(CORPUS_DIR / "progress_watchdog.py"), "--pid", str(pid), "--log", str(log_path)],
        stdout=open(CORPUS_DIR / "progress_watchdog_stdout.log", "w"), stderr=subprocess.STDOUT,
    ))
    print(f"Spawned 3 watchdogs (mem_watchdog, mem_logger, progress_watchdog) "
          f"against PID {pid}: {[p.pid for p in procs]}")
    return procs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-c", "--config", default=str(CORPUS_DIR / "lora_config.yaml"))
    ap.add_argument("--skip-stop-check", action="store_true", help="DANGEROUS: skip the harness/dashboard/ollama stop step (only for isolated smoke tests where you've already verified the machine is clean)")
    ap.add_argument("--skip-watchdogs", action="store_true", help="DANGEROUS: don't auto-spawn mem_watchdog/mem_logger/progress_watchdog (only if you're starting them yourself)")
    args = ap.parse_args()

    if not args.skip_stop_check:
        stop_harness_and_dependents()
    else:
        print("--skip-stop-check set: NOT stopping harness/dashboard/ollama. "
              "Only use this if you have already verified nothing else is resident.")

    if not args.skip_watchdogs:
        spawn_watchdogs()
    else:
        print("--skip-watchdogs set: NOT auto-spawning watchdogs.")

    enforce_max_seq_length(args.config)
    patch_loss_and_launch(args.config)


if __name__ == "__main__":
    main()
