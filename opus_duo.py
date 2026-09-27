#!/usr/bin/env python3
"""Opus as both artist and curator, in separate contexts. No local model.

The curator is a fresh `claude -p` that sees only the render and cell dump
(harness.opus_curate_review / opus_subject_check), never the artist's notes.

Defect count does not predict the verdict. The signals recorded are:
  1. whether the blind read names the intended subject
  2. whether the review treats the subject as constructed or as a placeholder

Usage: python3 opus_duo.py plan <slug> <task...>
       python3 opus_duo.py gates <slug> <path> [queries...]
       python3 opus_duo.py judge <slug> <path> [label]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

WORKSPACE = harness.WORKSPACE
LEDGER = Path("corpus/opus_duo_ledger.json")

# Reviewer phrasing for constructed vs placeholder, taken from
# calibration-run accepts and rejects.
CONSTRUCTED = re.compile(
    r"real constructed piece|it is constructed|constructed structure"
    r"|defects of a finished piece|polish gaps in a finished work"
    r"|hand-built|deliberate composition|not a geometric (stand-in|placeholder)",
    re.I)
PLACEHOLDER = re.compile(
    r"geometric placeholder|geometric stand-in|reads as (a )?placeholder"
    r"|never resolves|does not resolve|abandoned partway"
    r"|scaffolding|in-progress render|captured mid-build|renderer test pattern",
    re.I)


def _ledger():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"rounds": [], "cost_usd": 0.0}


def _save(led):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2, default=str))


def _spend(led, add):
    led["cost_usd"] = round(led["cost_usd"] + (add or 0), 4)
    if led["cost_usd"] > 40:
        print(f"!! CAP EXCEEDED: ${led['cost_usd']:.2f} of $40 -- stopping")
        _save(led)
        sys.exit(2)
    return led["cost_usd"]


def artist(slug, task, extra=""):
    """Run one artist turn in a fresh context. Returns cost in USD or None.

    The artist sees the task, `extra` and files on disk, never the curator's reasoning.
    """
    style = (WORKSPACE / "STYLE.md").read_text()
    prompt = f"""You are the artist in AGENTSCII, making real ANSI/textmode
art with the canvas_* tools. Work in Python from the repo root:

    import canvas_tools as ct
    W = {str(WORKSPACE)!r}
    ct.new_canvas(W, {slug!r}, 80, 50, bg=0)      # 80 wide x 100 px tall
    ct.slab_px / ct.sphere_px / ct.capsule_px      # LIT volumes
    ct.fill_px / ct.circle_px                      # FLAT elements only
    ct.strand_shade / ct.text / ct.metrics
    ct.save_ans(W, {slug!r}, 'scratch/{slug}.ans', title=..., handles='opus')

Render and LOOK at your work before you finish:
    import harness
    b64, _ = harness.render_ans_to_png_b64('workspace/scratch/{slug}.ans')

{task}

{extra}

=== STYLE.md ===
{style}
"""
    r = harness._run_claude_p(
        ["claude", "-p", prompt, "--model", harness.OPUS_MODEL,
         "--allowedTools", "Bash,Read,Write", "--output-format", "json"],
        timeout=1500, retries=0, cwd=str(Path(__file__).parent))
    if r is None or r.returncode != 0:
        print("ARTIST FAILED:", r.stderr[:300] if r is not None else "no result")
        return None
    return json.loads(r.stdout).get("total_cost_usd")


def gates(path, queries):
    """Run the same gates submit_piece runs. Returns True if they pass."""
    ok, report = harness.check_piece_gates(path, retrieval_queries=queries)
    print(("GATES PASS" if ok else "GATES BLOCKED") + "\n" + report)
    return ok


def judge(path, label):
    """Blind subject read plus full defect review, both in fresh contexts."""
    sub = harness.opus_subject_check(path)
    rev = harness.opus_curate_review(path, "accept",
                                     "Submitted for review. Assess on its own merits.")
    text = rev.get("opus_reasoning") or rev.get("message") or ""
    verdict = rev.get("opus_verdict")
    # A blocked review has no verdict. Report that rather than
    # defect_lines 0, which would read as a clean sheet.
    if verdict is None:
        print(json.dumps({"label": label, "path": str(path),
                          "REVIEW_DID_NOT_RUN": rev.get("status") or "no verdict",
                          "message": text.strip()}, indent=2))
        return {"label": label, "path": str(path), "verdict": None,
                "blocked": rev.get("status") or "no verdict", "reasoning": text}
    constructed = bool(CONSTRUCTED.search(text))
    placeholder = bool(PLACEHOLDER.search(text))
    m = harness._compute_piece_metrics(path)
    out = {
        "glyph_carried_pct": round(harness._glyph_carried_pct(path), 1),
        "label": label, "path": str(path),
        "blind_subject": sub.get("blind_subject"),
        "verdict": verdict,
        "reads_constructed": constructed,
        "reads_placeholder": placeholder,
        "defect_lines": len([l for l in text.split("\n")
                             if l.strip().startswith(("- ", "| ", "**"))]),
        "metrics": harness._fmt_metrics(m) if m else None,
        "reasoning": text,
    }
    print(json.dumps({k: v for k, v in out.items() if k != "reasoning"}, indent=2))
    return out


if __name__ == "__main__":
    cmd, slug = sys.argv[1], sys.argv[2]
    led = _ledger()
    if cmd == "plan":
        task = " ".join(sys.argv[3:])
        c = artist(slug, task)
        print(f"plan cost ${c}  running total ${_spend(led, c):.2f}")
        _save(led)
    elif cmd == "gates":
        gates(sys.argv[3], sys.argv[4:])
    elif cmd == "judge":
        res = judge(sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else slug)
        led["rounds"].append(res)
        _save(led)
