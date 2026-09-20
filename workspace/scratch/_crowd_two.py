#!/usr/bin/env python3
# raze -- CROWD legibility test v2: 2 figures, bigger heads (head_scale), STRONGER directional
# contrast (low ambient so shadowed sides fall to near-black -> reads as lit 3D volume not flat gray).
import sys
sys.path.insert(0, "scratch")
from figure_common import new_canvas, light_field, standing_figure, sgr
from canvas import write_ans

W = 80; H = 46
cv = new_canvas(H, W)

# dim blue far -> gray near depth field
import random as _r
_rng = _r.Random(7)
for y in range(H):
    d = y / max(1, H - 1)
    fg = 4 if d < 0.5 else (8 if d < 0.85 else 7)
    for x in range(W):
        cv[y][x] = [' ', fg, 0]
for y in range(H):
    for x in range(W):
        if _rng.random() < 0.02:
            cv[y][x] = ['\u2591', 8, 0]

def fig_light(fx, fy, lmax=16.0, ambient=0.10):
    lx = fx - 8.0; ly = fy + 4.0   # lamp low-left of each figure
    return lambda x, y: light_field(x, y, lx, ly, lmax=lmax, ambient=ambient)

# TWO figures, big heads (1.5), strong pose contrast, LOW ambient for real lit/shadow volume:
standing_figure(cv, 26, 30, fig_light(26, 30), height=30.0, stance="contrapposto",
                base_fg=8, hot_fg=15, iris_fg=93, one_eye=True, head_scale=1.5)
standing_figure(cv, 54, 32, fig_light(54, 32), height=27.0, stance="contrapposto",
                base_fg=8, hot_fg=15, iris_fg=93, one_eye=False, head_scale=1.5)

# frame + title card (Pass 6)
def setc(x, y, ch, fg, bg=0):
    if 0 <= x < W and 0 <= y < H: cv[y][x] = [ch, fg, bg]
for x in range(W): setc(x, 0, "\u2584", 13, 0)
for x in range(W):
    setc(x, H - 3, "\u2550", 13, 0); setc(x, H - 2, "\u2550", 8, 0)
for y in range(1, 6):
    for x in range(1, 24):
        if x == 1 or x == 23 or y == 1 or y == 5:
            setc(x, y, "\u2502" if x in (1, 23) else "\u2500", 8, 0)
for i, ch in enumerate("C R O W D"):
    setc(4 + i * 3, 3, ch, 14, 0)

out = []
for y in range(H):
    row = []; cur_fg = None
    for x in range(W):
        ch, fg, bg = cv[y][x]
        if fg != cur_fg:
            row.append(sgr(fg, bg)); cur_fg = fg
        row.append(ch)
    out.append(''.join(row))
write_ans("_crowd_two.ans", out, title="CROWD // two forms in the dark", handles="raze / hollis")
print("wrote _crowd_two.ans")
