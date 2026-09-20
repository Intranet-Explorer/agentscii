#!/usr/bin/env python3
# EMBER CROWD v9 -- direct hand-placed pass via house canvas.py primitives.
# Fixes v8's bug (space+fg shows no color -> sky bands were invisible): warm sky
# bands are now bg-colored fields. Crowd is a bumpy black MASS of shoulders/heads
# with a warm backlit rim, sitting on the horizon; sun disc clearly ABOVE it.
import sys
sys.path.insert(0, 'scratch')
import canvas as C

W, H = 80, 40
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=0, fill_bg=0)    # black void base

# ---- SKY: clean solid warm bands as bg-colored fields (top->bottom dusk) ----
# bright ANSI indices (8+base): 91 red, 93 yellow, 95 magenta, 94 blue, 103 amber
bands = [
     (0,  9,  94),     # deep night -- dim blue field
     (9, 14,  95),     # violet/magenta band
      (14, 18,  91),   # crimson band
      (18, 22, 103),   # amber/orange near horizon (warmest)
]
for y0, y1, fg in bands:
    for y in range(y0, min(y1, H)):
        C.rect(cv, 0, y, W - 1, y, ch=' ', fg=fg, bg=fg)   # solid colored field

# ---- SUN: solid bright disc clearly ABOVE the crowd top (crowd top ~ row 22) ----
C.ellipse(cv, 40, 17, 5, 3, ch='\u2588', fg=15, bg=0, fill=True)    # white-hot core
C.ellipse(cv, 40, 17, 7, 4, ch='\u2593', fg=14, bg=0, fill=False)   # amber halo ring

# ---- CROWD: bumpy black MASS of shoulders/heads on the horizon ----
horizon = 22
# head-line profile: shoulders (wide dips) with occasional taller head bumps
def top_at(x):
    base = horizon
    shoulder = (x // 4) % 3            # 0,1,2 repeating -> bumpy shoulder line
    t = base - (shoulder == 0)        # dip down on shoulders
    if x % 6 in (2, 3):               # a head rises every ~6 cols
        t -= 1
    return int(t)

for x in range(W):
    top = top_at(x)
    for y in range(top, H):
        cv.cells[y][x] = ['\u2588', 0, 0]      # solid black mass

# ---- backlit RIM: warm line on the very top edge of the crowd ----
for x in range(W):
    top = top_at(x)
    if 0 <= top < H:
        cv.cells[top][x] = ['\u2588', 93, 0]   # amber rim catching shoulders/heads

out = []
cv.render(out)
C.write_ans('scratch/_ember_crowd_v9.ans', out, title='EMBER CROWD v1.0', handles='raze')
