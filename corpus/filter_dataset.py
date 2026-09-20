#!/usr/bin/env python3
"""corpus/filter_dataset.py -- drop pathological examples from
train_subsample.jsonl and rebuild the training data (user direction,
2026-09-20, task 2): "Drop all over-cap, empty-target, and
single-glyph examples. Rebuild the dataset; report new counts."

Three drop conditions, checked in this order (an example counts once,
under whichever condition it hits first):
  1. empty_target       -- target.strip() == ""
  2. single_glyph_target -- target is one repeated (char,color) run
     (same regex-based check as scan_pathologies.py's raw-text scan,
     kept identical so the two reports are directly comparable)
  3. over_cap           -- REAL tokenized length (via
     prepare_training_data.build_prompt + tokenizer.apply_chat_template
     on the full {"messages": [user, assistant]} pair, the exact same
     path mlx_lm's ChatDataset.process uses and the exact same path
     scan_pathologies.py's tokenized_scan measured) exceeds
     max_seq_length. This is NOT a token-count estimate -- it's the
     real tokenizer, so a kept example is guaranteed to fit.

Writes the filtered set back to --subsample-out (default: overwrites
train_subsample.jsonl, after saving the untouched original to
train_subsample_pre_filter.jsonl.bak), then re-runs
prepare_training_data.main()-equivalent logic is left to the caller
(run prepare_training_data.py separately) so this script does exactly
one job.

Usage:
    python3 corpus/filter_dataset.py
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))
from prepare_training_data import build_prompt  # noqa: E402


def is_empty_target(target):
    return target.strip() == ""


def is_single_glyph_target(target):
    runs = re.findall(r"\d+,[0-9a-f]{2}:(\S+)", target)
    return bool(runs) and len(set(runs)) == 1 and len(runs) == target.count("\n") + 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subsample", default=str(CORPUS_DIR / "train_subsample.jsonl"))
    ap.add_argument("--subsample-out", default=str(CORPUS_DIR / "train_subsample.jsonl"))
    ap.add_argument("--backup", default=str(CORPUS_DIR / "train_subsample_pre_filter.jsonl.bak"))
    ap.add_argument("--max-seq-length", type=int, default=4096)
    ap.add_argument("--model", default="/Users/octo/.cache/huggingface/hub/models--mlx-community--Mistral-Nemo-Instruct-2407-4bit/snapshots/647ca0751669b21a364c86ccc5df54c4d7e4e91c")
    ap.add_argument("--report", default=str(CORPUS_DIR / "filter_report.json"))
    args = ap.parse_args()

    src = Path(args.subsample)
    if not Path(args.backup).exists():
        shutil.copy(src, args.backup)
        print(f"Backed up untouched original to {args.backup}")
    else:
        print(f"Backup already exists at {args.backup}, not overwriting it.")

    sys.path.insert(0, "/Users/octo/Library/Python/3.9/lib/python/site-packages")
    from mlx_lm.utils import load
    print("Loading tokenizer (loads full model weights too)...")
    _, tokenizer = load(args.model)

    rows = []
    with open(args.backup) as f:
        for line in f:
            rows.append(json.loads(line))

    counts = {
        "total": len(rows),
        "empty_target": 0,
        "single_glyph_target": 0,
        "over_cap": 0,
        "kept": 0,
    }
    kept_rows = []
    for i, row in enumerate(rows):
        target = row["target"]
        if is_empty_target(target):
            counts["empty_target"] += 1
            continue
        if is_single_glyph_target(target):
            counts["single_glyph_target"] += 1
            continue
        prompt = build_prompt(row)
        messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": target},
        ]
        tokens = tokenizer.apply_chat_template(messages)
        if len(tokens) > args.max_seq_length:
            counts["over_cap"] += 1
            continue
        kept_rows.append(row)
        if (i + 1) % 5000 == 0:
            print(f"  scanned {i + 1}/{len(rows)}...")

    counts["kept"] = len(kept_rows)

    with open(args.subsample_out, "w") as f:
        for row in kept_rows:
            f.write(json.dumps(row) + "\n")

    Path(args.report).write_text(json.dumps(counts, indent=2))
    print(json.dumps(counts, indent=2))
    print(f"\nFiltered dataset written to {args.subsample_out}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
