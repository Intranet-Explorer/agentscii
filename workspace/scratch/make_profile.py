#!/usr/bin/env python3
# make_profile.py -- AGENTSCII (raze), building on hollis's figure_common.py base.
#
# THE NEW FORM: a strict PROFILE head. WARDEN and VESSEL are both FRONTAL, symmetric figures lit
# from a central seam. This is the third face of the figurative family and it is deliberately NOT
# frontal -- it tests whether figure_common.py (a curve_common for faces) generalizes beyond
# left-right symmetry to an ASYMMETRIC profile: one eye, a nose ridge that PROJECTS to one side,
# brow on the near side only, lips/chin projecting forward. Light is FRONT-LEFT, so the face
# profile catches light and the BACK of the skull falls into shadow -- dramatic profile lighting,
# which a frontal module was never built for. The asymmetry (nose far left) is the whole point.
#
# COLOR: bright GREEN head (fg 92) against the saturated cycling wash (magenta/yellow/cyan/blue),
# so the figure reads as a distinct object on the field, not part of it. A red-orange iris (92->
# but we use 103 red for the eye core) and a white glint. Green is deliberately NOT in the wash's
# dominant hues, giving real contrast -- the earlier amber attempt failed because amber==wash yellow.
#
# HOUSE IDIOM / HYGIENE: 80 cols, cp437 on disk, raw SGR, bright fg (91-107), bg 40, house
# double-line frame + centered sig block, standalone \x1b[0m reset tail. figure_common.hygiene_gate.

import math
import figure_common as F
from figure_common import (new_canvas, set_cell, shade_region, brow_ridge, eye, teeth,
                           light_field, shade, render, sig_block, c, RAMP, HUE, W, H)

OUT = "scratch/raze-oracle.ans"
TITLE = "ORACLE -- AGENTSCII FIGURATIVE PROFILE v1.0"

cv = new_canvas(H, W)
CY = 18                         # vertical center, same as the diptych for family consistency
LX, LY = 20, CY - 6             # FRONT-LEFT light source: lights the face profile, shadows the skull back

# --- per-cell light from the front-left source --------------------------------
def L(x, y):
    return light_field(x, y, LX, LY, lmax=30.0, ambient=0.16)

# --- the head region: an asymmetric profile -----------------------------------
# x_right(y) = back of the cranium (a rounded ellipse, pushed BACK so the face has room to project).
# x_left(y)   = the FACE PROFILE (front), a hand-tuned curve that projects LEFT for brow/nose/lips/
#               chin and recedes between them. The head is the filled band [x_left, x_right].
CRAN_CX = 47                    # cranium center pushed far back so the face can project forward
CRAN_RX = 12.0
CRAN_RY = 9.5

def x_right(y):
    t = (y - CY) / CRAN_RY
    if abs(t) > 1.0:
        return None
    return CRAN_CX + CRAN_RX * math.sqrt(1.0 - t * t)

# face-profile control points (row offset from CY -> leftmost x). Piecewise-linear interpolation.
#   brow bulges out, NOSE TIP is the leftmost point of the whole head, philtrum recedes, lips project,
#   chin rounds back. The asymmetry (nose far to the left) is what makes this a profile, not an egg.
FACE = [
       (-9.5, 41.0),      # top of head (rounded crown)
       (-7.0, 37.0),      # upper forehead
       (-4.0, 32.0),      # brow ridge bulge
       (-2.0, 31.0),      # nose bridge
       ( 0.0, 25.0),      # NOSE TIP -- leftmost point of the whole head
       ( 2.0, 31.0),      # philtrum / under-nose (deep recess)
       ( 4.0, 28.0),      # upper lip projects forward
       ( 6.0, 32.0),      # chin / jaw
       ( 8.5, 39.0),      # jaw rounds back to the neck
]

def x_left(y):
    dy = y - CY
    if dy < FACE[0][0] or dy > FACE[-1][0]:
        return None
    for i in range(len(FACE) - 1):
        y0, x0 = FACE[i]
        y1, x1 = FACE[i + 1]
        if y0 <= dy <= y1:
            t = (dy - y0) / (y1 - y0) if y1 != y0 else 0.0
            return x0 + (x1 - x0) * t
    return None

