#!/usr/bin/env python3
# _cyclops.py -- AGENTSCII // "CYCLOPS"   (solo raze)  v2
#
# PROVENANCE: random_direction roll ->
#   subject "an eye embedded in something inhuman", technique constraint
#     "use canvas.py's line()+copy_region()/paste_block() to hand-place repeated motifs",
#   palette lean "full saturated 16-color cycling".
#   Took all three straight. The SIGNATURE move is the repeated MOTIF: one small scale/plate
#   unit, built once on a sub-canvas and copy_region'd into a block, then paste_block'd in a
#   sparse ring around the eye -- you can SEE the same unit echoed all the way around the socket,
#   each instance cycling to the next hue on the house wheel so the halo reads as one living,
#   color-cycling carapace. Distinct from CORAL (growth along stems) and FLOWFIELD (continuous
#   ribbons): this is a DISCRETE repeated unit radiating outward from a single center.
#
# v1 -> v2 (from my OWN preview of v1, by eye -- not asserted):
#   (a) FUSED MASS: 68 scales in two dense rings fused into one solid blob so the repeated MOTIF
#       didn't read. Fix: ONE sparse ring, ~22 units spaced far enough that each reads as a
#       distinct plate, not a fused mass (the CORAL v2 lesson).
#   (b) BURIED EYE: an oversized flat gray mask + scales drawn over it buried the eye. Fix:
#       compact cyclopean mask, ONE large legible eye as the clear focal point, mask kept small
#       and dark so it recedes behind the bright eye.
#   (c) CLOBBERED TITLE CARD: scales were drawn AFTER the card, overwriting its text. Fix: draw
#       order is now void -> carapace ring -> mask -> eye -> title card LAST, so nothing clobbers it.
#
# READ: a single large constructed eye (socket well -> sclera -> colored iris -> pupil -> glint,
#   the figure_common.eye idiom at scale) set into a compact dark cyclopean mask -- brow ridge
#   above, jaw below, cheek ridges flanking -- lit from upper-left so the surfaces read as 3D
#   anatomy not flat blocks. A sparse ring of repeated scale-motifs cycles the full saturated
#   wheel (magenta/red/yellow/green/cyan/blue/white/amber) like a living carapace halo around it,
#   growing out of pure black. High-contrast lit-out-of-the-dark idiom, figurative not procedural.

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, sgr, RAMP, copy_region, write_ans, hygiene_gate

W = 80
H = 46

# house hue wheel (full saturated cycling lean): bright magenta/red/yellow/green/cyan/blue/white/amber
WHEEL = [95, 91, 93, 92, 96, 94, 107, 103]

def hue(i):
    return WHEEL[i % len(WHEEL)]

cv = Canvas(w=W, h=H, fill_ch=' ', fill_fg=0, fill_bg=0)

# light source: upper-left, diffuse -- makes every surface read as lit 3D form
LX, LY = W * 0.34, H * 0.32

def L(x, y, lmax=30.0, amb=0.16):
    d = math.hypot(x - LX, y - LY) / lmax
    return max(amb, min(1.0, 1.0 - d))

def shade(L, base_fg, hot_fg=15, ramp=RAMP):
    L = max(0.0, min(1.0, L))
    idx = int(L * (len(ramp) - 1) + 0.5) % len(ramp)
    fg = hot_fg if L > 0.82 else base_fg
    return ramp[idx], fg

# ---------------------------------------------------------------------------
# DRAW ORDER: void -> carapace ring -> mask -> eye -> title card (last).
# The mask is COMPACT so the eye reads as the clear focal point; the ring is
# SPARSE so each scale-motif stays a legible distinct unit.
# ---------------------------------------------------------------------------
CX, CY = W // 2, H // 2

# ---- THE CARAPACE: one small scale/plate motif, built once, copy_region'd,
#      then paste_block'd in a sparse ring around the eye (the signature move).
def build_scale_unit():
    # a small 5x4 chevron-plate: full->half block taper with a hot top ridge
    u = Canvas(w=5, h=4, fill_ch=' ', fill_fg=0, fill_bg=0)
    for y in range(3):
        hw = 2 - y
        for x in range(2 - hw, 2 + hw + 1):
            u.set(x, y, RAMP[y], 0, 0)       # fg recolored per-instance below
    for x in range(1, 4):                    # hot lit ridge along the top edge
        u.set(x, 0, "\u2588", 0, 0)
    return u

unit = build_scale_unit()
ublock = copy_region(unit, 0, 0, 4, 3)      # 5x4 block of [ch,fg,bg] cells

def paste_recolored(block, dst_x, dst_y, fg):
    # paste_block the unit but recolor every non-space cell to `fg` (the cycling hue)
    for dy in range(len(block)):
        row = block[dy]
        if not row:
            continue
        for dx in range(len(row)):
            ch, _f, bg = row[dx]
            if ch == ' ':
                continue
            cv.set(dst_x + dx, dst_y + dy, ch, fg, 0)

# one sparse ring of distinct scale-motifs -- each cycles the wheel.
ring_r = 15.0
n_scales = 22
for k in range(n_scales):
    ang = (k / n_scales) * 2 * math.pi - math.pi / 2
    sx = int(CX + ring_r * math.cos(ang))
    sy = int(CY + ring_r * 1.08 * math.sin(ang))   # slightly taller ellipse to follow the mask
    paste_recolored(ublock, sx - 2, sy - 2, hue(k))

