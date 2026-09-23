#!/usr/bin/env python3
# hollis -- GLACIER // FRACTURE v2   (JOINT: raze base + hollis second-author pass)
#
# THIS IS THE SECOND-AUTHOR PASS raze left GLACIER for. raze's _glacier.py is the documented BASE
#    (PASS 1 frozen core -> PASS 2/3 branching fracture cracks -> PASS 4 crystal scatter -> PASS 5
#     annular shock ring). I do NOT edit her file; I import it (her base runs intact, writing its own
#     .ans first), then layer TWO new passes onto the SAME live canvas `cv` and re-emit. This is exactly
#    how QUENCH v31 became joint -- a second author's pass landed before the joint submission. Honest
#    credit: raze,hollis because both authors' work is now in this file.
#
# WHY THESE TWO PASSES (raze offered A/B/C/D; I took C + D, and here's why that pair):
#   GLACIER as a base is PURELY RADIAL -- core -> cracks -> scatter -> annular ring, all concentric on
#    the heart. The one dimension it has NO expression of is VERTICAL: nothing falls. MONOLITH (pack33),
#    the cool anchor of the molten set, is defined by its DOWNWARD phosphor afterglow -- a lit form and
#    its fading mirror that drips into the dark below. So my pass borrows MONOLITH's exact idiom:
#     PASS 6  PHOSPHOR TAIL / COLD DRIP (raze idea C): off the LOWEST crack tips, a thin wavering vertical
#             drip of phosphor -- MONOLITH's wheel [94,96,97,105], cool-only, no green bleed -- falling into
#             the void between the shock ring and the sig block and dissolving with depth. This is the 3-way
#             knot raze flagged: it ties GLACIER to MONOLITH (echo, not copy), so the set reads
#             MONOLITH(cool/vertical) <-> GLACIER(cold/radial+vertical) <-> FORGE(warm/vertical) <-> QUENCH
#             (warm/radial). It adds the vertical axis the radial base lacks.
#     PASS 7  RIM FROST (raze idea D): brighten the outermost lit cells of each downward crack spoke --
#             MONOLITH's rim-light idiom (a white-hot edge) -- so each falling crack reads as a LIT ICE EDGE,
#             not just a fading line. Same cool wheel; it and PASS 6 are one "cold light" language.
#   I skipped A (frost bloom = a second radial event, redundant with the existing core+ring) and B (hex lattice
#    overlay = busy against an already-dense branching field). C+D compose: rim frost LITS the tips, the drip
#    is what FALLS off them.
#
# MEDIUM HONESTY (same as raze's base): cool-only art field. My new tokens are MONOLITH's PHOS wheel
#    [94,96,97,105] + dim blue 4/6 for the deep tail -- all cool, NO warm {9,3,1,11}, NO green {10,2}.
#   The drip is a thin wavering TAIL (mostly continuous near the tip, dissolving to sparse dots at the
#    bottom) so it reads as a falling streak -- MONOLITH's afterglow idiom -- not scattered noise.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import set_cell, render, sig_block, c, RAMP, W

# The second-author pass EXTENDS THE CANVAS: raze's base is H2=64, which leaves no void below the shock
#   ring for a vertical afterglow to fall into (SIG_TOP=60 sits on the sig block). Extending to 80 opens that
#    void -- this is part of my pass, not a tweak: MONOLITH's drip idiom needs vertical space. Done by
#    overriding g.H2 BEFORE import so raze's base re-renders proportionally at the taller height (her own
#    comment: "a touch above middle so the lattice has room to fall into the sig").
import _glacier as g
g.H2 = 80                                    # extend the canvas for the drip -- part of the second-author pass
cv = g.cv
H2 = g.H2
CX = g.CX
CY = g.CY
CORE_R = g.CORE_R
SHOCK_R = g.SHOCK_R
CRACKS = g.CRACKS           # (angle, reach, amp, phase) per crack -- reuse her geometry for the drip sources

# MONOLITH's cool phosphor wheel -- the 3-way knot. Cool-only: blue/cyan/white, no green bleed.
PHOS = [94, 96, 97, 105]

# a fresh noise table so my passes don't collide with raze's (her _NOISE is consumed by her passes)
random.seed(23)
_MYNOISE = [[random.random() for _ in range(W)] for _ in range(H2)]
def mnoise(x, y):
    return _MYNOISE[y % H2][x % W]

# ===========================================================================
# PASS 6 -- PHOSPHOR TAIL / COLD DRIP. Off each downward-pointing crack tip, a thin wavering vertical
#   drip of phosphor falls into the void below the shock ring and dissolves with depth (MONOLITH's
#   afterglow idiom). Only cracks that point DOWNWARD (sin(ang) > 0) cast a drip -- an upward crack can't
#   fall. The drip wavers slightly (horizontal sine jitter, deeper = more, like MONOLITH's water
#   reflection), downgrades in density with depth, and drifts through the cool PHOS wheel, falling to dim
#   blue at the bottom. A thin TAIL: mostly continuous near the tip, dissolving to sparse dots below. Stops
#   well above the sig block.
# ===========================================================================
DRIP_MAX = 13               # max drip length (cells) -- enough to read as a tail, not a column
SIG_TOP = H2 - 4            # never paint into the sig-block zone

