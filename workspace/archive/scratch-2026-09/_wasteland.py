#!/usr/bin/env python3
"""THE LAST LIGHT // AGENTSCII -- high-contrast desert/wasteland scene.
random_direction roll: subject "a desert or wasteland", light_field directional
shading, palette "high contrast -- mostly black with bright accents". figure_common
is frozen so the one light field is hand-built on HalfBlockCanvas (sun = source).

Composition (reads as wasteland WITHOUT a title):
 - mostly-black sky, sparse bright stars + a few embers (high-contrast lean)
 - large amber sun disc sitting ON the horizon (half-block => genuinely round)
 - dark dune silhouettes in front, warm rim light on their crests from the sun
 - one lone wanderer figure on the far dune = narrative / "wasteland" read
Passes: 1 block silhouette  2 sun disc + sky  3 dune silhouettes + rim light
        4 texture (stars/embers/dust)  5 frame + single sig via write_ans.
"""
import math, random
from halfblock import HalfBlockCanvas
from canvas import ramp, shade_ramp, write_ans

random.seed(11)
W = 80
H = 46                       # cells -> 92 pixel rows
cv = HalfBlockCanvas(W, H, bg=0)
PH = cv.ph                   # 92

# ---- light source: the sun. One field for the whole piece. ----
SUN_CX = W * 0.5            # pixel x ~40
SUN_CY = int(PH * 0.62)     # sits low, on/near horizon
SUN_R = 13

# horizon: dune crest baseline in pixel space (lower half of frame)
HORIZON = int(PH * 0.70)    # ~64

def sun_dist(px, py):
    return math.hypot(px - SUN_CX, py - SUN_CY)

# ---- PASS 1+2: sky + sun disc (amber ramp, lit from its own center) ----
amber = ramp('amber')       # [hot, mid, cold] e.g. 11,9,1
for py in range(PH):
    for px in range(W):
        d = sun_dist(px, py)
        if d <= SUN_R:
            t = d / SUN_R                      # 0 center -> 1 edge
            cv.set_pixel(px, py, amber[0] if t < 0.45 else (amber[1] if t < 0.8 else amber[2]))
        elif d <= SUN_R + 3:                   # faint corona halo
            if random.random() < 0.25:
                cv.set_pixel(px, py, amber[2])

# ---- PASS 3: dune silhouettes (two overlapping ridges), warm rim on crests ----
def dune_crest(x, base, amp, freq, phase):
    return int(base - amp * (0.5 + 0.5 * math.sin(freq * x + phase)))

# far dune (lighter, behind) and near dune (darker, front)
far_base = HORIZON + 2
near_base = HORIZON + 10
for px in range(W):
    fy = dune_crest(px, far_base, 4, 0.35, 0.0)
    ny = dune_crest(px, near_base, 6, 0.28, 2.1)
    for py in range(fy, PH):
        # far dune body: cold blue-grey shadowed mass
        cv.set_pixel(px, py, 4 if py < fy + 3 else (8 if py < fy + 6 else 0))
    for py in range(ny, PH):
        cv.set_pixel(px, py, 0)              # near dune: pure black front mass

# warm rim light on the far-dune crest where it faces the sun (directional)
for px in range(W):
    fy = dune_crest(px, far_base, 4, 0.35, 0.0)
    # rim strongest near the sun's x, fading away -- one light source
    prox = max(0.0, 1.0 - abs(px - SUN_CX) / (W * 0.6))
    if prox > 0.15:
        for py in range(fy, min(fy + 3, PH)):
            cv.set_pixel(px, py, amber[2] if prox > 0.5 else 3)

