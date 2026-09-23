#!/usr/bin/env python3
# THE WATCHER v4 -- one eye lit out of the dark.
# Rebuilt to clear the flat-region gate: every lit surface is shaded by a
# DIRECTIONAL density falloff (dot of surface normal and light dir) mapped onto
# the block-density ramp via dither_region, so no single glyph level covers >40
# contiguous cells -- even the highlight core breaks up into ▓▒░ instead of
# saturating into one solid full-block patch.
import math
import canvas as C

W, H = 80, 46
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

# Light source: upper-left.
LX, LY = -0.6, -0.75          # light direction (pointing from surface toward light)
LN = math.hypot(LX, LY)
LX /= LN; LY /= LN

def orb_region(x, y):
    dx = x - 40.0; dy = y - 22.0
    return (dx*dx)/(34.0**2) + (dy*dy)/(34.0**2) <= 1.0

# Directional density: bright where the surface faces the light, dark on the
# far side. Continuous falloff -> no flat patch anywhere on the orb.
def orb_density(x, y):
    dx = x - 40.0; dy = y - 22.0
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx/r, dy/r
    dot = nx*LX + ny*LY            # -1..1
    d = 0.5 + 0.5*dot             # 0..1
    return max(0.0, min(1.0, d))

# Orb body: light-gray lit side -> black shadow, density-dithered across the disc.
C.dither_region(cv, orb_region, orb_density, fg=7, bg=0)

# Iris: smaller disc, cyan/magenta family, same directional light.
def iris_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(12.0**2) + (dy*dy)/(12.0**2) <= 1.0

def iris_density(x, y):
    dx = x - 40.0; dy = y - 23.0
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx/r, dy/r
    dot = nx*LX + ny*LY
    return max(0.0, min(1.0, 0.5 + 0.5*dot))

C.dither_region(cv, iris_region, iris_density, fg=6, bg=4)   # cyan lit -> blue shadow

# Pupil recess: dark disc, subtle depth ramp (not a flat black hole).
def pupil_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(5.0**2) + (dy*dy)/(5.0**2) <= 1.0

def pupil_density(x, y):
    dx = x - 40.0; dy = y - 23.0
    r = math.hypot(dx, dy)/5.0
    return max(0.0, min(1.0, 0.35 + 0.4*(1.0 - r)))   # faint rim, darker center

C.dither_region(cv, pupil_region, pupil_density, fg=4, bg=0)

# Glint: tiny bright spot on the lit side of the iris (small enough to not be a flat region).
for y in range(18, 22):
    for x in range(35, 39):
        if (x-36.5)**2 + (y-19.5)**2 <= 2.0**2:
            cv.set(x, y, C.RAMP[0], fg=15, bg=0)

# Background atmosphere: sparse starfield behind the orb (negative space, not subject).
def bg_region(x, y):
    dx = x - 40.0; dy = y - 22.0
    return not ((dx*dx)/(36.0**2) + (dy*dy)/(36.0**2) <= 1.0)
C.texture_fill(cv, bg_region, fg=5, bg=0, density=0.06, seed=7)

# Frame: title card up top.
cv.set_row = None
out = []
# top border + title line (drawn as text rows above the canvas render)
top = [C.sgr(13) + "\u2550"*W]
def sigline(text, fg):
    pad = max(0, W - len(text)); left = pad//2; right = pad-left
    return C.sgr(12) + " "*left + C.sgr(fg) + text + C.sgr(12) + " "*right
top.append(sigline("THE WATCHER", 5))

cv.render(out)
# bottom border
out.append(C.sgr(13) + "\u2550"*W)

full = top + out
C.write_ans('scratch/_watcher.v4.ans', full, title='THE WATCHER', handles='raze,hollis')
