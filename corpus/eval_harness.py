#!/usr/bin/env python3
"""Fill-in-the-middle eval on the frozen holdout.

Masks a region, has a model fill it, scores half_block_pct/shade_pct and
copy detection on the fill, and optionally runs a blind pairwise judgment
against the original. Run on the untrained base model first for a baseline.

Usage:
    python3 corpus/eval_harness.py --model qwen3.8:27b-mlx --n 30
    python3 corpus/eval_harness.py --model <some-8b-model> --n 30
"""
import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np
import harness
import windowing as w
import prepare_training_data as ptd

OLLAMA_URL = "http://localhost:11434/api/chat"

_RUN_RE = re.compile(r"(\d+),([0-9a-f]{2}):(.*?)(?=\s\d+,[0-9a-f]{2}:|\s\[MASK|$)")


def decode_rle_row(body, width):
    """Inverse of windowing.rle_encode_row.

    Parses 'col,fgbg:glyphs ...' into a width-length list of (char, fg, bg);
    unlisted cells are true background.
    """
    row = [(" ", 7, 0)] * width
    for m in _RUN_RE.finditer(body):
        col = int(m.group(1))
        color = m.group(2)
        fg, bg = int(color[0], 16), int(color[1], 16)
        glyphs = m.group(3)
        for i, ch in enumerate(glyphs):
            pos = col + i
            if 0 <= pos < width:
                row[pos] = (ch, fg, bg)
    return row


def decode_window_text(text, height, width):
    """Inverse of encode_window: 'rNN <body>' lines to (height, width) char/fg/bg arrays.

    Missing rows are true background.
    """
    chars = np.full((height, width), 0x20, dtype=np.uint32)
    fg = np.full((height, width), 7, dtype=np.uint8)
    bg = np.zeros((height, width), dtype=np.uint8)
    for line in text.splitlines():
        # lstrip only: rstrip would drop a trailing run of coloured spaces.
        line = line.lstrip()
        m = re.match(r"^r(\d+)\s+(.*)$", line)
        if not m:
            continue
        r = int(m.group(1))
        if not (0 <= r < height):
            continue
        body = m.group(2)
        row = decode_rle_row(body, width)
        for c, (ch, f, b) in enumerate(row):
            chars[r, c] = ord(ch) if ch else 0x20
            fg[r, c] = f
            bg[r, c] = b
    return chars, fg, bg


def _round_trip_self_test():
    """Encode and decode a random grid; True if visible cells match exactly.

    Scores are meaningless if this fails.
    """
    rng = np.random.default_rng(0)
    h, wd = w.WINDOW_ROWS, w.WINDOW_COLS
    chars = rng.choice([0x20, 0x2580, 0x2584, 0x2591, ord("X"), ord("#")], size=(h, wd))
    fg = rng.integers(0, 16, size=(h, wd), dtype=np.uint8)
    bg = rng.integers(0, 16, size=(h, wd), dtype=np.uint8)
    # Make some cells true background (space, bg=0), which the encoder omits.
    is_bg = (chars == 0x20) & (rng.random((h, wd)) < 0.3)
    bg = np.where(is_bg, 0, bg)
    text = w.encode_window(chars, fg, bg)
    d_chars, d_fg, d_bg = decode_window_text(text, h, wd)
    # Compare emitted cells only; omitted background cells don't keep fg.
    visible_mask = ~((chars == 0x20) & (bg == 0))
    chars_match = np.array_equal(chars[visible_mask], d_chars[visible_mask])
    fg_match = np.array_equal(fg[visible_mask], d_fg[visible_mask])
    bg_match = np.array_equal(bg[visible_mask], d_bg[visible_mask])
    return chars_match and fg_match and bg_match


def call_ollama_fill(model, prompt, timeout=180, num_predict=800):
    """Ask an Ollama model to fill the mask. Returns the reply text.

    "think": False is required: Qwen3 models otherwise spend the whole
    num_predict budget on a hidden reasoning trace and return empty content.
    num_predict caps a runaway generation (about 2.5x the p90 target length).
    """
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {**harness.SAMPLING, "num_predict": num_predict},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        r = json.loads(resp.read())
    return r.get("message", {}).get("content", "")


