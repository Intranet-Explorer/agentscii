#!/usr/bin/env python3
# _reactor.py -- raze solo. THE REACTOR // "a fusion vessel, lit from its own core."
#
# PROVENANCE / WHY NEW: GHOST ENGINE (pack41) proved the bilateral-mirror + industrial
# register works and is NEW to the house; hollis flagged "a mirror-symmetric machine/
# structure in a DIFFERENT register" as wide open. This takes that exact signature move
# -- build the LEFT half, C.mirror(cv,'v'), radial light from the core -- but breaks it on
# two axes so it's not a reskin of GHOST ENGINE:
#   (1) VERTICAL architecture vs GHOST ENGINE's HORIZONTAL twin-cylinder layout. A tall
#       containment vessel + a vertical stack of cooling fins, not flanking cylinders.
#   (2) HOT plasma palette -- amber/red/white-hot core with a cool cyan glass sheen as the
#       rare accent -- vs GHOST ENGINE's blue-steel body / cyan valve rings.
#
# SIGNATURE MOVE: paint x < MID only, mirror(axis='v') copies it right -> perfect bilateral
# symmetry for free (ACiDDraw's mirror tool). Light is RADIAL from the plasma core (CX,CORE_Y)
# so the whole vessel glows out of black and the falloff reads as a lit mass, not flat blocks.
#
# PASSES (METHODOLOGY): P1 flat silhouettes -> verify massing; P2 radial shade every surface
# from the ONE core source; P3 constructed accents (plasma column, valve ports, glass sheen);
# P4 texture the void around the vessel; P5 frame.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, RAMP, write_ans
from figure_common import light_field, shade, c, c_bright, RESET

W, H = 80, 52
cv = Canvas(W, H)
CX = W / 2.0
MID = W // 2
SEED = 7
random.seed(SEED)

# plasma core: the light source + center of mass (slightly above mid so the vessel reads tall)
CORE_X, CORE_Y = CX, 25.0
LX, LY = CORE_X, CORE_Y           # ONE radial source for the whole piece

def L(x, y):
    return light_field(x, y, LX, LY, lmax=34.0, ambient=0.10)

# ---- P1: silhouette region functions (the ANATOMY as massing), LEFT HALF ONLY --
# Everything is defined for x < MID; mirror() handles the right side.

def vessel(x, y):
     # the containment chamber: a tall vertical capsule (two rounded ends + straight sides)
    cy = CORE_Y
    ry = 17.0          # half-height of the rounded end
    rx = 8.5           # half-width of the body
    top_cap = cy - ry
    bot_cap = cy + ry
    if y < top_cap or y > bot_cap:
        return False
    if top_cap <= y <= bot_cap:
        # straight-sided mid-section
        return abs(x - CX) <= rx
    t = (y - cy) / ry
    hw = rx * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw

def plasma(x, y):
     # the hot column up the spine: a thin bright core running vertically through the vessel
    cy = CORE_Y
    ry = 15.0
    if (y - cy) / ry < -1.0 or (y - cy) / ry > 1.0:
        return False
    t = (y - cy) / ry
    # narrow at the ends, slightly wider through the middle -- a lens/column of light
    hw = 2.4 * math.sqrt(max(0.0, 1.0 - t * t)) + 0.8
    return abs(x - CX) <= hw

def fins(x, y):
     # a vertical stack of cooling-fins radiating outward from the vessel at several heights.
     # Bilateral plates: each fin is a horizontal bar anchored to the vessel wall, tapering out.
    cy = CORE_Y
    ry = 15.0
    if (y - cy) / ry < -1.0 or (y - cy) / ry > 1.0:
        return False
    # fin rows at fixed heights; each is a thin band that extends outward from the vessel wall
    fin_ys = [CORE_Y + k * 4.5 for k in range(-3, 4)]   # 7 fins stacked vertically
    for k, fy in enumerate(fin_ys):
        if abs(y - fy) <= 0.8:
            inner = 6.0
            # stagger the fin lengths so the stack reads as a real cooling-rack, not a ladder
            outer = 17.0 - (k % 2) * 3.5
            if inner <= abs(x - CX) <= outer:
                return True
    return False

def base(x, y):
     # the wide trapezoidal pedestal the vessel is bolted to (the "floor")
    cy = CORE_Y + 18.5
    t = (y - cy) / 4.5
    if abs(t) > 1.0:
        return False
    hw = 24.0 * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

def dome(x, y):
     # the rounded cap / valve housing at the very top of the vessel
    cy = CORE_Y - 17.0
    d = math.hypot(x - CX, y - cy)
    return d <= 4.2

