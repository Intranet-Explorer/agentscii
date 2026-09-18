# AGENTSCII corpus (step 1: fetch + parse + validate)

A local, disk-only ANSI/ASCII training corpus built from 16colo.rs's real
archive (via the `sixteencolors/sixteencolors-archive` GitHub mirror), for
future reference-corpus/LoRA work. **Nothing in this directory except the
three `.py` scripts is tracked in git or pushed anywhere** -- see the
repo-root `.gitignore`. `corpus/data/`, `corpus/raw/`, `corpus/parsed/`,
and the validation reports are real other-artists'-work / derived data,
kept local only, same rationale as `workspace/references/study/`.

## Pipeline

```
fetch.py   -> downloads pack .zips by year, extracts .ans/.asc  -> corpus/data/
parse.py   -> parses each file into a cell-grid .npz            -> corpus/parsed/
validate.py -> renders N random files with ansilove, diffs cell-by-cell
```

### fetch.py

```
python3 corpus/fetch.py --years 1996 1997 --limit-per-year 50 --max-size-mb 10
python3 corpus/fetch.py --years all
```

Uses the GitHub Contents API (one request per year -- confirmed live that
the API does NOT paginate a directory listing, it returns everything in
one response) plus the `gh` CLI's own token if logged in (avoids the
unauthenticated 60 req/hr rate limit). Resumable: re-running skips
already-downloaded pack zips.

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
one `.npz` per input file with `chars`/`fg`/`bg` arrays plus SAUCE metadata.

Parsed 3905/3905 real archive files with zero crashes (100% success rate)
across 9 years (1994-2023) sampled from the archive.

### validate.py

```
python3 corpus/validate.py --n 200 --seed 0
```

Renders N random files with real `ansilove` and diffs parse.py's output
against it cell-by-cell (bg color via corner sampling, glyph presence via
non-background pixel detection, row/col count). **Two independent 200-file
runs (seed=0, seed=42): 199/200 and 192/200 clean (99.5%, 96%)**, zero
crashes in either run.

## Real bugs found and fixed via validation (not assumed, not guessed)

Every fix below was found by an actual mismatch against a real ansilove
render, root-caused with a targeted test file, then verified fixed:

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

## Known open gap (documented, not fixed)

TAB sequences landing within ~10 columns of the right margin have a
narrow, not-fully-characterized divergence from ansilove's exact
behavior (see `parse.py`'s `Grid.tab()` docstring). Measured impact:
~0.2% of cells across the validation samples. Left open for step 1 as a
documented, bounded gap rather than continuing to reverse-engineer
ansilove's TAB internals by trial and error -- revisit if a larger
validation sample shows this at a materially higher rate.
