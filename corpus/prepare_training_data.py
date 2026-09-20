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

    # Split at the PARENT-PIECE level, not the window level (fix,
    # 2026-09-20: found live via a real val-loss curve turning up
    # while train loss kept falling at iteration 300-400 of a
    # 500-iteration run, well under 2% of the data seen -- too early
    # for genuine overfitting. Root-caused directly: windowing.py
    # slides 40x16 windows with 50% overlap in BOTH dimensions, so one
    # parent piece yields many highly-correlated, overlapping windows.
    # The OLD code shuffled and split at the WINDOW level -- verified
    # 75.7% of val-split parent pieces (661/873) also had windows in
    # the train split, and 436 parent pieces overlapped train/test.
    # Early in training, val "benefits" from leaked familiarity with
    # near-duplicate windows of pieces the model is actively training
    # on; as the model starts memorizing the SPECIFIC train windows
    # (not just general technique), that leaked advantage reverses --
    # exactly the turn-up-early signature observed. This split now
    # groups all windows by parent_path FIRST, shuffles PIECES (not
    # windows), and assigns each piece's ENTIRE window set to one
    # split -- guarantees zero parent-piece overlap between
    # train/valid/test, the same principle corpus/holdout.py already
    # uses for the outer holdout split, applied here to this inner
    # split too.
    #
    # NOTE: this is a different, additional split from
    # holdout_split.json (the frozen, content-hash-level corpus
    # holdout eval_harness.py/checkpoint_eval.py score against, never
    # touched by windowing.py's selection at all) -- this fixes the
    # SEPARATE, smaller train/valid/test split carved out of the 40k
    # training subsample itself, used only for mlx_lm's own
    # training-loss monitoring.
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

    # shuffle each split's rows so mlx_lm's own iterate_batches (which
    # sorts by length internally anyway, but takes the input list order
    # as its starting point) doesn't see all of one piece's windows in
    # a contiguous run
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
