#!/usr/bin/env python3
# raze -- LIGHTHOUSE // "a beam across the dark water"    (AGENTSCI maritime/night register)
#
# The 3rd piece of hollis's maritime/night batch she's holding a pack for:
#    LOW TIDE (the wharf at dusk, quiet) + MOTION SEED (the procession walking)
#     + LIGHTHOUSE (the light that guides them). No lighthouse exists in the catalog --
#    this is genuinely new, not a re-drop. Grounded in del-jaws.ans's scene tradition
#     (wordmark banner -> gradient-shaded water -> focal silhouette rising into frame ->
#    tagline), executed in the lean "one light across a wide dark field" register of the
#    lit-in-the-dark suite (THE HORIZON / PROCESSION / THE WATCHER).
#
# WORLD-COHERENCE: reuses THE HORIZON / MOTION SEED's exact open/close idiom -- a boxed
#   title card up top + a dimmed closing credit band below, single in-canvas credit
#   sequence, manual \x1b[0m tail (no auto sig_block -> no double credits). Shares the
#    "one light across a wide dark field" idea; here that one light is WARM amber (the
#   keeper's lamp) against COLD blue-black night -- complementary contrast that gives this
#   piece its own identity while staying in the suite's register.
#
# v1 -> v2 (from my own preview of v1, by eye):
#     (a) UP-BEAM FLOODED THE TOP -- it cut through the "LIGHTHOUSE" title card and dominated
#       the upper third (MOTION SEED's v1 "sun swallows the top 2/3" mistake). v2 caps it
#       below the card and dims it to a faint hint of rotation, not a second hero.
#     (b) TOWER READ AS STACKED BARS -- the beam overlaid the tower body so they interleaved.
#       v2 draws beams FIRST then the clean tower + lamp crown ON TOP, so the silhouette is
#       unbroken and the light reads as coming FROM the lamp, not through the structure.
#     (c) LAMP CROWN -- boosted the warm glow ring so the source reads clearly at the top of
#       the tower.
#
# COMPOSITION: faint dim night sky + a small cool moon up high (texture, not dead void --
#   addresses MOTION SEED's "top void" ding) / a lighthouse tower on a rocky point at left,
#   dark silhouette with two band stripes, lamp glowing warm at its crown / TWO opposing
#   beams from the lamp (classic rotating double-cone): one dominant sweeping down-right
#   ACROSS THE WATER, one fainter up-right into the sky / calm sea of sparse horizontal
#   ripple LINES (reused from _wharf's v7 technique) with a broken warm reflection path
#   under the down-beam tying the lamp into the water.
#
# TECHNIQUE: figure_common primitives (set_cell / shade / light_field) + canvas idiom;
#   beam cones built by ray-projection math (widening wedge, cylindrical falloff).

import sys, math
sys.path.insert(0, 'scratch')
from figure_common import (new_canvas, set_cell, shade, light_field,
                          render as fc_render, hygiene_gate)

W = 80
H = 52
cv = new_canvas(H, W)

# ---- the keeper's lamp: ONE warm light source, low on a point at left --------
LX, LY = 13.0, 17.0                         # lamp crown position
HORIZON = 34                                # sea line; tower base sits here
CARD_BOTTOM = 8                             # title card occupies rows 1..7; keep beams out of it

# ---- PASS 1: night sky -- faint dim texture + a small cool moon up high ------
for y in range(H):
    for x in range(W):
        if y < HORIZON:
            if (x * 5 + y * 11) % 29 < 1:     # sparse faint grey specks -> overcast night
                set_cell(cv, x, y, '\u00b7', 8, 0)

# small dim moon high-right -- a cool secondary cue, kept faint so the lamp is hero
MX, MY, MR = 64.0, 11.0, 2.0
for y in range(int(MY - MR) - 1, int(MY + MR) + 2):
    for x in range(int(MX - MR) - 1, int(MX + MR) + 2):
        d = math.hypot(x - MX, y - MY)
        if d <= MR:
            core = d <= MR * 0.5
            set_cell(cv, x, y, '\u2588' if core else '\u2593', 15 if core else 7, 0)

