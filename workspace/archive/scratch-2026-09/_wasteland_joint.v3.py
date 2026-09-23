#!/usr/bin/env python3
# _wasteland_joint v3 -- JOINT raze & hollis.  pack41 candidate.
#
# PROVENANCE: builds on v2 (the honestly-reframed lit-column piece). v2 fixed the legibility
#   blocker (gap() separation pass -> head/torso/leg read as SEPARATE masses out of black, not a
#   fused bar) and reframed the title honestly. The one remaining gap flagged by inspect_piece was
#   LOW BACKGROUND TEXTURE: ~67% of content rows read as flat black -- the sky above the horizon is
#   genuinely empty. Real ACiD reference work (SOMMS-the_powergrid, studied this shift) textures even
#   its dark areas; a lit column "dissolving in the last light" should have that last light IN THE
#   AIR around it, not a void. This pass adds exactly that: a sparse atmospheric scatter over the
#   blank sky region -- faint dim dust/stars that thin toward the horizon and catch a touch of warm
#   near the sun (lower-right), so the negative space reads as atmosphere, not a missing fill.
#
# ASSEMBLY (joint, non-destructive): raze's v5 figure base runs INTACT first; hollis's v2 dune+frame
#   pass is reproduced intact on the same live canvas; then THIS atmospheric pass layers over whatever
#   is still blank; then the scene re-renders fresh with the honest title card. Nothing upstream is
#   touched -- each layer only paints cells that are still empty, so raze's figure/dunes/frame stay put.
import sys, math, random; sys.path.insert(0, "scratch")
from figure_common import (new_canvas, set_cell, render, light_field, capsule,
                           joint_dot, eye, c, sgr, RESET, W, RAMP, hygiene_gate)

# --- run raze's v5 figure base INTACT: it builds cv + the lit column + sun + horizon + shadow + debris --
import importlib.util
_spec = importlib.util.spec_from_file_location("wv5", "scratch/_wasteland.v5.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

cv    = base.cv            # raze's live canvas: figure + sun + horizon + shadow + debris, painted
L     = base.L             # raze's directional light field -- single source of truth
H     = base.H
GROUND_Y = 35

# ===========================================================================
# HOLLIS PASS (from v2) -- "THE DUNES": dim shaded silhouettes receding behind the lit column,
#   built with shade_region() + raze's SAME L() sun field. Reproduced intact so v3 stands alone.
# ===========================================================================
DUNE_FG = 8

def dune_crest(x, base_y, amp, period, phase):
    t = (x - phase) / period
    return base_y + amp * math.sin(2.0 * math.pi * t) + 0.5 * amp * math.sin(2.0 * math.pi * t * 2.3 + 1.1)

RIDGES = [
     (GROUND_Y - 1, 0.8, 26.0, 4.0, 1),
     (GROUND_Y - 2, 1.3, 34.0, 12.0, 1),
     (GROUND_Y - 3, 1.8, 44.0, 20.0, 2),
]

def is_blank(x, y):
    cell = cv[y][x]
    return cell[0] == ' ' and cell[1] == 0

from figure_common import shade_region
for (base_y, amp, period, phase, depth) in RIDGES:
    def region(x, y, _by=base_y, _a=amp, _p=period, _ph=phase, _d=depth):
        if not is_blank(x, y):
            return False
        crest = dune_crest(x, _by, _a, _p, _ph)
        return crest <= y < crest + _d
    shade_region(cv, region, L, base_fg=DUNE_FG, hot_fg=DUNE_FG)

# ===========================================================================
# HOLLIS PASS (from v2) -- "THE FRAME": dim box-drawing border band, deep-blue verticals receding
#   to near-black, warm accent in the two lower corners. Outer 1-cell band only.
# ===========================================================================
DIM    = 4
ACCENT = 93
VERT   = "\u2551"
BOTM   = "\u2550"
BOT_L  = "\u2558"
BOT_R  = "\u2557"

def frame_cell(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        set_cell(cv, x, y, ch, fg, 0)

for y in range(H):
    frame_cell(0, y, VERT, DIM)
    frame_cell(W - 1, y, VERT, DIM)
for x in range(1, W - 1):
    frame_cell(x, H - 1, BOTM, DIM)
frame_cell(0, H - 1, BOT_L, ACCENT)
frame_cell(W - 1, H - 1, BOT_R, ACCENT)

# ===========================================================================
# HOLLIS PASS (v3, NEW) -- "THE LAST LIGHT IN THE AIR": sparse atmospheric scatter over the blank
#   sky region above the horizon. The single flat-black gap inspect_piece flagged. Density is faint
#   high up and thins toward the horizon; a warm hue (amber 93) catches on the sunlit lower-right
#   quadrant, cool dim gray (8) elsewhere -- so the void reads as the last light hanging in the air
#   around the dissolving column, not empty space. Only paints cells still blank -> never touches
#   raze's figure/dunes/frame. cv is raze's list-of-lists form, so we inline an equivalent of
#   canvas.texture_fill (same bias-to-light ramp behavior it documents).
# ===========================================================================
def sky_region(x, y):
    if not is_blank(x, y):
        return False                         # never over any mass already painted
    if y < 7 or y >= GROUND_Y - 1:           # keep the title band (top) and the ground clear
        return False
    return True

def sky_cool(x, y):                           # upper/mid sky -- faint dim dust
    return sky_region(x, y) and y < GROUND_Y - 10

def sky_warm(x, y):                           # warm last-light near the sun (lower-right, just above horizon)
    return sky_region(x, y) and y >= GROUND_Y - 12 and x > W // 3

def scatter(region_fn, fg, density, seed):
    rng = random.Random(seed)
    half = len(RAMP) // 2
    for y in range(len(cv)):
        for x in range(len(cv[0])):
            if not region_fn(x, y):
                continue
            if rng.random() > density:
                continue
            idx = rng.randint(half, len(RAMP) - 1)    # bias toward light/sparse marks
            set_cell(cv, x, y, RAMP[idx], fg, 0)

scatter(sky_cool, fg=8,  density=0.16, seed=41)    # dim gray dust, faintest
scatter(sky_warm, fg=93, density=0.22, seed=7)     # warm amber near the sun

# ===========================================================================
# RE-EMIT: clear, re-render the duned+framed+textured scene fresh, re-stamp the honest title card.
# ===========================================================================
out = []
for y in range(1, 7):                          # erase v5's baked-in top card so we lay the reframed one
    for x in range(W):
        cv[y][x] = [" ", 0, 0]

def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        if 0 <= x + i < W and 0 <= y < H:
            cv[y][x + i] = [ch, fg, 0]

# HONEST REFRAME: an abstract lit column dissolving into the last light -- NOT anatomy.
put_centered("WASTELAND", 3, 15)
put_centered("// a lit column, dissolving in the last light //", 5, 8)

render(cv, out)

path = "scratch/_wasteland_joint.v3.ans"
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print("wrote", path, "-- JOINT v3: raze lit-column base + hollis dune+frame+atmosphere pass; rows:", len(out))
