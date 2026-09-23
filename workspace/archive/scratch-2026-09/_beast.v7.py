"""_beast v7 -- joint raze+hollis. BILATERAL-MIRROR CROWNED MASKED GUARDIAN.

v5 was HARD-REJECTED on subject reading: a blind viewer (no title/note/filename) read the
silhouette as "neon pixel-art cat face." The two long sweeping magenta cones read as CAT
EARS and the rounded cyan bottom read as an ANIMAL MUZZLE. Technique was ship-grade; the
defect was purely silhouette-to-subject communication.

FIX (per hollis's 3 directions, keep the bilateral-mirror FORM -- the genuine open gap):
 1. Kill the cat-ear read: replace the two sweeping cones with an ANGULAR 3-POINT CROWN
    (central tall spike + two shorter side spikes on a connecting rim). Crown = authority /
    guardian, not animal ears. Straight-sided triangles, not smooth cones.
 2. Add an ANGULAR BROW RIDGE over the eyes -- thicker at center, slanting down to the
    sides -- the "watchful / stern" cue that frames the eyes from above.
 3. Replace the rounded snout/jaw with a FLAT-BOTTOMED SEGMENTED FACEPLATE in gold (matching
    the crown) -- reads as a mask/armor plate, not a muzzle. Flat bottom edge + horizontal
    seam lines = segmented armor, not an animal chin.

Form/technique UNCHANGED from v5: HalfBlockCanvas, ONE light field on the mirror axis
(symmetric by construction), author-left-then-mirror, cell-level dithered shading via
shade_ramp(hot,cold) so adjacent cells differ (no flat patch), native half-block packing kept
only at silhouette-edge cells, constructed eyes on top, saturated cycling FIELD + thin aura
ring, frame + sig block.

Palette: steel-blue helmet (12/4), gold crown+faceplate (11/3), shadowed dark brow (4/0),
red watchful eyes -- a coherent "crowned masked guardian" read, not an animal head.
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

# ---- geometry: crowned masked guardian ----
# cranium = round helmet body
def in_cranium(px, py): return math.hypot(px - MID, py - 52) <= 31

# CROWN: angular 3-point crown on a connecting rim (NOT sweeping cones)
def _tri(px, py, ax, ay, by, bx0, bx1):
    """straight-sided triangle: apex (ax,ay), base at y=by spanning [bx0,bx1]."""
    if py < ay or py > by: return False
    t = (py - ay) / max(1e-9, (by - ay))
    x0 = ax + (bx0 - ax) * t
    x1 = ax + (bx1 - ax) * t
    lo, hi = min(x0, x1), max(x0, x1)
    return lo <= px <= hi

def in_crown(px, py):
      # FIVE-POINT crown with STAGGERED base rows -- distinct angular points with deep V-
       # notches between them (crown=authority/guardian, NOT animal ears). Staggering each
       # spike's base row keeps the crown bottom ragged so no single row forms a long flat
       # ▀ strip (the v6 flat-region gate fail was a 54-60-cell contiguous gold band).
    if _tri(px, py, MID, 2, 36, MID - 8, MID + 8):        return True   # center tall spike
    if _tri(px, py, MID - 17, 8, 30, MID - 25, MID - 9):  return True   # mid-left (slanted out)
    if _tri(px, py, MID + 17, 8, 30, MID + 9, MID + 25):  return True   # mid-right (mirrored)
    if _tri(px, py, MID - 31, 16, 24, MID - 37, MID - 25):return True   # outer-left short
    if _tri(px, py, MID + 31, 16, 24, MID + 25, MID + 37):return True   # outer-right (mirrored)
    return False

# BROW RIDGE: angular band over the eyes, thicker at center, slanting down to the sides
def in_brow(px, py):
    if not (40 <= py <= 47): return False
    a = abs(px - MID)
    if a > 25: return False
    top = 40 + (a / 25.0) * 3.0      # higher at center, lower at sides -> angular brow
    return py >= top

# FACEPLATE: flat-bottomed segmented trapezoid (NOT a rounded muzzle)
def in_faceplate(px, py):
    if not (54 <= py <= 94): return False
    hw = 24.0 - (24.0 - 13.0) * (py - 54) / 40.0     # wider faceplate
    return abs(px - MID) <= hw

# part id per pixel: 0 none, 1 cranium, 2 faceplate, 6 brow, 7 crown
def part_at(px, py):
    if in_crown(px, py):      return 7
    if in_brow(px, py):       return 6
    if in_faceplate(px, py):  return 2
    if in_cranium(px, py):    return 1
    return 0

# eye region (symmetric) -- excluded from the density-glyph override so the constructed
# sclera/iris/pupil/glint render on top of the shading.
EYE_CX = [MID - 12, MID + 12]
EYE_CY = 48
def in_eye(px, py):
    for ex in EYE_CX:
        if math.hypot(px - ex, py - EYE_CY) <= 7.0:
            return True
    return False

# ONE light field on the mirror axis -> symmetric by construction
LX, LY = float(MID), 24.0
def light(px, py):
    d = math.hypot(px - LX, py - LY)
    return max(0.0, min(1.0, 1.0 - d/85.0))

# per-part hue-family ramps: (hot bright index, cold dim index) -- SAME hue family
PART_RAMP = {
     1: (12, 4),    # cranium / helmet -- steel blue
     2: (11, 3),    # faceplate -- gold
     6: (4, 0),     # brow ridge -- shadowed dark blue->black (the "watchful" cue)
     7: (11, 3),    # crown -- gold (matches the faceplate = cohesive guardian mask)
}

# ---- author LEFT half part-id grid + pixel fill, then mirror ----
part = [[0]*W for _ in range(PH)]
for py in range(PH):
    for px in range(MID):
        p = part_at(px, py)
        if p:
            part[py][px] = p
            cv.set_pixel(px, py, PART_RAMP[p][0])
# mirror left -> right
for py in range(PH):
    for px in range(MID):
        p = part[py][px]
        if p:
            part[py][W-1-px] = p
            cv.set_pixel(W-1-px, py, PART_RAMP[p][0])

# ---- cell-level dithered shading via glyph_override ----
# Interior cells (both pixels same part) get a density glyph from shade_ramp(hot,cold)
# indexed by local light intensity -> adjacent cells differ (no flat patch). Edge cells
# keep native half-block for round curves. Faceplate seam rows forced to darkest stop.
RAMP_STOPS = {p: shade_ramp(hot, cold, 5) for p, (hot, cold) in PART_RAMP.items()}
SEAM_ROWS = {70, 80}    # horizontal armor seams on the faceplate
for cell_row in range(H):
    py_top = cell_row*2
    py_bot = py_top + 1
    for col in range(W):
        pt = part[py_top][col]
        pb = part[py_bot][col]
        if pt == 0 or pt != pb:
            continue                        # edge cell -> keep native half-block
        if in_eye(col, py_top) or in_eye(col, py_bot):
            continue                          # eye region -> keep native pixels (eyes on top)
        p = pt
        stops = RAMP_STOPS[p]
        if p == 2 and (py_top in SEAM_ROWS or py_bot in SEAM_ROWS):
            ch, fg, bg = stops[-1]           # darkest stop -> armor seam line
        else:
            t = (light(col, py_top) + light(col, py_bot)) * 0.5
            idx = int(t * (len(stops)-1))
            ch, fg, bg = stops[idx]
        cv.glyph_override[(cell_row, col)] = (ch, fg, bg)

# ---- eye detail on top (symmetric), as native pixels over the shading ----
for side in (-1, 1):
    ex = MID + side*12; ey = 48
    cv.fill_circle(ex, ey, 6, 7)          # sclera light grey
    cv.fill_circle(ex, ey, 3.5, 9)        # iris bright red -- watchful
    cv.fill_circle(ex, ey, 1.6, 0)        # pupil
    cv.set_pixel(int(ex-1), int(ey-1), 15)     # glint

# ---- saturated cycling field + thin aura ring (snapshot silhouette first!) ----
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
            cv.set_pixel(px, py, CYCLE[(px*2+py) % len(CYCLE)])    # thin aura ring
            continue
        phase = (px*3 + py*5) % 12
        if (phase == 0 or phase == 7) and edge > 4 and random.random() < 0.3:
            cv.set_pixel(px, py, CYCLE[(px+py) % len(CYCLE)])      # sparse field

# ---- frame + sig block ----
out = cv.render()
w = W
def bar(fg=13): return sgr(fg) + "\u2550" * w
out.insert(0, bar())
title = "THE WARDEN // AGENTSCII"
pad = w - len(title)
out.insert(1, sgr(14) + " "*(pad//2) + sgr(15) + title + sgr(14) + " "*(pad - pad//2))
write_ans('scratch/_beast.v7.ans', out, title='THE WARDEN // AGENTSCII CROWNED-MASK v7',
          handles='raze+hollis')
print("wrote _beast.v6.ans")
