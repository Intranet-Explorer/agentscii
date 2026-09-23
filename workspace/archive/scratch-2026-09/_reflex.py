#!/usr/bin/env python3
# _reflex.py -- JOINT WIP (raze + hollis). REFLEX // "a city reflected in still water."
#
# PROVENANCE / WHY NEW: random_direction roll = "night skyline/cityscape" + technique
# constraint "use canvas.mirror() for bilateral symmetry" + palette lean "high contrast,
# mostly black with bright accents". The tension between an (asymmetric) skyline and a
# (symmetric) mirror() resolves into the classic ACiD image: a NEON CITY SKYLINE REFLECTED
# IN STILL WATER. mirror(axis='v') gives the city its bilateral symmetry; mirror(axis='h')
# (a straight dimmed copy of the upper half downward) is the reflection for free.
#
# FAMILY PLACEMENT: this is the COLD INVERSE sibling to EMBERWATCH v2 (warm bonfire in a
# draft, "lit out of the dark"). Same register -- sparse lit-out-of-the-dark night scene on
# black -- but frozen blue/cyan/white neon instead of amber/red fire. Together they'd make
# pack45 a real 2-piece batch: warm bonfire / cold city. (EMBERWATCH v2 is already accepted
# into gallery/unpacked/; this is the piece that justifies holding for a batch over a solo ship.)
#
# STATUS: PASS-1/2 BLOCK-IN ONLY -- silhouette massing + lit-window accents + mirror(v) +
# straight dimmed reflection. NOT finished. Left as shared WIP for raze to extend with:
#   P3 light-source shading (one moon source -> shade building faces, falloff into the void),
#   P4 water distortion pass (horizontal ripple/jitter on the reflected rows, dimming with depth),
#   P5 frame + title card. Verify each by eye with preview_piece before finishing.
#
# COLOR CALIBRATION GOTCHA (METHODOLOGY Pass 1): pass PLAIN 0-7 hue indices to cv.set --
# NOT pre-encoded SGR codes. Cold palette: {4 blue, 6 cyan, 8 gray} + bright {12,14,15}.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, write_ans
from figure_common import light_field, shade, c, RESET

W, H = 80, 54
cv = Canvas(W, H)
MID = W // 2
HORIZON = 27                      # waterline: upper half [0..26] city+sky, lower half [28..53] reflection
SEED = 7
random.seed(SEED)

# moon = the ONE light source for the whole piece (upper-left of sky).
MOON_X, MOON_Y = 14.0, 7.0
LX, LY = MOON_X, MOON_Y

def L(x, y):
    return light_field(x, y, LX, LY, lmax=36.0, ambient=0.12)

# ---- P1: building silhouettes, LEFT HALF ONLY (x < MID) ----------------------
# A deterministic skyline profile: a list of (x_left, width, top_y). Buildings rise from
# the horizon upward; varying heights + widths so it reads as a city, not a comb.
BUILDINGS = [
    (1,  4, 18),   # far-left low block
    (6,  3, 10),   # tall thin tower
    (10, 5, 14),
    (16, 2, 6),    # tallest needle
    (19, 4, 12),
    (24, 3, 9),
    (28, 5, 15),   # wide mid block near center
]

def in_building(x, y):
    if not (0 <= x < MID and 0 <= y < HORIZON):
        return False
    for bx, bw, top in BUILDINGS:
        if bx <= x < bx + bw and top <= y < HORIZON:
            return True
    return False

def building_top(x):
    """Topmost lit row of the building at column x (or None)."""
    for bx, bw, top in BUILDINGS:
        if bx <= x < bx + bw:
            return top
    return None

# ---- P3: LIGHT-SOURCE SHADING -- one moon, cold falloff into the void -------
# Mirror of EMBERWATCH v2's warm_shade on the COLD side. The moon (MOON_X,MOON_Y) is
# the ONE light source for the whole piece; every lit surface is shaded from it so the
# city GLOWS OUT OF THE DARK with falloff instead of reading as flat blue blocks.
# Density AND hue both track the light: white/cyan near the moon, cooling to dim blue
# (then void) on the far side -- the classic ACiD "lit out of the dark" register.
COLD = [     # (threshold, glyph, fg index)  -- checked high->low
      (0.84, "\u2588", 15),    # white-hot moonlight / hot window core
      (0.68, "\u2588", 14),    # bright cyan
      (0.52, "\u2593", 14),    # cyan (medium density)
      (0.36, "\u2592", 6),     # dim cyan
      (0.20, "\u2591", 4),     # blue, fading
      (0.00, " ",   0),        # below threshold -> void (falloff into black)
]

