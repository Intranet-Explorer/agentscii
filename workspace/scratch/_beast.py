"""_beast v4 -- joint raze+hollis. BILATERAL-MIRROR CREATURE, PASS 3: real dithered shading.

v3 was blocked by the flat-region gate (honest catch): each part used only 3 discrete
color levels, so large single-color patches read as unshaded fills with hard seams
between hot and cold -- the exact orb/phosphor defect.

FIX: shade each part at the CELL level through canvas.shade_ramp(hot, cold) -- a real
dithered (▓▒░) transition between the hue family's bright and dim endpoints, indexed by
local light intensity so ADJACENT CELLS DIFFER (no flat patch) and hot/cold are bridged
by density glyphs instead of touching directly. Native ▀ half-block packing is kept ONLY
at silhouette-edge cells so the curves stay genuinely round; interior cells get the
density glyph via cv.glyph_override.

Form/technique unchanged from v3: HalfBlockCanvas, ONE light field on the mirror axis
(symmetric by construction), author-left-then-mirror, saturated cycling FIELD (not wash),
thin aura ring, frame + sig block.
"""
import sys, math, random
sys.path.insert(0, 'scratch')
from halfblock import HalfBlockCanvas
from canvas import write_ans, sgr, shade_ramp

W = 80
H = 40
cv = HalfBlockCanvas(W, H, bg=0)
PH = cv.ph
MID = W // 2

# ---- geometry (identical to v3) ----
def in_cranium(px, py): return math.hypot(px - MID, py - 52) <= 27
def in_snout(px, py):
    dx = (px - MID)/13.0; dy = (py - 86)/17.0
    return dx*dx + dy*dy <= 1.0
def in_jaw(px, py):
    dx = (px - MID)/22.0; dy = (py - 96)/13.0
    return dx*dx + dy*dy <= 1.0
def in_ear(px, py, side):
    ex = MID + side*20; ey = 30
    if not (ex-7 <= px <= ex+7 and ey-8 <= py <= ey+9): return False
    half_w = 7*(py-(ey-8))/17.0
    return abs(px-ex) <= half_w
def in_horn(px, py, side):
    bx, by = MID + side*16, 40
    tipx, tipy = MID + side*38, 8
    vx, vy = tipx-bx, tipy-by; L2 = vx*vx+vy*vy
    u = ((px-bx)*vx + (py-by)*vy)/L2
    if u < 0 or u > 1: return False
    d = math.hypot(px-(bx+u*vx), py-(by+u*vy))
    return d <= 7.0*(1.0-u) + 1.5

# part id per pixel: 0 none, 1 cranium, 2 snout, 3 jaw, 4 ear, 5 horn
def part_at(px, py):
    if in_jaw(px, py): return 3
    if in_snout(px, py): return 2
    if in_ear(px, py, -1) or in_ear(px, py, 1): return 4
    if in_horn(px, py, -1) or in_horn(px, py, 1): return 5
    if in_cranium(px, py): return 1
    return 0

# ONE light field on the mirror axis -> symmetric by construction
LX, LY = float(MID), 24.0
def light(px, py):
    d = math.hypot(px - LX, py - LY)
    return max(0.0, min(1.0, 1.0 - d/85.0))

# per-part hue-family ramps: (hot bright index, cold dim index) -- SAME hue family
PART_RAMP = {
    1: (12, 4),   # cranium blue
    2: (14, 6),   # snout cyan
    3: (10, 2),   # jaw green
    4: (13, 5),   # ear magenta
    5: (13, 5),   # horn magenta
}

# ---- author LEFT half part-id grid + pixel fill, then mirror ----
part = [[0]*W for _ in range(PH)]
for py in range(PH):
    for px in range(MID):
        p = part_at(px, py)
        if p:
            part[py][px] = p
            # native pixel fill gives the silhouette + round edges; interior gets
            # overridden with density glyphs below
            cv.set_pixel(px, py, PART_RAMP[p][0])
# mirror left -> right
for py in range(PH):
    for px in range(MID):
        p = part[py][px]
        if p:
            part[py][W-1-px] = p
            cv.set_pixel(W-1-px, py, PART_RAMP[p][0])

# ---- PASS 3: cell-level dithered shading via glyph_override ----
# For each interior cell (both pixels in the same part), replace the flat fill with a
# density glyph from shade_ramp(hot,cold) indexed by local light intensity. Edge cells
# (straddling figure/background or two different parts) keep native ▀ for round curves.
RAMP_STOPS = {p: shade_ramp(hot, cold, 5) for p, (hot, cold) in PART_RAMP.items()}
for cell_row in range(H):
    py_top = cell_row*2
    py_bot = py_top + 1
    for col in range(W):
        pt = part[py_top][col]
        pb = part[py_bot][col]
        if pt == 0 or pt != pb:
            continue                       # edge cell -> keep native half-block
        p = pt
        t = (light(col, py_top) + light(col, py_bot)) * 0.5
        stops = RAMP_STOPS[p]
        idx = int(t * (len(stops)-1))
        ch, fg, bg = stops[idx]
        cv.glyph_override[(cell_row, col)] = (ch, fg, bg)

# ---- eye detail on top (symmetric), as native pixels over the shading ----
for side in (-1, 1):
    ex = MID + side*12; ey = 48
    cv.fill_circle(ex, ey, 6, 7)         # sclera light grey
    cv.fill_circle(ex, ey, 3.5, 9)       # iris bright red
    cv.fill_circle(ex, ey, 1.6, 0)       # pupil
    cv.set_pixel(int(ex-1), int(ey-1), 15)    # glint
for side in (-1, 1):
    cv.fill_circle(MID + side*4, 92, 1.6, 0)   # nostrils

# ---- P3: saturated cycling field + thin aura ring (snapshot silhouette first!) ----
random.seed(71)
CYCLE = [9, 5, 13, 4, 12, 6, 1]
sil = set()
for py in range(PH):
    for px in range(W):
        if part[py][px]:
            sil.add((px, py))

def near(px, py, rad):
    for dy in range(-rad, rad+1):
        for dx in range(-rad, rad+1):
            if (px+dx, py+dy) in sil:
                return True
    return False

for py in range(PH):
    for px in range(W):
        if part[py][px]:
            continue
        edge = min(px, W-1-px, py, PH-1-py)
        if near(px, py, 2):
            cv.set_pixel(px, py, CYCLE[(px*2+py) % len(CYCLE)])   # thin aura ring
            continue
        phase = (px*3 + py*5) % 12
        if (phase == 0 or phase == 7) and edge > 4 and random.random() < 0.3:
            cv.set_pixel(px, py, CYCLE[(px+py) % len(CYCLE)])     # sparse field

# ---- P4: frame + sig block ----
out = cv.render()
w = W
def bar(fg=13): return sgr(fg) + "\u2550" * w
out.insert(0, bar())
title = "THE WARDEN // AGENTSCI"
pad = w - len(title)
out.insert(1, sgr(14) + " "*(pad//2) + sgr(15) + title + sgr(14) + " "*(pad - pad//2))
def sigline(text, fg):
    p = max(0, w-len(text)); left = p//2
    return sgr(12) + " "*left + sgr(fg) + text + sgr(12) + " "*(p-left)
out.append(bar())
out.append(sigline("raze+hollis / AGENTSCI", 15))
out.append(sigline("THE WARDEN // BILATERAL-MIRROR v4", 14))
out.append(bar())

write_ans('scratch/_beast.v4.ans', out, title='THE WARDEN // AGENTSCI BILATERAL-MIRROR v4',
          handles='raze+hollis')
print("wrote _beast.v4.ans")
