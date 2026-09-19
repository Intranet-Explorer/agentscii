#!/usr/bin/env python3
"""corpus/subsample.py -- stratified subsample to ~40k training
examples for the v1 run (user direction, 2026-09-19), keeping the p90
("high") shading tier over-represented relative to the full window
population (which is ALREADY oversampled 3x at the piece-selection
stage in windowing.py -- this subsample step further concentrates it,
it doesn't undo or replace that earlier oversampling).

Strategy: since windowing.py already oversampled p90-tier PIECES 3x
before windowing, the resulting windows.jsonl already has ~2x more
"high"-bucket windows than "mid" (787,772 vs 381,342 in the full
1,324,191-window set) -- this step samples a FIXED, EXPLICIT target
ratio (default 50% high / 35% mid / 15% low) out of that pool, rather
than just taking a uniform random 40k slice (which would already skew
high-heavy from the earlier oversampling, but not to a controlled,
reported ratio).

Usage:
    python3 corpus/subsample.py [--windows corpus/windows.jsonl]
                                 [--n 40000]
                                 [--high-frac 0.5] [--mid-frac 0.35] [--low-frac 0.15]
"""
import argparse
import json
import random
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--n", type=int, default=40000)
    ap.add_argument("--high-frac", type=float, default=0.50)
    ap.add_argument("--mid-frac", type=float, default=0.35)
    ap.add_argument("--low-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(CORPUS_DIR / "train_subsample.jsonl"))
    args = ap.parse_args()

    assert abs(args.high_frac + args.mid_frac + args.low_frac - 1.0) < 1e-6, "fractions must sum to 1.0"

    # Reservoir-style bucket pass: read the file ONCE (1.3M lines is
    # too large to hold every line in memory as parsed JSON), tracking
    # byte offsets per bucket, then a second pass seeks to the sampled
    # offsets -- avoids loading the whole 1.3M-line file into memory
    # twice or holding it all as Python objects at once.
    offsets = {"high": [], "mid": [], "low": []}
    with open(args.windows, "rb") as f:
        offset = f.tell()
        for raw_line in f:
            try:
                row = json.loads(raw_line)
                bucket = row.get("shade_bucket")
                if bucket in offsets:
                    offsets[bucket].append(offset)
            except Exception:
                pass
            offset = f.tell()

    print(f"Full pool: high={len(offsets['high'])} mid={len(offsets['mid'])} low={len(offsets['low'])}")

    rng = random.Random(args.seed)
    targets = {
        "high": round(args.n * args.high_frac),
        "mid": round(args.n * args.mid_frac),
        "low": round(args.n * args.low_frac),
    }
    chosen_offsets = []
    for bucket, target in targets.items():
        pool = offsets[bucket]
        take = min(target, len(pool))
        if take < target:
            print(f"WARNING: bucket '{bucket}' only has {len(pool)} windows, "
                  f"wanted {target} -- taking all {take} available, real shortfall reported honestly.")
        chosen_offsets.extend(rng.sample(pool, take))

    rng.shuffle(chosen_offsets)
    chosen_offsets_set = set(chosen_offsets)

    with open(args.windows, "rb") as f_in, open(args.out, "wb") as f_out:
        offset = f_in.tell()
        for raw_line in f_in:
            if offset in chosen_offsets_set:
                f_out.write(raw_line)
            offset = f_in.tell()

    print(f"\nSubsample written: {len(chosen_offsets)} examples -> {args.out}")
    print(f"Target ratio: high={args.high_frac} mid={args.mid_frac} low={args.low_frac}")
    print(f"Actual counts: high={min(targets['high'], len(offsets['high']))} "
          f"mid={min(targets['mid'], len(offsets['mid']))} "
          f"low={min(targets['low'], len(offsets['low']))}")


if __name__ == "__main__":
    main()
