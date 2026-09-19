#!/usr/bin/env python3
"""corpus/token_stats.py -- token-length stats per window (context +
target), using tiktoken (cl100k_base, a reasonable stand-in encoding
for length-budgeting purposes -- the actual training tokenizer may
differ, but relative comparisons across windows/formats hold either
way).

Usage:
    python3 corpus/token_stats.py [--windows corpus/windows.jsonl] [--sample N]
"""
import argparse
import json
import statistics
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def pctile(sorted_vals, p):
    if not sorted_vals:
        return 0
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--windows", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--sample", type=int, default=None,
                     help="only tokenize the first N windows, for a quick estimate on a huge file")
    args = ap.parse_args()

    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tok = lambda s: len(enc.encode(s))
        enc_name = "tiktoken cl100k_base"
    except ImportError:
        tok = lambda s: len(s) // 4  # rough chars/4 fallback, documented as approximate
        enc_name = "approximate (chars/4 -- tiktoken not installed)"

    context_lens = []
    target_lens = []
    total_lens = []
    char_context_lens = []
    char_target_lens = []
    n = 0
    with open(args.windows) as f:
        for line in f:
            if args.sample and n >= args.sample:
                break
            row = json.loads(line)
            ctx_tok = tok(row["context"])
            tgt_tok = tok(row["target"])
            context_lens.append(ctx_tok)
            target_lens.append(tgt_tok)
            total_lens.append(ctx_tok + tgt_tok)
            char_context_lens.append(len(row["context"]))
            char_target_lens.append(len(row["target"]))
            n += 1

    print(f"Tokenizer: {enc_name}")
    print(f"Windows measured: {n}\n")

    for label, vals in [("context", context_lens), ("target", target_lens), ("context+target", total_lens)]:
        if not vals:
            continue
        s = sorted(vals)
        print(f"{label} tokens: mean={statistics.mean(s):.0f} median={pctile(s,50):.0f} "
              f"p90={pctile(s,90):.0f} p99={pctile(s,99):.0f} max={s[-1]}")

    print()
    for label, vals in [("context chars", char_context_lens), ("target chars", char_target_lens)]:
        if not vals:
            continue
        s = sorted(vals)
        print(f"{label}: mean={statistics.mean(s):.0f} median={pctile(s,50):.0f} "
              f"p90={pctile(s,90):.0f} max={s[-1]}")

    if context_lens:
        ratio = statistics.mean(char_context_lens) / statistics.mean(context_lens)
        print(f"\nchars-per-token (context, informational): {ratio:.2f}")


if __name__ == "__main__":
    main()
