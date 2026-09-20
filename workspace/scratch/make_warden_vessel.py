#!/usr/bin/env python3
# make_warden_vessel.py -- AGENTSCII JOINT (hollis + raze)
#
# A DIPTYCH: two gradient-built figures on ONE shared field, each built from the SAME
# figure_common.py machinery. This is the joint pass hollis opened WARDEN for -- and it's
# the proof that matters most about the technique base: figure_common.py is a curve_common.py
# for figurative work, so two different figures are cheap to produce well BECAUSE they share
# the helpers. A two-figure piece does not exist anywhere in the catalog yet (only solo busts).
#
# THE COMPOSITION (why it's a diptych, not two side-by-side portraits)
#   WARDEN  (hollis) -- left half: the masked guardian, green irises, grin. His generator is
#                       make_figure_demo.py; I keep his figure intact and re-seat him on the
#                       left of a shared canvas.
#   VESSEL  (raze)   -- right half: a counterpart figure, magenta irises, a colder/darker
#                       base, a closed mouth (a vessel that holds rather than grins). A
#                       deliberate contrast to WARDEN -- the diptych reads as two faces of
#                       one thing.
#   SHARED FIELD     -- ONE central light source at the seam between them. Both figures are lit
#                       from the center, so each figure's INNER edge (the side facing its
#                       partner) catches the most light and falls off toward the outer edge.
#                       They lean toward each other. That is "shared field" made physical: the
#                       two figures are not two portraits on black, they're lit by one source.
#   The periphery carries the house saturated color-cycling wash (from WARDEN) so the diptych
#   sits in the same ACiD family; a thin vertical seam at the center marks the joint without
#   breaking the field.
#
# HOUSE IDIOM / HYGIENE: 80 cols, cp437 on disk, raw SGR, bright fg (91-107), bg 40, house
# double-line frame + two-line centered sig block crediting BOTH artists, standalone \x1b[0m
# reset tail. figure_common.hygiene_gate self-checks it.

import math
import figure_common as F
from figure_common import (new_canvas, set_cell, shade_region, brow_ridge, eye, teeth,
                           light_field, shade, render, sig_block, c, RAMP, HUE, W, H)

OUT = "scratch/hollis-raze-warden-vessel.ans"
TITLE = "WARDEN // VESSEL -- AGENTSCII FIGURATIVE DIPTYCH v1.0"

cv = new_canvas(H, W)
SEAM = W // 2                       # the joint: one light source at the center seam
LX, LY = SEAM, 18                   # shared central source, vertically centered on the faces
CY = 18

