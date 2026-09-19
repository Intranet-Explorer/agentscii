#!/usr/bin/env python3
"""corpus/windowing.py -- step 2: slice train-split pieces into 40x16
windows with overlap, RLE-encode rows, and build fill-in-the-middle
(FITM) examples. Conditioning is SAUCE year + group + per-window
technique metrics (half_block_pct, shade_pct, shade_bucket) -- NOT a
caption (dropped from v1, user direction 2026-09-19: "FIM doesn't need
captions... captions return in a later phase if prompt-conditioning is
needed").

Window size (user direction, 2026-09-19): "shrink the window, 40 cols
x 16 rows, not 80x24." At 40 cols, a window covers only half the width
of a typical 80-col real archive piece, so real column tiling is now
used (COL_OVERLAP), not just row tiling with column pad/trim.

Selection (user direction, 2026-09-19): train on the H=30/S=15 subset
(half_block_pct > 30 OR shade_pct > 15, AND alnum_pct < 15, AND
distinct_colors >= 4), oversample the p90 tier (H=36.8/S=38.3, same
filters) ~3x so the model sees more heavily shaded work. Only pieces on
the TRAIN side of holdout_split.json are ever windowed -- holdout is
never touched here.

RLE row encoding (user direction): "not raw cells... run-length
(r00 4,0:###)". The user's example is illustrative shorthand, not a
literal spec -- documented interpretation used here, shown against
real output below so it's inspectable/correctable:

    r00 4,3a:▄▄▄ 12,07:██

  - "r00"        row index within the window, zero-padded to 2 digits
  - "4,3a:▄▄▄"   a RUN starting at column 4, color code "3a" (hex nibble
                 pair: fg=3, bg=a=10), glyphs "▄▄▄" written LITERALLY
                 (not count-compressed) so the model sees real glyph
                 identity, not just a run length
  - runs are space-separated; a run ends where (char,fg,bg) changes
  - fully-blank runs (space, bg=0) are OMITTED entirely (not encoded
    as an explicit "empty" run) -- most of a typical window's runs are
    blank background, and skipping them is the actual compression this
    format buys over raw cells
  - "color code" packs BOTH fg and bg as two hex digits (fg then bg),
    not a single index -- chosen over the literal 1-digit example
    because a single index alone can't represent a colored glyph on a
    colored background without silently dropping the background, which
    is real information a training target needs. Consistent with using
    the FULL cell tuple, just compactly.

Usage:
    python3 corpus/windowing.py [--limit-pieces N] [--out corpus/windows.jsonl]
"""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent

WINDOW_ROWS = 16
WINDOW_COLS = 40
ROW_OVERLAP = 8    # 50% overlap on rows
COL_OVERLAP = 20   # 50% overlap on cols -- user direction, 2026-09-19: "shrink the window, 40 cols x 16 rows, not 80x24"

# Selection thresholds -- user direction, 2026-09-19
H_THRESH = 30.0
S_THRESH = 15.0
H_P90 = 36.8
S_P90 = 38.3
ALNUM_MAX = 15.0
COLORS_MIN = 4
OVERSAMPLE_P90 = 3


def rle_encode_row_runs(row_chars, row_fg, row_bg):
    """One row -> list of (start_col, color_code, glyphs) run tuples.
    Runs of identical (char,fg,bg) are merged; true-background runs
    (space, bg=0) are omitted entirely. Structured form used both by
    rle_encode_row (joins into the final string) and by
    make_fitm_example's column-shift logic, which needs real
    structured runs -- NOT a naive str.split(' ') re-parse of the
    joined string, which is ambiguous and breaks: a run of literal
    SPACE glyphs on a colored background (a real, valid case -- e.g.
    a solid color block with no visible character) contains the same
    ' ' character used as the inter-run separator, so splitting on
    space silently shreds that run's glyph content into garbage
    tokens. Caught live via a real crash, not by inspection."""
    runs = []
    n = len(row_chars)
    i = 0
    while i < n:
        ch, fg, bg = row_chars[i], row_fg[i], row_bg[i]
        j = i + 1
        while j < n and row_chars[j] == ch and row_fg[j] == fg and row_bg[j] == bg:
            j += 1
        run_len = j - i
        if not (ch == " " and bg == 0):
            color_code = f"{fg:x}{bg:x}"
            glyphs = ch * run_len
            runs.append((i, color_code, glyphs))
        i = j
    return runs


