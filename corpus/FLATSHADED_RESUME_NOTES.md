# Flat->shaded training track -- resume notes

Training is PAUSED (user direction, 2026-09-21) after the first
500-iteration run showed a copy-failure: the model achieved low loss
by reproducing the flat input almost unchanged (0.0% pixel diff on
_phosphor, 0.5% on _reach, and the one real edit on _guardian.v1 was
destructive, not additive shading). Diagnosis (user, verbatim): "The
no-op result is the copy failure: most target cells equal the input,
so reproducing the input minimizes loss."

Do NOT act on any of this until the user explicitly resumes the
training track. This file is a durable TODO, not a task in progress.

## 1. Mask the loss to cells that differ (the real fix for the copy failure)

Currently `corpus/build_flat_shaded_dataset.py::build_prompt` + the
mlx_lm "messages" format masks the loss to the WHOLE completion
(target_text), matching FIM's old convention. For flat->shaded, most
cells in a window are UNCHANGED by flattening (plain background, text,
already-simple regions -- flatten_piece_and_merge only touches cells
with real half-block/shade glyphs to begin with). A loss over the
whole target lets "copy the input" trivially minimize loss on the
majority-unchanged cells, drowning out the gradient signal from the
minority of cells that actually need new shading.

Real fix: compute a per-cell diff mask (flat_chars/fg/bg vs
target_chars/fg/bg, cell-by-cell) at dataset-build time, and only
include DIFFERING cells in the loss -- either via a different RLE
encoding that omits identical runs (so the target text itself is
shorter and only contains the real edits), or via an explicit
mlx_lm-compatible loss-masking mechanism if the framework supports a
per-token/per-span mask beyond prompt-vs-completion. Needs design work
BEFORE the next training run -- not implemented yet.

## 2. Explain the dataset shrink: ~30k -> 2,740

The old FIM dataset was 31,243 rows (corpus/train_subsample.jsonl).
The flat-shaded dataset built by
corpus/build_flat_shaded_dataset.py is only 3,000 windows requested,
2,740 kept after the max_seq_length=5120 filter (110 dropped as
over-cap). This is NOT the same reduction as the FIM pathology-drop
filtering from earlier in the project -- it's a smaller REQUESTED
size (--n-windows 3000, set deliberately small for a first "does the
design even work" pass, not meant to be the final training set size).
User asked for an explanation of the shrink -- write one up (this
note + a real accounting of n-windows request vs FIM's original
subsample size) before/when training resumes, don't just quietly
reuse 2,740 as if it were an intentional final number.

## 3. Infra fixes needed before the next training launch

- **Tokenizer regex fix**: every launch logs `The tokenizer you are
  loading from '...' with an incorrect regex pattern... You should
  set the fix_mistral_regex=True flag`. Not yet addressed -- probably
  a one-line change wherever `AutoTokenizer`/mlx_lm's `load()` is
  called (train_launch.py, checkpoint_eval.py, eval_on_raze.py,
  generate_region.py all load this same tokenizer). Check whether
  mlx_lm's `load()` exposes a way to pass this through, or whether it
  needs a direct HF tokenizer post-load patch.
- **Resume-from-checkpoint**: train_launch.py has no way to resume a
  killed/interrupted run from its last saved checkpoint (0000100_,
  0000200_, etc `adapters.safetensors`) -- every interruption this
  session (memory contention, Metal OOM, agent_close) required a full
  restart from iteration 0. A real resume path (load the latest
  checkpoint's adapter weights + optimizer state if mlx_lm.lora
  supports it, continue from `--resume-iters N`) would have saved
  significant wall-clock time across the 4 launch attempts this
  session.
- **Preflight logging to the run's own log**: `enforce_max_seq_length()`
  currently prints preflight results to stdout, which train_launch.py
  redirects into the run's log file already (this mostly works) --
  but confirm this is genuinely landing in EVERY run's own log, not
  occasionally lost to a race with the watchdog spawn order, and that
  it's clearly delineated (a run's log should be self-contained enough
  to answer "did preflight pass, on what data, at what cap" without
  cross-referencing a separate file).
- **Watchdogs attached to the correct PID and log file on every
  launch**: found live this session -- `mem_watchdog_stdout.log`/
  `mem_watchdog_kill_report.json` are per-invocation-current, but the
  OLDER `corpus/mem_watchdog.log` file (a stale leftover from a much
  earlier abandoned run, PID 17159) is still sitting in the repo and
  can be confused for current state (I mistakenly read it as current
  once this session before finding the real, current
  mem_watchdog_stdout.log). Also: watchdog PID targeting has been
  correct in practice this session (each spawn_watchdogs() call
  correctly targeted the new launch's own PID), but the STALE LOG FILE
  problem is real and worth fixing -- either timestamp/rotate
  watchdog logs per-run, or have spawn_watchdogs() write to a
  run-specific log path (e.g. named after the adapter_path or a
  timestamp) instead of a fixed shared filename that accumulates
  confusing history across unrelated runs.

## Context for whoever resumes this

Full loss-masking-to-diff-cells redesign (#1) is the real blocker --
without it, re-running more iterations or tuning LR further will keep
optimizing the same copy-shortcut, not real shading. Do that design
work first, verify on a small re-rendered pair set (same "render 5
pairs, judge before training" discipline used earlier), THEN resume
training only after the masked-loss design is confirmed to target the
right cells.