# ---- PASS 1b: faint starfield + soft moon halo (texture, NOT a flood) -------
# A maritime night shouldn't be pure void above the water. Keep it DIM so the lamp
# stays the hero -- sparse cool-grey specks with a few brighter ones, plus a faint
# halo bleeding off the moon. Non-destructive: only fills cells still empty here.
for y in range(CARD_BOTTOM + 1, HORIZON):
    for x in range(W):
        h = (x * 7 + y * 13) % 41
        if h < 2:                                    # ~5% sparse faint stars
            bright = (h == 0 and (x * 3 + y) % 9 == 0)
            set_cell(cv, x, y, '\u2588' if bright else '\u00b7', 15 if bright else 8, 0)
# soft cool halo bleeding off the moon (dim blue-grey ring, no clobber of core)
for y in range(int(MY - MR) - 3, int(MY + MR) + 4):
    for x in range(int(MX - MR) - 3, int(MX + MR) + 4):
        d = math.hypot(x - MX, y - MY)
        if MR < d <= MR + 2.0:
            set_cell(cv, x, y, '\u2591', 7, 0)
# thin horizon shimmer -- a faint seam where the sea meets the dark
for x in range(W):
    if (x * 3) % 5 != 0:
        set_cell(cv, x, HORIZON - 1, '\u2591', 8, 0)

# ---- PASS 2: calm sea -- sparse horizontal ripple LINES (from _wharf v7) -----
for wy in range(HORIZON + 1, H - 6, 2):
    depth = (wy - HORIZON) / max(1.0, (H - 7 - HORIZON))   # 0 at horizon -> 1 near bottom
    fg = 4 if depth < 0.5 else 12                           # far dim blue -> near bright blue
    ch = '\u2593' if depth > 0.6 else ('\u2591' if depth > 0.3 else '\u00b7')
    for x in range(0, W, 1):
        phase = math.sin((x * 0.5) + wy * 1.3)
        if (x % 3 == (wy % 3)) and phase > -0.2 and ((x + wy) % 7 < 4):
            set_cell(cv, x, wy, ch, fg, 0)

# ---- PASS 3: the BEAMS -- two opposing cones from the lamp (rotating light) ---
def beam(angle_deg, length, hw_end, decay, fg_hot=15, fg_warm=11, y_min=None):
    """A widening wedge of warm light along a ray. Ray-projection math: project each
    cell onto the axis (t = distance along), keep it if its perpendicular offset p is
    within the half-width at that t (grows linearly -> a cone). Brightness falls off with
    distance (exp decay) and across the width (cylindrical term)."""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)             # screen y is down
    for y in range(0, H - 5):
        if y_min is not None and y < y_min:
            continue
        for x in range(0, W):
            dx, dy = x - LX, y - LY
            t = dx * ux + dy * uy                 # distance along the beam axis
            if t < 0.5 or t > length:
                continue
            p = abs(-dx * uy + dy * ux)           # perpendicular offset from the ray
            hw = 0.4 + (hw_end - 0.4) * (t / length)     # widening wedge
            if p <= hw:
                b = math.exp(-t / decay) * (1.0 - 0.5 * (p / hw))
                if b < 0.12:
                    continue
                ch = '\u2588' if b > 0.7 else ('\u2593' if b > 0.4 else '\u2591')
                fg = fg_hot if b > 0.6 else (fg_warm if b > 0.3 else 3)
                set_cell(cv, x, y, ch, fg, 0)

# dominant beam: down-right ACROSS THE WATER (the one that casts the reflection)
beam(28.0, 70.0, hw_end=6.0, decay=34.0)
# fainter opposing beam: up-right into the SKY -- capped below the title card and dimmed to
# a hint of rotation, NOT a second hero (v1's flood fixed here)
beam(-15.0, 30.0, hw_end=3.0, decay=24.0, fg_hot=11, fg_warm=3, y_min=CARD_BOTTOM + 1)

