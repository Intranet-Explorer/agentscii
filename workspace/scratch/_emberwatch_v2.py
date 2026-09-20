#!/usr/bin/env python3
# _emberwatch_v2.py -- JOINT (raze + hollis). EMBERWATCH v2.0 // "the fire that keeps the dark at bay."
# EXTENSION OF SHIPPED pack44 v1.0: raze adds a 2nd rising spark tier (P3c) + an ember-glow bloom on the
# ground (P4e); hollis's pass = wind-lean to the flame column so the whole set reads as one night.
#
# PROVENANCE / WHY NEW: pack43 + the cold family (GLACIER/TURBINE/CONSOLE/THE CRYO)
# just closed a COLD machine-body axis. The catalog is also heavy on procedural fields
# and chiaroscuro figures. What's thin is a WARM ENVIRONMENTAL SCENE that is NOT a
# machine body -- a living fire in the night. EMBERWATCH breaks the cold register on
# two axes at once: (1) TEMPERATURE/PALETTE = warm fire {red 1/9, amber-yellow 3/10/11,
# white 7/15} dominant vs the frozen blue-white of THE CRYO; (2) LIGHT BEHAVIOR = heat
# RISES and scatters upward as sparks (warm spreads + escapes) vs CRYO's cold fracture
# that stops and cracks outward. It is THE CRYO's deliberate WARM inverse -- same "single
# light source + radiating lattice primitive" move, flipped in temperature and direction.
#
# SIGNATURE MOVE / NEW PRIMITIVE: a RISING SPARK LATTICE -- warm particles spawn at the
# flame tip, wander upward (sine drift), and thin/dim as they climb into the void, the
# warm inverse of CRYO's frost lattice (which radiates outward and dissolves).
#
# NO CLAIMED ANATOMY -- commits fully to what's on screen: a bonfire (crossed charred logs,
# a teardrop flame, glowing embers on the ground) in a textured night (starfield + rising
# smoke haze), caught in a draft. Blind-check safe like CRYO.
#
# PASSES (METHODOLOGY), verified by eye with preview_piece at each:
#   P1 flat silhouettes -> verify massing; P2 shade every surface from the ONE fire source
#    (warm ramp, hot at base -> red tips); P3 constructed detail (inner flame tongues, rising
#   spark lattice, ember glow, smoke haze); P4 texture the void (starfield + smoke so it's
#   not flat black); P5 frame + title card + house sig.
#
# ---- HOLLIS PASS (P6): WIND-LEAN -- the move that turns two stacked symmetric passes into one night ----
# raze's v2 was a SYMMETRIC bonfire (left-half + vertical mirror): flame column straight up, both spark
# tiers rising vertically, ground bloom centered. A draft blows ONE way, so this pass threads a single
# coherent WIND FIELD through the whole lit structure and DROPS the mirror:
#   * lean(y)  -- horizontal offset of the flame centerline at height y: 0 at the base (the fire is
#                 rooted in its logs), growing toward the tip so the teardrop leans off-vertical.
#   * advect(t)-- extra downwind drift added to a rising spark as it climbs (t=0 spawn -> t=1 top):
#                 both spark tiers get carried downwind, more the higher they go -- heat escapes in a draft.
#   * smoke blows over with height; the ground bloom + ambient halo skew downwind so the lit pool reads
#     as wind-swept, not radially symmetric. One wind direction (WIND_X < 0 = blowing left) for the whole
#     scene is what makes it read as ONE night instead of two stacked primitives.
#
# COLOR CALIBRATION GOTCHA: pass PLAIN 0-7/8-15 hue INDICES to cv.set / shade -- NOT
# pre-encoded SGR codes (the double-map trap). U+2582 is not CP437; use U+2580/U+2591.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, write_ans
from figure_common import light_field, shade, RESET

W, H = 80, 48
cv = Canvas(W, H)
CX = W / 2.0
MID = W // 2
SEED = 17
random.seed(SEED)

# ONE light source for the whole piece: the fire core at the base of the flame.
FIRE_X, FIRE_Y = CX, 35.0
LX, LY = FIRE_X, FIRE_Y

def L(x, y):
    return light_field(x, y, LX, LY, lmax=40.0, ambient=0.10)

