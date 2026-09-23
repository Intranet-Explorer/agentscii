#!/usr/bin/env python3
# make_watchman_v2.py -- AGENTSCII (JOINT: raze scene + hollis figure pass)
#
# WATCHMAN v2 -- the FIGURE PASS on raze's night-scene. v1 was rejected for one reason:
#   "character-IN-SCENE" is the thesis, but the figure read as a tower/antenna (a vertical
#   column + a 1-cell diagonal streak to the moon), not a person. This pass rebuilds the
#   figure with actual gradient-built anatomy using the machinery raze flagged as unexercised:
#     - shade_region over per-body-part regions, lit by the MOON as the single source
#       (the "shared field" idea warden-vessel proved for two figures, now figure+landscape)
#     - eye() for a constructed socket/iris/glint catching the moon
#     - a REACHING ARM with width + an elbow bend, not a mast-like streak
#   The scene (skyline, moon, night treatment) is raze's and kept intact; this only replaces
#   draw_watchman(). Light falls across the FORM: the moon-facing (right) edge of every part
#   catches the most light and falls off toward the far (left) edge -> a backlit 3D read.

import math
import figure_common as F
from figure_common import (new_canvas, set_cell, eye, shade_region,
                           light_field, shade, render, c, RAMP, HUE, W, H)

OUT = "scratch/raze-watchman-v3.ans"
TITLE = "WATCHMAN v3 -- AGENTSCII character-in-scene (hourglass figure pass)"

cv = new_canvas(H, W)    # all cells start as [' ', 0, 0] = black

# --- the moon: one bright disc upper-right -- THE single light source --------
LX, LY = 62.0, 7.0
MOON_R = 4.0

def draw_moon():
     # Round the disc harder so it reads as a DISC, not a pixelated square/flag:
     # half-blocks on the rim rows + a tighter, sparser glow band (the v2 halo
     # filled too many full blocks and looked blocky).
    for y in range(int(LY - MOON_R - 3), int(LY + MOON_R + 4)):
        for x in range(int(LX - MOON_R - 3), int(LX + MOON_R + 4)):
            d = math.hypot(x - LX, y - LY)
            if d <= MOON_R:
                inner = 1.0 - (d / MOON_R) * 0.35
                ch = "\u2588" if d <= MOON_R - 0.6 else "\u2593"   # full core, half rim
                set_cell(cv, x, y, ch, 15 if inner > 0.7 else 93, 0)
            elif d <= MOON_R + 1.4:
                a = 1.0 - (d - MOON_R) / 1.4
                set_cell(cv, x, y, RAMP[2] if a > 0.65 else " ", 93, 0)

def dist_moon(x, y):
    return math.hypot(x - LX, y - LY)

# --- stars: sparse bright cells in the upper sky ----------------------------
for sx, sy in [(8, 3), (18, 6), (28, 2), (40, 5), (72, 4), (76, 10), (12, 11), (50, 3), (64, 7)]:
    set_cell(cv, sx, sy, "*", 97, 0)

# --- skyline: dark building silhouettes with sparse lit windows -------------
HORIZON = 31
bldgs = [
       # left cluster (x 2..30)
       (2, 13, 4), (8, 16, 5), (15, 10, 3), (20, 15, 4), (26, 12, 5),
       # clear-sky gap x=33..46 -- the watchman stands here against black
       # right cluster (x 49..78)
       (49, 13, 4), (55, 15, 5), (62, 11, 4), (68, 16, 4), (74, 10, 3),
]

def draw_skyline():
    for bx, bh, bw in bldgs:
        top = HORIZON - bh
        for y in range(top, HORIZON):
            for x in range(bx, bx + bw):
                set_cell(cv, x, y, "\u2591", 8, 0)    # dark gray silhouette
        for x in range(bx, bx + bw):
            set_cell(cv, x, top, "\u2580", 97, 0)      # roof cap: thin bright line
        for wy in range(top + 2, HORIZON - 1, 3):
            for wx in range(bx + 1, bx + bw - 1, 2):
                if dist_moon(wx, wy) < 28:
                    cyc = int((wx * 0.7 + wy * 0.3)) % len(HUE)
                    set_cell(cv, wx, wy, "\u2588", HUE[cyc], 0)

# --- rooftop ridge: the foreground platform ---------------------------------
def draw_ridge():
    for x in range(W):
        set_cell(cv, x, HORIZON + 1, "\u2580", 94, 0)   # top edge: bright rim
        for y in range(HORIZON + 2, H):
            set_cell(cv, x, y, "\u2593", 8, 0)           # body: dark ground

# --- the watchman v2: a real humanoid, backlit by the moon ------------------
# Figure is LARGER and lower-anchored than v1 so it READS FIRST as a person.
FX = 37                       # figure center x (foreground, in the clear-sky gap)
FEET = HORIZON + 1            # feet on the ridge top
HEAD_CY = FEET - 23           # head center -- up into the mid-sky
HEAD_R = 2.6

# A light function that falls across the FORM: bright on the moon-facing side, dark on
# the far side. We bias by horizontal distance to the moon so every part gets a rim read.
def L_form(x, y):
    # base diffuse from the moon
    L = light_field(x, y, LX, LY, lmax=30.0, ambient=0.18)
    # extra boost on the right (moon-facing) edge of the figure -> rim light
    dxr = x - FX
    if dxr > 0:
        L += 0.12 * min(1.0, dxr / 4.0)
    return max(0.0, min(1.0, L))

