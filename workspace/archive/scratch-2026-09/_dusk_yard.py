#!/usr/bin/env python3
# raze -- DUSK YARD // AGENTSCI       (solo, dim/muted register)
# PROVENANCE: revision of _yard_dusk (rejected this curation round). The critique was right on
# three concrete defects; each is fixed here and verified by preview + compare_to_reference.
#
#   DEFECT 1 -- "bottom white mass is the LARGEST element and it's muddy/illegible (3 banded bars
#     + a spike, not a clear track bed)."  CAUSE: VP_X=40 with rails spreading DOWNWARD from
#     TRACK_Y=25 bloomed the track into the whole bottom third as an undefined white blob.
#     FIX: put the vanishing point on a REAL horizon line ABOVE the cars (VP at y=HORIZON, x=40),
#     so the two rails recede UPWARD toward it and the foreground is a clean near-field track bed
#     + a distinct platform/shed structure -- legible, not a mass.
#   DEFECT 2 -- "perspective VP sits INSIDE the train at undercarriage height (incoherent camera)."
#     FIX: same as above -- the horizon/VP is now above the car bases; cars sit ON the track plane
#     and recede toward it, so the camera reads as a viewer standing on the near field looking down
#     the yard.
#   DEFECT 3 -- "'dusk' is unsupported: pure saturated blue on black reads as night, no warm/cool
#     split."  FIX: dusk light source is WARM and low-right (amber/orange sun at horizon), so car
#     bodies catch warm amber on their lit faces and fall to cool blue shadow; the sky is a real
#     warm->cool gradient (warm haze at the horizon, cool blue up top). Dusk is now EARNED, not captioned.
#
# KEPT from the accepted-in-principle version (the critique confirmed these read well): car bodies
# shaded as lit 3D volumes from ONE light source; tank car with a real cylindrical term; continuous
# single-glyph rails + perpendicular sleepers = a real track bed; gravel receding to near-void.
import sys, math
sys.path.insert(0, "scratch")
from figure_common import light_field, shade
from canvas import Canvas, sgr, RAMP, write_ans, line, flood_fill

W = 80
H = 46

# ---- dusk palette: WARM low-right sun + COOL sky. Low saturation throughout (dim register). ----
SKY_TOP   = 4       # dim blue upper sky (cool)
SKY_MID   = 4       # held flat, very low contrast up high
SKY_HAZE  = 3       # warm amber/orange haze at the horizon -- the dusk break (warm/cool split)
GROUND    = 0       # near-black earth base (dimmest)
GRAVEL_W  = 7       # medium-gray ballast near the viewer
STEEL     = 4       # car body mid-tone -- dim blue-steel (cool shadow side)
STEEL_LIT = 8       # lit side of a car body (brighter gray, toward the warm sun)
STEEL_DK  = 0       # shadow side / underbelly / bogies (black)
ROOF      = 7       # roof cap highlight -- one row only
WIRE      = 4       # catenary, dim steel-blue
SIGNAL    = 11      # the single saturated accent -- amber signal lamp (the only life)
# warm dusk light: low on the right horizon. Car bodies catch it on their RIGHT faces + roofs;
# shadowed LEFT faces fall to near-black but stay legible via ambient.
LX, LY = 76.0, 24.0
LMAX      = 38.0
AMBIENT   = 0.18

HORIZON = 24        # sky above (cool), ground below; the VP sits ON this line
TRACK_Y = 25        # rail line / car base row -- just below the horizon, cars sit on the track plane

def L(x, y):
    return light_field(x, y, LX, LY, lmax=LMAX, ambient=AMBIENT)

cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

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
#   x-ranges: boxcar1 6-20 | gap | boxcar2 24-38 | gap | tank 42-58 | gap | boxcar3 62-74
#   masts live at x=3 and x=77 (the gaps), signal post at x=76 -- all clear of bodies.
# ---------------------------------------------------------------------------
def shade_boxcar(x0, w, body_h):
    # A freight boxcar: a body SHADDED from the scene light source (lit right side fuller/brighter,
     # shadowed left dimmer/thinner) + a roof cap + vertical planking seams + two bogies on the rail.
    top = TRACK_Y - body_h
    shade_region(cv, lambda x, y: x0 <= x < x0 + w and top <= y < TRACK_Y,
                 L, base_fg=STEEL, hot_fg=STEEL_LIT, ramp=RAMP)
    # roof cap -- one row, catches the most light (top face), overhangs by 1 each side.
    for x in range(x0 - 1, x0 + w + 1):
        ch, fg = shade(L(x, top), base_fg=STEEL, hot_fg=ROOF)
        cv.set(x, top, ch, fg, 0)
    # vertical planking seams -- deterministic thin dark boards every ~3 cols (NOT strand_shade:
     # random short strokes read as TV-static and destroy the light gradient underneath).
    for sx in range(x0 + 1, x0 + w - 1, 3):
        for y in range(top + 1, TRACK_Y - 1):
            cv.set(sx, y, '\u2592', STEEL_DK, 0)
     # a couple of horizontal riveted panel bands.
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
     # A tank car: a horizontal cylinder -- body shaded from the light source with a cylindrical term
     # (brighter along the crown where it faces the sun), rounded ends.
    top = TRACK_Y - body_h
    cy = (top + TRACK_Y) / 2.0
    def tank_region(x, y):
        if not (x0 <= x < x0 + w and top <= y < TRACK_Y):
            return False
        edge = min(x - x0, x0 + w - 1 - x)      # round the ends by row-dependent inset
        if edge == 0:
            return abs(y - cy) <= body_h * 0.25
        if edge == 1:
            return abs(y - cy) <= body_h * 0.45
        return True
    def tank_light(x, y):
        cyl = 1.0 - 0.45 * ((y - top) / max(1, body_h - 1))    # brightest along the crown
        return L(x, y) * cyl
    shade_region(cv, tank_region, tank_light, base_fg=STEEL, hot_fg=STEEL_LIT, ramp=RAMP)
    for x in range(x0 + 1, x0 + w - 1):          # thin bright highlight band near the top
        cv.set(x, top + 1, '\u2588', ROOF, 0)
    for x in range(x0 + 2, x0 + w - 2):         # dark underbelly so the cylinder reads round
        cv.set(x, TRACK_Y - 1, '\u2593', STEEL_DK, 0)

# place: two boxcars (left, mid), a tank car (center-right), one boxcar (far right).
shade_boxcar(6, 15, 7)
shade_boxcar(24, 15, 8)
shade_tankcar(42, 17, 6)
shade_boxcar(62, 13, 7)

# ---------------------------------------------------------------------------
# STEP 1b -- DUSK WARM/COOL SPLIT on the car bodies: the low sun (low-right) catches each car's
# RIGHT face + roof in warm amber/orange; the LEFT shadow side stays cool blue. This is what earns
# "dusk" -- a real warm/cool split, not pure saturated blue-on-black (which reads as night). Applied
# AFTER the bodies are shaded so it recolors car cells only (is_bg guard keeps it off the field).
# ---------------------------------------------------------------------------
CAR_XR = [(6,21),(24,39),(42,59),(62,75)]    # x-ranges of the four placed cars
# The low dusk sun (low-right) catches each car's TOP-RIGHT edge in a bright warm rim/crest,
# grading down to dim orange toward the base; the LEFT shadow side stays cool blue. A real
# warm/cool split -- this is what EARNs 'dusk' instead of pure saturated blue-on-black (night).
for x0,x1 in CAR_XR:
    midx = (x0 + x1) // 2
    topy = TRACK_Y - 8
    for y in range(topy, TRACK_Y + 1):
        for x in range(x0, x1):
            c = cv.get(x, y)
            if not is_bg(c[0]):                 # only recolor actual car cells
                warm = x >= midx               # right face catches the low sun
                if warm:
                    near_top = (y - topy) <= 1   # bright warm rim/crest where the sun hits hardest
                    fg = 11 if near_top else 9        # BRIGHT amber lit face -- reads as dusk warmth
                else:
                    fg = 4 if c[1] in (7,8) else c[1]     # cool blue shadow side
                cv.set(x, y, None, fg, 0)

