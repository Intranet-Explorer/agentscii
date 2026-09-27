#!/usr/bin/env python3
"""Generate flat -> shaded training pairs.

Input is a flattened copy of the piece; target is the original. Unlike
fill-in-the-middle, nothing is hidden: only the rendering technique
(solid color vs half-block and shade dither) differs, so the model learns
to shade a flat layout.

Flattening:
  1. Split into blocks (2x4 cells, or 1x2 where detail is high).
  2. Flatten a block only if it holds a half-block (U+2580/2584) or shade
     glyph (U+2591-2593). Plain fills, text and blank space are kept.
  3. A flattened block becomes full blocks in its dominant colour, by a
     coverage-weighted vote: full block fg 1.0; half-block fg 0.5, bg 0.5;
     shade glyphs by ink density (░ 0.25, ▒ 0.5, ▓ 0.75 fg, rest bg);
     coloured space bg 1.0; anything else fg 1.0. Ties go to the lowest index.
  4. True background (space, bg 0) is never touched.
  5. Small flattened regions merge into their largest flattened neighbour.

Usage:
    python3 corpus/flat_shaded_pairs.py --n 5 --out corpus/flat_shaded_examples
    Renders example pairs as PNGs for review. Writes no training data.
"""
import argparse
import random
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np

import windowing as w
from eval_harness import render_grid_to_png

FULL_BLOCK_CP = 0x2588
HALF_BLOCK_CP = {0x2580, 0x2584}
SHADE_WEIGHTS = {0x2591: 0.25, 0x2592: 0.5, 0x2593: 0.75}  # nominal fg-ink density

REGION_ROWS = 2
REGION_COLS = 4
# Adaptive block size: 2x4 where a block is uniform, 1x2 where it has many
# distinct (char, fg, bg) cells. A fixed 2x4 grid destroys letterforms, and
# block-drawn logos aren't caught by an alnum check.
COARSE_REGION = (2, 4)
FINE_REGION = (1, 2)
EDGE_DENSITY_THRESHOLD = 0.5  # above this, a coarse block is re-flattened at FINE_REGION


def _region_dominant_color(chars, fg, bg, r0, r1, c0, c1):
    """Dominant colour of a region by coverage-weighted vote (module docstring, step 3)."""
    votes = {}  # color_idx -> total weight
    for r in range(r0, r1):
        for c in range(c0, c1):
            cp = int(chars[r, c])
            f, b = int(fg[r, c]), int(bg[r, c])
            is_space = cp == 0x20
            if is_space and b == 0:
                continue  # true background, no vote
            if cp == FULL_BLOCK_CP:
                votes[f] = votes.get(f, 0.0) + 1.0
            elif cp in HALF_BLOCK_CP:
                votes[f] = votes.get(f, 0.0) + 0.5
                votes[b] = votes.get(b, 0.0) + 0.5
            elif cp in SHADE_WEIGHTS:
                fg_w = SHADE_WEIGHTS[cp]
                votes[f] = votes.get(f, 0.0) + fg_w
                votes[b] = votes.get(b, 0.0) + (1.0 - fg_w)
            elif is_space and b != 0:
                votes[b] = votes.get(b, 0.0) + 1.0
            else:
                votes[f] = votes.get(f, 0.0) + 1.0
    if not votes:
        return None
    best_weight = max(votes.values())
    # Tie-break on lowest colour index.
    best = min(c for c, wgt in votes.items() if wgt == best_weight)
    return best


def _block_edge_density(chars, fg, bg, r0, r1, c0, c1):
    """Detail proxy: (distinct (char, fg, bg) - 1) / (cells - 1). 0 = uniform, 1 = all differ."""
    n_cells = (r1 - r0) * (c1 - c0)
    if n_cells <= 1:
        return 0.0
    triples = set()
    for r in range(r0, r1):
        for c in range(c0, c1):
            triples.add((int(chars[r, c]), int(fg[r, c]), int(bg[r, c])))
    return (len(triples) - 1) / (n_cells - 1)


