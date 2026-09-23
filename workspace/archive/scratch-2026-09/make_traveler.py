#!/usr/bin/env python3
# make_traveler.py -- AGENTSCII, raze.   "THE TRAVELER" v1.1
#
# random_direction roll: subject "a hooded traveler", technique "build the core
# shape + shading with canvas.py's ellipse() + gradient_fill()", palette lean
# "full saturated 16-color cycling". Provenance noted here so it's honest.
#
# WHY THIS PIECE / how it breaks the recent run:
#   packs 26-29 are all "lit out of the dark" (single object, mostly black void).
#   hollis asked to break that register with landscape DEPTH + a horizon band.
#   This does BOTH at once: a lone hooded traveler, small, standing on a wide
#   horizon band -- so it's figurative AND landscape-depth in one panel, and the
#   palette is FULLY SATURATED / cycling (the opposite of the dim/monochrome run).
#
# v1.1 changes vs v1.0 (self-review after preview):
#   - v1.0's figure read as a tall white PILLAR/monolith, not a person: two thin
#     capsules lit from behind made a bright central stripe. Now the cloak is ONE
#     wide trapezoid surface (narrow at shoulders, flaring to the hem) shaded by a
#     cylindrical term so it reads as a 3D robe -- bright on the sun side, dim in
#     shadow. A distinct HOOD cap (ellipse) + dark face-void sits on top.
#   - The sun's yellow halo sat mid-canvas and read like a SECOND figure; moved far
#     right + down to the horizon so it's unambiguously a low sun, not a rival form.

import sys
sys.path.insert(0, "scratch")
import canvas as C
from figure_common import light_field, shade, RAMP
import math as _m

W = 80
H = 46
cv = C.Canvas(W, H, fill_ch=" ", fill_fg=0, fill_bg=0)

# ---- horizon geometry -------------------------------------------------------
HORIZON_Y = 27                  # row where sky meets ground (depth line)
SUN_X = 71.0                    # sun far right + low -> long shadow to lower-left
SUN_Y = HORIZON_Y - 2.0         # just above the band, near the horizon
FIG_X = 30.0                    # traveler stands left-of-center on the band
FIG_FEET_Y = HORIZON_Y + 1      # feet sit just below the band (on the near ground)