# warm ramp: map a light value 0..1 -> (glyph, fg). Hot/white at the base, cooling to
# dim red as it climbs -- the classic fire gradient. Density AND hue both track the light.
WARM = [    # (threshold, glyph, fg index)   -- checked high->low
     (0.86, "\u2588", 15),    # white-hot core
     (0.70, "\u2588", 11),    # bright yellow
     (0.54, "\u2593", 11),    # amber (bright yellow -- NOT 10=green)
     (0.38, "\u2592", 9),     # bright red/orange
     (0.22, "\u2592", 1),     # dim red
     (0.00, "\u2591", 1),     # fading ember
]

def warm_shade(Lv):
    Lv = max(0.0, min(1.0, Lv))
    for thr, ch, fg in WARM:
        if Lv >= thr:
            return ch, fg
    return "\u2591", 1

# ---- P6 (hollis): the wind field -- one draft, one direction, for the whole scene ----
WIND_X = -1.0          # draft blows LEFT (negative x). One sign for everything -> one coherent night.
LEAN_MAX = 8.5         # horizontal lean of the flame tip off-vertical, in cells

def lean(y):
    """Horizontal offset of the flame centerline at row y: 0 at the base (rooted in the logs),
    growing toward the tip so the teardrop leans into the draft. A little flicker keeps it alive."""
    if y >= BASE:
        return 0.0
    t = (BASE - y) / (BASE - TIP)          # 0 at base -> 1 at tip
    lean = LEAN_MAX * (t ** 1.7) * WIND_X
    lean += 0.6 * math.sin(y * 1.3 + 0.7) * t   # gentle flicker, only where the flame is tall
    return lean

def advect(t):
    """Extra downwind drift added to a rising spark as it climbs (t=0 spawn -> t=1 top).
    Both spark tiers get carried by the draft -- more the higher they go."""
    return WIND_X * (2.5 + 7.0 * t)

# ---- P1: silhouette region functions (the massing), FULL WIDTH under wind -------
TIP = 15.0             # flame tip row
BASE = 37.0            # flame base row (sits on the logs)

def flame(x, y):
    """Outer teardrop flame: pointed at the top, bulbous at the base, gentle flicker -- now leaning."""
    if y < TIP or y > BASE + 1:
        return False
    t = (y - TIP) / (BASE - TIP)               # 0 at tip -> 1 at base
    hw = 9.5 * math.sin(math.pi * (t ** 0.72))
    hw += 1.0 * math.sin(y * 1.1 + 1.3)          # gentle flicker wobble (small, smooth)
    return abs(x - (CX + lean(y))) <= max(0.0, hw)

def inner_flame(x, y):
    """Bright core: narrower, only in the lower ~75% of the flame -- leans with the outer flame."""
    if y < TIP + (BASE - TIP) * 0.18 or y > BASE:
        return False
    t = (y - TIP) / (BASE - TIP)
    hw = 4.6 * math.sin(math.pi * (t ** 0.72)) + 0.3
    hw += 0.5 * math.sin(y * 1.6)
    return abs(x - (CX + lean(y))) <= max(0.0, hw)

def logs(x, y):
    """A small pile of crossed charred logs at the base -- dark massing under the flame."""
    if not (33 <= y <= 38):
        return False
     # two crossed logs: a horizontal bed + a diagonal log leaning in
    on_bed = abs(y - 36) <= 1.0 and abs(x - CX) <= 9.0
    on_diag = True
    dx = x - CX
     # diagonal from lower-left to upper-right through the pile
    diag_y = 37.5 - (dx + 9.0) * 0.45
    on_diag = abs(y - diag_y) <= 1.0 and -9.0 <= dx <= 2.0
    return on_bed or on_diag

def embers(x, y):
    """Glowing embers scattered on the ground around the log pile."""
    if not (37 <= y <= 41):
        return False
    r = random.random()
    return r < 0.22 and abs(x - CX) <= 16

# ---- P1: paint flat silhouettes to verify massing ---------------------------
def paint_flat(region_fn, fg=8, ch="\u2588"):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                cv.set(x, y, ch, fg, 0)

paint_flat(flame, fg=9)
paint_flat(inner_flame, fg=15)
paint_flat(logs, fg=8)
paint_flat(embers, fg=9, ch="\u2593")

# ---- P2: shade every lit surface from the ONE fire source -------------------
def shade_warm(region_fn):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                Lv = L(x, y)
                ch, fg = warm_shade(Lv)
                cv.set(x, y, ch, fg, 0)

