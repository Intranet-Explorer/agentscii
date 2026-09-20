#!/usr/bin/env python3
# pre_release_dedup_guard.py  --  AGENTSCII pre-release dedup gate
# author: raze (joint-credited with hollis, who runs it as a release-checklist
#         step from pack18 onward; spec requested by hollis after the pack17
#         nebula-dup incident).
#
# WHAT IT DOES
#   Scans every .ans currently in gallery/unpacked/ and checks it against the
#   LIVE shipped catalog (every gallery/packNN/*.ans). Two failure classes:
#
#     1. MD5 COLLISION  -- a byte-identical piece is already shipped somewhere.
#        This is the NEBULA class (pack17): release_pack does not clear
#        unpacked/, so an already-shipped piece lingers and gets re-bundled.
#        HARD FAIL: always exits non-zero.
#
#     2. NAME COLLISION -- same .ans basename already shipped, but DIFFERENT
#        bytes. Catches a re-bundle of an old version under a new pack number
#        that the md5 check alone would miss if the bytes drifted. Because
#        legitimate versioned re-releases DO reuse slugs (e.g. poster.v8 ships
#        in two packs with different bytes), this is a WARNING by default and
#        only becomes fatal under --strict, so the gate doesn't cry wolf on
#        intentional new versions.
#
#   The _held-already-shipped/ and _held-superseded/ quarantine dirs are NOT
#   part of the live catalog and are excluded from the shipped index (per
#   hollis's spec -- they're audit trails, not things a future release should
#   be compared against as "already shipped").
#
# USAGE
#   python3 pre_release_dedup_guard.py            # default: md5=block, name=warn
#   python3 pre_release_dedup_guard.py --strict   # name collisions also block
#   python3 pre_release_dedup_guard.py --md5-only  # name collisions never fatal
#   python3 pre_release_dedup_guard.py -v          # verbose per-file listing
#
# EXIT CODES
#   0  clean (no hard failures; name warnings do not set non-zero unless --strict)
#   1  one or more MD5 collisions, OR a name collision under --strict
#   2  usage / structural error (e.g. unpacked/ missing)
#
# Designed to be run as a pre-release gate: it prints a one-line verdict so it
# slots cleanly into hollis's release checklist and fails loudly if a dup would
# ship.

import os
import sys
import hashlib
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent  # .../workspace
GALLERY = WORKSPACE / "gallery"
UNPACKED = GALLERY / "unpacked"

# Quarantine dirs: audit trails, NOT live catalog. Excluded from the shipped index.
EXCLUDE_DIRS = {"_held-already-shipped", "_held-superseded"}

# Version-suffix heuristic for core-slug matching: strip a trailing .vN or -vNN
# so "raze-nebula-v12" and "raze-nebula" compare as the same core piece.
VERSION_RE = re.compile(r"(?:\.[vV]|-v|_v)(\d+)$")


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def core_slug(basename_noext: str) -> str:
    """Strip a trailing version suffix so v1/v2 of the same piece share a slug."""
    prev = None
    s = basename_noext
    while True:
        m = VERSION_RE.search(s)
        if not m:
            return s
        s = s[: m.start()]
        if s == prev:  # guard against pathological infinite loop
            break
        prev = s
    return s


def shipped_index():
    """Return (md5_map, name_map, pack_count) over the LIVE catalog only."""
    md5_map = {}   # md5 -> [relpaths]
    name_map = {}  # basename(.ans) -> [relpaths]
    core_map = {}  # core-slug -> set(basenames)
    packs = sorted(p for p in GALLERY.glob("pack*") if p.is_dir())
    for pack in packs:
        for ans in sorted(pack.glob("*.ans")):
            rel = str(ans.relative_to(WORKSPACE))
            digest = md5_of(ans)
            md5_map.setdefault(digest, []).append(rel)
            name_map.setdefault(ans.name, []).append(rel)
            core = core_slug(ans.stem)
            core_map.setdefault(core, set()).add(ans.name)
    return md5_map, name_map, core_map, packs


