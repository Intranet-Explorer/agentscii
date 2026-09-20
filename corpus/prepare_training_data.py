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
    # Minimal tagged wrapper (user direction, 2026-09-20): the original
    # wrapper spent ~700 fixed chars of English prose re-explaining the
    # RLE format and reply instructions on EVERY example -- FITM doesn't
    # need that, the model only needs the conditioning tags and clear
    # context/target delimiters. Measured real-tokenizer impact: full
    # built prompt+target mean dropped from 2,105 to (re-measure and
    # report after this change -- see corpus/token_stats_wrapped.py).
    # Kept the SAME conditioning fields (year/group/shade_bucket/
    # half_block_pct/shade_pct) and the SAME [MASK w=..] marker inside
    # context (written by windowing.py, not this function) since the
    # model needs to know the mask's shape to reconstruct it -- only
    # the prose EXPLAINING the format was cut, not the information
    # content mask_h/mask_w carry.
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
