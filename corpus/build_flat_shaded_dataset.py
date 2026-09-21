#!/usr/bin/env python3
"""corpus/build_flat_shaded_dataset.py -- build the mlx_lm training
dataset for the flat->shaded task (user direction, 2026-09-20, the
REFRAMED objective after the real-piece test showed FITM-without-
conditioning only learns texture statistics: "build a 'flat -> shaded'
pair generator... the model learns to take a simple block-in and turn
it into detailed, shaded work -- which is precisely the skill raze
lacks").

Task shape: input = a flattened window (flatten_piece_and_merge, full
piece flattened+merged BEFORE windowing, per user direction -- window
crops of the flattened piece, not per-window flattening), RLE-encoded
the same way as the old FITM context. Target = the SAME window,
un-flattened (the real original), RLE-encoded the same way as the old
FITM target. No mask this time -- the whole window is visible in
flattened form; the task is "add the shading technique", not "guess
hidden content".

Only windows with real half_block_pct/shade_pct are used (a window
with 0% of either technique flattens to a no-op -- zero training
signal, same reasoning as flat_shaded_pairs.py's pick_example_windows
threshold).

Per-PIECE flatten+merge is cached (flatten once per parent piece, slice
many windows out of it) -- flattening 1.16k pieces to build ~30k
windows would otherwise re-flatten the same piece dozens of times.

Split at parent-piece level (same zero-leak logic as
prepare_training_data.py) directly into train.jsonl/valid.jsonl/
test.jsonl in mlx_lm's "messages" chat format, ready for
train_launch.py.

Usage:
    python3 corpus/build_flat_shaded_dataset.py --n-windows 6000 --out-dir corpus/mlx_train_data_flatshaded
"""
import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np

import windowing as w
import flat_shaded_pairs as fsp


