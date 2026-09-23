#!/usr/bin/env python3
"""Build a high-craft-filtered CLIP index from the full one.

The full index covers all 37 years of 16colo.rs, so find_patches
returns early-90s BBS ads and NFO headers as readily as illustration
work -- 30.9% of the 850k patches are 1990-1995 (measured
2026-09-23), and raze studies whatever comes back during live shifts.

Selection (union, not intersection -- any one qualifies):
  * technique tier: shade or half_block at/above the index p90
  * year >= 2005 (the modern illustration era)
  * known illustration groups: Blocktronics, ACiD, iCE, Fuel,
    Mistigris, Impure, ansi_love

Writes a sibling index that find_patches_clip can load by path. Shares
the parent index's embeddings by row index -- no re-embedding, which
is what makes this cheap (the original pass was 4 GPU-hours).
"""
import sqlite3
import sys
from pathlib import Path

import numpy as np

SRC = Path("corpus/clip_index")
DST = Path("corpus/clip_index_highcraft")
HIGH_CRAFT = ("blocktronics", "mistigris", "mist", "fuel", "acid", "ice",
              "ansi_love", "impure")


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
    dst_path.unlink(missing_ok=True)  # unlink-first, or CREATE TABLE throws
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
