#!/usr/bin/env python3
"""Qwen blind-read validation against Opus's blind subject check.

For every piece that already has an Opus blind read, show Qwen the SAME
render -- title rows redacted, no filename, no notes, fresh context per piece
-- and ask what it depicts. Then judge match/mismatch against the intended
title the way opus_subject_check does, and compare the two judgements.

Qwen is asked only for a description. The match/mismatch call is made the
same way for both sides so the comparison is of the READ, not of two
different judging procedures.

Writes workspace/qwen_blind_validation.json. Run with the harness stopped.
"""
import base64
import glob
import json
import os
import re
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

ROOT = os.path.expanduser("~/agentscii")
OUT = os.path.expanduser("~/agentscii-private/calibration/qwen_blind_validation.json")

PROMPT = ("What does this depict? One line, then confidence 1-5.\n\n"
          "Answer in this exact format:\n"
          "SUBJECT: <one short phrase naming the literal subject, or "
          '"abstract/no clear subject" if there genuinely is none>\n'
          "CONFIDENCE: <1-5>")


def locate(p):
    if os.path.exists(p):
        return p
    b = os.path.basename(p)
    for cand in (f"workspace/rejected/{b}", f"workspace/gallery/unpacked/{b}",
                 f"workspace/submissions/{b}"):
        full = os.path.join(ROOT, cand)
        if os.path.exists(full):
            return full
    hits = glob.glob(os.path.join(ROOT, "gallery", "pack*", b)) or \
        glob.glob(os.path.join(ROOT, "workspace", "gallery", "pack*", b))
    return hits[0] if hits else None


def opus_side(conn):
    """{file: {blind_subject, verdict, intended}} from the logged Opus calls."""
    out = {}
    rows = conn.execute(
        "SELECT path, opus_verdict, opus_reasoning, timestamp FROM opus_reviews "
        "WHERE qwen_decision='subject_check' ORDER BY timestamp"
    ).fetchall()
    for path, verdict, reasoning, _ts in rows:
        f = locate(path)
        if not f:
            continue
        rec = out.setdefault(f, {"blind_subject": None, "opus_verdict": None})
        if verdict == "n/a_subject_id":
            for line in (reasoning or "").splitlines():
                if line.strip().upper().startswith("SUBJECT:"):
                    rec["blind_subject"] = line.split(":", 1)[1].strip()
                    break
        elif verdict == "n/a_subject_match":
            for line in (reasoning or "").splitlines():
                if line.strip().upper().startswith("VERDICT:"):
                    v = line.split(":", 1)[1].strip().upper()
                    rec["opus_verdict"] = ("match" if "MATCH" in v
                                           and "MISMATCH" not in v else "mismatch")
                    break
    return out


def qwen_read(png_b64, model):
    """One blind read, fresh context: image only, no history, no title."""
    messages = [{"role": "user", "content": [
        {"type": "text", "text": PROMPT},
        {"type": "image_url",
         "image_url": {"url": f"data:image/png;base64,{png_b64}"}},
    ]}]
    resp = harness.call_ollama(model, messages, None)
    txt = (resp.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
    subject = conf = None
    for line in txt.splitlines():
        s = line.strip()
        if s.upper().startswith("SUBJECT:") and subject is None:
            subject = s.split(":", 1)[1].strip()
        elif s.upper().startswith("CONFIDENCE:") and conf is None:
            m = re.search(r"[1-5]", s)
            conf = int(m.group()) if m else None
    if subject is None:                      # model ignored the format
        subject = " ".join(txt.split())[:120] or None
    return subject, conf, txt


def judge(intended, blind_subject):
    """Match/mismatch, same wording opus_subject_check uses, same judge."""
    prompt = (
        f'An artist intended to draw: "{intended}"\n'
        f"An independent blind viewer, shown ONLY the rendered image with no "
        f'title, described the subject as: "{blind_subject}"\n\n'
        "Does the blind description plausibly match what the artist intended "
        '(allowing for stylized/conceptual titles -- e.g. "THE WATCHER" '
        "matching a description of an eye is a MATCH, not a mismatch), or "
        "does it read as a genuinely different subject than intended?\n\n"
        "Answer in this exact format:\nVERDICT: MATCH or VERDICT: MISMATCH\n"
        "REASON: <one sentence>")
    r = harness._run_claude_p(
        ["claude", "-p", prompt, "--model", harness.OPUS_MODEL,
         "--output-format", "json"])
    if r is None or r.returncode != 0:
        return None, "(judge call failed)"
    reasoning = json.loads(r.stdout).get("result", "")
    for line in reasoning.splitlines():
        if line.strip().upper().startswith("VERDICT:"):
            v = line.split(":", 1)[1].strip().upper()
            return ("match" if "MATCH" in v and "MISMATCH" not in v
                    else "mismatch"), reasoning
    return None, reasoning


def main():
    conn = sqlite3.connect(os.path.join(ROOT, "state.db"))
    opus = opus_side(conn)
    model = harness.AGENTS["curator"]["model"]
    print(f"  {len(opus)} pieces with an Opus blind read | qwen model: {model}")

    done = {}
    if os.path.exists(OUT):
        done = {r["file"]: r for r in json.load(open(OUT))}
        print(f"  resuming: {len(done)} already read")

    results = list(done.values())
    for i, (f, rec) in enumerate(sorted(opus.items()), 1):
        if f in done:
            continue
        intended = harness._extract_intended_title(f)
        b64, _n = harness.render_ans_to_png_b64(
            f, offset=0, max_rows=140, redact_title_rows=True)
        if not b64 or not intended or not rec.get("blind_subject"):
            print(f"  [{i}/{len(opus)}] skip {os.path.basename(f)} "
                  f"(render={bool(b64)} title={bool(intended)} "
                  f"opus_read={bool(rec.get('blind_subject'))})")
            continue
        t0 = time.time()
        try:
            subj, conf, raw = qwen_read(b64, model)
        except Exception as e:
            print(f"  [{i}/{len(opus)}] ERROR {os.path.basename(f)}: {str(e)[:70]}")
            continue
        row = {"file": os.path.relpath(f, ROOT), "intended": intended,
               "qwen_subject": subj, "qwen_confidence": conf,
               "opus_subject": rec["blind_subject"],
               "opus_verdict": rec["opus_verdict"], "qwen_verdict": None,
               "qwen_raw": raw[:400]}
        results.append(row)
        print(f"  [{i}/{len(opus)}] {os.path.basename(f):26s} "
              f"{time.time()-t0:4.0f}s  qwen: {str(subj)[:48]!r}")
        with open(OUT, "w") as fh:          # checkpoint every piece
            json.dump(results, fh, indent=2)

    # Judge each Qwen read against the intended title, same procedure as Opus.
    for r in results:
        if r.get("qwen_verdict") or not r.get("qwen_subject"):
            continue
        v, _reason = judge(r["intended"], r["qwen_subject"])
        r["qwen_verdict"] = v
        print(f"  judge {os.path.basename(r['file']):26s} qwen={v}")
        with open(OUT, "w") as fh:
            json.dump(results, fh, indent=2)

    print(f"  wrote {OUT} ({len(results)} pieces)")


if __name__ == "__main__":
    main()
