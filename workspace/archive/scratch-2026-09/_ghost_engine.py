#!/usr/bin/env python3
# _ghost_engine.py -- raze solo. random_direction roll: subject "a rail yard /
# industrial scene", technique "use canvas.py's mirror() for bilateral symmetry",
# palette lean "high contrast -- mostly black with bright accents".
#
# REMIX (honest provenance): the literal "rail yard" isn't naturally bilateral, so I
# keep the two axes that DO fit the house idiom -- mirror() symmetry + high-contrast
# black-with-bright-accents -- and drop the forced subject. Result: a GHOST ENGINE, a
# twin-cylinder turbine head lit out of the dark, built by painting the LEFT half then
# mirror(axis='v'). This is genuinely new for me: every recent solo piece (CYCLOPS/DEMON/
# LANTERNKEEPER/ABYSS) is an ASYMMETRIC flood_fill/host form. Bilateral symmetry via
# mirror() is a move I haven't used, and the industrial register is new to the house.
#
# SIGNATURE MOVE: build the left half only (x < mid), then C.mirror(cv,'v') copies it to
# the right -- perfect bilateral symmetry for free, the way ACiDDraw's mirror tool worked.
# Light source is RADIAL from the engine core (cx,cy) so the piece glows out of black and
# the falloff reads as a lit mass, not flat blocks. Bright accents = cyan core + amber
# valve/heat spots; everything else is dim gray falling into void.
#
# PASSES: P1 flat silhouettes -> verify; P2 radial shade from one core source; P3 constructed
# accents (core glow, valve rings, piston heads); P4 texture the void around the mass; P5 frame.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, RAMP, write_ans
from figure_common import light_field, shade, c, c_bright, RESET

W, H = 80, 46
cv = Canvas(W, H)
CX = W / 2.0
MID = W // 2
SEED = 11
random.seed(SEED)

# engine core: the light source + center of mass
CORE_X, CORE_Y = CX, 22.0
LX, LY = CORE_X, CORE_Y          # ONE radial source for the whole piece

def L(x, y):
    return light_field(x, y, LX, LY, lmax=30.0, ambient=0.10)

# ---- P1: silhouette region functions (the ANATOMY as massing), LEFT HALF ONLY --
# Everything is defined for x < MID; mirror() handles the right side.

def spine(x, y):
    # central vertical core column: a tall rounded shaft down the symmetry axis
    cy, ry, rx = CORE_Y, 16.0, 4.5
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return False
    hw = rx * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

def cylinder(x, y):
    # two twin cylinders flanking the spine: upper (angled up-out) + lower (down-out)
    for sgn in (-1, 1):
        bx = CX + sgn * 5.0
        by = CORE_Y - 6.0
        tx = CX + sgn * 24.0
        ty = CORE_Y - 13.0
        for t in [i / 12.0 for i in range(13)]:
            px = bx + (tx - bx) * t
            py = by + (ty - by) * t
            hw = 3.4 * (1.0 - 0.5 * t) + 0.6
            if abs(x - px) <= hw and abs(y - py) <= hw:
                return True
        # lower cylinder, mirrored down
        bx = CX + sgn * 5.0
        by = CORE_Y + 6.0
        tx = CX + sgn * 24.0
        ty = CORE_Y + 13.0
        for t in [i / 12.0 for i in range(13)]:
            px = bx + (tx - bx) * t
            py = by + (ty - by) * t
            hw = 3.4 * (1.0 - 0.5 * t) + 0.6
            if abs(x - px) <= hw and abs(y - py) <= hw:
                return True
    return False

def piston_head(x, y):
    # the cylinder heads: solid rounded caps at the outer ends of each cylinder
    for sgn in (-1, 1):
        for (cxp, cyp) in ((CX + sgn * 24.0, CORE_Y - 13.0), (CX + sgn * 24.0, CORE_Y + 13.0)):
            d = math.hypot(x - cxp, y - cyp)
            if d <= 3.6:
                return True
    return False

def mounting_base(x, y):
    # the engine sits on a wide trapezoidal base (the "yard" floor it's bolted to)
    cy = CORE_Y + 18.0
    t = (y - cy) / 5.0
    if abs(t) > 1.0:
        return False
    hw = 26.0 * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

def manifold(x, y):
    # a ring of bolt holes / valve rings around the core (industrial detail)
    d = math.hypot(x - CX, y - CORE_Y)
    if 7.5 <= d <= 9.0:
        ang = math.atan2(y - CORE_Y, x - CX)
        return abs(math.sin(ang * 6.0)) < 0.35   # discrete valve ports around the ring
    return False

# ---- P1: paint flat silhouettes (dim gray, unlit) to verify massing ----------
def paint_flat(region_fn, fg=8):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                cv.set(x, y, "\u2588", fg, 0)

