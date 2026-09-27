#!/usr/bin/env python3
"""Gate calibration: run known-good archive art through the defect reviewer.

Checks whether the reviewer rejects real 16colo.rs work with the same
vocabulary it uses on house pieces. House pieces are mixed into the batch.

Blinding:
  * SAUCE records and trailing metadata stripped (they name group, artist, year)
  * in-file credit rows redacted from the render (redact_title_rows)
  * neutral shuffled slugs (piece_a, piece_b, ...)
  * same prompt as the live gate, no hint this is a calibration run
"""
import json
import random
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

# Reference pieces are local-only and are not shipped with this repo.
# List your own (path, label) pairs here before running a calibration.
REAL = []
HOUSE = [
    ("workspace/references/study/_opus_AQUEDUCT.ans", "house/opus AQUEDUCT"),
    ("workspace/rejected/_keeper.v7.ans", "house/qwen _keeper.v7"),
]

# SAUCE: 128-byte record at EOF, optionally preceded by a COMNT block.
# Holds title, author and group in plain text.
SAUCE = b"SAUCE"


def strip_sauce(raw):
    i = raw.rfind(SAUCE)
    if i == -1:
        return raw
    j = raw.rfind(b"COMNT", 0, i)
    cut = j if j != -1 else i
    # EOF marker (^Z) often sits just before SAUCE
    while cut > 0 and raw[cut - 1:cut] == b"\x1a":
        cut -= 1
    return raw[:cut]


def anonymise(src, dst):
    raw = strip_sauce(Path(src).read_bytes())
    Path(dst).write_bytes(raw)
    return len(raw)


def main():
    rng = random.Random(20260923)
    batch = [(p, kind, "real") for p, kind in REAL] + \
            [(p, kind, "house") for p, kind in HOUSE]
    rng.shuffle(batch)

    tmp = Path(tempfile.mkdtemp(prefix="calib_"))
    labels = {}
    for i, (src, kind, origin) in enumerate(batch):
        slug = f"piece_{chr(ord('a') + i)}"
        dst = tmp / f"{slug}.ans"
        n = anonymise(src, dst)
        labels[slug] = {"source": src, "kind": kind, "origin": origin,
                        "bytes_after_strip": n}

    out = []
    for slug, meta in labels.items():
        path = tmp / f"{slug}.ans"
        r = harness.opus_curate_review(
            str(path), "accept",
            "Piece submitted for review. Assess it on its own merits.")
        verdict = r.get("opus_verdict")
        reasoning = r.get("opus_reasoning") or r.get("message") or ""
        rec = {"slug": slug, **meta, "verdict": verdict,
               "cost": r.get("cost"), "status": r.get("status"),
               "reasoning": reasoning}
        out.append(rec)
        print(f"{slug}  [{meta['origin']:5}] {meta['kind']:22} -> "
              f"{verdict or r.get('status')}")
        Path("corpus/gate_calibration.json").write_text(
            json.dumps(out, indent=2, default=str))

    print()
    for origin in ("real", "house"):
        rows = [r for r in out if r["origin"] == origin]
        acc = sum(1 for r in rows if r["verdict"] == "accept")
        print(f"{origin:5}: {acc} accept / {len(rows)} reviewed")
    print(f"total cost: ${sum(r.get('cost') or 0 for r in out):.2f}")


if __name__ == "__main__" and not REAL:
    sys.exit("REAL is empty: add local reference pieces to gate_calibration.REAL first")
if __name__ == "__main__":
    main()
