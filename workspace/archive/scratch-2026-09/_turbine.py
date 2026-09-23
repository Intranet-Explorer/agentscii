#!/usr/bin/env python3
# _turbine.py -- raze solo. THE TURBINE // "a dyno, lit down its axis from the hot end."
#
# PROVENANCE / WHY NEW (pack43 companion to THE REACTOR): hollis opened a "reactor/industrial"
# pack43 batch and named two non-reskin companions. This is #1 -- a HORIZONTAL counterpart that
# reads as a family with THE REACTOR but breaks it on two axes so it's NOT a reskin:
#    (1) HORIZONTAL architecture vs THE REACTOR's VERTICAL vessel -- a long capsule body + a row of
#        vertical cooling fins, lit ALONG its axis, not a tall vessel + stacked horizontal fins.
#    (2) Light travels DOWN the x-axis from ONE end (the hot intake at left), not radially out of a
#        central core -- "radial light along an axis" as hollis described it. Same HOT plasma palette
#        (amber body / white-hot core / red tips + cool cyan sheen) so it sits in THE REACTOR's family,
#        but distinct from GHOST ENGINE's blue-steel/cyan twin-cylinder on BOTH axes.
#
# SIGNATURE MOVE: paint y < MID only, mirror(axis='h') copies it down -> perfect bilateral symmetry
# across the HORIZONTAL centerline (ACiDDraw's mirror tool). Because the body is lit from ONE end it
# is NOT left-right symmetric -- so the horizontal axis is its only clean bilateral axis, which forces
# the body's centerline onto the canvas centerline (CY = H/2) and rules out an asymmetric bottom-only
# pedestal. The turbine glows OUT of a heat-shimmer void instead of sitting on a floor -- same "lit
# mass in the dark" mood as THE REACTOR, mirrored the other way.
#
# COLOR CALIBRATION (the gotcha I hit on THE REACTOR): canvas.sgr/figure_common.c both map a plain
# 0-7 hue index via (90+(fg&7)) if fg>7 else (30+fg). Pass PLAIN 0-7 hue indices everywhere
# (3=amber, 4=blue, 6=cyan, 7=white, 1=red) -- NOT pre-encoded SGR codes like 91/93, which double-map
# and silently corrupt color. shade() returns a bright-range fg; feed that straight back into c(),
# which now passes SGR codes through untouched (the ORACLE guard).

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, write_ans
from figure_common import light_field, shade, c, RESET

W, H = 80, 52
cv = Canvas(W, H)
CY = H / 2.0                      # body centerline ON the canvas centerline so mirror(axis='h') closes
MID = H // 2                      # paint y < MID (top half incl. centerline), mirror down
SEED = 13
random.seed(SEED)

# hot end (light source + center of mass): the intake is at LEFT, so light travels DOWN the axis.
LX, LY = 16.0, CY
CX = W / 2.0                     # body's horizontal center

def L(x, y):
    return light_field(x, y, LX, LY, lmax=38.0, ambient=0.12)    # steep enough that the far end dims

# ---- P1: silhouette region functions (the ANATOMY as massing), TOP HALF ONLY --
# Everything is defined for y < MID; mirror(axis='h') handles the bottom side. All regions are
# symmetric about CY by construction (abs(y-CY)), so the top-bottom mirror closes cleanly.

def body(x, y):
      # the containment chamber: a long HORIZONTAL capsule (two rounded ends + straight sides)
    cy = CY
    rx = 25.0                   # half-length of the body
    ry = 7.0                    # half-height of the body
    left = CX - rx
    right = CX + rx
    if x < left or x > right:
        return False
    if left <= x <= right:
        return abs(y - cy) <= ry
    t = (x - CX) / rx
    hh = ry * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(y - cy) <= hh

def fins(x, y):
      # a row of cooling-fins radiating PERPENDICULAR to the axis (vertical bars at several x's),
      # staggered in length so the rack reads as a real turbine casing, not a ladder.
    cy = CY
    rx = 25.0
    if x < CX - rx or x > CX + rx:
        return False
    fin_xs = [CX + k * 6.0 for k in range(-3, 4)]        # 7 fins along the body
    for k, fx in enumerate(fin_xs):
        if abs(x - fx) <= 1.0:
            inner = 5.0
            outer = 12.0 - (k % 2) * 3.0                 # stagger long/short so they don't align
            return inner <= abs(y - cy) <= outer
    return False

def plasma(x, y):
      # the hot core running down the spine: a thin bright column along the centerline, brightest at
      # the hot end (left), cooling toward the far end (right). Kept THIN so it reads as a distinct
      # white-hot stripe over the amber body, not blended into it.
    rx = 23.0
    if x < CX - rx or x > CX + rx:
        return False
    t = (x - CX) / rx
    hh = 1.1 * math.sqrt(max(0.0, 1.0 - t * t)) + 0.7    # narrow lens/column of light along the axis
    return abs(y - CY) <= hh

def intake(x, y):
      # the hot end cap / valve housing at the LEFT -- where the light comes from
    d = math.hypot(x - (CX - 25.0), y - CY)
    return d <= 3.4

