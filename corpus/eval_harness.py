#!/usr/bin/env python3
"""corpus/eval_harness.py -- FIM eval harness, run BEFORE any training
so "better" has a real baseline (user direction, 2026-09-19): from the
FROZEN HOLDOUT (never seen by windowing.py's selection, never to be
trained on), mask a region, have a model fill it, render, score
half_block_pct/shade_pct on the filled region, plus a blind pairwise
Opus check against the real ground-truth original.

Run against the UNTRAINED base model first to establish what "better"
means before any fine-tuning exists to compare against.

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

OLLAMA_URL = "http://localhost:11434/api/chat"

_RUN_RE = re.compile(r"(\d+),([0-9a-f]{2}):(.*?)(?=\s\d+,[0-9a-f]{2}:|\s\[MASK|$)")


def decode_rle_row(body, width):
    """Reverse of rle_encode_row: 'col,fgbg:glyphs col,fgbg:glyphs...'
    -> a width-length list of (char, fg, bg), true-background elsewhere.
    Real inverse of windowing.py's encoder, built and tested against
    real encoder output (round-tripped) before trusting it on model
    output, which will be noisier/possibly malformed."""
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
    """Reverse of encode_window -- parses 'rNN <body>' lines back into
    (height, width) char/fg/bg arrays. Lines for rows with no content
    are left as true background (never emitted by the encoder, so
    absence is unambiguous)."""
    chars = np.full((height, width), 0x20, dtype=np.uint32)
    fg = np.full((height, width), 7, dtype=np.uint8)
    bg = np.zeros((height, width), dtype=np.uint8)
    for line in text.splitlines():
        # lstrip only -- a plain rstrip()/strip() would silently drop
        # a trailing literal SPACE glyph run (e.g. a colored-space cell
        # at the very end of a row, a real and valid case), found live
        # via the round-trip self-test failing on exactly this case
        # before it was ever trusted on real model output.
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
    """Encode a real random grid, decode it, and confirm an EXACT
    match before trusting either function on model output. This is a
    hard requirement, not a nice-to-have: if the encoder/decoder don't
    round-trip on the encoder's OWN output, no eval score computed
    downstream means anything."""
    rng = np.random.default_rng(0)
    h, wd = w.WINDOW_ROWS, w.WINDOW_COLS
    chars = rng.choice([0x20, 0x2580, 0x2584, 0x2591, ord("X"), ord("#")], size=(h, wd))
    fg = rng.integers(0, 16, size=(h, wd), dtype=np.uint8)
    bg = rng.integers(0, 16, size=(h, wd), dtype=np.uint8)
    # true-background cells must actually be (space, bg=0) for a fair
    # round-trip test, matching the encoder's own omission rule
    is_bg = (chars == 0x20) & (rng.random((h, wd)) < 0.3)
    bg = np.where(is_bg, 0, bg)
    text = w.encode_window(chars, fg, bg)
    d_chars, d_fg, d_bg = decode_window_text(text, h, wd)
    # only compare cells the encoder actually emitted (true-background
    # cells with fg!=7 are lossy by design -- the encoder never records
    # fg for omitted background cells, since it's invisible)
    visible_mask = ~((chars == 0x20) & (bg == 0))
    chars_match = np.array_equal(chars[visible_mask], d_chars[visible_mask])
    fg_match = np.array_equal(fg[visible_mask], d_fg[visible_mask])
    bg_match = np.array_equal(bg[visible_mask], d_bg[visible_mask])
    return chars_match and fg_match and bg_match


def call_ollama_fill(model, prompt, timeout=180, num_predict=800):
    """Real, load-bearing fix found live via two separate bugs, in
    order:
    1. The first version omitted harness.py's own documented SAMPLING
       settings and had no num_predict cap -- a single call ran 10+
       minutes / 7,054 decode iterations (per Ollama's server.log) for
       what should be a short structured answer.
    2. After adding num_predict=800, the reply came back EMPTY with
       done_reason="length" -- inspecting the raw Ollama response
       directly (not just the parsed content field) revealed a
       separate "thinking" field containing a full chain-of-thought
       reasoning trace that consumed the entire num_predict budget
       before the model ever got to write real content. qwen3.8:27b
       is a Qwen3-family reasoning model; harness.py's SAMPLING
       comment calling it "non-thinking mode" describes sampling
       PARAMETERS, not an actual thinking-mode switch -- confirmed via
       a direct curl test that Ollama's chat API has a separate
       top-level "think": false field that actually disables it.
    num_predict=800 is kept as a hard ceiling regardless (roughly 2.5x
    the real p90 target-token count from token_stats.py) so a single
    bad/repetitive generation still can't consume the whole eval run's
    time budget even with thinking correctly disabled."""
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


def make_eval_prompt(context_text, mask_h, mask_w):
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
    """Reuse harness.py's own cell-grid rasterizer by writing a
    synthetic .ans-equivalent SGR stream and calling its renderer --
    avoids reimplementing palette/font logic a third time. Wrapped in
    try/except: model-generated grids are untrusted input and CAN
    trigger a real PIL/rasterizer crash on malformed content (found
    live: 'tile cannot extend outside image', a genuine PIL error on
    some transient bad model output during a real eval run) -- a
    single bad generation must not kill the whole eval batch."""
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
    """User direction, 2026-09-19: 'how often the filled region
    duplicates adjacent rows/columns from context.' A cheap, common
    failure mode for a small/undertrained FIM model is literally
    copying the nearest real row or column outward into the hole
    instead of constructing new content -- this catches that directly,
    rather than only via the (noisier, more expensive) blind pairwise
    Opus judgment.

    Returns two numbers:
    - exact_match_frac: fraction of the mask's edge rows/columns (up
      to 4 checkable: row above, row below, col left, col right) that
      are an EXACT full duplicate of their nearest real neighbor.
    - cell_overlap_frac: a softer, continuous signal -- mean fraction
      of individual cells (char,fg,bg all matching) between each edge
      row/column and its neighbor, averaged over all checkable edges.
      Included because exact-full-row equality is a blunt binary
      signal that a model copying MOST but not all of a row (a
      partial-copy failure mode, still real duplication) would score
      0 on -- cell_overlap_frac catches the partial case exact_match
      misses.

    Cell equality is the full (char, fg, bg) triple -- a row that
    happens to share glyphs but different colors with its neighbor is
    NOT counted as copied, since that's a real (if suspicious)
    coincidence, not literal duplication."""
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
    """Blind pairwise: which region reads better, model's fill or the
    real ground truth -- randomized A/B, no labels beyond A/B."""
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
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-opus-5",
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir, capture_output=True, text=True, timeout=90,
        )
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

        prompt = make_eval_prompt(context_text, mask_h, mask_w)
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
        # same check against the REAL ground-truth fill, as a baseline
        # for how much "duplication" is normal in real art (a genuine
        # repeating pattern -- a brick wall, a fence -- legitimately
        # duplicates its neighbor row/column; copy_detection_score
        # can't distinguish that from a lazy model copy on its own,
        # so the ground-truth rate is the honest reference point for
        # "how much of this is just real repeating texture").
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
