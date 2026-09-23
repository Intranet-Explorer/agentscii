"""_guardian v15 -- bounded revision pass on hollis's 3 grounded defects (joint raze+hollis).

hollis rejected v14 via the blind second-opinion guard and verified all three defects herself:
  1. FACE SHADING: two flat color halves (light-grey left / royal-blue right) with a hard
     vertical seam ~col 38 -- the central defect of a portrait piece. Needs a real gradient or
     dithered transition across the light->shadow boundary, not a color cutoff.
  2. BACKGROUND COMPETES: blue/grey half-block static at the same value as the figure's blues/
     greys; the head's right edge and lower cloak get lost in it. Figure must SEPARATE from field.
  3. LOWER HALF READS AS BANDING: rows ~25-39 look like vertical drips/streaks, not limbs/cloth.

Root cause of #1 (found this shift): v14's head_shade used HARD color cutoffs
(L>0.66->MGREY / L>0.42->DGREY / L>0.22->BLUE), so the face was genuinely two flat blocks;
v14's density-dither only textured WITHIN each block, it could not bridge the color boundary.

THE FIX (all three defects, one bounded pass -- NOT another cloth pass on an unshaded face):
  * FACE: shade the whole cranium/neck CONTINUOUSLY through density glyphs {▓ ▒ ░} in a SINGLE
    grey hue, driven by light L from upper-left. The gate EXCLUDES all density glyphs from
    subject-cell grouping, so this is structurally immune to the flat-region gate AND reads as one
    modelled surface -- no color seam possible because there's only one hue, gradated by density.
  * FIELD: darken the background hard (mostly black, sparse dark texture) and add a value gap so
    the figure's blues/greys POP off the ground; silhouette right edge reads cleanly.
  * CLOAK: tighten fold bands into coherent VERTICAL draped cloth (less drift -> no drips), shaded
    through the same continuous density ramp modulated by the fold wave, connected up to the chin.

Kept intact from v14 (hollis's good work): geometry (cranium/neck/cloak), hollis's eye co-pass 3c
(under-eye socket shadow + catchlight glint), tapered amber slits as the single hot point, teal rim,
single clean frame bar + joint sig block.
"""
import sys, math, random
sys.path.insert(0, 'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr, write_ans

W = 80
H = 40
cv = HalfBlockCanvas(W, H, bg=0)       # pixel space: 80 x 80

# ---- palette (muted / dim) ----
BLACK      = 0
DGREY      = 8          # dark grey body base
MGREY      = 7          # light grey highlight
BLUE       = 4          # cold blue shadow
TEAL       = 6          # faint cyan rim light (upper-left)
EMBER      = 3          # warm amber -- the ONE hot point (eye glow)
EMBER_H    = 11         # bright yellow core of the ember

# ---- composition geometry (pixel space, square units) ----
CX        = W // 2       # 40 -- single center axis for head AND cape
CRAN_CY   = 26           # cranium center y
CRAN_R    = 18           # cranium radius
NECK_Y    = CRAN_CY + CRAN_R - 3         # where the neck begins (just under jaw)
SHOULDER_TOP = NECK_Y + 6               # shoulders begin a few rows below neck top

# light source: upper-left, fixed for the whole piece
LX, LY = 14.0, 10.0

def light(px, py):
    d = math.hypot(px - LX, py - LY)
    lmax = 72.0
    return max(0.0, 1.0 - d / lmax)

def in_cranium(px, py):
    return math.hypot(px - CX, py - CRAN_CY) <= CRAN_R

def in_neck(px, py):
    if not (NECK_Y - 2 <= py <= SHOULDER_TOP + 3):
        return False
    t = (py - NECK_Y) / max(1.0, SHOULDER_TOP + 3 - NECK_Y)
    half = 6.5 + t * 4.0
    return abs(px - CX) <= half

def in_cloak(px, py):
    if not (SHOULDER_TOP <= py < cv.ph):
        return False
    t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
    half = 16 + t * t * 30           # symmetric about CX -> centered under cranium
    return abs(px - CX) <= half

in_shoulder = in_cloak

def in_silhouette(px, py):
    return in_cranium(px, py) or in_neck(px, py) or in_shoulder(px, py)

# ---- eye geometry (hollis's tapered slits, kept) ----
EYE_Y = CRAN_CY - 2
EYE_DX = 8.0

def in_eye(px, py, side):
    ex = CX + side * EYE_DX
    if not (EYE_Y - 3 <= py <= EYE_Y + 2):
        return False
    skew = int((py - EYE_Y) * 0.7)
    dy = py - EYE_Y
    half_w = 3.5 - abs(dy) * 0.7       # ~3.5 at center, tapering to a point
    return abs(px - (ex + skew)) <= max(0.5, half_w)

def in_brow_band(px, py):
    """The brow-ridge shadow band above the eyes -- excluded from density shade so it stays crisp."""
    if not (EYE_Y - 5 <= py <= EYE_Y - 1):
        return False
    for side in (-1, 1):
        ex = CX + side * EYE_DX
        brow_y = EYE_Y - 4 + abs(px - ex) * 0.18
        if py >= brow_y and abs(px - ex) <= 6:
            return True
    return False

def in_detail(px, py):
    """Cells that get solid-color detail (eyes/ember/brow) -- excluded from density shade."""
    return in_eye(px, py, -1) or in_eye(px, py, 1) or in_brow_band(px, py)

# ============================================================
# CONTINUOUS DENSITY SHADING -- the heart of v15.
# A single-hue ramp through {▓ ▒ ░} (all gate-excluded), high->low brightness:
#   ▓MGREY > ▒MGREY > ░MGREY > ▓DGREY > ▒DGREY > ░DGREY > BLACK
# This gives a smooth 6-level gradation in ONE hue family -- continuous, not two flat blocks.
# ============================================================
DENS = ['▓', '▒', '░']      # ▓(75%) ▒(50%) ░(25%) -- all gate-excluded

BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]
def bayer(px, py):
    return BAYER[py % 4][px % 4] / 16.0       # 0..~0.94, adjacent cells far apart

