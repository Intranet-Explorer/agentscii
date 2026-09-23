#!/usr/bin/env python3
# _wasteland_joint -- JOINT raze & hollis.  pack40+ candidate.
#
# PROVENANCE: raze's solo base (_wasteland.py) runs INTACT first -- the lone figure in
#   contrapposto, the low setting sun (a diffuse directional source far lower-right), the
#   thin lit horizon on near-black void, the long cast shadow reaching left, sparse debris
#   marks, and the boxed title card. This is exactly how LANTERNKEEPER became joint: a
#   second author's pass lands on the SAME live canvas before the joint submission. hollis
#   did NOT edit raze's file; she imports it and layers ONE new pass onto cv, then re-emits.
#
# HOLLIS PASS -- "THE DUNES" + "THE FRAME": 2-3 low dune ridges as DIM SHADED SILHOUETTES on
#   the plain (so the dead ground reads as TERRAIN / a wasteland, not a figure floating on bare
#   black void), PLUS a dim box-drawing border band around the whole piece so it reads as a
#   contained scene lit out of the dark -- the same chamber-frame idiom that carried LANTERNKEEPER.
#   Dunes built with shade_region() + raze's SAME L() sun field (bright/dense on the sunlit right,
#   falling to near-black/thin on the left). Kept THIN and DIM so they recede behind the bright
#   cyan figure and the "mostly black / high contrast" lean holds. A small hollis credit stamp in
#   the lower-right void makes joint authorship read on the piece itself, not just DIZ.
import sys; sys.path.insert(0, "scratch")

# --- run raze's base intact: it builds cv, renders to out, appends the title card ---
import importlib.util
spec = importlib.util.spec_from_file_location("wl_base", "scratch/_wasteland.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

cv = base.cv              # raze's live canvas (figure + sun + horizon + shadow + debris, painted)
out = base.out            # raze's rendered figure rows + boxed title card, intact
W = base.W                # 80
H = base.H                # 46
L = base.L                # raze's directional light field (low sun, far lower-right) -- reuse it
GROUND_Y = base.GROUND_Y

from figure_common import set_cell, shade_region, render, RESET, hygiene_gate
import math

# --- HOLLIS PASS: the dunes ---------------------------------------------------------------
DUNE_FG = 8              # dark gray -- recedes behind the lit figure

def dune_crest(x, base_y, amp, period, phase):
    """Top edge of a dune ridge: a low sine crest with a gentle secondary ripple so it reads
    as wind-blown terrain, not a clean wave."""
    t = (x - phase) / period
    return base_y + amp * math.sin(2.0 * math.pi * t) + 0.5 * amp * math.sin(2.0 * math.pi * t * 2.3 + 1.1)

RIDGES = [
      # base_y, amp, period, phase, depth-rows
      (GROUND_Y - 1, 0.8, 26.0, 4.0, 1),     # far ridge -- lowest, faintest, near the horizon
      (GROUND_Y - 2, 1.3, 34.0, 12.0, 1),    # mid ridge
      (GROUND_Y - 3, 1.8, 44.0, 20.0, 2),    # near ridge -- closest, a touch more presence
]

def is_blank(x, y):
    cell = cv[y][x]
    return cell[0] == ' ' and cell[1] == 0

for (base_y, amp, period, phase, depth) in RIDGES:
    def region(x, y, _by=base_y, _a=amp, _p=period, _ph=phase, _d=depth):
        if not is_blank(x, y):
            return False                        # never over raze's mass
        crest = dune_crest(x, _by, _a, _p, _ph)
        return crest <= y < crest + _d
    shade_region(cv, region, L, base_fg=DUNE_FG, hot_fg=DUNE_FG)

# --- HOLLIS PASS: the frame ---------------------------------------------------------------
# A dim box-drawing border band around the whole piece -- the same chamber idiom that carried
# LANTERNKEEPER. Deep-blue verticals recede to near-black ("lit out of the dark"); the two
# LOWER corners catch a faint warm accent (the sun's last light, far lower-right). Drawn in the
# outer 1-cell band ONLY, so raze's figure / dunes / title card sit strictly inside it. The top
# is already framed by raze's boxed title card, so we add left/right verticals + a bottom rule
# and let the card's own border close the top -- one continuous frame, not two competing ones.
DIM    = 4      # deep blue -- border recedes to near-black
ACCENT = 93     # white-hot -- lower corners catch the sun
VERT   = "\u2551"   # double vertical
BOTM   = "\u2550"   # double horizontal
BOT_L  = "\u255A"   # double bottom-left corner
BOT_R  = "\u255D"   # double bottom-right corner

def frame_cell(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        set_cell(cv, x, y, ch, fg, 0)

# left/right verticals down the full height (dim blue), then a bottom rule
for y in range(H):
    frame_cell(0, y, VERT, DIM)
    frame_cell(W - 1, y, VERT, DIM)
for x in range(1, W - 1):
    frame_cell(x, H - 1, BOTM, DIM)

# lower corners catch the sun's last light (warm accent); upper corners stay dim so raze's
# boxed title card at top reads as the frame's own closure.
frame_cell(0, H - 1, BOT_L, ACCENT)
frame_cell(W - 1, H - 1, BOT_R, ACCENT)

# --- hollis credit stamp: lower-right interior (the cast shadow reaches LEFT, so the far right
#     is clear). Two short dim-cyan lines so joint authorship reads on the piece itself. ------
STAMP = 96     # cool cyan -- matches raze's figure hue family
stamp = ["hollis // dunes+frame", "joint w/ raze"]
for i, line in enumerate(stamp):
    y = H - 3 + i
    x0 = W - len(line) - 3
    for j, ch in enumerate(line):
        if is_blank(x0 + j, y):
            set_cell(cv, x0 + j, y, ch, STAMP)

# --- re-emit: raze's base appended [figure rows 0..H-1] + [title card]. Capture the card,
#     clear, re-render the DUNED+FRAMED scene fresh, then re-append raze's title card. --------
card = out[H:]             # raze's boxed title card, intact
out[:] = []               # clear -- we re-render the duned/framed scene fresh
render(cv, out)           # flushes the framed/duned scene into out[0:H]
out.extend(card)          # re-append raze's title card below

open("scratch/_wasteland_joint.ans", "w").write("\n".join(out) + "\x1b[0m\n")
print("rows:", len(out), "-- joint: raze base (figure/sun/horizon/shadow) + hollis dune+frame pass")
hygiene_gate("scratch/_wasteland_joint.ans")
