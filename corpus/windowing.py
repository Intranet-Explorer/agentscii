#!/usr/bin/env python3
"""corpus/windowing.py -- step 2: slice train-split pieces into 80x24
windows with overlap, RLE-encode rows, and build fill-in-the-middle
(FITM) examples.

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

WINDOW_ROWS = 24
WINDOW_COLS = 80
ROW_OVERLAP = 12   # 50% overlap on rows
COL_OVERLAP = 0    # most corpus files are exactly 80 cols already; no col-tiling needed for those

# Selection thresholds -- user direction, 2026-09-19
H_THRESH = 30.0
S_THRESH = 15.0
H_P90 = 36.8
S_P90 = 38.3
ALNUM_MAX = 15.0
COLORS_MIN = 4
OVERSAMPLE_P90 = 3


def rle_encode_row(row_chars, row_fg, row_bg):
    """One row -> 'r{idx} run run run...' string (idx filled in by caller).
    Runs of identical (char,fg,bg) are merged; true-background runs
    (space, bg=0) are omitted entirely."""
    tokens = []
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
            tokens.append(f"{i},{color_code}:{glyphs}")
        i = j
    return " ".join(tokens)


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
    with ROW_OVERLAP row overlap. Pieces narrower than WINDOW_COLS are
    left-aligned and padded with true background on the right (rare in
    practice -- most real archive pieces are exactly 80 cols); pieces
    shorter than WINDOW_ROWS are skipped (too little content for a
    meaningful FITM example)."""
    n_rows, n_cols = chars.shape
    if n_rows < WINDOW_ROWS:
        return
    stride = WINDOW_ROWS - ROW_OVERLAP
    row = 0
    while row + WINDOW_ROWS <= n_rows:
        c_slice = chars[row:row + WINDOW_ROWS, :]
        f_slice = fg[row:row + WINDOW_ROWS, :]
        b_slice = bg[row:row + WINDOW_ROWS, :]
        if n_cols < WINDOW_COLS:
            pad_w = WINDOW_COLS - n_cols
            c_slice = np.pad(c_slice, ((0, 0), (0, pad_w)), constant_values=0x20)
            f_slice = np.pad(f_slice, ((0, 0), (0, pad_w)), constant_values=7)
            b_slice = np.pad(b_slice, ((0, 0), (0, pad_w)), constant_values=0)
        elif n_cols > WINDOW_COLS:
            c_slice = c_slice[:, :WINDOW_COLS]
            f_slice = f_slice[:, :WINDOW_COLS]
            b_slice = b_slice[:, :WINDOW_COLS]
        yield row, c_slice, f_slice, b_slice
        row += stride
        if row < n_rows and row + WINDOW_ROWS > n_rows and n_rows - WINDOW_ROWS > row - stride:
            # one final window flush against the bottom edge, so the
            # last few rows of a piece aren't always dropped just
            # because they don't land on a stride boundary
            row = n_rows - WINDOW_ROWS


def make_fitm_example(chars, fg, bg, rng):
    """Mask a random rectangle inside the window; context = the window
    with that rectangle blanked to true background; target = the
    rectangle's real original content, RLE-encoded on its own
    coordinate system (row/col relative to the rectangle, not the
    window) so the target is self-contained."""
    h, w = chars.shape
    # mask rectangle: 20-40% of window area, clamped to sane min size
    area_frac = rng.uniform(0.20, 0.40)
    target_area = area_frac * h * w
    mask_h = max(3, min(h - 1, round((target_area * h / w) ** 0.5)))
    mask_w = max(3, min(w - 1, round((target_area * w / h) ** 0.5)))
    top = rng.randint(0, h - mask_h)
    left = rng.randint(0, w - mask_w)

    context_chars = chars.copy()
    context_fg = fg.copy()
    context_bg = bg.copy()
    # A masked hole is marked with a real, otherwise-unused sentinel
    # glyph (private-use codepoint) so the model sees an unambiguous
    # "reconstruct this" marker, not a plain space it might confuse
    # with real negative-space background.
    MASK_CP = 0xE000
    context_chars[top:top + mask_h, left:left + mask_w] = MASK_CP
    context_fg[top:top + mask_h, left:left + mask_w] = 0
    context_bg[top:top + mask_h, left:left + mask_w] = 0

    context_text = encode_window(context_chars, context_fg, context_bg)
    # replace the literal mask glyph with a short marker line instead
    # of RLE-encoding thousands of identical sentinel runs
    context_text = f"MASK at row={top} col={left} h={mask_h} w={mask_w}\n" + context_text

    target_chars = chars[top:top + mask_h, left:left + mask_w]
    target_fg = fg[top:top + mask_h, left:left + mask_w]
    target_bg = bg[top:top + mask_h, left:left + mask_w]
    target_text = encode_window(target_chars, target_fg, target_bg)

    return context_text, target_text, (top, left, mask_h, mask_w)


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
            for row_off, c_win, f_win, b_win in make_windows(chars, fg, bg):
                any_window = True
                n_windows += 1
                context_text, target_text, mask_box = make_fitm_example(c_win, f_win, b_win, rng)
                out_f.write(json.dumps({
                    "parent_path": rel_path,
                    "sauce_group": sauce_group,
                    "sauce_year": year,
                    "row_offset": row_off,
                    "window_rows": WINDOW_ROWS,
                    "window_cols": WINDOW_COLS,
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
