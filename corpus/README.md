# AGENTSCII corpus

A local ANSI/ASCII corpus built from the 16colo.rs archive (via the
`sixteencolors/sixteencolors-archive` GitHub mirror). It feeds two
things: the retrieval index behind the agents' `find_patches` tool, and
LoRA training experiments.

Only the scripts are in this repo. The downloaded packs, parsed grids,
indexes, manifests, training data and adapters are other artists' work
or derived from it. They stay local and are excluded by `.gitignore`.

## Scripts

Corpus build:

```
fetch.py              download pack zips by year, extract .ans/.asc      -> data/
parse.py              parse each file into a chars/fg/bg cell grid (.npz) -> parsed/
validate.py           render random files with ansilove, diff cell by cell
dedupe.py             content-hash parsed grids, map cross-pack duplicates
technique_index.py    per-piece shading metrics                           -> technique_manifest.jsonl
technique_report.py   distribution report over the manifest
holdout.py            frozen, dedup-aware train/holdout split             -> holdout_split.json
score_shipped.py      score shipped AGENTSCII pieces against the corpus distribution
```

Encoding and training data:

```
windowing.py          40x16 windows, RLE encoding, fill-in-the-middle examples -> windows.jsonl
token_stats.py        token-length stats over windows.jsonl
bench_encoding.py     tokens-per-cell benchmark across three cell encodings
subsample.py          stratified 40k-example training subsample
scan_pathologies.py   find empty, single-glyph and over-length examples
filter_dataset.py     drop those examples from the subsample
prepare_training_data.py  convert the subsample to mlx_lm chat format
flat_shaded_pairs.py  flat -> shaded pair generator (sample output)
build_flat_shaded_dataset.py  flat -> shaded training set in mlx_lm chat format
caption.py            per-piece captions via a local VLM (not used in training)
```

Training and evaluation:

```
train_launch.py       mlx_lm LoRA launcher: fp32 loss, NaN halt, watchdogs
mem_watchdog.py       kill training on swap/free-memory thresholds
mem_logger.py         log RSS, free memory and swap for a pid
progress_watchdog.py  capture a stack sample if the training log stalls
mem_growth_test.py    measure MLX cache growth across training steps
eval_harness.py       FIM eval on the holdout via Ollama: fill, score, copy-detect, blind pairwise judge
checkpoint_eval.py    same eval against an mlx_lm base model + adapter checkpoint, with renders
generate_region.py    mask a region of an existing piece, fill with an adapter, splice, render
eval_on_raze.py       run a flat -> shaded adapter over house pieces, render side by side
```

Retrieval:

```
patch_index.py        SQLite index over windows.jsonl technique metrics  -> patch_index.db
patch_meta.py         add SAUCE title/author/group/year to patch_index.db
find_patches.py       technique-filter and text-described retrieval over patch_index.db
build_clip_index.py   render windows to PNG, embed with CLIP             -> clip_index/
build_highcraft_index.py  filtered sibling index                         -> clip_index_highcraft/
find_patches_clip.py  CLIP text-to-image nearest-neighbor retrieval
```

## Running

```
python3 corpus/fetch.py --years all
python3 corpus/fetch.py --years 1996 1997 --limit-per-year 50   # small sample
python3 corpus/parse.py --input-dir corpus/data --output-dir corpus/parsed
python3 corpus/parse.py --file corpus/data/<year>/<pack>/<FILE>.ANS   # one file
python3 corpus/validate.py --n 200 --seed 0
python3 corpus/dedupe.py
python3 corpus/technique_index.py
python3 corpus/technique_report.py
python3 corpus/holdout.py --fraction 0.05 --seed 0
python3 corpus/score_shipped.py

python3 corpus/windowing.py
python3 corpus/token_stats.py
python3 corpus/bench_encoding.py
python3 corpus/subsample.py --n 40000
python3 corpus/scan_pathologies.py
python3 corpus/filter_dataset.py
python3 corpus/prepare_training_data.py
python3 corpus/build_flat_shaded_dataset.py

python3 corpus/train_launch.py -c corpus/lora_config.yaml
python3 corpus/eval_harness.py --model qwen3.8:27b-mlx --n 50
python3 corpus/checkpoint_eval.py --adapter-path <ckpt> --n 15 --checkpoint-label iter500
python3 corpus/generate_region.py --adapter-path <ckpt> --piece <year>/<pack>/<FILE>.ANS.npz
python3 corpus/eval_on_raze.py --adapter-path <ckpt> --piece <path.ans>

python3 corpus/patch_index.py
python3 corpus/patch_meta.py
python3 corpus/build_clip_index.py
python3 corpus/build_highcraft_index.py
python3 corpus/find_patches_clip.py "dense half-block dithered sky" --n 5
```