def nozzle(x, y):
      # the far-end nozzle / exhaust at the RIGHT -- a small ringed cap, dimmer (cooled off)
    d = math.hypot(x - (CX + 25.0), y - CY)
    return d <= 2.6

def ports(x, y):
      # valve ports around the body's mid-section (industrial detail, discrete marks along the axis)
    if CX - 14.0 <= x <= CX + 14.0:
        ang = math.sin((x - CX) * 0.9)
        return abs(ang) < 0.16 and abs(y - CY) <= 7.5
    return False

# ---- P1: paint flat silhouettes (dim gray, unlit) to verify massing ----------
def paint_flat(region_fn, fg=8):
    for y in range(MID):
        for x in range(W):
            if region_fn(x, y):
                cv.set(x, y, "\u2588", fg, 0)

paint_flat(body, fg=9)
paint_flat(fins, fg=8)
paint_flat(intake, fg=10)
paint_flat(nozzle, fg=7)
paint_flat(ports, fg=11)
paint_flat(plasma, fg=15)

# ---- P2: shade every lit surface from the ONE hot-end source -----------------
def shade_region(region_fn, base_fg, hot_fg):
    for y in range(MID):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = shade(L(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

shade_region(body,   base_fg=3, hot_fg=7)       # chamber: glowing AMBER body (3), white-hot near the intake (7)
shade_region(fins,   base_fg=4, hot_fg=6)       # fins: cool BLUE plates (4), cyan sheen near the core (6) -- cold contrast
shade_region(intake, base_fg=3, hot_fg=7)       # end cap: warm amber housing (3), white at the seam (7)
shade_region(nozzle, base_fg=8, hot_fg=8)       # far nozzle: dim gray, cooled off -- recedes into void

# ---- P3: constructed bright accents ------------------------------------------
# plasma core: white-hot heart at the intake cooling to red tips toward the far end -- drawn on top.
for y in range(MID):
    for x in range(W):
        if plasma(x, y):
            Lc = light_field(x, y, LX, LY, lmax=10.0, ambient=0.25)    # short reach -> pops as a hot stripe
            ch, fg = shade(Lc, base_fg=3, hot_fg=7)                    # amber body (3) -> white at the heart (7)
            cv.set(x, y, "\u2588", fg, 0)                              # force full block so it stands over the body
            if x > CX + 16:                                             # red-hot tips concentrated at the FAR nozzle end
                cv.set(x, y, "\u2588", 1, 0)

# valve ports: cyan glass sheen (the rare cool accent against the warm body)
for y in range(MID):
    for x in range(W):
        if ports(x, y):
            cv.set(x, y, "\u2593", 6, 0)

# P3b: specular sheen on each fin's light-facing (core/intake-facing) edge so fins read as PLATES
# catching the axial light, not flat bars. Light is at the hot end, so the lit side faces that way.
for fx in [CX + k * 6.0 for k in range(-3, 4)]:
    for t in [i / 10.0 for i in range(11)]:
        py = CY - (12.0 - t * 7.0)         # outer->inner down the fin toward the core
        px = fx
        if px < LX:                        # only the side facing the hot end glows
            cv.set(int(px), int(py), "\u2588", 6, 0)

# core bloom: a faint ring of light around the plasma heart at the intake so it glows, not just dots
for y in range(MID):
    for x in range(W):
        d = math.hypot(x - LX, y - LY)
        if 2.4 < d <= 4.2:
            cv.set(x, y, "\u2592", 6, 0)

# ---- MIRROR: the signature move -- copy top half onto bottom -----------------
mirror(cv, axis='h')

# ---- P4: texture the void around the mass (not flat black) -------------------
def in_mass(x, y):
    return (body(x, y) or fins(x, y) or intake(x, y)
            or nozzle(x, y) or ports(x, y) or plasma(x, y))

# P4a: gray heat-shimmer dust far out (the turbine's atmosphere), not flat black.
texture_fill(cv, lambda x, y: not in_mass(x, y), fg=8, density=0.30, seed=SEED + 1)
for y in range(H):
    for x in range(W):
        if in_mass(x, y):
            continue
        d = math.hypot(x - LX, y - LY)
          # P4b: axial energy bloom -- cool cyan near the hot end thinning to gray down-axis and out,
          # so it glows OUT of the dark instead of sitting in near-empty space (THE REACTOR move).
        if 4.2 < d <= 36.0:
            Lb = light_field(x, y, LX, LY, lmax=36.0, ambient=0.06)
            p = Lb * 0.55 if d < 14 else Lb * 0.28         # denser near the hot end, sparse far out
            if random.random() < p:
                ch = "\u2591" if d < 16 else ("\u2592" if random.random() < 0.4 else "\u2591")
                cv.set(x, y, ch, 6 if d < 9 else (7 if d < 16 else 8), 0)

# ---- P5: frame + title card --------------------------------------------------
out = []
out.append(c(13) + "\u2554" * W)             # top rule
cv.render(out)                                 # body rows appended in place
out.append(c(13) + "\u2557" * W)              # bottom rule

write_ans("scratch/_turbine.ans", out, title="THE TURBINE v1.0", handles="raze", add_sig=True)
print("wrote scratch/_turbine.ans")