def ports(x, y):
     # a ring of valve ports around the mid-vessel (industrial detail, discrete marks)
    d = math.hypot(x - CX, y - CORE_Y)
    if 9.0 <= d <= 10.5:
        ang = math.atan2(y - CORE_Y, x - CX)
        return abs(math.sin(ang * 8.0)) < 0.30   # discrete ports around the ring
    return False

# ---- P1: paint flat silhouettes (dim gray, unlit) to verify massing ----------
def paint_flat(region_fn, fg=8):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                cv.set(x, y, "\u2588", fg, 0)

paint_flat(vessel, fg=9)
paint_flat(fins, fg=8)
paint_flat(dome, fg=10)
paint_flat(base, fg=7)
paint_flat(ports, fg=11)
paint_flat(plasma, fg=15)

# ---- P2: radial shade every lit surface from the ONE core source -------------
def shade_region(region_fn, base_fg, hot_fg):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                ch, fg = shade(L(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

shade_region(vessel, base_fg=3, hot_fg=7)            # chamber: glowing AMBER body (3), white-hot near core (7)
shade_region(fins, base_fg=4, hot_fg=6)              # fins: cool BLUE plates (4), cyan sheen near core (6) -- cold contrast
shade_region(dome, base_fg=3, hot_fg=7)              # cap: warm amber housing (3), white at the top seam (7)
shade_region(base, base_fg=8, hot_fg=8)              # pedestal: dim gray floor, recedes into void

# ---- P3: constructed bright accents ------------------------------------------
# plasma column: white-hot heart with amber falloff -- the reactor's core, drawn on top
for y in range(H):
    for x in range(MID):
        if plasma(x, y):
            d = math.hypot(x - CX, y - CORE_Y)
            Lc = light_field(x, y, LX, LY, lmax=10.0, ambient=0.2)
            ch, fg = shade(Lc, base_fg=3, hot_fg=7)    # amber body (3) -> white at the very center (7)
            cv.set(x, y, ch, fg, 0)
            if abs((y - CORE_Y)/15.0) > 0.80:    # red-hot tips where the column cools off
                cv.set(x, y, ch, 1, 0)

# valve ports: cyan glass sheen (the rare cool accent against the warm vessel)
for y in range(H):
    for x in range(MID):
        if ports(x, y):
            cv.set(x, y, "\u2593", 6, 0)

# P3b: specular sheen down each fin's light-facing (inner/core-facing) edge so fins read as
# PLATES catching the core light, not flat bars. Light is at the core, so the lit side faces in.
for fy in [CORE_Y + k * 4.5 for k in range(-3, 4)]:
    for t in [i / 10.0 for i in range(11)]:
        px = CX + (22.0 - t * 16.0)      # inner->outer along the fin
        py = fy
        cv.set(int(px), int(py), "\u2588", 6, 0)       # cyan sheen stripe on the core-facing edge

# core bloom: a faint ring of light around the plasma heart so it glows, not just dots
for y in range(H):
    for x in range(MID):
        d = math.hypot(x - CX, y - CORE_Y)
        if 2.6 < d <= 4.4:
            cv.set(x, y, "\u2592", 6, 0)

# ---- MIRROR: the signature move -- copy left half onto right -----------------
mirror(cv, axis='v')

# ---- P4: texture the void around the mass (not flat black) -------------------
def in_mass(x, y):
    return (vessel(x, y) or fins(x, y) or dome(x, y)
            or base(x, y) or ports(x, y) or plasma(x, y))

# P4a: gray heat-shimmer dust far out (the chamber's atmosphere), not flat black -- two
# density layers of varied glyphs so the void reads as a textured field, not empty space.
texture_fill(cv, lambda x, y: not in_mass(x, y), fg=8, density=0.30, seed=SEED + 1)
for y in range(H):
    for x in range(MID):
        if in_mass(x, y):
            continue
        d = math.hypot(x - CX, y - CORE_Y)
        # P4b: radial energy bloom -- cool cyan near the core thinning to gray at the edges,
        # so it glows OUT of the dark instead of sitting in near-empty space (GHOST ENGINE move).
        if 4.4 < d <= 30.0:
            Lb = light_field(x, y, LX, LY, lmax=30.0, ambient=0.06)
            p = Lb * 0.55 if d < 12 else Lb * 0.30      # denser near the core, sparse far out
            if random.random() < p:
                ch = "\u2591" if d < 14 else ("\u2592" if random.random() < 0.4 else "\u2591")
                cv.set(x, y, ch, 6 if d < 8 else (7 if d < 14 else 8), 0)

# ---- P5: frame + title card --------------------------------------------------
out = []
out.append(c(13) + "\u2554" * W)          # top rule
cv.render(out)                              # body rows appended in place
out.append(c(13) + "\u2557" * W)           # bottom rule

write_ans("_reactor.ans", out, title="THE REACTOR v1.0", handles="raze", add_sig=True)
