#!/usr/bin/env python3
"""corpus/validate.py -- validate parse.py's output against real ansilove
renders on N random files, report mismatch categories.

Methodology: ansilove renders a fixed 8x16px bitmap font per cell (CP437,
80x25 font by default). Rather than reverse-engineer ansilove's embedded
font bitmaps for pixel-perfect text matching (a much bigger undertaking
than validating the actual thing this corpus cares about -- the cell
grid's colors and structure), this validates STRUCTURALLY per cell:

  1. BG COLOR: sample the 4 corner pixels of each 8x16 cell block in
     ansilove's PNG (corners are guaranteed background-only for every
     real CP437 glyph -- no glyph in the font touches all 4 corners) and
     compare to the expected palette RGB for parse.py's bg value.
  2. GLYPH PRESENCE: a truly blank cell (space, fg==bg after accounting
     for a solid block glyph in the same fg/bg) should show near-zero
     variance across the whole cell; a drawn glyph should show some
     fg-colored pixels distinct from bg. Compares "is something drawn
     here" as a boolean, not exact glyph shape.
  3. ROW/COL COUNT: parsed n_rows/n_cols vs the PNG's pixel dimensions
     divided by the 8x16 cell size.

Requires `ansilove` on PATH (brew install ansilove) -- confirmed present
and its real 8x16px/cell, CP437-80x25-font output was inspected directly
before writing this (see corpus/parse.py's module docstring) before
trusting it as ground truth.

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
    """Run ansilove on a copy of the file (ansilove writes <input>.png next
    to the input, which would litter the corpus if run in place) in a
    scratch dir. Passes -i ONLY when ice_colors is True (the file's own
    SAUCE TFlags bit), matching exactly what parse.py resolves --
    confirmed live that ansilove does NOT auto-apply the SAUCE iCE flag
    without -i: rendering a real iCE-flagged file with and without -i
    produced genuinely different pixels (39303/768000 differing byte
    values on a real test file), so passing -i unconditionally would have
    made every non-iCE file a systematic, spurious validation mismatch.
    Returns a PIL Image or None on failure."""
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
                # ansilove's own stdout (SAUCE dump, comments field etc.)
                # is CP437/raw-byte text, not guaranteed valid UTF-8 --
                # found live: a real file's SAUCE comment field crashed
                # this with UnicodeDecodeError on byte 0xfe. errors=
                # "replace" keeps the batch running; we only use r.stderr
                # for the error message anyway, never r.stdout.
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
    rgb = tuple(int(v) for v in rgb)  # rgb may be numpy uint8 scalars from
    # a sliced array -- uint8 arithmetic wraps on subtraction instead of
    # going negative, corrupting every distance calc silently (found live:
    # RuntimeWarning: overflow encountered in scalar subtract on every
    # single comparison). Force real Python ints before any arithmetic.
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
        # a 1-row difference is common and NOT a real bug: ansilove may
        # trim/not-trim a final near-empty row differently than parse.py's
        # max_row_seen convention -- bucket this separately from a
        # genuine structural mismatch (row_diff > 1) so the report doesn't
        # conflate a cosmetic off-by-one with real parsing defects.
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
            # FULL BLOCK (U+2588) fills the entire cell with the FOREGROUND
            # color -- corners are fg, not bg, for this one glyph. Every
            # other CP437 glyph (including the shade ramps ░▒▓) leaves at
            # least one corner as true background. Found live: the corner-
            # sampling heuristic below flagged a correct █ cell as a false
            # "bg mismatch" because it compared the glyph's own ink color
            # (found at all 4 corners) against the cell's actual bg.
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

            # glyph presence: does the cell contain any pixel that's NOT
            # close to the expected bg color? CP437 codepoint 0x00 (NUL)
            # is a genuinely blank glyph in the font (distinct from ' '
            # 0x20, but visually identical) -- found live: the earlier
            # version of this check only excluded literal space, so a
            # correctly-blank NUL cell was flagged as a false "expected
            # glyph, found none" mismatch. Both codepoints render as pure
            # background, no ink, in the real font.
            #
            # A cell with fg == bg is ALSO legitimately indistinguishable
            # from "no glyph" by any pixel test -- found live, confirmed
            # exhaustively: every remaining glyph_presence_mismatch in a
            # 200-file validation run traced to exactly this (e.g.
            # arl-flash.ans: 1229/1229 mismatches were fg==bg cells; two
            # more real files matched their mismatch count to their fg==bg
            # count exactly, 660/660 and 535/535). A real artist
            # deliberately using fg==bg (a flat, glyph-shape-irrelevant
            # fill) is correct output, not a defect -- exclude these cells
            # from the presence check entirely rather than trying to guess
            # a pixel threshold that would work for them.
            fg_idx = int(parsed["fg"][r, c])
            expects_glyph = expected_char not in (" ", "\x00") and fg_idx != expected_bg_idx
            cell_flat = cell.reshape(-1, 3)
            # NOTE: always check distance from the TRUE background here,
            # not expected_check_rgb (which is deliberately the FG color
            # for a full block, for the corner-sampling check above) --
            # found live: reusing expected_check_rgb here for a █ cell
            # checks "is any pixel far from fg", which is false for a cell
            # that's entirely fg, producing a false "no glyph found"
            # mismatch on every single full-block cell in the sample.
            dists_to_bg = np.sum((cell_flat.astype(int) - np.array(expected_bg_rgb)) ** 2, axis=1)
            has_nonbg_pixels = bool(np.any(dists_to_bg > 400))
            if expects_glyph != has_nonbg_pixels:
                # a handful of CP437 codepoints ARE visually blank at some
                # sizes (e.g. codepoint 0x20 duplicates, NBSP-like cells)
                # or a glyph whose ink is genuinely very close in color to
                # its own bg in an edge palette case -- still counted, but
                # bucketed distinctly from a bg color mismatch.
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
            # A single file's unexpected failure (any exception not
            # already caught inside validate_file itself) must never
            # crash the whole batch -- found live: a genuinely unhandled
            # UnicodeDecodeError from ansilove's own stdout on one file's
            # SAUCE comment field killed a 200-file run at file ~130,
            # discarding all prior progress. Record it as an error result
            # and keep going.
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
