#!/usr/bin/env python3
"""Build a high-craft subset of the CLIP index.

The full index is dominated by early-90s BBS ads and NFO headers. A patch
is kept if any one of these holds:
  * shade or half_block at or above the index p90
  * year >= 2005
  * group matches HIGH_CRAFT

Writes a sibling index find_patches_clip can load by path. Embeddings are
copied by row index, not recomputed.
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np

SRC = Path("corpus/clip_index")
DST = Path("corpus/clip_index_highcraft")
HIGH_CRAFT = ("mistigris", "mist", "fuel", "ice", "ansi_love", "impure")


def _year(p):
    try:
        return int(p.split("/")[0])
    except (ValueError, IndexError):
        return 0


def _group(p):
    parts = p.split("/")
    g = parts[1].lower() if len(parts) > 1 else ""
    return any(k in g for k in HIGH_CRAFT)


def main():
    src_db = sqlite3.connect(SRC / "meta.db")
    rows = src_db.execute(
        "SELECT row_idx, parent_path, row_offset, col_offset, window_rows, "
        "window_cols, half_block_pct, shade_pct FROM meta"
    ).fetchall()
    shades = sorted(r[7] for r in rows)
    hbs = sorted(r[6] for r in rows)
    p90_sh = shades[int(len(shades) * 0.90)]
    p90_hb = hbs[int(len(hbs) * 0.90)]

    keep = [r for r in rows
            if r[7] >= p90_sh or r[6] >= p90_hb
            or _year(r[1]) >= 2005 or _group(r[1])]
    print(f"kept {len(keep)} of {len(rows)} "
          f"({100*len(keep)/len(rows):.1f}%), p90 shade={p90_sh:.1f} "
          f"half_block={p90_hb:.1f}")

    emb = np.load(SRC / "embeddings.npy", mmap_mode="r")
    idx = np.array([r[0] for r in keep], dtype=np.int64)
    DST.mkdir(parents=True, exist_ok=True)
    np.save(DST / "embeddings.npy", np.ascontiguousarray(emb[idx]))

    dst_path = DST / "meta.db"
    dst_path.unlink(missing_ok=True)  # or CREATE TABLE fails on rerun
    dst_db = sqlite3.connect(dst_path)
    dst_db.execute("""CREATE TABLE meta (
        row_idx INTEGER PRIMARY KEY,
        parent_path TEXT, row_offset INTEGER, col_offset INTEGER,
        window_rows INTEGER, window_cols INTEGER,
        half_block_pct REAL, shade_pct REAL)""")
    dst_db.executemany(
        "INSERT INTO meta VALUES (?,?,?,?,?,?,?,?)",
        [(i,) + tuple(r[1:]) for i, r in enumerate(keep)])
    dst_db.commit()
    dst_db.close()
    print(f"wrote {dst_path} and {DST/'embeddings.npy'}")


if __name__ == "__main__":
    sys.exit(main())