def build_prompt(row):
    """Same tagged-header convention as prepare_training_data.py's
    build_prompt, minus the MASK fields (there's no mask in this task)
    and with an explicit FLAT->SHADE instruction tag so the model can
    tell this task apart from the old FIM task if both ever coexist in
    context (they won't in this dataset, but the tag costs ~6 tokens
    and removes any ambiguity for free)."""
    group = row.get("sauce_group") or "unknown"
    year = row.get("sauce_year") or "unknown"
    half = row.get("orig_half_block_pct", 0.0)
    shade = row.get("orig_shade_pct", 0.0)
    tag = f"[TASK=SHADE Y={year} G={group} HALF={half:.1f} SHADE={shade:.1f}]"
    return f"{tag}\n<FLAT>\n{row['flat_text']}\n</FLAT>\n<SHADE>"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-windows", type=int, default=6000)
    ap.add_argument("--min-half-block", type=float, default=10.0)
    ap.add_argument("--min-shade", type=float, default=10.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-frac", type=float, default=0.03)
    ap.add_argument("--test-frac", type=float, default=0.02)
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "mlx_train_data_flatshaded"))
    args = ap.parse_args()

    parsed_dir = CORPUS_DIR / "parsed"
    holdout = json.loads((CORPUS_DIR / "holdout_split.json").read_text())
    train_paths = holdout["train_paths"]

    rng = random.Random(args.seed)
    candidates = sorted(set(train_paths))
    rng.shuffle(candidates)

    windows = []
    flatten_cache = {}  # parent_path -> (flat_chars_full, flat_fg_full, flat_bg_full)
    n_pieces_flattened = 0
    t0 = time.time()

    for rel in candidates:
        if len(windows) >= args.n_windows:
            break
        npz_path = parsed_dir / rel
        try:
            d = np.load(npz_path)
        except Exception:
            continue
        chars_full, fg_full, bg_full = d["chars"], d["fg"], d["bg"]
        if chars_full.shape[0] < w.WINDOW_ROWS or chars_full.shape[1] < w.WINDOW_COLS:
            continue

        sauce_group = d["sauce_group"].item().decode("utf-8", "replace") if d["sauce_group"].size else ""
        sauce_date = d["sauce_date"].item().decode("utf-8", "replace") if d["sauce_date"].size else ""
        year = sauce_date[:4] if len(sauce_date) >= 4 and sauce_date[:4].isdigit() else rel.split("/")[0]

        # up to 2 windows per piece (real diversity of position without
        # spending the whole flatten cost on a single sample per piece)
        n_rows, n_cols = chars_full.shape
        max_row0 = n_rows - w.WINDOW_ROWS
        max_col0 = n_cols - w.WINDOW_COLS
        local_seed = int(hashlib.md5(rel.encode()).hexdigest()[:8], 16)
        local_rng = random.Random(local_seed)
        n_attempts = min(2, max(1, (max_row0 + 1) * (max_col0 + 1)))
        tried_positions = set()

        piece_flattened = False
        for _ in range(n_attempts):
            row0 = local_rng.randint(0, max_row0)
            col0 = local_rng.randint(0, max_col0)
            if (row0, col0) in tried_positions:
                continue
            tried_positions.add((row0, col0))

            c_win = chars_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
            f_win = fg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
            b_win = bg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
            half_pct, shade_pct = w.window_technique_metrics(c_win, f_win, b_win)
            if half_pct < args.min_half_block or shade_pct < args.min_shade:
                continue

            if rel not in flatten_cache:
                flat_chars_full, flat_fg_full, flat_bg_full = fsp.flatten_piece_and_merge(chars_full, fg_full, bg_full)
                flatten_cache[rel] = (flat_chars_full, flat_fg_full, flat_bg_full)
                n_pieces_flattened += 1
                piece_flattened = True
            flat_chars_full, flat_fg_full, flat_bg_full = flatten_cache[rel]

            flat_c = flat_chars_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
            flat_f = flat_fg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
            flat_b = flat_bg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]

            flat_text = w.encode_window(flat_c, flat_f, flat_b)
            target_text = w.encode_window(c_win, f_win, b_win)
            if not flat_text or not target_text:
                continue  # degenerate (fully blank after windowing) -- skip

            windows.append({
                "parent_path": rel, "row0": row0, "col0": col0,
                "sauce_group": sauce_group, "sauce_year": year,
                "orig_half_block_pct": half_pct, "orig_shade_pct": shade_pct,
                "flat_text": flat_text, "target_text": target_text,
            })
            if len(windows) >= args.n_windows:
                break

        if (n_pieces_flattened % 200 == 0) and piece_flattened:
            elapsed = time.time() - t0
            print(f"  ...{len(windows)} windows from {n_pieces_flattened} flattened pieces, {elapsed:.0f}s elapsed")

    elapsed = time.time() - t0
    print(f"\n{len(windows)} windows collected from {n_pieces_flattened} flattened pieces in {elapsed:.0f}s")

    # split at parent-piece level, same zero-leak logic as prepare_training_data.py
    from collections import defaultdict
    by_parent = defaultdict(list)
    for row in windows:
        by_parent[row["parent_path"]].append(row)

    parents = list(by_parent.keys())
    split_rng = random.Random(args.seed)
    split_rng.shuffle(parents)

    n_rows = len(windows)
    n_val_target = round(n_rows * args.val_frac)
    n_test_target = round(n_rows * args.test_frac)

    val_rows, test_rows, train_rows = [], [], []
    val_parents, test_parents = set(), set()
    i = 0
    while i < len(parents) and len(val_rows) < n_val_target:
        p = parents[i]; val_rows.extend(by_parent[p]); val_parents.add(p); i += 1
    while i < len(parents) and len(test_rows) < n_test_target:
        p = parents[i]; test_rows.extend(by_parent[p]); test_parents.add(p); i += 1
    for p in parents[i:]:
        train_rows.extend(by_parent[p])

    split_rng.shuffle(train_rows)
    split_rng.shuffle(val_rows)
    split_rng.shuffle(test_rows)

    train_parents_check = set(r["parent_path"] for r in train_rows)
    leak_val = train_parents_check & val_parents
    leak_test = train_parents_check & test_parents
    print(f"Parent-piece split: {len(parents)} pieces ({len(train_parents_check)} train / {len(val_parents)} val / {len(test_parents)} test)")
    print(f"Leak check: {len(leak_val)} train+val overlap, {len(leak_test)} train+test overlap (must be 0)")
    assert not leak_val and not leak_test, "parent-piece split leaked -- do not proceed"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split_rows in [("train", train_rows), ("valid", val_rows), ("test", test_rows)]:
        out_path = out_dir / f"{split_name}.jsonl"
        with open(out_path, "w") as f:
            for row in split_rows:
                prompt = build_prompt(row)
                completion = row["target_text"]
                f.write(json.dumps({"messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion},
                ]}) + "\n")
        print(f"{split_name}: {len(split_rows)} examples -> {out_path}")

    print(f"\nTotal: {n_rows} examples (train={len(train_rows)}, valid={len(val_rows)}, test={len(test_rows)})")
    print(f"Output dir: {out_dir}")


if __name__ == "__main__":
    main()
