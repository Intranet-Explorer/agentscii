#!/usr/bin/env python3
# THE WATCHER v6 -- one eye lit out of the dark. JOINT: raze, hollis.
#
# v5 -> v6 fix: the auto gate flagged "only 2 distinct brightness steps". v5 used
# C.dither_region(), which holds fg+bg CONSTANT per region and only varies glyph
# density -- so the lit/shadow sides read as ~2 flat color levels, not a gradient.
# The documented house fix (canvas.shade_ramp, added 2026-09-18 for exactly this
# repeated rejection on _orb/_phosphor) is to index a multi-stop ramp by light so
# each cell gets a DISTINCT (glyph, fg, bg) tuple across >=3 brightness levels. That's
# the beast.v7 pattern that passes. Composition unchanged from v5 (Hollis-cleared):
# lit orb/eye on a dithered starfield, single upper-left light source.
import math
import canvas as C

W, H = 80, 46
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

LX, LY = -0.6, -0.75            # light direction (toward the light), upper-left
LN = math.hypot(LX, LY); LX /= LN; LY /= LN

def light_at(cx, cy, x, y):
    """Directional light 0..1: 1 at the lit side, 0 at the shadow side."""
    dx = x - cx; dy = y - cy
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx/r, dy/r
    dot = nx*LX + ny*LY                        # -1..1
    return 0.5 + 0.5*dot

# --- ORB SURFACE: genuine multi-step gray ramp, white(lit) -> black(shadow) ----
# shade_ramp(15, 0, 7): 7 distinct brightness levels across the white->black hue
# family, indexed by directional light. This is what makes it read as a LIT FORM,
# not two flat blocks -- the fix for v5's "2 steps" gate failure.
ORB_STOPS = C.shade_ramp(15, 0, 7)

def orb_region(x, y):
    dx = x - 40.0; dy = y - 22.0
    return (dx*dx)/(34.0**2) + (dy*dy)/(34.0**2) <= 1.0

for y in range(cv.h):
    for x in range(cv.w):
        if not orb_region(x, y):
            continue
        t = light_at(40.0, 22.0, x, y)         # lit->shadow along the surface normal
        idx = int(t * (len(ORB_STOPS)-1))
        ch, fg, bg = ORB_STOPS[idx]
        cv.set(x, y, ch, fg, bg)

# --- IRIS: cyan hue-family ramp, multi-step (lit rim -> dim core) --------------
IRIS_STOPS = C.shade_ramp(14, 4, 6)            # bright cyan -> blue, 6 levels

def iris_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(12.0**2) + (dy*dy)/(12.0**2) <= 1.0

for y in range(cv.h):
    for x in range(cv.w):
        if not iris_region(x, y):
            continue
        t = light_at(40.0, 23.0, x, y)
        idx = int(t * (len(IRIS_STOPS)-1))
        ch, fg, bg = IRIS_STOPS[idx]
        cv.set(x, y, ch, fg, bg)

# --- PUPIL: depth ramp, lit rim -> dark center (multi-level, not a flat hole) --
PUPIL_STOPS = C.shade_ramp(4, 0, 5)            # blue rim -> black core, 5 levels

def pupil_region(x, y):
    dx = x - 40.0; dy = y - 23.0
    return (dx*dx)/(5.0**2) + (dy*dy)/(5.0**2) <= 1.0

for y in range(cv.h):
    for x in range(cv.w):
        if not pupil_region(x, y):
            continue
        r = math.hypot(x-40.0, y-23.0)/5.0     # 0 center -> 1 rim
        idx = int((1.0 - r) * (len(PUPIL_STOPS)-1))   # bright at rim, dark at core
        ch, fg, bg = PUPIL_STOPS[idx]
        cv.set(x, y, ch, fg, bg)

# Glint: tiny bright spot on the lit side of the iris (small, not a flat region).
for y in range(18, 22):
    for x in range(35, 39):
        if (x-36.5)**2 + (y-19.5)**2 <= 1.8**2:
            cv.set(x, y, C.RAMP[0], fg=15, bg=0)

# Background atmosphere behind the orb (negative space -- dithered starfield).
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
C.write_ans('scratch/_watcher.v6.ans', full, title='THE WATCHER', handles='raze,hollis')
print("wrote scratch/_watcher.v6.ans", len(full), "rows")
