#!/usr/bin/env python3
"""Convert train_subsample.jsonl to mlx_lm.lora train/valid/test.jsonl.

Uses the "messages" chat format; with --mask-prompt only the target counts
toward the loss. The prompt carries SAUCE year/group and window technique
metrics as conditioning.

valid/test here are carved from the training subsample for loss
monitoring only. The frozen corpus holdout is separate and untouched.

Usage:
    python3 corpus/prepare_training_data.py
"""
import argparse
import json
import random
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def build_prompt(row):
    group = row.get("sauce_group") or "unknown"
    year = row.get("sauce_year") or "unknown"
    half = row.get("half_block_pct", 0.0)
    shade = row.get("shade_pct", 0.0)
    bucket = row.get("shade_bucket", "unknown")
    mask_h, mask_w = row["mask_box"][2], row["mask_box"][3]
    # Tags and delimiters only; prose explaining the format just costs
    # tokens. The mask shape stays, since the model needs it.
    tag = (
        f"[Y={year} G={group} TIER={bucket} HALF={half:.1f} SHADE={shade:.1f} "
        f"MASKH={mask_h} MASKW={mask_w}]"
    )
    return f"{tag}\n<CTX>\n{row['context']}\n</CTX>\n<FILL>"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subsample", default=str(CORPUS_DIR / "train_subsample.jsonl"))
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "mlx_train_data"))
    ap.add_argument("--val-frac", type=float, default=0.03)
    ap.add_argument("--test-frac", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rows = []
    with open(args.subsample) as f:
        for line in f:
            rows.append(json.loads(line))

    # Split by parent piece, not by window. Windows overlap 50%, so a
    # window-level split leaks near-duplicates into valid/test.
    from collections import defaultdict
    by_parent = defaultdict(list)
    for row in rows:
        by_parent[row["parent_path"]].append(row)

    parents = list(by_parent.keys())
    rng = random.Random(args.seed)
    rng.shuffle(parents)

    n_rows = len(rows)
    n_val_target = round(n_rows * args.val_frac)
    n_test_target = round(n_rows * args.test_frac)

    val_rows, test_rows, train_rows = [], [], []
    val_parents, test_parents = set(), set()
    i = 0
    while i < len(parents) and len(val_rows) < n_val_target:
        p = parents[i]
        val_rows.extend(by_parent[p])
        val_parents.add(p)
        i += 1
    while i < len(parents) and len(test_rows) < n_test_target:
        p = parents[i]
        test_rows.extend(by_parent[p])
        test_parents.add(p)
        i += 1
    for p in parents[i:]:
        train_rows.extend(by_parent[p])

    # Shuffle so one piece's windows aren't contiguous.
    rng.shuffle(train_rows)
    rng.shuffle(val_rows)
    rng.shuffle(test_rows)

    train_parents_check = set(r["parent_path"] for r in train_rows)
    leak_val = train_parents_check & val_parents
    leak_test = train_parents_check & test_parents
    print(f"Parent-piece-level split: {len(parents)} unique pieces "
          f"({len(train_parents_check)} train / "
          f"{len(val_parents)} val / {len(test_parents)} test)")
    print(f"Leak check: {len(leak_val)} parent pieces in both train+val, "
          f"{len(leak_test)} in both train+test (must be 0)")
    assert not leak_val and not leak_test, "parent-piece split leaked -- do not proceed"

    n = len(rows)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split_rows in [("train", train_rows), ("valid", val_rows), ("test", test_rows)]:
        out_path = out_dir / f"{split_name}.jsonl"
        with open(out_path, "w") as f:
            for row in split_rows:
                prompt = build_prompt(row)
                completion = row["target"]
                # "messages", not prompt/completion: mlx_lm 0.29.1's
                # CompletionsDataset crashes under --mask-prompt with
                # Mistral's chat template. ChatDataset works.
                f.write(json.dumps({"messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion},
                ]}) + "\n")
        print(f"{split_name}: {len(split_rows)} examples -> {out_path}")

    print(f"\nTotal: {n} examples (train={len(train_rows)}, "
          f"valid={len(val_rows)}, test={len(test_rows)})")
    print(f"Output dir: {out_dir}")


if __name__ == "__main__":
    main()
