#!/usr/bin/env python3
"""Blind pairwise: Opus-artist pieces vs the Qwen-artist baseline.

Blind in the ways that matter, per the design the human asked for
earlier: titles/credits redacted from both renders, order randomized
per comparison, neutral A/B labels, and the judge is told nothing about
which model made what. Prints the mapping only after the verdict.
"""
import json
import random
import subprocess
import sys
import tempfile
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

BASE = [
    ("workspace/rejected/_keeper.v7.ans", "qwen/_keeper.v7"),
    ("workspace/references/study/_lastlight.v3.ans", "qwen/_lastlight.v3"),
]
OPUS = [
    ("workspace/scratch/_opus1.ans", "opus/AQUEDUCT"),
    ("workspace/scratch/_opus2.ans", "opus/PROSPECTOR"),
    ("workspace/scratch/_opus3.ans", "opus/CROSSING"),
]
PROMPT = """Read a.png and b.png in this directory. Two pieces of
ANSI/textmode art. You have NO other context -- no titles, no artist,
no intent. Titles and credit lines have been redacted from both.

Judge which is the better piece of art, on these grounds only:
does a subject actually resolve into a thing; is it lit coherently
from a consistent source; is there real depth and arrangement, or is
it flat blocks; would it hold up in a real ANSI art pack.

Be skeptical of both. Say what is wrong with each.

End with exactly one line: WINNER: A or WINNER: B or WINNER: TIE
"""


def render(path, out):
    b64, _ = harness.render_ans_to_png_b64(
        path, offset=0, max_rows=140, redact_title_rows=True)
    if b64 is None:
        return False
    Path(out).write_bytes(base64.b64decode(b64))
    return True


def compare(p1, l1, p2, l2, rng):
    flip = rng.random() < 0.5
    (pa, la), (pb, lb) = ((p2, l2), (p1, l1)) if flip else ((p1, l1), (p2, l2))
    d = tempfile.mkdtemp(prefix="pairwise_")
    if not (render(pa, Path(d) / "a.png") and render(pb, Path(d) / "b.png")):
        return None
    r = harness._run_claude_p(
        ["claude", "-p", PROMPT, "--model", "claude-opus-5",
         "--allowedTools", "Read", "--output-format", "json"],
        timeout=600, retries=0, cwd=d)
    if r is None or r.returncode != 0:
        return {"error": (r.stderr[:200] if r else "no result")}
    data = json.loads(r.stdout)
    txt = data.get("result", "")
    verdict = next((ln.split(":", 1)[1].strip().upper()
                    for ln in txt.splitlines()
                    if ln.strip().upper().startswith("WINNER:")), "?")
    winner = {"A": la, "B": lb}.get(verdict, verdict)
    return {"A": la, "B": lb, "verdict": verdict, "winner": winner,
            "cost": data.get("total_cost_usd"), "reasoning": txt[-1500:]}


def main():
    rng = random.Random(20260923)
    out = []
    for op, ol in OPUS:
        for bp, bl in BASE:
            res = compare(op, ol, bp, bl, rng)
            if res is None or "error" in res:
                print(f"{ol} vs {bl}: FAILED {res}")
                continue
            print(f"{ol} vs {bl}  ->  WINNER: {res['winner']}  "
                  f"(shown as {res['verdict']}, ${res['cost']})")
            res.update(opus_piece=ol, base_piece=bl)
            out.append(res)
            Path("corpus/opus_pairwise.json").write_text(
                json.dumps(out, indent=2, default=str))
    wins = sum(1 for r in out if r["winner"].startswith("opus"))
    print(f"\nOpus won {wins} of {len(out)} blind comparisons")
    print(f"total cost: ${sum(r.get('cost') or 0 for r in out):.2f}")


if __name__ == "__main__":
    main()
