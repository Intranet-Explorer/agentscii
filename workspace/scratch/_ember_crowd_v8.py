#!/usr/bin/env python3
# EMBER CROWD v8 -- direct hand-placed pass via house canvas.py primitives.
# Accepts the 16-color medium ceiling (per _ember_crowd.note.txt): a few SOLID warm
# sky bands (dusk atmosphere, not a smooth gradient), a sun disc clearly ABOVE the
# crowd silhouette so the backlit read lands, a clean stepped black row of
# shoulders/heads sitting on the horizon, NO ground band (drop it -- cleaner).
import sys
sys.path.insert(0, 'scratch')
import canvas as C

W, H = 80, 40
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=0, fill_bg=0)   # black void base

# ---- SKY: clean solid warm bands, top->bottom dusk ----
# bright ANSI indices (8+base): 91 red, 93 yellow, 107 white, 95 magenta, 94 blue, 96 cyan
bands = [
     (0,  8,  94),    # deep night -- dim blue (bright-blue reads as the darkest cool we have)
     (8,  13, 95),    # violet/magenta band
     (13, 17, 91),    # crimson
     (17, 20, 103),   # amber/orange near horizon (bright amber = warmest)
]
for y0, y1, fg in bands:
    for y in range(y0, min(y1, H)):
        C.rect(cv, 0, y, W - 1, y, ch=' ', fg=fg, bg=0)

# ---- SUN: solid bright disc clearly ABOVE the crowd top (crowd top ~ row 21) ----
C.ellipse(cv, 40, 16, 5, 3, ch='\u2588', fg=15, bg=0, fill=True)   # white-hot core
C.ellipse(cv, 40, 16, 7, 4, ch='\u2593', fg=14, bg=0, fill=False)  # amber halo ring

# ---- CROWD: clean stepped black silhouette of shoulders/heads on the horizon ----
horizon = 21
for x in range(W):
    # bumpy head-line: alternating shoulder dips + occasional head bumps
    step = (x // 3) % 2
    top = horizon - (1 if step else 0)
    # every ~5th column rises a head bump
    if x % 5 == 2:
        top -= 1
    for y in range(top, H):
        cv.cells[y][x] = ['\u2588', 0, 0]   # solid black mass

# ---- backlit RIM: a thin warm line on the very top edge of the crowd ----
for x in range(W):
    step = (x // 3) % 2
    top = horizon - (1 if step else 0)
    if x % 5 == 2:
        top -= 1
    if 0 <= top < H:
        cv.cells[top][x] = ['\u2588', 93, 0]   # amber rim catching the shoulders

out = []
cv.render(out)
C.write_ans('scratch/_ember_crowd_v8.ans', out, title='EMBER CROWD v1.0', handles='raze')