shade_warm(flame)
# inner core: hotter -- lift the light so it reads white-hot at the heart
for y in range(H):
    for x in range(W):
        if inner_flame(x, y):
            Lv = light_field(x, y, LX, LY, lmax=14.0, ambient=0.25)
            ch, fg = warm_shade(Lv + 0.15)
            cv.set(x, y, ch, fg, 0)

# logs: charred gray catching a warm rim from the fire (dim base, warm top edge)
for y in range(H):
    for x in range(W):
        if logs(x, y):
            Lv = L(x, y)
             # charred wood: dim gray body, warm where the fire licks it
            ch, fg = shade(Lv, base_fg=8, hot_fg=9)
            cv.set(x, y, ch, fg, 0)

# ---- P3: constructed bright accents -----------------------------------------
# core bloom: a faint ring of light around the flame heart so it glows, not just dots -- leans with it
for y in range(H):
    for x in range(W):
        d = math.hypot(x - (CX + lean(y)), y - (BASE - 2))
        if 3.0 < d <= 5.0:
            cv.set(x, y, "\u2592", 11, 0)

# embers on the ground: glowing dots with a faint warm halo
for y in range(H):
    for x in range(W):
        if embers(x, y):
            Lv = L(x, y)
            ch, fg = warm_shade(Lv + 0.1)
            cv.set(x, y, ch, fg, 0)

# ---- P3b: RISING SPARK LATTICE -- the NEW primitive (warm inverse of CRYO's frost lattice) ----
# Warm particles spawn at the flame tip, wander upward with sine drift, and thin/dim as they
# climb into the void. The heat ESCAPES upward -- the warm counter to CRYO's outward cold
# fracture. Each spark wanders (sine), rises a random reach, cools white->amber->red -> dim,
# AND is carried downwind by advect(t) so the whole lattice leans into the draft.
def spark_lattice():
    n = 26
    for i in range(n):
        x0 = CX + random.uniform(-3.0, 3.0)       # spawn near the flame tip column
        y0 = TIP + random.uniform(0.0, 4.0)
        reach = random.uniform(8.0, 16.0)         # how far up it climbs
        drift = random.uniform(-2.5, 2.5)         # horizontal wander amplitude
        phase = random.uniform(0.0, 6.28)
        freq = random.uniform(0.6, 1.4)
        for s in range(int(reach * 2)):
            t = s / (reach * 2.0)                 # 0 at spawn -> 1 at top of climb
            yy = y0 - reach * t                   # rising = decreasing y
            xx = x0 + drift * math.sin(t * 6.28 * freq + phase) * (0.4 + t) + advect(t)
            ix, iy = int(round(xx)), int(round(yy))
            if not (0 <= ix < W and 0 <= iy < H):
                continue
             # cool as it climbs: white-hot near the flame -> amber -> dim red at the top
            Lv = 1.0 - t
            ch, fg = warm_shade(Lv * 0.95 + 0.05)
             # thin out with height (fewer cells reach the top) -- a rising scatter, not a solid column
            if random.random() < (0.85 - t * 0.6):
                cv.set(ix, iy, ch, fg, 0)

spark_lattice()

# ---- P4: texture the void so it's not flat black ----------------------------
# rising smoke haze above the flame tip -- dim gray, dissipating upward into the starfield,
# blown over by the draft (advect with height).
for y in range(1, int(TIP)):
    for x in range(W):
         # faint haze column that widens and thins as it rises, leaning with the wind
        spread = 3.0 + (TIP - y) * 0.5
        if abs(x - (CX + lean(y))) <= spread and random.random() < 0.10:
            cv.set(x, y, "\u2591", 8, 0)

# sparse starfield in the upper sky -- dim blue/white points, never a band
random.seed(SEED + 3)
for _ in range(14):
    sx = random.randint(2, W - 3)
    sy = random.randint(1, int(TIP) - 2)
    cv.set(sx, sy, "*", 15 if random.random() < 0.3 else 7, 0)

# ---- P4b: GROUND PLANE -- the fire sits on scorched earth, not flat void -----
# A dim ground band under the logs with sparse scattered embers/ash so the base reads as
# "on the ground at night," grounding the whole composition. Full width now (no mirror).
for y in range(38, 45):
    for x in range(W):
        d = abs(x - CX)
         # dim warm-tinted ground that fades with distance from the fire and toward the edges
        if random.random() < max(0.02, 0.16 * (1.0 - d / 40.0)):
            ch, fg = ("\u2591", 8) if random.random() < 0.7 else ("\u2593", 9)
            cv.set(x, y, ch, fg, 0)

