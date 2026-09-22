#!/usr/bin/env python3
"""corpus/build_clip_index.py -- CLIP visual embedding index over the
train-split patch corpus, replacing find_patches()'s title-keyword
matching (user direction, 2026-09-20: keyword matching only works when
a real content-bearing SAUCE title happens to exist -- most don't.
"Replace title matching with visual embeddings. Render each patch to
PNG, embed with CLIP (open_clip, a ViT-B/32 or similar, MPS on this
machine), store in a vector index. Query = CLIP text embedding ->
nearest patches. Title keywords become an optional filter, not the
primary match.").

Pipeline: for each candidate window in corpus/patch_index.db, skip
windows that are mostly blank (subject_frac < 0.1, same convention as
technique_index.py's subject_cells) or mostly ASCII text
(alnum_frac > 0.3 -- logos/wordmarks aren't what a shading-technique
query is after), render to PNG (harness's own rasterizer via
eval_harness.render_grid_to_png, same renderer used everywhere else in
this pipeline), embed batches with open_clip ViT-B/32 (openai
weights), store as a single float32 .npy matrix + a parallel
sqlite table mapping row index -> (parent_path, row_offset, col_offset).

Runs single-process for rendering (multiprocessing via Pool hits a
macOS spawn/heredoc incompatibility when driven from -c; a real
Pool-based render step is a possible future speedup but out of scope
here) with the CLIP forward pass batched on MPS. Caps total windows
processed via --limit so the full pass stays inside the user's ~4hr
budget on this machine -- reports the real measured render+embed rate
and extrapolates, rather than assuming.

Usage:
    python3 corpus/build_clip_index.py --limit 60000 --out corpus/clip_index
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
AGENTSCII_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(AGENTSCII_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import numpy as np

from find_patches import _load_patch_grids
from eval_harness import render_grid_to_png


def is_usable(chars, bg):
    is_space = (chars == 0x20)
    is_true_bg = is_space & (bg == 0)
    subject_frac = 1.0 - (is_true_bg.sum() / chars.size)
    alnum_mask = ((chars >= 0x30) & (chars <= 0x39)) | ((chars >= 0x41) & (chars <= 0x5A)) | ((chars >= 0x61) & (chars <= 0x7A))
    alnum_frac = alnum_mask.sum() / chars.size
    return subject_frac >= 0.1 and alnum_frac <= 0.3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(CORPUS_DIR / "patch_index.db"))
    ap.add_argument("--limit", type=int, default=60000, help="max windows to process (after blank/alnum filtering, before this cap is applied to CANDIDATES pulled from the db)")
    ap.add_argument("--out", default=str(CORPUS_DIR / "clip_index"))
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--time-budget-hours", type=float, default=4.0)
    args = ap.parse_args()

    import torch
    import open_clip

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading CLIP ViT-B-32 (openai) on {device}...")
    t0 = time.time()
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    model = model.to(device).eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    print(f"  loaded in {time.time()-t0:.1f}s")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    total_available = conn.execute("SELECT COUNT(*) FROM patches").fetchone()[0]
    print(f"{total_available} candidate windows in {args.db}")

    # pull a randomized candidate pool larger than --limit since some
    # fraction gets filtered (blank/alnum) -- oversample 2x, trim after
    pull_n = min(total_available, args.limit * 2)
    rows = conn.execute(
        f"SELECT id, parent_path, row_offset, col_offset, window_rows, window_cols, "
        f"half_block_pct, shade_pct FROM patches ORDER BY RANDOM() LIMIT ?",
        (pull_n,),
    ).fetchall()
    conn.close()

    render_dir = out_dir / "_render_tmp"
    render_dir.mkdir(exist_ok=True)

    t_start = time.time()
    time_budget_s = args.time_budget_hours * 3600

    kept_meta = []
    imgs_batch = []
    embeddings = []
    n_skipped_blank_alnum = 0
    n_render_fail = 0
    n_processed_candidates = 0
    _last_checkpoint = [0]

    def _write_checkpoint(out_dir, embeddings, kept_meta):
        if not embeddings:
            return
        emb_matrix = np.concatenate(embeddings, axis=0)
        np.save(out_dir / "embeddings.npy", emb_matrix)
        meta_db = out_dir / "meta.db"
        if meta_db.exists():
            meta_db.unlink()
        meta_conn = sqlite3.connect(str(meta_db))
        meta_conn.execute("""
            CREATE TABLE meta (
                row_idx INTEGER PRIMARY KEY,
                parent_path TEXT, row_offset INTEGER, col_offset INTEGER,
                window_rows INTEGER, window_cols INTEGER,
                half_block_pct REAL, shade_pct REAL
            )
        """)
        meta_conn.executemany(
            "INSERT INTO meta VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(i, m["parent_path"], m["row_offset"], m["col_offset"], m["window_rows"],
              m["window_cols"], m["half_block_pct"], m["shade_pct"]) for i, m in enumerate(kept_meta)],
        )
        meta_conn.commit()
        meta_conn.close()
        print(f"  [checkpoint] wrote {emb_matrix.shape[0]} embeddings to {out_dir}")

    def flush_batch():
        if not imgs_batch:
            return
        with torch.no_grad():
            batch = torch.stack([preprocess(im) for im in imgs_batch]).to(device)
            feats = model.encode_image(batch)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        embeddings.append(feats.cpu().numpy().astype(np.float32))
        imgs_batch.clear()

    from PIL import Image

    for row in rows:
        if len(kept_meta) >= args.limit:
            break
        elapsed = time.time() - t_start
        if elapsed > time_budget_s:
            print(f"  time budget ({args.time_budget_hours}h) reached at {len(kept_meta)} kept -- stopping early")
            break
        n_processed_candidates += 1

        grids = _load_patch_grids(row["parent_path"], row["row_offset"], row["col_offset"], row["window_rows"], row["window_cols"])
        if grids is None:
            n_render_fail += 1
            continue
        chars, fg, bg = grids
        if not is_usable(chars, bg):
            n_skipped_blank_alnum += 1
            continue

        png_path = render_dir / f"{len(kept_meta)}.png"
        ok = render_grid_to_png(chars, fg, bg, png_path)
        if not ok or not png_path.exists():
            n_render_fail += 1
            continue

        try:
            img = Image.open(png_path).convert("RGB")
            img.load()
        except Exception:
            n_render_fail += 1
            continue

        imgs_batch.append(img)
        kept_meta.append({
            "parent_path": row["parent_path"], "row_offset": row["row_offset"],
            "col_offset": row["col_offset"], "window_rows": row["window_rows"],
            "window_cols": row["window_cols"], "half_block_pct": row["half_block_pct"],
            "shade_pct": row["shade_pct"],
        })
        png_path.unlink()  # embedded, don't need the file anymore

        if len(imgs_batch) >= args.batch_size:
            flush_batch()

        if len(kept_meta) % 5000 == 0:
            rate = len(kept_meta) / elapsed
            print(f"  ...{len(kept_meta)} kept ({n_processed_candidates} candidates seen, "
                  f"{n_skipped_blank_alnum} skipped blank/alnum, {n_render_fail} render fail) "
                  f"{rate:.1f}/s, {elapsed/60:.1f} min elapsed")

        # Checkpoint every 50k kept patches (found live, 2026-09-21: a
        # concurrent training run's memory watchdog killed this process
        # mid-run via SIGKILL -- this script only wrote embeddings.npy/
        # meta.db at the very end, so a kill at minute 107 lost 380k
        # patches of real compute with nothing recoverable. Writing
        # periodic checkpoints means a future interruption loses at
        # most one checkpoint interval's worth of work, and a resumed
        # run can pick up from the last checkpoint instead of
        # restarting from zero.)
        if len(kept_meta) % 50000 == 0 and len(kept_meta) > 0 and len(kept_meta) != _last_checkpoint[0]:
            flush_batch()
            _write_checkpoint(out_dir, embeddings, kept_meta)
            _last_checkpoint[0] = len(kept_meta)

    flush_batch()
    import shutil
    shutil.rmtree(render_dir, ignore_errors=True)

    if not embeddings:
        print("No embeddings produced -- aborting.")
        sys.exit(1)

    # Final write reuses _write_checkpoint (which unlinks meta.db before
    # recreating the table) instead of duplicating the CREATE TABLE logic --
    # the duplicated version here used to crash with "table meta already
    # exists" whenever a mid-run checkpoint had already created it (every
    # run over 50k patches), landing embeddings.npy but never meta.db's
    # final flush. Found live 2026-09-21: an 871,882-patch run hit exactly
    # this, stuck at the 850k checkpoint's meta.db with a fully up-to-date
    # embeddings.npy -- 21,882 embeddings with no queryable metadata.
    _write_checkpoint(out_dir, embeddings, kept_meta)
    emb_matrix = np.concatenate(embeddings, axis=0)

    total_time = time.time() - t_start
    print(f"\nDone. {len(kept_meta)} patches embedded in {total_time/60:.1f} min "
          f"({len(kept_meta)/total_time:.1f} patches/s).")
    print(f"  candidates examined: {n_processed_candidates}, skipped blank/alnum: {n_skipped_blank_alnum}, "
          f"render failures: {n_render_fail}")
    print(f"  embeddings: {out_dir / 'embeddings.npy'} shape {emb_matrix.shape}")
    print(f"  meta: {out_dir / 'meta.db'}")


if __name__ == "__main__":
    main()
