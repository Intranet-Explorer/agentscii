#!/usr/bin/env python3
"""Validate parse.py output against ansilove renders on N random files.

Checks structure per 8x16 cell rather than exact glyph shape:
  1. BG colour: majority of the 4 corner pixels vs the parsed bg. Only █
     reaches all four corners, so it is checked against fg instead.
  2. Glyph presence: whether any pixel differs from bg, vs whether the
     parsed cell should show ink.
  3. Row and column count vs PNG size.

Requires ansilove on PATH.

Usage:
    python3 corpus/validate.py --n 200 --seed 0
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))
import parse as parsemod  # noqa: E402

CELL_W, CELL_H = 8, 16

ANSI_PALETTE = [
    (0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
    (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170),
    (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
    (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255),
]


def render_with_ansilove(path, ice_colors):
    """Render a copy of the file with ansilove in a temp dir. Returns (Image, None) or (None, error).

    ansilove writes the PNG next to its input, hence the copy. It ignores
    the SAUCE iCE flag, so -i is passed only when ice_colors is set, to
    match parse.py.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp_in = Path(td) / Path(path).name
        tmp_in.write_bytes(Path(path).read_bytes())
        cmd = ["ansilove", "-c", "80"]
        if ice_colors:
            cmd.append("-i")
        cmd.append(str(tmp_in))
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=td,
                encoding="utf-8", errors="replace",
                # ansilove echoes SAUCE bytes that aren't valid UTF-8.
            )
        except subprocess.TimeoutExpired:
            return None, "ansilove timed out"
        out_png = tmp_in.with_suffix(tmp_in.suffix + ".png")
        if not out_png.exists():
            return None, f"ansilove produced no output (exit {r.returncode}): {r.stderr[:200]}"
        try:
            img = Image.open(out_png).convert("RGB")
            img.load()
            return img, None
        except Exception as e:
            return None, f"failed to open ansilove PNG: {e}"


def _closest_palette_index(rgb):
    best_i, best_d = 0, float("inf")
    rgb = tuple(int(v) for v in rgb)  # uint8 subtraction would wrap
    for i, p in enumerate(ANSI_PALETTE):
        d = sum((a - b) ** 2 for a, b in zip(rgb, p))
        if d < best_d:
            best_d, best_i = d, i
    return best_i, best_d