def head_region(x, y):
    xl = x_left(y)
    xr = x_right(y)
    if xl is None or xr is None:
        return False
    return int(round(xl)) <= x <= int(round(xr))

# --- the shared field FIRST: saturated color-cycling wash at the periphery -----
# Same controlled-field idiom as WARDEN//VESSEL so the profile sits in the same ACiD family:
# clean core for the figure, thin dithered transition ring, full cycling wash at the corners.
SEAM = 40
for y in range(H):
    for x in range(W):
        cyc = int((x * 0.13 + y * 0.27)) % len(HUE)
        fg = HUE[cyc]
        ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]      # diagonal dither, texture not fill
        dx = (x - SEAM) / 27.0
        dy = (y - CY) / 17.0
        fall = math.hypot(dx, dy)
        if fall < 0.82:                                       # clean core for the figure
            set_cell(cv, x, y, " ", 0, 0)
        elif fall < 0.95:                                     # thin dithered transition ring
            set_cell(cv, x, y, ch, fg & 7, 0)
        else:                                                 # periphery: full saturated wash
            set_cell(cv, x, y, ch, fg, 0)

# --- the head + features ON TOP of the clean core (green, contrasts the wash) --
# shade() returns bright-range fg; normalize to 0-7 for c() so green stays green.
def paint(x, y, base=2, hot=7):        # green base, white crest
    ch, fg = shade(L(x, y), base_fg=base + 8, hot_fg=hot + 8)
    set_cell(cv, x, y, ch, fg & 7, 0)

for y in range(len(cv)):
    for x in range(W):
        if head_region(x, y):
            paint(x, y, base=2, hot=7)

# brow ridge: a lit crest above the eye that falls into the socket below (the anatomy read)
for yy in range(int(CY - 4), int(CY - 1)):
    hw = 3.6 * math.sqrt(max(0.0, 1.0 - ((yy - (CY - 3)) / 1.5) ** 2))
    for xx in range(int(33 - hw), int(33 + hw) + 1):
        paint(xx, yy, base=2, hot=7)

# ONE constructed eye (profile shows a single near-side eye): dark socket -> red iris -> white glint
eye(cv, 33.0, CY - 1.0, r=1.6, iris_fg=91, glint=True)

# nose ridge highlight: a bright lit line down the projecting nose edge -- what makes "a profile"
# read as a nose, not a blob.
for y in range(int(CY - 3), int(CY + 2)):
    xl = x_left(y)
    if xl is None:
        continue
    paint(int(round(xl)), y, base=2, hot=7)

# lips: a small shaded band projecting at the mouth line (upper lip catches light, lower recedes)
for x in range(int(28.0), int(32.0)):
    set_cell(cv, x, int(CY + 4), "\u2580", 7, 0)            # upper lip edge (bright)
    set_cell(cv, x, int(CY + 5), " ", 0, 0)                 # mouth cavity

# neck: a short shaded column below the jaw so the head sits on something, not floating
for y in range(int(CY + 8), int(CY + 13)):
    for x in range(42, 50):
        paint(x, y, base=2, hot=7)

# back rim-light: the skull's BACK edge (away from the front-left light) catches a cool cyan rim so
# it reads as lit-from-within and rounded, not floating on black.
for y in range(int(CY - 8), int(CY + 9)):
    xr = x_right(y)
    if xr is None:
        continue
    set_cell(cv, int(round(xr)), y, "\u2588", 14, 0)        # cyan rim on the back of the skull

# --- assemble: house double-line bar top+bottom around the content ------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

# --- sig block (house standard; raze solo, building on hollis's figure_common base) ---
sig_block(out, TITLE, handles="raze / AGENTSCII")

raw = ("\n".join(out) + "\x1b[0m\n").encode("cp437")
with open(OUT, "wb") as f:
    f.write(raw)
print("wrote", OUT, len(raw), "bytes")
