#!/usr/bin/env python3
"""Download 16colo.rs artpacks by year and extract .ANS/.ASC files.

Source: the sixteencolors/sixteencolors-archive GitHub repo, one zip per
pack under a directory per year.

Usage:
    python3 corpus/fetch.py --years 1996 1997 --limit-per-year 50
    python3 corpus/fetch.py --years all --max-size-mb 10

Output layout:
    corpus/raw/<year>/<packname>.zip       -- downloaded pack archives
    corpus/data/<year>/<packname>/*.ANS    -- extracted .ANS/.ASC files
    corpus/data/manifest.jsonl             -- one record per extracted file
"""
import argparse
import json
import os
import sys
import time
import zipfile
import zlib
import io
from pathlib import Path

import requests

REPO = "sixteencolors/sixteencolors-archive"
API_BASE = f"https://api.github.com/repos/{REPO}/contents"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/master"

CORPUS_DIR = Path(__file__).resolve().parent
RAW_DIR = CORPUS_DIR / "raw"
DATA_DIR = CORPUS_DIR / "data"
MANIFEST_PATH = DATA_DIR / "manifest.jsonl"

ALL_YEARS = [str(y) for y in range(1990, 2027)]

ANS_EXTS = {".ans", ".asc", ".ice", ".nfo"}  # recognized
WANTED_EXTS = {".ans", ".asc"}

USER_AGENT = "agentscii-corpus-fetch/1.0 (research corpus build, contact via github.com/Intranet-Explorer/agentscii)"


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        # Fall back to the gh CLI token. Unauthenticated API calls are
        # limited to 60/hour.
        try:
            import subprocess
            out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
            if out.returncode == 0 and out.stdout.strip():
                token = out.stdout.strip()
        except Exception:
            pass
    if token:
        s.headers.update({"Authorization": f"token {token}"})
    return s


def _get_json(session, url, retries=3):
    for attempt in range(retries):
        r = session.get(url, timeout=30)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = r.headers.get("X-RateLimit-Reset")
            wait = max(5, int(reset) - int(time.time())) if reset else 60
            print(f"  [rate limited, waiting {wait}s]", file=sys.stderr)
            time.sleep(min(wait, 300))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"failed to fetch {url} after {retries} retries")


def list_year_packs(session, year):
    """Return [(pack_zip_name, size_bytes, download_url), ...] for a year.

    The Contents API ignores per_page/page for directories and returns the
    whole listing in one response, so there is no pagination loop.
    """
    url = f"{API_BASE}/{year}"
    try:
        items = _get_json(session, url)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []  # no directory for this year
        raise
    packs = [
        (item["name"], item["size"], item["download_url"])
        for item in items
        if item["type"] == "file" and item["name"].lower().endswith(".zip")
    ]
    if len(items) >= 1000:
        # The Contents API silently truncates listings at 1000 entries.
        # No year is that large yet; this warns if one gets there.
        print(
            f"  [WARNING: {year} returned {len(items)} items -- at/over "
            f"GitHub's ~1000-entry directory listing limit, some packs may "
            f"be silently missing. Consider the Git Trees API instead if "
            f"this year needs full coverage.]",
            file=sys.stderr,
        )
    return packs


def download_pack(session, year, name, url, dest, retries=3):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True  # already downloaded
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=60)
            r.raise_for_status()
            tmp = dest.with_suffix(".zip.part")
            tmp.write_bytes(r.content)
            tmp.rename(dest)
            return True
        except Exception as e:
            print(f"  [retry {attempt+1}/{retries}] {name}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return False


def extract_pack(zip_path, out_dir, manifest_fh):
    """Extract .ans/.asc members from a pack zip. Returns the count extracted.

    Flattens nested directories and logs and skips members zipfile can't
    read (old implode/shrink methods, corrupt data).
    """
    extracted = 0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = Path(info.filename).suffix.lower()
                if ext not in WANTED_EXTS:
                    continue
                try:
                    data = zf.read(info)
                except (NotImplementedError, zipfile.BadZipFile, RuntimeError,
                        zlib.error, EOFError) as e:
                    # Corrupt deflate data raises a bare zlib.error, and a
                    # truncated member raises EOFError; neither is BadZipFile.
                    print(f"    [skip member, unsupported: {info.filename}: {e}]", file=sys.stderr)
                    continue
                safe_name = Path(info.filename).name  # drop internal dirs
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / safe_name
                # Suffix members that share a basename after flattening.
                if out_path.exists():
                    stem, suf = out_path.stem, out_path.suffix
                    n = 2
                    while out_path.exists():
                        out_path = out_dir / f"{stem}__{n}{suf}"
                        n += 1
                out_path.write_bytes(data)
                manifest_fh.write(json.dumps({
                    "path": str(out_path.relative_to(DATA_DIR)),
                    "pack_zip": zip_path.name,
                    "size": len(data),
                }) + "\n")
                extracted += 1
    except (zipfile.BadZipFile, OSError) as e:
        print(f"  [bad zip, skipping whole pack: {zip_path.name}: {e}]", file=sys.stderr)
    return extracted


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", nargs="+", default=["all"],
                     help="years to fetch, e.g. '1996 1997', or 'all' for 1990-2026")
    ap.add_argument("--limit-per-year", type=int, default=None,
                     help="max number of packs to download per year (for a quick sample)")
    ap.add_argument("--max-size-mb", type=float, default=None,
                     help="skip individual pack zips larger than this")
    ap.add_argument("--seed", type=int, default=0, help="random seed for --limit-per-year sampling")
    args = ap.parse_args()

    years = ALL_YEARS if args.years == ["all"] else args.years
    session = _session()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest_mode = "a" if MANIFEST_PATH.exists() else "w"

    total_packs = 0
    total_files = 0
    with open(MANIFEST_PATH, manifest_mode) as manifest_fh:
        for year in years:
            print(f"=== {year} ===")
            try:
                packs = list_year_packs(session, year)
            except Exception as e:
                print(f"  [failed to list {year}: {e}]", file=sys.stderr)
                continue
            print(f"  {len(packs)} packs listed")

            if args.max_size_mb is not None:
                max_bytes = args.max_size_mb * 1024 * 1024
                packs = [p for p in packs if p[1] <= max_bytes]
                print(f"  {len(packs)} packs after size filter (<= {args.max_size_mb}MB)")

            if args.limit_per_year is not None and len(packs) > args.limit_per_year:
                import random
                rng = random.Random(args.seed)
                packs = rng.sample(packs, args.limit_per_year)
                print(f"  sampled down to {len(packs)} packs (seed={args.seed})")

            for name, size, url in packs:
                zip_dest = RAW_DIR / year / name
                ok = download_pack(session, year, name, url, zip_dest)
                if not ok:
                    print(f"  [FAILED to download after retries: {name}]", file=sys.stderr)
                    continue
                total_packs += 1
                out_dir = DATA_DIR / year / Path(name).stem
                if out_dir.exists() and any(out_dir.iterdir()):
                    # Already extracted. Re-extracting would create __2
                    # copies via the basename de-dup.
                    continue
                try:
                    n = extract_pack(zip_dest, out_dir, manifest_fh)
                except Exception as e:
                    # One bad pack must not end a long run.
                    print(f"  [unexpected error extracting {name}, skipping pack: {e}]", file=sys.stderr)
                    n = 0
                total_files += n
                if total_packs % 25 == 0:
                    manifest_fh.flush()
                    print(f"  ...{total_packs} packs processed, {total_files} .ans/.asc files extracted so far")

    print(f"\nDone. {total_packs} packs downloaded, {total_files} .ans/.asc files extracted.")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
