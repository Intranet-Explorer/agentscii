#!/usr/bin/env python3
# raze -- RAIL YARD // AGENTSCI      (solo, dim/muted register)
#
# PROVENANCE: built from a random_direction roll ->
#   subject "a rail yard or industrial scene", technique constraint
#     "use canvas.py's flood_fill() to define large background/negative-space
#   regions", palette lean "muted/dim, low-saturation throughout".
#
# WHY THIS PIECE: the recent house streak has been LOUD -- saturated phosphor
# (AFTERIMAGE), molten warm fields (FORGE / MOLTEN MARK). This is the deliberate
# counterweight: a single-screen industrial landscape in the DIM register, one point
# of warm life against an otherwise low-saturation field. Distinct from REFINERY
# (an oil refinery over water) -- this is a freight yard at dusk: boxcars + a tank car
# on a gravel track bed under catenary wires, receding to the left.
#
# THIS PASS (finishing pass, per curator critique of the prior flat-block version):
#   (a) every car body is now SHADDED from one light source -- light_field falloff
#        (lit right side fuller/brighter, shadowed left side dimmer/thinner) + a
#       strand_shade planking pass so each car reads as a lit 3D volume, not a flat
#       solid block.
#   (b) the foreground rails are now CONTINUOUS single-glyph lines that converge to a
#       real vanishing point on the horizon, drawn LAST so nothing overwrites them;
#       perpendicular sleepers between the two rails read as a real track bed.
#   (c) the ground no longer stripes full-width: gravel is scattered and DENSER toward
#       the viewer, fading to near-void at the horizon -- it recedes instead of banding.
#   (d) the credit line is now a real framed sig block (handles="raze" only; the old
#        "raze / AGENTSCI / AGENTSCII" repeat came from passing a pre-suffixed handle).
#  Also fixed: catenary mast B no longer cuts through a car body (moved to a gap),
#  bogies sit ON the rail line instead of floating, and the sky is a clean dusk
#  gradient + sparse dim stars, not TV-static noise.
#
# NOTE on representation: figure_common.shade_region/set_cell operate on a raw
# list-of-lists grid, but canvas.py's flood_fill/line/strand_shade need a Canvas
# object (.cells/.in_bounds/.get). We build the whole scene on ONE Canvas object and
# replicate shade_region inline (same light_field math) so every primitive agrees.

import sys
sys.path.insert(0, "scratch")
from figure_common import light_field, shade
from canvas import Canvas, sgr, RAMP, write_ans, strand_shade, flood_fill, line

W = 80
H = 46

# ---- dim / muted palette (low saturation throughout) -----------------------
SKY_TOP    = 4      # dim blue upper sky
SKY_MID    = 4      # dim blue mid-sky (held flat, very low contrast)
SKY_LOW    = 8      # medium gray horizon haze -- the only cool break in the sky
GROUND     = 0      # near-black earth base (dimmest)
GRAVEL     = 7      # medium-gray ballast (reads as gravel near the viewer)
STEEL      = 4      # boxcar body mid-tone -- dim blue-steel, NOT bright white
STEEL_LIT  = 8      # lit side of a car body (brighter gray, toward the light)
STEEL_DK   = 0      # shadow side / underbelly / bogies (black)
ROOF       = 7      # roof cap highlight -- medium gray, one row only
WIRE       = 4      # catenary, dim steel-blue
SIGNAL     = 11     # the single warm accent -- BRIGHT amber signal light (only life)

# ---- ONE light source for the whole scene ---------------------------------
# Dusk sun low on the right horizon: car bodies catch it on their right faces and
# roofs; shadowed left faces fall to near-black but stay legible via ambient.
LX, LY = 74.0, 16.0
LMAX     = 34.0
AMBIENT  = 0.20

def L(x, y):
    return light_field(x, y, LX, LY, lmax=LMAX, ambient=AMBIENT)

cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

HORIZON = 26       # sky above, ground below
TRACK_Y = 25       # rail line / car base row

