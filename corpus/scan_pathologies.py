#!/usr/bin/env python3
"""corpus/scan_pathologies.py -- scan every training example for the
pathologies that can cause NaN loss or degenerate training (user
direction, 2026-09-19): empty/all-space window, zero-length FITM
target, target that's pure padding, sequence over the token cap.

Scans train_subsample.jsonl (the 40k pre-tokenization examples) AND
the tokenized mlx_train_data/{train,valid,test}.jsonl (post-conversion,
using the real tokenizer) so both the raw-content pathology and its
tokenized consequence are counted precisely.

Usage:
    python3 corpus/scan_pathologies.py
"""
import argparse
import json
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def scan_raw_subsample(path):
    """Pathologies visible directly in the RLE text, before tokenization."""
    counts = {
        "total": 0,
        "empty_target": 0,          # target == ""
        "empty_context": 0,         # context has no real 'rNN' content lines at all
        "target_all_same_glyph": 0, # target is fully one repeated (char,color) run -- degenerate but not necessarily wrong
    }
    bad_indices = {"empty_target": [], "empty_context": []}
    with open(path) as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            counts["total"] += 1
            target = row["target"]
            context = row["context"]
            if target.strip() == "":
                counts["empty_target"] += 1
                if len(bad_indices["empty_target"]) < 20:
                    bad_indices["empty_target"].append(i)
            # context has no real content rows (only the MASK marker line survives)
            content_lines = [l for l in context.splitlines() if l.startswith("r") and not l.startswith("MASK")]
            if not content_lines:
                counts["empty_context"] += 1
                if len(bad_indices["empty_context"]) < 20:
                    bad_indices["empty_context"].append(i)
            # crude "all one repeated run" check: target has exactly 1 distinct run signature
            import re
            runs = re.findall(r"\d+,[0-9a-f]{2}:(\S+)", target)
            if runs and len(set(runs)) == 1 and len(runs) == target.count("\n") + 1:
                counts["target_all_same_glyph"] += 1
    return counts, bad_indices


def scan_tokenized(mlx_data_dir, model_path, max_seq_length=3072):
    """Pathologies only visible after real tokenization: empty completion
    token span (ntoks=0 -> guaranteed NaN loss), sequences over the
    token cap (silently truncated by mlx_lm, which can chop a target's
    tail off entirely if the prompt alone already exceeds the cap)."""
    sys.path.insert(0, str(CORPUS_DIR.parent))
    sys.path.insert(0, "/Users/octo/Library/Python/3.9/lib/python/site-packages")
    from mlx_lm.utils import load
    from mlx_lm.tuner.datasets import load_local_dataset, CacheDataset
    import types

    print("Loading tokenizer (this loads the full model too, ~1-2s)...")
    model, tokenizer = load(model_path)
    config = types.SimpleNamespace(
        mask_prompt=True, prompt_feature="prompt", text_feature="text",
        completion_feature="completion", chat_feature="messages",
    )
    train_raw, valid_raw, test_raw = load_local_dataset(Path(mlx_data_dir), tokenizer, config)

    results = {}
    for split_name, split_raw in [("train", train_raw), ("valid", valid_raw), ("test", test_raw)]:
        if not split_raw:
            continue
        ds = CacheDataset(split_raw)
        n = len(ds)
        empty_completion = 0
        over_cap = 0
        empty_completion_indices = []
        for i in range(n):
            tokens, offset = ds[i]
            completion_len = len(tokens) - offset
            # Real threshold, found live: even a genuinely EMPTY target
            # string still tokenizes to exactly 2 tokens (a leading
            # space + EOS, confirmed directly: tokens[offset:] ==
            # [1032, 2] for a known real empty-target example) --
            # completion_len<=0 alone NEVER fires. <=2 is the correct
            # threshold for "the model is taught nothing here."
            if completion_len <= 2:
                empty_completion += 1
                if len(empty_completion_indices) < 20:
                    empty_completion_indices.append(i)
            if len(tokens) > max_seq_length:
                over_cap += 1
        results[split_name] = {
            "total": n,
            "empty_completion_span": empty_completion,
            "over_token_cap": over_cap,
            "empty_completion_sample_indices": empty_completion_indices,
        }
        print(f"  {split_name}: {n} examples, "
              f"{empty_completion} with empty/near-empty completion span (<=2 tokens), "
              f"{over_cap} over {max_seq_length} tokens")
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subsample", default=str(CORPUS_DIR / "train_subsample.jsonl"))
    ap.add_argument("--mlx-data-dir", default=str(CORPUS_DIR / "mlx_train_data"))
    ap.add_argument("--model", default="/Users/octo/.cache/huggingface/hub/models--mlx-community--Mistral-Nemo-Instruct-2407-4bit/snapshots/647ca0751669b21a364c86ccc5df54c4d7e4e91c")
    ap.add_argument("--out", default=str(CORPUS_DIR / "pathology_report.json"))
    ap.add_argument("--skip-tokenized", action="store_true", help="skip the slower tokenized scan (raw-text scan only)")
    args = ap.parse_args()

    print("=== Raw text scan (train_subsample.jsonl, 40k examples) ===")
    raw_counts, raw_bad = scan_raw_subsample(args.subsample)
    print(json.dumps(raw_counts, indent=2))

    report = {"raw_scan": raw_counts, "raw_bad_indices_sample": raw_bad}

    if not args.skip_tokenized:
        print("\n=== Tokenized scan (mlx_train_data/{train,valid,test}.jsonl) ===")
        tok_results = scan_tokenized(args.mlx_data_dir, args.model)
        report["tokenized_scan"] = tok_results

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nFull report: {args.out}")


if __name__ == "__main__":
    main()