def flatten_window(chars, fg, bg, coarse_region=COARSE_REGION, fine_region=FINE_REGION,
                    edge_threshold=EDGE_DENSITY_THRESHOLD):
    """Flatten technique-bearing blocks at coarse or fine size depending on detail.

    High-detail coarse blocks are split into fine sub-blocks, each flattened
    only if it has a technique glyph itself.
    Returns (flat_chars, flat_fg, flat_bg, was_flattened); was_flattened
    marks reassigned cells so merging never touches original content.
    """
    h, wd = chars.shape
    flat_chars = chars.copy()
    flat_fg = fg.copy()
    flat_bg = bg.copy()
    was_flattened = np.zeros((h, wd), dtype=bool)
    cr, cc = coarse_region
    fr, fc = fine_region

    def _flatten_one_block(r0, r1, c0, c1):
        region_chars = chars[r0:r1, c0:c1]
        has_technique = np.isin(region_chars, list(HALF_BLOCK_CP) + list(SHADE_WEIGHTS.keys())).any()
        if not has_technique:
            return
        dom_color = _region_dominant_color(chars, fg, bg, r0, r1, c0, c1)
        if dom_color is None:
            return
        for r in range(r0, r1):
            for c in range(c0, c1):
                is_space = int(chars[r, c]) == 0x20
                is_true_bg = is_space and int(bg[r, c]) == 0
                if is_true_bg:
                    continue
                flat_chars[r, c] = FULL_BLOCK_CP
                flat_fg[r, c] = dom_color
                flat_bg[r, c] = 0
                was_flattened[r, c] = True

    for r0 in range(0, h, cr):
        r1 = min(r0 + cr, h)
        for c0 in range(0, wd, cc):
            c1 = min(c0 + cc, wd)
            region_chars = chars[r0:r1, c0:c1]
            has_technique = np.isin(region_chars, list(HALF_BLOCK_CP) + list(SHADE_WEIGHTS.keys())).any()
            if not has_technique:
                continue  # plain block, keep

            density = _block_edge_density(chars, fg, bg, r0, r1, c0, c1)
            if density <= edge_threshold:
                _flatten_one_block(r0, r1, c0, c1)
            else:
                # High-detail block: flatten at fine size.
                for fr0 in range(r0, r1, fr):
                    fr1 = min(fr0 + fr, r1)
                    for fc0 in range(c0, c1, fc):
                        fc1 = min(fc0 + fc, c1)
                        _flatten_one_block(fr0, fr1, fc0, fc1)

    return flat_chars, flat_fg, flat_bg, was_flattened


MIN_REGION_CELLS = 20  # smaller flattened regions merge into a neighbour
MAX_MERGE_PASSES = 5   # merges can expose new small regions; cap the passes