def rle_encode_row(row_chars, row_fg, row_bg):
    """One row -> 'run run run...' string (row prefix added by caller).
    Runs of identical (char,fg,bg) are merged; true-background runs
    (space, bg=0) are omitted entirely."""
    runs = rle_encode_row_runs(row_chars, row_fg, row_bg)
    return " ".join(f"{col},{color}:{glyphs}" for col, color, glyphs in runs)


def encode_window(chars_grid, fg_grid, bg_grid):
    """A (rows, cols) window -> multi-line RLE text, one 'rNN ...' line
    per row that has at least one non-blank run. Fully-blank rows are
    omitted (same reasoning as blank runs within a row)."""
    lines = []
    for r in range(chars_grid.shape[0]):
        row_chars = [chr(cp) for cp in chars_grid[r].tolist()]
        row_fg = fg_grid[r].tolist()
        row_bg = bg_grid[r].tolist()
        body = rle_encode_row(row_chars, row_fg, row_bg)
        if body:
            lines.append(f"r{r:02d} {body}")
    return "\n".join(lines)


def select_pieces(train_paths_set):
    """Apply the H=30/S=15 selection + p90 oversampling, restricted to
    the train split. Returns a list of relative .npz paths, with p90
    pieces appearing OVERSAMPLE_P90 times (so downstream windowing
    naturally sees them more often)."""
    base = []
    p90 = []
    with open(CORPUS_DIR / "technique_manifest.jsonl") as f:
        for line in f:
            row = json.loads(line)
            path = row["path"]
            if path not in train_paths_set:
                continue
            if row["alnum_pct"] >= ALNUM_MAX or row["distinct_colors"] < COLORS_MIN:
                continue
            is_base = row["half_block_pct"] > H_THRESH or row["shade_pct"] > S_THRESH
            if not is_base:
                continue
            base.append(path)
            is_p90 = row["half_block_pct"] > H_P90 or row["shade_pct"] > S_P90
            if is_p90:
                p90.append(path)
    selected = list(base)
    for _ in range(OVERSAMPLE_P90 - 1):
        selected.extend(p90)
    return selected, len(base), len(p90)


def make_windows(chars, fg, bg):
    """Slide a WINDOW_ROWS x WINDOW_COLS window over a full piece grid
    with ROW_OVERLAP/COL_OVERLAP overlap in each dimension. At the
    smaller 40x16 window size (user direction, 2026-09-19: "shrink the
    window, 40 cols x 16 rows, not 80x24"), a window only covers HALF
    the width of a typical 80-col real archive piece -- real column
    tiling is now required, not just row tiling with column pad/trim
    like the original 80-col-window version used (a single window at
    the old 80-col width WAS the whole canvas width, so no column
    tiling was ever needed there). Pieces narrower than WINDOW_COLS or
    shorter than WINDOW_ROWS are padded with true background rather
    than skipped, since a real 40x16 window is small enough that many
    genuinely valid narrow/short pieces would otherwise be discarded
    entirely (unlike the old 80x24 case, where a piece shorter than the
    window was almost always a near-empty banner not worth training on
    anyway)."""
    n_rows, n_cols = chars.shape

    def _tile_starts(total, window, overlap):
        stride = window - overlap
        starts = []
        pos = 0
        while pos + window <= total:
            starts.append(pos)
            pos += stride
        if not starts:
            starts = [0]
        elif starts[-1] + window < total:
            # one final window flush against the far edge, so trailing
            # content isn't always dropped just for not landing on a
            # stride boundary
            starts.append(total - window)
        return starts

    row_starts = _tile_starts(max(n_rows, WINDOW_ROWS), WINDOW_ROWS, ROW_OVERLAP)
    col_starts = _tile_starts(max(n_cols, WINDOW_COLS), WINDOW_COLS, COL_OVERLAP)

    for row in row_starts:
        for col in col_starts:
            row_end = min(row + WINDOW_ROWS, n_rows)
            col_end = min(col + WINDOW_COLS, n_cols)
            c_slice = chars[row:row_end, col:col_end]
            f_slice = fg[row:row_end, col:col_end]
            b_slice = bg[row:row_end, col:col_end]
            pad_h = WINDOW_ROWS - c_slice.shape[0]
            pad_w = WINDOW_COLS - c_slice.shape[1]
            if pad_h > 0 or pad_w > 0:
                c_slice = np.pad(c_slice, ((0, pad_h), (0, pad_w)), constant_values=0x20)
                f_slice = np.pad(f_slice, ((0, pad_h), (0, pad_w)), constant_values=7)
                b_slice = np.pad(b_slice, ((0, pad_h), (0, pad_w)), constant_values=0)
            yield (row, col), c_slice, f_slice, b_slice