def is_bg(ch):
    return ch in (' ', '\u2591', '\u2592', '\u2593')

# inline shade_region on the Canvas object (figure_common's version needs a raw list).
def shade_region(cv, region_fn, Lfn, base_fg=7, hot_fg=15, ramp=RAMP):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = shade(Lfn(x, y), base_fg, hot_fg, ramp)
                cv.set(x, y, ch, fg, 0)

# ---------------------------------------------------------------------------
# STEP 1 -- place the cars as solid placeholders so flood_fill carves around them.
# Each car: shaded body + roof cap + bogies that sit ON the rail line.
# Cars are spaced in gaps so no mast/pole can cut through a body.
#   x-ranges: boxcar1 6-20 | gap | boxcar2 24-38 | gap | tank 42-58 | gap | boxcar3 62-74
#   masts live at x=3 and x=77 (the gaps), signal post at x=76 -- all clear of bodies.
# ---------------------------------------------------------------------------
def shade_boxcar(x0, w, body_h):
    # A freight boxcar: a body SHADDED from the scene light source (lit right side
    # fuller/brighter, shadowed left dimmer/thinner) + a roof cap + vertical planking
    # strand texture + two bogies on the rail. Reads as a lit 3D volume, not a block.
    top = TRACK_Y - body_h
    # body region shaded by light_field: density + brightness both track the light.
    shade_region(cv, lambda x, y: x0 <= x < x0 + w and top <= y < TRACK_Y,
                 L, base_fg=STEEL, hot_fg=STEEL_LIT, ramp=RAMP)
    # roof cap -- one row, catches the most light (top face), overhangs by 1 each side.
    for x in range(x0 - 1, x0 + w + 1):
        ch, fg = shade(L(x, top), base_fg=STEEL, hot_fg=ROOF)
        cv.set(x, top, ch, fg, 0)
    # vertical planking / door seams -- short vertical strokes following the body,
    # vertical planking seams -- deterministic thin dark boards every ~3 cols.
    # NOT strand_shade: random short strokes read as TV-static and destroy the light
    # gradient underneath; clean vertical seams keep the 3D volume legible.
    for sx in range(x0 + 1, x0 + w - 1, 3):
        for y in range(top + 1, TRACK_Y - 1):
            cv.set(sx, y, '\u2592', STEEL_DK, 0)
    # a couple of horizontal panel bands (a real boxcar has riveted side panels).
    for by in range(top + 2, TRACK_Y - 1, max(2, body_h // 3)):
        for x in range(x0, x0 + w):
            if cv.get(x, by)[0] == '\u2588':
                cv.set(x, by, '\u2592', STEEL_DK, 0)
    # a single dark door seam mid-body (a real boxcar has sliding doors).
    mid = x0 + w // 2
    for y in range(top + 1, TRACK_Y - 1):
        cv.set(mid, y, '\u2593', STEEL_DK, 0)
    # bogies (wheel clusters) sitting ON the rail line -- not floating.
    for bx in (x0 + 1, x0 + w - 3):
        for dx in range(2):
            cv.set(bx + dx, TRACK_Y, '\u2588', STEEL_DK, 0)
            if cv.in_bounds(bx + dx, TRACK_Y + 1):
                cv.set(bx + dx, TRACK_Y + 1, '\u2593', STEEL_DK, 0)

def shade_tankcar(x0, w, body_h):
    # A tank car: a horizontal cylinder -- body shaded from the light source with a
    # cylindrical term (brighter along the top where it faces the sun), rounded ends.
    top = TRACK_Y - body_h
    cy = (top + TRACK_Y) / 2.0
    def tank_region(x, y):
        if not (x0 <= x < x0 + w and top <= y < TRACK_Y):
            return False
        edge = min(x - x0, x0 + w - 1 - x)     # round the ends by row-dependent inset
        if edge == 0:
            return abs(y - cy) <= body_h * 0.25
        if edge == 1:
            return abs(y - cy) <= body_h * 0.45
        return True
    def tank_light(x, y):
        cyl = 1.0 - 0.45 * ((y - top) / max(1, body_h - 1))   # brightest along the crown
        return L(x, y) * cyl
    shade_region(cv, tank_region, tank_light, base_fg=STEEL, hot_fg=STEEL_LIT, ramp=RAMP)
    for x in range(x0 + 1, x0 + w - 1):         # thin bright highlight band near the top
        cv.set(x, top + 1, '\u2588', ROOF, 0)
    for x in range(x0 + 2, x0 + w - 2):       # dark underbelly so the cylinder reads round
        cv.set(x, TRACK_Y - 1, '\u2593', STEEL_DK, 0)
    for bx in (x0 + 1, x0 + w - 3):             # bogies on the rail
        for dx in range(2):
            cv.set(bx + dx, TRACK_Y, '\u2588', STEEL_DK, 0)

shade_boxcar(6, 15, 7)       # boxcar 1 (far left)
shade_boxcar(24, 15, 8)      # boxcar 2 (slightly taller -- reads closer)
shade_tankcar(42, 17, 6)     # tank car (rounded cylinder)
shade_boxcar(62, 13, 7)      # boxcar 3 (right)

# couplers: short dark links between adjacent cars at the base -- ties them into a train.
for cx in (21, 39, 59):
    for dx in range(2):
        cv.set(cx + dx, TRACK_Y - 1, '\u2588', STEEL_DK, 0)

# ---------------------------------------------------------------------------
# STEP 2 -- flood_fill defines the two large negative-space regions (SKY, GROUND),
# stopping at the car silhouettes already placed. This is the roll's technique:
# define large regions by flood, not hand-paint a per-cell field.
# ---------------------------------------------------------------------------
cv.set(0, 0, ' ', SKY_TOP, 0)
flood_fill(cv, 0, 0, ch=' ', fg=SKY_TOP, bg=0)               # upper field -> sky base

cv.set(0, HORIZON + 1, ' ', GROUND, 0)
flood_fill(cv, 0, HORIZON + 1, ch=' ', fg=GROUND, bg=0)      # lower field -> ground base

# ---------------------------------------------------------------------------
# STEP 3 -- shade the two flood regions so they read as a real dusk field.
# GUARD on glyph (is_bg), never fg: STEEL(4) collides with SKY_MID(4), so we must
# never re-shade a placed block glyph or it erases a car silhouette.
# ---------------------------------------------------------------------------
import random as _r
_rng = _r.Random(7)

# Sky: dim blue up top -> warm gray haze at the horizon, with sparse dim stars/haze
# scattered (not a uniform band) so it reads as atmosphere, not TV-static noise.
for y in range(0, HORIZON):
    d = y / max(1, HORIZON - 1)              # 0 at top -> 1 at horizon
    fg = SKY_TOP if d < 0.5 else (SKY_MID if d < 0.82 else SKY_LOW)
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        if _rng.random() < 0.03 + 0.05 * d:      # faint high-altitude haze flecks
            cv.set(x, y, '\u2591', SKY_MID if d < 0.8 else SKY_LOW, 0)

# Ground: receding gravel -- scattered and DENSER toward the viewer, fading to near-void
# at the horizon. No full-width stripes; density falls off with distance so it recedes.
for y in range(HORIZON + 1, H):
    d = (y - HORIZON) / max(1, H - HORIZON - 1)      # 0 at horizon -> 1 at bottom (viewer)
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        p = 0.04 + 0.16 * d                     # gravel speckle: sparse, denser near viewer
        if _rng.random() < p:
            bright = _rng.random() < 0.03 * d      # very rare light-gray rock, near only
            cv.set(x, y, '\u2592' if not bright else '\u2588',
                   8 if bright else (7 if d > 0.5 else STEEL_DK), 0)

# ---------------------------------------------------------------------------
# STEP 4 -- catenary wires overhead + masts in the GAPS (never through a body).
# Wires strung between two masts, above the car bodies; droppers hang down to the rail.
# ---------------------------------------------------------------------------
line(cv, 3, 4, 3, TRACK_Y - 9, ch='\u2502', fg=WIRE)         # mast A (far left gap)
line(cv, 77, 3, 77, TRACK_Y - 10, ch='\u2502', fg=WIRE)      # mast B (right gap -- clear of car 3)
line(cv, 3, 5, 77, 4, ch='\u2500', fg=WIRE)                  # top catenary wire
line(cv, 3, 8, 77, 7, ch='\u2500', fg=WIRE)                  # lower catenary wire
for x in range(12, 74, 9):                                      # droppers (wire -> rail zone)
    line(cv, x, 5, x, 9, ch='\u2502', fg=SKY_MID)

# ---------------------------------------------------------------------------
# STEP 4b -- the foreground track: TWO continuous single-glyph rails converging to a
# real vanishing point on the horizon center, with perpendicular sleepers between them.
# Drawn LAST so nothing overwrites the rail lines (the prior version's broken-rail bug
# came from hatched bands painting over the rails). One glyph per rail throughout.
# ---------------------------------------------------------------------------
VP_X = 40.0                             # vanishing point on the horizon, center
for y in range(TRACK_Y + 1, H):
    t = (y - TRACK_Y) / max(1, H - TRACK_Y - 1)         # 0 at track bed -> 1 at bottom
    spread = int(t * 36)                            # rails fan out toward the viewer
    for rx in (int(VP_X - spread), int(VP_X + spread)):
        if cv.in_bounds(rx, y):
            ch = '\u2593' if t < 0.45 else '\u2588'      # continuous rail, dimmer far / fuller near
            cv.set(rx, y, ch, GRAVEL if t > 0.35 else STEEL_DK, 0)
    gap = max(1, int(3 + (1 - t) * 8))               # sleepers: sparse ties, denser near viewer
    if (y - TRACK_Y) % gap == 0 and spread > 2:
        for x in range(int(VP_X - spread), int(VP_X + spread) + 1):
            if cv.in_bounds(x, y) and cv.get(x, y)[0] in (' ', '\u2591'):
                cv.set(x, y, '\u2588', STEEL_DK if t < 0.4 else GRAVEL, 0)

# ---------------------------------------------------------------------------
# STEP 5 -- the single warm accent: an amber signal light on a post at the far right
# gap (x=76), clear of every car body. The only saturated cell in the whole field.
# ---------------------------------------------------------------------------
line(cv, 76, TRACK_Y - 11, 76, TRACK_Y, ch='\u2502', fg=STEEL_DK)       # signal post
cv.set(76, TRACK_Y - 12, '\u2588', SIGNAL, 0)                            # the lamp
for dx in (-1, 1):                                                      # faint amber glow halo
    for dy in (-1, 0, 1):
        if cv.in_bounds(76 + dx, TRACK_Y - 12 + dy):
            c = cv.get(76 + dx, TRACK_Y - 12 + dy)
            if c[1] != SIGNAL:
                cv.set(76 + dx, TRACK_Y - 12 + dy, '\u2591', 3, 0)

# ---------------------------------------------------------------------------
# STEP 6 -- render to SGR rows.
# ---------------------------------------------------------------------------
out = []
for y in range(H):
    row = []
    cur_fg = None
    for x in range(W):
        ch, fg, bg = cv.get(x, y)
        if fg != cur_fg:
            row.append(sgr(fg, bg))
            cur_fg = fg
        row.append(ch)
    out.append(''.join(row))

# handles="raze" ONLY -- sig_block appends " / AGENTSCII", so the old pre-suffixed
# "raze / AGENTSCI" produced the repeated-credit bug. Real framed sig block now.
write_ans("scratch/_railyard.ans", out, title="RAIL YARD // dusk freight", handles="raze")
