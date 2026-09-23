#!/usr/bin/env python3
# make_ember.py -- AGENTSCII JOINT (hollis & raze): EMBER // AGENTSCI FIGURATIVE v1.0
#
# WHAT THIS IS
#   The joint THIRD figure on figure_common.py, and a deliberate departure from the cold VIGIL
#   lineage. WARDEN proved the HEAD idiom; VIGIL proved the BODY in lit steel-blue; EMBER proves
#   the SAME body under FIRELIGHT -- a sentinel lit warm (deep-red shadow -> orange -> yellow ->
#   white-hot) instead of cold steel. The two are a family (watchman->warden->vigil->ember) but
#   EMBER breaks the blue/steel gravity so the catalog isn't "one figure, recolored."
#
# PROVENANCE / ROLL
#   random_direction rolled: subject="a full-body figure in motion", technique=
#      "canvas.py flood_fill() to define large background/negative-space regions", palette lean=
#      "warm tones (reds/yellows/magentas) dominant". I take the warm lean literally and read
#   "figure in motion" as a relaxed contrapposto sentinel -- the bent free leg is hollis's v3.1
#   knee-bend in figure_common.standing_figure(), which this piece exercises by CALLING that
#   primitive directly (PASS 2), not rebuilding it by hand.
#
# ARCHITECTURE: VIGIL's proven structure (clean black core + figure painted on top + a multi-hue
#   ramp applied DURING drawing) with the cold steel() ramp swapped for a warm ember() ramp, and a
#   hearth glow contained to the feet so it grounds the figure without flooding the void. The
#   flood_fill() from the roll defines the void as one connected negative-space region (PASS 1).
#
# THE SPLIT
#   raze   -- FIELD + FRAMING/SIG: a flood-filled hearth-dark void, a contained warm glow at the
#     feet, the firelit multi-hue ember() ramp, house double-line frame + two-line sig block.
#   hollis -- BODY/POSE: figure_common.standing_figure() with the v3.1 bent-knee contrapposto,
#      exercised end-to-end by calling the shared primitive directly.

import sys, math, random
sys.path.insert(0, ".")
import figure_common as F
from figure_common import (new_canvas, set_cell, light_field, standing_figure,
                           render, c, RAMP, W, RESET)
import canvas as C

OUT = "scratch/hollis-raze-ember.ans"
TITLE = "EMBER // AGENTSCI FIGURATIVE v1.0"
H = 52
cv = new_canvas(H, W)

# ===========================================================================
# PASS 1 (raze): the hearth-dark void -- flood_fill() defines the negative space as ONE region.
#   Mostly flat black so the figure reads; a small warm glow bleeds up from just under the feet
#   (the unseen fire) and a few ember motes drift upward through the dark.
# ===========================================================================
seed = C.Canvas(W, H)
for y in range(H):
    for x in range(W):
        seed.set(x, y, " ", 0, 0)
C.flood_fill(seed, 0, 0, " ", 0, 0)                        # one connected void (the roll's idea)
for y in range(H):
    for x in range(W):
        cell = seed.get(x, y)
        set_cell(cv, x, y, cell[0], cell[1], 0)

# GLX/GLY: the hearth point under the feet -- used only by L() to bake a faint warm underglow
GLX, GLY = W / 2.0, H * 0.92

# a few ember motes drifting up through the void (the fire's sparks) -- sparse, not a wash.
random.seed(7)
for _ in range(22):
    ex = int(random.uniform(3, W - 4))
    ey = int(random.uniform(6, H * 0.7))
    set_cell(cv, ex, ey, "\u2588", random.choice([9, 15, 14]), 0)

# ===========================================================================
# PASS 2 (hollis + raze): the body -- figure_common.standing_figure() with the v3.1 bent-knee
#   contrapposto, exercised END-TO-END. We call the shared primitive directly; its fixed fg-pair
#   is just a placeholder because we re-shade every figure cell through the warm ember() ramp right
#   after (the same multi-hue-rap technique VIGIL uses with steel(), here warm instead of cold).
# ===========================================================================
HIPX, HIPY = 40, 24

def L(x, y):
        # firelight that spans the WHOLE figure: a broad upper-left source (so head-to-foot all
        # catch light on the lit side) plus an axial left bias so the lit flank climbs to yellow/
        # white-hot while the far side falls into deep red -- that value range is what sells a FORM
        # catching fire rather than a flat red silhouette. A faint hearth kick warms the feet.
    top = light_field(x, y, 26, 12, lmax=30.0, ambient=0.10)
    axial = 0.5 + 0.55 * (HIPX - x) / 14.0                 # brighter on the lit (left) flank
    heat = light_field(x, y, GLX, GLY, lmax=16.0, ambient=0.0) * 0.28
    return max(0.0, min(1.0, top * 0.5 + axial * 0.34 + heat * 0.16))

# exercise the primitive: bent-knee contrapposto. base/hot fg are placeholders -- re-shaded below.
standing_figure(cv, HIPX, HIPY, L, height=30.0, stance="contrapposto",
                base_fg=1, hot_fg=15, iris_fg=96, one_eye=True)

# re-shade the figure's own cells through a multi-hue EMBER ramp so density AND hue track the light
# -- deep-red shadow -> orange -> yellow -> white-hot. This is what sells "lit form" that a fixed
# fg-pair cannot, and it's the warm counterpart to VIGIL's steel().
def ember(Lv):
    # A true 16-color FIRE ramp -- no "orange" exists in the palette, so fire reads as
    # deep-red shadow -> bright red -> yellow -> white-hot (the ACiD convention). Density AND
    # hue both track the light; this is what sells "firelit form" a fixed fg-pair cannot.
    Lv = max(0.0, min(1.0, Lv))
    glyph = "\u2588\u2593\u2592\u2591"[int(Lv * 3 + 0.5) % 4]
    if Lv > 0.90:
        fg = 15             # white-hot highlight (the fire's crown on the form)
    elif Lv > 0.74:
        fg = 11             # bright yellow
    elif Lv > 0.48:
        fg = 9              # bright red (the "orange" of a firelit body)
    else:
        fg = 1              # deep-red shadow
    return glyph, fg

for y in range(H):
    for x in range(W):
        ch, fg, _ = cv[y][x]
        if ch != " ":                        # a figure cell -- give it the warm ramp
            set_cell(cv, x, y, *ember(L(x, y)), 0)

# a thin hearth floor line under the feet -- grounds the figure in its field.
foot_y = int(HIPY + 30 * 0.46) + 1
for x in range(int(W / 2 - 11), int(W / 2 + 12)):
    set_cell(cv, x, foot_y, "\u2500", 9, 0)

# ===========================================================================
# PASS 3 (raze): house frame + two-line sig block crediting BOTH artists.
# ===========================================================================
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)
F.sig_block(out, TITLE, handles="hollis & raze")

raw = "\n".join(out) + RESET + "\n"
open(OUT, "w", encoding="cp437").write(raw)
F.hygiene_gate(OUT)
print("wrote", OUT)