def make_fitm_example(chars, fg, bg, rng, area_frac_range=None, fixed_mask_size=None):
    """Mask a random rectangle inside the window; context = the window
    with that rectangle blanked to true background; target = the
    rectangle's real original content, RLE-encoded on its own
    coordinate system (row/col relative to the rectangle, not the
    window) so the target is self-contained.

    area_frac_range overrides the default mask-size range -- used by
    eval_harness.py with a LARGER range than training (user direction,
    2026-09-19: "use larger masks: roughly 14x8 cells or ~20% of the
    subject area, so the fill requires real construction, not
    interpolation" -- a harder eval than the ~300-token-tuned training
    mask size, deliberately, since the training-size mask is easy
    enough to interpolate from adjacent context rather than requiring
    real construction).

    fixed_mask_size=(mask_h, mask_w) pins the mask to a specific shape
    with +/-1 cell jitter per dimension, rather than deriving mask_h/
    mask_w from area_frac via the WINDOW's own aspect ratio (40:16 =
    2.5:1) -- the user's literal "14x8" target is a 1.75:1 rectangle,
    a genuinely different shape than what area_frac alone would
    produce at the same cell count (verified directly: 20% area_frac
    on a 40x16 window naturally comes out ~7x18, not ~8x14)."""
    h, w = chars.shape
    if fixed_mask_size:
        base_h, base_w = fixed_mask_size
        mask_h = max(3, min(h - 1, base_h + rng.randint(-1, 1)))
        mask_w = max(3, min(w - 1, base_w + rng.randint(-1, 1)))
    else:
        # mask rectangle: 12-25% of window area (tuned down from an initial
        # 20-40%, user direction, 2026-09-19: "target under ~300 tokens" --
        # 20-40% measured at a real mean of 461 target tokens on a 10k
        # sample, well over the target; 12-25% is the range that actually
        # lands near it, verified below), clamped to sane min size
        lo, hi = area_frac_range if area_frac_range else (0.12, 0.25)
        area_frac = rng.uniform(lo, hi)
        target_area = area_frac * h * w
        mask_h = max(3, min(h - 1, round((target_area * h / w) ** 0.5)))
        mask_w = max(3, min(w - 1, round((target_area * w / h) ** 0.5)))
    top = rng.randint(0, h - mask_h)
    left = rng.randint(0, w - mask_w)

    # For rows that intersect the masked band, encode the real content
    # to the LEFT and RIGHT of the masked column range normally, with
    # an explicit "[MASK]" token standing in for the masked span
    # itself -- NOT a private-use sentinel glyph written into the grid
    # and RLE-encoded like real content. Found live building this: an
    # earlier version did exactly that (U+E000 written into the grid,
    # encoded like any other glyph) -- it "worked" in the sense that
    # nothing crashed, but wasted real tokens on runs of an invisible,
    # rarely-trained-on codepoint, and an earlier version of THIS fix
    # blanked the masked rows' ENTIRE width (not just the masked
    # columns), silently discarding real, visible context on either
    # side of the hole within those rows -- caught by inspecting a
    # real example before trusting it, not assumed correct.
    lines = []
    for r in range(h):
        row_chars = [chr(cp) for cp in chars[r].tolist()]
        row_fg = fg[r].tolist()
        row_bg = bg[r].tolist()
        if top <= r < top + mask_h:
            left_body = rle_encode_row(row_chars[:left], row_fg[:left], row_bg[:left])
            right_runs = rle_encode_row_runs(
                row_chars[left + mask_w:], row_fg[left + mask_w:], row_bg[left + mask_w:]
            )
            # re-offset the right-hand run's column indices back to the
            # window's real coordinate system (rle_encode_row_runs was
            # given a slice starting at 0, not `left + mask_w`) --
            # working with structured (col, color, glyphs) tuples here,
            # not re-parsing a joined string (see rle_encode_row_runs's
            # docstring for the real bug that caused).
            right_body = " ".join(
                f"{col + left + mask_w},{color}:{glyphs}" for col, color, glyphs in right_runs
            )
            body_parts = [p for p in (left_body, f"[MASK w={mask_w}]", right_body) if p]
            body = " ".join(body_parts)
        else:
            body = rle_encode_row(row_chars, row_fg, row_bg)
        if body:
            lines.append(f"r{r:02d} {body}")
    lines.insert(0, f"MASK rows {top}-{top + mask_h - 1} cols {left}-{left + mask_w - 1}")
    context_text = "\n".join(lines)

    target_chars = chars[top:top + mask_h, left:left + mask_w]
    target_fg = fg[top:top + mask_h, left:left + mask_w]
    target_bg = bg[top:top + mask_h, left:left + mask_w]
    target_text = encode_window(target_chars, target_fg, target_bg)

    return context_text, target_text, (top, left, mask_h, mask_w)


