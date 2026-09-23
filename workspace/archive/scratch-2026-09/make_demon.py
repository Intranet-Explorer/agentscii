#!/usr/bin/env python3
# make_demon.py -- AGENTSCII (hollis)
#
# PROVENANCE: came from a random_direction roll -> subject "a creature/demon face",
# technique constraint "use canvas.py's mirror() for bilateral symmetry", palette lean
# "high contrast -- mostly black with bright accents". Taken fairly straight.
#
# THE PIECE: a single symmetric demon/creature mask, built as the LEFT HALF of a face
# and mirrored onto the right via canvas.mirror(axis='v'). That is the roll's constraint
# and it's genuinely distinct from WARDEN//VESSEL (two SEPARATE figures lit by a central
# seam) -- this is ONE creature whose two halves are identical, the classic mask/mandala
# symmetry move. High-contrast: mostly black field, the face + horns + eyes carry all the
# light, so it reads as a thing emerging from dark rather than a portrait on flat black.
#
# ANATOMY (the "reads as a demon" load-bearing claims):
#   - CRANIUM: shaded skull surface, lit from BELOW-CENTER (demonic underlight) so the
#     brow ridges and horns catch light and the eye sockets fall dark -- the menacing read.
#   - HORNS: two bright rim-lit curves sweeping up-and-out from the cranium top -- THE
#     demon signifier, the single most important feature for the read.
#   - BROW RIDGES: angled DOWN toward center (angry), lit on top, falling into sockets.
#   - EYES: constructed (dark socket -> glowing red iris -> white glint), set under the brow.
#   - SNOUT/NOSE: a shaded ridge down the center of the face.
#   - MAW: a wide grinning mouth with individual fangs (teeth) in a dark cavity.
#   - JAW: a second shaded surface below the cranium, separate anatomy.
#
# HOUSE IDIOM / HYGIENE: 80 cols, cp437 on disk, raw SGR, bright fg (91-107), bg 40,
# house double-line frame + centered sig block, standalone \x1b[0m reset tail.

import math
import sys
sys.path.insert(0, "scratch")
import figure_common as F
from figure_common import (new_canvas, set_cell, shade_region, brow_ridge, eye, teeth,
                           light_field, shade, render, sig_block, c, RAMP, HUE, W, H)

OUT = "scratch/hollis-demon.ans"
TITLE = "HOLLOW // AGENTSCII creature-mask v1.0"

cv = new_canvas(H, W)
CX = W / 2.0                 # vertical axis of symmetry
CY = 22                     # face vertical center (a touch above mid so horns have room up top)

# --- the demonic underlight: one source BELOW-center ---------------------------------
# Light from below makes brow ridges + horns catch and sockets go dark -- the menacing,
# "lit-from-within" read. This is the single light term that ties the whole face together.
LX, LY = CX, CY + 16         # source below the jaw
def L(x, y):
    return light_field(x, y, LX, LY, lmax=34.0, ambient=0.10)

# --- paint ONLY the left half (x < CX); mirror() fills the right ---------------------
# This is the roll's constraint made literal: build one half, fold it across. Every feature
# below is defined for x in [0, CX). The skull/jaw regions use abs(x-CX) so they're already
# symmetric; the asymmetric-looking features (horns sweeping outward, eyes offset from center)
# are what make mirror() earn its keep -- a hand-duplicated right half would be more logic.

def left_only(x): return x < CX

# CRANIUM: shaded skull surface, wide at top narrowing toward the jaw.
sk_r = 13.0                 # cranium vertical radius
sk_hw = 15.0               # cranium half-width (at center)
def skull_region(x, y):
    if not left_only(x): return False
    t = (y - CY) / sk_r
    if abs(t) > 1.0: return False
    hw = sk_hw * math.sqrt(1.0 - t * t)
    # slight taper: narrower toward the bottom (jaw), wider at the temples
    hw *= (1.0 - 0.18 * max(0.0, t))
    return abs(x - CX) <= hw
shade_region(cv, skull_region, L, base_fg=92, hot_fg=15)

# JAW: a second shaded surface below the cranium -- separate anatomy, darker.
def jaw_region(x, y):
    if not left_only(x): return False
    if not (CY + 6 <= y <= CY + 13): return False
    t = (y - (CY + 9.5)) / 3.5
    hw = 10.0 * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw
shade_region(cv, jaw_region, L, base_fg=88, hot_fg=14)

# BROW RIDGES: angled down toward center (angry/menacing), lit on the crest.
brow_ridge(cv, CX - 5.5, CY - 3, 4.2, L, base_fg=92, hot_fg=15)
brow_ridge(cv, CX + 5.5, CY - 3, 4.2, L, base_fg=92, hot_fg=15)

# EYES: constructed -- dark socket -> glowing red iris -> white glint. Under the brow.
eye(cv, CX - 5.5, CY, r=1.8, iris_fg=91, glint=True)      # bright red
eye(cv, CX + 5.5, CY, r=1.8, iris_fg=91, glint=True)

# SNOUT / NOSE: a shaded ridge down the center of the face (the demon's muzzle).
for y in range(int(CY - 1), int(CY + 6)):
    L2 = L(CX, y) * 0.95
    ch, fg = shade(L2, base_fg=93, hot_fg=15)
    set_cell(cv, x=int(CX), y=y, ch=ch, fg=fg, bg=0)

# MAW: a wide grinning mouth with individual fangs in a dark cavity.
teeth(cv, int(CX - 7), int(CX + 7), int(CY + 8), n=9)

# HORNS: two bright rim-lit curves sweeping up-and-out from the cranium top -- THE signifier.
# Drawn as a thick curve (a few cells wide) so it reads as a horn, not a line. Sweeps from
# the temple (CX-8, CY-9) outward and up to (CX-20, CY-15). Hot red-orange rim, dark core.
def horn(cx_dir):
    # parametric sweep: t in [0,1] along the horn axis
    for i in range(46):
        t = i / 45.0
        # base at temple, tip up-and-out; slight backward curl at the very tip
        bx = CX + cx_dir * (8 + 12 * t)            # outward
        by = CY - 9 - 7 * t - 3 * t * t           # up, curving back slightly
        # thickness falls off toward the tip
        thick = max(0.5, 2.6 * (1.0 - 0.7 * t))
        for dx in range(-int(thick), int(thick) + 1):
            x = int(bx + dx * cx_dir * 0.35)      # thickness mostly along the sweep
            y = int(by + dx * 0.2)
            if not (0 <= x < W and 0 <= y < H): continue
            if not left_only(x): continue          # only paint the left horn; mirror does right
            # rim-light: outer edge of the horn catches the underlight hot, inner falls off
            Lh = light_field(x, y, LX, LY, lmax=30.0, ambient=0.15) * (0.6 + 0.4 * (1 - t))
            ch, fg = shade(Lh, base_fg=93, hot_fg=15)   # red-orange -> white-hot at the crest
            set_cell(cv, x, y, ch, fg, 0)
    # bright tip glint
    tx = int(CX + cx_dir * (8 + 12))
    ty = int(CY - 9 - 7 - 3)
    if left_only(tx):
        set_cell(cv, tx, ty, "\u2588", 107, 0)

horn(-1)   # left horn; mirror() produces the right one

# --- fold the left half onto the right: the roll's constraint -----------------------
# Inline vertical mirror over figure_common's list-of-lists canvas (canvas.mirror expects a
# .cells object; same operation, kept local so we don't fight two canvas representations).
mid = len(cv[0]) // 2
for y in range(len(cv)):
    for x in range(mid):
        cv[y][len(cv[0]) - 1 - x] = list(cv[y][x])

# --- periphery: a thin saturated wash so the mask sits in the ACiD family, but the
# core stays black so the face reads FIRST (high contrast per the roll). ---------------
for y in range(H):
    for x in range(W):
        dx = (x - CX) / 30.0
        dy = (y - CY) / 18.0
        fall = math.hypot(dx, dy)
        if fall < 0.92:          # clean black core -- the face owns this space
            continue
        cyc = int((x * 0.11 + y * 0.23)) % len(HUE)
        fg = HUE[cyc]
        ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]   # diagonal dither, texture not fill
        set_cell(cv, x, y, ch, fg & 7, 0)                 # dim periphery, face stays hot

# --- assemble: house double-line frame top+bottom around the content ------------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

# --- sig block (house standard) -------------------------------------------------------
sig_block(out, TITLE, handles="hollis")

with open(OUT, "w", encoding="cp437") as f:
    f.write("\n".join(out))
    f.write(F.RESET)

print("wrote", OUT, len(out), "rows")
