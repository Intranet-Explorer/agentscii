#!/usr/bin/env python3
"""corpus/score_shipped.py -- score every shipped AGENTSCII piece
against the corpus technique_manifest.jsonl percentile distribution,
using the SAME subject-only metric definitions as technique_index.py
(half_block_pct, shade_pct over non-true-background subject cells).

Shipped pieces are agent-authored UTF-8 (not CP437 like the real
archive), so they're parsed via harness.py's own _parse_ans_grid
(correct UTF-8 decode) rather than corpus/parse.py (built for CP437
archive files) -- but the METRIC FORMULAS applied afterward are
identical to technique_index.py's, cell for cell, so the numbers are
directly comparable.

Usage:
    python3 corpus/score_shipped.py
"""
import json
import sys
from pathlib import Path

AGENTSCII_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
import harness

CORPUS_DIR = Path(__file__).resolve().parent

HALF_BLOCK_CHARS = set("\u2580\u2584")  # ▀ ▄  (matches technique_index.py, NOT harness's own _HALF_BLOCK_CHARS which lumps in █)
SHADE_CHARS = set("\u2591\u2592\u2593")  # ░ ▒ ▓


def score_piece(path):
    """Subject-only half_block_pct/shade_pct. Delegates directly to
    harness._compute_piece_metrics (which was fixed 2026-09-19 to use
    this exact glyph set/denominator) rather than reimplementing the
    same logic a second time -- two independent implementations of
    "the same definition" are how they silently drift apart again."""
    m = harness._compute_piece_metrics(path)
    if m is None or m["subject_cell_count"] == 0:
        return None
    return {
        "half_block_pct": m["half_block_pct"],
        "shade_pct": m["shade_char_pct"],
        "subject_cells": m["subject_cell_count"],
    }


def percentile_of(value, sorted_dist):
    """What fraction of sorted_dist is <= value -- i.e. this piece's
    percentile RANK within the corpus distribution."""
    if not sorted_dist:
        return None
    import bisect
    idx = bisect.bisect_right(sorted_dist, value)
    return 100.0 * idx / len(sorted_dist)


def main():
    # Load the corpus distribution (subject-only, same definition)
    half_dist = []
    shade_dist = []
    with open(CORPUS_DIR / "technique_manifest.jsonl") as f:
        for line in f:
            row = json.loads(line)
            if row["subject_cells"] < 50:  # skip near-empty pieces, unstable %
                continue
            half_dist.append(row["half_block_pct"])
            shade_dist.append(row["shade_pct"])
    half_dist.sort()
    shade_dist.sort()
    print(f"Corpus distribution: {len(half_dist)} pieces (subject_cells >= 50)")

    gallery = AGENTSCII_ROOT / "workspace" / "gallery"
    pieces = sorted(gallery.glob("pack*/*.ans"))
    results = []
    for p in pieces:
        m = score_piece(p)
        if m is None:
            continue
        half_pctile = percentile_of(m["half_block_pct"], half_dist) or 0.0
        shade_pctile = percentile_of(m["shade_pct"], shade_dist) or 0.0
        results.append({
            "path": str(p.relative_to(gallery)),
            "half_block_pct": round(m["half_block_pct"], 1),
            "half_block_percentile": round(half_pctile, 1),
            "shade_pct": round(m["shade_pct"], 1),
            "shade_percentile": round(shade_pctile, 1),
            "subject_cells": m["subject_cells"],
        })

    results.sort(key=lambda r: -(r["half_block_percentile"] + r["shade_percentile"]))

    print(f"\n{len(results)} shipped pieces scored.\n")
    print(f"{'piece':<45} {'half%':>7} {'half_pctile':>12} {'shade%':>7} {'shade_pctile':>13}")
    for r in results:
        print(f"{r['path']:<45} {r['half_block_pct']:>7.1f} {r['half_block_percentile']:>11.1f}% "
              f"{r['shade_pct']:>7.1f} {r['shade_percentile']:>12.1f}%")

    import statistics
    half_pctiles = [r["half_block_percentile"] for r in results]
    shade_pctiles = [r["shade_percentile"] for r in results]
    print(f"\nSummary across {len(results)} shipped pieces:")
    print(f"  half_block percentile: mean={statistics.mean(half_pctiles):.1f} median={statistics.median(half_pctiles):.1f}")
    print(f"  shade percentile:      mean={statistics.mean(shade_pctiles):.1f} median={statistics.median(shade_pctiles):.1f}")

    out_path = CORPUS_DIR / "shipped_scoring_report.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull report: {out_path}")


if __name__ == "__main__":
    main()
