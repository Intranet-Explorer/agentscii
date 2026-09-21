#!/usr/bin/env python3
"""corpus/find_patches_clip.py -- CLIP-embedding retrieval over
corpus/clip_index/ (built by build_clip_index.py), replacing
find_patches()'s title-keyword matching as the PRIMARY match (user
direction, 2026-09-20: "Replace title matching with visual embeddings.
... Query = CLIP text embedding -> nearest patches. Title keywords
become an optional filter, not the primary match.").

find_patches.py's keyword-matching path only works when a real
content-bearing SAUCE title happens to exist for a piece, which is
true for a small minority of the corpus. This module embeds the QUERY
TEXT with the same CLIP text tower used nowhere else in this pipeline
(open_clip ViT-B-32, openai weights -- matching build_clip_index.py's
image tower exactly, since CLIP's image/text embeddings are only
comparable when both come from the same trained pair) and does a
cosine-similarity nearest-neighbor search over the embedding matrix --
this works for ANY query, not just ones that happen to match a title
substring.

Usage as a library:
    from corpus.find_patches_clip import find_patches_clip
    hits = find_patches_clip("dense half-block dithered gradient", n=5)
    # each hit: {"parent_path", "row_offset", "col_offset", "window_rows",
    #            "window_cols", "half_block_pct", "shade_pct", "score",
    #            "chars", "fg", "bg"}

CLI:
    python3 corpus/find_patches_clip.py "dense half-block dithered sky" --n 5
"""
import argparse
import sqlite3
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np

from find_patches import _load_patch_grids, _rle_text

CLIP_INDEX_DIR = CORPUS_DIR / "clip_index"

_model = None
_tokenizer = None
_device = None


def _load_clip():
    global _model, _tokenizer, _device
    if _model is not None:
        return
    import torch
    import open_clip
    _device = "mps" if torch.backends.mps.is_available() else "cpu"
    _model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    _model = _model.to(_device).eval()
    _tokenizer = open_clip.get_tokenizer("ViT-B-32")


def embed_text(query):
    import torch
    _load_clip()
    with torch.no_grad():
        tokens = _tokenizer([query]).to(_device)
        feat = _model.encode_text(tokens)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.cpu().numpy().astype(np.float32)[0]


def find_patches_clip(query, n=5, index_dir=None, half_block_min=None, shade_min=None):
    """CLIP nearest-neighbor retrieval. Loads the full embedding matrix
    into memory each call (a few hundred MB for ~800K x 512 float32 --
    acceptable for an interactive/tool-call use pattern, not a hot
    loop) -- optional half_block_min/shade_min filter the candidate
    pool by technique metric BEFORE ranking by similarity, for a
    "shaded AND about X" combined query."""
    index_dir = Path(index_dir) if index_dir else CLIP_INDEX_DIR
    emb_path = index_dir / "embeddings.npy"
    meta_path = index_dir / "meta.db"
    if not emb_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"{index_dir} missing embeddings.npy/meta.db -- run corpus/build_clip_index.py first")

    embeddings = np.load(emb_path)  # (N, 512), already L2-normalized by build_clip_index.py
    q = embed_text(query)  # (512,), already L2-normalized

    scores = embeddings @ q  # cosine similarity since both sides are unit-norm

    conn = sqlite3.connect(str(meta_path))
    conn.row_factory = sqlite3.Row

    if half_block_min is not None or shade_min is not None:
        where = []
        params = []
        if half_block_min is not None:
            where.append("half_block_pct >= ?"); params.append(half_block_min)
        if shade_min is not None:
            where.append("shade_pct >= ?"); params.append(shade_min)
        allowed_rows = {r["row_idx"] for r in conn.execute(
            f"SELECT row_idx FROM meta WHERE {' AND '.join(where)}", params
        ).fetchall()}
        order = np.argsort(-scores)
        order = [i for i in order if i in allowed_rows]
    else:
        order = np.argsort(-scores)

    hits = []
    for idx in order:
        if len(hits) >= n:
            break
        row = conn.execute("SELECT * FROM meta WHERE row_idx = ?", (int(idx),)).fetchone()
        if row is None:
            continue
        grids = _load_patch_grids(row["parent_path"], row["row_offset"], row["col_offset"], row["window_rows"], row["window_cols"])
        if grids is None:
            continue
        chars, fg, bg = grids
        hit = dict(row)
        hit["score"] = float(scores[idx])
        hit["chars"], hit["fg"], hit["bg"] = chars, fg, bg
        try:
            hit["rle_text"] = _rle_text(chars, fg, bg)
        except Exception:
            hit["rle_text"] = None
        hits.append(hit)
    conn.close()
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--half-block-min", type=float, default=None)
    ap.add_argument("--shade-min", type=float, default=None)
    ap.add_argument("--index-dir", default=None)
    args = ap.parse_args()

    hits = find_patches_clip(args.query, n=args.n, index_dir=args.index_dir,
                              half_block_min=args.half_block_min, shade_min=args.shade_min)
    print(f"{len(hits)} hits for {args.query!r}:")
    for h in hits:
        print(f"  score={h['score']:.3f} {h['parent_path']} @ ({h['row_offset']},{h['col_offset']}) "
              f"half_block={h['half_block_pct']:.1f} shade={h['shade_pct']:.1f}")


if __name__ == "__main__":
    main()
