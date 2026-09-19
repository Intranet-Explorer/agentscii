#!/usr/bin/env python3
"""corpus/prepare_training_data.py -- convert train_subsample.jsonl
into mlx_lm.lora's expected {train,valid,test}.jsonl format, using the
"messages" chat format (NOT "prompt"/"completion" -- see the real bug
documented below) with --mask-prompt masking the prompt in the loss so
only the completion/target contributes (user direction, 2026-09-19:
"loss masked to the FITM target only (not the context)").

The prompt embeds SAUCE year/group + per-window technique metrics as
conditioning (captions were dropped from v1, per prior direction).

A small internal validation/test split is carved out of the 40k
training subsample itself (NOT the frozen corpus holdout, which stays
completely untouched for the real eval_harness.py baseline/scoring --
this internal split is only for mlx_lm's own training-loss monitoring).

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
    return (
        f"Piece metadata: year={year} group={group} "
        f"half_block_pct={half:.1f} shade_pct={shade:.1f} shade_bucket={bucket}\n\n"
        "Below is a window of ANSI/textmode art, run-length encoded. "
        "Each line is 'r{row} col,FB:glyphs col,FB:glyphs ...' where F "
        "is the foreground color (hex 0-f) and B is the background "
        "color (hex 0-f), and 'glyphs' are the literal characters at "
        "that run. Background cells (space, color 07 or omitted) are "
        "not shown.\n\n"
        f"A rectangular region marked [MASK w={mask_w}] spanning "
        f"{mask_h} rows has been removed. Reconstruct ONLY that "
        f"region, consistent with the surrounding art.\n\n"
        f"{row['context']}\n\n"
        f"Reply with ONLY the reconstructed region as {mask_h} lines "
        f"in the same 'r00 col,FB:glyphs ...' format, using ROW/COLUMN "
        f"indices LOCAL to the masked region (r00 = the region's first "
        f"row, column 0 = the region's first column). No explanation."
    )


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

    rng = random.Random(args.seed)
    rng.shuffle(rows)

    n = len(rows)
    n_val = round(n * args.val_frac)
    n_test = round(n * args.test_frac)
    val_rows = rows[:n_val]
    test_rows = rows[n_val:n_val + n_test]
    train_rows = rows[n_val + n_test:]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split_rows in [("train", train_rows), ("valid", val_rows), ("test", test_rows)]:
        out_path = out_dir / f"{split_name}.jsonl"
        with open(out_path, "w") as f:
            for row in split_rows:
                prompt = build_prompt(row)
                completion = row["target"]
                # "messages" format (mlx_lm's ChatDataset), NOT
                # "prompt"/"completion" (CompletionsDataset) -- found
                # live: CompletionsDataset.process's own --mask-prompt
                # path has a real bug in mlx_lm 0.29.1 (passes
                # messages[0], a bare dict, to apply_chat_template,
                # which requires a LIST of messages; crashes with
                # "dict object has no element 0" on Mistral's chat
                # template). ChatDataset.process uses messages[:-1] (a
                # real list slice), which doesn't hit this bug --
                # verified working end-to-end before committing to it.
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
