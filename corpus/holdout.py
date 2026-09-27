#!/usr/bin/env python3
"""Deterministic train/holdout split, computed once and frozen before training.

Usage:
    python3 corpus/holdout.py [--manifest corpus/technique_manifest.jsonl]
                               [--fraction 0.05] [--seed 0]
                               [--out corpus/holdout_split.json]

Splits by distinct piece (dedupe.py's canonical paths, if the report
exists), and keeps every duplicate on the same side as its canonical, so
a held-out piece can't leak into training via a copy in another pack.
"""
import argparse
import json
import random
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(CORPUS_DIR / "technique_manifest.jsonl"))
    ap.add_argument("--dedupe-report", default=str(CORPUS_DIR / "dedupe_report.json"))
    ap.add_argument("--fraction", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(CORPUS_DIR / "holdout_split.json"))
    args = ap.parse_args()

    all_paths = []
    with open(args.manifest) as f:
        for line in f:
            all_paths.append(json.loads(line)["path"])
    all_paths_set = set(all_paths)

    # Without a dedupe report, split raw paths (no duplicate-leak protection).
    dedupe_path = Path(args.dedupe_report)
    if dedupe_path.exists():
        dd = json.loads(dedupe_path.read_text())
        canonical = [p for p in dd["canonical_paths"] if p in all_paths_set]
        dup_map = dd["duplicate_map"]
        split_unit = "canonical_content_hash"
    else:
        canonical = sorted(all_paths)
        dup_map = {}
        split_unit = "raw_path (no dedupe report found)"

    rng = random.Random(args.seed)
    shuffled = sorted(canonical)  # independent of manifest order
    rng.shuffle(shuffled)
    n_holdout = max(1, round(len(shuffled) * args.fraction))
    holdout_canonical = set(shuffled[:n_holdout])
    train_canonical = set(shuffled[n_holdout:])

    # Duplicates follow their canonical piece to the same side.
    holdout_paths = set()
    train_paths = set()
    for c in holdout_canonical:
        holdout_paths.add(c)
        holdout_paths.update(dup_map.get(c, []))
    for c in train_canonical:
        train_paths.add(c)
        train_paths.update(dup_map.get(c, []))

    # Paths missing from the dedupe report default to train.
    uncovered = all_paths_set - holdout_paths - train_paths
    train_paths.update(uncovered)

    out = {
        "split_unit": split_unit,
        "seed": args.seed,
        "fraction_requested": args.fraction,
        "n_canonical_pieces": len(shuffled),
        "n_canonical_holdout": len(holdout_canonical),
        "n_raw_paths_total": len(all_paths_set),
        "n_raw_paths_holdout": len(holdout_paths),
        "n_raw_paths_train": len(train_paths),
        "n_uncovered_defaulted_to_train": len(uncovered),
        "holdout_paths": sorted(holdout_paths),
        "train_paths": sorted(train_paths),
    }
    Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"Split unit: {split_unit}")
    print(f"Canonical pieces: {len(shuffled)}, holdout: {len(holdout_canonical)} "
          f"({100*len(holdout_canonical)/len(shuffled):.1f}%)")
    print(f"Raw paths: {len(all_paths_set)} total, "
          f"{len(holdout_paths)} holdout ({100*len(holdout_paths)/len(all_paths_set):.1f}%), "
          f"{len(train_paths)} train")
    if uncovered:
        print(f"WARNING: {len(uncovered)} manifest paths not covered by dedupe report, defaulted to train")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
