#!/usr/bin/env python3
"""Run the flat -> shaded adapter on agent-made pieces and render the results.

Per piece: parse, flatten with flatten_piece_and_merge (as in training),
tile into windows, shade each window with the adapter using the training
build_prompt, splice back, and render original, flat and shaded PNGs.

There is no ground truth; the output is for visual judgment.

Usage:
    python3 corpus/eval_on_raze.py --adapter-path corpus/lora_adapters_flatshaded \\
        --piece workspace/rejected/_reach.ans --piece workspace/rejected/_phosphor.ans \\
        --piece workspace/scratch/_guardian.v1.ans --out-dir corpus/raze_eval
"""
import argparse
import json
import os
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np
import harness
import windowing as w
import flat_shaded_pairs as fsp
from build_flat_shaded_dataset import build_prompt


def _write_ans(chars, fg, bg, out_path):
    lines = []
    for r in range(chars.shape[0]):
        parts = []
        cur_fg, cur_bg = None, None
        for c in range(chars.shape[1]):
            f, b, ch = int(fg[r, c]), int(bg[r, c]), chr(int(chars[r, c]))
            if (f, b) != (cur_fg, cur_bg):
                sgr_fg = 30 + (f % 8) + (60 if f >= 8 else 0)
                sgr_bg = 40 + (b % 8) + (60 if b >= 8 else 0)
                parts.append(f"\x1b[0;{sgr_fg};{sgr_bg}m")
                cur_fg, cur_bg = f, b
            parts.append(ch)
        lines.append("".join(parts))
    text = "\r\n".join(lines) + "\x1b[0m\r\n"
    out_path.write_bytes(text.encode("utf-8"))


def _grid_dict_to_arrays(grid, n_rows):
    """Convert harness._parse_ans_grid's {(row, col): (char, fg, bg)} to parse.py-style arrays."""
    n_cols = 80
    chars = np.full((n_rows, n_cols), ord(" "), dtype=np.uint32)
    fg = np.full((n_rows, n_cols), 7, dtype=np.uint8)
    bg = np.zeros((n_rows, n_cols), dtype=np.uint8)
    for (r, c), (ch, f, b) in grid.items():
        if r >= n_rows or c >= n_cols:
            continue
        chars[r, c] = ord(ch)
        fg[r, c] = f
        bg[r, c] = b
    return chars, fg, bg


def _parse_raze_piece(ans_path):
    """Parse an agent-authored piece with harness._parse_ans_grid.

    Not corpus/parse.py: that parser is CP437-only, and agent output can be
    UTF-8. harness._parse_ans_grid tries UTF-8 and falls back to CP437.
    """
    grid, total_lines = harness._parse_ans_grid(str(ans_path))
    return _grid_dict_to_arrays(grid, total_lines)


def eval_on_raze_piece(model, tokenizer, ans_path, out_dir, label):
    chars, fg, bg = _parse_raze_piece(ans_path)
    n_rows, n_cols = chars.shape
    print(f"  {ans_path}: {n_rows}x{n_cols}")

    if n_rows < w.WINDOW_ROWS or n_cols < w.WINDOW_COLS:
        print(f"    SKIP: smaller than one window ({n_rows}x{n_cols} < {w.WINDOW_ROWS}x{w.WINDOW_COLS})")
        return None

    flat_chars_full, flat_fg_full, flat_bg_full = fsp.flatten_piece_and_merge(chars, fg, bg)

    # Tile non-overlapping windows over the whole piece and splice each
    # shaded window back into a full-piece copy.
    shaded_full_chars = flat_chars_full.copy()
    shaded_full_fg = flat_fg_full.copy()
    shaded_full_bg = flat_bg_full.copy()

    from mlx_lm import generate as mlx_generate

    sauce_group = ""  # agent pieces carry no SAUCE
    sauce_year = "2026"
    n_windows_done = 0
    for r0 in range(0, n_rows - w.WINDOW_ROWS + 1, w.WINDOW_ROWS):
        for c0 in range(0, n_cols - w.WINDOW_COLS + 1, w.WINDOW_COLS):
            flat_c = flat_chars_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]
            flat_f = flat_fg_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]
            flat_b = flat_bg_full[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS]
            flat_text = w.encode_window(flat_c, flat_f, flat_b)
            if not flat_text:
                continue  # blank window

            half_pct, shade_pct = w.window_technique_metrics(flat_c, flat_f, flat_b)
            row = {
                "sauce_group": sauce_group, "sauce_year": sauce_year,
                "orig_half_block_pct": half_pct, "orig_shade_pct": shade_pct,
                "flat_text": flat_text,
            }
            prompt = build_prompt(row)
            messages = [{"role": "user", "content": prompt}]
            formatted = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
            raw_reply = mlx_generate(model, tokenizer, formatted, max_tokens=1200, verbose=False)

            try:
                out_h, out_w = w.WINDOW_ROWS, w.WINDOW_COLS
                model_chars, model_fg, model_bg = eh_decode_window_text(raw_reply, out_h, out_w)
            except Exception as e:
                print(f"    window ({r0},{c0}): decode failed ({e}), leaving flat")
                continue

            shaded_full_chars[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS] = model_chars
            shaded_full_fg[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS] = model_fg
            shaded_full_bg[r0:r0 + w.WINDOW_ROWS, c0:c0 + w.WINDOW_COLS] = model_bg
            n_windows_done += 1

    print(f"    {n_windows_done} windows shaded")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{label}"

    _write_ans(chars, fg, bg, base.with_suffix(".original.ans"))
    _write_ans(flat_chars_full, flat_fg_full, flat_bg_full, base.with_suffix(".flat.ans"))
    _write_ans(shaded_full_chars, shaded_full_fg, shaded_full_bg, base.with_suffix(".model_shaded.ans"))

    import base64
    results = {}
    for suffix in ["original", "flat", "model_shaded"]:
        ans_p = base.with_suffix(f".{suffix}.ans")
        png_p = base.with_suffix(f".{suffix}.png")
        b64, note = harness.render_ans_to_png_b64(str(ans_p))
        if b64:
            png_p.write_bytes(base64.b64decode(b64))
            results[suffix] = str(png_p)
        else:
            print(f"    render failed for {suffix}: {note}")
            results[suffix] = None

    return {"piece": str(ans_path), "label": label, "n_windows_shaded": n_windows_done, **{f"{k}_png": v for k, v in results.items()}}


def eh_decode_window_text(text, height, width):
    import eval_harness as eh
    return eh.decode_window_text(text, height, width)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default=os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--Mistral-Nemo-Instruct-2407-4bit/snapshots/647ca0751669b21a364c86ccc5df54c4d7e4e91c"))
    ap.add_argument("--adapter-path", required=True)
    ap.add_argument("--piece", action="append", required=True)
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "raze_eval"))
    args = ap.parse_args()

    from mlx_lm import load
    print(f"Loading base model + adapter {args.adapter_path}...")
    model, tokenizer = load(args.base_model, adapter_path=args.adapter_path)
    print("Loaded.")

    results = []
    for piece_path in args.piece:
        label = Path(piece_path).stem
        r = eval_on_raze_piece(model, tokenizer, piece_path, args.out_dir, label)
        if r:
            results.append(r)

    out_path = Path(args.out_dir) / "manifest.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\n{len(results)}/{len(args.piece)} pieces evaluated. Manifest: {out_path}")


if __name__ == "__main__":
    main()
