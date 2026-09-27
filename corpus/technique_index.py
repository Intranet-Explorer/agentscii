#!/usr/bin/env python3
"""Per-piece technique metrics over the parsed corpus, for selecting shading-heavy pieces.

Subject cells are all cells except true background (space on bg 0).
Metrics, as a share of subject cells:
  half_block_pct  -- ▀ ▄ only. Full block is counted separately, unlike
                     harness.py's _HALF_BLOCK_CHARS.
  shade_pct       -- ░ ▒ ▓
  full_block_pct  -- █; flat fills can be all full block with no technique.
  distinct_colors -- distinct visible colours (fg, or bg for a coloured space)
  alnum_pct       -- ASCII letters and digits; flags text and logo pieces.
  subject_cells   -- raw count, for judging the percentages.

Usage:
    python3 corpus/technique_index.py [--parsed-dir corpus/parsed] [--manifest corpus/technique_manifest.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent

HALF_BLOCK_CP = {0x2580, 0x2584}          # ▀ ▄  (not full block)
SHADE_CP = {0x2591, 0x2592, 0x2593}       # ░ ▒ ▓
FULL_BLOCK_CP = {0x2588}                  # █

# ASCII 0-9, A-Z, a-z.
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

    # Visible colour: bg for a coloured space, else fg (as harness.py).
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