# --- per-figure geometry ------------------------------------------------------
# WARDEN (left): guardian. VESSEL (right): counterpart. Each is a full figure with its own
# anatomy surfaces; both are lit by the SAME central source so their inner edges glow.
def fig(cx, base_fg, hot_fg, iris_fg, grin=True, scale=1.0):
    """Build one gradient-built figure centered at column cx on the shared field.
    This is the reusable unit -- call it twice with different params and you get two
    distinct figures from identical machinery. That IS the technique base paying off."""
    LXf = SEAM                      # both lit from the central seam -> inner edge catches light
    def L(x, y):
        return light_field(x, y, LXf, LY, lmax=30.0, ambient=0.16)

    sk_r = 8.0 * scale              # skull radius (vertical)
    sk_hw = 12.0 * scale            # skull half-width

    def skull_region(x, y):
        t = (y - CY) / sk_r
        if abs(t) > 1.0: return False
        hw = sk_hw * math.sqrt(1.0 - t * t)
        return abs(x - cx) <= hw
    shade_region(cv, skull_region, L, base_fg=base_fg, hot_fg=hot_fg)

    # jaw: a second shaded surface below the skull (separate anatomy)
    def jaw_region(x, y):
        if not (CY + 3 * scale <= y <= CY + 10 * scale): return False
        t = (y - (CY + 6.5 * scale)) / (3.5 * scale)
        hw = 7.5 * scale * math.sqrt(max(0.0, 1.0 - t * t))
        return abs(x - cx) <= hw
    shade_region(cv, jaw_region, L, base_fg=base_fg - 4, hot_fg=hot_fg)

    # brow ridges: lit crests that fall into the eye sockets (the anatomy read)
    brow_ridge(cv, cx - 5 * scale, CY - 3 * scale, 3.6 * scale, L, base_fg=base_fg, hot_fg=hot_fg)
    brow_ridge(cv, cx + 5 * scale, CY - 3 * scale, 3.6 * scale, L, base_fg=base_fg, hot_fg=hot_fg)

    # constructed eyes: dark socket -> colored iris -> white glint (not dots)
    eye(cv, cx - 5 * scale, CY, r=1.7 * scale, iris_fg=iris_fg, glint=True)
    eye(cv, cx + 5 * scale, CY, r=1.7 * scale, iris_fg=iris_fg, glint=True)

    # nose: a shaded ridge down the center of the face
    for y in range(int(CY - 1), int(CY + 4)):
        L2 = L(cx, y) * 0.9
        ch, fg = shade(L2, base_fg=base_fg, hot_fg=hot_fg)
        set_cell(cv, x=cx, y=y, ch=ch, fg=fg, bg=0)

    # mouth: WARDEN grins (teeth in a cavity); VESSEL is closed (a held line)
    if grin:
        teeth(cv, int(cx - 5 * scale), int(cx + 5 * scale), int(CY + 6 * scale), n=7)
    else:
        for x in range(int(cx - 4 * scale), int(cx + 4 * scale) + 1):
            set_cell(cv, x, int(CY + 6 * scale), "\u2580", hot_fg & 7 if hot_fg > 7 else hot_fg, 0)

    # outer rim-light: the figure's OUTER edge (away from the seam) catches a cool rim so it
    # reads as lit-from-within, not floating. Direction depends on which side of the seam.
    outer = -1 if cx < SEAM else +1
    for y in range(int(CY - 7 * scale), int(CY + 10 * scale)):
        t = (y - CY) / sk_r
        if abs(t) > 1.0: continue
        hw = sk_hw * math.sqrt(1.0 - t * t)
        rx = int(cx + outer * hw)
        if 0 <= rx < W:
            set_cell(cv, rx, y, "\u2588", (iris_fg & 7) + 8, 0)

# --- the shared field: saturated color-cycling wash at the periphery ----------
# Clean black core so the two figures read; a thin dithered transition ring; full cycling
# wash at the corners. Same controlled-field idiom as WARDEN v1.0 -- the diptych sits in the
# same family, not on flat black like the two old portraits.
for y in range(H):
    for x in range(W):
        cyc = int((x * 0.13 + y * 0.27)) % len(HUE)
        fg = HUE[cyc]
        ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]      # diagonal dither, texture not fill
        dx = (x - SEAM) / 26.0
        dy = (y - CY) / 17.0
        fall = math.hypot(dx, dy)
        if fall < 0.80:                                       # clean core for the two figures
            set_cell(cv, x, y, " ", 0, 0)
        elif fall < 0.94:                                     # thin dithered transition ring
            set_cell(cv, x, y, ch, fg & 7, 0)
        else:                                                 # periphery: full saturated wash
            set_cell(cv, x, y, ch, fg, 0)

# --- the two figures, lit by one shared central source ------------------------
fig(cx=SEAM - 16, base_fg=96, hot_fg=15, iris_fg=93, grin=True,  scale=1.0)   # WARDEN (hollis): green guardian, grins
fig(cx=SEAM + 16, base_fg=92, hot_fg=14, iris_fg=95, grin=False, scale=0.92)  # VESSEL (raze): magenta counterpart, holds

# --- the seam: a thin vertical joint marking where the two figures meet -------
for y in range(CY - 11, CY + 12):
    set_cell(cv, SEAM, y, "\u2502", 94, 0)        # faint center seam

# --- assemble: house double-line bar top+bottom around the content ------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

# --- sig block (house standard, BOTH artists credited) ------------------------
sig_block(out, TITLE, handles="hollis / raze")

raw = "\n".join(out) + F.RESET + "\n"
open(OUT, "w", encoding="cp437").write(raw)
F.hygiene_gate(OUT)
print("wrote", OUT)
