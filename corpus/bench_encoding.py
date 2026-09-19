#!/usr/bin/env python3
"""corpus/bench_encoding.py -- benchmark 3 candidate cell encodings on
the ACTUAL tokenizer, tokens-per-cell, to pick the cheapest before
committing (user direction, 2026-09-19: "RLE at 0.89 chars/token
suggests it's the wrong choice").

Encodings compared, all on the SAME real sample of windows:

  (a) CURRENT RLE -- run-length merged runs, 2-hex color code,
      literal glyph repetition, blank-background runs omitted
      (corpus/windowing.py's rle_encode_row).

  (b) PLAIN PER-CELL, single-char color code -- one token per cell,
      "{col}{glyph}{colorchar}" with color packed into ONE character
      (not 2 hex digits) by mapping the 256 possible (fg,bg) pairs to
      a single printable ASCII-adjacent codepoint range. No run-length
      compression at all -- the literal "raw per-cell dump" baseline
      the user asked to measure against.

  (c) PACKED SINGLE-CODEPOINT -- each (char, fg, bg) triple mapped to
      ONE Unicode Private-Use-Area codepoint. 252 distinct glyphs (the
      corpus's real full vocabulary, confirmed by direct enumeration)
      x 16 fg x 16 bg = 64,512 possible combinations, comfortably
      inside the ~131,068 Supplementary PUA-A+B codepoint space. One
      codepoint per cell, background cells included (no RLE, no run
      structure) -- the theoretical floor on cell-count-to-symbol
      ratio, IF the tokenizer treats each codepoint as ~1 token (it
      often doesn't for rare/unassigned codepoints -- this is exactly
      what's being measured, not assumed).

Usage:
    python3 corpus/bench_encoding.py [--windows corpus/windows.jsonl] [--sample N]
"""
import argparse
import json
import statistics
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent

import sys
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))
import numpy as np
import windowing as w


# --- encoding (b): plain per-cell, single-char color code -----------------
# 256 possible (fg,bg) pairs (16x16) -> one printable codepoint each,
# starting just above ASCII printable range to stay out of the way of
# real glyph characters.
_COLOR_CHAR_BASE = 0x2100  # arbitrary distinct block, not used by real CP437 art
def _color_char(fg, bg):
    return chr(_COLOR_CHAR_BASE + fg * 16 + bg)


def encode_plain_percell(chars, fg, bg):
    """One line per row: every cell as glyph+colorchar, no RLE, no
    omission of background cells -- the literal raw dump baseline."""
    lines = []
    h, wd = chars.shape
    for r in range(h):
        row_tokens = []
        for c in range(wd):
            ch = chr(int(chars[r, c]))
            row_tokens.append(ch + _color_char(int(fg[r, c]), int(bg[r, c])))
        lines.append(f"r{r:02d} " + "".join(row_tokens))
    return "\n".join(lines)


# --- encoding (c): packed single-codepoint ---------------------------------
# Build the real glyph vocabulary -> index map from the corpus's
# actual distinct glyphs (252, confirmed by direct enumeration -- see
# module docstring), not assumed/guessed.
def build_glyph_vocab():
    manifest_glyphs = set()
    # Reuse technique_manifest.jsonl's existing pass over the corpus
    # would need re-parsing chars; instead do a real, direct pass over
    # a sample of parsed files (matches the 252-glyph count already
    # confirmed via a full-corpus enumeration this session).
    import glob
    files = glob.glob(str(CORPUS_DIR / "parsed" / "**" / "*.npz"), recursive=True)
    import random
    rng = random.Random(0)
    sample = rng.sample(files, min(2000, len(files)))
    for f in sample:
        try:
            d = np.load(f)
        except Exception:
            continue
        manifest_glyphs.update(np.unique(d["chars"]).tolist())
    return sorted(manifest_glyphs)


_PUA_BASE = 0xF0000  # Supplementary Private Use Area-A start


