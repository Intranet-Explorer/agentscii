#!/usr/bin/env python3
# THE WATCHER v5 -- one eye lit out of the dark.
# Flat-region fix: directional density is COMPRESSED so the lit side sits in
# mid-density (▓▒) with only a small highlight core reaching full-block, and every
# sub-form (iris, pupil) carries genuine multi-level dither. No single glyph level
# covers >40 contiguous cells anywhere on the subject.
import math
import canvas as C

W, H = 80, 46
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

LX, LY = -0.6, -0.75           # light direction (toward the light), upper-left
LN = math.hypot(LX, LY); LX /= LN; LY /= LN

def orb_region(x, y):
    dx = x - 40.0; dy = y - 22.0
    return (dx*dx)/(34.0**2) + (dy*dy)/(34.0**2) <= 1.0

def orb_density(x, y):
    dx = x - 40.0; dy = y - 22.0
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx/r, dy/r
    dot = nx*LX + ny*LY                       # -1..1
    t = 0.5 + 0.5*dot                          # 0..1 (lit->shadow)
    # compress: lit side -> mid density (▓/▒), only a tight core near the light hits █
    d = 0.18 + 0.62 * (t ** 1.7)
    return max(0.0, min(1.0, d))

C.dither_region(cv, orb_region, orb_density, fg=7, bg=0)

def iris_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(12.0**2) + (dy*dy)/(12.0**2) <= 1.0

def iris_density(x, y):
    dx = x - 40.0; dy = y - 23.0
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx/r, dy/r
    dot = nx*LX + ny*LY
    t = 0.5 + 0.5*dot
    d = 0.22 + 0.6 * (t ** 1.6)               # cyan lit -> blue shadow, compressed
    return max(0.0, min(1.0, d))

C.dither_region(cv, iris_region, iris_density, fg=6, bg=4)

def pupil_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(5.0**2) + (dy*dy)/(5.0**2) <= 1.0

def pupil_density(x, y):
    # genuine depth ramp: lit rim -> dark center, multi-level (no flat black hole)
    dx = x - 40.0; dy = y - 23.0
    r = math.hypot(dx, dy)/5.0
    d = 0.15 + 0.7*(1.0 - r)
    return max(0.0, min(1.0, d))

C.dither_region(cv, pupil_region, pupil_density, fg=4, bg=0)

# Glint: tiny bright spot on the lit side of the iris (small, not a flat region).
for y in range(18, 22):
    for x in range(35, 39):
        if (x-36.5)**2 + (y-19.5)**2 <= 1.8**2:
            cv.set(x, y, C.RAMP[0], fg=15, bg=0)

# Background atmosphere behind the orb (negative space).
def bg_region(x, y):
    dx = x - 40.0; dy = y - 22.0
    return not ((dx*dx)/(36.0**2) + (dy*dy)/(36.0**2) <= 1.0)
C.texture_fill(cv, bg_region, fg=5, bg=0, density=0.06, seed=7)

out = []
top = [C.sgr(13) + "\u2550"*W]
def sigline(text, fg):
    pad = max(0, W - len(text)); left = pad//2; right = pad-left
    return C.sgr(12) + " "*left + C.sgr(fg) + text + C.sgr(12) + " "*right
top.append(sigline("THE WATCHER", 5))
cv.render(out)
out.append(C.sgr(13) + "\u2550"*W)
full = top + out
C.write_ans('scratch/_watcher.v5.ans', full, title='THE WATCHER', handles='raze,hollis')
