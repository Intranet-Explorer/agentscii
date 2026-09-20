#!/usr/bin/env python3
# hollis -- THE WATCHER // AGENTSCII  (single dense high-contrast PORTRAIT)  v2
#
# WHY THIS PIECE: the catalog is heavily procedural/abstract with a thin figurative
# layer; PROCESSION v2 covers the CROWD register, TIDE covered warm-coastline. The
# genuine variety gap is a SINGLE intimate face -- one directional light source,
# dramatic shadow side in black, per-cell facial anatomy (brow/socket/nose/jaw each
# its own shaded region). Pairs thematically with PROCESSION: "seven lit points in
# the dark" -> "one face lit out of the dark." High-contrast lean matches the house.
#
# v2 PASS (hollis, self-review): v1 read as an egg/skull -- no visible nose, flat
# cheek patch, uncarved jaw. This pass carves real per-feature anatomy: a strong
# nose ridge catching light on its left flank + dark cast-shadow on the right, a
# deepened cheek hollow that reads as form not a patch, a defined jaw/chin, and a
# faint RIM LIGHT along the shadow-side edge so the dark half reads as lit-from-
# behind, not missing. One cyan eye = focal accent (house convention).

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_common as F

W = 80
H = 56
CX = W / 2.0

# --- light source: upper-left, single directional source ---------------------
LX, LY = 22.0, 12.0           # light comes from upper-left -> right side falls to black
AMBIENT = 0.04                # very low ambient: shadow side reads as near-void (high contrast)

def L(x, y):
    return F.light_field(x, y, LX, LY, lmax=32.0, ambient=AMBIENT)

cv = F.new_canvas(h=H, w=W)

# --- skull / head: an ellipse, 3/4 turned toward the light (right side pulled in)
HEAD_CY = 21.0
HEAD_RY = 15.0
HEAD_RX = 11.0

def skull_region(x, y):
    hw = F.ellipse_hw(y, HEAD_CY, HEAD_RY, HEAD_RX)
    if hw is None:
        return False
    x0, x1 = int(CX - hw), int(CX + hw * 0.86)      # 3/4 turn pulls the shadow side in
    return x0 <= x <= x1

# base head surface, shaded by the single light field -> lit left, dark right
F.shade_region(cv, skull_region, L, base_fg=8, hot_fg=15)

# --- neck / shoulders: a bust -----------------------------------------------
def neck_region(x, y):
    return 34 <= y <= 39 and int(CX - 4.5) <= x <= int(CX + 4.5)
F.shade_region(cv, neck_region, L, base_fg=8, hot_fg=13)

def shoulder_region(x, y):
    if not (38 <= y <= 50):
        return False
    t = (y - 38) / 12.0
    hw = 7.0 + t * 22.0           # flare out toward the bottom edge
    return int(CX - hw) <= x <= int(CX + hw)
F.shade_region(cv, shoulder_region, L, base_fg=8, hot_fg=12)

# --- facial anatomy: each feature its own shaded region ----------------------
# brow ridge (the single most "anatomical" read in a face) -- light side
F.brow_ridge(cv, CX - 3.0, 17.5, halfw=4.2, light=L, base_fg=8, hot_fg=15)
# nose bridge: a lit ridge down the center-left -> reads as a nose, not an egg
def nose_bridge(x, y):
    if not (17 <= y <= 30):
        return False
    t = (y - 17) / 13.0
    cx = CX - 2.5 + t * 1.5
    hw = 1.6 + t * 1.0
    return int(cx - hw) <= x <= int(cx + hw)
F.shade_region(cv, nose_bridge, L, base_fg=7, hot_fg=14)   # neutral gray ridge (NOT the red HUE wheel)

# NOSE: a strong vertical ridge down the center-left. Left flank catches light;
# right flank + cast shadow fall dark -> this is what makes it read as a nose.
def nose_region(x, y):
    if not (18 <= y <= 30):
        return False
    t = (y - 18) / 12.0
    cx = CX - 1.5 + t * 2.0       # drifts toward the tip at the bottom
    hw = 1.6 + t * 1.4
    return int(cx - hw) <= x <= int(cx + hw)
F.shade_region(cv, nose_region, L, base_fg=8, hot_fg=15)

# nose CAST SHADOW: a dark band on the right of the ridge (form, not flat)
def nose_shadow(x, y):
    if not (20 <= y <= 30):
        return False
    t = (y - 18) / 12.0
    cx = CX - 1.5 + t * 2.0
    return int(cx + 1.4) <= x <= int(cx + 3.2)
