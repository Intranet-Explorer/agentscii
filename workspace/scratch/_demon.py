#!/usr/bin/env python3
# _demon.py -- raze solo. random_direction roll: subject "a creature/demon face",
# technique constraint "use canvas.py's flood_fill() to define large background/
# negative-space regions", palette lean "high contrast -- mostly black with bright accents".
#
# SIGNATURE MOVE (the flood_fill one): the piece is built by CARVING. We paint a flat
# silhouette of the demon head/horns/jaw, then flood_fill the void AROUND it from every
# corner -- the fill stops at the subject's boundary, so the negative space is DEFINED BY
# the subject (the classic ACiD "cut the figure out of the dark" move). Then we CARVE the
# EYE SOCKETS and MOUTH as interior voids (flood_fill from inside each), drop glowing irises
# into the sockets, and light every lit surface with per-feature gradient shading from ONE
# upper-left source so cranium / jaw / horns read as separable 3D surfaces, not a flat mass.
#
# PASS structure: (1) silhouette+voids  -> verify by eye; (2) per-surface gradient shade;
# (3) constructed eyes + mouth accents; (4) atmospheric texture in the carved void; (5) frame.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, flood_fill, texture_fill, RAMP
from figure_common import light_field, shade, HUE, c, c_bright, RESET

W, H = 80, 46
cv = Canvas(W, H)
CX = W / 2.0
SEED = 7

# ---- silhouette region functions (the ANATOMY as massing) -------------------
def head_region(x, y):
      # cranium: a wide rounded skull, center of mass high
    cy, ry, rx = 18.0, 12.5, 18.0
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return False
    hw = rx * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

def jaw_region(x, y):
      # lower jaw: a separate mass hanging below the cranium, tapering to a chin
    cy, ry, rx = 32.0, 8.0, 11.5
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return False
    hw = rx * math.sqrt(1.0 - t * t)
    taper = max(0.55, 1.0 - max(0.0, (y - cy)) / ry * 0.45)     # rounded jaw, not a stiletto
    hw *= taper
    return abs(x - CX) <= hw

def horn_region(x, y):
      # two swept-back horns: rise from the upper skull flanks, curve up-and-out to points
    for sgn in (-1, 1):
        bx = CX + sgn * 9.0
        by = 13.0
        tx = CX + sgn * 27.0
        ty = 2.0
        for t in [0.0, 0.12, 0.24, 0.36, 0.48, 0.6, 0.72, 0.84, 0.96]:
            px = bx + (tx - bx) * t
            py = by + (ty - by) * t
            hw = 2.9 * (1.0 - t) + 0.5
            if abs(x - px) <= hw and abs(y - py) <= hw:
                return True
    return False

def silhouette(x, y):
    return head_region(x, y) or jaw_region(x, y) or horn_region(x, y)

# interior voids carved OUT of the face (flood_fill from inside -> stops at subject boundary)
EYE_L = (CX - 7.0, 16.0)
EYE_R = (CX + 7.0, 16.0)
MOUTH = (CX, 31.0)

def in_socket(x, y):
    for (ex, ey) in (EYE_L, EYE_R):
        if math.hypot(x - ex, y - ey) <= 3.4:
            return True
    return False

def in_mouth(x, y):
      # a wide dark maw: an ellipse of cavity below the nose bridge
    dx = (x - MOUTH[0]) / 7.5
    dy = (y - MOUTH[1]) / 3.6
    return (dx * dx + dy * dy) <= 1.0

# ---- PASS 1: flat silhouette, sockets+maw excluded --------------------------
for y in range(H):
    for x in range(W):
        if silhouette(x, y) and not in_socket(x, y) and not in_mouth(x, y):
            cv.set(x, y, "\u2588", 91, 0)

# ---- flood_fill the VOID around the subject (the signature move) ------------
for sx in range(0, W, 4):
    for sy in [0, H - 1]:
        flood_fill(cv, sx, sy, " ", 7, bg=0)

# carve the interior voids: sockets + maw as true black holes (flood from inside)
for (ex, ey) in (EYE_L, EYE_R):
    flood_fill(cv, int(ex), int(ey), " ", 7, bg=0)
flood_fill(cv, int(MOUTH[0]), int(MOUTH[1]), " ", 7, bg=0)

# ---- PASS 2: per-surface gradient shading from ONE upper-left source --------
LX, LY = 26.0, 8.0          # light source: upper-left
LMAX = 34.0
def L(x, y):
    return light_field(x, y, LX, LY, lmax=LMAX, ambient=0.16)

# cranium + jaw lit as red demon skin (warm), with a subtle hue shift by surface
def shade_skin(cv, region_fn, base_fg, hot_fg):
    for y in range(H):
        for x in range(W):
            if not region_fn(x, y):
                continue
            if in_socket(x, y) or in_mouth(x, y):
                continue
            ch, fg = shade(L(x, y), base_fg=base_fg, hot_fg=hot_fg, ramp=RAMP)
            cv.set(x, y, ch, fg, 0)

