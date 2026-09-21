#!/usr/bin/env python3
"""corpus/patch_meta.py -- add a parent_meta table (SAUCE title/author/
group/year per unique parsed piece) to patch_index.db, for
find_patches()'s text-match path. Scans corpus/parsed directly (86,093
files) rather than corpus/windows.jsonl (1.26M rows, no title/author
field) since SAUCE title/author isn't carried through windowing.

Usage:
    python3 corpus/patch_meta.py [--parsed-dir corpus/parsed] [--db corpus/patch_index.db]
"""
import argparse
import sqlite3
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS parent_meta (
    parent_path TEXT PRIMARY KEY,
    sauce_title TEXT,
    sauce_author TEXT,
    sauce_group TEXT,
    sauce_date TEXT
);
CREATE INDEX IF NOT EXISTS idx_title ON parent_meta(sauce_title);
CREATE INDEX IF NOT EXISTS idx_author ON parent_meta(sauce_author);
"""


def _decode(field):
    if field.size == 0:
        return ""
    return field.item().decode("utf-8", "replace").strip()


def build_meta(parsed_dir, db_path, batch_size=2000):
    parsed_dir = Path(parsed_dir)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)

    files = sorted(parsed_dir.rglob("*.npz"))
    rows_buf = []
    n_errors = 0

    def flush():
        if rows_buf:
            conn.executemany(
                "INSERT OR REPLACE INTO parent_meta "
                "(parent_path, sauce_title, sauce_author, sauce_group, sauce_date) "
                "VALUES (?, ?, ?, ?, ?)",
                rows_buf,
            )
            rows_buf.clear()

    for i, path in enumerate(files):
        rel = str(path.relative_to(parsed_dir))
        try:
            d = np.load(path)
            rows_buf.append((
                rel, _decode(d["sauce_title"]), _decode(d["sauce_author"]),
                _decode(d["sauce_group"]), _decode(d["sauce_date"]),
            ))
        except Exception:
            n_errors += 1
            continue
        if len(rows_buf) >= batch_size:
            flush()
        if (i + 1) % 20000 == 0:
            print(f"  ...{i+1}/{len(files)}")
    flush()
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM parent_meta").fetchone()[0]
    conn.close()
    print(f"parent_meta: {count}/{len(files)} pieces indexed ({n_errors} errors)")
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--db", default=str(CORPUS_DIR / "patch_index.db"))
    args = ap.parse_args()
    build_meta(args.parsed_dir, args.db)


if __name__ == "__main__":
    main()
