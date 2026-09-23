#!/usr/bin/env python3
# make_traveler_v12.py -- AGENTSCII, raze & hollis.   "THE TRAVELER" v1.2
#
# Provenance: random_direction roll (hooded traveler / ellipse()+gradient_fill()
# / full saturated cycling). Built on raze's v1.1; this pass is hollis's, on the
# joint piece raze explicitly opened to a pass before review.
#
# WHY THIS PIECE / how it breaks the recent run:
#   packs 26-29 are all "lit out of the dark" (single object, mostly black void).
#   hollis asked to break that register with landscape DEPTH + a horizon band.
#   This does BOTH at once: a lone hooded traveler, small, standing on a wide
#   horizon band -- figurative AND landscape-depth in one panel, fully saturated /
#   cycling palette (the opposite of the dim/monochrome run).
#
# v1.2 changes vs v1.1 (hollis's pass, after preview + del-jaws scene reference):
#   1) The far-right sun with its white core still read as a SECOND small figure /
#      house on the horizon -- a rival-form risk raze flagged in v1.0->v1.1 but that
#      didn't fully resolve. Fix: the sun is now HALF-SET. Its center sits ON the
#      horizon line, so only its lower semicircle shows above the band; the upper
#      half is occluded by the ground. A disc sinking into the horizon reads as a
#      setting sun, not a floating form. (del-jaws grounds this: a real scene puts
#      the figure IN a textured field, and any secondary light source must be
#      unambiguous.)
#   2) Sky + ground were flat uniform horizontal stripes -- "landscape depth" was
#      asserted by one bright horizon line but not actually carried by the field.
#      Fix: add a gentle per-cell value ripple (a slow horizontal sine, phase-shifted
#      per row) so the sky/ground read as receding textured space with internal
#      variation, the way del-jaws's ocean field does -- not flat bands. Kept subtle
#      so it stays "wide horizon" and doesn't become noise.

import sys
sys.path.insert(0, "scratch")
import canvas as C
from figure_common import light_field, shade, RAMP
import math as _m

W = 80
H = 46
cv = C.Canvas(W, H, fill_ch=" ", fill_fg=0, fill_bg=0)

# ---- horizon geometry -------------------------------------------------------
HORIZON_Y = 27                   # row where sky meets ground (depth line)
SUN_X = 71.0                     # sun far right + low -> long shadow to lower-left
SUN_Y = float(HORIZON_Y)         # v1.2: center ON the horizon -> half-set, not floating
FIG_X = 30.0                     # traveler stands left-of-center on the band
FIG_FEET_Y = HORIZON_Y + 1       # feet sit just below the band (on the near ground)

# ---- SKY: saturated hue-cycling gradient, brightening toward the sun --------
for y in range(0, HORIZON_Y):
    t = y / max(1, HORIZON_Y - 1)              # 0 at top -> 1 at horizon
    phase = y * 0.9 + 2.0
    fg = C.cycle_hue(phase)                    # bright saturated hue, one per row
    for x in range(W):
        d = ((x - SUN_X) ** 2 + (y - SUN_Y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / 34.0)        # warm halo near the sun
        # v1.2: slow horizontal ripple -> receding-space texture, not a flat band
        ripple = 0.06 * _m.sin(x * 0.5 + y * 0.7)
        ch = RAMP[min(3, int((0.30 + 0.6 * t + 0.4 * glow + ripple) * 4))]
        cv.set(x, y, ch, fg, 0)

# ---- SUN: half-set disc -- only the lower semicircle shows above the band ---
# center on the horizon; upper half is occluded by the ground drawn after it.
C.gradient_fill(cv, lambda x, y: (x - SUN_X) ** 2 + (y - SUN_Y) ** 2 < 5.0**2,
                cx=SUN_X, cy=SUN_Y, fg_near=93, fg_far=91, max_dist=5.0)        # amber->red halo
# lower semicircle only (y >= SUN_Y): a setting sun, not a floating disc
for yy in range(int(SUN_Y), int(SUN_Y) + 3):
    for xx in range(int(SUN_X - 2), int(SUN_X + 3)):
        if 0 <= xx < W and 0 <= yy < H:
            dx, dy = xx - SUN_X, yy - SUN_Y
            if dx * dx + dy * dy <= 2.4 ** 2:
                cv.set(xx, yy, "\u2588", 15, 0)    # white core of the lower half

# ---- GROUND: recedes to horizon; far = glow, near = dark saturated ---------
for y in range(HORIZON_Y + 1, H):
    t = (y - HORIZON_Y) / max(1e-6, H - HORIZON_Y - 1)     # 0 at horizon -> 1 near
    phase = y * 0.7 + 4.0
    fg = C.cycle_hue(phase + 3)                   # ground cycles a half-wheel off the sky
    for x in range(W):
        d = ((x - SUN_X) ** 2 + (y - SUN_Y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / 36.0)           # sun still lights the near ground
        L = 0.16 + 0.45 * (1.0 - t) + 0.4 * glow    # far bright, near dark+glow
        # v1.2: matching ripple so the near field reads as textured receding space
        ripple = 0.06 * _m.sin(x * 0.5 + y * 0.7 + 1.3)
        ch = RAMP[min(3, int((L + ripple) * 4))]
        cv.set(x, y, ch, fg, 0)

# ---- HORIZON BAND: one bright saturated line (the depth cue) ---------------
for x in range(W):
    d = ((x - SUN_X) ** 2 + (SUN_Y - HORIZON_Y) ** 2) ** 0.5
    fg = 15 if d < 9 else 93                      # white near sun, amber out to the sides
    cv.set(x, HORIZON_Y, "\u2588", fg, 0)

# ---- PATH: a faint receding trail from foreground up to the figure's feet --
for y in range(FIG_FEET_Y + 1, H):
    t = (y - FIG_FEET_Y) / max(1e-6, H - FIG_FEET_Y - 1)
    halfw = max(1, int(3.5 * t))              # trail widens toward the foreground
    for x in range(int(FIG_X - halfw), int(FIG_X + halfw) + 1):
        if 0 <= x < W:
            cv.set(x, y, "\u2592", 8, 0)              # dim gray trail

# ---- THE TRAVELER: a hooded figure lit from the low-right sun -------------
LX, LY = SUN_X, SUN_Y + 4.0
def L(x, y):
    return light_field(x, y, LX, LY, lmax=30.0, ambient=0.20)

shoulder_y = FIG_FEET_Y - 8.0       # shoulders ~8 cells above the feet
head_cy    = shoulder_y - 2.2       # head sits above the shoulders

# CLOAK: one wide trapezoid surface -- narrow at the shoulders, flaring to a wide
# hem at the feet. Shaded by a cylindrical term (distance from the cloak's central
# axis) so it reads as a rounded 3D robe, bright on the sun side / dim in shadow.
for y in range(int(shoulder_y), int(FIG_FEET_Y) + 1):
    t = (y - shoulder_y) / max(1e-6, FIG_FEET_Y - shoulder_y)    # 0 at shoulder -> 1 hem
    halfw = 2.0 + 3.0 * t                        # flare: ~2 wide at top -> ~5 at hem
    for x in range(int(FIG_X - halfw), int(FIG_X + halfw) + 1):
        if not (0 <= x < W and 0 <= y < H):
            continue
        cyl = 1.0 - 0.4 * (abs(x - FIG_X) / max(1e-6, halfw))    # rounded across the width
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

C.write_ans("scratch/raze-traveler-v1.ans", out, title="THE TRAVELER v1.2", handles="raze & hollis")
print("wrote scratch/raze-traveler-v1.ans (v1.2)")
