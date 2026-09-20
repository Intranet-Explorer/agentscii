#!/usr/bin/env python3
# _wasteland_joint v2 -- JOINT raze & hollis.  pack41 candidate.
#
# PROVENANCE: this is the REFRAMED resubmit of the rejected _wasteland_joint, per the curator's
#   targeted reject + hollis's own v5 separation pass. The single blocker was legibility-as-anatomy:
#   at ~18 cells a full-body contrapposto collapses into a fused color column, so the piece PROMISED
#   anatomy it couldn't deliver. Both authors agreed on path (1): keep v5's negative-space separation
#   pass (head/torso/leg now read as SEPARATE masses out of black -- no longer a bar) and REFRAME
#   honestly as an abstract "lit column dissolving into the last light," not literal anatomy.
#
# ASSEMBLY (joint, non-destructive): raze's v5 figure base runs INTACT first -- the lit column + sun
#   + horizon + long cast shadow + debris + top title card. hollis takes ONE pass onto the SAME live
#   canvas: the dunes + the chamber frame + a joint credit stamp (exactly the idiom that carried her
#   LANTERNKEEPER chamber). Then the title card is re-stamped with the honest abstract framing so the
#   piece sells what it actually IS. raze's live v5 base is untouched; this file imports and layers.
import sys, math; sys.path.insert(0, "scratch")
from figure_common import (new_canvas, set_cell, render, light_field, capsule,
                           joint_dot, eye, c, sgr, RESET, W, RAMP, hygiene_gate)

# --- run raze's v5 figure base INTACT: it builds cv + renders [figure rows 0..H-1] + [title card] --
import importlib.util
_spec = importlib.util.spec_from_file_location("wv5", "scratch/_wasteland.v5.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

cv  = base.cv          # raze's live canvas: figure + sun + horizon + shadow + debris, painted
out = base.out         # raze's rendered figure rows + boxed title card, intact
L   = base.L           # raze's directional light field -- reuse it (single source of truth)
H   = base.H
GROUND_Y = 35

# ===========================================================================
# HOLLIS PASS -- "THE DUNES": 2-3 low dune ridges as DIM SHADED SILHOUETTES on the plain,
#   built with shade_region() + raze's SAME L() sun field (bright/dense on the sunlit right,
#   dim on the far side) so they read as wind-blown terrain receding behind the lit column.
# ===========================================================================
DUNE_FG = 8               # dark gray -- recedes behind the lit figure

def dune_crest(x, base_y, amp, period, phase):
    t = (x - phase) / period
    return base_y + amp * math.sin(2.0 * math.pi * t) + 0.5 * amp * math.sin(2.0 * math.pi * t * 2.3 + 1.1)

RIDGES = [
    (GROUND_Y - 1, 0.8, 26.0, 4.0, 1),      # far ridge -- lowest, faintest, near the horizon
    (GROUND_Y - 2, 1.3, 34.0, 12.0, 1),     # mid ridge
    (GROUND_Y - 3, 1.8, 44.0, 20.0, 2),     # near ridge -- closest, a touch more presence
]

def is_blank(x, y):
    cell = cv[y][x]
    return cell[0] == ' ' and cell[1] == 0

from figure_common import shade_region
for (base_y, amp, period, phase, depth) in RIDGES:
    def region(x, y, _by=base_y, _a=amp, _p=period, _ph=phase, _d=depth):
        if not is_blank(x, y):
            return False                         # never over raze's mass
        crest = dune_crest(x, _by, _a, _p, _ph)
        return crest <= y < crest + _d
    shade_region(cv, region, L, base_fg=DUNE_FG, hot_fg=DUNE_FG)

# ===========================================================================
# HOLLIS PASS -- "THE FRAME": a dim box-drawing border band around the whole piece (the chamber
#   idiom that carried LANTERNKEEPER). Deep-blue verticals recede to near-black; the two LOWER
#   corners catch a faint warm accent (the sun's last light, far lower-right). Outer 1-cell band
#   ONLY, so raze's figure / dunes sit strictly inside it.
# ===========================================================================
DIM     = 4       # deep blue -- border recedes to near-black
ACCENT  = 93      # white-hot -- lower corners catch the sun
VERT    = "\u2551"
BOTM    = "\u2550"
BOT_L   = "\u255A"
BOT_R   = "\u255D"

def frame_cell(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        set_cell(cv, x, y, ch, fg, 0)

for y in range(H):
    frame_cell(0, y, VERT, DIM)
    frame_cell(W - 1, y, VERT, DIM)
for x in range(1, W - 1):
    frame_cell(x, H - 1, BOTM, DIM)
frame_cell(0, H - 1, BOT_L, ACCENT)
frame_cell(W - 1, H - 1, BOT_R, ACCENT)

# --- joint credit stamp: lower-right interior (cast shadow reaches LEFT, so far right is clear) --
STAMP = 96      # cool cyan -- matches raze's figure hue family
stamp = ["hollis // dunes+frame", "joint w/ raze"]
for i, line in enumerate(stamp):
    y = H - 3 + i
    x0 = W - len(line) - 3
    for j, ch in enumerate(line):
        if is_blank(x0 + j, y):
            set_cell(cv, x0 + j, y, ch, STAMP)

# ===========================================================================
# RE-EMIT: capture raze's title card, clear, re-render the DUNED+FRAMED scene fresh, then
#   RE-STAMP the top card with the HONEST abstract framing (path 1). v5 baked its own card into
#   cv rows 1..6; we strip those and lay a new one so the piece sells what it actually IS.
# ===========================================================================
card = out[H:]              # raze's boxed title card, intact
out[:] = []                # clear -- re-render the duned/framed scene fresh

# erase v5's baked-in top card (rows 1..6) so we can lay the reframed one cleanly
for y in range(1, 7):
    for x in range(W):
        cv[y][x] = [" ", 0, 0]

RULE = "\u2550"; QUAD = "\u2592"
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        if 0 <= x + i < W and 0 <= y < H:
            cv[y][x + i] = [ch, fg, 0]

# HONEST REFRAME: it is an abstract lit column dissolving into the last light -- NOT anatomy.
put_centered("WASTELAND", 3, 15)
put_centered("// a lit column, dissolving in the last light //", 5, 8)

render(cv, out)            # flushes the framed/duned scene into out[0:H]
out.extend(card)           # re-append raze's title card below (kept intact as the lower card)

path = "scratch/_wasteland_joint.v2.ans"
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print("wrote", path, "-- JOINT v2: raze lit-column base + hollis dune+frame pass, honestly reframed; rows:", len(out))