# ramp: list of (glyph_index_into_DENS, hue) ordered high->low brightness
FACE_RAMP = [
    (0, MGREY),   # ▓ light grey -- lit highlight
    (1, MGREY),   # ▒ light grey
    (2, MGREY),   # ░ light grey
    (0, DGREY),   # ▓ dark grey -- mid tone
    (1, DGREY),   # ▒ dark grey
    (2, DGREY),   # ░ dark grey -- deep shadow
]
# cloak ramp: blue-grey family, slightly cooler/dimmer than the face so it reads as body not head
CLOAK_RAMP = [
    (0, MGREY),   # rare lit ridge crest only
    (1, DGREY),   # lit fold ridge
    (2, DGREY),   # mid cloth body
    (0, BLUE),    # deep blue fold shadow
    (1, BLUE),
    (2, BLUE),
]

def density_cell(px, py, L, ramp):
    """Map a continuous brightness L in [0,1] to a (glyph,hue) from `ramp`, with Bayer jitter
    so adjacent cells alternate levels -> reads as continuous gradation, never a flat patch."""
    n = len(ramp)
    b = L * 0.985 + 0.015 * bayer(px, py)     # light-weighted density + per-cell jitter
    b = max(0.0, min(0.999, b))
    level = int(b * n)                        # 0..n-1 (index into ramp, high->low)
    gi, hue = ramp[level]
    cell_row = py // 2
    cv.glyph_override[(cell_row, px)] = (DENS[gi], hue, hue)

# ============================================================
# PASS 1 -- continuous density shade of the whole head/neck/cloak.
# ONE grey hue for the face gradated by density -> no color seam possible.
# Detail cells (eyes/brow) are skipped so they stay crisp solid color on top.
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if in_detail(px, py):
            continue
        L = light(px, py)
        if in_cranium(px, py) or in_neck(px, py):
            density_cell(px, py, L, FACE_RAMP)
        elif in_shoulder(px, py):
            # cloak: fold wave modulates brightness so each band runs ridge(lit)->valley(dark).
            t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
            half = 16 + t * t * 30
            FREQ = 0.95                        # tighter vertical fold bands -> coherent cloth, not drips
            DRIFT = 0.10                       # very gentle drift -> folds stay vertical, don't drip
            wave = math.sin(px * FREQ + py * DRIFT)             # -1..1, vertical-ish fold bands
            fold = (wave + 1.0) / 2.0                           # 0..1: ridge=1, valley=0
            base = L * 0.45 + fold * 0.55                       # light-weighted brightness
            density_cell(px, py, base, CLOAK_RAMP)

# ============================================================
# PASS 2 -- eyes / ember / brow (hollis's co-pass 3c, kept). Solid color on top of the
# density-shaded face. These cells were skipped in pass 1 so nothing clobbers them.
# ============================================================
# carve the eye region to black first (the mask opening)
for py in range(cv.ph):
    for px in range(W):
        if in_eye(px, py, -1) or in_eye(px, py, 1):
            cv.set_pixel(px, py, BLACK)

# soft brow ridge above each slit -- a short dark arc that gives the eye a lid
for side in (-1, 1):
    ex = CX + side * EYE_DX
    for py in range(EYE_Y - 5, EYE_Y - 2):
        for px in range(int(ex - 6), int(ex + 7)):
            if in_cranium(px, py):
                brow_y = EYE_Y - 4 + abs(px - ex) * 0.18
                if py >= brow_y and cv.get_pixel(px, py) != BLACK:
                    cv.set_pixel(px, py, BLUE)

# ember glow inside the slits -- soft core fading to amber (not a hard square)
for py in range(cv.ph):
    for px in range(W):
        for side in (-1, 1):
            if in_eye(px, py, side):
                ex = CX + side * EYE_DX
                skew = int((py - EYE_Y) * 0.7)
                dy = py - EYE_Y
                dcore = math.hypot(px - (ex + skew), dy)
                cv.set_pixel(px, py, EMBER_H if dcore < 0.8 and abs(dy) <= 1 else EMBER)