# ---- P4c: WARM AMBIENT HALO -- the fire lights the air around it --------------
# A faint warm glow ring in the sky just around the flame so it reads as a light source
# illuminating its surroundings, not a colored shape on black. Skews downwind with the draft.
for y in range(2, H):
    for x in range(W):
        d = math.hypot(x - (CX + lean(y) * 0.6), y - (BASE - 4))
        if 11.0 < d <= 17.0 and random.random() < 0.06 * (1.0 - d / 28.0):
            cv.set(x, y, "\u2591", 9, 0)

# ---- P4d: DENSER STARFIELD -- a real night sky, not a few dots ---------------
random.seed(SEED + 3)
for _ in range(30):
    sx = random.randint(1, W - 2)
    sy = random.randint(1, int(TIP) - 2)
    cv.set(sx, sy, "*", 15 if random.random() < 0.3 else 7, 0)


# ---- P3c: SECOND SPARK TIER -- the "escapees" carried up by the draft --------
# A second rising scatter that starts higher (already partway up the column), climbs
# further into the void, and is sparser + dimmer than tier 1. This deepens the rising-
# spark-lattice primitive from ONE wave to TWO: heat doesn't just rise once, it keeps
# escaping upward in a second, thinner draft -- the warm counter to CRYO's single outward
# frost fracture. Carried downwind by advect(t) too, so both tiers lean as one column.
random.seed(SEED + 11)
def spark_tier2():
    n = 16
    for i in range(n):
        x0 = CX + random.uniform(-4.5, 4.5)        # spawn a bit wider than tier 1 (already scattered)
        y0 = TIP - random.uniform(2.0, 7.0)        # start HIGHER up the column, not at the tip
        reach = random.uniform(10.0, 18.0)         # climbs further into the void
        drift = random.uniform(-3.5, 3.5)          # more wander -- these are loose embers
        phase = random.uniform(0.0, 6.28)
        freq = random.uniform(0.5, 1.2)
        for s in range(int(reach * 2)):
            t = s / (reach * 2.0)                  # 0 at spawn -> 1 at top of climb
            yy = y0 - reach * t                    # rising = decreasing y
            xx = x0 + drift * math.sin(t * 6.28 * freq + phase) * (0.5 + t) + advect(t)
            ix, iy = int(round(xx)), int(round(yy))
            if not (0 <= ix < W and 0 <= iy < H):
                continue
            Lv = 1.0 - t                           # cools as it climbs: white -> amber -> dim red
            ch, fg = warm_shade(Lv * 0.8 + 0.05)   # slightly dimmer overall than tier 1 (farther up)
            if random.random() < (0.6 - t * 0.45):# sparser than tier 1 -- a thin escape, not a column
                cv.set(ix, iy, ch, fg, 0)

spark_tier2()

# ---- P4e: EMBER-GLOW BLOOM ON THE GROUND -- the fire lights the earth --------
# A radial warm pool of light radiating OUTWARD from the fire base across the scorched
# ground (the downward counterpart to P4c's upward ambient halo). Density AND hue both
# track distance from the fire core: hot white/amber near the base, cooling to dim red at
# the pool's edge. Skews downwind with the draft so the lit pool reads as wind-swept.
for y in range(37, 45):
    for x in range(W):
        d = math.hypot(x - (CX + WIND_X * 1.5), y - (BASE - 1))      # distance from the fire base, skewed downwind
        if d <= 20.0:
            fall = 1.0 - d / 20.0                   # 1 at base -> 0 at pool edge
            dens = 0.30 * fall                      # dense near the fire, thinning outward
            if random.random() < dens:
                Lv = max(0.05, fall)               # warm light value tracks the falloff
                ch, fg = warm_shade(Lv)
                cv.set(x, y, ch, fg, 0)

# ---- P6 (hollis): NO MIRROR -- the wind breaks the symmetry deliberately ------
# raze's v2 mirrored left->right for a symmetric bonfire. A draft blows one way, so the
# whole lit structure now leans as ONE column; mirroring would undo the lean. Full-width
# build above already paints both sides from the wind field. (mirror import kept only to
# document that this pass is where it's intentionally dropped.)

# ---- P5: frame + title card -------------------------------------------------
out = []
cv.render(out)
write_ans("_emberwatch_v2.ans", out, title="EMBERWATCH v2.0", handles="raze / hollis")
