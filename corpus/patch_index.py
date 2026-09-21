#!/usr/bin/env python3
"""corpus/patch_index.py -- build a fast queryable SQLite index over
corpus/windows.jsonl (1.26M windows) for find_patches() retrieval.

windows.jsonl already carries per-window technique metrics computed
during the FIM windowing pass (half_block_pct, shade_pct, shade_bucket)
plus the parent piece's location -- exactly what a technique-based
retrieval query needs. This step strips out the heavy "context"/
"target" text fields (RLE-ish prompt data, not needed for retrieval)
and loads only the compact numeric/metadata columns into SQLite with
indexes on the fields a query filters by, so find_patches() never has
to hold 1.26M dicts in memory or re-parse the full jsonl per call.

Usage:
    python3 corpus/patch_index.py [--windows corpus/windows.jsonl] [--db corpus/patch_index.db]
"""
import argparse
import json
import sqlite3
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS patches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_path TEXT NOT NULL,
    sauce_group TEXT,
    sauce_year TEXT,
    row_offset INTEGER NOT NULL,
    col_offset INTEGER NOT NULL,
    window_rows INTEGER NOT NULL,
    window_cols INTEGER NOT NULL,
    half_block_pct REAL NOT NULL,
    shade_pct REAL NOT NULL,
    shade_bucket TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_half_block ON patches(half_block_pct);
CREATE INDEX IF NOT EXISTS idx_shade ON patches(shade_pct);
CREATE INDEX IF NOT EXISTS idx_bucket ON patches(shade_bucket);
CREATE INDEX IF NOT EXISTS idx_group ON patches(sauce_group);
CREATE INDEX IF NOT EXISTS idx_year ON patches(sauce_year);
"""


def build_index(windows_path, db_path, batch_size=5000):
    windows_path = Path(windows_path)
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)

    rows_buf = []
    n_total = 0
    n_errors = 0

    def flush():
        if rows_buf:
            conn.executemany(
                "INSERT INTO patches (parent_path, sauce_group, sauce_year, "
                "row_offset, col_offset, window_rows, window_cols, "
                "half_block_pct, shade_pct, shade_bucket) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows_buf,
            )
            rows_buf.clear()

    with open(windows_path) as f:
        for line in f:
            n_total += 1
            try:
                d = json.loads(line)
                rows_buf.append((
                    d["parent_path"], d.get("sauce_group") or None,
                    d.get("sauce_year") or None, d["row_offset"], d["col_offset"],
                    d["window_rows"], d["window_cols"], d["half_block_pct"],
                    d["shade_pct"], d["shade_bucket"],
                ))
            except Exception:
                n_errors += 1
                continue
            if len(rows_buf) >= batch_size:
                flush()
            if n_total % 200000 == 0:
                print(f"  ...{n_total} read")
    flush()
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM patches").fetchone()[0]
    conn.close()
    print(f"Indexed {count}/{n_total} windows ({n_errors} parse errors) -> {db_path}")
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--db", default=str(CORPUS_DIR / "patch_index.db"))
    args = ap.parse_args()
    build_index(args.windows, args.db)


if __name__ == "__main__":
    main()
