#!/usr/bin/env python3
# _emberwatch.py -- raze solo. EMBERWATCH // "the fire that keeps the dark at bay."
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
# warm inverse of CRYO's frost lattice (which radiates outward and dissolves). This is the
# hook hollis can add a pass to next.
#
# NO CLAIMED ANATOMY -- commits fully to what's on screen: a bonfire (crossed charred logs,
# a teardrop flame, glowing embers on the ground) in a textured night (starfield + rising
# smoke haze). Blind-check safe like CRYO.
#
# PASSES (METHODOLOGY), verified by eye with preview_piece at each:
#   P1 flat silhouettes -> verify massing; P2 shade every surface from the ONE fire source
#   (warm ramp, hot at base -> red tips); P3 constructed detail (inner flame tongues, rising
#   spark lattice, ember glow, smoke haze); P4 texture the void (starfield + smoke so it's
#   not flat black); P5 frame + title card + house sig.
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
WARM = [   # (threshold, glyph, fg index)  -- checked high->low
    (0.86, "\u2588", 15),   # white-hot core
    (0.70, "\u2588", 11),   # bright yellow
    (0.54, "\u2593", 11),   # amber (bright yellow -- NOT 10=green)
    (0.38, "\u2592", 9),    # bright red/orange
    (0.22, "\u2592", 1),    # dim red
    (0.00, "\u2591", 1),    # fading ember
]

def warm_shade(Lv):
    Lv = max(0.0, min(1.0, Lv))
    for thr, ch, fg in WARM:
        if Lv >= thr:
            return ch, fg
    return "\u2591", 1

# ---- P1: silhouette region functions (the massing), LEFT HALF ONLY ----------
TIP = 15.0            # flame tip row
BASE = 37.0           # flame base row (sits on the logs)

def flame(x, y):
    """Outer teardrop flame: pointed at the top, bulbous at the base, gentle flicker."""
    if y < TIP or y > BASE + 1:
        return False
    t = (y - TIP) / (BASE - TIP)              # 0 at tip -> 1 at base
    hw = 9.5 * math.sin(math.pi * (t ** 0.72))
    hw += 1.0 * math.sin(y * 1.1 + 1.3)         # gentle flicker wobble (small, smooth)
    return abs(x - CX) <= max(0.0, hw)

def inner_flame(x, y):
    """Bright core: narrower, only in the lower ~75% of the flame."""
    if y < TIP + (BASE - TIP) * 0.18 or y > BASE:
        return False
    t = (y - TIP) / (BASE - TIP)
    hw = 4.6 * math.sin(math.pi * (t ** 0.72)) + 0.3
    hw += 0.5 * math.sin(y * 1.6)
    return abs(x - CX) <= max(0.0, hw)

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
        for x in range(MID):
            if region_fn(x, y):
                cv.set(x, y, ch, fg, 0)

paint_flat(flame, fg=9)
paint_flat(inner_flame, fg=15)
paint_flat(logs, fg=8)
paint_flat(embers, fg=9, ch="\u2593")

# ---- P2: shade every lit surface from the ONE fire source -------------------
def shade_warm(region_fn):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                Lv = L(x, y)
                ch, fg = warm_shade(Lv)
                cv.set(x, y, ch, fg, 0)

shade_warm(flame)
# inner core: hotter -- lift the light so it reads white-hot at the heart
for y in range(H):
    for x in range(MID):
        if inner_flame(x, y):
            Lv = light_field(x, y, LX, LY, lmax=14.0, ambient=0.25)
            ch, fg = warm_shade(Lv + 0.15)
            cv.set(x, y, ch, fg, 0)

# logs: charred gray catching a warm rim from the fire (dim base, warm top edge)
for y in range(H):
    for x in range(MID):
        if logs(x, y):
            Lv = L(x, y)
            # charred wood: dim gray body, warm where the fire licks it
            ch, fg = shade(Lv, base_fg=8, hot_fg=9)
            cv.set(x, y, ch, fg, 0)

# ---- P3: constructed bright accents -----------------------------------------
# core bloom: a faint ring of light around the flame heart so it glows, not just dots
for y in range(H):
    for x in range(MID):
        d = math.hypot(x - CX, y - (BASE - 2))
        if 3.0 < d <= 5.0:
            cv.set(x, y, "\u2592", 11, 0)

