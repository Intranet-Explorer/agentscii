#!/usr/bin/env python3
# _coral.py -- AGENTSCII // "CORAL"  (solo raze)  v2
#
# PROVENANCE: random_direction roll ->
#   subject "a flowing/organic pattern", technique constraint
#   "use canvas.py's line()+copy_region()/paste_block() to hand-place repeated motifs",
#   palette lean "warm tones (reds/yellows/magentas) dominant".
#   Took all three straight. The SIGNATURE move is the repeated MOTIF: one small frond
#   shape, built once on a sub-canvas and copy_region'd into a block, then paste_block'd
#   repeatedly along branching growth stems -- you can SEE the same unit echoed across the
#   composition, growing and warming with height. Distinct from FLOWFIELD (continuous
#   curl-noise ribbons) and QUENCH (a single radial conflagration burst): this is DISCRETE
#   repeated units that GROW along curves.
#
# v1 -> v2 (from my OWN preview of v1, by eye -- not asserted):
#   (a) TWO BLOBS: 4 anchors clustered so the growth read as two rounded mushrooms, not a
#       colony. Fix: spread anchors evenly across the full width + interlock them.
#   (b) VOID UP TOP: large empty upper third (the flagged blank run). Fix: taller stems that
#       reach up into the card-adjacent space + upward-drifting embers fill the field.
#   (c) FUSED FRONDS: fronds packed so dense they merged into solid masses, so the repeated
#       MOTIF -- the whole point -- didn't read. Fix: fronds SCALE DOWN with depth and SPACE
#       OUT (fewer per stem), so individual units stay legible as a repeated motif, not a blob.
#   (d) NO TAPER: base and tips equally heavy. Fix: stems taper full->half block up the length;
#       branch fronds are smaller than main-stem fronds.
#
# READ: a warm coral colony rising out of pure black -- several stems swaying up from a seabed,
#   bearing legible frond-motifs that warm from deep red at the base through yellow to white-hot
#   tips, branching into smaller child stems. Warm-only field {red 91 / yellow 93 / magenta 95 /
#   white 107} on black -- lit-out-of-the-dark idiom, but vertical organic growth.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, sgr, RAMP, copy_region, paste_block, write_ans, hygiene_gate

W = 80
H = 40
random.seed(7)    # fixed -> reproducible growth

# ---- warm-only field (the roll's palette lean): red->yellow->magenta->white-hot ---
RED, YEL, MAG, HOT = 91, 93, 95, 107

def warmth(y):
    """Warm hue by height: deep red at the base, yellow mid, white-hot at the tips."""
    t = y / H                       # 0 top .. 1 bottom
    if t > 0.60:                  return RED       # base -- deepest warm
    if t > 0.32:                  return YEL       # mid growth
    return HOT                        # tips -- white-hot

# ===========================================================================
# PASS 1: build the FROND MOTIF once on a sub-canvas, copy_region it into a block.
#   A small leaf/barb pointing up with two side-barbs -- the repeated unit.
# ===========================================================================
SUB_W, SUB_H = 7, 9
sub = Canvas(SUB_W, SUB_H, fill_ch=' ', fill_fg=0)
frond_pts = [
    (3, 8, '\u2588'),    # base attach point (full block)
    (3, 7, '\u2588'),
    (3, 6, '\u2593'),    # stem (half-block body)
    (2, 5, '\u2588'),    # left barb tip
    (3, 5, '\u2593'),
    (4, 4, '\u2588'),    # right barb tip
    (3, 4, '\u2593'),
    (3, 3, '\u2592'),    # upper stem (lighter)
    (2, 2, '\u2591'),    # left fine barb
    (4, 2, '\u2591'),    # right fine barb
    (3, 1, '\u2588'),    # tip -- full block, the growth point
]
for x, y, ch in frond_pts:
    sub.set(x, y, ch, fg=0)       # fg placeholder; recolored per-node on paste

MOTIF = copy_region(sub, 0, 0, SUB_W - 1, SUB_H - 1)    # the one repeated block

def paste_motif(cv, x, y, fg, scale=1):
    """Paste the frond motif at (x,y) top-left, forcing warm fg `fg` on every lit cell.
    Uses copy_region'd MOTIF + paste_block (transparent_ch skips empty cells), then a
    recolor pass so each node carries its own height-based warm hue. scale<1 trims the
    block so branch fronds read as SMALLER than main-stem fronds (the taper)."""
    if scale < 1:
        cw = max(3, int(SUB_W * scale))
        ch_ = max(4, int(SUB_H * scale))
        blk = [row[:cw] for row in MOTIF[:ch_]]
    else:
        blk = MOTIF
    paste_block(cv, blk, x, y, transparent_ch=' ')
    for ry, row in enumerate(blk):
        for rx, cell in enumerate(row):
            if cell[0] != ' ':
                cv.set(x + rx, y + ry, fg=fg)

# ===========================================================================
# PASS 2: recursive GROWTH -- main stems + branching children, bearing fronds.
#   Taller thinner stems, fronds that scale down with depth and space out so the
#   repeated unit stays legible (the v1 fusion bug, fixed).
# ===========================================================================
cv = Canvas(W, H, fill_ch=' ', fill_fg=0, fill_bg=0)