def build_eval_prompt(d, rel_path, c_win, f_win, b_win, context_text, mask_box):
    """Build the eval prompt with training's build_prompt(), so eval matches the training format.

    Conditioning fields are computed as windowing.py does: SAUCE group/year
    from the piece, technique metrics over the whole window before masking.
    """
    sauce_group = d["sauce_group"].item().decode("utf-8", "replace") if d["sauce_group"].size else ""
    sauce_date = d["sauce_date"].item().decode("utf-8", "replace") if d["sauce_date"].size else ""
    year = sauce_date[:4] if len(sauce_date) >= 4 and sauce_date[:4].isdigit() else rel_path.split("/")[0]
    half_pct, shade_pct = w.window_technique_metrics(c_win, f_win, b_win)
    bucket = w.shade_bucket(half_pct, shade_pct)
    row = {
        "sauce_group": sauce_group, "sauce_year": year,
        "half_block_pct": half_pct, "shade_pct": shade_pct, "shade_bucket": bucket,
        "mask_box": list(mask_box), "context": context_text,
    }
    return ptd.build_prompt(row)


def make_eval_prompt(context_text, mask_h, mask_w):
    """Deprecated. Old prose prompt that doesn't match the training format. Use build_eval_prompt()."""
    return (
        "Below is a window of ANSI/textmode art, run-length encoded. "
        "Each line is 'r{row} col,FB:glyphs col,FB:glyphs ...' where F "
        "is the foreground color (hex 0-f) and B is the background "
        "color (hex 0-f), and 'glyphs' are the literal characters at "
        "that run. Background cells (space, color 07 or omitted) are "
        "not shown.\n\n"
        f"A rectangular region marked [MASK w={mask_w}] spanning "
        f"{mask_h} rows has been removed. Reconstruct ONLY that "
        f"region, consistent with the surrounding art.\n\n"
        f"{context_text}\n\n"
        f"Reply with ONLY the reconstructed region as {mask_h} lines "
        f"in the same 'r00 col,FB:glyphs ...' format, using ROW/COLUMN "
        f"indices LOCAL to the masked region (r00 = the region's first "
        f"row, column 0 = the region's first column). No explanation."
    )


def render_grid_to_png(chars, fg, bg, out_path):
    """Render a cell grid to PNG via harness.render_ans_to_png_b64. Returns True on success.

    Model output can crash PIL, so any exception returns False instead of
    killing the batch.
    """
    try:
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
        tmp = out_path.with_suffix(".ans")
        tmp.write_bytes(text.encode("utf-8"))
        b64, note = harness.render_ans_to_png_b64(str(tmp))
        if b64:
            out_path.write_bytes(base64.b64decode(b64))
        return b64 is not None
    except Exception:
        return False


def copy_detection_score(model_chars, model_fg, model_bg,
                          full_chars, full_fg, full_bg, top, left, mask_h, mask_w):
    """Measure how much the fill copies its neighbouring context rows/columns.

    Returns (exact_match_frac, cell_overlap_frac):
      exact_match_frac: share of the fill's edge rows/columns (up to 4) that
                        exactly duplicate the adjacent context row/column.
      cell_overlap_frac: mean share of matching cells per edge; catches
                         partial copies.
    A cell matches only if char, fg and bg all match.
    """
    h, wd = full_chars.shape

    def _row_pair(r):
        return full_chars[r, left:left + mask_w], full_fg[r, left:left + mask_w], full_bg[r, left:left + mask_w]

    def _col_pair(c):
        return full_chars[top:top + mask_h, c], full_fg[top:top + mask_h, c], full_bg[top:top + mask_h, c]

    def _cell_overlap(a, b):
        ac, af, ab = a
        bc, bf, bb = b
        match = (ac == bc) & (af == bf) & (ab == bb)
        return float(np.mean(match))

    def _exact(a, b):
        return bool(np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2]))

    checks = []
    if top > 0:
        checks.append((_row_pair(top - 1), (model_chars[0], model_fg[0], model_bg[0])))
    if top + mask_h < h:
        checks.append((_row_pair(top + mask_h), (model_chars[-1], model_fg[-1], model_bg[-1])))
    if left > 0:
        checks.append((_col_pair(left - 1), (model_chars[:, 0], model_fg[:, 0], model_bg[:, 0])))
    if left + mask_w < wd:
        checks.append((_col_pair(left + mask_w), (model_chars[:, -1], model_fg[:, -1], model_bg[:, -1])))

    if not checks:
        return 0.0, 0.0

    exact_matches = sum(1 for neighbor, edge in checks if _exact(neighbor, edge))
    overlaps = [_cell_overlap(neighbor, edge) for neighbor, edge in checks]
    return exact_matches / len(checks), float(np.mean(overlaps))


