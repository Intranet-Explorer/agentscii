#!/usr/bin/env python3
"""Mask a region of a real piece, fill it with a LoRA checkpoint, splice, and render.

Output per piece: the original with the fill spliced in (.ans and .png)
plus the untouched original, for visual comparison. Uses the same prompt
and decode path as checkpoint_eval.py.

Usage:
    python3 corpus/generate_region.py --adapter-path /tmp/ckpt_dirs/iter200 \\
        --piece 1994/dope0894/CM-TMD.ANS.npz --out-dir corpus/region_gen \\
        [--row0 R --col0 C] [--mask-h 8] [--mask-w 14] [--seed 1]

    # or let it pick a window/mask position itself:
    python3 corpus/generate_region.py --adapter-path /tmp/ckpt_dirs/iter200 \\
        --piece 1994/dope0894/CM-TMD.ANS.npz --out-dir corpus/region_gen
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
import eval_harness as eh


def _write_ans(chars, fg, bg, out_path):
    """Write cell arrays as a UTF-8 .ans, same encoding as eval_harness.render_grid_to_png."""
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


def generate_region(
    model, tokenizer, piece_npz_path, out_dir, label,
    row0=None, col0=None, mask_h=8, mask_w=14, seed=1,
):
    """Fill one masked region and splice it into a copy of the whole piece.

    Writes spliced and original .ans/.png. Returns paths and technique
    metrics; there is no ground truth to score against.
    """
    d = np.load(piece_npz_path)
    chars_full, fg_full, bg_full = d["chars"], d["fg"], d["bg"]
    n_rows, n_cols = chars_full.shape

    if n_rows < mask_h + 2 or n_cols < mask_w + 2:
        raise ValueError(f"{piece_npz_path}: piece too small ({n_rows}x{n_cols}) for a {mask_h}x{mask_w} mask")

    rng = __import__("random").Random(seed)
    if row0 is None:
        row0 = rng.randint(0, n_rows - mask_h)
    if col0 is None:
        col0 = rng.randint(0, n_cols - mask_w)

    # Context is one training-sized window around the mask, clamped to
    # the piece, to match the training input.
    win_r0 = max(0, min(row0 - (w.WINDOW_ROWS - mask_h) // 2, n_rows - w.WINDOW_ROWS))
    win_c0 = max(0, min(col0 - (w.WINDOW_COLS - mask_w) // 2, n_cols - w.WINDOW_COLS))
    win_r0, win_c0 = max(0, win_r0), max(0, win_c0)
    if n_rows < w.WINDOW_ROWS or n_cols < w.WINDOW_COLS:
        raise ValueError(f"{piece_npz_path}: piece smaller than one training window ({n_rows}x{n_cols} < {w.WINDOW_ROWS}x{w.WINDOW_COLS})")

    c_win = chars_full[win_r0:win_r0 + w.WINDOW_ROWS, win_c0:win_c0 + w.WINDOW_COLS]
    f_win = fg_full[win_r0:win_r0 + w.WINDOW_ROWS, win_c0:win_c0 + w.WINDOW_COLS]
    b_win = bg_full[win_r0:win_r0 + w.WINDOW_ROWS, win_c0:win_c0 + w.WINDOW_COLS]

    top, left = row0 - win_r0, col0 - win_c0

    # Same context format as make_fitm_example, but at a fixed mask
    # position, which that function doesn't support. Keep the two in sync.
    lines = []
    for r in range(w.WINDOW_ROWS):
        row_chars = [chr(cp) for cp in c_win[r].tolist()]
        row_fg = f_win[r].tolist()
        row_bg = b_win[r].tolist()
        if top <= r < top + mask_h:
            left_body = w.rle_encode_row(row_chars[:left], row_fg[:left], row_bg[:left])
            right_runs = w.rle_encode_row_runs(
                row_chars[left + mask_w:], row_fg[left + mask_w:], row_bg[left + mask_w:]
            )
            right_body = " ".join(
                f"{col + left + mask_w},{color}:{glyphs}" for col, color, glyphs in right_runs
            )
            body_parts = [p for p in (left_body, f"[MASK w={mask_w}]", right_body) if p]
            body = " ".join(body_parts)
        else:
            body = w.rle_encode_row(row_chars, row_fg, row_bg)
        if body:
            lines.append(f"r{r:02d} {body}")
    lines.insert(0, f"MASK rows {top}-{top + mask_h - 1} cols {left}-{left + mask_w - 1}")
    context_text = "\n".join(lines)
    mask_box = (top, left, mask_h, mask_w)

    prompt = eh.build_eval_prompt(d, str(piece_npz_path), c_win, f_win, b_win, context_text, mask_box)

    from mlx_lm import generate as mlx_generate
    messages = [{"role": "user", "content": prompt}]
    formatted = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    raw_reply = mlx_generate(model, tokenizer, formatted, max_tokens=800, verbose=False)

    model_chars, model_fg, model_bg = eh.decode_window_text(raw_reply, mask_h, mask_w)
    model_half, model_shade = w.window_technique_metrics(model_chars, model_fg, model_bg)

    # Splice into a copy of the whole piece.
    spliced_chars = chars_full.copy()
    spliced_fg = fg_full.copy()
    spliced_bg = bg_full.copy()
    spliced_chars[row0:row0 + mask_h, col0:col0 + mask_w] = model_chars
    spliced_fg[row0:row0 + mask_h, col0:col0 + mask_w] = model_fg
    spliced_bg[row0:row0 + mask_h, col0:col0 + mask_w] = model_bg

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(piece_npz_path).stem.replace(".ans", "").replace(".ANS", "").replace(".asc", "").replace(".ASC", "")
    base = out_dir / f"{label}_{stem}"

    _write_ans(spliced_chars, spliced_fg, spliced_bg, base.with_suffix(".spliced.ans"))
    _write_ans(chars_full, fg_full, bg_full, base.with_suffix(".original.ans"))
    ok_spliced = eh.render_grid_to_png(spliced_chars, spliced_fg, spliced_bg, base.with_suffix(".spliced.png"))
    ok_original = eh.render_grid_to_png(chars_full, fg_full, bg_full, base.with_suffix(".original.png"))

    return {
        "piece": str(piece_npz_path), "label": label,
        "row0": row0, "col0": col0, "mask_h": mask_h, "mask_w": mask_w,
        "model_half_block_pct": model_half, "model_shade_pct": model_shade,
        "spliced_ans": str(base.with_suffix(".spliced.ans")),
        "original_ans": str(base.with_suffix(".original.ans")),
        "spliced_png": str(base.with_suffix(".spliced.png")) if ok_spliced else None,
        "original_png": str(base.with_suffix(".original.png")) if ok_original else None,
        "raw_reply_len_chars": len(raw_reply),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default=os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--Mistral-Nemo-Instruct-2407-4bit/snapshots/647ca0751669b21a364c86ccc5df54c4d7e4e91c"))
    ap.add_argument("--adapter-path", default=None, help="omit for the untrained base model")
    ap.add_argument("--piece", action="append", required=True, help="relative path under corpus/parsed, repeatable for multiple pieces")
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "region_gen"))
    ap.add_argument("--label", default="gen")
    ap.add_argument("--row0", type=int, default=None)
    ap.add_argument("--col0", type=int, default=None)
    ap.add_argument("--mask-h", type=int, default=8)
    ap.add_argument("--mask-w", type=int, default=14)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    from mlx_lm import load
    print(f"Loading base model{' + adapter ' + args.adapter_path if args.adapter_path else ' (no adapter)'}...")
    if args.adapter_path:
        model, tokenizer = load(args.base_model, adapter_path=args.adapter_path)
    else:
        model, tokenizer = load(args.base_model)
    print("Loaded.")

    parsed_dir = Path(args.parsed_dir)
    results = []
    for piece_rel in args.piece:
        piece_path = parsed_dir / piece_rel
        if not piece_path.exists():
            print(f"SKIP {piece_rel}: not found under {parsed_dir}")
            continue
        try:
            r = generate_region(
                model, tokenizer, piece_path, args.out_dir, args.label,
                row0=args.row0, col0=args.col0, mask_h=args.mask_h, mask_w=args.mask_w,
                seed=args.seed,
            )
            results.append(r)
            print(f"  {piece_rel}: half={r['model_half_block_pct']:.1f} shade={r['model_shade_pct']:.1f} "
                  f"-> {r['spliced_png']}")
        except Exception as e:
            print(f"  {piece_rel}: FAILED ({e})")

    out_path = Path(args.out_dir) / f"{args.label}_manifest.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\n{len(results)}/{len(args.piece)} generated. Manifest: {out_path}")


if __name__ == "__main__":
    main()