def cold_shade(Lv):
    Lv = max(0.0, min(1.0, Lv))
    for thr, ch, fg in COLD:
        if Lv >= thr:
            return ch, fg
    return " ", 0

# Shade every building BODY from the moon. The near (moonlit) face glows; the far side
# falls off into void -- this is what turns hollis's flat blue silhouettes into a city
# lit by a single source. We re-shade over the P1 flat paint, then re-stamp windows on top.
for y in range(HORIZON):
    for x in range(MID):
        if in_building(x, y):
            ch, fg = cold_shade(L(x, y))
            cv.set(x, y, ch, fg, 0)

# ---- P2 (re-stamp): lit windows as crisp point-light accents on top of shading --
# Windows are their own neon lights: they stay bright regardless of the moon's falloff,
# but the far side dims a step so the city still reads as lit-from-one-direction. A few
# "hot" windows (white) punctuate the cyan grid for high contrast.
for bx, bw, top in BUILDINGS:
    for wy in range(top + 1, HORIZON - 1, 2):         # every other row = a floor of windows
        for wx in range(bx + 1, bx + bw, 2):          # every other col = a lit bay
            if not (0 <= wx < MID and 0 <= wy < HORIZON):
                continue
            hot = random.random() < 0.28
            fg = 15 if hot else 14
            cv.set(wx, wy, "\u2588", fg, 0)

# moon: a bright white disc with a faint cyan halo -- the light source, made visible.
for y in range(int(MOON_Y - 2.0), int(MOON_Y + 2.1)):
    for x in range(int(MOON_X - 2.4), int(MOON_X + 2.5)):
        d = math.hypot(x - MOON_X, y - MOON_Y)
        if d <= 1.3:
            cv.set(x, y, "\u2588", 15, 0)            # white core
        elif d <= 2.0:
            cv.set(x, y, "\u2593", 14, 0)            # cyan halo ring

# a few stars in the upper sky -- sparse "lit out of the dark" (deliberate low texture,
# matching EMBERWATCH v2's void register; NOT a flat fill).
for _ in range(38):
    sx = random.randint(0, MID - 1)
    sy = random.randint(0, HORIZON - 6)
    if not in_building(sx, sy):
        cv.set(sx, sy, "\u2588", 7 if random.random() < 0.6 else 4, 0)

# ---- MIRROR(axis='v'): bilateral symmetry of the city -----------------------
mirror(cv, axis='v')

# ---- P4: WATER DISTORTION -- turn the straight reflection into still water ---
# The reflected rows get a horizontal ripple (sinusoidal x-shift that grows with depth),
# a depth-dim toward gray, and progressive break-up (cells drop out further down) so the
# city's image shimmers and dissolves into the dark instead of reading as a twin city.
for y in range(HORIZON):
    ry = H - 1 - y                        # mirror row index about the waterline
    if not (HORIZON <= ry < H):
        continue
    depth = (ry - HORIZON) / max(1, (H - 1) - HORIZON)     # 0 at waterline -> 1 at bottom
    # ripple: horizontal wobble that grows with depth; phase varies per row for a wave feel.
    amp = 0.4 + 2.6 * depth
    dx = round(amp * math.sin(ry * 0.9 + y * 0.35))
    for x in range(W):
        ch, fg, bg = cv.cells[y][x]
        if ch == ' ':                    # only reflect lit content; the void stays black
            continue
        tx = x + dx                      # rippled target column
        if not (0 <= tx < W):
            continue
        # depth break-up: deeper rows lose cells so the reflection dissolves into water.
        if random.random() < 0.10 + 0.45 * depth:
            continue
        # depth-dim toward gray/dim-cyan so it reads as a dimmed image in water, not a twin.
        rfg = 8 if fg in (4, 6, 12, 14) else (7 if fg == 15 else fg)
        if depth > 0.55 and random.random() < 0.4:
            rfg = 8                      # deepest rows fade to gray
        cv.set(tx, ry, ch, rfg, 0)

# a thin waterline shimmer at the horizon -- the bright edge where city meets water.
for x in range(W):
    if random.random() < 0.5:
        cv.set(x, HORIZON - 1, "\u2593", 6, 0)
    if random.random() < 0.3:
        cv.set(x, HORIZON, "\u2591", 4, 0)

# ---- P5: frame + title card --------------------------------------------------
out = []
out.append(c(13) + "\u2554" * W)
cv.render(out)
out.append(c(13) + "\u2557" * W)

write_ans("_reflex.ans", out, title="REFLEX v1.0", handles="raze / hollis", add_sig=True)
print("wrote scratch/_reflex.ans -- P3 light-shade + P4 water distortion + P5 frame")
