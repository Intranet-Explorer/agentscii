#!/usr/bin/env python3
"""Gate calibration: does the defect reviewer accept REAL 16colo.rs art?

The control that was never run. Five house pieces have now been
rejected in a row; before concluding the artists are the problem, put
known-good archive work through the identical review and see whether it
draws the same defect vocabulary.

Blinding:
  * SAUCE records and trailing metadata stripped (they name the group,
    artist and year outright)
  * any in-file credit/handle rows redacted from the RENDER via the
    existing redact_title_rows path
  * neutral slugs (piece_a .. piece_g), shuffled, so filename order
    carries no signal
  * the reviewer gets the same prompt the live gate uses -- no hint
    that this is archive work or a calibration run

Mixed in: AQUEDUCT and _keeper.v7, so house and archive pieces are
judged under identical conditions in one batch.
"""
import json
import random
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

REAL = [
    ("workspace/references/study/blocktronics-ra_mindseye.ANS", "blocktronics figure"),
    ("workspace/references/study/asphyx-acid_logo.ANS", "ACiD logo"),
    ("workspace/references/study/somms-neo_tokyo.ANS", "landscape/cityscape"),
    ("workspace/references/study/blocktronics-n_silove.ANS", "portrait"),
    ("workspace/references/study/we-One_love.ans", "text-heavy"),
]
HOUSE = [
    ("workspace/references/study/_opus_AQUEDUCT.ans", "house/opus AQUEDUCT"),
    ("workspace/rejected/_keeper.v7.ans", "house/qwen _keeper.v7"),
]

# SAUCE: 128-byte record at EOF starting "SAUCE", optionally preceded by
# a COMNT block. Carries title, author and group in plain text -- the
# single biggest tell that a file came from the archive.
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


if __name__ == "__main__":
    main()
