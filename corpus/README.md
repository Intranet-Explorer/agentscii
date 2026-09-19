# AGENTSCII corpus (step 1: fetch + parse + validate + dedupe + index + holdout)

A local, disk-only ANSI/ASCII training corpus built from 16colo.rs's real
archive (via the `sixteencolors/sixteencolors-archive` GitHub mirror), for
future reference-corpus/LoRA work. **Nothing in this directory except the
`.py` scripts is tracked in git or pushed anywhere** -- see the
repo-root `.gitignore`. `corpus/data/`, `corpus/raw/`, `corpus/parsed/`,
and all reports/manifests are real other-artists'-work / derived data,
kept local only, same rationale as `workspace/references/study/`.

## Pipeline

```
fetch.py            -> downloads pack .zips by year, extracts .ans/.asc  -> corpus/data/
parse.py            -> parses each file into a cell-grid .npz            -> corpus/parsed/
validate.py         -> renders N random files with ansilove, diffs cell-by-cell
dedupe.py           -> content-hashes parsed pieces, finds cross-pack duplicates
technique_index.py  -> per-piece shading/technique metrics                -> technique_manifest.jsonl
technique_report.py -> distribution report over the technique manifest
holdout.py           -> frozen, dedup-aware train/holdout split            -> holdout_split.json
score_shipped.py     -> scores every shipped AGENTSCII piece against the corpus percentile distribution
windowing.py         -> step 2: 40x16 windows, RLE encoding, fill-in-the-middle examples -> windows.jsonl
token_stats.py       -> token-length stats over windows.jsonl
bench_encoding.py    -> tokens/cell benchmark across 3 candidate cell encodings
subsample.py         -> stratified 40k-example subsample for v1 -> train_subsample.jsonl
eval_harness.py      -> FIM eval: mask+fill+score+pairwise-Opus-judge against frozen holdout
prepare_training_data.py -> converts train_subsample.jsonl to mlx_lm chat-messages format
lora_config.yaml     -> mlx_lm.lora hyperparameters for the v1 training run
caption.py           -> per-parent-piece caption via local VLM + SAUCE year/group prefix (DROPPED from v1, kept for a later phase)
```

## Current real numbers (full run, all 37 available years, 1990-2026)

- **86,093** `.ans`/`.asc` files fetched from **4,832 packs** across every
  year 16colo.rs has (not a partial sample -- confirmed against the
  GitHub API's own year listing, `1990`-`2026`, all present).
- **86,093/86,093 parsed, zero crashes** (100%).
- **81,468 unique pieces by content hash** (chars+fg+bg grid, not source
  path or SAUCE metadata) -- **4,625 duplicate copies (5.4%)** across
  4,158 groups, real cross-pack re-releases/compilations, spot-checked
  and confirmed genuine (e.g. `NEOTOKYO.ANS` appears in 3 separate 1994
  packs). See `dedupe_report.json`.
- **Validation against real ansilove**, three independent 200-file random
  samples across the full 37-year corpus: seed=0 199/200 (99.5%), seed=42
  192/200 (96.0%), seed=100 198/200 (99.0%) -- **combined 589/600 (98.2%)
  clean**, zero crashes in any run. Confirms the parser holds up on
  material outside the original 9-year sample it was built against
  (1990-1993 and 2024-2026 in particular).
- **Technique index**: 86,093/86,093 indexed, zero errors. See
  `technique_manifest.jsonl` and the distribution table below.
- **Holdout split**: 5.0% held out (4,073 unique pieces / 4,294 raw
  paths including duplicates), frozen to `holdout_split.json`,
  **never trained on**. Split at the content-hash level, not the raw
  file level -- verified zero duplicate groups leak across the
  train/holdout boundary (a piece and its re-release in another pack
  are always on the same side).

### fetch.py

```
python3 corpus/fetch.py --years 1996 1997 --limit-per-year 50 --max-size-mb 10
python3 corpus/fetch.py --years all
```

Uses the GitHub Contents API (one request per year -- confirmed live that
the API does NOT paginate a directory listing, it returns everything in
one response) plus the `gh` CLI's own token if logged in (avoids the
unauthenticated 60 req/hr rate limit). Resumable: re-running skips
already-downloaded pack zips AND already-extracted pack output
directories (the latter guard added after a real full-archive run
crashed partway through and needed a safe resume -- see bug list below).

