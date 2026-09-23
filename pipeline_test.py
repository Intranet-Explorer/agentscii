#!/usr/bin/env python3
"""Pipeline test: Opus plans, Qwen executes.

Opus produces, per piece, in ONE claude -p call:
  workspace/scratch/<slug>.spec.md      the written composition spec
  workspace/scratch/<slug>.blockin.ans  flat silhouettes, no shading

The block-in is then PINNED (copied read-only to
workspace/references/blockins/) so the curator can diff the finished
piece against exactly what was planned. Qwen's shifts add the shading,
texture, frame and signature passes and may not change subject,
layout, scale relationships or light direction.

Success criterion is NOT metrics (calibration proved they don't predict
the verdict): does the finished piece still read as a constructed
subject after Qwen's passes. Measured by running the blind subject
check on the block-in alone and again on the finished piece.

Usage: python3 pipeline_test.py plan <slug> <brief>
       python3 pipeline_test.py blindcheck <path>
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

WORKSPACE = harness.WORKSPACE
PINNED = WORKSPACE / "references" / "blockins"


def plan(slug, brief):
    style = (WORKSPACE / "STYLE.md").read_text()
    catalog = (WORKSPACE / "CATALOG.md").read_text()[:3500]
    prompt = f"""You are the COMPOSITION planner for AGENTSCII, an
ANSI/textmode art house. You do NOT finish pieces. You decide what the
piece is and where everything sits; another artist does the shading,
texture and detail passes afterwards.

Brief: {brief}

Produce exactly two artifacts.

1. workspace/scratch/{slug}.spec.md -- a written spec with these
   headings, concrete and specific, no hedging:
     ## Subject          one sentence: what a viewer must see
     ## Layout           every element, its pixel-space position and
                         size, and which plane it occupies
                         (foreground / midground / background)
     ## Scale            the size relationships that carry depth,
                         stated as ratios
     ## Palette          specific colour indices 0-15 per element
     ## Light            ONE direction for the whole piece, and which
                         face of each form is lit
     ## Do not change    what the executing artist must preserve

2. workspace/scratch/{slug}.blockin.ans -- the block-in ONLY: flat
   single-colour silhouettes in correct position and scale, NO shading,
   NO texture, NO frame, NO signature. Build it with canvas_tools:

     import canvas_tools as ct
     W = {str(WORKSPACE)!r}
     ct.new_canvas(W, {slug!r}, 80, 50, bg=0)
     ct.fill_px / ct.circle_px / ct.capsule_px   # flat colour only
     ct.save_ans(W, {slug!r}, 'scratch/{slug}.blockin.ans',
                 title=None, add_sig=False)

   Pixel space is 80 wide x 100 tall; 50 cell rows.

The single thing that matters: a viewer looking at the block-in alone
must be able to say what the subject is. Composition carries that, not
detail. Check it yourself by rendering:

     import harness
     b64, _ = harness.render_ans_to_png_b64(
         'workspace/scratch/{slug}.blockin.ans')

=== STYLE.md ===
{style}

=== CATALOG.md (do not repeat these subjects) ===
{catalog}
"""
    r = harness._run_claude_p(
        ["claude", "-p", prompt, "--model", "claude-opus-5",
         "--allowedTools", "Bash,Read,Write", "--output-format", "json"],
        timeout=1500, retries=0, cwd=str(Path(__file__).parent))
    if r is None or r.returncode != 0:
        print("FAILED:", r.stderr[:300] if r is not None else "no result")
        return None
    data = json.loads(r.stdout)
    cost = data.get("total_cost_usd")

    spec = WORKSPACE / "scratch" / f"{slug}.spec.md"
    blockin = WORKSPACE / "scratch" / f"{slug}.blockin.ans"
    ok = spec.exists() and blockin.exists()
    if ok:
        PINNED.mkdir(parents=True, exist_ok=True)
        shutil.copy2(blockin, PINNED / f"{slug}.blockin.ans")
        shutil.copy2(spec, PINNED / f"{slug}.spec.md")
        # read-only: the pin is the comparison baseline, it must not drift
        for f in (PINNED / f"{slug}.blockin.ans", PINNED / f"{slug}.spec.md"):
            f.chmod(0o444)
    print(json.dumps({"slug": slug, "cost_usd": cost, "spec": spec.exists(),
                      "blockin": blockin.exists(), "pinned": ok}, indent=2))
    return cost


def blindcheck(path):
    r = harness.opus_subject_check(path)
    print(json.dumps({"path": path, "status": r.get("status"),
                      "blind_subject": r.get("blind_subject"),
                      "intended": r.get("intended_title")}, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        plan(sys.argv[2], " ".join(sys.argv[3:]))
    elif sys.argv[1] == "blindcheck":
        blindcheck(sys.argv[2])
