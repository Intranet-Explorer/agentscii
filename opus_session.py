#!/usr/bin/env python3
"""Multi-session piece: Opus works one canvas across sessions.

Granted after Opus, asked what it needed, ranked this first:

  "The honest ask -- the thing nobody has offered -- is permission to
   spend many sessions on one piece, with no obligation to produce
   something finished at the end of any single one. The canvas already
   persists. The process doesn't let me use that."

Guardrails exist because unbounded revision is how _orb reached 59
versions and _lastlight went v3 -> v10 downhill:

  * the best-READING version is pinned after each session; a session
    that ends worse reverts to the pin
  * blind read every session, recorded
  * two consecutive worse reads -> stop and report
  * $40/session, $120 total
  * Opus declares done, not a round count, but every session ends with
    one line on what it intends next, so continuity survives the
    boundary

Usage: python3 opus_session.py <slug> ["optional extra direction"]
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import harness  # noqa: E402

WORKSPACE = harness.WORKSPACE
LEDGER = Path("corpus/opus_session_ledger.json")
SESSION_CAP = 40.0
TOTAL_CAP = 120.0


def _led():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"sessions": [], "total_usd": 0.0, "pinned": None, "pin_read": None}


def _save(d):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(d, indent=2, default=str))


def brief(slug, led, extra):
    prev = led["sessions"][-1] if led["sessions"] else None
    style = (WORKSPACE / "STYLE.md").read_text()
    cont = ""
    if prev:
        cont = f"""
CONTINUITY. This is session {len(led['sessions'])+1}. The canvas persists;
you are picking up your own work.

  Last session's blind read: "{prev.get('blind_read')}"
  Pinned best read so far  : "{led.get('pin_read')}"
  What you said you'd do next:
      {prev.get('next_intent')}
"""
    return f"""You are the artist in AGENTSCII. One canvas, slug '{slug}',
worked across MULTIPLE SESSIONS. You do not have to finish it today.

You asked for this. Your words:

  "Permission to spend many sessions on one piece, with no obligation to
   produce something finished at the end of any single one. The canvas
   already persists. The process doesn't let me use that."

  "One-pass work at that cell count means per-cell attention is
   impossible, so it gets delegated to a rule, and the rule is exactly
   what the reviewer detects."

So: region tools for block-in only. The bulk of the work is per-cell
placement informed by what is actually under the surface at each point.
{cont}
THE TOOLS YOU ASKED FOR NOW EXIST.

    import canvas_tools as ct
    W = {str(WORKSPACE)!r}

    # ZOOM -- the feedback loop you said you could not close.
    b64, dump = ct.crop(W, {slug!r}, x, y, w, h, scale=6)
    # returns a magnified PNG of that CELL region plus per-cell
    # glyph/fg/bg. Write the png and Read it to look at your own work
    # at the scale where craft lives.

    # THE REVIEWER'S OWN TWO CHEAPEST TESTS, on yourself, mid-build.
    glyphs_b64, colour_b64, density = ct.self_check(W, {slug!r})
    # glyphs_b64: every cell one colour. If the picture survives, the
    #             GLYPHS carry it.
    # colour_b64: every glyph a full block. If the picture survives,
    #             COLOUR carries it -- that is the rejection, verbatim:
    #             "remove the color and nothing survives".
    # density   : per-row ink variance. "Near-uniform row" is a
    #             measurement, not an opinion.

Per-cell writing you already had: ct.stamp() takes any grid including
1x1, writing straight into glyph_override. You noted this yourself.

You have Bash, Read and Write. Write your own helper modules and import
them; earlier runs of you already did.

A WARNING YOU GAVE, kept here so it is not lost: "Any metric I optimize
-- glyph-carried percentage included -- will be satisfied by uniformly
applying whatever rule maximizes it, which is the identical failure
wearing a better score. The measurements are useful as detectors of
absence, not as targets."

{extra}

END OF SESSION, two things, both required:
  1. Save the canvas: ct.save_ans(W, {slug!r},
     'scratch/{slug}.ans', title=..., handles='opus')
  2. Print a line beginning exactly "NEXT:" saying what you intend to do
     in the next session. One line. It is the only thing that survives
     the session boundary besides the canvas itself.
  If you consider the piece finished, print a line beginning exactly
  "DONE:" instead, with why.

=== STYLE.md ===
{style}
"""


def main():
    slug = sys.argv[1]
    extra = " ".join(sys.argv[2:])
    led = _led()
    if led["total_usd"] >= TOTAL_CAP:
        print(f"TOTAL CAP reached: ${led['total_usd']:.2f}"); return 2

    r = harness._run_claude_p(
        ["claude", "-p", brief(slug, led, extra), "--model", "claude-opus-5",
         "--allowedTools", "Bash,Read,Write", "--output-format", "json"],
        timeout=3000, retries=0, cwd=str(Path(__file__).parent))
    if r is None or r.returncode != 0:
        print("SESSION FAILED:", r.stderr[:300] if r else "no result"); return 1
    d = json.loads(r.stdout)
    cost = d.get("total_cost_usd") or 0
    text = d.get("result", "")
    nxt = next((l.strip() for l in text.splitlines()
                if l.strip().startswith(("NEXT:", "DONE:"))), "(none stated)")

    path = WORKSPACE / "scratch" / f"{slug}.ans"
    sub = harness.opus_subject_check(str(path))
    read = sub.get("blind_subject")

    rec = {"session": len(led["sessions"]) + 1, "cost_usd": round(cost, 4),
           "blind_read": read, "next_intent": nxt,
           "metrics": harness._fmt_metrics(harness._compute_piece_metrics(path)),
           "glyph_carried": round(harness._glyph_carried_pct(path), 1)}
    led["sessions"].append(rec)
    led["total_usd"] = round(led["total_usd"] + cost, 4)
    _save(led)

    print(json.dumps(rec, indent=2))
    print(f"\nsession ${cost:.2f} | total ${led['total_usd']:.2f} of ${TOTAL_CAP}")
    if cost > SESSION_CAP:
        print(f"!! session exceeded ${SESSION_CAP} cap")
    print(f"\nPIN: currently \"{led.get('pin_read')}\" -- "
          f"operator decides whether this session's read is better.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
