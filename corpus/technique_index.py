#!/usr/bin/env python3
"""corpus/technique_index.py -- per-piece technique metrics for the
whole parsed corpus, to select a shading-heavy training subset.

For every parsed .npz, computes (over non-space, non-true-background
cells -- the "subject" convention already used in harness.py's
_compute_piece_metrics, applied here across the WHOLE canvas since
these files have no drawn "subject" boundary the way an in-progress
agent piece does):

  half_block_pct   -- % of subject cells that are UPPER/LOWER half
                       block (U+2580 UPPER, U+2584 LOWER) -- the
                       two-color-per-cell subpixel technique, NOT
                       counting the plain full block (kept separate,
                       per explicit instruction: "half-block %, shade
                       %, and full-block % are three metrics, not one
                       bucket" -- harness.py's own _HALF_BLOCK_CHARS
                       lumps upper/lower/full together for a DIFFERENT
                       purpose [gating an agent's in-progress piece]
                       and is deliberately NOT reused here).
  shade_pct        -- % of subject cells that are a RAMP density glyph
                       (U+2591 LIGHT, U+2592 MEDIUM, U+2593 DARK shade).
  full_block_pct   -- % of subject cells that are the plain full block
                       (U+2588), tracked separately since a flat-fill
                       piece can be nearly all full-block with zero
                       real half-block/shade technique.
  distinct_colors  -- number of distinct visible colors across all
                       subject cells (fg for non-space cells, bg for
                       space-with-nonzero-bg cells -- same "visible
                       color" convention as harness.py to avoid the
                       fg-vs-bg confusion bug documented there).
  alnum_pct        -- % of subject cells whose glyph is an ASCII
                       letter or digit (this is the "logos and text
                       layouts" signal the user wants to filter OUT of
                       the shading-heavy training subset: pieces that
                       are mostly rendered text/wordmarks rather than
                       shaded illustration).
  subject_cells    -- raw count (percentages are meaningless on a
                       near-empty file without this for context).

Usage:
    python3 corpus/technique_index.py [--parsed-dir corpus/parsed] [--manifest corpus/technique_manifest.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent

HALF_BLOCK_CP = {0x2580, 0x2584}          # ▀ ▄  (NOT full block, see docstring)
SHADE_CP = {0x2591, 0x2592, 0x2593}       # ░ ▒ ▓
FULL_BLOCK_CP = {0x2588}                  # █

# ASCII letters + digits only (0-9, A-Z, a-z) -- codepoint ranges, cheap
# to check without building a huge set.
def _is_alnum_cp(cp):
    return (0x30 <= cp <= 0x39) or (0x41 <= cp <= 0x5A) or (0x61 <= cp <= 0x7A)


def compute_technique_metrics(npz_path):
    d = np.load(npz_path)
    chars = d["chars"]
    fg = d["fg"]
    bg = d["bg"]

    is_space = (chars == 0x20)
    is_true_bg = is_space & (bg == 0)
    subject_mask = ~is_true_bg
    subject_cells = int(subject_mask.sum())

    if subject_cells == 0:
        return {
            "half_block_pct": 0.0, "shade_pct": 0.0, "full_block_pct": 0.0,
            "distinct_colors": 0, "alnum_pct": 0.0, "subject_cells": 0,
        }

    subj_chars = chars[subject_mask]
    subj_fg = fg[subject_mask]
    subj_bg = bg[subject_mask]
    subj_is_space = is_space[subject_mask]

    half_ct = np.isin(subj_chars, list(HALF_BLOCK_CP)).sum()
    shade_ct = np.isin(subj_chars, list(SHADE_CP)).sum()
    full_ct = np.isin(subj_chars, list(FULL_BLOCK_CP)).sum()

    # visible color = bg when the cell is a colored space, else fg --
    # same convention as harness.py's visible_idx, to avoid the
    # documented SGR-vs-palette-index confusion class.
    visible = np.where(subj_is_space, subj_bg, subj_fg)
    distinct_colors = int(np.unique(visible).size)

    alnum_ct = sum(1 for cp in subj_chars.tolist() if _is_alnum_cp(cp))

    return {
        "half_block_pct": 100.0 * int(half_ct) / subject_cells,
        "shade_pct": 100.0 * int(shade_ct) / subject_cells,
        "full_block_pct": 100.0 * int(full_ct) / subject_cells,
        "distinct_colors": distinct_colors,
        "alnum_pct": 100.0 * alnum_ct / subject_cells,
        "subject_cells": subject_cells,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--manifest", default=str(CORPUS_DIR / "technique_manifest.jsonl"))
    args = ap.parse_args()

    parsed_dir = Path(args.parsed_dir)
    files = sorted(parsed_dir.rglob("*.npz"))
    if not files:
        print("No .npz files found under", parsed_dir, file=sys.stderr)
        sys.exit(1)

    errors = []
    with open(args.manifest, "w") as out:
        for i, path in enumerate(files):
            rel = str(path.relative_to(parsed_dir))
            try:
                m = compute_technique_metrics(path)
            except Exception as e:
                errors.append((rel, str(e)))
                continue
            m["path"] = rel
            out.write(json.dumps(m) + "\n")
            if (i + 1) % 500 == 0:
                print(f"  ...{i+1}/{len(files)}")

    print(f"\nDone. {len(files) - len(errors)}/{len(files)} indexed, {len(errors)} errors.")
    if errors:
        print("Errors:")
        for rel, err in errors[:20]:
            print(f"  {rel}: {err}")
    print(f"Manifest written to {args.manifest}")


if __name__ == "__main__":
    main()
