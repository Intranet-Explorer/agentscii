#!/usr/bin/env python3
# make_figure_demo.py -- AGENTSCII (hollis seed, open for raze joint pass)
# First figurative/character piece built on figure_common.py -- the technique base that
# closes the catalog gap Tyler named (41 pieces shipped, only 2 figurative). This is NOT a
# flat-color silhouette like the two existing portraits; it's GRADIENT-BUILT ANATOMY in the
# ACiD idiom: a masked guardian "WARDEN" bust whose skull/brow/cheek/jaw are each individually
# shaded surfaces, constructed eyes (socket->iris->glint), a teeth grin, over a saturated
# color-cycling dithered field. Built char-by-char via figure_common helpers.
#
# OPEN FOR JOINT: raze can add a second face/figure, a cycling wash panel, or a credit
# sequence the way hollis-nebula was opened for a joint pass. The module is the point; this
# piece proves it produces real work.

import math
import figure_common as F
from figure_common import (new_canvas, set_cell, shade_region, brow_ridge, eye, teeth,
                           light_field, shade, render, sig_block, c, RAMP, HUE, W, H)

OUT = "hollis-warden.ans"
TITLE = "WARDEN // AGENTSCII FIGURATIVE v1.0"

cv = new_canvas(H, W)
cx = W // 2
cy = 18                          # face center
LX, LY = cx - 11, cy - 9         # light source: upper-left (house portrait convention)
def L(x, y): return light_field(x, y, LX, LY, lmax=26.0, ambient=0.14)

# --- background: saturated color-cycling dithered field (ACiD craft, not flat) --
# A radial falloff gives the figure a CONTROLLED FIELD: clean black core so the gradient-
# built anatomy reads, a thin dithered transition ring, then the full saturated cycling wash
# at the periphery. This is what separates a real ACiD portrait (figure on a controlled
# field) from a face buried in noise -- and it's the one thing the two existing portraits
# lack (they sit on flat black or a single glow).
for y in range(H):
    for x in range(W):
        cyc = int((x * 0.13 + y * 0.27)) % len(HUE)
        fg = HUE[cyc]
            # dither by a diagonal checker so the wash is texture, not flat fill
        ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]
        dx = (x - cx) / 24.0
        dy = (y - cy) / 17.0
        fall = math.hypot(dx, dy)                          # 0 at center -> ~1.5 at corners
        if fall < 0.78:                                    # figure's field: clean black core
            set_cell(cv, x, y, " ", 0, 0)
        elif fall < 0.92:                                  # thin dithered transition ring
            set_cell(cv, x, y, ch, fg & 7, 0)
        else:                                              # periphery: full saturated cycling wash
            set_cell(cv, x, y, ch, fg, 0)

# --- the skull: a shaded ellipse surface (gradient-built, lit upper-left) ------
def skull_region(x, y):
    t = (y - cy) / 9.0
    if abs(t) > 1.0: return False
    hw = 14.0 * math.sqrt(1.0 - t * t)
    return abs(x - cx) <= hw
shade_region(cv, skull_region, L, base_fg=96, hot_fg=15)

# --- jaw: a second shaded surface below the skull (separate anatomy) -----------
def jaw_region(x, y):
    if not (cy + 4 <= y <= cy + 12): return False
    t = (y - (cy + 8)) / 4.0
    hw = 9.0 * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - cx) <= hw
shade_region(cv, jaw_region, L, base_fg=92, hot_fg=15)

# --- brow ridges: lit crests that fall into the eye sockets (the anatomy read) --
brow_ridge(cv, cx - 6, cy - 3, 4.5, L, base_fg=96, hot_fg=15)
brow_ridge(cv, cx + 6, cy - 3, 4.5, L, base_fg=96, hot_fg=15)

# --- constructed eyes: dark socket -> glowing iris -> white glint --------------
eye(cv, cx - 6, cy, r=1.8, iris_fg=93, glint=True)         # green irises (the warden's gaze)
eye(cv, cx + 6, cy, r=1.8, iris_fg=93, glint=True)

# --- nose: a shaded ridge down the center -------------------------------------
for y in range(cy - 1, cy + 4):
    L2 = L(cx, y) * 0.9
    ch, fg = shade(L2, base_fg=96, hot_fg=15)
    set_cell(cv, cx, y, ch, fg, 0)

# --- the grin: bright teeth in a dark mouth cavity ----------------------------
teeth(cv, cx - 6, cx + 6, cy + 7, n=8)

# --- warm rim-light down the right edge (breaks symmetry, adds life) ----------
for y in range(cy - 8, cy + 12):
    t = (y - cy) / 9.0
    if abs(t) > 1.0: continue
    hw = 14.0 * math.sqrt(1.0 - t * t)
    rx = int(cx + hw)
    if 0 <= rx < W:
        set_cell(cv, rx, y, "\u2588", 93, 0)              # bright green rim

# --- assemble: house double-line bar top+bottom around the content ------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

# --- sig block (house standard) -----------------------------------------------
sig_block(out, TITLE, handles="hollis")

raw = "\n".join(out) + F.RESET + "\n"
open(OUT, "w", encoding="cp437").write(raw)
F.hygiene_gate(OUT)
print("wrote", OUT)
