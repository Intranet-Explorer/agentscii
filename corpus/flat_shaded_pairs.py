#!/usr/bin/env python3
"""corpus/flat_shaded_pairs.py -- "flat -> shaded" pair generator for
a REFRAMED training objective (design only, not wired into training
yet -- user direction, 2026-09-20, after the real-piece test showed
FITM-without-conditioning learns texture statistics, not content:
"That's the training objective, not tuning. Stop tuning this
adapter... build a 'flat -> shaded' pair generator. For each corpus
window, create a flattened version (quantize to dominant color per
region, remove half-blocks and shade glyphs), and the target is the
original.").

Why this is a different objective than the old FIM task, not just a
different mask shape: the old task hid a rectangular hole and asked
the model to guess unseen content from surrounding context alone --
genuinely ambiguous (a hole could contain a letter, a pattern,
anything), which is why it degraded to matching texture statistics.
This task shows the model the FULL window, fully visible, with real
color/shape structure already in place -- only the RENDERING technique
(solid color vs. half-block sub-cell blend / shade dither) is
different between input and target. There's no content to guess, only
a rendering operation to learn: "given this flat color layout, apply
the shading technique real artists use." Matches the technique gap
the whole project started from (raze: shade-heavy, ~0% half-block).

Flattening algorithm, per WINDOW_ROWS x WINDOW_COLS window:
  1. Partition the window into REGION_ROWS x REGION_COLS non-
     overlapping cell blocks (default 2 rows x 4 cols -- chosen to be
     roughly SQUARE in rendered pixels, since a terminal cell here
     renders ~9px wide x ~19px tall (measured directly from
     eval_harness.render_grid_to_png's actual output), so a 2x4 cell
     block is ~18x38px -- not square, closer to critique: 4 cols x 19h
     vs 2 rows x 19h... see docstring note below on the actual
     measured ratio and why 2x4 was chosen anyway).
  2. A region is flattened ONLY if it contains at least one
     half-block (U+2580/U+2584) or shade (U+2591/U+2592/U+2593) glyph
     in the ORIGINAL -- regions that are already plain (solid
     full-block fills, real text, blank background) are left
     untouched. This preserves real structure (title text, solid
     panels) as shared context between input and target, rather than
     degrading the whole window uniformly.
  3. For a flattened region, compute one DOMINANT visible color via a
     coverage-weighted vote over its cells:
       - full block (U+2588): fg, weight 1.0
       - half-block (U+2580/U+2584): fg weight 0.5, bg weight 0.5
         (each half-block cell is visually half fg, half bg)
       - shade glyphs: weight by their nominal ink density --
         U+2591 (light) ~0.25 fg / 0.75 bg, U+2592 (medium) ~0.5/0.5,
         U+2593 (dark) ~0.75/0.25 -- the standard ordering used
         elsewhere in this corpus for "light/medium/dark" density.
       - space with bg != 0 (a colored blank): bg, weight 1.0
       - anything else (rare: stray glyphs inside a mixed region):
         fg, weight 1.0
     then every cell in the region is replaced with a FULL BLOCK
     glyph in the single highest-weight color (ties broken by lowest
     color index, deterministic).
  4. True-background cells (space, bg == 0) are NEVER touched, in
     either flattened or untouched regions -- never invent content in
     genuinely blank space (the exact failure mode the real-piece
     test caught in generate_region.py's TS-GIMP result).

Target = the original window, byte-identical, unchanged.

Usage:
    python3 corpus/flat_shaded_pairs.py --n 5 --out corpus/flat_shaded_examples
    # renders N example pairs (flat left, shaded/original right) as
    # PNGs plus a composite grid image, for visual review BEFORE any
    # training decision. No dataset/mlx_train_data write in this
    # script -- explicitly design/preview only per user instruction
    # ("design only, don't train yet... Training resumes only after
    # the pair examples look right").
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
# Adaptive flattening (user direction, 2026-09-20, after review found
# the fixed 2x4 grid destroyed logo/text letterforms: "Adaptive
# flattening: 2x4 regions where local variance is low, 1x2 where edge
# density is high. No text detector -- logos are drawn in blocks, so
# alnum_pct won't catch them."). A block's local variance/edge density
# is measured over its OWN glyph identity + color pattern (not a
# separate detector) -- a block where every cell has the same
# (char, fg, bg) triple is "low variance" (safe to flatten coarsely);
# a block with many distinct triples packed together is "high edge
# density" (letterforms, fine detail) and gets flattened at half the
# region size instead, preserving more real structure.
COARSE_REGION = (2, 4)
FINE_REGION = (1, 2)
EDGE_DENSITY_THRESHOLD = 0.5  # fraction of distinct (char,fg,bg) triples in a COARSE block above which it's treated as high-detail and re-flattened at FINE_REGION instead


def _region_dominant_color(chars, fg, bg, r0, r1, c0, c1):
    """Coverage-weighted vote over one region's cells -> single color
    index. See module docstring step 3 for the weighting rule."""
    votes = {}  # color_idx -> total weight
    for r in range(r0, r1):
        for c in range(c0, c1):
            cp = int(chars[r, c])
            f, b = int(fg[r, c]), int(bg[r, c])
            is_space = cp == 0x20
            if is_space and b == 0:
                continue  # true background, contributes no color vote
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
    # deterministic tie-break: lowest color index among the max-weight colors
    best = min(c for c, wgt in votes.items() if wgt == best_weight)
    return best


def _block_edge_density(chars, fg, bg, r0, r1, c0, c1):
    """Fraction of distinct (char,fg,bg) triples within a block,
    normalized by cell count -- cheap proxy for local detail/edge
    density with no text detector: a solid-color block has 1 distinct
    triple regardless of size (density -> 0 as it's amortized over
    more cells); a block where every cell differs has density -> 1."""
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
    """Adaptive two-pass flattening (see COARSE_REGION/FINE_REGION/
    EDGE_DENSITY_THRESHOLD docstring above). Pass 1: scan at
    coarse_region size; a block with technique glyphs AND low edge
    density gets flattened at coarse_region. Pass 2: a block with
    technique glyphs AND high edge density is instead subdivided into
    fine_region sub-blocks and each flattened independently (still
    only if that finer sub-block itself contains a technique glyph --
    a coarse block can be "high detail" overall while having plain
    sub-regions inside it). Returns (flat_chars, flat_fg, flat_bg,
    was_flattened) -- was_flattened is a bool array marking which
    cells were actually reassigned (needed by
    flatten_piece_and_merge's region-merge step, which must only ever
    touch flattened cells, never original plain/text content)."""
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
                continue  # already-plain region, leave untouched regardless of detail level

            density = _block_edge_density(chars, fg, bg, r0, r1, c0, c1)
            if density <= edge_threshold:
                _flatten_one_block(r0, r1, c0, c1)
            else:
                # high-detail block (letterform/fine pattern): re-scan
                # at fine_region granularity instead of the coarse one
                for fr0 in range(r0, r1, fr):
                    fr1 = min(fr0 + fr, r1)
                    for fc0 in range(c0, c1, fc):
                        fc1 = min(fc0 + fc, c1)
                        _flatten_one_block(fr0, fr1, fc0, fc1)

    return flat_chars, flat_fg, flat_bg, was_flattened


MIN_REGION_CELLS = 20  # user direction, 2026-09-20: "merge any region below a minimum size into its largest neighbor"
MAX_MERGE_PASSES = 5   # bounded iteration so chains of small regions can consolidate without risking an infinite loop


def merge_small_regions(flat_chars, flat_fg, flat_bg, was_flattened, min_cells=MIN_REGION_CELLS, max_passes=MAX_MERGE_PASSES):
    """Consolidate fragmented flat-color patches into raze-scale
    coherent blobs (user direction, 2026-09-20, after the raze
    comparison showed corpus art is inherently more detailed/
    fragmented than raze's simple single-blob pieces: "the fix is to
    make the flat version simplify, not just strip technique...
    merge any region below a minimum size into its largest
    neighbor. That produces big coherent blobs like raze's.").

    Operates ONLY on cells where was_flattened is True -- original
    plain/text regions are never touched by merging, same rule as
    flatten_window's own blank-space guard, for the same reason (the
    real-piece test's TS-GIMP/bw_blockalypse failures were both
    "the model touched something it shouldn't have").

    Connected components (4-connectivity) are computed per distinct
    color over the was_flattened mask via scipy.ndimage.label. Any
    component smaller than min_cells gets recolored to match
    whichever ADJACENT flattened component (sharing a 4-connected
    boundary) is largest -- ties broken by lowest color index for
    determinism. Repeats up to max_passes times since a merge can
    itself create a newly-adjacent small remnant; stops early once a
    pass makes no changes."""
    from scipy import ndimage

    flat_fg = flat_fg.copy()
    h, wd = flat_fg.shape

    for _pass in range(max_passes):
        # label connected components per distinct color, all sharing
        # one global label space by offsetting each color's local
        # labels
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
            break  # nothing left to merge, done

        changed = False
        for gid in small_labels:
            comp_mask = combined_labels == gid
            # dilate by 1 (4-connectivity) to find touching neighbor labels
            dilated = ndimage.binary_dilation(comp_mask, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
            border = dilated & ~comp_mask & was_flattened
            neighbor_labels = np.unique(combined_labels[border])
            neighbor_labels = [n for n in neighbor_labels if n != 0 and n != gid]
            if not neighbor_labels:
                continue  # isolated flattened patch with no flattened neighbor -- leave it (never merge into plain/text)
            # pick the largest neighboring component, tie-break lowest color index
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
    """Full pipeline at PARENT PIECE level (user direction, 2026-09-20:
    "flatten the whole piece before windowing" -- NOT per-40x16-window
    as the first design did; a window crop of a detailed corpus piece
    is inherently more fragmented than a crop of one of raze's simple
    single-blob pieces, and per-window flattening couldn't fix that --
    merging needs the WHOLE piece's connectivity to consolidate small
    patches into big ones, which a 40x16 crop boundary would cut off).
    Returns (flat_chars, flat_fg, flat_bg) at the full piece's
    original shape -- windowing/cropping for pair examples happens
    AFTER this, by slicing the same (row0,col0) window out of both the
    returned flat piece and the untouched original."""
    flat_chars, flat_fg, flat_bg, was_flattened = flatten_window(chars, fg, bg, coarse_region, fine_region, edge_threshold)
    flat_fg = merge_small_regions(flat_chars, flat_fg, flat_bg, was_flattened, min_cells=min_cells)
    return flat_chars, flat_fg, flat_bg


def pick_example_windows(n, seed=1, min_half_block=15.0, min_shade=15.0):
    """Sample N real train-split windows with enough half-block/shade
    presence that flattening actually does something visible (a window
    with 0% of either technique would flatten to a no-op, an
    uninformative example for visual review)."""
    import json
    holdout = json.loads((CORPUS_DIR / "holdout_split.json").read_text())
    train_paths = set(holdout["train_paths"])
    parsed_dir = CORPUS_DIR / "parsed"

    rng = random.Random(seed)
    candidates = sorted(train_paths)  # sorted first: python set iteration order is
    # hash-randomized per-process, so without this, the SAME seed produced
    # DIFFERENT picks across runs (found live comparing two runs meant to
    # use "the same 5 pairs" -- sorting first makes rng.shuffle's result
    # reproducible run to run for a given seed, as the caller expects)
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
        # hash(rel) is Python's built-in str hash, randomized per-process
        # by default (PYTHONHASHSEED) -- using it here made "the same
        # seed" pick DIFFERENT windows on every run (found live: two
        # runs with --seed 1 produced different mask positions for the
        # same candidate order). hashlib.md5 is stable across runs/
        # processes -- use that instead for anything that needs to be
        # reproducible by seed alone.
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
        # flatten+merge the WHOLE piece first (user direction,
        # 2026-09-20: merging needs full-piece connectivity, a window
        # crop can't consolidate patches that a crop boundary cuts
        # off), THEN slice the SAME (row0,col0) window out of both the
        # flattened full piece and the untouched original -- this is
        # the actual flat/shaded pair, not the old per-window flatten.
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
