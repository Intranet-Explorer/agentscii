#!/usr/bin/env python3
"""corpus/technique_report.py -- distribution report over
technique_manifest.jsonl, to pick thresholds for a shading-heavy
training subset (gradients/form/lighting -- NOT logos/text layouts).

Usage:
    python3 corpus/technique_report.py [--manifest corpus/technique_manifest.jsonl]
                                        [--min-subject-cells 200]
"""
import argparse
import json
import statistics
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent

METRICS = ["half_block_pct", "shade_pct", "full_block_pct", "alnum_pct", "distinct_colors"]

PERCENTILES = [1, 5, 10, 25, 50, 75, 90, 95, 99]


def pctile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(CORPUS_DIR / "technique_manifest.jsonl"))
    ap.add_argument("--min-subject-cells", type=int, default=200,
                     help="exclude near-empty/tiny pieces from the distribution (they have unstable %% stats)")
    args = ap.parse_args()

    rows = []
    with open(args.manifest) as f:
        for line in f:
            rows.append(json.loads(line))

    total = len(rows)
    rows = [r for r in rows if r["subject_cells"] >= args.min_subject_cells]
    print(f"Total pieces in manifest: {total}")
    print(f"Pieces with >= {args.min_subject_cells} subject cells: {len(rows)} "
          f"({100*len(rows)/total:.1f}%)\n")

    print(f"{'metric':<20} {'mean':>8} {'p50':>8} {'p90':>8} {'p95':>8} {'p99':>8} {'max':>8}")
    dists = {}
    for m in METRICS:
        vals = sorted(r[m] for r in rows)
        dists[m] = vals
        mean = statistics.mean(vals) if vals else 0
        p50, p90, p95, p99 = (pctile(vals, p) for p in (50, 90, 95, 99))
        mx = vals[-1] if vals else 0
        print(f"{m:<20} {mean:>8.2f} {p50:>8.2f} {p90:>8.2f} {p95:>8.2f} {p99:>8.2f} {mx:>8.2f}")

    print()
    # Report candidate-subset size across a RANGE of thresholds rather
    # than picking one -- "above the corpus median" would keep half the
    # corpus, which isn't a meaningful "shading-heavy" filter. Also
    # requires distinct_colors >= 4 as a floor: a piece can have high
    # half_block_pct or shade_pct while being nearly monochrome (e.g. a
    # 2-color halftone effect), which is a real but different technique
    # from the graduated lit-to-shadow color transitions the user means.
    print("Candidate shading-heavy subset size at various thresholds")
    print("(half_block_pct > H OR shade_pct > S, AND alnum_pct < 15, AND distinct_colors >= 4):\n")
    print(f"{'H (half-block%)':>16} {'S (shade%)':>12} {'alnum<15':>10} {'colors>=4':>10} {'n':>8} {'pct':>7}")
    for h_thresh, s_thresh in [(10, 5), (20, 10), (30, 15), (36.8, 38.3), (42.3, 46.4)]:
        subset = [
            r for r in rows
            if (r["half_block_pct"] > h_thresh or r["shade_pct"] > s_thresh)
            and r["alnum_pct"] < 15.0
            and r["distinct_colors"] >= 4
        ]
        print(f"{h_thresh:>16.1f} {s_thresh:>12.1f} {'yes':>10} {'yes':>10} "
              f"{len(subset):>8} {100*len(subset)/len(rows):>6.1f}%")
    print("\n(the middle row's H/S are this corpus's own p90 values for each metric --")
    print(" i.e. 'meaningfully above 90% of all archive pieces on either half-block or shade usage')")


if __name__ == "__main__":
    main()