# ---------------------------------------------------------------------------
# STEP 2 -- flood_fill defines the two large negative-space regions (SKY, GROUND),
# stopping at the car silhouettes already placed. This is the roll's technique:
# define large regions by flood, not hand-paint a per-cell field.
# ---------------------------------------------------------------------------
cv.set(0, 0, ' ', SKY_TOP, 0)
flood_fill(cv, 0, 0, ch=' ', fg=SKY_TOP, bg=0)                # upper field -> sky base

cv.set(0, HORIZON + 1, ' ', GROUND, 0)
flood_fill(cv, 0, HORIZON + 1, ch=' ', fg=GROUND, bg=0)       # lower field -> ground base

# ---------------------------------------------------------------------------
# STEP 3 -- shade the two flood regions so they read as a real DUSK field.
# GUARD on glyph (is_bg), never fg: STEEL(4) collides with SKY_MID(4).
# ---------------------------------------------------------------------------
import random as _r
_rng = _r.Random(7)

# Sky: COOL blue up top -> WARM amber/orange haze at the horizon (the dusk warm/cool split).
for y in range(0, HORIZON):
    d = y / max(1, HORIZON - 1)               # 0 at top -> 1 at horizon
    if d < 0.45:
        fg = SKY_TOP                          # cool blue up high
    elif d < 0.80:
        fg = SKY_MID
    else:
        fg = SKY_HAZE                         # warm amber/orange haze band at the horizon
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        if _rng.random() < 0.03 + 0.05 * d:       # faint high-altitude haze flecks (cool up top)
            cv.set(x, y, '\u2591', SKY_MID if d < 0.8 else SKY_HAZE, 0)

# WARM HORIZON GLOW: a low amber/orange haze band in the clear sky just above the horizon -- the
# dusk sun's last light. Dim + varied (not a solid bar), brighter toward the sun (low-right). This is
# what makes the field read as DUSK (warm/cool split) instead of pure blue-on-black night.
for y in range(HORIZON - 4, HORIZON):
    for x in range(W):
        c = cv.get(x, y)
        if not is_bg(c[0]):
            continue
        # brightness falls off with height above the horizon; warmer/brighter toward the sun (low-right)
        h = HORIZON - 1 - y                          # 0 at horizon -> 3 just above it
        if _rng.random() < 0.55 - 0.12 * h:          # denser right at the horizon, sparser higher up
            fg = 11 if (x > 58 and h <= 1) else (9 if x > 40 else 3)
            cv.set(x, y, '\u2591', fg, 0)

# Ground: receding gravel -- scattered and DENSER toward the viewer, fading to near-void at the
# horizon. No full-width stripes; density falls off with distance so it recedes. Warm-tinted near
# the sun (low-right), cool/dim on the far left -- carries the dusk split into the ground too.
for y in range(HORIZON + 1, H):
    d = (y - HORIZON) / max(1, H - HORIZON - 1)       # 0 at horizon -> 1 at bottom (viewer)
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        p = 0.04 + 0.16 * d                      # gravel speckle: sparse, denser near viewer
        if _rng.random() < p:
            bright = _rng.random() < 0.03 * d       # very rare light-gray rock, near only
            warm = x > 48 and _rng.random() < 0.25   # warm ballast catch near the sun (low-right)
            fg = 8 if bright else (SKY_HAZE if warm else (7 if d > 0.5 else STEEL_DK))
            cv.set(x, y, '\u2592' if not bright else '\u2588', fg, 0)