paint_flat(spine, fg=9)
paint_flat(cylinder, fg=8)
paint_flat(piston_head, fg=9)
paint_flat(mounting_base, fg=7)
paint_flat(manifold, fg=10)

# ---- P2: radial shade every lit surface from the ONE core source -------------
def shade_region(region_fn, base_fg, hot_fg):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                ch, fg = shade(L(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

shade_region(spine, base_fg=94, hot_fg=15)             # core shaft: cyan-steel, white-hot near core
shade_region(cylinder, base_fg=92, hot_fg=94)          # cylinders: blue-steel body, cyan sheen near core
shade_region(piston_head, base_fg=91, hot_fg=15)      # heads: AMBER-yellow combustion at the outer ends
shade_region(mounting_base, base_fg=8, hot_fg=8)      # base: dim gray floor, recedes into void

# ---- P3: constructed bright accents (the "bright accents" of the lean) -------
# core glow: a small white-hot disc at the very center, the engine's heart
for y in range(int(CORE_Y - 2), int(CORE_Y + 3)):
    for x in range(MID):
        d = math.hypot(x - CX, y - CORE_Y)
        if d <= 1.6:
            cv.set(x, y, "\u2588", 15, 0)
# cyan valve-ring accent on the manifold (the rare bright cool color)
for y in range(H):
    for x in range(MID):
        if manifold(x, y):
            cv.set(x, y, "\u2593", 14, 0)   # cyan-ish bright, half-block = heat sheen

# P3b: specular tube-highlights -- a bright stripe down each cylinder's light-facing
# edge so they read as TUBES, not flat wedges. Light is at the core, so the lit side
# of every cylinder faces inward toward CX/CORE_Y.
for sgn in (-1, 1):
    for (bx, by, tx, ty) in ((CX + sgn*5.0, CORE_Y-6.0, CX+sgn*24.0, CORE_Y-13.0),
                             (CX + sgn*5.0, CORE_Y+6.0, CX+sgn*24.0, CORE_Y+13.0)):
        for t in [i/12.0 for i in range(13)]:
            px = bx + (tx-bx)*t
            py = by + (ty-by)*t
            # offset the stripe toward the core (the lit side): perpendicular-ish nudge
            hx = px + (CX-px)*0.28
            hy = py + (CORE_Y-py)*0.28
            for dx in (-1, 0, 1):
                cv.set(int(hx)+dx, int(hy), "\u2588", 94, 0)   # cyan sheen stripe
# core bloom: a faint ring of light around the white heart so it glows, not just dots
for y in range(H):
    for x in range(MID):
        d = math.hypot(x-CX, y-CORE_Y)
        if 1.6 < d <= 3.2:
            cv.set(x, y, "\u2592", 14, 0)

# ---- MIRROR: the signature move -- copy left half onto right -----------------
mirror(cv, axis='v')

# ---- P4: texture the void around the mass (not flat black) -------------------
def in_mass(x, y):
    return (spine(x, y) or cylinder(x, y) or piston_head(x, y)
            or mounting_base(x, y) or manifold(x, y))

# P4a: sparse gray dust far out (the yard's atmosphere), thinning toward the edges
random.seed(SEED + 1)
texture_fill(cv, lambda x, y: not in_mass(x, y), fg=8, density=0.10, seed=SEED + 1)

# P4b: radial energy bloom -- faint cool light radiating from the core into the void,
# DENSER near the engine, thinning outward. This is what makes the piece glow OUT of the
# dark instead of sitting in near-empty space (the density gap vs the house references).
random.seed(SEED + 2)
for y in range(1, H - 1):
    for x in range(1, W - 1):
        if in_mass(x, y):
            continue
        d = math.hypot(x - CX, y - CORE_Y)
        # bloom probability falls off with distance from the core
        p = max(0.0, 0.34 * (1.0 - d / 34.0))
        if random.random() < p:
            # near the core it's a cool cyan sheen; far out it dims to gray dust
            fg = 94 if d < 12 else (8 if d > 26 else 93)
            ch = "\u2592" if d < 16 else "\u00b7"
            cv.set(x, y, ch, fg, 0)

# ---- P5: frame (house-standard double-line border) --------------------------
def frame():
    for x in range(W):
        cv.set(x, 0, "\u2550", 13, 0); cv.set(x, H - 1, "\u2550", 13, 0)
    for y in range(H):
        cv.set(0, y, "\u2551", 13, 0); cv.set(W - 1, y, "\u2551", 13, 0)
frame()

# ---- render + write ----------------------------------------------------------
out = []
cv.render(out)
write_ans("scratch/_ghost_engine.ans", out, title="GHOST ENGINE v1.0", handles="raze")