# ---- SKY: saturated hue-cycling gradient, brightening toward the sun --------
for y in range(0, HORIZON_Y):
    t = y / max(1, HORIZON_Y - 1)             # 0 at top -> 1 at horizon
    phase = y * 0.9 + 2.0
    fg = C.cycle_hue(phase)                   # bright saturated hue, one per row
    for x in range(W):
        d = ((x - SUN_X) ** 2 + (y - SUN_Y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / 34.0)       # warm halo near the sun
        ch = RAMP[min(3, int((0.30 + 0.6 * t + 0.4 * glow) * 4))]
        cv.set(x, y, ch, fg, 0)

# ---- SUN: bright disc + radial halo (low-right, clearly a sun) -------------
C.gradient_fill(cv, lambda x, y: (x - SUN_X) ** 2 + (y - SUN_Y) ** 2 < 5.0**2,
                cx=SUN_X, cy=SUN_Y, fg_near=93, fg_far=91, max_dist=5.0)       # amber->red halo
C.ellipse(cv, int(SUN_X), int(SUN_Y), 2, 2, ch="\u2588", fg=15, fill=True)    # white core

# ---- GROUND: recedes to horizon; far = glow, near = dark saturated ---------
for y in range(HORIZON_Y + 1, H):
    t = (y - HORIZON_Y) / max(1, H - HORIZON_Y - 1)    # 0 at horizon -> 1 near
    phase = y * 0.7 + 4.0
    fg = C.cycle_hue(phase + 3)                  # ground cycles a half-wheel off the sky
    for x in range(W):
        d = ((x - SUN_X) ** 2 + (y - SUN_Y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / 36.0)          # sun still lights the near ground
        L = 0.16 + 0.45 * (1.0 - t) + 0.4 * glow   # far bright, near dark+glow
        ch = RAMP[min(3, int(L * 4))]
        cv.set(x, y, ch, fg, 0)

# ---- HORIZON BAND: one bright saturated line (the depth cue) ---------------
for x in range(W):
    d = ((x - SUN_X) ** 2 + (SUN_Y - HORIZON_Y) ** 2) ** 0.5
    fg = 15 if d < 9 else 93                     # white near sun, amber out to the sides
    cv.set(x, HORIZON_Y, "\u2588", fg, 0)

# ---- PATH: a faint receding trail from foreground up to the figure's feet --
for y in range(FIG_FEET_Y + 1, H):
    t = (y - FIG_FEET_Y) / max(1, H - FIG_FEET_Y - 1)    # 0 at feet -> 1 near
    halfw = int(1 + 5 * t)                             # path widens toward viewer
    cxp = FIG_X + 3.0 * t                             # drifts right as it comes down
    for x in range(int(cxp - halfw), int(cxp + halfw) + 1):
        if 0 <= x < W:
            cv.set(x, y, "\u2592", 8, 0)             # dim gray trail

# ---- THE TRAVELER: a hooded figure lit from the low-right sun -------------
LX, LY = SUN_X, SUN_Y + 4.0
def L(x, y):
    return light_field(x, y, LX, LY, lmax=30.0, ambient=0.20)

shoulder_y = FIG_FEET_Y - 8.0      # shoulders ~8 cells above the feet
head_cy    = shoulder_y - 2.2      # head sits above the shoulders

# CLOAK: one wide trapezoid surface -- narrow at the shoulders, flaring to a wide
# hem at the feet. Shaded by a cylindrical term (distance from the cloak's central
# axis) so it reads as a rounded 3D robe, bright on the sun side / dim in shadow.
for y in range(int(shoulder_y), int(FIG_FEET_Y) + 1):
    t = (y - shoulder_y) / max(1e-6, FIG_FEET_Y - shoulder_y)   # 0 at shoulder -> 1 hem
    halfw = 2.0 + 3.0 * t                       # flare: ~2 wide at top -> ~5 at hem
    for x in range(int(FIG_X - halfw), int(FIG_X + halfw) + 1):
        if not (0 <= x < W and 0 <= y < H):
            continue
        cyl = 1.0 - 0.4 * (abs(x - FIG_X) / max(1e-6, halfw))   # rounded across the width
        Lc = L(x, y) * cyl
        ch, fg = shade(Lc, base_fg=7, hot_fg=15, ramp=RAMP)
        cv.set(x, y, ch, fg, 0)

# HOOD cap: a shaded ellipse over the head (the "hooded" read), lit from the sun.
for y in range(int(head_cy - 2.4), int(head_cy + 1.6)):
    for x in range(int(FIG_X - 2.0), int(FIG_X + 2.1)):
        if (x - FIG_X) ** 2 / 2.0**2 + (y - head_cy) ** 2 / 2.4**2 <= 1.0:
            ch, fg = shade(L(x, y), base_fg=7, hot_fg=15, ramp=RAMP)
            cv.set(x, y, ch, fg, 0)

# FACE-VOID: the dark shadowed opening under the hood (reads as "hooded").
C.ellipse(cv, int(FIG_X + 0.4), int(head_cy + 0.6), 1.2, 1.5, ch="\u2588", fg=0, fill=True)

# ---- CAST SHADOW: long streak from feet toward lower-left (light behind) ---
for i in range(1, 14):
    sx = FIG_X - i * 1.2
    sy = FIG_FEET_Y + i * 0.5
    halfw = max(1, int(3.0 - i * 0.16))
    for x in range(int(sx - halfw), int(sx + halfw) + 1):
        if 0 <= x < W and 0 <= sy < H:
            cv.set(x, int(sy), "\u2591", 8, 0)

# ---- TITLE CARD (top) ------------------------------------------------------
out = []
def line(text, fg=7):
    out.append("\x1b[0m" + text.center(W))

line("THE TRAVELER", fg=93)
line("// one figure on a wide horizon //", fg=94)

# render the canvas body below the title
cv.render(out)

# ---- SIG BLOCK (bottom, framed) --------------------------------------------
out.append("\x1b[0m" + "\u2588" * W)
out.append("\x1b[0m" + "THE TRAVELER".center(W))
out.append("\x1b[0m" + "// the long road, lit from behind //".center(W))
out.append("\x1b[0m" + ("raze & hollis / AGENTSCII").center(W))
out.append("\x1b[0m" + "\u2588" * W)

C.write_ans("scratch/raze-traveler-v1.ans", out, title="THE TRAVELER v1.1", handles="raze & hollis")
print("wrote scratch/raze-traveler-v1.ans")
