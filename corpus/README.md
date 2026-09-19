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
windowing.py         -> step 2: 80x24 windows, RLE encoding, fill-in-the-middle examples -> windows.jsonl
token_stats.py       -> token-length stats over windows.jsonl
caption.py           -> per-parent-piece caption via local VLM + SAUCE year/group prefix -> captions.json
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

80x24 windows, 50% row overlap (12-row stride). **20,245 of the 55,161
selected piece-instances (37%) were too short (<24 rows) to yield even
one window** -- a real, material fraction of the shading-heavy subset
is short-form pieces (banners, small logos) rather than full-canvas
art; not fixed here since a genuinely 18-row piece can't be padded into
a meaningful 24-row context without inventing content, flagged rather
than worked around. Final count: **264,947 windows across 34,916
pieces yielded at least one window.**

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

### Fill-in-the-middle (FITM)

Each window gets one FITM example: a random rectangle (20-40% of
window area) is masked in the CONTEXT (marked with an explicit `MASK
at row=R col=C h=H w=W` line, real background cells left alone so the
model can't confuse "masked" with "empty"), and the TARGET is that
rectangle's real original content, RLE-encoded on its own local
coordinate system.

### Token stats (tiktoken cl100k_base, full 264,947 windows -- exact, not sampled)

| | mean | median | p90 | p99 | max |
|---|---|---|---|---|---|
| context tokens | 5,003 | 4,992 | 6,792 | 8,243 | 12,073 |
| target tokens | 1,501 | 1,472 | 2,454 | 3,310 | 5,398 |
| context+target tokens | 6,503 | 6,493 | 9,020 | 11,101 | 16,121 |

chars-per-token (context): 0.89 -- **the RLE format tokenizes WORSE
than 1 char/token** under a standard BPE vocabulary (cl100k_base
wasn't trained on dense box-drawing/block Unicode, so each glyph often
costs more than one token) -- a real cost of this encoding worth
weighing against its cell-count compression before committing to it
for training, not assumed free.

## Step 2: captioning (caption.py)

```
python3 corpus/caption.py
```

For each window's parent piece: render via real `ansilove` (CP437,
correct for real archive files), one call to the local VLM
(`qwen3.8:27b-mlx` via Ollama) asking for a plain, un-opinionated
description, prefixed with `[year / group]` from SAUCE metadata
(falling back to the year directory in the parsed path when a file has
no SAUCE record, common in early-90s packs). One caption per unique
parent piece, not per window, since many windows share a parent.

**Real captions produced, verified by eye against their actual
renders** -- e.g. `[1990] This is a pixel-art portrait... depicting a
woman with voluminous bright red hair... rendered with chunky, blocky
pixels in a limited palette` for a real 1990 face portrait. Roughly
right, not exact -- matches the "caption quality only needs to be
roughly right" instruction.

**Honest throughput finding: measured ~26 seconds per caption
end-to-end** (render + local VLM inference) on this machine. Full
coverage of all 34,916 unique parent pieces would take roughly **252
hours** of continuous local inference -- not run to completion.
`captions_sample.json` has a real 300-piece sample (~2.2 hours) to
validate the pipeline and caption quality; captioning the full training
set is a real, sizeable compute cost to plan for before step 3, not
a quick script run.

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