_HALF_BLOCK_CP = {0x2580, 0x2584}  # ▀ ▄ -- matches technique_index.py/harness.py's corpus-aligned definition
_SHADE_CP = {0x2591, 0x2592, 0x2593}  # ░ ▒ ▓


def window_technique_metrics(chars, fg, bg):
    """Subject-only half_block_pct/shade_pct for ONE window (not the
    parent piece) -- user direction, 2026-09-19: 'condition each
    example on SAUCE year + group + the technique metrics
    (half_block_pct, shade_pct bucket).' Same glyph set/denominator as
    corpus/technique_index.py and harness.py's _compute_piece_metrics
    (kept in sync deliberately, see harness.py's own comment on this)."""
    is_space = (chars == 0x20)
    is_true_bg = is_space & (bg == 0)
    subject_mask = ~is_true_bg
    subject_cells = int(subject_mask.sum())
    if subject_cells == 0:
        return 0.0, 0.0
    subj_chars = chars[subject_mask]
    half_ct = sum(1 for cp in subj_chars.tolist() if cp in _HALF_BLOCK_CP)
    shade_ct = sum(1 for cp in subj_chars.tolist() if cp in _SHADE_CP)
    return 100.0 * half_ct / subject_cells, 100.0 * shade_ct / subject_cells