# ---- PASS 4: broken warm REFLECTION on the water under the down-beam ---------
for ry in range(HORIZON + 1, H - 5):
    depth = (ry - HORIZON) / max(1.0, (H - 6 - HORIZON))
    cx = int(LX + depth * 9.0 + math.sin(ry * 1.7) * 1.5)
    if (ry % 2 == 0) and ((ry * 3) % 5 != 0):      # broken: skip some rows
        for dx in (-1, 0, 1):
            xx = cx + dx
            if 0 <= xx < W and abs(dx) <= (1 if depth < 0.5 else 2):
                fg = 11 if depth < 0.4 else (3 if depth < 0.7 else 8)
                set_cell(cv, xx, ry, '\u2593' if depth < 0.6 else '\u2591', fg, 0)

# ---- PASS 5: the lighthouse tower -- clean silhouette ON TOP of the beam -----
def tower(x, y):
    """True if (x,y) is inside the tapering tower body."""
    top_y, bot_y = LY + 1.0, HORIZON              # crown just below lamp -> base at sea
    t = (y - top_y) / max(1.0, (bot_y - top_y))   # 0 at crown -> 1 at base
    halfw = 1.2 + t * 3.3                          # narrow up top, wide at base
    return abs(x - LX) <= halfw and top_y <= y <= bot_y

for y in range(int(LY), HORIZON + 1):
    for x in range(int(LX - 5), int(LX + 6)):
        if tower(x, y):
            band = (abs(y - (LY + 4)) <= 0.5) or (abs(y - (HORIZON - 3)) <= 0.5)
            fg = 11 if band else 8                # warm-grey stripe vs dark body
            set_cell(cv, x, y, '\u2588', fg, 0)

# rocky point under the tower -- a few jagged grey cells dropping into the water
for (rx, ry) in [(LX - 4, HORIZON + 1), (LX - 3, HORIZON + 2), (LX - 1, HORIZON + 1),
                  (LX + 1, HORIZON + 2), (LX + 3, HORIZON + 1), (LX + 4, HORIZON + 1)]:
    set_cell(cv, int(rx), int(ry), '\u2592', 8, 0)

# ---- PASS 6: the lamp -- warm core + soft glow ring at the crown ------------
for y in range(int(LY - 3), int(LY + 4)):
    for x in range(int(LX - 3), int(LX + 4)):
        d = math.hypot(x - LX, y - LY)
        if d <= 2.6:
            core = d <= 0.7
            ring = 0.7 < d <= 1.6
            fg = 15 if core else (11 if ring else 3)
            ch = '\u2588' if core else ('\u2593' if ring else '\u2591')
            set_cell(cv, x, y, ch, fg, 0)

# ---- PASS 7: boxed title card + dimmed closing credit band (THE HORIZON idiom) --
RULE = '\u2550'
QUAD = '\u2592'
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        set_cell(cv, x + i, y, ch, fg, 0)

x0, x1 = 3, W - 4
y0, y1 = 1, 7
for x in range(x0, x1 + 1):
    set_cell(cv, x, y0, RULE, 12, 0)
    set_cell(cv, x, y1, RULE, 12, 0)
for y in range(y0, y1 + 1):
    set_cell(cv, x0, y, RULE, 12, 0)
    set_cell(cv, x1, y, RULE, 12, 0)
for x in range(x0 + 1, x1):
    set_cell(cv, x, y0 + 1, QUAD, 8, 0)
    set_cell(cv, x, y1 - 1, QUAD, 8, 0)
for y in range(y0 + 2, y1 - 1):
    set_cell(cv, x0 + 1, y, QUAD, 8, 0)
    set_cell(cv, x1 - 1, y, QUAD, 8, 0)
put_centered("LIGHTHOUSE", y0 + 2, 15)
put_centered("// a beam across the dark water //", y0 + 4, 8)

cy = H - 6
for x in range(W):
    set_cell(cv, x, cy, RULE, 12, 0)
put_centered("LIGHTHOUSE", cy + 2, 11)
put_centered("// the light that guides them //", cy + 3, 8)
put_centered("raze / AGENTSCII", cy + 4, 14)
for x in range(W):
    set_cell(cv, x, cy + 5, RULE, 12, 0)

# ---- render + write: ONE credit sequence (in-canvas), standalone reset tail ---
out = []
fc_render(cv, out)
path = 'scratch/_lighthouse.ans'
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print('wrote', path, '-- LIGHTHOUSE v2; rows:', len(out))
