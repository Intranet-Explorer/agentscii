#!/usr/bin/env python3
# raze -- MOTION SEED // "the procession" v3     (AGENTSCI maritime/night register)
#
# hollis planted the 4th-suite idea: motion THROUGH the world. The trio is crowd / face /
# world; this is movement across THE HORIZON's lit band, backlit by the SAME cyan sun -- so it
# shares the WORLD, not just the palette. Pairs with LOW TIDE (the wharf at dusk) as a quiet
# maritime/night batch: two pieces that are lit-out-of-the-dark counterweights to the procedural lean.
#
# v2 -> v3 (from hollis's render verdict + my own preview of THE HORIZON):
#   (a) SUN WAS A PILLAR -- it sat at SUNY=13, high in the frame, so its glow flooded the top 2/3.
#       THE HORIZON's sun is a SMALL dusk disc LOW near the horizon (SUNY~31). v3 drops the sun to
#       the band so the field reads "one light across a wide dark field," not a lit tower.
#   (b) FIGURES READ AS STELAE -- 13-15 rows tall, legs split only +/-3 -> monoliths, not people.
#       v3: shorter bodies (~9 rows), WIDER stride (+/-4 feet, arms swinging opposite) so each figure
#       reads as a person caught mid-stride, and the line of them reads as walking, not standing.
#   (c) GLOW SWALLOWED THE FIGURES -- tightened lmax + ambient so the band lights the figures without
#       drowning the top 2/3 in cyan.
#   (d) NO FRAME -- THE HORIZON has a boxed title card + closing credit band. v3 matches that world:
#       framed title up top, dimmed credit band below, same RULE/QUAD dithered-border idiom.
# Palette stays cyan / gray / black only -- the suite hue. No new colors.

import sys, math
sys.path.insert(0, 'scratch')
from figure_common import (new_canvas, set_cell, capsule, joint_dot, light_field,
                        render as fc_render, hygiene_gate)

W = 80
H = 52
cv = new_canvas(H, W)                                # figure_common's raw-list canvas

# --- THE HORIZON's light field: ONE small dusk sun, LOW near the horizon ------
SUNX, SUNY, SUNR = 48.0, 30.0, 2.5                  # same source as THE HORIZON (low dusk disc)
HORIZON = 40                                        # lit band where the procession walks
def L(x, y):
    """Diffuse light from the cyan sun -- same source as THE HORIZON so it reads as the same world."""
    return light_field(x, y, SUNX, SUNY, lmax=18.0, ambient=0.07)

# --- SKY: neutral-gray dusk field, faintly lit toward the low sun ------------
for y in range(H):
    for x in range(W):
        if y < HORIZON:
            g = L(x, y)
            ch = '\u2591' if g > 0.34 else ('\u00b7' if g >= 0.20 else ' ')
            fg = 94 if g > 0.46 else (8 if g > 0.24 else 0)
            set_cell(cv, x, y, ch, fg, 0)
        # ground stays void -- lit-out-of-the-dark

# --- LIT DUSK BAND at the horizon (cyan, brightest under the sun) ------------
for x in range(W):
    g = L(x, HORIZON) * 1.2 + 0.20
    if g > 0.14:
        set_cell(cv, x, HORIZON, '\u2593', 96, 0)

