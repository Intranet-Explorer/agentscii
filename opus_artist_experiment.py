#!/usr/bin/env python3
"""Opus-as-artist experiment: 3 shifts, Opus 5 in the artist seat.

The discriminating test the project has been building toward: same
canvas tools, same STYLE.md, same gate, different model. If Opus
clears the bar the local model has missed for 41 shifts and 985 canvas
calls, the composition ceiling is the model. If it fails the same way,
the ceiling is the tooling or the task framing.

Deliberately NOT wired into harness.run_shift: this is a measurement,
not a new seat. It drives the same canvas_tools module the artist seat
drives, through `claude -p` with the real tool schemas, and writes to
the same workspace.

Usage: python3 opus_artist_experiment.py [n_shifts]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

WORKSPACE = harness.WORKSPACE
CANVAS_TOOLS = [t for t in harness.TOOLS
                if t["function"]["name"].startswith("canvas_")
                or t["function"]["name"] in ("find_patches", "preview_piece",
                                             "compare_to_reference",
                                             "inspect_piece")]


def _brief(slug):
    style = (WORKSPACE / "STYLE.md").read_text()
    catalog = (WORKSPACE / "CATALOG.md").read_text()
    return f"""You are the artist in AGENTSCII, making real ANSI/textmode art.

Draw ONE new piece this session, on canvas slug '{slug}'.

Subject: something NOT in the catalog below, with several distinct
forms at different scales -- a scene, a creature with limbs, a machine,
a structure in a landscape. NOT a single centered round object.

Work in Python, driving canvas_tools directly. The module is already
importable from the repo root:

    import canvas_tools as ct
    W = {str(WORKSPACE)!r}
    ct.new_canvas(W, {slug!r}, 80, 50, bg=0)
    ct.slab_px(W, {slug!r}, x, y, w, h, color, light_direction='top-left',
               shadow_color=..., hi_color=..., side='left', side_w=...)
    ct.sphere_px(W, {slug!r}, cx, cy, r, color, light_x, light_y,
                 shadow_color=...)
    ct.capsule_px(W, {slug!r}, ax, ay, bx, by, r, color,
                  light_direction='top-left', shadow_color=...)
    ct.strand_shade(W, {slug!r}, region_dict, [dx,dy], [colors], ...)
    ct.text(W, {slug!r}, x, y, "TEXT", fg, bg)
    ct.metrics(W, {slug!r})          # half_block/shade/colors/masses
    ct.save_ans(W, {slug!r}, 'scratch/_{slug}.ans', title='TITLE',
                handles='opus')

Pixel space is 80 wide x 100 tall (2 pixels per cell row). Cell rows
are 50. Check your work with ct.metrics() as you go, and render a PNG
to look at it:

    import harness
    b64, _ = harness.render_ans_to_png_b64('workspace/scratch/_{slug}.ans')

The house bar is _orb.v59: 37.9% half_block / 32.1% shade, subject-only.

=== STYLE.md ===
{style}

=== CATALOG.md (do not repeat these subjects) ===
{catalog[:4000]}
"""


def run_shift(n, slug):
    prompt = _brief(slug)
    t0 = time.time()
    r = harness._run_claude_p(
        ["claude", "-p", prompt, "--model", "claude-opus-5",
         "--allowedTools", "Bash,Read,Write", "--output-format", "json"],
        timeout=1500, retries=0, cwd=str(Path(__file__).parent),
    )
    el = time.time() - t0
    if r is None or r.returncode != 0:
        err = r.stderr[:300] if r is not None else "no result"
        print(f"shift {n}: FAILED after {el:.0f}s -- {err}")
        return None
    data = json.loads(r.stdout)
    cost = data.get("total_cost_usd")
    print(f"shift {n}: done in {el:.0f}s, cost ${cost}")
    return {"shift": n, "slug": slug, "seconds": el, "cost_usd": cost,
            "result_tail": data.get("result", "")[-1200:]}


def main():
    n_shifts = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out = []
    for i in range(1, n_shifts + 1):
        slug = f"opus{i}"
        res = run_shift(i, slug)
        if res:
            path = WORKSPACE / "scratch" / f"_{slug}.ans"
            if path.exists():
                m = harness._compute_piece_metrics(path)
                res["metrics"] = m
                res["gate"] = harness._flat_region_check(path) or "PASS"
                print("   ", harness._fmt_metrics(m))
                print("    gate:", str(res["gate"])[:90])
            else:
                res["metrics"] = None
                print("    NO FILE PRODUCED")
            out.append(res)
        Path("corpus/opus_artist_results.json").write_text(
            json.dumps(out, indent=2, default=str))
    total = sum(r.get("cost_usd") or 0 for r in out)
    print(f"\ntotal cost: ${total:.2f} across {len(out)} shifts")


if __name__ == "__main__":
    main()