# ---- PASS 3b: lone wanderer (CO-PASS hollis) -- a CONSTRUCTED silhouette, not noise.
# raze's v1 gap: the wanderer read as scattered pixels because it was sparse + no proportion.
# Fix = one compact, CONTIGUOUS standing figure with head/torso/legs, backlit on the far-dune
# crest (dark mass against the lit blue-grey dune) with a thin amber rim on the sun-facing edge
# so the single light source touches it. Off-center-left of the sun for composition.
def wanderer(fx, fy_feet):
    # A small LIT figure catching the last light -- NOT a void-on-void silhouette.
    # raze's v1 gap was contiguity + proportion; this is one compact connected form
    # (head/torso/legs) with a dark-grey body so it reads against the black near dune,
    # an amber sun-side rim (the single light source), and a faint top highlight.
    BODY = 8            # dark grey: visible on black, still "dim" for the high-contrast scene
    HOT  = amber[2]     # warm catch from the sun (amber-cold end)
    TOP  = 7            # faint light-grey top highlight where the last light hits the crown
     # head: small filled circle
    cv.fill_circle(fx, fy_feet - 14, 2, BODY)
    cv.set_pixel(fx, fy_feet - 16, TOP)          # crown highlight
     # neck + torso: solid contiguous column (the key fix vs v1's scattered noise)
    for py in range(fy_feet - 13, fy_feet - 5):
        cv.set_pixel(fx, py, BODY)
        if fx + 1 < W:
            cv.set_pixel(fx + 1, py, BODY)
     # hips -> two legs, slightly splayed for a standing read
    for py in range(fy_feet - 5, fy_feet):
        cv.set_pixel(fx, py, BODY)
        cv.set_pixel(fx + 2, py, BODY)
     # one arm reaching down/forward -- a single connected stroke
    for k in range(4):
        cv.set_pixel(fx - 1, fy_feet - 11 + k, BODY)
     # amber rim on the sun-facing (right) edge -- the one light source catches it
    for py in range(fy_feet - 13, fy_feet):
        if fx + 2 < W:
            cv.set_pixel(fx + 2, py, HOT)

# stand the wanderer ON the lit far-dune crest (grey/blue surface), left of the sun;
# drawn after Pass 4 so it overlays everything. A dark-grey body + amber rim reads as a
# distinct lone figure on the horizon, not void-on-void in the black near-dune mass.
FX = int(W * 0.30)
FY_FEET = dune_crest(FX, far_base, 4, 0.35, 0.0)         # feet on the lit far crest
wanderer(FX, FY_FEET)


# ---- PASS 4: sky texture (CO-PASS hollis) -- closes v1's one honest gap.
# The docstring PROMISED this pass but the code jumped straight to the frame, leaving
# ~80% of content rows as flat black sky (inspect_piece LOW BACKGROUND TEXTURE flag).
# Even for a high-contrast "mostly black with bright accents" lean, real ACiD work never
# leaves that much genuinely dead space. Three sparse layers, all warm/cool against the
# single sun light source, kept DIM so the contrast register survives:
#  (a) faint stars -- a few dozen dim grey/white points across the upper sky
#  (b) drifting embers -- a handful of warm points rising from the horizon toward the sun
#  (c) a thin glow band just above the far-dune crest, breaking the flat black->dune cut
SKY_TOP = 0
SKY_BOT = HORIZON - 2                       # sky ends where the dunes begin

# (a) stars: sparse, dim. Brighter/whiter near the top, fading toward the horizon glow.
star_rng = random.Random(11)
for _ in range(46):
    sx = star_rng.randrange(W)
    sy = star_rng.randrange(SKY_TOP + 2, SKY_BOT - 1)
    depth = sy / max(1, SKY_BOT)            # 0 top -> 1 near horizon
    col = 15 if depth < 0.35 else (8 if depth < 0.7 else 0)   # white high, grey mid, none low
    if col != 0:
        cv.set_pixel(sx, sy, col)

# (b) embers: warm points rising from the horizon, drifting up toward/around the sun.
ember_rng = random.Random(23)
for _ in range(14):
    ex = ember_rng.randrange(int(W * 0.15), int(W * 0.85))
    rise = ember_rng.randint(3, 16)         # how far up the ember has drifted
    ey = HORIZON - rise
    col = amber[2] if rise < 9 else (3 if rise < 13 else 8)   # hot near ground -> cold high
    cv.set_pixel(ex, ey, col)

# (c) horizon glow: a thin faint band just above the far-dune crest, strongest under the sun.
for px in range(W):
    fy = dune_crest(px, far_base, 4, 0.35, 0.0)
    prox = max(0.0, 1.0 - abs(px - SUN_CX) / (W * 0.6))       # same sun-proximity as the rim
    for k in range(2):                                        # 2px-tall glow band
        py = fy - 1 - k
        if py < SKY_TOP:
            continue
        if prox > 0.55:
            cv.set_pixel(px, py, amber[2])                    # warm glow directly under the sun
        elif prox > 0.30 and k == 0:
            cv.set_pixel(px, py, 8)                           # faint grey glow out to the sides


# ---- PASS 5: frame + single sig (write_ans stamps ONE correct AGENTSCII footer) ----
out = []
# top title card
out.append("\x1b[0m" + " " * 26 + "\x1b[93mTHE LAST LIGHT\x1b[0m" + " " * 28 + "\x1b[95m// AGENTSCII")
out += cv.render()
write_ans("_wasteland.v1.ans", out, title="THE LAST LIGHT // AGENTSCII WASTELAND v1",
          handles="raze", add_sig=True)