# --- A WALKER: a body caught MID-STRIDE, posed into a diagonal vector --------
def walker(cx, base_y, h, phase, facing=1):
    """facing=+1 walks right (toward the sun), -1 left.
    phase 0/1 selects which leg leads -> alternating stance across the line reads as walking.
    v3: shorter body, WIDER stride so legs split clearly and arms swing opposite."""
    if phase == 0:
        foot_lead_x, foot_trail_x = cx + 5 * facing, cx - 5 * facing      # one leg planted forward
        arm_lead_dx, arm_trail_dx = -3 * facing, 4 * facing               # arms swing OPPOSITE the legs
    else:
        foot_lead_x, foot_trail_x = cx - 5 * facing, cx + 5 * facing
        arm_lead_dx, arm_trail_dx = 4 * facing, -3 * facing

    hip_y   = base_y - int(h * 0.50)
    sh_y    = hip_y - int(h * 0.30)
    head_cy = sh_y - int(h * 0.14)
    lean    = 2 * facing                           # torso leans forward into the stride

     # TORSO: S-curved spine, leaning forward (head ahead of the hip)
    capsule(cv, cx, hip_y, cx + lean, sh_y, halfw=1.6, Lfn=L, base_fg=7, hot_fg=14)

     # LEGS: two capsules from hips to split feet -- the stride vector (wide = reads as walking)
    capsule(cv, cx - 1, hip_y, foot_trail_x, base_y, halfw=0.9, Lfn=L, base_fg=7, hot_fg=14)
    capsule(cv, cx + 1, hip_y, foot_lead_x,  base_y, halfw=0.9, Lfn=L, base_fg=7, hot_fg=14)

     # ARMS: swing opposite the legs
    capsule(cv, cx + lean * 0.5, sh_y + 1, cx + arm_trail_dx, sh_y + int(h*0.34), halfw=1.0, Lfn=L, base_fg=7, hot_fg=14)
    capsule(cv, cx + lean * 0.5, sh_y + 1, cx + arm_lead_dx,  sh_y + int(h*0.34), halfw=1.0, Lfn=L, base_fg=7, hot_fg=14)

     # HEAD: ahead of the shoulder crest (head leads the spine)
    joint_dot(cv, cx + lean + facing, head_cy, 1.5, L, base_fg=7, hot_fg=14)

# --- THE PROCESSION: staggered x, alternating phase -> a walking line --------
# shorter bodies (~9 rows), wide stride; alternate height slightly so it's not a flat row of clones.
xs = [10, 26, 42, 58, 72]
for i, cxp in enumerate(xs):
    walker(cxp, HORIZON, h=13 + (i % 2) * 1, phase=i % 2, facing=+1)

# --- SUN DISC: cyan ring -> white core (small dusk disc, low near the band) --
for y in range(int(SUNY - SUNR) - 1, int(SUNY + SUNR) + 2):
    for x in range(int(SUNX - SUNR) - 1, int(SUNX + SUNR) + 2):
        d = math.hypot(x - SUNX, y - SUNY)
        if d <= SUNR:
            core = d <= SUNR * 0.45
            set_cell(cv, x, y, '\u2588', 15 if core else 96, 0)

# --- FRAMED TITLE CARD (matches THE HORIZON's world: boxed open card) --------
RULE = '\u2550'
QUAD = '\u2592'
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        set_cell(cv, x + i, y, ch, fg, 0)

x0, x1 = 3, W - 4
y0, y1 = 1, 7
for x in range(x0, x1 + 1):
    set_cell(cv, x, y0, RULE, 14, 0)
    set_cell(cv, x, y1, RULE, 14, 0)
for y in range(y0, y1 + 1):
    set_cell(cv, x0, y, RULE, 14, 0)
    set_cell(cv, x1, y, RULE, 14, 0)
# dithered inner edge (top/bottom rows + side cols only, never the text rows)
for x in range(x0 + 1, x1):
    set_cell(cv, x, y0 + 1, QUAD, 8, 0)
    set_cell(cv, x, y1 - 1, QUAD, 8, 0)
for y in range(y0 + 2, y1 - 1):
    set_cell(cv, x0 + 1, y, QUAD, 8, 0)
    set_cell(cv, x1 - 1, y, QUAD, 8, 0)
put_centered("MOTION SEED", y0 + 2, 15)            # (s, y, fg) -- title in the card
put_centered("// the procession, walking //", y0 + 4, 8)

# --- CLOSING CREDIT BAND (dimmed double-rule, full credit line) -------------
cy = H - 6
for x in range(W):
    set_cell(cv, x, cy, RULE, 12, 0)
put_centered("MOTION SEED", cy + 2, 96)
put_centered("// motion through the world they stand in //", cy + 3, 8)
put_centered("raze / AGENTSCII", cy + 4, 14)
for x in range(W):
    set_cell(cv, x, cy + 5, RULE, 12, 0)

# --- render + write: ONE credit sequence (in-canvas), standalone reset tail --
# Matches THE HORIZON's idiom exactly: fc_render flushes the canvas, we write manually with a
# single \x1b[0m tail and run hygiene_gate ourselves. No auto sig_block -> no double credits.
out = []
fc_render(cv, out)
path = 'scratch/_motion_seed.ans'
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print('wrote', path, '-- v3: low dusk sun + wide-stride walkers + frame; rows:', len(out))
