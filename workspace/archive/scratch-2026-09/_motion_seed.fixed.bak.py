#!/usr/bin/env python3
# raze -- MOTION SEED // "the procession" v2    (AGENTSCI maritime/night register)
#
# hollis planted the 4th-suite idea: motion THROUGH the world. The trio is crowd / face /
# world; this is movement across THE HORIZON's lit band, backlit by the SAME cyan sun -- so it
# shares the WORLD, not just the palette. Pairs with LOW TIDE (the wharf at dusk) as a quiet
# maritime/night batch: two pieces that are lit-out-of-the-dark counterweights to the procedural lean.
#
# v1 -> v2: v1's "walkers" were vertical bars with feet +/-1px apart -- identical, no stride read.
# The fix (from STRIDE, shipped pack38): MOTION reads as a DIAGONAL VECTOR -- legs split wide
# (one planted forward, one trailing back), arms swinging OPPOSITE the legs, torso leaning forward,
# head ahead of the spine. Built from figure_common's capsule()/joint_dot() surfaces lit by ONE cyan
# point source, so each figure is a lit 3D form, not a flat silhouette. Clean hygiene via write_ans.

import sys, math
sys.path.insert(0, 'scratch')
from canvas import write_ans                       # clean sig-block + standalone reset + hygiene_gate
from figure_common import (new_canvas, set_cell, capsule, joint_dot, light_field,
                        shade_region, render as fc_render)

W = 80
H = 52
cv = new_canvas(H, W)                              # figure_common's raw-list canvas

# --- THE HORIZON's light field: one cyan sun high in the frame ---------------
SUNX, SUNY, SUNR = 56.0, 13.0, 3.0
HORIZON = 40             # lit band where the procession walks
def L(x, y):
    """Diffuse light from the cyan sun -- same source as THE HORIZON so it reads as the same world."""
    return light_field(x, y, SUNX, SUNY, lmax=30.0, ambient=0.10)

# --- SKY: neutral-gray dusk field, faintly lit toward the sun ----------------
for y in range(H):
    for x in range(W):
        if y < HORIZON:
            g = L(x, y)
            ch = '\u2591' if g > 0.30 else ('\u00b7' if g >= 0.16 else ' ')
            fg = 94 if g > 0.42 else (7 if g > 0.22 else 8)
            set_cell(cv, x, y, ch, fg, 0)
        # ground stays void -- lit-out-of-the-dark

# --- LIT DUSK BAND at the horizon (cyan, brightest under the sun) ------------
for x in range(W):
    g = L(x, HORIZON) * 1.2 + 0.20
    if g > 0.12:
        set_cell(cv, x, HORIZON, '\u2593', 96, 0)

# --- A WALKER: a body caught MID-STRIDE, posed by hand into a diagonal -------
def walker(cx, base_y, h, phase, facing=1):
    """facing=+1 walks right (toward the sun), -1 left.
    phase 0/1 selects which leg leads -> alternating stance across the line reads as walking."""
    if phase == 0:
        foot_lead_x, foot_trail_x = cx + 3 * facing, cx - 3 * facing    # one leg planted forward
        arm_lead_dx, arm_trail_dx = -1 * facing, 2 * facing             # arms swing OPPOSITE the legs
    else:
        foot_lead_x, foot_trail_x = cx - 3 * facing, cx + 3 * facing
        arm_lead_dx, arm_trail_dx = 2 * facing, -1 * facing

    hip_y   = base_y - int(h * 0.46)
    sh_y    = hip_y - int(h * 0.30)
    head_cy = sh_y - int(h * 0.16)
    lean    = 2 * facing                         # torso leans forward into the stride

    # TORSO: S-curved spine, leaning forward (head ahead of the hip)
    capsule(cv, cx, hip_y, cx + lean, sh_y, halfw=2.0, Lfn=L, base_fg=8, hot_fg=96)

    # LEGS: two capsules from hips to split feet -- the stride vector
    capsule(cv, cx - 1, hip_y, foot_trail_x, base_y, halfw=1.4, Lfn=L, base_fg=8, hot_fg=96)
    capsule(cv, cx + 1, hip_y, foot_lead_x,  base_y, halfw=1.4, Lfn=L, base_fg=8, hot_fg=96)

    # ARMS: swing opposite the legs
    capsule(cv, cx + lean * 0.5, sh_y + 1, cx + arm_trail_dx, sh_y + int(h*0.30), halfw=1.2, Lfn=L, base_fg=8, hot_fg=96)
    capsule(cv, cx + lean * 0.5, sh_y + 1, cx + arm_lead_dx,  sh_y + int(h*0.30), halfw=1.2, Lfn=L, base_fg=8, hot_fg=96)

    # HEAD: ahead of the shoulder crest (head leads the spine)
    joint_dot(cv, cx + lean + facing, head_cy, 1.7, L, base_fg=8, hot_fg=96)

# --- THE PROCESSION: staggered x, alternating phase -> a walking line --------
xs = [8, 17, 26, 35, 44, 53, 62, 71]
for i, cxp in enumerate(xs):
    walker(cxp, HORIZON, h=13 + (i % 2) * 2, phase=i % 2, facing=+1)

# --- SUN DISC: cyan ring -> white core --------------------------------------
for y in range(int(SUNY - SUNR) - 1, int(SUNY + SUNR) + 2):
    for x in range(int(SUNX - SUNR) - 1, int(SUNX + SUNR) + 2):
        d = math.hypot(x - SUNX, y - SUNY)
        if d <= SUNR:
            core = d <= SUNR * 0.45
            set_cell(cv, x, y, '\u2588', 15 if core else 96, 0)

# --- tagline ---------------------------------------------------------------
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        set_cell(cv, x + i, y, ch, fg, 0)
put_centered("// the procession, walking //", 3)

# --- render clean via write_ans (proper standalone reset, cp437, hygiene_gate)
rows = []
fc_render(cv, rows)
write_ans('scratch/_motion_seed.ans', rows, title='MOTION SEED // the procession v2.0', handles='raze')
print('wrote scratch/_motion_seed.ans -- v2: striding procession lit by THE HORIZON cyan sun; rows:', len(rows))
