#!/usr/bin/env python3
"""corpus/checkpoint_eval.py -- evaluate one LoRA checkpoint against
the frozen holdout, using the SAME hardened eval methodology as
eval_harness.py (mask+fill+score+copy-detection), but running
inference directly via mlx_lm (base model + adapter checkpoint)
instead of Ollama, and rendering real PNG samples for every checkpoint
(user direction, 2026-09-19: "render samples at every checkpoint and
keep them -- I want to see them as images, not just metrics").

A FIXED set of holdout examples (same seed every call) is used across
ALL checkpoints, so metrics and renders are directly comparable
checkpoint to checkpoint -- not just comparable to the untrained
baseline once.

Usage:
    python3 corpus/checkpoint_eval.py --adapter-path corpus/lora_adapters/0000500_adapters.safetensors --n 15 --checkpoint-label iter500
    python3 corpus/checkpoint_eval.py --n 15 --checkpoint-label baseline   # no adapter = the untrained base model
"""
import argparse
import json
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np
import harness
import windowing as w
import eval_harness as eh

BASE_MODEL = "/Users/octo/.cache/huggingface/hub/models--mlx-community--Mistral-Nemo-Instruct-2407-4bit/snapshots/647ca0751669b21a364c86ccc5df54c4d7e4e91c"


