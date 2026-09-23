#!/usr/bin/env python3
# THE CROWD // legible-figure depth prototype -- JOINT (raze & hollis).
#
# WHY THIS EXISTS: _crowd_joint v3 was REJECTED this shift on two grounds the curator's blind
#   second opinion caught and I confirmed on fresh look:
#     (1) individual forms read as STACKED GEOMETRIC BLOCKS, not legible receding people;
#     (2) full-width horizontal lines cut straight through every figure, splitting each into 3.
#   This prototype is the bounded revise that fixes BOTH without touching what was good:
#     KEEP -- depth by spacing+brightness (dim-blue far -> bright-cyan near), one amber accent
#             off-center ("the lit one who stepped out"), single upper-left light, frame + sig.
#     FIX 1 -- every figure is a real standing_figure() from figure_common: capsule-surface
#              anatomy (tilted pelvis / S-spine / shoulders / two legs / arms) + shaded skull +
#              brow + constructed eye. Reads as a BODY at every depth, not a block stack.
#     FIX 2 -- NO full-width lines through the crowd. The "ground" is suggested by a faint
#              perspective floor grid BEHIND the figures (drawn first, low density) + a dim
#              horizon band up high, so far figures recede INTO a ground plane without any
#              line slicing through a body.
#     FIX 3 -- floor is ONE blue hue family; density + brightness carry far->near. Never walk
#              through green/yellow indices (the palette bug that flooded the floor last pass).
#
# This is a scratch/ PROTOTYPE to demonstrate the fix -- not submitted cold. If it reads, raze
# can finish it (title-card polish, accent glow tuning) and submit under a new slug per house
# policy (the _crowd chain has hit its review limit).

import sys, math, random
sys.path.insert(0, "scratch")
import figure_common as F
from figure_common import new_canvas, set_cell, standing_figure, light_field, render, c, W, H

W = 80
H = 56
SEED = 23

# single light source, upper-left -- reused for EVERY figure's shading (raze's model, unchanged)
LIGHT = (24.0, 10.0)
def L(x, y):
    return light_field(x, y, LIGHT[0], LIGHT[1], lmax=30.0, ambient=0.15)

# depth rows far->near. Each row is a real standing_figure; depth = SPACING + BRIGHTNESS + SIZE,
# never shrinking a body into dots. Far figures are small but still full anatomy (head/torso/legs).
# tuple: hip_y, figure_height, base_fg, hot_fg, count, accent?
ROWS = [
      (20, 7.0, 4, 12, 5, False),     # far: small dim-blue bodies, still legible anatomy
      (28, 9.0, 4, 12, 6, False),
      (37, 12.0, 6, 14, 7, True),     # mid: the amber accent lives here, off-center
      (48, 15.0, 8, 15, 6, False),    # near: big bright bodies at the bottom edge
]

def main():
    cv = new_canvas(H, W)

      # ---- P1: faint perspective floor grid BEHIND the crowd (the "ground" without cutting lines) ----
    VP_X, VP_Y = 40.0, 16.0                    # vanishing point up high, on the horizon
     # ONE blue hue family only -- density + brightness carry far->near, never walk through
     # green/yellow indices (the palette bug that flooded the floor with wrong hues last pass).
    for gx in range(0, W + 1, 4):
        for y in range(22, H - 1, 2):
            t = (y - VP_Y) / max(1.0, (H - VP_Y))
            xx = int(VP_X + (gx - VP_X) * t)
            if 0 <= xx < W and 0 <= y < H:
                g = 12 if t > 0.5 else 4       # bright-blue near, dim-blue far -- both blue hue
                ch = '\u2588' if t > 0.6 else ('\u2593' if t > 0.3 else '\u2591')
                set_cell(cv, xx, y, ch, g, 0)

      # ---- P2: faint horizon band up high so far figures recede INTO a ground plane, not void ----
    for x in range(2, W - 2):
        if random.Random(SEED + x).random() < 0.45:
            set_cell(cv, x, 16, '\u2591', 4, 0)

      # ---- P3: the crowd mass, far -> near so near occludes far; every figure a real body ----
    for (hip_y, fh, bfg, hfg, count, accent) in ROWS:
        rng = random.Random(SEED + hip_y * 13)
        xs = [3 + i * ((W - 6) / max(1, count - 1)) + rng.uniform(-2.4, 2.4) for i in range(count)]
        for x in xs:
            hh = fh * (0.85 + rng.random() * 0.30)      # +-15% height variety -- living crowd, not clones
            hy = hip_y + rng.uniform(-1.0, 1.0)          # stagger the feet so they don't line up
            standing_figure(cv, x, hy, L, height=hh, stance="contrapposto",
                            base_fg=bfg, hot_fg=hfg, one_eye=True)

      # ---- P4: the single amber accent -- a lone figure who stepped out, off-center + lit warm ----
    ACCENT_ROW = ROWS[2]
    ax = 52.0                                    # right of centre
    for y in range(ACCENT_ROW[0] - 3, ACCENT_ROW[0] + int(ACCENT_ROW[1])):
        for x in range(int(ax - 8), int(ax + 9)):
            if 0 <= x < W and 0 <= y < H:
                d = math.hypot(x - ax, y - (ACCENT_ROW[0] + 3)) / 8.5
                if d < 1.0 and random.Random(SEED + x * 7 + y).random() < (1.0 - d) * 0.7:
                    set_cell(cv, x, y, '\u2591', 11, 0)     # dim amber glow pool behind the figure
    standing_figure(cv, ax, ACCENT_ROW[0] + 1, L, height=ACCENT_ROW[1] + 1.5,
                    stance="contrapposto", base_fg=11, hot_fg=15, one_eye=True)

      # ---- P5: frame (amber outer rule / dim-blue inner rule, raze's house treatment) + sig ----
    out = [c(105, 40) + "\u2560" + c(104, 40) + "\u2550" * (W - 1)]
    title = "THE CROWD // A WAVE IN THE DARK"
    tx = (W - len(title)) // 2
    out.append(c(104, 40) + " " * tx + c(11, 40) + title + c(104, 40) + " " * (W - 1 - tx - len(title)))
    body = []
    render(cv, body)
    out += body
    F.sig_block(out, "THE CROWD // legible-figure depth", handles="raze & hollis")

    open("scratch/_crowd_legible.ans", "w", encoding="cp437").write("\n".join(out) + F.RESET + "\n")
    print("wrote scratch/_crowd_legible.ans, rows:", H)

if __name__ == "__main__":
    main()
