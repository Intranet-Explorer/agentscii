#!/usr/bin/env python3
"""corpus/holdout.py -- deterministic train/holdout split, computed
ONCE and frozen to disk before any training happens.

Usage:
    python3 corpus/holdout.py [--manifest corpus/technique_manifest.jsonl]
                               [--fraction 0.05] [--seed 0]
                               [--out corpus/holdout_split.json]

Splits by CONTENT HASH (via corpus/dedupe.py's canonical-path list, if a
dedupe report is present), not by raw file count, so a piece that
appears in 3 packs doesn't leak across train/holdout by having 2 of its
3 copies on one side and 1 on the other -- the split must be at the
level of *distinct pieces*, or a shading-heavy piece the model was
"held out" from could still have been trained on via a duplicate under
a different pack name.
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

    # Prefer splitting on canonical (deduped) pieces if a dedupe report
    # exists -- fall back to raw paths otherwise (still deterministic,
    # just without the duplicate-leak protection).
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
    shuffled = sorted(canonical)  # sort first for determinism regardless of manifest write order
    rng.shuffle(shuffled)
    n_holdout = max(1, round(len(shuffled) * args.fraction))
    holdout_canonical = set(shuffled[:n_holdout])
    train_canonical = set(shuffled[n_holdout:])

    # Expand each canonical piece back out to every raw path that shares
    # its content hash -- a duplicate of a held-out piece must ALSO be
    # held out, or it leaks the exact same content into training under
    # a different filename.
    holdout_paths = set()
    train_paths = set()
    for c in holdout_canonical:
        holdout_paths.add(c)
        holdout_paths.update(dup_map.get(c, []))
    for c in train_canonical:
        train_paths.add(c)
        train_paths.update(dup_map.get(c, []))

    # Any raw path not covered by the dedupe report (shouldn't happen if
    # the manifest and dedupe report were built from the same parsed
    # dir, but don't silently drop files if they were) defaults to train.
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