def merge_small_regions(flat_chars, flat_fg, flat_bg, was_flattened, min_cells=MIN_REGION_CELLS, max_passes=MAX_MERGE_PASSES):
    """Merge small flattened regions into their largest flattened neighbour. Returns new flat_fg.

    Simplifies fragmented corpus art into large blobs like a block-in.
    Only cells with was_flattened are considered. Components are
    4-connected per colour; any smaller than min_cells takes the colour of
    its largest adjacent component (ties to lowest index). Repeats up to
    max_passes or until nothing changes.
    """
    from scipy import ndimage

    flat_fg = flat_fg.copy()
    h, wd = flat_fg.shape

    for _pass in range(max_passes):
        # Label components per colour into one shared label space.
        combined_labels = np.zeros((h, wd), dtype=np.int64)
        next_label = 1
        label_color = {}   # label id -> color
        label_size = {}     # label id -> cell count
        for color in np.unique(flat_fg[was_flattened]):
            color_mask = was_flattened & (flat_fg == color)
            labeled, n = ndimage.label(color_mask, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
            for lbl in range(1, n + 1):
                comp_mask = labeled == lbl
                size = int(comp_mask.sum())
                gid = next_label
                next_label += 1
                combined_labels[comp_mask] = gid
                label_color[gid] = int(color)
                label_size[gid] = size

        small_labels = [gid for gid, size in label_size.items() if size < min_cells]
        if not small_labels:
            break

        changed = False
        for gid in small_labels:
            comp_mask = combined_labels == gid
            # Dilate by one cell to find touching components.
            dilated = ndimage.binary_dilation(comp_mask, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
            border = dilated & ~comp_mask & was_flattened
            neighbor_labels = np.unique(combined_labels[border])
            neighbor_labels = [n for n in neighbor_labels if n != 0 and n != gid]
            if not neighbor_labels:
                continue  # no flattened neighbour; never merge into original content
            # Largest neighbour, tie-break on lowest colour index.
            best = max(neighbor_labels, key=lambda n: (label_size.get(n, 0), -label_color.get(n, 0)))
            new_color = label_color[best]
            if new_color != label_color[gid]:
                flat_fg[comp_mask] = new_color
                changed = True

        if not changed:
            break

    return flat_fg


def flatten_piece_and_merge(chars, fg, bg, coarse_region=COARSE_REGION, fine_region=FINE_REGION,
                             edge_threshold=EDGE_DENSITY_THRESHOLD, min_cells=MIN_REGION_CELLS):
    """Flatten and merge a whole piece. Returns (flat_chars, flat_fg, flat_bg), same shape.

    Run on the whole piece, then window: merging needs connectivity that a
    window boundary would cut.
    """
    flat_chars, flat_fg, flat_bg, was_flattened = flatten_window(chars, fg, bg, coarse_region, fine_region, edge_threshold)
    flat_fg = merge_small_regions(flat_chars, flat_fg, flat_bg, was_flattened, min_cells=min_cells)
    return flat_chars, flat_fg, flat_bg


def pick_example_windows(n, seed=1, min_half_block=15.0, min_shade=15.0):
    """Sample n train-split windows with enough half-block and shade for flattening to show."""
    import json
    holdout = json.loads((CORPUS_DIR / "holdout_split.json").read_text())
    train_paths = set(holdout["train_paths"])
    parsed_dir = CORPUS_DIR / "parsed"

    rng = random.Random(seed)
    candidates = sorted(train_paths)  # set order varies per process; sort for reproducibility
    rng.shuffle(candidates)

    picked = []
    for rel in candidates:
        if len(picked) >= n:
            break
        npz_path = parsed_dir / rel
        try:
            d = np.load(npz_path)
        except Exception:
            continue
        chars_full, fg_full, bg_full = d["chars"], d["fg"], d["bg"]
        if chars_full.shape[0] < w.WINDOW_ROWS or chars_full.shape[1] < w.WINDOW_COLS:
            continue
        # md5, not hash(): built-in str hash is randomized per process.
        import hashlib
        local_seed = int(hashlib.md5(rel.encode()).hexdigest()[:8], 16)
        local_rng = random.Random(local_seed)
        row0 = local_rng.randint(0, chars_full.shape[0] - w.WINDOW_ROWS)
        col0 = local_rng.randint(0, chars_full.shape[1] - w.WINDOW_COLS)
        c_win = chars_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        f_win = fg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        b_win = bg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        half_pct, shade_pct = w.window_technique_metrics(c_win, f_win, b_win)
        if half_pct < min_half_block or shade_pct < min_shade:
            continue
        picked.append({
            "rel": rel, "row0": row0, "col0": col0,
            "chars": c_win, "fg": f_win, "bg": b_win,
            "chars_full": chars_full, "fg_full": fg_full, "bg_full": bg_full,
            "half_block_pct": half_pct, "shade_pct": shade_pct,
        })
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(CORPUS_DIR / "flat_shaded_examples"))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    examples = pick_example_windows(args.n, seed=args.seed)
    print(f"{len(examples)}/{args.n} example windows picked (half_block>=15%, shade>=15%)")

    results = []
    for i, ex in enumerate(examples):
        # Flatten the whole piece, then cut the same window from flat and original.
        flat_chars_full, flat_fg_full, flat_bg_full = flatten_piece_and_merge(
            ex["chars_full"], ex["fg_full"], ex["bg_full"]
        )
        r0, c0 = ex["row0"], ex["col0"]
        flat_chars = flat_chars_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]
        flat_fg = flat_fg_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]
        flat_bg = flat_bg_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]

        stem = Path(ex["rel"]).stem.replace(".ANS", "").replace(".ans", "").replace(".ASC", "").replace(".asc", "")
        flat_png = out_dir / f"{i:02d}_{stem}_flat.png"
        shaded_png = out_dir / f"{i:02d}_{stem}_shaded.png"
        render_grid_to_png(flat_chars, flat_fg, flat_bg, flat_png)
        render_grid_to_png(ex["chars"], ex["fg"], ex["bg"], shaded_png)

        flat_half, flat_shade = w.window_technique_metrics(flat_chars, flat_fg, flat_bg)
        is_space = (flat_chars == 0x20)
        is_true_bg = is_space & (flat_bg == 0)
        subject = ~is_true_bg
        n_colors = len(np.unique(np.where(is_space, flat_bg, flat_fg)[subject])) if subject.any() else 0
        results.append({
            "rel": ex["rel"], "row0": ex["row0"], "col0": ex["col0"],
            "orig_half_block_pct": ex["half_block_pct"], "orig_shade_pct": ex["shade_pct"],
            "flat_half_block_pct": flat_half, "flat_shade_pct": flat_shade,
            "flat_n_colors": n_colors,
            "flat_png": str(flat_png), "shaded_png": str(shaded_png),
        })
        print(f"  [{i}] {ex['rel']}: orig half={ex['half_block_pct']:.1f} shade={ex['shade_pct']:.1f} "
              f"-> flat half={flat_half:.1f} shade={flat_shade:.1f} n_colors={n_colors}")

    import json
    (out_dir / "manifest.json").write_text(json.dumps(results, indent=2))
    print(f"\n{len(results)} pairs rendered to {out_dir}")


if __name__ == "__main__":
    main()
