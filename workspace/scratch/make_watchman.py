#!/usr/bin/env python3
# make_watchman.py -- AGENTSCII (raze)
#
# WATCHMAN -- a character-IN-SCENE: a lone sentinel on a rooftop ridge at night,
# lit by one moon that also lights the cityscape behind him. The catalog has solo
# busts and diptychs but no figure standing *inside an environment*.
#
# LESSON from v1/v2: filling every cell with color reads as ACiD NOISE, not a scene.
# Real night scenes (railyard) use mostly BLACK with sparse bright elements. So:
#   - sky: black, with stars and a moon glow only near the disc
#   - buildings: dark gray silhouettes, lit windows are sparse bright cells
#   - watchman: a dark figure with a bright rim-light on the moon-facing edge
#   - color-cycling lives in lit windows + the rim, not as a fill

import math
import figure_common as F
from figure_common import (new_canvas, set_cell, eye, render, c, RAMP, HUE, W, H)

OUT = "scratch/raze-watchman.ans"
TITLE = "WATCHMAN -- AGENTSCII character-in-scene v1.0"

cv = new_canvas(H, W)   # all cells start as [' ', 0, 0] = black

# --- the moon: one bright disc upper-right ----------------------------------
LX, LY = 62.0, 7.0
MOON_R = 4.0

def draw_moon():
    for y in range(int(LY - MOON_R - 3), int(LY + MOON_R + 4)):
        for x in range(int(LX - MOON_R - 3), int(LX + MOON_R + 4)):
            d = math.hypot(x - LX, y - LY)
            if d <= MOON_R:
                inner = 1.0 - (d / MOON_R) * 0.35
                set_cell(cv, x, y, "\u2588", 15 if inner > 0.7 else 93, 0)
            elif d <= MOON_R + 2.0:
                a = 1.0 - (d - MOON_R) / 2.0
                set_cell(cv, x, y, RAMP[2] if a > 0.5 else " ", 93, 0)

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
        # body: dark gray silhouette
        for y in range(top, HORIZON):
            for x in range(bx, bx + bw):
                set_cell(cv, x, y, "\u2591", 8, 0)   # dark gray (dim white = gray)
        # roof cap: thin bright line
        for x in range(bx, bx + bw):
            set_cell(cv, x, top, "\u2580", 97, 0)
        # lit windows: sparse, only on the moon-facing side, cycling color
        for wy in range(top + 2, HORIZON - 1, 3):
            for wx in range(bx + 1, bx + bw - 1, 2):
                if dist_moon(wx, wy) < 28:
                    cyc = int((wx * 0.7 + wy * 0.3)) % len(HUE)
                    set_cell(cv, wx, wy, "\u2588", HUE[cyc], 0)

# --- rooftop ridge: the foreground platform ---------------------------------
def draw_ridge():
    for x in range(W):
        # top edge: bright rim
        set_cell(cv, x, HORIZON + 1, "\u2580", 94, 0)
        # body: dark ground
        for y in range(HORIZON + 2, H):
            set_cell(cv, x, y, "\u2593", 8, 0)

# --- the watchman: a standing figure on the ridge, rim-lit by the moon ------
FX = 40
FEET = HORIZON + 1
HEAD_CY = FEET - 22

FX = 40                 # figure center x (foreground)
RIDGE_TOP = HORIZON + 1 # stands on the ridge top

def draw_watchman():
     # A LARGE foreground humanoid silhouette, backlit by the moon. Solid dark body
     # with a bright rim on the moon-facing edge -- reads as a person, not a streak.
    feet = RIDGE_TOP
    head_top = feet - 20
    neck_y = feet - 16
    hip_y = feet - 8
     # --- legs: two tapered columns from hips to feet ---
    for y in range(hip_y, feet):
        t = (y - hip_y) / (feet - hip_y)
        lw = 1.0 + 0.6 * t                 # left leg half-width
        rw = 1.0 + 0.6 * t
        for x in range(int(FX - 2 - lw), int(FX - 1)):   # left leg
            set_cell(cv, x, y, "\u2588", 8, 0)
        for x in range(int(FX + 1), int(FX + 2 + rw)):   # right leg
            set_cell(cv, x, y, "\u2588", 8, 0)
     # --- torso: a tapered block from hips up to the shoulders ---
    for y in range(neck_y, hip_y):
        t = (y - neck_y) / (hip_y - neck_y)
        halfw = 3.0 + 2.0 * t              # narrow at shoulders, wider at hips
        for x in range(int(FX - halfw), int(FX + halfw) + 1):
            set_cell(cv, x, y, "\u2593", 8, 0)
     # --- shoulders: a wide bright-rimmed band ---
    for x in range(int(FX - 4), int(FX + 5)):
        set_cell(cv, x, neck_y, "\u2593", 8, 0)
     # --- head: a solid dark disc above the shoulders ---
    hr = 3.0
    hcy = head_top + hr
    for y in range(int(hcy - hr), int(hcy + hr) + 1):
        t = (y - hcy) / hr
        if abs(t) > 1.0: continue
        hw = hr * math.sqrt(1.0 - t * t)
        for x in range(int(FX - hw), int(FX + hw) + 1):
            set_cell(cv, x, y, "\u2593", 8, 0)
     # --- a raised arm reaching up toward the moon (the watchman's pose) ---
    for i in range(9):
        ax = int(FX + 3 + i * 0.4)
        ay = int(neck_y - 1 - i)
        set_cell(cv, ax, ay, "\u2593", 8, 0)
     # --- bright rim-light on the moon-facing (right) edge of the whole figure ---
    for y in range(int(hcy - hr), feet):
        t = (y - neck_y) / (hip_y - neck_y) if neck_y <= y < hip_y else 1.0
        halfw = 3.0 + 2.0 * max(0.0, min(1.0, t))
        rx = int(FX + halfw)
        if 0 <= rx < W:
            set_cell(cv, rx, y, "\u2588", 97, 0)
     # a glint in the eye area (the watchman sees the moon)
    set_cell(cv, int(FX + 1), int(hcy - 1), "\u2588", 96, 0)

# --- assemble scene ----------------------------------------------------------
draw_skyline()
draw_ridge()
draw_moon()          # moon on top of the clear upper sky (nothing covers it)
draw_watchman()

# --- frame + sig block (house standard) -------------------------------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

title = "WATCHMAN // one light, two figures of the night"
out.append(c(97, 40) + " " + c(104, 40) + title + c(104, 40) + " " * (W - len(title) - 1))
out += [c(104, 40) + "\u2550" * W]

def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    return c(104, 40) + " " * left + c(fg, 40) + text + c(104, 40) + " " * (pad - left)

out.append(sigline("raze / AGENTSCII", 97))
out.append(sigline(TITLE, 96))
out.append(c(105, 40) + "\u2563" + c(104, 40) + "\u2550" * (W - 1))

with open(OUT, "w", encoding="cp437") as f:
    f.write("\n".join(out) + "\n\x1b[0m\n")

print("wrote", OUT, len(out), "lines")
F.hygiene_gate(OUT)
