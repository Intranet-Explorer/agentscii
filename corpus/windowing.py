#!/usr/bin/env python3
"""Slice train-split pieces into overlapping 40x16 windows and build fill-in-the-middle examples.

Conditioning is SAUCE year and group plus per-window technique metrics
(half_block_pct, shade_pct, shade_bucket). No captions.

Selection: half_block_pct > 30 or shade_pct > 15, with alnum_pct < 15 and
distinct_colors >= 4. The p90 tier (36.8 / 38.3) is oversampled 3x. Only
train-split pieces are used; the holdout is never touched.

Row encoding:

    r00 4,3a:▄▄▄ 12,07:██

  - "r00": row index in the window
  - "4,3a:▄▄▄": run starting at column 4, fg=3 bg=a (hex), glyphs written
    literally so the model sees each glyph
  - runs are space-separated and end where (char, fg, bg) changes
  - true-background runs (space, bg 0) are omitted
  - both fg and bg are encoded; a single index would drop the background

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
COL_OVERLAP = 20   # 50% overlap on cols

# Selection thresholds
H_THRESH = 30.0
S_THRESH = 15.0
H_P90 = 36.8
S_P90 = 38.3
ALNUM_MAX = 15.0
COLORS_MIN = 4
OVERSAMPLE_P90 = 3


def rle_encode_row_runs(row_chars, row_fg, row_bg):
    """One row to a list of (start_col, color_code, glyphs) runs, true background omitted.

    Use these tuples rather than splitting the joined string: a run of
    coloured spaces contains the separator character.
    """
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
    """One row to 'run run ...' text; the caller adds the row prefix."""
    runs = rle_encode_row_runs(row_chars, row_fg, row_bg)
    return " ".join(f"{col},{color}:{glyphs}" for col, color, glyphs in runs)


def encode_window(chars_grid, fg_grid, bg_grid):
    """Encode a window as 'rNN ...' lines. Blank rows are omitted."""
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
    """Select train-split pieces by threshold. Returns (paths, n_base, n_p90).

    p90 pieces appear OVERSAMPLE_P90 times in paths.
    """
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
    """Yield ((row, col), chars, fg, bg) for overlapping windows tiled over a piece.

    Pieces smaller than a window are padded with true background, not skipped.
    """
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
            # Add a final window flush with the far edge.
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
    """Mask a random rectangle. Returns (context_text, target_text, (top, left, h, w)).

    Context marks the hole with [MASK w=N] on each masked row. The target
    is the original content in the rectangle's own coordinates.

    area_frac_range overrides the default 12-25% of window area.
    fixed_mask_size=(h, w) fixes the shape with +/-1 jitter; eval uses
    larger masks so the fill has to be constructed, not interpolated.
    """
    h, w = chars.shape
    if fixed_mask_size:
        base_h, base_w = fixed_mask_size
        mask_h = max(3, min(h - 1, base_h + rng.randint(-1, 1)))
        mask_w = max(3, min(w - 1, base_w + rng.randint(-1, 1)))
    else:
        # 12-25% of window area keeps targets near 300 tokens.
        lo, hi = area_frac_range if area_frac_range else (0.12, 0.25)
        area_frac = rng.uniform(lo, hi)
        target_area = area_frac * h * w
        mask_h = max(3, min(h - 1, round((target_area * h / w) ** 0.5)))
        mask_w = max(3, min(w - 1, round((target_area * w / h) ** 0.5)))
    top = rng.randint(0, h - mask_h)
    left = rng.randint(0, w - mask_w)

    # On masked rows, encode content left and right of the hole normally
    # with a [MASK] token between, so no context on those rows is lost.
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
            # Shift right-hand runs back to window columns.
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


_HALF_BLOCK_CP = {0x2580, 0x2584}  # ▀ ▄, as in technique_index.py
_SHADE_CP = {0x2591, 0x2592, 0x2593}  # ░ ▒ ▓


def window_technique_metrics(chars, fg, bg):
    """Subject-only (half_block_pct, shade_pct) for one window.

    Same definition as technique_index.py and harness._compute_piece_metrics;
    keep them in sync.
    """
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
    """'high' (p90 tier), 'mid' (base tier) or 'low', from the selection thresholds."""
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
        # Limit unique pieces but keep their oversample copies.
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
    n_dropped_empty_target = 0

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

                # A mask entirely in true background gives an empty
                # target. It teaches nothing and has been linked to NaN loss.
                if target_text.strip() == "":
                    n_dropped_empty_target += 1
                    continue

                # Metrics per window, not per piece; windows vary widely.
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
    print(f"Windows with an empty FITM target, dropped (mask fell entirely in true background): {n_dropped_empty_target}")
    print(f"Total windows / FITM examples WRITTEN: {n_windows - n_dropped_empty_target}")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
