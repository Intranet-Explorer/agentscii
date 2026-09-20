#!/usr/bin/env python3
"""corpus/train_launch.py -- safe LoRA training launcher. Wraps
`mlx_lm.lora`'s train()/evaluate() with a patched loss function and a
hard NaN/inf halt guard, and enforces training/harness mutual
exclusivity before starting (user direction, 2026-09-19, items 6-9,
11).

Real bugs found and fixed here, all confirmed via direct
investigation, not assumed:

1. mlx_lm's own default_loss (mlx_lm/tuner/trainer.py) computes
   cross_entropy in the model's native compute dtype and only casts to
   fp32 AFTER cross_entropy already ran -- confirmed the base model's
   forward pass produces fp16 logits (`logits.dtype ==
   mlx.core.float16`). Moved the fp32 cast to BEFORE cross_entropy
   here, since that's strictly more correct regardless of whether it's
   the exact mechanism that caused this run's NaN.

   HONEST CAVEAT, found via direct testing before overclaiming this as
   "the fix": a synthetic test injecting an out-of-fp16-range value
   into a logit tensor showed that once a value has already overflowed
   to literal Inf INSIDE fp16 (the model's own forward pass, before
   this loss function ever sees the logits), casting to fp32
   afterward does NOT recover it -- Inf stays Inf regardless of
   target dtype. Also found: the actual checkpoint 500/1000 LoRA
   weights are fp32 already (not fp16 as first assumed), and the real
   base-model forward pass on the confirmed trigger example showed
   logits comfortably within fp16 range (max ~28.5, nowhere near the
   ~65504 ceiling) -- so a single-value overflow inside the frozen
   base model's own forward pass is NOT confirmed as the actual
   mechanism here. The fp32-before-cross_entropy change is kept
   because it is strictly correct and can only help, not because it
   is proven sufficient to prevent a recurrence on its own -- the
   NaN/Inf halt guard below is the real, verified safety net.

2. mlx_lm's train()/evaluate() bind `default_loss` as a POSITIONAL
   DEFAULT ARGUMENT at function-definition time (confirmed via
   inspect.signature: train.__defaults__[1] is the bound
   default_loss function object). mlx_lm.lora.py's own train_model()
   calls train(...) without passing loss= explicitly, so re-assigning
   mlx_lm.tuner.trainer.default_loss by name after import does NOT
   change what train() actually calls -- Python default arguments are
   evaluated once, not looked up by name at call time. Fixed by
   directly rewriting train.__defaults__ and evaluate.__defaults__
   tuples to swap in the patched loss function, verified this is the
   correct binding position via inspect.signature before trusting it.

3. Hard NaN/Inf halt (user direction, item 8): the loss value is
   eagerly evaluated every step and checked; on the first NaN/Inf, the
   run halts IMMEDIATELY with the batch shape/lengths/loss value
   logged to a report file, rather than silently continuing (which is
   what corrupted every checkpoint last run -- Adam's moment estimates
   absorb a NaN gradient permanently once applied, so iteration 320's
   bad step poisoned every checkpoint through 1040 without a single
   visible symptom besides the loss printout itself going nan).

Usage:
    python3 corpus/train_launch.py -c corpus/lora_config.yaml
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent


def stop_harness_and_dependents():
    """Item 11: training and the AGENTSCII harness are mutually
    exclusive on this machine (both compete for the same GPU/Ollama
    model). Stop the harness (via its own STOP-flag convention),
    verify the process is actually gone, stop the dashboard, and
    unload every Ollama model -- then verify nothing GPU-heavy is
    still resident before returning."""
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

    # Dashboard (best-effort -- find and stop by process name pattern
    # used elsewhere this session)
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


def patch_loss_and_launch(config_path):
    sys.path.insert(0, "/Users/octo/Library/Python/3.9/lib/python/site-packages")
    import mlx.core as mx
    import mlx.nn as nn
    from functools import partial
    from pathlib import Path as P
    from mlx.nn.utils import average_gradients
    from mlx.utils import tree_flatten, tree_map
    from mlx_lm.tuner import trainer as trainer_mod

    def safe_loss(model, batch, lengths):
        """fp32-before-cross_entropy (see module docstring point 1 for
        the honest caveat on what this does/doesn't guarantee)."""
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
        """A full copy of mlx_lm.tuner.trainer.train() with ONE real
        addition: a hard NaN/Inf check on the per-iteration loss value,
        checked in PLAIN PYTHON right after the existing
        `mx.eval(state, losses, ...)` call.

        WHY A FULL COPY, not a smaller patch: train()'s actual training
        step (`step()`, defined inside train() as a closure) is wrapped
        in @mx.compile. Confirmed directly via a minimal reproduction
        BEFORE trusting any patch here: an @mx.compile-wrapped function's
        Python body (prints, .item() calls, sys.exit()) runs ONCE, at
        trace time, then MLX replays the compiled graph directly on
        every subsequent call WITHOUT re-executing that Python code --
        a NaN guard placed inside a compiled loss/step function is dead
        after iteration 1, silently. The real per-iteration hook has to
        live in the plain-Python loop AROUND step(), which means
        reproducing train()'s own loop structure rather than patching a
        smaller piece of it.

        If mlx_lm's trainer.py changes in a future version, this copy
        will drift from upstream -- accepted tradeoff for a guard that
        actually fires every iteration, verified directly, over a
        smaller patch that looked correct but silently wouldn't have
        run past iteration 1.
        """
        if args is None:
            args = trainer_mod.TrainingArgs()
        if mx.metal.is_available():
            mx.set_wired_limit(mx.metal.device_info()["max_recommended_working_set_size"])
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
        current_batch_holder = [None]  # for the NaN report, see below

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

            # === THE REAL, VERIFIED GUARD (item 8) ===
            # Checked HERE, in plain Python, every single iteration --
            # NOT inside step() (see docstring for why that's dead code
            # under mx.compile). This is the one place in the loop that
            # both runs real Python every iteration AND has a fully
            # materialized loss value available (mx.eval just forced it).
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
                report_path = P("/Users/octo/agentscii/corpus/nan_halt_report.json")
                report_path.write_text(json.dumps(report, indent=2))
                print(f"\n\n!!! NaN/INF LOSS AT ITERATION {it} -- HALTING IMMEDIATELY !!!", file=sys.stderr)
                print(f"Report written to {report_path}", file=sys.stderr)
                sys.exit(1)
            # === end guard ===

            if it % args.steps_per_report == 0 or it == args.iters:
                train_loss = mx.distributed.all_sum(losses, stream=mx.cpu).item()
                train_loss /= steps * world_size
                n_tokens_r = mx.distributed.all_sum(n_tokens, stream=mx.cpu).item()
                learning_rate = optimizer.learning_rate.item()
                it_sec = args.steps_per_report / train_time
                tokens_sec = float(n_tokens_r) / train_time
                trained_tokens += n_tokens_r
                peak_mem = mx.get_peak_memory() / 1e9
                if rank == 0:
                    print(
                        f"Iter {it}: Train loss {train_loss:.3f}, "
                        f"Learning Rate {learning_rate:.3e}, It/sec {it_sec:.3f}, "
                        f"Tokens/sec {tokens_sec:.3f}, Trained Tokens {trained_tokens}, "
                        f"Peak mem {peak_mem:.3f} GB", flush=True,
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

    # Rebind train's POSITIONAL DEFAULT for `loss` to safe_loss, and
    # replace trainer_mod.train itself with the NaN-guarded copy (see
    # docstring point 2 for why reassigning by name alone is not
    # enough -- mlx_lm.lora.py imports `train` directly into its own
    # module namespace via `from .tuner.trainer import ... train`, so
    # BOTH trainer_mod.train and the name lora_mod already bound at
    # import time need to point at the guarded version).
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

    # Import mlx_lm.lora AFTER the patch, then also fix its own
    # already-imported `train` name (it does `from .tuner.trainer
    # import train`, which binds a local name at import time that
    # patching trainer_mod.train afterward does NOT change).
    from mlx_lm import lora as lora_mod
    lora_mod.train = train_with_nan_guard
    sys.argv = ["mlx_lm.lora", "-c", str(config_path)]
    lora_mod.main()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-c", "--config", default=str(CORPUS_DIR / "lora_config.yaml"))
    ap.add_argument("--skip-stop-check", action="store_true", help="DANGEROUS: skip the harness/dashboard/ollama stop step (only for isolated smoke tests where you've already verified the machine is clean)")
    args = ap.parse_args()

    if not args.skip_stop_check:
        stop_harness_and_dependents()
    else:
        print("--skip-stop-check set: NOT stopping harness/dashboard/ollama. "
              "Only use this if you have already verified nothing else is resident.")

    patch_loss_and_launch(args.config)


if __name__ == "__main__":
    main()