def generate_fill_mlx(model, tokenizer, prompt, max_tokens=800):
    from mlx_lm import generate as mlx_generate
    messages = [{"role": "user", "content": prompt}]
    formatted = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    text = mlx_generate(model, tokenizer, formatted, max_tokens=max_tokens, verbose=False)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default=BASE_MODEL)
    ap.add_argument("--adapter-path", default=None, help="path to a checkpoint's adapters.safetensors dir; omit for the untrained base model")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42, help="FIXED seed across all checkpoints so the same examples are compared every time")
    ap.add_argument("--checkpoint-label", required=True, help="e.g. baseline, iter500, iter1000 -- used in output filenames")
    ap.add_argument("--opus-pairwise", action="store_true", help="run a blind Opus pairwise judgment per example (real cost -- see eval_harness.py's own pairwise for the same methodology)")
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--holdout-split", default=str(CORPUS_DIR / "holdout_split.json"))
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "checkpoint_evals"))
    args = ap.parse_args()

    from mlx_lm import load
    print(f"Loading base model{' + adapter ' + args.adapter_path if args.adapter_path else ' (no adapter -- baseline)'}...")
    t0 = time.time()
    if args.adapter_path:
        model, tokenizer = load(args.base_model, adapter_path=args.adapter_path)
    else:
        model, tokenizer = load(args.base_model)
    print(f"Loaded in {time.time()-t0:.1f}s")

    import random
    rng = random.Random(args.seed)

    split = json.loads(Path(args.holdout_split).read_text())
    holdout_paths = split["holdout_paths"]
    parsed_dir = Path(args.parsed_dir)

    candidates = rng.sample(holdout_paths, min(len(holdout_paths), args.n * 3))

    out_dir = Path(args.out_dir) / args.checkpoint_label
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    n_done = 0
    for rel in candidates:
        if n_done >= args.n:
            break
        npz_path = parsed_dir / rel
        try:
            d = np.load(npz_path)
        except Exception:
            continue
        chars_full, fg_full, bg_full = d["chars"], d["fg"], d["bg"]
        if chars_full.shape[0] < w.WINDOW_ROWS or chars_full.shape[1] < w.WINDOW_COLS:
            continue
        # re-seed a LOCAL rng per example so mask position is identical
        # across checkpoints for the SAME example (the shared `rng`
        # above is only used to pick WHICH examples, consumed once;
        # per-example mask placement uses its own derived seed so it's
        # reproducible independent of how many examples were skipped
        # before it in the candidate list)
        # hash(rel) is Python's built-in str hash, randomized per-process
        # by default (PYTHONHASHSEED) -- this made mask position differ
        # across SEPARATE PROCESS INVOCATIONS even for the identical
        # (rel, seed) pair, silently breaking the "same examples, same
        # mask position, directly comparable checkpoint to checkpoint"
        # claim this script's own docstring makes. Found live comparing
        # iter200 vs iter500 results.json: same 15 piece paths (that part
        # IS controlled by the outer `rng.sample(..., seed=args.seed)`
        # above, which only picks WHICH pieces) but different (row0,
        # col0) mask positions for 4/15 of them across the two runs --
        # each checkpoint eval was silently scoring a DIFFERENT actual
        # reconstruction task on those pieces, not the same one.
        # hashlib.md5 is stable across runs/processes -- use that.
        import hashlib
        local_seed = int(hashlib.md5(rel.encode()).hexdigest()[:8], 16)
        local_rng = random.Random(local_seed)
        row0 = local_rng.randint(0, chars_full.shape[0] - w.WINDOW_ROWS)
        col0 = local_rng.randint(0, chars_full.shape[1] - w.WINDOW_COLS)
        c_win = chars_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        f_win = fg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        b_win = bg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]

        context_text, target_text, mask_box = w.make_fitm_example(
            c_win, f_win, b_win, local_rng, fixed_mask_size=(8, 14)
        )
        top, left, mask_h, mask_w = mask_box

        prompt = eh.build_eval_prompt(d, rel, c_win, f_win, b_win, context_text, mask_box)
        try:
            raw_reply = generate_fill_mlx(model, tokenizer, prompt)
        except Exception as e:
            results.append({"path": rel, "error": f"mlx generate failed: {e}"})
            continue

        model_chars, model_fg, model_bg = eh.decode_window_text(raw_reply, mask_h, mask_w)
        truth_chars = c_win[top:top + mask_h, left:left + mask_w]
        truth_fg = f_win[top:top + mask_h, left:left + mask_w]
        truth_bg = b_win[top:top + mask_h, left:left + mask_w]

        model_half, model_shade = w.window_technique_metrics(model_chars, model_fg, model_bg)
        truth_half, truth_shade = w.window_technique_metrics(truth_chars, truth_fg, truth_bg)
        copy_exact, copy_overlap = eh.copy_detection_score(
            model_chars, model_fg, model_bg, c_win, f_win, b_win, top, left, mask_h, mask_w
        )

        # Render the FULL window with the model's fill spliced in, for
        # a real, inspectable image -- not just the isolated patch --
        # so a human can see the fill in its actual context.
        full_with_fill_chars = c_win.copy()
        full_with_fill_fg = f_win.copy()
        full_with_fill_bg = b_win.copy()
        full_with_fill_chars[top:top + mask_h, left:left + mask_w] = model_chars
        full_with_fill_fg[top:top + mask_h, left:left + mask_w] = model_fg
        full_with_fill_bg[top:top + mask_h, left:left + mask_w] = model_bg

        png_path = out_dir / f"{n_done:03d}_{Path(rel).stem}.png"
        eh.render_grid_to_png(full_with_fill_chars, full_with_fill_fg, full_with_fill_bg, png_path)
        truth_png_path = out_dir / f"{n_done:03d}_{Path(rel).stem}_truth.png"
        eh.render_grid_to_png(c_win, f_win, b_win, truth_png_path)

        result_entry = {
            "path": rel, "row0": row0, "col0": col0, "mask_box": list(mask_box),
            "model_half_block_pct": model_half, "model_shade_pct": model_shade,
            "truth_half_block_pct": truth_half, "truth_shade_pct": truth_shade,
            "model_copy_exact_frac": copy_exact, "model_copy_overlap_frac": copy_overlap,
            "render_path": str(png_path), "truth_render_path": str(truth_png_path),
            "raw_reply_len_chars": len(raw_reply),
        }

        if args.opus_pairwise:
            # Isolated-PATCH pairwise (matches eval_harness.py's own
            # methodology exactly, NOT the full-window render used
            # above) -- the full-window PNG is for human inspection,
            # the isolated patch is what Opus judges, same as the
            # hardened baseline, so pairwise win rates are directly
            # comparable checkpoint to checkpoint and against the
            # baseline.
            patch_model_png = out_dir / f"{n_done:03d}_{Path(rel).stem}_patch_model.png"
            patch_truth_png = out_dir / f"{n_done:03d}_{Path(rel).stem}_patch_truth.png"
            ok_m = eh.render_grid_to_png(model_chars, model_fg, model_bg, patch_model_png)
            ok_t = eh.render_grid_to_png(truth_chars, truth_fg, truth_bg, patch_truth_png)
            if ok_m and ok_t:
                result_entry["pairwise"] = eh.opus_pairwise_eval(patch_model_png, patch_truth_png)
            else:
                result_entry["pairwise"] = {"status": "error", "message": "render failed"}

        results.append(result_entry)
        n_done += 1
        print(f"  [{n_done}/{args.n}] {rel}: half={model_half:.1f}/{truth_half:.1f} "
              f"shade={model_shade:.1f}/{truth_shade:.1f} copy={copy_exact:.2f}/{copy_overlap:.2f}")

    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(results, indent=2))

    valid = [r for r in results if "error" not in r]
    print(f"\n{len(valid)}/{len(results)} completed without error.")
    if valid:
        import statistics
        summary = {
            "checkpoint_label": args.checkpoint_label,
            "adapter_path": args.adapter_path,
            "n_valid": len(valid),
            "n_total": len(results),
            "model_half_block_pct_mean": statistics.mean(r["model_half_block_pct"] for r in valid),
            "truth_half_block_pct_mean": statistics.mean(r["truth_half_block_pct"] for r in valid),
            "model_shade_pct_mean": statistics.mean(r["model_shade_pct"] for r in valid),
            "truth_shade_pct_mean": statistics.mean(r["truth_shade_pct"] for r in valid),
            "model_copy_exact_frac_mean": statistics.mean(r["model_copy_exact_frac"] for r in valid),
            "model_copy_overlap_frac_mean": statistics.mean(r["model_copy_overlap_frac"] for r in valid),
        }
        if args.opus_pairwise:
            pairwise_ok = [r["pairwise"]["winner"] for r in valid if r.get("pairwise", {}).get("status") == "ok"]
            summary["pairwise_model_wins"] = pairwise_ok.count("model")
            summary["pairwise_ground_truth_wins"] = pairwise_ok.count("ground_truth")
            summary["pairwise_ties"] = pairwise_ok.count("tie")
            summary["pairwise_n_judged"] = len(pairwise_ok)
        print(json.dumps(summary, indent=2))
        # append to a running cross-checkpoint summary log
        summary_log = Path(args.out_dir) / "checkpoint_summary.jsonl"
        with open(summary_log, "a") as f:
            f.write(json.dumps(summary) + "\n")
        print(f"\nAppended to {summary_log}")
    print(f"Full results + renders: {out_dir}")


if __name__ == "__main__":
    main()
