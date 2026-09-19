#!/usr/bin/env python3
"""corpus/caption.py -- step 2 captioning: for each window's PARENT
piece, generate a content caption from an ansilove render using the
local VLM (qwen3.8:27b-mlx via Ollama), prepend SAUCE year/group.
Captions are cached per parent piece (one real VLM call per unique
piece, not per window -- many windows share a parent) since "caption
quality only needs to be roughly right" per instruction, not a
per-window luxury re-render.

Usage:
    python3 corpus/caption.py [--windows corpus/windows.jsonl]
                               [--out corpus/captions.json]
                               [--limit N]
"""
import argparse
import base64
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434/api/chat"
CAPTION_MODEL = "qwen3.8:27b-mlx"


def render_to_png(ans_path, out_png):
    """ansilove render -- real archive files are CP437, this is the
    correct renderer for them (unlike harness.py's own renderer, which
    is built for UTF-8 agent-authored files)."""
    result = subprocess.run(
        ["ansilove", "-c", "80", "-o", str(out_png), str(ans_path)],
        capture_output=True, text=True, timeout=30,
    )
    return out_png.exists() and out_png.stat().st_size > 0


def caption_with_vlm(png_path, timeout=90):
    img_b64 = base64.b64encode(png_path.read_bytes()).decode()
    payload = json.dumps({
        "model": CAPTION_MODEL,
        "messages": [{
            "role": "user",
            "content": (
                "This is a piece of ANSI/ASCII textmode art. In one or "
                "two plain sentences, describe its literal visual "
                "content -- subject, style, notable colors/technique. "
                "Don't guess at a title or artist; just describe what "
                "you see."
            ),
            "images": [img_b64],
        }],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        r = json.loads(resp.read())
    return r.get("message", {}).get("content", "").strip()


def get_sauce_meta(npz_path):
    import numpy as np
    d = np.load(npz_path)
    group = d["sauce_group"].item().decode("utf-8", "replace").strip() if d["sauce_group"].size else ""
    date = d["sauce_date"].item().decode("utf-8", "replace").strip() if d["sauce_date"].size else ""
    year = date[:4] if len(date) >= 4 and date[:4].isdigit() else None
    if not year:
        # fall back to the year directory in the parsed path (corpus/parsed/<year>/<pack>/<file>)
        rel = str(npz_path)
        for part in Path(rel).parts:
            if part.isdigit() and len(part) == 4:
                year = part
                break
    return group or None, year or None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows", default=str(CORPUS_DIR / "windows.jsonl"))
    ap.add_argument("--parsed-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--data-dir", default=str(CORPUS_DIR / "data"))
    ap.add_argument("--out", default=str(CORPUS_DIR / "captions.json"))
    ap.add_argument("--limit", type=int, default=None, help="cap number of UNIQUE parent pieces captioned")
    args = ap.parse_args()

    parsed_dir = Path(args.parsed_dir)
    data_dir = Path(args.data_dir)

    parent_paths = set()
    with open(args.windows) as f:
        for line in f:
            row = json.loads(line)
            parent_paths.add(row["parent_path"])
    parent_paths = sorted(parent_paths)
    if args.limit:
        parent_paths = parent_paths[:args.limit]
    print(f"{len(parent_paths)} unique parent pieces to caption")

    captions = {}
    existing = Path(args.out)
    if existing.exists():
        captions = json.loads(existing.read_text())
        print(f"Resuming: {len(captions)} already captioned")

    errors = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, rel_npz in enumerate(parent_paths):
            if rel_npz in captions:
                continue
            npz_path = parsed_dir / rel_npz
            # the real source .ans/.asc lives under data_dir at the same
            # relative path minus the .npz suffix
            ans_rel = rel_npz[:-len(".npz")] if rel_npz.endswith(".npz") else rel_npz
            ans_path = data_dir / ans_rel
            if not ans_path.exists():
                errors += 1
                continue
            png_path = Path(tmpdir) / "render.png"
            try:
                ok = render_to_png(ans_path, png_path)
                if not ok:
                    errors += 1
                    continue
                caption = caption_with_vlm(png_path)
            except Exception as e:
                errors += 1
                continue

            group, year = get_sauce_meta(npz_path)
            prefix_parts = [p for p in (year, group) if p]
            prefix = " / ".join(prefix_parts)
            full_caption = f"[{prefix}] {caption}" if prefix else caption

            captions[rel_npz] = full_caption

            if (i + 1) % 50 == 0:
                print(f"  ...{i+1}/{len(parent_paths)} captioned, {errors} errors")
                Path(args.out).write_text(json.dumps(captions, indent=2))  # checkpoint

    Path(args.out).write_text(json.dumps(captions, indent=2))
    print(f"\nDone. {len(captions)} captions written, {errors} errors.")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