def validate_file(path):
    """Returns a dict: {status: 'ok'|'mismatch'|'error', categories: [...],
    n_cells_checked, n_cells_mismatched}."""
    try:
        parsed = parsemod.parse_file(path)
    except Exception as e:
        return {"status": "error", "categories": [f"parse_failed: {e}"]}

    img, err = render_with_ansilove(path, bool(parsed["ice_colors"]))
    if img is None:
        return {"status": "error", "categories": [f"ansilove_failed: {err}"]}

    png_w, png_h = img.size
    expected_rows = int(parsed["n_rows"])
    expected_cols = int(parsed["n_cols"])
    png_rows = png_h // CELL_H
    png_cols = png_w // CELL_W

    categories = []
    if png_cols != expected_cols:
        categories.append(f"col_count_mismatch(parsed={expected_cols},png={png_cols})")
    row_diff = abs(png_rows - expected_rows)
    if row_diff > 0:
        # Off-by-one is usually a trailing-row trim difference; report it
        # separately from real structural mismatches.
        if row_diff == 1:
            categories.append("row_count_off_by_one")
        else:
            categories.append(f"row_count_mismatch(parsed={expected_rows},png={png_rows},diff={row_diff})")

    arr = np.array(img)
    check_rows = min(expected_rows, png_rows)
    check_cols = min(expected_cols, png_cols)

    n_checked = 0
    n_bg_mismatch = 0
    n_glyph_presence_mismatch = 0
    bg_mismatch_examples = []
    glyph_mismatch_examples = []

    for r in range(check_rows):
        for c in range(check_cols):
            y0, x0 = r * CELL_H, c * CELL_W
            cell = arr[y0:y0 + CELL_H, x0:x0 + CELL_W]
            expected_char = chr(int(parsed["chars"][r, c]))
            expected_bg_idx = int(parsed["bg"][r, c])
            expected_bg_rgb = ANSI_PALETTE[expected_bg_idx]

            n_checked += 1
            # █ fills the cell with fg, so its corners are fg. Every other
            # glyph leaves at least one corner as bg.
            if expected_char == "\u2588":
                expected_fg_idx = int(parsed["fg"][r, c])
                expected_check_rgb = ANSI_PALETTE[expected_fg_idx]
            else:
                expected_check_rgb = expected_bg_rgb

            corners = [tuple(int(v) for v in cell[0, 0]), tuple(int(v) for v in cell[0, -1]),
                       tuple(int(v) for v in cell[-1, 0]), tuple(int(v) for v in cell[-1, -1])]
            from collections import Counter
            corner_counts = Counter(corners)
            sampled_rgb, corner_count = corner_counts.most_common(1)[0]

            if corner_count >= 3:
                actual_idx, dist = _closest_palette_index(sampled_rgb)
                expected_idx = int(parsed["fg"][r, c]) if expected_char == "\u2588" else expected_bg_idx
                if actual_idx != expected_idx and dist > 100:
                    n_bg_mismatch += 1
                    if len(bg_mismatch_examples) < 5:
                        bg_mismatch_examples.append({
                            "row": r, "col": c, "char": expected_char,
                            "expected_idx": expected_idx, "expected_rgb": expected_check_rgb,
                            "actual_rgb": sampled_rgb, "closest_idx": actual_idx,
                        })

            # Glyph presence: any pixel far from bg. NUL and space are both
            # blank, and fg == bg shows no ink, so none of those expect a glyph.
            fg_idx = int(parsed["fg"][r, c])
            expects_glyph = expected_char not in (" ", "\x00") and fg_idx != expected_bg_idx
            cell_flat = cell.reshape(-1, 3)
            # Measure against the real bg, not expected_check_rgb (fg for █).
            dists_to_bg = np.sum((cell_flat.astype(int) - np.array(expected_bg_rgb)) ** 2, axis=1)
            has_nonbg_pixels = bool(np.any(dists_to_bg > 400))
            if expects_glyph != has_nonbg_pixels:
                # Can also come from blank-looking glyphs or ink close to bg;
                # counted separately from bg mismatches.
                n_glyph_presence_mismatch += 1
                if len(glyph_mismatch_examples) < 5:
                    glyph_mismatch_examples.append({
                        "row": r, "col": c, "char": expected_char,
                        "expects_glyph": expects_glyph, "has_nonbg_pixels": has_nonbg_pixels,
                    })

    if n_bg_mismatch > 0:
        categories.append(f"bg_color_mismatch(count={n_bg_mismatch}/{n_checked})")
    if n_glyph_presence_mismatch > 0:
        categories.append(f"glyph_presence_mismatch(count={n_glyph_presence_mismatch}/{n_checked})")

    status = "ok" if not categories else "mismatch"
    return {
        "status": status,
        "categories": categories,
        "n_cells_checked": n_checked,
        "n_bg_mismatch": n_bg_mismatch,
        "n_glyph_presence_mismatch": n_glyph_presence_mismatch,
        "bg_mismatch_examples": bg_mismatch_examples,
        "glyph_mismatch_examples": glyph_mismatch_examples,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input-dir", default=str(CORPUS_DIR / "data"))
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--report", default=str(CORPUS_DIR / "validation_report.json"))
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    files = sorted(
        p for p in input_dir.rglob("*")
        if p.suffix.lower() in (".ans", ".asc") and p.is_file()
    )
    if not files:
        print("No .ans/.asc files found under", input_dir, file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    sample = rng.sample(files, min(args.n, len(files)))
    print(f"Validating {len(sample)} random files (seed={args.seed}) against ansilove...")

    results = []
    category_counts = {}
    for i, path in enumerate(sample):
        try:
            res = validate_file(path)
        except Exception as e:
            # One bad file must not end the batch.
            res = {"status": "error", "categories": [f"unexpected_exception: {e}"]}
        res["path"] = str(path.relative_to(input_dir))
        results.append(res)
        for cat in res["categories"]:
            key = cat.split("(")[0]
            category_counts[key] = category_counts.get(key, 0) + 1
        if (i + 1) % 25 == 0:
            print(f"  ...{i+1}/{len(sample)}")

    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_mismatch = sum(1 for r in results if r["status"] == "mismatch")
    n_error = sum(1 for r in results if r["status"] == "error")

    print(f"\n=== Validation report: {len(sample)} files ===")
    print(f"  ok:       {n_ok}")
    print(f"  mismatch: {n_mismatch}")
    print(f"  error:    {n_error}")
    print(f"\nMismatch/error categories:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    with open(args.report, "w") as f:
        json.dump({
            "n_files": len(sample), "n_ok": n_ok, "n_mismatch": n_mismatch, "n_error": n_error,
            "category_counts": category_counts, "results": results,
        }, f, indent=2, default=str)
    print(f"\nFull report: {args.report}")


if __name__ == "__main__":
    main()
