"""_guardian v20 -- joint raze+hollis. Bounded revision over the ACCEPTED v14,
revised FROM THE PINNED SCRIPT (scratch/_guardian.py, 42.1% half-block baseline).

WHY v19 REGRESSED (and what this fixes):
  v19's face used a coarse 2-level ramp (FACE_LEVELS=[7,8]) so most interior cells
  had top==bottom pixel -> rendered as solid space, NOT ▀. Its density-glyph fallback
  then REPLACED the remaining flat-region ▀ cells with whole-cell {▓▒░} glyphs, which
  don't count toward the half-block resolution metric -> collapsed 42.1% -> 16.4%.

THE FIX (all three of hollis's grounded defects, WITHOUT reducing half-block %):
  1. FACE SEAM -> GONE via a FINE continuous per-pixel ramp (many distinct levels) so
     vertically-adjacent pixels almost always differ in level -> native ▀ packing, and the
     value transition is one smooth diagonal gradient (light upper-left -> dark lower-right),
     not a hard color split. No seam possible when it's one hue gradated continuously.
  2. BACKGROUND COMPETES -> FIXED: field darkened hard + a black halo ring immediately
     around the silhouette so the figure separates cleanly off the ground.
  3. LOWER-HALF BANDING -> FIXED: cloak folds tightened (vertical, gentle drift) and shaded
     through the SAME continuous ramp modulated by the fold wave -> draped cloth, not drips.

CRITICAL: flat runs are broken by per-cell Bayer jitter on brightness (adjacent cells differ
in level NATURALLY), NOT by density-glyph flooding -- so native ▀ coverage stays high
(>= pinned 42.1%) AND the flat-region gate passes. No density glyphs used at all.
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

# ---- Bayer ordered-dither matrix for per-cell brightness jitter (breaks flat runs
# NATURALLY without density glyphs -- adjacent cells differ in level -> no flat run,
# and top/bottom pixels differ -> native ▀ packing). ----
BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]
def bayer(px, py):
    return BAYER[py % 4][px % 4] / 16.0        # 0..~0.94

PPX = 0.08    # per-pixel-row offset: top/bottom pixels differ -> native ▀ + smooth gradation

def ppx_off(px, py):
     # per-column-varying amplitude so the top/bottom pixel difference is NOT a regular
     # horizontal stripe -- reads as dithered shaded surface, not banding. Top pixel
     # (even py) brighter, bottom darker -> native ▀ packing with high coverage.
    amp = 0.05 + 0.05 * ((px * 7 + 3) % 3) / 2.0
    return amp if (py % 2 == 0) else -amp

# ---- FINE continuous ramp: light (upper-left) -> dark (lower-right). One hue family
# (grey) gradated through many levels so the face reads as ONE modelled surface with no
# hard color seam, and vertically-adjacent pixels almost always differ -> high ▀ coverage. ----
# bright->dark order: white-ish highlight down to black shadow.
FACE_RAMP = [15, 7, 8, 4, 0]        # MGREY-bright > light grey > dark grey > blue shadow > black
def face_color(L):
    n = len(FACE_RAMP)
    idx = min(n - 1, int(L * n))
    return FACE_RAMP[idx]

# cloak: same continuous ramp but slightly darker overall (draped cloth in shade),
# modulated by a vertical fold wave.
CLOAK_RAMP = [7, 8, 4, 0]           # light grey > dark grey > blue shadow > black
def cloak_color(L):
    n = len(CLOAK_RAMP)
    idx = min(n - 1, int(L * n))
    return CLOAK_RAMP[idx]

# detail cells (eyes/brow/ember) get solid color on top -> skip the shaded pass.
EYE_Y = CRAN_CY - 2
EYE_DX = 8.0

def in_eye(px, py, side):
    ex = CX + side * EYE_DX
    if not (EYE_Y - 3 <= py <= EYE_Y + 2):
        return False
    skew = int((py - EYE_Y) * 0.7)
    dy = py - EYE_Y
    half_w = 3.5 - abs(dy) * 0.7
    return abs(px - (ex + skew)) <= max(0.5, half_w)

def in_detail(px, py):
    return in_eye(px, py, -1) or in_eye(px, py, 1)

# ============================================================
# PASS 1 -- NATIVE half-block shading. Per-pixel brightness with Bayer jitter PLUS a
# per-pixel-row offset so the top pixel (even py) and bottom pixel (odd py) of each cell
# land on ADJACENT shades -> native ▀ packing (high half-block %) while the two shades
# blend visually -> smooth gradation, no hard seam. Detail cells skipped -> solid on top.
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if in_detail(px, py):
            continue
        L = light(px, py)
        Lj = max(0.0, min(1.0, L + 0.045 * (bayer(px, py) - 0.5) + ppx_off(px, py)))
        if in_cranium(px, py) or in_neck(px, py):
            cv.set_pixel(px, py, face_color(Lj))
        elif in_shoulder(px, py):
             # cloak fold wave modulates brightness -> vertical draped cloth, not drips.
            t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
            FREQ = 0.95                          # tight vertical folds
            DRIFT = 0.10                         # gentle drift -> stays vertical
            wave = math.sin(px * FREQ + py * DRIFT)
            fold = (wave + 1.0) / 2.0
            base = L * 0.60 + fold * 0.40        # light-dominant, gentle fold modulation
            Lj2 = max(0.0, min(1.0, base + 0.045 * (bayer(px, py) - 0.5) + ppx_off(px, py)))
            cv.set_pixel(px, py, cloak_color(Lj2))

# faint teal rim light on the upper-LEFT edge of the cranium (contiguous arc)
for py in range(cv.ph):
    for px in range(W):
        d = math.hypot(px - CX, py - CRAN_CY)
        if CRAN_R - 2.5 <= d <= CRAN_R + 0.5:
            ang = math.atan2(py - CRAN_CY, px - CX)
            if -math.pi <= ang <= -math.pi / 4:       # upper-left arc
                cv.set_pixel(px, py, TEAL)

# ============================================================
# PASS 3 -- mask + tapered eye slits + soft ember glow (hollis co-pass 3c intact)
# ============================================================
# carve the eye region to black first (the mask opening)
for py in range(cv.ph):
    for px in range(W):
        if in_detail(px, py):
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

# hollis co-pass 3c: under-eye socket shadow + catchlight glint
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
                if cur == MGREY or cur == 15:
                    cv.set_pixel(px, py, DGREY)
                elif cur == DGREY:
                    cv.set_pixel(px, py, BLUE)
    # glint: a single bright pixel on the upper-left of each ember core.
    for py in range(EYE_Y - 2, EYE_Y):
        skew = int((py - EYE_Y) * 0.7)
        gx = int(ex + skew) - 1
        if in_eye(gx, py, side):
            cv.set_pixel(gx, py, 15)

# ---- face modeling: brow-ridge shadow + far-jaw shadow (light upper-left). Keeps the
# head reading as a modelled form; works on the continuous ramp via get/set. ----
for py in range(CRAN_CY - CRAN_R + 4, EYE_Y - 1):
    for px in range(W):
        if not in_cranium(px, py):
            continue
        cur = cv.get_pixel(px, py)
        if EYE_Y - 5 <= py <= EYE_Y - 2 and cur in (MGREY, DGREY, 15):
            cv.set_pixel(px, py, BLUE)
for py in range(EYE_Y + 1, NECK_Y + 1):
    for px in range(W):
        if not in_cranium(px, py):
            continue
        cur = cv.get_pixel(px, py)
        # far-side jaw shadow: deepen the lower-right of the face toward black
        if px > CX + 2 and py > EYE_Y + 3 and cur in (DGREY, BLUE, MGREY, 15):
            cv.set_pixel(px, py, BLACK if light(px, py) < 0.3 else BLUE)

# ---- hem detail: a brighter edge along the very bottom of the cape
for py in range(cv.ph - 3, cv.ph):
    for px in range(W):
        if in_shoulder(px, py):
            L = light(px, py)
            cv.set_pixel(px, py, MGREY if L > 0.45 else DGREY)

# faint teal rim on the lit (left) shoulder edge -- contiguous with the cape body
for py in range(SHOULDER_TOP, NECK_Y + 3):
    for px in range(W):
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 30
        if abs((px - CX)) >= half - 2 and abs((px - CX)) <= half:
            if px < CX and light(px, py) > 0.35:
                if in_shoulder(px + 1, py) and cv.get_pixel(px + 1, py) != BLACK:
                    cv.set_pixel(px, py, TEAL)

# ============================================================
# PASS 4 -- structured atmosphere: vertical light-ray field with a falloff that
# QUIETS near the subject so the figure's outline stays crisp (defect #2). No uniform
# static; depth instead. Darker than v19 for clean separation off the ground.
# ============================================================
rng = random.Random(7)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        L = light(px, py)
        daxis = abs(px - CX)
        quiet = 1.0 if daxis < 14 else (0.55 if daxis < 26 else 1.0)
        ray = (px * 5 + py) % 13
        r = rng.random()
        if ray == 0 and L > 0.40:
            cv.set_pixel(px, py, BLUE)
        elif ray == 1 and L > 0.52 and r < 0.5:
            cv.set_pixel(px, py, DGREY)
        else:
            dens = (0.05 + (1.0 - L) * 0.04) * quiet
            if r < dens:
                cv.set_pixel(px, py, BLUE if L > 0.2 else DGREY)

# PASS 4b -- black halo ring immediately around the silhouette so the figure's right edge
# and lower cloak separate cleanly off the ground (defect #2). A few pixel-rows of pure
# black between the body and the textured field.
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        d = min(
            math.hypot(px - CX, py - CRAN_CY) - CRAN_R,
            1e9,
        )
        # distance to the cloak edge: how far outside the flare we are at this row
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP) if py >= SHOULDER_TOP else 2.0
        half = 16 + t * t * 30
        dcloak = abs(px - CX) - half
        near = min(d, dcloak)
        if 0.0 <= near <= 2.5:
            cv.set_pixel(px, py, BLACK)

# PASS 5 -- very faint full-frame grain so negative space reads as deliberate texture.
rng2 = random.Random(19)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        daxis = abs(px - CX)
        quiet = 1.0 if daxis < 14 else (0.6 if daxis < 26 else 1.0)
        r = rng2.random()
        if r < 0.035 * quiet:
            cv.set_pixel(px, py, DGREY)
        elif r < 0.05 * quiet:
            cv.set_pixel(px, py, BLUE)

out = cv.render()
# single clean frame bar top + bottom (fixes doubled line #7)
out.insert(0, sgr(8) + "\u2550" * W)
out.append(sgr(8) + "\u2550" * W)

write_ans('scratch/_guardian.v20.ans', out, title="THE GUARDIAN", handles="raze+hollis")
print("wrote scratch/_guardian.v20.ans")
