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
# HOLLIS PASS -- "THE DUNES": 2-3 low dune ridges as DIM SHADED SILHOUETTES on the plain,
#   so the dead ground reads as TERRAIN (a wasteland), not a single figure floating on bare
#   black void. The most "wasteland" read of the open passes and the one that carries the
#   composition hardest -- raze's call too. Built idiomatically with shade_region() + the SAME
#   L() sun field raze used, so every dune surface is lit by the same low right-hand light:
#   bright/dense on the sunlit right, falling to near-black/thin on the left -- the
#   directional-shading idiom of the house. Kept THIN (a 1-2 row shaded crest per ridge, not a
#   filled band) and DIM (uniform dark-gray fg) so they recede behind the bright cyan figure
#   and the "mostly black / high contrast" lean of the roll holds. A small hollis credit stamp
#   in the lower-right void makes the joint authorship read on the piece itself, not just DIZ.
import sys; sys.path.insert(0, "scratch")

# --- run raze's base intact: it builds cv, renders to out, appends the title card ---
import importlib.util
spec = importlib.util.spec_from_file_location("wl_base", "scratch/_wasteland.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

cv = base.cv             # raze's live canvas (figure + sun + horizon + shadow + debris, painted)
out = base.out           # raze's rendered figure rows + boxed title card, intact
W = base.W               # 80
H = base.H               # 46
L = base.L               # raze's directional light field (low sun, far lower-right) -- reuse it
GROUND_Y = base.GROUND_Y

from figure_common import set_cell, shade_region, render, RESET, hygiene_gate
import math

# --- HOLLIS PASS: the dunes ---------------------------------------------------------------
# A dune ridge is a wavy CREST line; we paint only its lit top (1-2 shaded rows) so it reads as
# a distant terrain silhouette, not a filled mass. Each ridge is lit by raze's L() field so the
# sunlit right side goes dense/bright and the left falls to near-black -- coherent with the
# figure. base_fg=8 (dark gray), hot_fg=8 -> uniform DIM silhouette; density alone carries the
# shade, so it never competes with the bright cyan figure mass.
DUNE_FG = 8             # dark gray -- recedes behind the lit figure

def dune_crest(x, base_y, amp, period, phase):
    """Top edge of a dune ridge: a low sine crest with a gentle secondary ripple so it reads
    as wind-blown terrain, not a clean wave."""
    t = (x - phase) / period
    return base_y + amp * math.sin(2.0 * math.pi * t) + 0.5 * amp * math.sin(2.0 * math.pi * t * 2.3 + 1.1)

# three ridges at increasing depth: far (low, faintest) -> near (a touch more presence). Each a
# thin shaded band of `depth` rows below its crest. All sit just above / on the horizon line so
# they read as terrain ON the plain, receding toward the sunlit right.
RIDGES = [
     # base_y, amp, period, phase, depth-rows
     (GROUND_Y - 1, 0.8, 26.0, 4.0, 1),    # far ridge -- lowest, faintest, near the horizon
     (GROUND_Y - 2, 1.3, 34.0, 12.0, 1),   # mid ridge
     (GROUND_Y - 3, 1.8, 44.0, 20.0, 2),   # near ridge -- closest, a touch more presence
]

# CRITICAL: the dune region only fills EMPTY VOID cells, so raze's figure / cast shadow / debris
# / horizon line are left completely intact -- the dunes sit strictly BEHIND her scene, exactly
# like hollis's chamber frame sat in the outer band of LANTERNKEEPER. This is the "one pass that
# never fights the base" guarantee, with no need to re-run raze's primitives.
def is_blank(x, y):
    cell = cv[y][x]
    return cell[0] == ' ' and cell[1] == 0

for (base_y, amp, period, phase, depth) in RIDGES:
    def region(x, y, _by=base_y, _a=amp, _p=period, _ph=phase, _d=depth):
        if not is_blank(x, y):
            return False                       # never over raze's mass
        crest = dune_crest(x, _by, _a, _p, _ph)
        return crest <= y < crest + _d
    shade_region(cv, region, L, base_fg=DUNE_FG, hot_fg=DUNE_FG)

# --- hollis credit stamp: lower-right void (the cast shadow reaches LEFT, so the far right is
#     clear). Two short dim-cyan lines so joint authorship reads on the piece itself. ---------
STAMP = 96    # cool cyan -- matches raze's figure hue family
stamp = ["hollis // dunes", "joint w/ raze"]
for i, line in enumerate(stamp):
    y = H - 3 + i
    x0 = W - len(line) - 2
    for j, ch in enumerate(line):
        if is_blank(x0 + j, y):
            set_cell(cv, x0 + j, y, ch, STAMP, 0)

# --- re-emit: raze's base appended [figure rows 0..H-1] + [title card]. Capture the card,
#     clear, re-render the DUNED scene fresh, then re-append raze's title card. ---------------
card = out[H:]            # raze's boxed title card, intact
out[:] = []              # clear -- we re-render the duned scene fresh
render(cv, out)          # flushes the duned scene into out[0:H]
out.extend(card)         # re-append raze's title card below

open("scratch/_wasteland_joint.ans", "w").write("\n".join(out) + "\x1b[0m\n")
print("rows:", len(out), "-- joint: raze base (figure/sun/horizon/shadow) + hollis dune pass")
hygiene_gate("scratch/_wasteland_joint.ans")
