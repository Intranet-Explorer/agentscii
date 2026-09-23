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

# (lone-wanderer pass dropped v1: read as scattered noise at this scale, not a figure)

# ---- PASS 4: texture -- sparse stars + embers in the mostly-black sky ----
for _ in range(38):
    px = random.randint(0, W - 1)
    py = random.randint(0, HORIZON - 6)            # above horizon only
    if sun_dist(px, py) < SUN_R + 5:
        continue
    col = random.choice([7, 8, 11, 14])           # bright accents on black
    cv.set_pixel(px, py, col)

# a few drifting embers near the horizon glow
for _ in range(14):
    px = int(SUN_CX + random.uniform(-W * 0.4, W * 0.4))
    py = int(HORIZON - random.randint(2, 16))
    if sun_dist(px, py) < SUN_R:
        continue
    cv.set_pixel(px, py, random.choice([9, 3]))

# ---- PASS 5: frame + single sig (write_ans stamps ONE correct AGENTSCII footer) ----
out = []
# top title card
out.append("\x1b[0m" + " " * 26 + "\x1b[93mTHE LAST LIGHT\x1b[0m" + " " * 28 + "\x1b[95m// AGENTSCII")
out += cv.render()
write_ans("_wasteland.v1.ans", out, title="THE LAST LIGHT // AGENTSCII WASTELAND v1",
          handles="raze", add_sig=True)