def encode_packed(chars, fg, bg, glyph_to_idx):
    """One PUA codepoint per cell: index = glyph_idx*256 + fg*16 + bg.
    No RLE, no background omission -- background cells get a real
    distinct codepoint too (glyph_idx for space), since the whole
    point of this scheme is "one symbol per cell," not a hybrid."""
    h, wd = chars.shape
    lines = []
    for r in range(h):
        row_chars = []
        for c in range(wd):
            g_idx = glyph_to_idx.get(int(chars[r, c]), 0)
            packed = g_idx * 256 + int(fg[r, c]) * 16 + int(bg[r, c])
            row_chars.append(chr(_PUA_BASE + packed))
        lines.append(f"r{r:02d} " + "".join(row_chars))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--sample", type=int, default=500)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    args = ap.parse_args()

    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")

    print("Building real glyph vocabulary from a 2000-file sample...")
    glyph_list = build_glyph_vocab()
    glyph_to_idx = {cp: i for i, cp in enumerate(glyph_list)}
    print(f"Real glyph vocabulary size: {len(glyph_list)}\n")

    # Sample real windows from windows.jsonl, but re-derive the RAW
    # (chars,fg,bg) grid for each by re-slicing the parent piece at the
    # stored (row_offset, col_offset) -- windows.jsonl only stores the
    # already-RLE-encoded text, not the raw arrays, so encodings (b)
    # and (c) need the real grid, not a re-decode of (a)'s text.
    parsed_dir = Path(args.parsed_dir)
    rows_meta = []
    with open(args.windows) as f:
        for i, line in enumerate(f):
            if i >= args.sample:
                break
            rows_meta.append(json.loads(line))
    print(f"Benchmarking on {len(rows_meta)} real windows\n")

    results = {"rle": [], "plain": [], "packed": []}
    cells_per_window = w.WINDOW_ROWS * w.WINDOW_COLS
    n_ok = 0
    for meta in rows_meta:
        npz_path = parsed_dir / meta["parent_path"]
        try:
            d = np.load(npz_path)
        except Exception:
            continue
        chars_full, fg_full, bg_full = d["chars"], d["fg"], d["bg"]
        r0, c0 = meta["row_offset"], meta["col_offset"]
        r1 = min(r0 + w.WINDOW_ROWS, chars_full.shape[0])
        c1 = min(c0 + w.WINDOW_COLS, chars_full.shape[1])
        c_win = chars_full[r0:r1, c0:c1]
        f_win = fg_full[r0:r1, c0:c1]
        b_win = bg_full[r0:r1, c0:c1]
        pad_h = w.WINDOW_ROWS - c_win.shape[0]
        pad_w = w.WINDOW_COLS - c_win.shape[1]
        if pad_h > 0 or pad_w > 0:
            c_win = np.pad(c_win, ((0, pad_h), (0, pad_w)), constant_values=0x20)
            f_win = np.pad(f_win, ((0, pad_h), (0, pad_w)), constant_values=7)
            b_win = np.pad(b_win, ((0, pad_h), (0, pad_w)), constant_values=0)

        rle_text = w.encode_window(c_win, f_win, b_win)
        plain_text = encode_plain_percell(c_win, f_win, b_win)
        packed_text = encode_packed(c_win, f_win, b_win, glyph_to_idx)

        for key, text in [("rle", rle_text), ("plain", plain_text), ("packed", packed_text)]:
            n_tok = len(enc.encode(text))
            results[key].append(n_tok / cells_per_window)
        n_ok += 1

    print(f"Windows successfully re-sliced: {n_ok}\n")
    print(f"{'encoding':<10} {'mean tok/cell':>15} {'median tok/cell':>17}")
    for key, label in [("rle", "RLE (a)"), ("plain", "plain per-cell (b)"), ("packed", "packed 1cp (c)")]:
        vals = results[key]
        if not vals:
            continue
        print(f"{label:<20} {statistics.mean(vals):>13.4f} {statistics.median(vals):>17.4f}")

    cheapest = min(results, key=lambda k: statistics.mean(results[k]) if results[k] else float("inf"))
    print(f"\nCheapest by mean tokens/cell: {cheapest}")


if __name__ == "__main__":
    main()
