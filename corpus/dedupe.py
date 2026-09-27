#!/usr/bin/env python3
"""Deduplicate the parsed corpus by content hash.

The same piece often appears in several packs (re-releases, compilations).
Hashes cell content only (chars, fg, bg), not path or SAUCE, and reports
exact duplicates.

Usage:
    python3 corpus/dedupe.py [--parsed-dir corpus/parsed] [--report corpus/dedupe_report.json]

Writes a report with:
  - total parsed files
  - unique content hashes
  - duplicate groups (hash -> paths)
  - one canonical path per hash (shortest, then alphabetical)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent


def content_hash(npz_path):
    """SHA-256 of a parsed piece's chars, fg and bg grids. Path and SAUCE are excluded."""
    d = np.load(npz_path)
    h = hashlib.sha256()
    h.update(d["chars"].tobytes())
    h.update(d["fg"].tobytes())
    h.update(d["bg"].tobytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--report", default=str(CORPUS_DIR / "dedupe_report.json"))
    args = ap.parse_args()

    parsed_dir = Path(args.parsed_dir)
    files = sorted(parsed_dir.rglob("*.npz"))
    if not files:
        print("No .npz files found under", parsed_dir, file=sys.stderr)
        sys.exit(1)

    hash_to_paths = {}
    errors = []
    for i, path in enumerate(files):
        rel = str(path.relative_to(parsed_dir))
        try:
            h = content_hash(path)
        except Exception as e:
            errors.append((rel, str(e)))
            continue
        hash_to_paths.setdefault(h, []).append(rel)
        if (i + 1) % 500 == 0:
            print(f"  ...{i+1}/{len(files)}")

    total = len(files)
    unique = len(hash_to_paths)
    dup_groups = {h: paths for h, paths in hash_to_paths.items() if len(paths) > 1}
    n_dup_files = sum(len(paths) for paths in dup_groups.values())
    n_dup_extra = n_dup_files - len(dup_groups)  # extra copies beyond one canonical each

    canonical = {}
    duplicates = {}
    for h, paths in hash_to_paths.items():
        # Shortest path favours the original pack over a nested compilation.
        chosen = sorted(paths, key=lambda p: (len(p), p))[0]
        canonical[h] = chosen
        for p in paths:
            if p != chosen:
                duplicates.setdefault(chosen, []).append(p)

    report = {
        "total_parsed_files": total,
        "unique_content_hashes": unique,
        "duplicate_groups": len(dup_groups),
        "duplicate_extra_copies": n_dup_extra,
        "errors": errors,
        "canonical_paths": sorted(canonical.values()),
        "duplicate_map": duplicates,  # canonical path -> [duplicate paths]
    }
    Path(args.report).write_text(json.dumps(report, indent=2))

    print(f"\nTotal parsed files: {total}")
    print(f"Unique pieces (by content hash): {unique}")
    print(f"Duplicate groups (2+ copies of the same piece): {len(dup_groups)}")
    print(f"Extra duplicate copies beyond one canonical each: {n_dup_extra}")
    if errors:
        print(f"Errors reading {len(errors)} files (see report)")
    print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