# cranium: warm red-orange skin
shade_skin(cv, head_region, base_fg=91, hot_fg=15)
# jaw: slightly cooler/darker red so it reads as a separate mass below the brow
shade_skin(cv, jaw_region, base_fg=88, hot_fg=91)

# horns: cool bone-grey, lit from the same source -- they catch light on their upper edge
for y in range(H):
    for x in range(W):
        if horn_region(x, y):
            ch, fg = shade(L(x, y), base_fg=8, hot_fg=15, ramp=RAMP)
            cv.set(x, y, ch, fg, 0)

# ---- PASS 3: constructed eyes (glowing irises in the carved sockets) --------
def glow_eye(ex, ey):
      # socket wall already black; drop a glowing iris + glint into it
    for y in range(int(ey - 2), int(ey + 3)):
        for x in range(int(ex - 2), int(ex + 3)):
            d = math.hypot(x - ex, y - ey)
            if d <= 1.0:
                cv.set(x, y, "\u2588", 96, 0)      # hot core (bright cyan-white)
            elif d <= 1.7:
                cv.set(x, y, "\u2593", 94, 0)      # mid glow
    cv.set(int(ex) - 1, int(ey) - 1, "\u2588", 15, 0)   # catch-light upper-left

for (ex, ey) in (EYE_L, EYE_R):
    glow_eye(ex, ey)

# maw: an open cavity -- inner red glow + a row of bright teeth along the upper lip
def render_maw():
    mx, my = MOUTH
    # inner glow: faint hot-red deep in the cavity
    for y in range(int(my - 2), int(my + 3)):
        for x in range(int(mx - 5), int(mx + 6)):
            dx = (x - mx) / 7.0; dy = (y - my) / 3.0
            if dx*dx + dy*dy <= 1.0:
                cv.set(x, y, "\u2592", 88, 0)     # dim red cavity depth
    # teeth: bright cells along the upper edge of the maw
    for x in range(int(mx - 6), int(mx + 7)):
        dx = (x - mx) / 7.5
        if abs(dx) <= 1.0:
            cv.set(x, int(my - 3), "\u2588", 15, 0)    # upper teeth row
render_maw()

# ---- PASS 4: atmospheric texture in the carved void (non-destructive) -------
def void_region(x, y):
      # everything that's NOT the lit subject and NOT already a bright accent
    cell = cv.get(x, y)
    if not silhouette(x, y):
        return True
    return False

rng = random.Random(SEED)
# sparse cool-grey dust in the outer void so the dark reads as atmosphere, not flat black
for y in range(H):
    for x in range(W):
        cell = cv.get(x, y)
        if cell[0] == " " and cell[1] == 7:     # untouched void cell
            if rng.random() < 0.06:
                idx = rng.randint(2, 3)
                cv.set(x, y, RAMP[idx], 8, 0)    # faint dim-grey speck

# light spills off the glowing eyes into the surrounding carved void (a demon's eyes cast light)
for (ex, ey) in (EYE_L, EYE_R):
    for y in range(int(ey - 6), int(ey + 7)):
        for x in range(int(ex - 6), int(ex + 7)):
            cell = cv.get(x, y)
            if silhouette(x, y):
                continue                      # don't paint over the face itself
            d = math.hypot(x - ex, y - ey)
            if d <= 5.0:
                idx = int((1.0 - d / 5.0) * (len(RAMP) - 1)) % len(RAMP)
                cv.set(x, y, RAMP[idx], 94, 0)   # cool cyan glow bleeding out

# ---- PASS 5: frame / title card --------------------------------------------
def box_row(fg=93):
    return "\x1b[0m" + c(fg, 0) + "\u2554" + "\u2550" * (W - 2) + "\u2557"

def text_row(s, fg=95):
    pad = W - len(s); half = pad // 2
    return "\x1b[0m" + c(fg, 0) + " " * half + s + " " * (pad - half)

out = []
out.append(box_row(93))
out.append(text_row("D E M O N", 95))
out.append(box_row(93))
for row in cv.cells:
    line = ""; prev_fg = None
    for cell in row:
        ch, fg, bg = cell[0], cell[1], cell[2]
        if fg != prev_fg:
            line += c(fg, bg); prev_fg = fg
        line += ch
    out.append(line + "\x1b[0m")
out.append(box_row(93))
out.append(text_row("// a face carved from the dark //", 96))
out.append(text_row("raze / AGENTSCII", 94))
out.append(box_row(93))
out.append(RESET)

with open("scratch/_demon.ans", "w") as f:
    f.write("\n".join(out))
print("wrote scratch/_demon.ans (full pass)")