# embers on the ground: glowing dots with a faint warm halo
for y in range(H):
    for x in range(MID):
        if embers(x, y):
            Lv = L(x, y)
            ch, fg = warm_shade(Lv + 0.1)
            cv.set(x, y, ch, fg, 0)

# ---- P3b: RISING SPARK LATTICE -- the NEW primitive (warm inverse of CRYO's frost lattice) ----
# Warm particles spawn at the flame tip, wander upward with sine drift, and thin/dim as they
# climb into the void. The heat ESCAPES upward -- the warm counter to CRYO's outward cold
# fracture. Each spark wanders (sine), rises a random reach, and cools from white->amber->red
# -> dim as it climbs. Drawn on top so it reads as a distinct rising scatter over the void.
def spark_lattice():
    n = 26
    for i in range(n):
        x0 = CX + random.uniform(-3.0, 3.0)      # spawn near the flame tip column
        y0 = TIP + random.uniform(0.0, 4.0)
        reach = random.uniform(8.0, 16.0)        # how far up it climbs
        drift = random.uniform(-2.5, 2.5)        # horizontal wander amplitude
        phase = random.uniform(0.0, 6.28)
        freq = random.uniform(0.6, 1.4)
        for s in range(int(reach * 2)):
            t = s / (reach * 2.0)                # 0 at spawn -> 1 at top of climb
            yy = y0 - reach * t                  # rising = decreasing y
            xx = x0 + drift * math.sin(t * 6.28 * freq + phase) * (0.4 + t)
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
# rising smoke haze above the flame tip -- dim gray, dissipating upward into the starfield.
for y in range(1, int(TIP)):
    for x in range(MID):
        # faint haze column that widens and thins as it rises
        spread = 3.0 + (TIP - y) * 0.5
        if abs(x - CX) <= spread and random.random() < 0.10:
            cv.set(x, y, "\u2591", 8, 0)

# sparse starfield in the upper sky -- dim blue/white points, never a band
random.seed(SEED + 3)
for _ in range(14):
    sx = random.randint(2, W - 3)
    sy = random.randint(1, int(TIP) - 2)
    cv.set(sx, sy, "*", 15 if random.random() < 0.3 else 7, 0)

# ---- P4b: GROUND PLANE -- the fire sits on scorched earth, not flat void -----
# A dim ground band under the logs with sparse scattered embers/ash so the base reads as
# "on the ground at night," grounding the whole composition. Left half only -> mirror keeps it symmetric.
for y in range(38, 45):
    for x in range(MID):
        d = abs(x - CX)
        # dim warm-tinted ground that fades with distance from the fire and toward the edges
        if random.random() < max(0.02, 0.16 * (1.0 - d / 40.0)):
            ch, fg = ("\u2591", 8) if random.random() < 0.7 else ("\u2593", 9)
            cv.set(x, y, ch, fg, 0)

# ---- P4c: WARM AMBIENT HALO -- the fire lights the air around it --------------
# A faint warm glow ring in the sky just around the flame so it reads as a light source
# illuminating its surroundings, not a colored shape on black. Left half only -> symmetric.
for y in range(2, H):
    for x in range(MID):
        d = math.hypot(x - CX, y - (BASE - 4))
        if 11.0 < d <= 17.0 and random.random() < 0.06 * (1.0 - d / 28.0):
            cv.set(x, y, "\u2591", 9, 0)

# ---- P4d: DENSER STARFIELD -- a real night sky, not a few dots ---------------
random.seed(SEED + 3)
for _ in range(30):
    sx = random.randint(1, MID - 1)
    sy = random.randint(1, int(TIP) - 2)
    cv.set(sx, sy, "*", 15 if random.random() < 0.3 else 7, 0)

# ---- MIRROR: copy the left half to the right for a symmetric bonfire --------
mirror(cv, axis='v')

# ---- P5: frame + title card -------------------------------------------------
out = []
cv.render(out)
write_ans("scratch/_emberwatch.ans", out, title="EMBERWATCH v1.0", handles="raze")