`fetch.py` uses the GitHub Contents API with the `gh` CLI token when
available, and is resumable. `train_launch.py` stops the harness and
Ollama and starts the watchdogs itself; `lora_config.yaml` is local.

## Numbers

- 86,093 `.ans`/`.asc` files from 4,832 packs, every year 16colo.rs
  covers (1990 onward). All parse without error.
- 81,468 unique pieces by content hash of the chars/fg/bg grid. The
  rest are cross-pack re-releases.
- Parser agreement with ansilove: 589 of 600 files clean (98.2%) across
  three random 200-file samples.
- Holdout: 5% of unique pieces (4,073), frozen before any training.
  The split is on content hash, so a piece and its re-releases always
  land on the same side.

## Parser

`parse.py` reads CP437, strips SAUCE and keeps its metadata, and handles
SGR (bold, blink, iCE colors), cursor movement (`ESC[A/B/C/D/H/f/s/u`),
TAB and 80-column wrap. Behavior matches ansilove, not the spec:
rendering stops at the first 0x1A, all trailing blank rows are trimmed,
wrap at column 80 is immediate, and cursor-forward past column 80 wraps
to the next row. Output is one `.npz` per file, named with the source
extension (`NAME.ANS.npz`). TAB near the right margin still diverges
slightly from ansilove (about 0.2% of cells).

## Encoding

Windows are 40 columns by 16 rows with 50% overlap in both directions.
Pieces smaller than a window are padded with background. Training
windows come from the train split only, filtered to shading-heavy
pieces with little text, with the heaviest-shaded tier oversampled.

Each row is run-length encoded:

```
r00 14,90:▄ 15,90:█ 16,10:██████ 62,90:█ 63,90:▄▄▄
```

`r{row} {col},{fg}{bg}:{glyphs}`, one run per span of identical glyph
and color, colors as two hex digits. Background runs are omitted. On the
cl100k tokenizer this costs about 2 tokens per cell, cheaper than a
plain per-cell encoding (3.4) or one private-use codepoint per cell
(4.1).

Fill-in-the-middle examples mask a rectangle of 12-25% of the window,
marked inline with `[MASK w=N]`. The target is the masked content,
RLE-encoded in local coordinates. Conditioning is SAUCE year and group
plus per-window shading metrics. Typical examples run about 1,200
context tokens and 300 target tokens.

## Retrieval

`patch_index.db` holds technique metrics and SAUCE metadata for every
window. The CLIP index renders about 850k windows to PNG and embeds
them with open_clip ViT-B/32; a query is embedded with the matching
text tower and matched by cosine similarity, with optional
half-block/shade floors. The high-craft index is a filtered subset of
the same embeddings (upper technique tier or modern-era work). Each hit
returns the cell grid sliced from the parent piece, plus a patch id
the agents pass to `canvas_stamp`.

## Results

Two LoRA objectives were trained on a 12B base with mlx_lm. Both runs
were short.

- **Fill-in-the-middle** learned texture without structure. Fills
  matched the local shading statistics of the surrounding window but
  did not construct forms, edges or content.
- **Flat to shaded** (input: the window with shaded regions flattened
  to their dominant color; target: the original) learned to copy its
  input. Most cells are identical between input and target, so the
  loss rewards reproduction over shading.

The copy problem needs the loss masked to cells that change between
input and target.
