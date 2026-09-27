#!/usr/bin/env python3
"""Retrieve cell-grid patches from the corpus. No training required.

Two layers:
  1. find_patches_by_technique(...): SQL over corpus/patch_index.db
     (built by patch_index.py). No model call.
  2. find_patches(description): the local Ollama model turns free text
     into technique filters and a title keyword, then calls layer 1.

Each hit carries chars/fg/bg arrays sliced from the parent .npz, plus
RLE text and a patch_id.

Usage as a library:
    from corpus.find_patches import find_patches, find_patches_by_technique
    hits = find_patches_by_technique(half_block_min=40, shade_min=10, n=5)
    hits = find_patches("dense half-block dithered gradient", n=5)
    # each hit: {"parent_path", "row_offset", "col_offset", "window_rows",
    #            "window_cols", "half_block_pct", "shade_pct", "chars",
    #            "fg", "bg", "rle_text", "sauce_title", "sauce_author"}

CLI:
    python3 corpus/find_patches.py --half-block-min 40 --shade-min 10 --n 5
    python3 corpus/find_patches.py --describe "dense half-block dithered sky" --n 5
"""
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent
DB_PATH = CORPUS_DIR / "patch_index.db"
PARSED_DIR = CORPUS_DIR / "parsed"
OLLAMA_MODEL = "qwen3.8:27b-mlx"


def make_patch_id(parent_path, row_offset, col_offset, window_rows, window_cols):
    """Encode a patch's location as an opaque id.

    Self-contained, so it survives restarts with no cache. canvas_stamp uses
    it to place the exact cells a hit returned.
    """
    payload = json.dumps([parent_path, int(row_offset), int(col_offset),
                           int(window_rows), int(window_cols)])
    import base64
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_patch_id(patch_id):
    import base64
    try:
        padded = patch_id + "=" * (-len(patch_id) % 4)
        payload = base64.urlsafe_b64decode(padded.encode()).decode()
        parent_path, row_offset, col_offset, window_rows, window_cols = json.loads(payload)
        return parent_path, row_offset, col_offset, window_rows, window_cols
    except Exception as e:
        raise ValueError(f"invalid patch_id {patch_id!r}: {e}")


def _load_patch_grids(parent_path, row_offset, col_offset, window_rows, window_cols):
    """Slice (chars, fg, bg) for one window from its parent .npz.

    Returns None if the file is missing or the window no longer fits
    (stale index after a re-parse).
    """
    npz_path = PARSED_DIR / parent_path
    if not npz_path.exists():
        return None
    d = np.load(npz_path)
    chars, fg, bg = d["chars"], d["fg"], d["bg"]
    r0, c0 = row_offset, col_offset
    r1, c1 = r0 + window_rows, c0 + window_cols
    if r1 > chars.shape[0] or c1 > chars.shape[1]:
        return None
    return chars[r0:r1, c0:c1], fg[r0:r1, c0:c1], bg[r0:r1, c0:c1]


def _rle_text(chars, fg, bg):
    import windowing as w
    return w.encode_window(chars, fg, bg)