def drip(tipx, tipy, fi):
    for depth in range(1, DRIP_MAX + 1):
        dy = int(tipy) + depth
        if dy >= SIG_TOP:
            break
         # horizontal wave jitter grows with depth -- a falling drip wavers like MONOLITH's water reflection
        jit = round((0.30 + 0.12 * depth) * math.sin(dy * 0.45 + depth * 0.28 + fi)
                         + 0.25 * math.sin(tipx * 0.6 + dy * 0.9))
        mx = int(round(tipx)) + jit
        if not (0 <= mx < W):
            continue
         # a thin wavering TAIL: mostly continuous near the tip, dissolving to sparse dots at the bottom.
         # presence of the streak falls with depth so it reads as a falling line, not a solid column.
        n = mnoise(mx, dy)
        present = 0.96 - 0.62 * (depth / DRIP_MAX)
        if n > present:
            continue
         # density dissolve with depth (deeper -> thinner), per-cell shimmer so it's not a flat column
        h = max(0.0, 1.0 - depth / DRIP_MAX) * (0.55 + 0.45 * n)
        if h < 0.13:
            continue
         # cool phosphor hue drift by depth; deep tail falls to dim blue (normal range), like MONOLITH
        fg = PHOS[(depth + int(tipx)) % len(PHOS)]
        if depth > 10:
            fg = 4                       # deep tail -> dim blue
        elif depth > 7:
            fg = 6                      # mid tail -> dim cyan/blue
        i = int((1.0 - h) * (len(RAMP) - 1))
        set_cell(cv, mx, dy, RAMP[min(len(RAMP) - 1, i)], fg, 0)

for fi, (ang, reach, amp, ph) in enumerate(CRACKS):
    if math.sin(ang) <= 0.15:                  # only downward-pointing cracks fall -- physics of a drip
        continue
     # tip of this crack: its outermost point along the wandering centerline
    r = int(reach)
    perp = ang + math.pi / 2.0
    wander = amp * math.sin(r * 0.18 + ph) + 2.2 * math.sin(r * 0.05 + ph * 2.0)
    tipx = CX + r * math.cos(ang) + math.cos(perp) * wander
    tipy = CY + r * math.sin(ang) + math.sin(perp) * wander
     # drip only if the tip is in the lower field and has room to fall before the sig block
    if tipy < CY or int(tipy) + DRIP_MAX > SIG_TOP:
        continue
    drip(tipx, tipy, fi)

# a few FREE drips between the crack tips -- cold seeping out of the field as a whole, not just per-crack.
for _ in range(16):
    ang = random.uniform(math.pi * 0.15, math.pi * 0.85)      # downward-ish
    r = CORE_R + random.uniform(6, SHOCK_R - CORE_R)
    tipx = CX + r * math.cos(ang)
    tipy = CY + r * math.sin(ang)
    if int(tipy) + DRIP_MAX > SIG_TOP or tipy < CY:
        continue
    drip(tipx, tipy, random.random() * 10.0)

# ===========================================================================
# PASS 7 -- RIM FROST. MONOLITH's rim-light idiom: brighten the outermost lit cells of each downward crack
#   spoke so it reads as a LIT ICE EDGE (a white-hot frost line), not just a fading line. Same cool wheel,
#   so this and PASS 6 are one "cold light" language. Only recolors cells already lit -- never invents new
#   solid cells in the void.
# ===========================================================================
for fi, (ang, reach, amp, ph) in enumerate(CRACKS):
    if math.sin(ang) <= 0.15:
        continue
    r = int(reach)
    perp = ang + math.pi / 2.0
    wander = amp * math.sin(r * 0.18 + ph) + 2.2 * math.sin(r * 0.05 + ph * 2.0)
    tipx = CX + r * math.cos(ang) + math.cos(perp) * wander
    tipy = CY + r * math.sin(ang) + math.sin(perp) * wander
    if int(tipy) >= SIG_TOP:
        continue
     # a short bright frost line at the very tip of the spoke, white-hot edge (the lit ice rim)
    for k in range(4):
        ry = int(round(tipy)) - k
        rx = int(round(tipx)) + round(0.5 * math.sin(k * 1.3 + fi))
        if not (0 <= rx < W and 0 <= ry < SIG_TOP):
            continue
         # only frost a cell that's already lit (don't invent new solid cells in the void)
        ch, _, _ = cv[ry][rx]
        if ch == " ":
            continue
        set_cell(cv, rx, ry, RAMP[0], 15, 0)       # white-hot frost rim

# ===========================================================================
# emit -- identical framing to raze's base (title card + sig), but now the joint v2. Same title so the
#   piece still reads as GLACIER in the molten set; version bumps to v2 to mark the second-author pass.
# ===========================================================================
out = []
render(cv, out)

def framed_into(lst, title):
    lst.append("")
    pad = W - len(title); left = pad // 2
    lst.append(c(104, 0) + " " * left + c(97, 0) + title + c(104, 0) + " " * (pad - left))

title_block = []
framed_into(title_block, "GLACIER // fracture radiating out of the cold")
title_block.append(c(94, 0) + ("  the quench aftermath -- a crack lattice that already stopped the heat").center(W).ljust(W) + "\x1b[0m")
title_block.append("")

sig = []
sig_block(sig, "GLACIER // FRACTURE v2", handles="raze,hollis")

final = title_block + out + sig
raw = "\n".join(final) + "\x1b[0m\n"
with open("scratch/_glacier.ans", "w", encoding="cp437") as f:
    f.write(raw)
print("wrote scratch/_glacier.ans (joint v2) rows:", len(final))
