"""_guardian v8 -- THIRD revision round. Joint raze+hollis.

The head was accepted as genuinely good (teal cranium rim, amber embers in mask
slits, directional upper-left shade). The failure across the prior two REJECTs was
localized to the LOWER BODY / cloak. This pass rebuilds the cloak so it reads as a
SOLID draped mass, not thin radiating streaks:

 A. Solid drape first: the cape is a filled flare from shoulders to frame edge,
    shaded from the SAME upper-left light source as the head (lit left -> grey,
    shadow right -> floored at BLUE so it never dissolves into the grain).
 B. Coherent vertical fold bands on top of that solid mass -- a continuous function
    of x with gentle vertical drift, subtle amplitude growing toward the hem. This
    gives cloth undulation on BOTH sides (the v7 flat-blue cone had folds only where
    light happened to lift them; per-column random phase made stripes, not cloth).
 C. Closed silhouette + a ~2px quiet ring of true black around the whole figure so
    its outline separates crisply from the background grain on both edges
    (hollis point #2: "the figure still bleeds into the grain").

Head passes 1-5 + prior revision rounds (raze) and hollis cape 3b / sig-block fix /
eye co-pass 3c are unchanged. Muted/dim throughout by design (random_direction roll).
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
DGREY      = 8          # dark grey body base / fold valley on the lit side
MGREY      = 7          # light grey highlight / fold ridge
BLUE       = 4          # cold blue shadow -- the cloak's darkest solid floor
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
     # neck tapers slightly wider toward the shoulders -- smooth transition
    t = (py - NECK_Y) / max(1.0, SHOULDER_TOP + 3 - NECK_Y)
    half = 6.5 + t * 4.0
    return abs(px - CX) <= half

def in_cloak(px, py):
     # Cape: symmetric flare centered on CX (the same axis as the cranium), widening
     # smoothly from the shoulders down to a wide hem at the frame edge. A narrower
     # flare (t*t*18, not 30) so it reads as draped cloth, not a full-width cone.
    if not (SHOULDER_TOP <= py < cv.ph):
        return False
    t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
    half = 16 + t * t * 18           # symmetric about CX -> centered under cranium
    return abs(px - CX) <= half

in_shoulder = in_cloak

def in_silhouette(px, py):
    return in_cranium(px, py) or in_neck(px, py) or in_shoulder(px, py)

# ---- directional shade ramps (one light source, density ramp) ----
def head_shade(px, py):
    L = light(px, py)
    if L > 0.66:
        return MGREY              # lit highlight (light grey)
    if L > 0.42:
        return DGREY             # mid tone -- one continuous form, no seam
    if L > 0.22:
        return BLUE              # cold shadow
    return BLACK

# ============================================================
# PASS 1 + 2 -- silhouette block-in then directional shade
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if in_cranium(px, py) or in_neck(px, py):
            cv.set_pixel(px, py, head_shade(px, py))

# faint teal rim light on the upper-LEFT edge of the cranium (contiguous arc)
for py in range(cv.ph):
    for px in range(W):
        d = math.hypot(px - CX, py - CRAN_CY)
        if CRAN_R - 2.5 <= d <= CRAN_R + 0.5:
            ang = math.atan2(py - CRAN_CY, px - CX)
            if -math.pi <= ang <= -math.pi/4:       # upper-left arc
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
    half_w = 3.5 - abs(dy) * 0.7       # ~3.5 at center, tapering to a point
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

# ember glow inside the slits -- soft core fading to amber (not a hard square).
# The core respects the slit's taper + skew so it never spills past the slit edge.
for py in range(cv.ph):
    for px in range(W):
        for side in (-1, 1):
            if in_eye(px, py, side):
                ex = CX + side * EYE_DX
                skew = int((py - EYE_Y) * 0.7)
                dy = py - EYE_Y
                dcore = math.hypot(px - (ex + skew), dy)
                cv.set_pixel(px, py, EMBER_H if dcore < 0.8 and abs(dy) <= 1 else EMBER)

# ============================================================
# PASS 3c -- hollis co-pass on the eyes: under-eye socket shadow + catchlight glint
# so each ember reads as an eye SET INTO a mask, not a flat glowing dot.
# ============================================================
for side in (-1, 1):
    ex = CX + side * EYE_DX
    for py in range(EYE_Y + 2, EYE_Y + 4):
        for px in range(int(ex - 4), int(ex + 5)):
            if in_cranium(px, py) and cv.get_pixel(px, py) != BLACK:
                cv.set_pixel(px, py, BLUE)

# ============================================================
# PASS 3b -- cloak/cape: SOLID drape mass + coherent vertical folds + closed rim.
# The one weak spot across the prior two REJECTs. Built so it reads as draped cloth:
#   - solid flare from shoulders to frame edge (filled, not radiating streaks)
#   - directional shade from the SAME upper-left light; shadow side floored at BLUE
#     so the silhouette stays closed and separates from the grain (never black holes)
#   - coherent vertical fold bands (continuous in x, gentle drift) on BOTH sides
#   - a 1px blue rim on the shadow (right) edge for crisp separation
# ============================================================
rng3 = random.Random(11)
_phase = [rng3.uniform(-0.6, 0.6) for _ in range(W)]       # per-column drape jitter

for py in range(cv.ph):
    for px in range(W):
        if not in_shoulder(px, py):
            continue
        L = light(px, py)
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        rel = (px - CX) / max(1.0, 16 + t * t * 18)         # -1..1 across the cape
         # coherent vertical folds: a continuous function of x with gentle vertical
         # drift, so the bands read as cloth drape, not per-column random stripes.
        fold = math.sin(px * 0.55 + py * 0.12 + _phase[px] * 0.3)      # -1..1, ridge at +1
        amp = 0.06 + t * 0.14                                # subtle near shoulders, gentle at hem
        Lf = L + fold * amp
        lit = L > 0.42
        near_edge = abs(rel) > 0.82
         # the very top of the cape (just under the shoulders/neck) stays a clean solid
         # mass -- folds emerge only below it, so the shoulder line reads as intentional
         # drape, not frayed strands where the quiet ring exposes ragged fold ridges.
        flat_top = t < 0.22
        if lit:
               # lit side: full value range -- ridge -> light grey, valley -> cold blue
            if Lf > 0.66 or flat_top:
                col = MGREY
            elif Lf > 0.50:
                col = DGREY
            elif Lf > 0.34:
                col = BLUE
            else:
                col = DGREY           # deep fold valley, dark grey -- never black (no tent-poles)
        else:
               # shadow side: floored at blue so the silhouette stays closed & separates from
               # the grain. Fold ridges show as a subtle grey ONLY in the cape's interior below
               # the shoulders; near the boundary or at the top the cloth stays solid blue.
            if Lf > 0.34 and not near_edge and not flat_top:
                col = DGREY
            elif fold > 0.25 and not near_edge and not flat_top:
                col = BLUE
            else:
                col = 4             # deep blue valley floor / solid edge -- the cloak's darkest
        cv.set_pixel(px, py, col)

# closed silhouette rim: a 1px dark-blue outline on the shadow (RIGHT) edge so the
# figure separates cleanly from the background grain on its dark side. Light is
# upper-left, so the right flank is the shadow side that bleeds into the grain.
for py in range(SHOULDER_TOP, cv.ph):
    for px in range(W):
        if not in_shoulder(px, py):
            continue
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 18
        on_edge = abs(abs(px - CX) - half) <= 1.0
        if on_edge and px > CX:
            cv.set_pixel(px, py, BLUE)

# faint teal rim on the LIT (left) shoulder edge -- contiguous with the cape body so
# it never leaves a disconnected patch (fixes stray fragment #5).
for py in range(SHOULDER_TOP, NECK_Y + 3):
    for px in range(W):
        t = (py - SHOULDER_TOP) / max(1, cv.ph - SHOULDER_TOP)
        half = 16 + t * t * 18
        if abs((px - CX)) >= half - 2 and abs((px - CX)) <= half:
            if px < CX and light(px, py) > 0.35:
                 # contiguity: a non-black cape pixel must sit immediately inward,
                 # so the rim can never float off the body edge (fixes stray teal).
                if in_shoulder(px + 1, py) and cv.get_pixel(px + 1, py) != BLACK:
                    cv.set_pixel(px, py, TEAL)

# ============================================================
# QUIET RING -- clear a ~2px halo of true black around the WHOLE silhouette so the
# figure's outline separates crisply from the background grain on BOTH edges (the
# shadow side especially). Atmosphere/grain below only paint OUTSIDE this ring.
# ============================================================
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        near = any(in_silhouette(px + dx, py + dy)
                   for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2))
        if near:
            cv.set_pixel(px, py, BLACK)

# ============================================================
# PASS 4 -- structured atmosphere: vertical light-ray field with a falloff that
# QUIETS near the subject so the figure's outline stays crisp (fixes #1). No
# uniform static; depth instead. Skips the quiet ring so it never repaints the edge.
# ============================================================
rng = random.Random(7)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        _near = any(in_silhouette(px + dx, py + dy)
                    for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2))
        if _near:
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
# texture, not empty black. Low density, dim colors only (muted). Quiets near the
# figure for the same reason as pass 4, and skips the quiet ring.
rng2 = random.Random(19)
for py in range(cv.ph):
    for px in range(W):
        if in_silhouette(px, py):
            continue
        _near = any(in_silhouette(px + dx, py + dy)
                    for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2))
        if _near:
            continue
        daxis = abs(px - CX)
        quiet = 1.0 if daxis < 14 else (0.6 if daxis < 26 else 1.0)
        r = rng2.random()
        if r < 0.035 * quiet:
            cv.set_pixel(px, py, DGREY)
        elif r < 0.05 * quiet:
            cv.set_pixel(px, py, BLUE)

out = cv.render()
# top frame bar only -- the bottom is terminated by sig_block's own magenta rule, so
# no manual bottom bar (that collided with sig_block's leading blank row + its rule).
out.insert(0, sgr(8) + "\u2550" * W)

write_ans('scratch/_guardian.v8.ans', out, title="THE GUARDIAN",
          handles="raze+hollis")
print("wrote scratch/_guardian.v8.ans")