def find_patches_by_technique(
    half_block_min=None, half_block_max=None,
    shade_min=None, shade_max=None,
    shade_bucket=None, title_like=None, author_like=None,
    sauce_group=None, sauce_year=None,
    n=5, db_path=None, seed=None,
):
    """Query patches by technique metrics. No model call.

    Every filter is optional. title_like/author_like are case-insensitive
    substring matches against parent_meta; wildcards are added here.
    """
    db_path = Path(db_path) if db_path else DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(
            f"{db_path} not found -- run corpus/patch_index.py "
            "(and corpus/patch_meta.py for title/author search) first"
        )
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    where = []
    params = []
    joins = ""
    if half_block_min is not None:
        where.append("p.half_block_pct >= ?"); params.append(half_block_min)
    if half_block_max is not None:
        where.append("p.half_block_pct <= ?"); params.append(half_block_max)
    if shade_min is not None:
        where.append("p.shade_pct >= ?"); params.append(shade_min)
    if shade_max is not None:
        where.append("p.shade_pct <= ?"); params.append(shade_max)
    if shade_bucket is not None:
        where.append("p.shade_bucket = ?"); params.append(shade_bucket)
    if sauce_group is not None:
        where.append("p.sauce_group = ?"); params.append(sauce_group)
    if sauce_year is not None:
        where.append("p.sauce_year = ?"); params.append(sauce_year)
    if title_like is not None or author_like is not None:
        has_meta = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parent_meta'"
        ).fetchone()
        if not has_meta:
            raise RuntimeError(
                "title_like/author_like requires parent_meta -- run corpus/patch_meta.py first"
            )
        joins = " JOIN parent_meta m ON m.parent_path = p.parent_path"
        if title_like is not None:
            where.append("m.sauce_title LIKE ? COLLATE NOCASE"); params.append(f"%{title_like}%")
        if author_like is not None:
            where.append("m.sauce_author LIKE ? COLLATE NOCASE"); params.append(f"%{author_like}%")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    order_sql = "ORDER BY RANDOM()" if seed is None else "ORDER BY RANDOM()"
    # Pull 4n random candidates; some may fail to load.
    sql = f"SELECT p.* FROM patches p{joins}{where_sql} {order_sql} LIMIT ?"
    if seed is not None:
        conn.execute("SELECT 1")  # no-op: sqlite's RANDOM() can't be seeded
    rows = conn.execute(sql, params + [max(n * 4, n)]).fetchall()
    conn.close()

    hits = []
    for row in rows:
        if len(hits) >= n:
            break
        grids = _load_patch_grids(
            row["parent_path"], row["row_offset"], row["col_offset"],
            row["window_rows"], row["window_cols"],
        )
        if grids is None:
            continue
        chars, fg, bg = grids
        hit = dict(row)
        hit["chars"], hit["fg"], hit["bg"] = chars, fg, bg
        hit["patch_id"] = make_patch_id(row["parent_path"], row["row_offset"],
                                         row["col_offset"], row["window_rows"], row["window_cols"])
        try:
            hit["rle_text"] = _rle_text(chars, fg, bg)
        except Exception:
            hit["rle_text"] = None
        hits.append(hit)
    return hits


_TRANSLATE_PROMPT = """You are translating a free-text description of \
ANSI/textmode art technique into a JSON query for a database of real \
40x16-cell patches. The database has these numeric fields per patch:

  half_block_pct  -- % of cells using half-block glyphs (\u2580 upper, \u2584 lower):
                      the "pixel" subpixel-shading technique
  shade_pct       -- % of cells using ramp/dither glyphs (\u2591 \u2592 \u2593)

Respond with ONLY a JSON object, no other text, with these keys (all \
optional, omit ones the description doesn't imply):
  "half_block_min": number 0-100 or null
  "shade_min": number 0-100 or null
  "keyword": a short single word/phrase from the description worth \
matching against piece titles (e.g. "sky", "dragon", "logo"), or null

Description: {description}

JSON:"""


def _translate_description(description, timeout=60):
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": _TRANSLATE_PROMPT.format(description=description)}],
        "stream": False,
    }).encode()
    import urllib.request
    req = urllib.request.Request(
        "http://localhost:11434/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        r = json.loads(resp.read())
    text = r.get("message", {}).get("content", "").strip()
    # Tolerate JSON wrapped in a code fence or prose.
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {}


def find_patches(description, n=5, db_path=None):
    """Free-text retrieval via the local model, then find_patches_by_technique.

    Falls back to an unfiltered sample if translation fails, and drops the
    keyword if it matches nothing. Does not raise on model errors.
    """
    query = {}
    try:
        query = _translate_description(description)
    except Exception as e:
        print(f"find_patches: description translation failed ({e}), falling back to unfiltered sample", file=sys.stderr)

    kwargs = dict(n=n, db_path=db_path)
    if query.get("half_block_min") is not None:
        kwargs["half_block_min"] = query["half_block_min"]
    if query.get("shade_min") is not None:
        kwargs["shade_min"] = query["shade_min"]
    keyword = query.get("keyword")
    if keyword:
        kwargs["title_like"] = keyword

    hits = find_patches_by_technique(**kwargs)
    if not hits and keyword:
        # Keyword matched nothing; retry without it.
        kwargs.pop("title_like", None)
        hits = find_patches_by_technique(**kwargs)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--describe", default=None, help="free-text description (uses the VLM translation path)")
    ap.add_argument("--half-block-min", type=float, default=None)
    ap.add_argument("--shade-min", type=float, default=None)
    ap.add_argument("--title-like", default=None)
    ap.add_argument("--author-like", default=None)
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    if args.describe:
        hits = find_patches(args.describe, n=args.n)
    else:
        hits = find_patches_by_technique(
            half_block_min=args.half_block_min, shade_min=args.shade_min,
            title_like=args.title_like, author_like=args.author_like, n=args.n,
        )

    print(f"{len(hits)} hits:")
    for h in hits:
        print(f"  {h['parent_path']} @ ({h['row_offset']},{h['col_offset']}) "
              f"half_block={h['half_block_pct']:.1f} shade={h['shade_pct']:.1f}")


if __name__ == "__main__":
    main()