### parse.py

```
python3 corpus/parse.py --input-dir corpus/data --output-dir corpus/parsed
python3 corpus/parse.py --file corpus/data/1996/forge_09/AS-MAXX.ANS   # single-file debug
```

Parses CP437, strips SAUCE (extracting title/author/group/date/iCE-colors
metadata), handles SGR (including bold/blink), cursor movement
(ESC[A/B/C/D/H/f/s/u), TAB, and 80-column wrap. Every design decision was
checked live against `ansilove` (the reference renderer,
`brew install ansilove`) rather than assumed from spec reading -- see the
module docstring and inline comments for the specific test cases. Output:
one `.npz` per input file with `chars`/`fg`/`bg` arrays plus SAUCE metadata,
named `<original filename with extension>.npz` (e.g. `FOO.ANS.npz`) --
**not** `<stem>.npz`, see bug list below for why that distinction matters.

### validate.py

```
python3 corpus/validate.py --n 200 --seed 0
```

Renders N random files with real `ansilove` and diffs parse.py's output
against it cell-by-cell (bg color via corner sampling, glyph presence via
non-background pixel detection, row/col count).

### dedupe.py

```
python3 corpus/dedupe.py
```

SHA-256 hashes each parsed piece's `chars`+`fg`+`bg` grid content
(deliberately excluding source path and SAUCE metadata, so two exact
re-releases of the same artwork under a different filename/credit still
hash identically). Reports unique-piece count and writes a canonical/
duplicate path map used by `holdout.py` to prevent train/holdout leaks.

### technique_index.py / technique_report.py

```
python3 corpus/technique_index.py
python3 corpus/technique_report.py
```

Per-piece metrics over the whole corpus: `half_block_pct` (▀▄ only, NOT
lumped with █ -- see docstring for why this is a different bucket from
harness.py's own `_HALF_BLOCK_CHARS`), `shade_pct` (░▒▓ RAMP density),
`full_block_pct` (█ alone), `distinct_colors`, `alnum_pct` (ASCII
letter/digit fraction -- the signal used to exclude logos/text layouts),
and raw `subject_cells` count. Distribution (86,093 pieces, restricted to
the 84,262 with >=200 subject cells):

| metric | mean | p50 | p90 | p95 | p99 |
|---|---|---|---|---|---|
| half_block_pct | 15.9 | 15.4 | 36.8 | 42.3 | 53.1 |
| shade_pct | 14.8 | 10.0 | 38.3 | 46.4 | 64.7 |
| full_block_pct | 19.3 | 14.7 | 49.2 | 58.8 | 76.0 |
| alnum_pct | 12.8 | 7.4 | 31.7 | 43.6 | 74.7 |
| distinct_colors | 6.4 | 6.0 | 13.0 | 15.0 | 16.0 |

Candidate shading-heavy subset size (half_block_pct > H OR shade_pct > S,
AND alnum_pct < 15, AND distinct_colors >= 4 -- the color floor excludes
near-monochrome halftone effects, a real but different technique from
graduated lit-to-shadow color transitions):

| H (half-block%) | S (shade%) | n | % of corpus |
|---|---|---|---|
| 10 | 5 | 37,116 | 44.0% |
| 20 | 10 | 35,277 | 41.9% |
| 30 | 15 | 31,194 | 37.0% |
| 36.8 (p90) | 38.3 (p90) | 13,359 | 15.9% |
| 42.3 (p95) | 46.4 (p95) | 6,848 | 8.1% |

No threshold has been chosen yet -- this is the raw distribution to pick
one from, not a recommendation. **Nothing has been windowed, captioned,
or trained on** as of this report.

### holdout.py

```
python3 corpus/holdout.py --fraction 0.05 --seed 0
```

Frozen 5% train/holdout split, computed once before any training step.
Splits on content-hash canonical pieces (via `dedupe_report.json`) then
expands each side back out to every raw duplicate path, so a piece
appearing in 3 packs never has 2 copies in train and 1 in holdout.

## Raze vs. the corpus (score_shipped.py)

```
python3 corpus/score_shipped.py
```

Scores every shipped AGENTSCII piece (130 pieces, 54 packs) against the
corpus technique distribution, using the EXACT SAME subject-only metric
definitions as `technique_index.py` (fixed 2026-09-19 so the two sides
are directly comparable -- `harness.py`'s own pinned-best gate had
briefly drifted to a whole-canvas denominator and a different glyph set
before being reverted to match).

**Summary across 130 shipped pieces:**

| metric | mean percentile | median percentile |
|---|---|---|
| half_block_pct | 37.2 | 36.5 |
| shade_pct | 89.8 | 97.7 |

**The house leans almost entirely on `▓░▒` dithering, not half-block
subpixel geometry, relative to the real archive**: median shade_pct
percentile is 97.7 (heavier dithering than 97.7% of the real 86,093-
piece corpus), while median half_block_pct percentile is 36.5 --
slightly BELOW the corpus median. **109 of 130 shipped pieces (84%)
have exactly 0.0% half_block_pct** -- zero ▀▄ usage at all. Full
per-piece breakdown in `shipped_scoring_report.json`.

## Step 2: windowing, RLE encoding, fill-in-the-middle (windowing.py)

**Nothing has been trained on. This step reports window counts and
token stats only, per instruction.**

```
python3 corpus/windowing.py
```

### Selection

Train-split pieces only (`holdout_split.json`'s `train_paths`; holdout
is never touched by this step). Base filter: `half_block_pct > 30 OR
shade_pct > 15`, AND `alnum_pct < 15`, AND `distinct_colors >= 4` --
**29,701 pieces**. The p90 tier within that (`half_block_pct > 36.8 OR
shade_pct > 38.3`, same alnum/color filters) -- **12,730 pieces** --
is oversampled 3x (i.e. appears as 3 separate piece-instances going
into windowing, each independently windowed) per instruction: "train
on the H=30/S=15 subset... but oversample the p90 tier ~3x so the
model sees more heavily shaded work."

### Windows

**40x16 windows** (user direction, 2026-09-19: "shrink the window, 40
cols x 16 rows, not 80x24"), 50% overlap in BOTH dimensions (8-row,
20-col stride). At this smaller width, a window only covers half of a
typical 80-col piece, so real 2D column tiling is used, not just row
tiling with column pad/trim like the original 80-col-window version.
Pieces smaller than the window are padded with true background rather
than skipped -- at 40x16 that discards far fewer real pieces than the
old 80x24 skip-if-too-small rule did. Final count: **1,324,191 windows
across all 55,161 selected piece-instances** (every piece now yields
at least one window, vs. 37% skipped entirely at the old size).

Conditioning is **SAUCE year + group + per-window technique metrics**
(`half_block_pct`, `shade_pct`, `shade_bucket` = low/mid/high, computed
per-WINDOW not per-parent-piece) -- captioning was dropped from v1 (see
below) since FIM doesn't need it.

### RLE row encoding

Rows are encoded as `r{NN} {col},{fg}{bg}:{glyphs} ...` -- run-length
merged runs of identical (char, fg, bg), color packed as two hex
digits (fg then bg, not a single palette index, since a single index
can't represent a colored glyph on a colored background without
silently dropping one). Fully-background runs (space, bg=0) are
omitted entirely -- that omission is the actual compression this
format buys over raw per-cell encoding, since most of a typical window
is background. Real example (see `windows.jsonl`):

```
r00 14,90:▄ 15,90:█ 16,10:██████████████████████████████████████████████ 62,90:█ 63,90:▄▄▄
```

**Real bug found and fixed**: a run of literal SPACE glyphs on a
colored background (a genuine, valid case -- a solid color block with
no visible character) contains the same `' '` character used as the
run separator. An early FITM masking implementation naively
`str.split(' ')`-reparsed an already-joined run string to shift column
indices, which silently corrupted exactly this case. Fixed by working
with structured `(col, color, glyphs)` run tuples throughout
(`rle_encode_row_runs`), never re-parsing joined text.

### Fill-in-the-middle (FITM)

Each window gets one FITM example: a rectangle is masked (marked with
an explicit `[MASK w=N]` inline token on each affected row, with real
left/right context on either side of the hole preserved -- NOT a
private-use sentinel glyph written into the grid and RLE-encoded like
real content, which an earlier version did; that wasted real tokens on
long runs of an invisible, rarely-trained-on codepoint and visually
looked identical to blank background when inspected). The TARGET is
the masked rectangle's real original content, RLE-encoded on its own
local coordinate system.

Mask area tuned to **12-25% of window area** (down from an initial
20-40%, which measured a real mean of 461 target tokens against the
user's "~300 tokens" target).

### Token stats (tiktoken cl100k_base, 30,000-window sample)

| | mean | median | p90 | p99 | max |
|---|---|---|---|---|---|
| context tokens | 1,225 | 1,219 | 1,911 | 2,456 | 3,148 |
| target tokens | 287 | 281 | 514 | 718 | 975 |
| context+target tokens | 1,512 | 1,510 | 2,349 | 2,988 | 3,776 |

Lands close to the stated targets (~1,200 context / ~300 target) at
the mean/median; the p90 tail runs meaningfully higher (context 1,911,
target 514) since mask size and window content density both vary
window to window -- reported honestly rather than force-tuned further
and distorting the mask-size distribution.

### Encoding benchmark (bench_encoding.py) -- RLE confirmed as the cheapest of 3

```
python3 corpus/bench_encoding.py
```

Measured tokens/cell on the ACTUAL tokenizer (tiktoken cl100k_base) for
3 candidate encodings, on the same 3,000 real windows:

| encoding | mean tokens/cell |
|---|---|
| **(a) current RLE** | **2.04** |
| (b) plain per-cell, 1-char color code | 3.36 |
| (c) packed single-codepoint (1 Unicode PUA char per cell) | 4.08 |

**RLE wins decisively -- it is NOT the wrong choice.** The "0.89
chars/token" number from the earlier token_stats.py report measures a
different thing (chars-per-token, not tokens-per-cell) and doesn't by
itself imply RLE is inefficient; benchmarked head-to-head against the
literal alternatives, it's the cheapest. The packed single-codepoint
scheme -- intuitively the most "compressed" (one symbol per cell,
252-glyph x 16-fg x 16-bg = 64,512 real distinct combinations, mapped
into Unicode Private-Use-Area codepoints) -- is actually the MOST
expensive, confirmed directly: a single PUA-A codepoint costs **4
tokens** under cl100k_base (falls back to raw UTF-8 byte-level
encoding, since the tokenizer was never trained on that codepoint
range), vs. 2 tokens for a real half-block character and 1 for plain
ASCII. Packing cells into rare codepoints trades real compression at
the character level for a worse outcome at the token level, which is
the level that actually matters for training/inference cost.

### Subsampling for v1 (subsample.py)

```
python3 corpus/subsample.py --n 40000
```

Stratified subsample to **40,000 training examples** (user direction,
2026-09-19), sampling a fixed, explicit ratio out of the full window
pool rather than a uniform slice: **50% high-tier (20,000) / 35%
mid-tier (14,000) / 15% low-tier (6,000)**, using the same
low/mid/high `shade_bucket` labels computed during windowing. The full
pool has plenty of headroom in every bucket (787,772 high / 381,342
mid / 155,077 low across 1,324,191 total windows), so the exact target
ratio was hit with no shortfall.

### Eval harness (eval_harness.py) -- baseline established, before any training

```
python3 corpus/eval_harness.py --model qwen3.8:27b-mlx --n 15
```

From the FROZEN HOLDOUT (never selected/windowed above): mask a random
40x16 region, have a model fill it (RLE format, same prompt style as
training), decode the reply back into a cell grid, score
`half_block_pct`/`shade_pct` on the filled region against the real
ground truth, render both, and run a blind pairwise Opus judgment
(randomized A/B, no labels) asking which looks like more plausible
ANSI art. Includes a hard round-trip self-test (encode a random grid,
decode it, require an exact match) that runs FIRST and aborts if it
fails -- a scoring run means nothing if the encoder/decoder don't even
agree with each other.

**Real bugs found and fixed while building this**:
- The RLE decoder's `line.strip()` silently dropped a trailing literal
  SPACE glyph run at the end of a line (the same space-as-separator
  ambiguity documented above) -- caught by the round-trip self-test
  failing before ever trusting the decoder on real model output; fixed
  to `lstrip()` only.
- The first real eval call took **10+ minutes and generated 7,054
  decode iterations** for what should be a ~300-token answer, then
  came back with EMPTY content. Inspecting the raw Ollama response
  (not just the parsed text) found a separate `"thinking"` field
  containing a full chain-of-thought trace that consumed the entire
  token budget -- `qwen3.8:27b-mlx` is a Qwen3-family reasoning model;
  `harness.py`'s own `SAMPLING` dict documents "non-thinking mode" but
  that describes sampling PARAMETERS, not an actual mode switch.
  Confirmed via direct testing that Ollama's chat API has a separate
  top-level `"think": false` field that actually disables it -- fixed,
  plus an explicit `num_predict=800` hard ceiling as a backstop.
- A malformed model-generated grid crashed PIL's PNG encoder mid-batch
  (`"tile cannot extend outside image"`) on one real eval run -- wrapped
  rendering in try/except so one bad generation can't kill the whole
  eval batch.

**Baseline established with the untrained base model (qwen3.8:27b-mlx,
15 holdout examples, no 8B model currently pulled locally -- see
below)**:

| metric | model (untrained base) | ground truth |
|---|---|---|
| half_block_pct (mean) | 11.1 | 14.9 |
| shade_pct (mean) | 15.7 | 19.0 |
| pairwise vs. ground truth (blind Opus judgment) | won 6 / lost 8 / tied 0 (of 14 judged, 1 render error) | -- |

The untrained base model is already reasonably competitive (43% blind
win rate against real ground truth, on both mechanical metrics running
slightly below ground truth rather than wildly off) -- this is the
number any fine-tuned v1 needs to beat, not zero. Full per-example
detail in `corpus/eval_results.json`.

**Model size gap, reported honestly**: the user's stated preference for
v1 is an 8B base model ("iteration speed matters more than final
quality while we're finding out whether this works at all"). No 8B
model is currently pulled in this Ollama instance -- the smallest
available is `mistral-nemo:12b`. The eval harness is fully
model-agnostic (`--model <any-ollama-model>`); running it against a
real 8B requires pulling one first, not a code change.

## Step 3: hardened eval + LoRA training v1

**Re-baseline (user direction, 2026-09-19): "harden the eval... expand
to 50 holdout examples, and use larger masks... add a copy-detection
metric... keep per-example results."**

```
python3 corpus/eval_harness.py --model qwen3.8:27b-mlx --n 50 --out corpus/eval_results_hardened.json
```

Changes from the earlier 15-example baseline:
- **50 holdout examples** (up from 15), zero errors.
- **Larger, fixed-shape masks (~8x14 cells, +/-1 jitter)**, not the
  training-tuned 12-25%-area range -- deliberately harder than
  training, per instruction ("so the fill requires real construction,
  not interpolation"). Added `fixed_mask_size` to
  `windowing.make_fitm_example` for this rather than deriving mask
  shape from an area fraction, since the literal "14x8" target (a
  1.75:1 rectangle) is a genuinely different shape than what 20% area
  on a 40x16 (2.5:1) window naturally produces via the area-fraction
  formula (~7x18) -- verified directly before trusting it.
- **Copy-detection metric**: checks the filled region's edge rows/
  columns against their real adjacent neighbors for exact duplication
  (`copy_exact_frac`) and a softer per-cell overlap fraction
  (`copy_overlap_frac`), computed for BOTH the model's fill and the
  real ground truth (as a baseline for how much "duplication" is just
  normal repeating texture -- a fence, a brick wall -- that
  copy-detection can't distinguish from lazy copying on its own).
- **Per-example results kept**, not just aggregates -- full detail in
  `corpus/eval_results_hardened.json` for post-hoc analysis by piece
  type.

**Hardened baseline, untrained qwen3.8:27b-mlx, 50 holdout examples:**

| metric | model | ground truth |
|---|---|---|
| half_block_pct (mean) | 12.7 | 13.2 |
| shade_pct (mean) | 10.5 | 12.2 |
| copy_exact_frac (mean) | 0.045 | 0.118 |
| copy_overlap_frac (mean) | 0.295 | 0.507 |
| pairwise vs. ground truth (blind Opus) | won 20 / lost 26 / tied 0 (of 46 judged) | -- |

**Real, non-obvious finding**: the model copies LESS than real ground
truth does by this metric (0.045 vs 0.118 exact, 0.295 vs 0.507
overlap) -- real archive art legitimately repeats adjacent rows/
columns more often than the untrained model does (borders, brick-wall/
fence-style textures, repeating dither patterns are all genuine,
intentional repetition). This means a low copy-detection score alone
is NOT evidence of good construction -- it needs to be read against
this ground-truth baseline, not a fixed threshold. Pairwise win rate
(30%) is consistent with the earlier smaller-sample estimate (43%),
within the noise of a 46-comparison sample.

### Real bugs found while building/running the hardened eval

- The `mlx-lm` LoRA infrastructure setup surfaced along the way (see
  below) exposed that `grad_checkpoint=true` combined with validation-
  loss computation genuinely hangs (0% CPU, macOS reports the process
  STATE as literally "stuck") under the installed `mlx-lm` 0.29.1 --
  isolated via direct testing (disabling grad_checkpoint fixed it
  immediately; val_batches size wasn't the cause, contrary to the
  first hypothesis). Unrelated to eval_harness.py itself but found
  while validating the overall pipeline was healthy before training.

## Step 3: LoRA training v1 (mlx-lm)

**Base model for iteration speed**: `mlx-community/Mistral-Nemo-
Instruct-2407-4bit` (a real MLX-native quant of the same 12B model
already available via Ollama as `mistral-nemo:12b`, downloaded fresh
via `huggingface_hub.snapshot_download` since `mlx_lm` needs the MLX
weight format directly, not Ollama's own format). Per instruction,
this is the fast-iteration model for v1; the final run targets
`qwen3.8:27b-mlx` so the trained adapter can drop directly into raze's
own seat.

**Hyperparameters** (`corpus/lora_config.yaml`): rank 16, scale 2.0
(alpha 32 / rank 16 -- `mlx_lm`'s config uses `rank`+`scale`, not
`rank`+`alpha` directly), lr 1e-5, ~3,000 iterations on the 40k
subsample, `--mask-prompt` so loss only counts the FITM target (not
the context), checkpoints every 500 steps.

**Data prep** (`corpus/prepare_training_data.py`): converts
`train_subsample.jsonl` into `mlx_lm`'s expected chat-messages JSONL
format (train/valid/test split: 38,000 / 1,200 / 800), embedding SAUCE
year/group + per-window technique metrics as conditioning text in the
prompt (captions dropped from v1, per prior direction).

### Real bugs found and fixed before training could run

1. **A genuine bug in `mlx_lm` 0.29.1's own `CompletionsDataset`
   class**: its `--mask-prompt` code path calls
   `tokenizer.apply_chat_template(messages[0], ...)`, passing a bare
   dict instead of a single-element list -- crashes immediately on
   Mistral's chat template with `jinja2.exceptions.UndefinedError:
   dict object has no element 0` (the template tries to iterate the
   dict as if it were a list of messages). Confirmed this is upstream
   library code, not a mistake in my own data format, by reading
   `mlx_lm/tuner/datasets.py` directly. Worked around by using the
   `messages`-format `ChatDataset` path instead of `prompt`/
   `completion` (`ChatDataset.process` uses `messages[:-1]`, a real
   list slice, which doesn't hit this bug) -- verified end-to-end
   before committing to it.
2. **`grad_checkpoint=true` + validation hangs indefinitely.** First
   observed as a real Metal OOM crash during a concurrent test run (a
   50-example eval_harness.py run sharing the same GPU); investigated
   further and found the crash recurred even in complete isolation.
   Bisected step by step: model loads and runs a single long forward
   pass fine (6.8s for a real 3,221-token example); `val_batches=0`
   trains cleanly; `val_batches=1` and `val_batches=4` both complete
   cleanly WITHOUT `grad_checkpoint`; `grad_checkpoint=true` with ANY
   validation never completes even one batch (0% CPU, process state
   "stuck", 3+ minutes with zero progress). Fixed by disabling
   `grad_checkpoint` -- peak memory without it measured at 35.4GB on a
   real training step, comfortably within this machine's 64GB, so its
   memory savings aren't needed here anyway.
3. **`val_batches=25` (the original production value) completes but
   leaves too little memory headroom for the next training step**,
   causing a real Metal OOM crash immediately after a successful
   25-batch validation pass (393s, real val loss 0.786). Reduced to
   `val_batches=8` -- a real, deliberate memory/thoroughness tradeoff,
   not an arbitrary number.

Config verified end-to-end at full production `batch_size`/
`max_seq_length` settings (just `grad_checkpoint` and `val_batches`
changed) before launching the real 3,000-iteration run.

## Step 2: captioning (caption.py) -- DROPPED FROM v1

Per user direction, 2026-09-19: "Drop captioning from v1. Kill the
300-piece job. FIM doesn't need captions. Condition each example on
SAUCE year + group + the technique metrics... Captions return in a
later phase if prompt-conditioning is needed." The 300-piece sample
job in progress was killed mid-run (no output file was ever produced).
`caption.py` itself is kept, unmodified, for the later phase mentioned
above -- it is NOT part of the v1 windowing/training pipeline.

For reference, the real findings from before it was dropped: captions
were roughly accurate when spot-checked against real renders, but
measured throughput was ~26s/caption end-to-end, meaning full coverage
of ~35k unique pieces would take on the order of 250 hours of
continuous local inference -- a real, sizeable cost that was the
practical reason this got reprioritized out of v1, not just the
architectural "FIM doesn't need it" argument.

## Real bugs found and fixed via validation (not assumed, not guessed)

Every fix below was found by an actual mismatch against a real ansilove
render or a real full-archive run, root-caused with a targeted test
case, then verified fixed:

1. **GitHub Contents API doesn't paginate a directory** -- an early
   version of fetch.py assumed standard pagination and looped forever
   re-fetching the same 778-item page for a large year.
2. **SAUCE 0x1A (EOF) is a hard stop, not a SAUCE-specific rule.**
   ansilove renders nothing at or after the first bare 0x1A byte in a
   file, independent of whether a SAUCE record follows it -- confirmed
   with `'ABC' + 0x1A + 'DEF'` rendering only `'ABC'`.
3. **Trailing blank rows are trimmed, ALL of them, not just one.**
   ansilove trims every consecutive wholly-empty row at the true end of
   a file. Checked across 500 real files: 12% have 2+ trailing blank
   rows (deliberate whitespace framing before EOF).
4. **ESC[A/B/C/D/H/f/s/u**: `ESC[s`/`ESC[u` (save/restore cursor
   position) were completely unhandled in the first version -- found
   extremely common in the real archive (12221 + 4551 occurrences in a
   500-file sample) and caused real 2-8 row divergences on files that
   rely on it for column-by-column drawing technique.
5. **End-of-line wrap is IMMEDIATE in ansilove, not deferred.** Filling
   column 80 then hitting an explicit `\r\n` produces TWO row advances
   (the auto-wrap AND the newline), not one -- the opposite of the
   deferred-wrap convention `~/agentscii/harness.py`'s own renderer uses
   (a deliberate, unrelated choice for agent-authored files, not changed
   here). Verified with a minimal test file and cross-checked against a
   real archive file's own `ESC[A` cursor-up compensation pattern.
6. **`ESC[nC` (cursor-forward) wraps to the next row at column 0 when it
   would overflow column 80** -- it does NOT clamp to column 79. Found
   on a real file drawn as a single 9KB line with zero literal newlines,
   using only cursor-forward moves.
7. Two `█` (full-block)-specific validator bugs: the corner-sampling
   bg-color check must compare against the glyph's OWN foreground color
   for `█` (it fills the whole cell, corners included), not background;
   and a cell with `fg == bg` is legitimately, correctly indistinguishable
   from "no glyph" by any pixel test (a real, deliberate flat-fill
   technique) -- excluded from the glyph-presence check rather than
   guessing a pixel threshold.
8. CP437 codepoint `0x00` (NUL) is a genuinely blank glyph in the font,
   distinct from space (`0x20`) but visually identical -- both must be
   excluded from the "expects a glyph" check.
9. **`parse.py` output naming collided on same-stem/different-extension
   pairs** (`NAME.ANS` + `NAME.ASC` in one pack, real different content):
   both mapped to `NAME.npz`, silently overwriting one file's parsed
   output with the other's. Found while computing exact corpus counts
   for a status report (3,905-file sample dropped to 3,883 `.npz` files
   -- the gap was the tell). Fixed by including the source extension in
   the output name (`NAME.ANS.npz` / `NAME.ASC.npz`); confirmed zero
   remaining collisions across the full 86,093-file corpus after the fix.
10. **Uncaught `zlib.error` killed a full 37-year fetch run** ~1000 packs
    / ~13,000 files in, on a single corrupted deflate stream inside one
    real 1995 pack zip (`"invalid distance too far back"`) -- raised as
    a bare `zlib.error`, not wrapped in `zipfile.BadZipFile`, so the
    existing per-member exception handling didn't catch it. Fixed by
    adding `zlib.error`/`EOFError` to the caught set, plus a second,
    broader per-pack try/except in `main()`'s loop as a backstop against
    any other unanticipated failure mode in a 4,800+-pack real archive.
    Also added an idempotent skip (pack output dir already has files ->
    don't re-extract) so a resumed run after a crash can't create `__2`
    duplicate-suffixed copies of files it already extracted correctly.

## Known open gap (documented, not fixed)

TAB sequences landing within ~10 columns of the right margin have a
narrow, not-fully-characterized divergence from ansilove's exact
behavior (see `parse.py`'s `Grid.tab()` docstring). Measured impact:
~0.2% of cells across the validation samples. Left open for step 1 as a
documented, bounded gap rather than continuing to reverse-engineer
ansilove's TAB internals by trial and error -- revisit if a larger
validation sample shows this at a materially higher rate.