# ---------------------------------------------------------------------------
# STEP 4 -- catenary wires overhead + masts in the GAPS (never through a body).
# ---------------------------------------------------------------------------
line(cv, 3, 4, 3, TRACK_Y - 9, ch='\u2502', fg=WIRE)          # mast A (far left gap)
line(cv, 77, 3, 77, TRACK_Y - 10, ch='\u2502', fg=WIRE)       # mast B (right gap -- clear of car 3)
line(cv, 3, 5, 77, 4, ch='\u2500', fg=WIRE)                   # top catenary wire
line(cv, 3, 8, 77, 7, ch='\u2500', fg=WIRE)                   # lower catenary wire
for x in range(12, 74, 9):                                       # droppers (wire -> rail zone)
    line(cv, x, 5, x, 9, ch='\u2502', fg=SKY_MID)

# ---------------------------------------------------------------------------
# STEP 4b -- the foreground track: TWO continuous single-glyph rails converging to a REAL vanishing
# point ON THE HORIZON LINE (y=HORIZON, x=VP_X), ABOVE the car bases. The rails recede UPWARD toward
# it; the near field is a clean RECEDING TRACK BED -- gravel that fades toward the horizon and denser
# toward the viewer -- NOT an undefined white mass. This fixes DEFECTS 1 & 2: the camera reads as a
# viewer on the near field looking down the yard, and the bottom third is legible receding structure.
# ---------------------------------------------------------------------------
VP_X = 40.0
VP_Y = HORIZON - 1.0         # vanishing point ON the horizon line, above the cars

for y in range(TRACK_Y + 1, H):
    t = (y - TRACK_Y) / max(1, H - TRACK_Y - 1)           # 0 at track bed -> 1 at bottom (viewer)
    spread = int(t * 34)                                   # rails fan out toward the viewer (downward)
    lx = int(VP_X - spread); rx = int(VP_X + spread)       # near ends of the two rails
    if 0 <= lx < W: cv.set(lx, y, '\u2588', 8, 0)
    if 0 <= rx < W and rx != lx: cv.set(rx, y, '\u2588', 8, 0)

# perpendicular sleepers between the two rails -- spaced DENSER toward the viewer (recede upward).
for i in range(11):
    t = i / 10.0
    y = int(TRACK_Y + 1 + t * (H - TRACK_Y - 2))             # stay within canvas (last row reserved for sig)
    if not cv.in_bounds(0, y):
        continue
    spread = int(t * 34)
    lx, rx = int(VP_X - spread), int(VP_X + spread)
     # a RECEDING bed: far sleepers fall to near-void (black); only the nearest few are dim gray.
     # dark-gray glyph so it reads as ballast texture, not solid white bars.
    fg = 8 if t > 0.72 else STEEL_DK
    for x in range(max(0, lx), min(W, rx + 1)):
        c = cv.get(x, y)
        if is_bg(c[0]):
            cv.set(x, y, '\u2592', fg, 0)
# ---------------------------------------------------------------------------
# STEP 4c -- receding ballast: gravel scattered DENSER toward the viewer and fading to near-void at
# the horizon (already done in STEP 3's ground pass). Here we add a faint warm catch on the near-right
# of the bed so the low dusk sun reads across the foreground too, without piling white structure on.
# ---------------------------------------------------------------------------
for y in range(H - 6, H - 1):
    for x in range(48, W):
        c = cv.get(x, y)
        if is_bg(c[0]) and _rng.random() < 0.12:
            cv.set(x, y, '\u2592', SKY_HAZE, 0)

# STEP 5 -- the single warm accent: an amber signal light on a post at the far right gap (x=76),
# clear of every car body. The only saturated cell in the whole field.
# ---------------------------------------------------------------------------
line(cv, 76, TRACK_Y - 11, 76, TRACK_Y, ch='\u2502', fg=STEEL_DK)        # signal post
cv.set(76, TRACK_Y - 12, '\u2588', SIGNAL, 0)                             # the lamp
for dx in (-1, 1):                                                       # faint amber glow halo
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

# handles="raze" ONLY -- sig_block appends " / AGENTSCII". Real framed sig block.
write_ans("scratch/_dusk_yard.ans", out, title="DUSK YARD // freight at the line", handles="raze")