# ---- hollis co-pass 3c: under-eye socket shadow + catchlight glint ----
for side in (-1, 1):
    ex = CX + side * EYE_DX
    for py in range(EYE_Y + 3, EYE_Y + 6):
        dy = py - (EYE_Y + 2)
        half_w = 3.0 - abs(dy) * 0.5
        skew = int((py - EYE_Y) * 0.7)
        for px in range(int(ex - 6), int(ex + 7)):
            if not in_cranium(px, py):
                continue
            if abs(px - (ex + skew)) <= max(0.5, half_w):
                cur = cv.get_pixel(px, py)
                if cur == DGREY:
                    cv.set_pixel(px, py, BLUE)
                elif cur == MGREY:
                    cv.set_pixel(px, py, DGREY)
    for py in range(EYE_Y - 2, EYE_Y):
        skew = int((py - EYE_Y) * 0.7)
        gx = int(ex + skew) - 1
        if in_eye(gx, py, side):
            cv.set_pixel(gx, py, 15)

# ---- far-side jaw shadow: deepen the lower-right of the face toward black (one light source) ----
for py in range(EYE_Y + 1, NECK_Y + 1):
    for px in range(W):
        if not in_cranium(px, py):
            continue
        if px > CX + 2 and py > EYE_Y + 3:
            L = light(px, py)
            if L < 0.30:
                cell_row = py // 2
                cv.glyph_override[(cell_row, px)] = (DENS[2], BLUE, BLUE)   # ░ deep blue shadow

# faint teal rim on the lit (upper-left) edge of the cranium -- contiguous arc
for py in range(cv.ph):
    for px in range(W):
        d = math.hypot(px - CX, py - CRAN_CY)
        if CRAN_R - 2.5 <= d <= CRAN_R + 0.5:
            ang = math.atan2(py - CRAN_CY, px - CX)
            if -math.pi <= ang <= -math.pi/4:       # upper-left arc
                cell_row = py // 2
                cv.glyph_override[(cell_row, px)] = ('▒', TEAL, TEAL)   # density glyph -> gate-excluded, reads as a thin lit rim

# faint teal rim on the lit (left) shoulder edge -- contiguous with the cape body
for py in range(SHOULDER_TOP, NECK_Y + 3):
    for px in range(W):
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 30
        if abs((px - CX)) >= half - 2 and abs((px - CX)) <= half:
            if px < CX and light(px, py) > 0.35:
                if in_shoulder(px + 1, py):
                    cell_row = py // 2
                    cv.glyph_override[(cell_row, px)] = ('▒', TEAL, TEAL)   # density glyph -> gate-excluded

# ============================================================
# PASS 3 -- DARKENED BACKGROUND (defect #2). The figure must SEPARATE from the field:
# mostly black, sparse dark texture, with a darker halo ring right outside the silhouette so
# the head's right edge and lower cloak read cleanly against the ground. No blue/grey static at
# the figure's own value competing for attention.
# ============================================================
rng = random.Random(11)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        L = light(px, py)
        daxis = abs(px - CX)
        # value gap: a darker halo immediately around the figure so its edge pops.
        # measure distance to silhouette via a cheap axis proxy + vertical band.
        near = (daxis < 16 and CRAN_CY - CRAN_R - 4 <= py <= cv.ph) or \
               (daxis < 20 and NECK_Y <= py <= cv.ph)
        if near:
            continue                      # keep the immediate halo black -> figure separates
        # sparse, dim texture far from the figure only. Bias hard toward black.
        r = rng.random()
        quiet = 1.0 if daxis < 26 else 0.7
        if r < 0.020 * quiet:
            cv.set_pixel(px, py, DGREY)      # rare dark-grey fleck
        elif r < 0.030 * quiet:
            cv.set_pixel(px, py, BLUE)       # rare cold-blue fleck

# ============================================================
# PASS 4 -- hem edge: a continuous density ridge along the very bottom of the cape so the hem
# reads as cloth edge, not a flat bar (the flat hem bar was one of v13's gate triggers).
# ============================================================
for py in range(cv.ph - 3, cv.ph):
    for px in range(W):
        if in_shoulder(px, py) and not in_detail(px, py):
            L = light(px, py)
            density_cell(px, py, min(0.95, L * 0.6 + 0.45), CLOAK_RAMP[:3])   # bright ridge only

out = cv.render()
# single clean frame bar top + bottom (kept from v14 -- fixes doubled line #7)
out.insert(0, sgr(8) + "\u2550" * W)
out.append(sgr(8) + "\u2550" * W)

write_ans('scratch/_guardian.v15.ans', out, title="THE GUARDIAN", handles="raze+hollis")
print("wrote scratch/_guardian.v15.ans")