def opus_pairwise_eval(model_png, truth_png):
    """Blind pairwise judgment of the model fill vs ground truth, randomized A/B."""
    import random
    from PIL import Image, ImageDraw, ImageFont

    model_img = Image.open(model_png).convert("RGB")
    truth_img = Image.open(truth_png).convert("RGB")
    model_is_a = random.random() < 0.5
    img_a = model_img if model_is_a else truth_img
    img_b = truth_img if model_is_a else model_img

    label_h = 24
    gap = 4
    hh = max(img_a.height, img_b.height) + label_h
    ww = img_a.width + gap + img_b.width
    canvas = Image.new("RGB", (ww, hh), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(harness._FONT_PATH, 16)
    except Exception:
        font = ImageFont.load_default()
    draw.text((4, 2), "A", font=font, fill=(255, 255, 0))
    draw.text((img_a.width + gap + 4, 2), "B", font=font, fill=(0, 255, 255))
    canvas.paste(img_a, (0, label_h))
    canvas.paste(img_b, (img_a.width + gap, label_h))

    tmpdir = tempfile.mkdtemp(prefix="fim_eval_")
    try:
        cmp_path = Path(tmpdir) / "compare.png"
        canvas.save(cmp_path)
        prompt = (
            "Read compare.png. It shows two small ANSI-art fragments "
            "side by side, A and B, that were each used to fill in a "
            "masked rectangle inside a larger piece. You have no other "
            "context. Which one looks like more plausible, coherent "
            "ANSI/textmode art -- consistent shading, sensible "
            "continuation of a form -- versus looking broken, random, "
            "or nonsensical?\n\n"
            "Answer in this exact format:\n"
            "WINNER: A or WINNER: B or WINNER: TIE\n"
            "REASON: <1-2 sentences>"
        )
        result = harness._run_claude_p(
            ["claude", "-p", prompt, "--model", harness.OPUS_MODEL,
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir,
        )
        if result is None:
            return {"status": "error", "message": "claude -p timed out after retry (120s x2)"}
        if result.returncode != 0:
            return {"status": "error", "message": f"claude CLI exit {result.returncode}"}
        data = json.loads(result.stdout)
        reasoning = data.get("result", "")
        winner = None
        for line in reasoning.splitlines():
            if line.strip().upper().startswith("WINNER:"):
                v = line.split(":", 1)[1].strip().upper()
                winner = "A" if v.startswith("A") else ("B" if v.startswith("B") else "TIE")
                break
        if winner is None:
            return {"status": "error", "message": "no parseable WINNER line"}
        if winner == "TIE":
            result_label = "tie"
        else:
            model_won = (winner == "A") == model_is_a
            result_label = "model" if model_won else "ground_truth"
        return {"status": "ok", "winner": result_label, "reasoning": reasoning}
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="qwen3.8:27b-mlx",
                     help="Ollama model to eval as the fill-in model (no 8B model is currently pulled locally -- pass one once available)")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--holdout-split", default=str(CORPUS_DIR / "holdout_split.json"))
    ap.add_argument("--out", default=str(CORPUS_DIR / "eval_results.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-opus", action="store_true", help="skip the pairwise Opus check (mechanical metrics only)")
    args = ap.parse_args()

    print("Round-trip self-test (encoder -> decoder on synthetic data)...")
    ok = _round_trip_self_test()
    print(f"  {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("ABORTING: round-trip self-test failed, scores would be meaningless.", file=sys.stderr)
        sys.exit(1)

    import random
    rng = random.Random(args.seed)

    split = json.loads(Path(args.holdout_split).read_text())
    holdout_paths = split["holdout_paths"]
    parsed_dir = Path(args.parsed_dir)

    candidates = rng.sample(holdout_paths, min(len(holdout_paths), args.n * 3))

    results = []
    n_done = 0
    tmpdir = Path(tempfile.mkdtemp(prefix="eval_render_"))
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
        row0 = rng.randint(0, chars_full.shape[0] - w.WINDOW_ROWS)
        col0 = rng.randint(0, chars_full.shape[1] - w.WINDOW_COLS)
        c_win = chars_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        f_win = fg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]
        b_win = bg_full[row0:row0 + w.WINDOW_ROWS, col0:col0 + w.WINDOW_COLS]

        context_text, target_text, mask_box = w.make_fitm_example(
            c_win, f_win, b_win, rng, fixed_mask_size=(8, 14)
        )
        top, left, mask_h, mask_w = mask_box

        prompt = build_eval_prompt(d, rel, c_win, f_win, b_win, context_text, mask_box)
        try:
            raw_reply = call_ollama_fill(args.model, prompt)
        except Exception as e:
            results.append({"path": rel, "error": f"ollama call failed: {e}"})
            continue

        model_chars, model_fg, model_bg = decode_window_text(raw_reply, mask_h, mask_w)
        truth_chars = c_win[top:top + mask_h, left:left + mask_w]
        truth_fg = f_win[top:top + mask_h, left:left + mask_w]
        truth_bg = b_win[top:top + mask_h, left:left + mask_w]

        model_half, model_shade = w.window_technique_metrics(model_chars, model_fg, model_bg)
        truth_half, truth_shade = w.window_technique_metrics(truth_chars, truth_fg, truth_bg)

        copy_exact, copy_overlap = copy_detection_score(
            model_chars, model_fg, model_bg, c_win, f_win, b_win, top, left, mask_h, mask_w
        )
        # Same check on the ground truth. Repeating textures copy
        # legitimately, so this is the baseline.
        truth_copy_exact, truth_copy_overlap = copy_detection_score(
            truth_chars, truth_fg, truth_bg, c_win, f_win, b_win, top, left, mask_h, mask_w
        )

        entry = {
            "path": rel, "row0": row0, "col0": col0, "mask_box": list(mask_box),
            "model_half_block_pct": model_half, "model_shade_pct": model_shade,
            "truth_half_block_pct": truth_half, "truth_shade_pct": truth_shade,
            "model_copy_exact_frac": copy_exact, "model_copy_overlap_frac": copy_overlap,
            "truth_copy_exact_frac": truth_copy_exact, "truth_copy_overlap_frac": truth_copy_overlap,
        }

        if not args.no_opus:
            model_png = tmpdir / f"model_{n_done}.png"
            truth_png = tmpdir / f"truth_{n_done}.png"
            ok_m = render_grid_to_png(model_chars, model_fg, model_bg, model_png)
            ok_t = render_grid_to_png(truth_chars, truth_fg, truth_bg, truth_png)
            if ok_m and ok_t:
                pw = opus_pairwise_eval(model_png, truth_png)
                entry["pairwise"] = pw
            else:
                entry["pairwise"] = {"status": "error", "message": "render failed"}

        results.append(entry)
        n_done += 1
        print(f"  [{n_done}/{args.n}] {rel}: model half={model_half:.1f} shade={model_shade:.1f} "
              f"| truth half={truth_half:.1f} shade={truth_shade:.1f} "
              f"| copy(exact/overlap)={copy_exact:.2f}/{copy_overlap:.2f}"
              + (f" | pairwise={entry.get('pairwise', {}).get('winner', 'n/a')}" if not args.no_opus else ""))

    Path(args.out).write_text(json.dumps(results, indent=2))

    valid = [r for r in results if "error" not in r]
    print(f"\n{len(valid)}/{len(results)} evals completed without error.")
    if valid:
        import statistics
        print(f"Model half_block_pct: mean={statistics.mean(r['model_half_block_pct'] for r in valid):.1f}")
        print(f"Truth half_block_pct: mean={statistics.mean(r['truth_half_block_pct'] for r in valid):.1f}")
        print(f"Model shade_pct:      mean={statistics.mean(r['model_shade_pct'] for r in valid):.1f}")
        print(f"Truth shade_pct:      mean={statistics.mean(r['truth_shade_pct'] for r in valid):.1f}")
        print(f"Model copy-exact frac:   mean={statistics.mean(r['model_copy_exact_frac'] for r in valid):.3f}")
        print(f"Truth copy-exact frac:   mean={statistics.mean(r['truth_copy_exact_frac'] for r in valid):.3f} "
              f"(baseline -- real repeating texture also 'copies' by this metric)")
        print(f"Model copy-overlap frac: mean={statistics.mean(r['model_copy_overlap_frac'] for r in valid):.3f}")
        print(f"Truth copy-overlap frac: mean={statistics.mean(r['truth_copy_overlap_frac'] for r in valid):.3f}")
        if not args.no_opus:
            pairwise_results = [r["pairwise"]["winner"] for r in valid if r.get("pairwise", {}).get("status") == "ok"]
            wins = pairwise_results.count("model")
            losses = pairwise_results.count("ground_truth")
            ties = pairwise_results.count("tie")
            print(f"Pairwise vs ground truth: model won {wins}, lost {losses}, tied {ties} (of {len(pairwise_results)})")
    print(f"\nFull results: {args.out}")


if __name__ == "__main__":
    main()
