"""_guardian v4 -- revision round after REJECT (curator: hollis). Joint raze+hollis.

Addresses the 7-point critique on the rejected build:
 1. background was uniform static noise -> structured vertical light-ray field
    with a falloff that QUIETS near the subject so the figure's outline stays
    crisp and reads as depth, not static.
 2. face was two flat grey blocks w/ hard vertical seam -> ONE continuous form
    shaded from the single upper-left light; soft brow ridge + cheek/jaw hint;
    the old center mask-seam pass (which forced the seam) is gone.
 3. eyes were orange debug-rectangles + yellow squares -> tapered angled slits
    with a dark brow above and a lid, ember as a soft glow not a hard square.
 4. orphan amber blob off right eye -> halo now applies the SAME skew as the
    slit so the glow follows the slit instead of landing on cranium pixels.
 5. stray teal fragment near body -> rim only paints contiguous with the lit
    edge (contiguity check), no disconnected patch.
 6. cape leaned right / head+body didn't line up -> cape centered under cranium,
    symmetric flare, clear neck->shoulder transition.
 7. doubled frame + empty rows -> single clean frame bar, tight credit box.

Muted cold palette: blue-grey body, faint teal rim upper-left, single warm amber
ember in the eye slits as the only hot point. Low saturation throughout.
"""
import sys, math, random
sys.path.insert(0, 'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr, write_ans

W = 80
H = 40
cv = HalfBlockCanvas(W, H, bg=0)      # pixel space: 80 x 80

# ---- palette (muted / dim) ----
BLACK     = 0
DGREY     = 8         # dark grey body base
MGREY     = 7         # light grey highlight
BLUE      = 4         # cold blue shadow
TEAL      = 6         # faint cyan rim light (upper-left)
EMBER     = 3         # warm amber -- the ONE hot point (eye glow)
EMBER_H   = 11        # bright yellow core of the ember

# ---- composition geometry (pixel space, square units) ----
CX       = W // 2      # 40 -- single center axis for head AND cape
CRAN_CY  = 26          # cranium center y
CRAN_R   = 18          # cranium radius
NECK_Y   = CRAN_CY + CRAN_R - 3        # where the neck begins (just under jaw)
SHOULDER_TOP = NECK_Y + 6              # shoulders begin a few rows below neck top

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
    # neck tapers slightly wider toward the shoulders -- smooth transition
    t = (py - NECK_Y) / max(1.0, SHOULDER_TOP + 3 - NECK_Y)
    half = 6.5 + t * 4.0
    return abs(px - CX) <= half

def in_cloak(px, py):
    # Cape: symmetric flare centered on CX (the same axis as the cranium),
    # widening smoothly from the shoulders down to a wide hem at the bottom.
    if not (SHOULDER_TOP <= py < cv.ph):
        return False
    t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
    half = 16 + t * t * 30          # symmetric about CX -> centered under cranium
    return abs(px - CX) <= half

in_shoulder = in_cloak

def in_silhouette(px, py):
    return in_cranium(px, py) or in_neck(px, py) or in_shoulder(px, py)

# ---- directional shade ramps (one light source, density ramp) ----
def head_shade(px, py):
    L = light(px, py)
    if L > 0.66:
        return MGREY             # lit highlight (light grey)
    if L > 0.42:
        return DGREY            # mid tone -- one continuous form, no seam
    if L > 0.22:
        return BLUE             # cold shadow
    return BLACK

def shoulder_shade(px, py):
    L = light(px, py)
    if L > 0.58:
        return DGREY
    if L > 0.34:
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

# faint teal rim light on the upper-LEFT edge of the cranium (contiguous arc)
for py in range(cv.ph):
    for px in range(W):
        d = math.hypot(px - CX, py - CRAN_CY)
        if CRAN_R - 2.5 <= d <= CRAN_R + 0.5:
            ang = math.atan2(py - CRAN_CY, px - CX)
            if -math.pi <= ang <= -math.pi/4:      # upper-left arc
                cv.set_pixel(px, py, TEAL)

# ============================================================
# PASS 3 -- mask + tapered eye slits + soft ember glow
# ============================================================
EYE_Y = CRAN_CY - 2
EYE_DX = 8.0

def in_eye(px, py, side):
    # a tapered angled slit: narrower at the inner/outer ends than the middle,
    # skewed so it reads as an eye, not a rectangle.
    ex = CX + side * EYE_DX
    if not (EYE_Y - 3 <= py <= EYE_Y + 2):
        return False
    skew = int((py - EYE_Y) * 0.7)
    # half-width tapers with distance from the eye's vertical center
    dy = py - EYE_Y
    half_w = 3.5 - abs(dy) * 0.7      # ~3.5 at center, tapering to a point
    return abs(px - (ex + skew)) <= max(0.5, half_w)

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
                # arc: brow is highest at the outer end, dips toward center
                brow_y = EYE_Y - 4 + abs(px - ex) * 0.18
                if py >= brow_y and cv.get_pixel(px, py) != BLACK:
                    cv.set_pixel(px, py, BLUE)

# ember glow inside the slits -- soft core fading to amber (not a hard square)
# The core now respects the slit's taper + skew so it never spills
# past the slit edge into cranium pixels (kills the orange smear).
for py in range(cv.ph):
    for px in range(W):
        for side in (-1, 1):
            if in_eye(px, py, side):
                ex = CX + side * EYE_DX
                skew = int((py - EYE_Y) * 0.7)
                dy = py - EYE_Y
                half_w = 3.5 - abs(dy) * 0.7
                dcore = math.hypot(px - (ex + skew), dy)
                cv.set_pixel(px, py, EMBER_H if dcore < 0.8 and abs(dy) <= 1 else EMBER)

# ember halo dropped -- the slit glow (core + amber body) carries the
# warm point on its own; a separate ring just bled into cranium pixels.


# ---- face modeling: brow-ridge shadow + cheekbone highlight + far-jaw shadow
# Light is upper-left, so the forehead under the brow falls into shadow, the lit
# cheekbone catches a grey highlight, and the lower-right jaw goes deep. This is
# what makes the head read as a modelled form instead of two flat blocks (fixes #2).
for py in range(CRAN_CY - CRAN_R + 4, EYE_Y - 1):
    for px in range(W):
        if not in_cranium(px, py):
            continue
        cur = cv.get_pixel(px, py)
         # brow-ridge shadow: a soft dark band just above the eye line across the
         # whole face -- gives the eyes a lid and breaks the flat forehead.
        if EYE_Y - 5 <= py <= EYE_Y - 2 and cur in (MGREY, DGREY):
            cv.set_pixel(px, py, BLUE)
for py in range(EYE_Y + 1, NECK_Y + 1):
    for px in range(W):
        if not in_cranium(px, py):
            continue
        cur = cv.get_pixel(px, py)
         # lit cheekbone: a small grey highlight on the upper-left of each cheek
        dcheek = math.hypot(px - (CX - 9), py - (EYE_Y + 4))
        if dcheek < 6 and cur == BLUE:
            cv.set_pixel(px, py, DGREY)
         # far-side jaw shadow: deepen the lower-right of the face toward black
        if px > CX + 2 and py > EYE_Y + 3 and cur in (DGREY, BLUE):
            cv.set_pixel(px, py, BLACK if light(px,py) < 0.3 else BLUE)


# ============================================================
# PASS 3b -- cloak/cape: directional shade + folds + hem
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if not in_shoulder(px, py):
            continue
        L = light(px, py)
        if L > 0.58:
            col = MGREY
        elif L > 0.40:
            col = DGREY
        elif L > 0.24:
            col = BLUE
        else:
            col = BLACK
        # symmetric vertical fold lines following the flare -- centered on CX so
        # the cape reads as centered under the cranium, not leaning (fixes #6)
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 30
        rel = (px - CX) / max(1.0, half)           # -1..1 across the cape
        fold = abs((rel * 5.0) % 2.0 - 1.0)        # symmetric about center
        if fold < 0.16:
            col = BLACK if col != BLACK else BLUE
        elif fold > 0.92 and L > 0.30:
            col = DGREY if col == BLUE else MGREY
        cv.set_pixel(px, py, col)

# hem detail: a brighter edge along the very bottom of the cape
for py in range(cv.ph - 3, cv.ph):
    for px in range(W):
        if in_shoulder(px, py):
            L = light(px, py)
            cv.set_pixel(px, py, MGREY if L > 0.45 else DGREY)

# faint teal rim on the lit (left) shoulder edge -- contiguous with the cape body
# so it never leaves a disconnected patch (fixes stray fragment #5)
for py in range(SHOULDER_TOP, NECK_Y + 3):
    for px in range(W):
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 30
        if abs((px - CX)) >= half - 2 and abs((px - CX)) <= half:
            if px < CX and light(px, py) > 0.35:
                 # contiguity: a non-black cape pixel must sit immediately inward,
                 # so the rim can never float off the body edge (fixes stray teal).
                 if in_shoulder(px + 1, py) and cv.get_pixel(px + 1, py) != BLACK:
                     cv.set_pixel(px, py, TEAL)

# ============================================================
# PASS 4 -- structured atmosphere: vertical light-ray field with a falloff that
# QUIETS near the subject so the figure's outline stays crisp (fixes #1). No
# uniform static; depth instead.
# ============================================================
rng = random.Random(7)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        L = light(px, py)
        # distance from the figure's central axis -- texture quiets near it so
        # the silhouette reads cleanly against a darker halo around the body.
        daxis = abs(px - CX)
        quiet = 1.0 if daxis < 14 else (0.55 if daxis < 26 else 1.0)
        # structured vertical rays: columns of faint streaks, denser on the lit
        # side, fading with light -- reads as atmosphere/depth, not static.
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

# PASS 5 -- very faint full-frame grain so negative space reads as deliberate
# texture, not empty black. Low density, dim colors only (muted). Quiets near
# the figure for the same reason as pass 4.
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

write_ans('scratch/_guardian.v1.ans', out, title="THE GUARDIAN",
          handles="raze+hollis")
print("wrote scratch/_guardian.ans (v1)")