def in_ellipse(x, y, cx, cy, rx, ry):
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return False
    hw = rx * math.sqrt(1.0 - t * t)
    return abs(x - cx) <= hw

def draw_watchman():
    # --- HEAD: a shaded sphere (gradient-built, not a flat block) -----------
    def head_region(x, y):
        return in_ellipse(x, y, FX, HEAD_CY, HEAD_R, HEAD_R + 0.4)
    shade_region(cv, head_region, L_form, base_fg=8, hot_fg=15)

    # --- NECK: short shaded column -----------------------------------------
    for y in range(int(HEAD_CY + HEAD_R), int(HEAD_CY + HEAD_R + 2)):
        for x in range(FX - 1, FX + 2):
            ch, fg = shade(L_form(x, y), base_fg=8, hot_fg=15)
            set_cell(cv, x, y, ch, fg, 0)

    # --- TORSO: an HOURGLASS silhouette (wide shoulders -> pinched waist ->
    #    slight hip flare). The single most important fix vs v2: a standing
    #    human is NOT a trapezoid widening to the base (that reads as an
    #    obelisk/tower). Waist pinch + shoulder width are what make it read
    #    "person".
    sh_y = HEAD_CY + HEAD_R + 2             # shoulder line
    hip_y = FEET - 9                        # hip line

    def torso_hw(t):
        if t < 0.45:                       # shoulders -> waist (narrowing)
            return 3.2 - 1.6 * (t / 0.45)
        else:                              # waist -> hips (slight flare)
            u = (t - 0.45) / 0.55
            return 1.6 + 0.9 * u

    for y in range(int(sh_y), int(hip_y)):
        t = (y - sh_y) / max(1.0, (hip_y - sh_y))
        hw = torso_hw(t)
        for x in range(int(FX - hw), int(FX + hw) + 1):
            ch, fg = shade(L_form(x, y), base_fg=8, hot_fg=15)
            set_cell(cv, x, y, ch, fg, 0)

    # --- LEGS: two clearly SEPARATED columns from hips to feet --------------
    # Wider gap + narrower legs so two limbs read as two legs, not one column.
    for leg in (-1, +1):
        lx = FX + leg * 2.0
        for y in range(int(hip_y), int(FEET)):
            t = (y - hip_y) / max(1.0, (FEET - hip_y))
            hw = 1.0 - 0.35 * t             # taper to the foot
            for x in range(int(round(lx - hw)), int(round(lx + hw)) + 1):
                ch, fg = shade(L_form(x, y), base_fg=8, hot_fg=15)
                set_cell(cv, x, y, ch, fg, 0)
        fx_ = int(round(lx))               # foot cap landing on the ridge
        for dx in (-1, 0, 1):
            ch, fg = shade(L_form(fx_ + dx, FEET - 1), base_fg=8, hot_fg=15)
            set_cell(cv, fx_ + dx, FEET - 1, "\u2580", fg, 0)

    # --- REACHING ARM: a limb WITH WIDTH and an elbow bend toward the moon --
    # Two segments (upper arm shoulder->elbow + forearm elbow->hand), each a
    # thick shaded band so it reads as an arm reaching up-right, not a mast.
    sh_x, sh_y2 = FX + 1.5, sh_y + 0.5     # shoulder joint
    el_x, el_y = FX + 4.5, sh_y - 3.0      # elbow (up and out toward moon)
    hd_x, hd_y = FX + 7.5, sh_y - 6.5      # hand (reaching toward the moon disc)

    def arm_band(x0, y0, x1, y1, halfw):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 4
        for i in range(steps + 1):
            t = i / steps
            px = x0 + (x1 - x0) * t
            py = y0 + (y1 - y0) * t
            dx, dy = (x1 - x0), (y1 - y0)
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln      # perpendicular offset band
            for s in range(-int(halfw * 2), int(halfw * 2) + 1):
                bx = px + nx * s * 0.5
                by = py + ny * s * 0.5
                ch, fg = shade(L_form(bx, by), base_fg=8, hot_fg=15)
                set_cell(cv, int(round(bx)), int(round(by)), ch, fg, 0)

    arm_band(sh_x, sh_y2, el_x, el_y, 1.0)     # upper arm
    arm_band(el_x, el_y, hd_x, hd_y, 0.8)      # forearm (thinner, reaching)
    # a brighter hand catch-light on the moon side -- the reach LANDS in the glow
    hx_, hy_ = int(round(hd_x)), int(round(hd_y))
    for dx, dy in [(0, 0), (1, 0), (0, -1)]:
        set_cell(cv, hx_ + dx, hy_ + dy, "\u2588", 15, 0)

    # --- far-side arm: a short shaded stub so the figure isn't one-armed ----
    arm_band(FX - 1.5, sh_y + 0.5, FX - 3.0, hip_y - 1, 0.8)

    # --- EYE: a constructed socket/iris/glint catching the moon ------------
    eye(cv, FX + 0.6, HEAD_CY - 0.2, r=1.1, iris_fg=96, glint=True)


# --- assemble scene ----------------------------------------------------------
draw_skyline()
draw_ridge()
draw_moon()           # moon on top of the clear upper sky (nothing covers it)
draw_watchman()       # figure last: foreground, reads first

# --- frame + sig block (house standard) -------------------------------------
out = []
render(cv, out)
F.sig_block(out, TITLE, "raze / hollis")
with open(OUT, "w", encoding="cp437") as f:
    f.write("\n".join(out))
    f.write("\x1b[0m\n")
print("wrote", OUT)
