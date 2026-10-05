#!/usr/bin/env python3
"""Primed-read test: Opus sees the title, then judges legibility and quality.

The calibration sheet asked Tyler a TITLE-GIVEN question. opus_subject_check
asked a BLIND one. This runs the title-given question past Opus so the
comparison is like-for-like.

The prompt below is fixed in advance and is NOT tuned after seeing results.
Writes workspace/primed_read.json.
"""
import base64
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

ROOT = os.path.expanduser("~/agentscii")
OUT = os.path.join(ROOT, "workspace", "primed_read.json")

# FIXED PROMPT -- do not edit after the first run.
PROMPT = (
    "Read render.png in this directory.\n\n"
    'This ANSI art piece is titled: "{title}". '
    "(a) Does the image read as its title? YES/NO. "
    "(b) Independently of (a), is it well made? YES/NO. "
    "One line of reasoning each.\n\n"
    "Answer in this exact format:\n"
    "A: YES or NO\nA_REASON: <one line>\nB: YES or NO\nB_REASON: <one line>"
)


def ask(ans_path, title):
    """One primed read. Same render + cwd pattern opus_subject_check uses."""
    b64, _n = harness.render_ans_to_png_b64(ans_path, offset=0, max_rows=4000)
    if not b64:
        return None, None, None, None, "(render failed)"
    tmpdir = tempfile.mkdtemp(prefix="primed_read_")
    try:
        (Path(tmpdir) / "render.png").write_bytes(base64.b64decode(b64))
        r = harness._run_claude_p(
            ["claude", "-p", PROMPT.format(title=title),
             "--model", harness.OPUS_MODEL,
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    if r is None or r.returncode != 0:
        return None, None, None, None, "(call failed)"
    txt = json.loads(r.stdout).get("result", "")
    out = {}
    for line in txt.splitlines():
        s = line.strip()
        for key in ("A:", "A_REASON:", "B:", "B_REASON:"):
            if s.upper().startswith(key):
                out[key.rstrip(":")] = s.split(":", 1)[1].strip()
    yn = lambda v: None if v is None else v.strip().upper().startswith("Y")  # noqa: E731
    return (yn(out.get("A")), out.get("A_REASON", ""),
            yn(out.get("B")), out.get("B_REASON", ""), txt[:600])


def main():
    man = {m["id"]: m for m in json.load(
        open(os.path.join(ROOT, "workspace", "calibration", "manifest.json")))}
    done = {}
    if os.path.exists(OUT):
        done = {r["id"]: r for r in json.load(open(OUT))}
        print(f"  resuming: {len(done)} already read")

    results = list(done.values())
    for i in sorted(man):
        if i in done:
            continue
        m = man[i]
        f = os.path.join(ROOT, m["file"])
        a, ar, b, br, raw = ask(f, m["intended"])
        if a is None and b is None and raw.startswith("("):
            print(f"  [{i}] {raw} -- skipping {m['file']}")
            continue
        results.append({"id": i, "file": m["file"], "slug": m["slug"],
                        "title": m["intended"], "verdict": m["verdict"],
                        "reads": a, "reads_reason": ar,
                        "good": b, "good_reason": br, "raw": raw})
        print(f"  [{i:2d}] {m['slug']:16s} reads={a} good={b}")
        with open(OUT, "w") as fh:          # checkpoint every piece
            json.dump(sorted(results, key=lambda r: r["id"]), fh, indent=2)
    print(f"  wrote {OUT} ({len(results)} pieces)")


if __name__ == "__main__":
    main()