def shade_bucket(half_pct, shade_pct):
    """Coarse bucket label for conditioning, derived from the same
    H=30/S=15 and p90=36.8/38.3 thresholds already used for selection
    -- 'low' / 'mid' (base tier) / 'high' (p90 tier), so the model
    (or a downstream classifier) has a categorical signal alongside
    the raw percentages."""
    if half_pct > H_P90 or shade_pct > S_P90:
        return "high"
    if half_pct > H_THRESH or shade_pct > S_THRESH:
        return "mid"
    return "low"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--holdout-split", default=str(CORPUS_DIR / "holdout_split.json"))
    ap.add_argument("--out", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--limit-pieces", type=int, default=None,
                     help="cap number of (deduped, pre-oversample) pieces processed, for a quick test run")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    split = json.loads(Path(args.holdout_split).read_text())
    train_paths_set = set(split["train_paths"])

    selected, n_base, n_p90 = select_pieces(train_paths_set)
    print(f"Base selection (H>{H_THRESH} OR S>{S_THRESH}, alnum<{ALNUM_MAX}, colors>={COLORS_MIN}): {n_base} pieces")
    print(f"p90 tier within that ({H_P90}/{S_P90}): {n_p90} pieces, oversampled {OVERSAMPLE_P90}x")
    print(f"Total selected (with oversampling, includes duplicates by design): {len(selected)}")

    if args.limit_pieces:
        # apply the limit to UNIQUE pieces, then let their oversample
        # copies ride along, so a quick test run still exercises the
        # oversampling logic instead of silently disabling it
        unique_order = []
        seen = set()
        for p in selected:
            if p not in seen:
                seen.add(p)
                unique_order.append(p)
            if len(unique_order) >= args.limit_pieces:
                break
        allowed = set(unique_order)
        selected = [p for p in selected if p in allowed]
        print(f"--limit-pieces {args.limit_pieces}: restricted to {len(selected)} (incl. oversample copies)")

    parsed_dir = Path(args.parsed_dir)
    rng = random.Random(args.seed)

    n_windows = 0
    n_fitm = 0
    n_pieces_processed = 0
    n_pieces_too_small = 0
    n_errors = 0

    with open(args.out, "w") as out_f:
        for i, rel_path in enumerate(selected):
            full_path = parsed_dir / rel_path
            try:
                d = np.load(full_path)
            except Exception as e:
                n_errors += 1
                continue
            chars, fg, bg = d["chars"], d["fg"], d["bg"]
            sauce_group = d["sauce_group"].item().decode("utf-8", "replace") if d["sauce_group"].size else ""
            sauce_date = d["sauce_date"].item().decode("utf-8", "replace") if d["sauce_date"].size else ""
            year = sauce_date[:4] if len(sauce_date) >= 4 and sauce_date[:4].isdigit() else rel_path.split("/")[0]

            any_window = False
            for (row_off, col_off), c_win, f_win, b_win in make_windows(chars, fg, bg):
                any_window = True
                n_windows += 1
                context_text, target_text, mask_box = make_fitm_example(c_win, f_win, b_win, rng)
                # technique metrics + bucket, for direct conditioning
                # (user direction, 2026-09-19: "condition each example
                # on SAUCE year + group + the technique metrics" --
                # computed per-WINDOW, not per-parent-piece, since a
                # window can be much more/less shaded than its parent's
                # overall average)
                half_pct, shade_pct = window_technique_metrics(c_win, f_win, b_win)
                out_f.write(json.dumps({
                    "parent_path": rel_path,
                    "sauce_group": sauce_group,
                    "sauce_year": year,
                    "row_offset": row_off,
                    "col_offset": col_off,
                    "window_rows": WINDOW_ROWS,
                    "window_cols": WINDOW_COLS,
                    "half_block_pct": half_pct,
                    "shade_pct": shade_pct,
                    "shade_bucket": shade_bucket(half_pct, shade_pct),
                    "mask_box": mask_box,
                    "context": context_text,
                    "target": target_text,
                }) + "\n")
                n_fitm += 1

            if any_window:
                n_pieces_processed += 1
            else:
                n_pieces_too_small += 1

            if (i + 1) % 2000 == 0:
                print(f"  ...{i+1}/{len(selected)} piece-instances, {n_windows} windows so far")

    print(f"\nDone.")
    print(f"Piece-instances iterated (incl. oversample copies): {len(selected)}")
    print(f"Pieces that yielded >=1 window: {n_pieces_processed}")
    print(f"Pieces too small for even one window (<{WINDOW_ROWS} rows): {n_pieces_too_small}")
    print(f"Load errors: {n_errors}")
    print(f"Total windows / FITM examples: {n_windows}")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
