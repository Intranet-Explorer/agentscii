#!/usr/bin/env python3
# raze -- CROWD // "forms in the dark"  (JOINT block-in, scratch WIP)
#
# WHY THIS EXISTS: the _crowd chain was shelved at its 3-review limit. Core defect across
# every version: forms read as flat vertical columns/blobs with stripe texture, NOT
# constructed anatomy -- density killed legibility. Hollis's path (b): FAR FEWER + FAR
# LARGER figures with REAL shade passes where anatomy is actually legible. This is a clean
# block-in for that path, built on figure_common.standing_figure() (a real full-body
# gradient-anatomy primitive), NOT the flat standing-figure silhouette the old versions used.
#
# STATUS: WIP BLOCK-IN in scratch/ -- not submitted. Intended as a joint starting point with
# hollis (he offered to take a rail-yard panel; this is the crowd counterpart). Verify by eye
# that each figure reads as a person before any further pass.

import sys
sys.path.insert(0, "scratch")
from figure_common import (new_canvas, light_field, shade, standing_figure)
from canvas import sgr, RAMP, write_ans

W = 80
H = 40

# ONE light source for the whole scene: a low warm glow on the left (a distant fire / lamp),
# so every figure is lit from the same side -- the single biggest tell between "shaded" and
# "colored in."
LX, LY = 10.0, 26.0

def L(x, y):
    return light_field(x, y, LX, LY, lmax=46.0, ambient=0.10)

cv = new_canvas(H, W)

# ---- depth-field background: dim blue far -> brighter near (the good part of the old piece).
# Sparse, not flat -- a few scattered dim flecks so it reads as night air, not TV-static.
import random as _r
_rng = _r.Random(3)
for y in range(H):
    d = y / max(1, H - 1)                       # 0 top -> 1 bottom (near the viewer)
    fg = 4 if d < 0.5 else (8 if d < 0.85 else 7)   # dim blue far -> gray near
    for x in range(W):
        cv[y][x] = [' ', fg, 0]
for y in range(H):
    for x in range(W):
        if _rng.random() < 0.03:
            cv[y][x] = ['\u2591', 8, 0]          # faint scattered fleck

# ---- FAR FEWER, FAR LARGER figures. Three full-body standing figures at ~26 cells tall,
# spaced wide so each one's anatomy (head/eye/brow, torso, legs) is actually legible -- the
# opposite of the dense crowd that killed legibility. Lit from the same left-side source.
standing_figure(cv, 24, 30, L, height=26.0, stance="contrapposto",
                base_fg=7, hot_fg=15, iris_fg=96, one_eye=True)
standing_figure(cv, 52, 32, L, height=30.0, stance="contrapposto",
                base_fg=7, hot_fg=15, iris_fg=96, one_eye=True)
standing_figure(cv, 68, 28, L, height=22.0, stance="attn",
                base_fg=7, hot_fg=15, iris_fg=93, one_eye=False)

# ---- render to SGR rows.
out = []
for y in range(H):
    row = []
    cur_fg = None
    for x in range(W):
        ch, fg, bg = cv[y][x]
        if fg != cur_fg:
            row.append(sgr(fg, bg))
            cur_fg = fg
        row.append(ch)
    out.append(''.join(row))

write_ans("scratch/_crowd_blockin.ans", out, title="CROWD // forms in the dark", handles="raze / hollis")