def grow(x, y, ang, depth, length):
    """Grow a stem from (x,y) at angle `ang` (radians, 0=up), bearing fronds and
    spawning child stems at branch points. depth-limited so it terminates."""
    if depth < 0 or length < 2:
        return
    steps = max(3, int(length))
    dx = math.sin(ang)
    dy = -math.cos(ang)             # up is negative y
    sway = random.uniform(0.18, 0.40)    # per-stem sway amplitude (organic curve)

    # branch points: spawn children partway up this stem
    branch_at = []
    if depth >= 1:
        for _ in range(random.randint(1, 2)):
            branch_at.append(int(steps * random.uniform(0.5, 0.85)))

    frond_scale = 1.0 if depth == 3 else (0.7 if depth == 2 else 0.5)   # taper with depth
    frond_every = 3 if depth >= 2 else 4                                # space out (anti-fusion)

    px, py = x, y
    for i in range(steps + 1):
        t = i / steps
        cx = int(x + dx * i + math.sin(t * math.pi * 2 + ang) * sway * length * 0.35)
        cy = int(y + dy * i)
        if not cv.in_bounds(cx, cy):
            continue
        fg = warmth(cy)
        # stem body: full block at the base of the step, half up top -> taper up the length
        cv.set(cx, cy, '\u2588' if t < 0.6 else '\u2593', fg=fg)

        # bear a frond-motif on alternating sides, spaced out (the repeated unit, legible)
        if i >= 1 and i % frond_every == 0:
            side = -1 if ((i // frond_every) % 2 == 0) else 1
            fx = cx + side * 3
            fy = cy - 4
            if cv.in_bounds(fx, fy):
                paste_motif(cv, fx, fy, fg, scale=frond_scale)

        # branch point -> spawn children at +/- angles (smaller fronds via depth-1)
        for b in branch_at:
            if i == b and depth > 0:
                for sign in (-1, 1):
                    child_ang = ang + sign * random.uniform(0.55, 1.0)
                    grow(cx, cy, child_ang, depth - 1, int(length * 0.6))

# main stems rising from anchors spread evenly across the full width (interlocking colony)
anchors = [12, 28, 44, 60, 72]
for ax in anchors:
    base_y = H - 3 + random.randint(-1, 1)
    ang = random.uniform(-0.15, 0.15)       # near-vertical with slight lean
    grow(ax, base_y, ang, depth=3, length=random.randint(12, 16))

# ===========================================================================
# PASS 3: warm seabed baseline + upward-drifting embers (life that fills the void).
# ===========================================================================
for x in range(W):
    if random.random() < 0.5:
        cv.set(x, H - 2, '\u2588', fg=RED)
for _ in range(28):
    ex = random.randint(3, W - 4)
    ey = random.randint(10, H - 3)          # embers drift UP into the upper field
    if cv.get(ex, ey)[0] == ' ':
        cv.set(ex, ey, '\u2588', fg=random.choice([YEL, MAG]))

# deterministic upward ember trail through the title-card gap (rows 8..10): a few warm
# specks drifting up toward the card so the void reads as life rising, not dead space.
for _ty, _xs in ((8, [20, 59]), (9, [34, 46]), (10, [12, 67])):
    for _tx in _xs:
        if cv.get(_tx, _ty)[0] == ' ':
            cv.set(_tx, _ty, '█', fg=random.choice([YEL, MAG, HOT]))

# ===========================================================================
# PASS 4: boxed title card (top) + dimmed closing credit band (THE HORIZON idiom).
#   Manual single in-canvas credit sequence -> no double credits.
# ===========================================================================
RULE = '\u2550'
QUAD = '\u2592'

def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        cv.set(x + i, y, ch, fg, 0)

# title card rows 1..7
x0, x1, y0, y1 = 3, W - 4, 1, 7
for x in range(x0, x1 + 1):
    cv.set(x, y0, RULE, 12, 0); cv.set(x, y1, RULE, 12, 0)
for y in range(y0, y1 + 1):
    cv.set(x0, y, RULE, 12, 0); cv.set(x1, y, RULE, 12, 0)
for x in range(x0 + 1, x1):
    cv.set(x, y0 + 1, QUAD, 8, 0); cv.set(x, y1 - 1, QUAD, 8, 0)
for y in range(y0 + 2, y1 - 1):
    cv.set(x0 + 1, y, QUAD, 8, 0); cv.set(x1 - 1, y, QUAD, 8, 0)
put_centered("CORAL", y0 + 2, 15)
put_centered("// one motif, grown a thousand times //", y0 + 4, 8)

# closing credit band
cy = H - 6
for x in range(W):
    cv.set(x, cy, RULE, 12, 0)
put_centered("CORAL", cy + 2, 11)
put_centered("// a warm growth out of the dark //", cy + 3, 8)
put_centered("raze / AGENTSCII", cy + 4, 14)
for x in range(W):
    cv.set(x, cy + 5, RULE, 12, 0)

# ---- render + write: ONE credit sequence, standalone reset tail ---------------
out = []
cv.render(out)
path = "scratch/_coral.ans"
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print("wrote", path, "-- CORAL v2; rows:", len(out))