def main():
    strict = False
    md5_only = False
    verbose = False
    for arg in sys.argv[1:]:
        if arg in ("--strict",):
            strict = True
        elif arg in ("--md5-only",):
            md5_only = True
        elif arg in ("-v", "--verbose"):
            verbose = True
        elif arg in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            print(f"!! unknown arg: {arg}", file=sys.stderr)
            return 2

    if not UNPACKED.is_dir():
        print(f"!! structural error: {UNPACKED} does not exist", file=sys.stderr)
        return 2

    md5_map, name_map, core_map, packs = shipped_index()
    unpacked_files = sorted(UNPACKED.glob("*.ans"))

    md5_hits = []      # (unpacked_rel, [shipped_rels])
    name_hits = []     # (unpacked_rel, basename, [shipped_rels], core_match_only)

    for ans in unpacked_files:
        rel = str(ans.relative_to(WORKSPACE))
        digest = md5_of(ans)

        # --- MD5 collision (hard) ---
        if digest in md5_map:
            md5_hits.append((rel, md5_map[digest]))

        # --- Name collision (soft unless --strict) ---
        if not md5_only and ans.name in name_map:
            shipped = [p for p in name_map[ans.name] if p != rel]
            if shipped:
                # Only a true name-collision if bytes differ (md5 already caught identical).
                same_bytes = digest in md5_map
                core_only = False
                if same_bytes:
                    continue  # already reported as md5 hit; don't double-report
                name_hits.append((rel, ans.name, shipped, core_only))

        # --- Core-slug advisory (possible version re-bundle under new number) ---
        if not md5_only:
            core = core_slug(ans.stem)
            siblings = sorted(core_map.get(core, set()))
            shipped_siblings = [s for s in siblings if s != ans.name]
            if shipped_siblings and (core, ) not in [(h[1],) for h in name_hits]:
                # advisory only: same core piece already shipped under a different exact name
                name_hits.append((rel, f"{ans.name} (core '{core}')",
                                  [f"shipped as {s}" for s in shipped_siblings], True))

    # --- Report ---
    print("=" * 68)
    print("AGENTSCII pre-release dedup guard")
    print(f"  unpacked/ : {len(unpacked_files)} .ans file(s)")
    print(f"  catalog   : {len(packs)} pack(s), "
          f"{sum(len(v) for v in md5_map.values())} shipped .ans, "
          f"{len(name_map)} distinct names")
    print("=" * 68)

    if verbose and unpacked_files:
        print("unpacked/ pieces:")
        for ans in unpacked_files:
            rel = str(ans.relative_to(WORKSPACE))
            digest = md5_of(ans)
            status = "OK"
            if digest in md5_map:
                status = "MD5-DUP"
            elif ans.name in name_map:
                status = "NAME-WARN"
            print(f"  [{status:9}] {rel}  md5={digest[:12]}")
        print()

    hard_fail = False

    if md5_hits:
        hard_fail = True
        print("!! MD5 COLLISION(S) -- byte-identical piece already shipped:")
        for rel, shipped in md5_hits:
            print(f"   {rel}")
            for s in shipped:
                print(f"      == identical to  {s}")
        print()

    if name_hits:
        fatal = strict and not md5_only
        label = "BLOCK" if fatal else "WARN"
        if fatal:
            hard_fail = True
        print(f"-- NAME COLLISION(S) [{label}]: same slug already shipped, bytes differ:")
        for rel, name, shipped, core_only in name_hits:
            tag = "core-slug advisory" if core_only else "exact-name collision"
            print(f"   {rel}  ({tag})")
            for s in shipped:
                print(f"      ~ matches     {s}")
        if not fatal:
            print("   (name collisions are non-fatal unless --strict is passed; "
                  "review whether these are intentional versioned re-releases)")
        print()

    # --- Verdict ---
    print("-" * 68)
    if hard_fail:
        n_md5 = len(md5_hits)
        n_name_fatal = len(name_hits) if (strict and not md5_only) else 0
        print(f"VERDICT: FAIL -- {n_md5} md5 collision(s), "
              f"{n_name_fatal} blocking name collision(s). Do NOT release.")
        return 1

    n_name_warn = len(name_hits) if not md5_only else 0
    if n_name_warn:
        print(f"VERDICT: PASS (with {n_name_warn} name warning(s) to eyeball -- "
              f"no byte-identical dups). Safe to release; review the warnings above.")
    else:
        print("VERDICT: PASS -- clean. No md5 or name collisions against the live catalog.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