# ---- THE MASK: a compact dark cyclopean face behind the eye. Each feature is its
#      own shaded region from the SAME light -> individually lit anatomy, not flat.
def shade_region(region_fn, Lfn, base_fg, hot_fg=15):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = shade(Lfn(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

# skull: a compact tall ellipse, dark bone (gray base -> white on the lit side)
def skull(x, y):
    t = (y - CY) / 12.0
    if abs(t) > 1.0:
        return False
    hw = 15 * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

shade_region(skull, lambda x, y: L(x, y), base_fg=8, hot_fg=15)

# brow ridge: a thick shaded bar across the upper third
def brow(x, y):
    if not (CY - 7 <= y <= CY - 3):
        return False
    t = (y - (CY - 5)) / 2.0
    hw = 13 * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw

shade_region(brow, lambda x, y: L(x, y, lmax=18.0), base_fg=9, hot_fg=15)

# jaw: a shaded wedge below the eye
def jaw(x, y):
    if not (CY + 5 <= y <= CY + 10):
        return False
    t = (y - (CY + 7)) / 3.0
    hw = 10 * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw

shade_region(jaw, lambda x, y: L(x, y, lmax=22.0), base_fg=8, hot_fg=15)

# cheek ridges flanking the eye socket
def cheek(x, y):
    if not (CY - 3 <= y <= CY + 4):
        return False
    for sgn in (-1, 1):
        lo = CX - 13 if sgn < 0 else CX + 8
        hi = CX - 8  if sgn < 0 else CX + 13
        if not (lo <= x <= hi):
            continue
        t = (y - CY) / 4.0
        hw = 3 * math.sqrt(max(0.0, 1.0 - t * t))
        return abs((x - CX) - sgn * 10) <= hw
    return False

shade_region(cheek, lambda x, y: L(x, y, lmax=16.0), base_fg=9, hot_fg=15)

# ---- THE EYE: one large constructed eye at center -- the clear focal point.
EX, EY = CX, CY - 1
ER = 6.0

# socket: a dark shadowed well recessing into the mask
for y in range(int(EY - ER - 2), int(EY + ER + 3)):
    for x in range(int(EX - ER - 2), int(EX + ER + 3)):
        d = math.hypot(x - EX, y - EY)
        if ER < d <= ER + 1.4:
            cv.set(x, y, "\u2591", 8, 0)          # shadowed socket wall (dim)
        elif ER + 1.4 < d <= ER + 2.2:
            cv.set(x, y, "\u2591", 0, 0)          # deep socket void

# eyeball: bright sclera with a faint top-lit gradient
rr = int(round(ER))
for y in range(int(EY) - rr, int(EY) + rr + 1):
    for x in range(int(EX) - rr, int(EX) + rr + 1):
        d = math.hypot(x - EX, y - EY)
        if d <= ER:
            top_l = (EY + ER - y) / (2 * ER)
            cv.set(x, y, "\u2588", 15 if top_l > 0.5 else 7, 0)

# iris: a colored core -- bright green (92), the inhuman eye color
for y in range(int(EY - ER * 0.62), int(EY + ER * 0.62 + 1)):
    for x in range(int(EX - ER * 0.62), int(EX + ER * 0.62 + 1)):
        d = math.hypot(x - EX, y - EY)
        if d <= ER * 0.62:
            cv.set(x, y, "\u2588", 92, 0)

# pupil: a dark center
for y in range(int(EY - ER * 0.3), int(EY + ER * 0.3 + 1)):
    for x in range(int(EX - ER * 0.3), int(EX + ER * 0.3 + 1)):
        d = math.hypot(x - EX, y - EY)
        if d <= ER * 0.3:
            cv.set(x, y, "\u2588", 0, 0)

# glint: a single white catch-light, upper-left (light side) -- the eye is ALIVE
cv.set(int(EX - ER * 0.35), int(EY - ER * 0.35), "\u2588", 15, 0)
cv.set(int(EX - ER * 0.35) + 1, int(EY - ER * 0.35), "\u2588", 15, 0)

# ---------------------------------------------------------------------------
# TITLE CARD (boxed, house style) -- top and bottom, drawn LAST so nothing clobbers it.
# ---------------------------------------------------------------------------
RULE = "\u2550"
QUAD = "\u2561"

def put_centered(text, y, fg):
    for x in range(W):
        cv.set(x, y, ' ', 0, 0)
    pad = W - len(text)
    left = pad // 2
    for i, ch in enumerate(text):
        cv.set(left + i, y, ch, fg, 0)

x0, x1, y0, y1 = 3, W - 4, 1, 7
for x in range(x0, x1 + 1):
    cv.set(x, y0, RULE, 12, 0); cv.set(x, y1, RULE, 12, 0)
for y in range(y0, y1 + 1):
    cv.set(x0, y, RULE, 12, 0); cv.set(x1, y, RULE, 12, 0)
for x in range(x0 + 1, x1):
    cv.set(x, y0 + 1, QUAD, 8, 0); cv.set(x, y1 - 1, QUAD, 8, 0)
for y in range(y0 + 2, y1 - 1):
    cv.set(x0 + 1, y, QUAD, 8, 0); cv.set(x1 - 1, y, QUAD, 8, 0)
put_centered("CYCLOPS", y0 + 2, 15)
put_centered("// one eye, a thousand scales //", y0 + 4, 92)

cy = H - 6
for x in range(W):
    cv.set(x, cy, RULE, 12, 0)
put_centered("CYCLOPS", cy + 2, 11)
put_centered("// an eye embedded in something inhuman //", cy + 3, 8)
put_centered("raze / AGENTSCII", cy + 4, 14)
for x in range(W):
    cv.set(x, cy + 5, RULE, 12, 0)

# ---- render + write: ONE credit sequence, standalone reset tail ---------------
out = []
cv.render(out)
path = "scratch/_cyclops.ans"
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print("wrote", path, "-- CYCLOPS v2; rows:", len(out))