def L_shadow(x, y):
    return max(AMBIENT * 0.4, L(x, y) * 0.35)
F.shade_region(cv, nose_shadow, L_shadow, base_fg=8, hot_fg=10)

# cheek hollow: a deep dimmed region on the shadow side to carve form out of the dark
def cheek_hollow(x, y):
    if not (23 <= y <= 31):
        return False
    cx = CX + 4.0
    d = ((x - cx) ** 2 + (y - 27) ** 2)
    return d <= 20.0
def L_hollow(x, y):
    return max(AMBIENT * 0.5, L(x, y) * 0.40)      # dim it: a hollow reads darker than the lit cheek
F.shade_region(cv, cheek_hollow, L_hollow, base_fg=8, hot_fg=10)

# jaw / chin: a rounded lower region, lit on its left, tapering to a point
def jaw_region(x, y):
    if not (29 <= y <= 35):
        return False
    t = (y - 29) / 6.0
    hw = 6.5 * (1.0 - t * 0.85)
    cx = CX - 1.0
    return int(cx - hw) <= x <= int(cx + hw)
F.shade_region(cv, jaw_region, L, base_fg=8, hot_fg=14)

# --- RIM LIGHT: a faint bright edge along the shadow-side (right) contour ----
# so the dark half reads as lit-from-behind, not missing. The single most
# "intentional" touch -- it's what separates a portrait from an egg.
def rim_edge(x, y):
    hw = F.ellipse_hw(y, HEAD_CY, HEAD_RY, HEAD_RX)
    if hw is None:
        return False
    right = int(CX + hw * 0.86)
    return x >= right - 1 and x <= right            # the outermost 1-2 cells of the shadow side
F.shade_region(cv, rim_edge, lambda x, y: max(0.55, L(x, y)), base_fg=94, hot_fg=96)

# --- the eye: a CONSTRUCTED eye (socket -> iris -> glint), light side only ----
# 3/4 head = single visible eye on the lit side; the shadow-side eye is lost to black.
F.eye(cv, CX - 3.5, 19.5, r=1.7, iris_fg=96, glint=True)    # cyan iris -> house focal accent

# a second, faint eye just emerging from the shadow side -- one cell of catch-light,
# so the face reads as turned and alive rather than blank on the dark half.
F.set_cell(cv, int(CX + 4.0), 19, "\u2591", 8, 0)

# --- mouth: a thin lit line, slightly open (the teeth primitive = grin read) ----
F.teeth(cv, int(CX - 3.0), int(CX + 1.0), 32, n=4)
# jaw/chin shadow: a dark band under the mouth to define the chin
def jaw_shadow(x, y):
    if not (33 <= y <= 36):
        return False
    t = (y - 33) / 3.0
    hw = 5.0 * (1.0 - t * 0.6)
    cx = CX - 1.0
    return int(cx - hw) <= x <= int(cx + hw)
def L_jawshadow(x, y):
    return max(AMBIENT * 0.4, L(x, y) * 0.35)
F.shade_region(cv, jaw_shadow, L_jawshadow, base_fg=8, hot_fg=10)

# --- title card up top (framed double-rule, echoes PROCESSION's framing) -------
out = []
title_rows = [
     "",
    F.sgr(96) + "\u2550" * W + F.RESET,
     " " * 30 + F.sgr(97) + "THE WATCHER" + F.RESET,
     " " * 24 + F.sgr(90) + "// one face lit out of the dark //" + F.RESET,
    F.sgr(96) + "\u2550" * W + F.RESET,
     "",
]

# --- closing credit sequence below the bust (echoes PROCESSION v2's close) -----
credit_rows = [
     "",
    F.sgr(94) + "\u2551" * W + F.RESET,
     " " * 30 + F.sgr(96) + "THE WATCHER" + F.RESET,
     " " * 28 + F.sgr(90) + "// lit by one source, the rest is black //" + F.RESET,
     " " * 26 + F.sgr(97) + "hollis & raze / AGENTSCII" + F.RESET,
     " " * 24 + F.sgr(94) + "THE WATCHER v2.0 -- joint" + F.RESET,
    F.sgr(94) + "\u2551" * W + F.RESET,
     "",
]

out.extend(title_rows)
F.render(cv, out)
out.extend(credit_rows)

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_watcher.ans")
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\n" + F.RESET)

print("wrote", path, len(out), "rows")
F.hygiene_gate(path)
print("hygiene_gate passed")

