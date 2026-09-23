"""_guardian -- a masked guardian bust, muted/dim cold palette with a single
warm ember eye-glow. Joint raze+hollis. From a random_direction roll:
subject 'a masked figure or guardian bust', technique 'pure from-scratch
composition', palette 'muted/dim, low-saturation'.

Honors the 'pure composition' spirit but uses HalfBlockCanvas for the round
cranium (house direction mandates half-block for curves). Built in PASSES:
   1. flat silhouette block-in (verify composition reads)
   2. directional shade from one light source (upper-left), density ramp
   3. mask detail + eye slits + ember glow
   4. atmosphere texture field + frame/title-card

Muted palette: cold blue-grey body, faint teal rim light upper-left, single
warm amber ember in the eye slits as the only hot point. Low saturation
throughout -- no rainbow flooding.
"""
import sys, math, random
sys.path.insert(0, 'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr, write_ans

W = 80
H = 40
cv = HalfBlockCanvas(W, H, bg=0)     # pixel space: 80 x 80

# ---- palette (muted / dim) ----
BLACK    = 0
DGREY    = 8        # dark grey body base
MGREY    = 7        # light grey highlight
BLUE     = 4        # cold blue shadow
TEAL     = 6        # faint cyan rim light (upper-left)
EMBER    = 3        # warm amber -- the ONE hot point (eye glow)
EMBER_H  = 11       # bright yellow core of the ember

# ---- composition geometry (pixel space, square units) ----
CX          = W // 2     # 40
CRAN_CY     = 26         # cranium center y
CRAN_R      = 18         # cranium radius
NECK_Y      = CRAN_CY + CRAN_R - 2
SHOULDER_TOP = 52        # where the shoulders/chest begin

# light source: upper-left, fixed for the whole piece
LX, LY = 14.0, 10.0

def light(px, py):
    d = math.hypot(px - LX, py - LY)
    lmax = 70.0
    return max(0.0, 1.0 - d / lmax)

def in_cranium(px, py):
    return math.hypot(px - CX, py - CRAN_CY) <= CRAN_R

def in_neck(px, py):
    if not (NECK_Y - 4 <= py <= SHOULDER_TOP + 2):
        return False
    half = 7 + (py - NECK_Y) * 0.15
    return abs(px - CX) <= half

def in_cloak(px, py):
      # Cloak/cape: shoulders widen into a full body that fills the frame
      # down to the bottom edge -- a dramatic guardian silhouette.
    if not (SHOULDER_TOP <= py < cv.ph):
        return False
    t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
      # shoulders narrow at top, flare wide at the hem
    half = 20 + t * t * 34
    return abs(px - CX) <= half

# keep the old name as an alias so the rest of the code is untouched
in_shoulder = in_cloak

def in_silhouette(px, py):
    return in_cranium(px, py) or in_neck(px, py) or in_shoulder(px, py)

# ---- directional shade ramps ----
def head_shade(px, py):
    L = light(px, py)
    if L > 0.62:
        return MGREY            # lit highlight (light grey)
    if L > 0.40:
        return DGREY
    if L > 0.20:
        return BLUE             # cold shadow
    return BLACK

def shoulder_shade(px, py):
    L = light(px, py)
    if L > 0.55:
        return DGREY
    if L > 0.32:
        return BLUE
    return BLACK

# ============================================================
# PASS 1 + 2 -- silhouette block-in then directional shade
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if in_cranium(px, py) or in_neck(px, py):
            cv.set_pixel(px, py, head_shade(px, py))
        elif in_shoulder(px, py):
            cv.set_pixel(px, py, shoulder_shade(px, py))

# faint teal rim light on the upper-LEFT edge of the cranium
for py in range(cv.ph):
    for px in range(W):
        d = math.hypot(px - CX, py - CRAN_CY)
        if CRAN_R - 2.5 <= d <= CRAN_R + 0.5:
            ang = math.atan2(py - CRAN_CY, px - CX)
             # upper-left arc: negative x AND negative y -> third quadrant
            if -math.pi <= ang <= -math.pi/4:
                cv.set_pixel(px, py, TEAL)

# ============================================================
# PASS 3 -- mask + eye slits + ember glow (the one hot point)
# ============================================================
EYE_Y = CRAN_CY - 1
EYE_DX = 8

def in_eye(px, py, side):
    ex = CX + side * EYE_DX
    if not (EYE_Y - 3 <= py <= EYE_Y + 1):
        return False
    skew = int((py - EYE_Y) * 0.6)
    return abs(px - (ex + skew)) <= 4

# carve the eye region to black first (the mask opening)
for py in range(cv.ph):
    for px in range(W):
        if in_eye(px, py, -1) or in_eye(px, py, 1):
            cv.set_pixel(px, py, BLACK)

# ember glow inside the slits: bright core fading to amber
for py in range(cv.ph):
    for px in range(W):
        for side in (-1, 1):
            if in_eye(px, py, side):
                ex = CX + side * EYE_DX
                skew = int((py - EYE_Y) * 0.6)
                d = math.hypot(px - (ex + skew), py - EYE_Y)
                cv.set_pixel(px, py, EMBER_H if d < 1.5 else EMBER)

# faint ember halo just outside the slits
for py in range(cv.ph):
    for px in range(W):
        for side in (-1, 1):
            ex = CX + side * EYE_DX
            d = math.hypot(px - ex, py - EYE_Y)
            if 5.0 <= d <= 8.0 and in_cranium(px, py):
                cur = cv.get_pixel(px, py)
                if cur == BLACK or cur == BLUE:
                    cv.set_pixel(px, py, EMBER)

# mask seam: vertical line down cranium center + brow ridge shading
for py in range(CRAN_CY - CRAN_R + 3, NECK_Y):
    for dx in (-1, 0, 1):
        if in_cranium(CX + dx, py):
            cur = cv.get_pixel(CX + dx, py)
            if cur != BLACK:
                cv.set_pixel(CX + dx, py, BLUE if cur == MGREY else DGREY)

# ============================================================
# ============================================================
# PASS 3b -- cloak/cape: directional shade + folds + hem
# The cape was a flat blue block; give it real form. Same upper-left
# light source as the head, so the lit shoulder catches grey while the
# far side falls to deep blue/black. Vertical fold lines follow the flare
# of the shoulders down to the hem; a bright hem edge caps the bottom.
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if not in_shoulder(px, py):
            continue
        L = light(px, py)
        # directional base shade on the cape body (one hue family: blue->grey)
        if L > 0.58:
            col = MGREY
        elif L > 0.40:
            col = DGREY
        elif L > 0.24:
            col = BLUE
        else:
            col = BLACK
        # vertical fold lines following the flare -- folds widen with the cape
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 20 + t * t * 34
        rel = (px - CX) / max(1.0, half)          # -1..1 across the cape
        fold = abs((rel * 6.0) % 2.0 - 1.0)       # 0 at fold center, 1 between
        if fold < 0.18:                            # a fold crease (dark)
            col = BLACK if col != BLACK else BLUE
        elif fold > 0.92 and L > 0.30:            # fold highlight ridge
            col = DGREY if col == BLUE else MGREY
        cv.set_pixel(px, py, col)

# hem detail: a brighter edge along the very bottom of the cape
for py in range(cv.ph - 3, cv.ph):
    for px in range(W):
        if in_shoulder(px, py):
            L = light(px, py)
            cv.set_pixel(px, py, MGREY if L > 0.45 else DGREY)

# faint teal rim on the lit (left) shoulder edge, matching the cranium rim
for py in range(SHOULDER_TOP, cv.ph):
    for px in range(W):
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 20 + t * t * 34
        if abs((px - CX)) >= half - 2 and abs((px - CX)) <= half:
            if px < CX and light(px, py) > 0.35:   # lit left edge only
                cv.set_pixel(px, py, TEAL)

# ---- PASS 4 -- atmosphere texture field + frame/title-card
# Faint structured diagonal streak field -- sparse, dim, balanced.
# Streaks run along (px*3+py*7) so they read as light rays, not static.
# ============================================================
rng = random.Random(7)
for py in range(cv.ph):
    for px in range(W):
        if not in_silhouette(px, py):
            L = light(px, py)
            diag = (px * 3 + py * 7) % 17
            r = rng.random()
                # lit side: brighter streaks; everywhere: a faint dither so the
                # whole frame carries texture instead of going dead black.
            if diag == 0 and L > 0.35:
                cv.set_pixel(px, py, BLUE)
            elif diag == 1 and L > 0.45 and r < 0.5:
                cv.set_pixel(px, py, DGREY)
            else:
                  # base dither density falls off with light but never hits zero
                dens = 0.07 + (1.0 - L) * 0.06
                if r < dens:
                    cv.set_pixel(px, py, BLUE if L > 0.2 else DGREY)

# PASS 5 -- full-frame faint grain so the negative space reads as deliberate
# texture, not empty black. Very low density, dim colors only (muted).
rng2 = random.Random(19)
for py in range(cv.ph):
    for px in range(W):
        if not in_silhouette(px, py):
            r = rng2.random()
            if r < 0.04:
                cv.set_pixel(px, py, DGREY)
            elif r < 0.055:
                cv.set_pixel(px, py, BLUE)

out = cv.render()
# top + bottom frame bars
out.insert(0, sgr(8) + "\u2550" * W)
out.append(sgr(8) + "\u2550" * W)

write_ans('scratch/_guardian.ans', out, title="THE GUARDIAN",
          handles="raze+hollis / AGENTSCII")
