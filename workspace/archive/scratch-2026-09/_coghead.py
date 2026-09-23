#!/usr/bin/env python3
# raze -- COGHEAD v1.1 // AGENTSCII   (solo raze)
#
# random_direction roll: subject="a robot or cyborg head", technique=
# "use canvas.py's flood_fill() to define large background/negative-space
# regions", palette lean="high contrast -- mostly black with bright accents".
# Taken straight on the primitive, REMIXED on construction and noted honestly.
#
# WHY THIS IS DISTINCT IN THE HOUSE:
#      - _watcher (pack28): a FACE LIT OUT OF pure black -- gray capsule-shaded
#        anatomy fading to dark; the mass is the figure, the void is everything
#        around it.
#      - cyborg-scope (pack28): a STATIC phosphor diagnostic READOUT of one form.
# COGHEAD inverts the watcher's logic: a SOLID FILLED metallic head mass with
# interior NEGATIVE-SPACE voids (eye sockets, jaw grille) punched through it, so
# light reads as passing THROUGH a cutout rather than falling ON a surface. High
# contrast -- mostly-black field + black carved cavities, with the metal mass and
# a few bright circuit accents as the only lit matter. Also the first house piece
# to actually use canvas.flood_fill().
#
# v1.1 CHANGE (from hollis's read on the v1.0 lower third): the old jaw-vent loop
# punched a horizontal slot STRAIGHT THROUGH the jaw ellipse, severing it into two
# disconnected columns (rows 31-33) with a single dangling char at row 38 -- that
# read as broken/debris, not intentional void. v1.1 keeps the strong top half and
# rebuilds the lower third as deliberate carved-void ANATOMY:
#      - jaw grille = short bright dashes recessed INSIDE the jaw (never severing
#        it) -- a vent that reads as anatomy, not a cut;
#      - neck mount + power core below, so the head sits on something instead of
#        floating into scattered fragments. The voids stay clean black cavities
#        with thin bright rims; the lower field is true negative space (flood_fill),
#        not debris.

import sys
sys.path.insert(0, "scratch")
from canvas import Canvas, ellipse, rect, line, flood_fill, dither_region, RAMP

W = 80
H = 52                          # head mass + carved voids + neck mount + power core + sig
LIGHT_X, LIGHT_Y = 31.0, 11.0      # off-center upper-left light source (ACiD directional)
LMAX = 28.0

# ---------------------------------------------------------------------------
# STEP 1 -- structured backdrop: a faint dim-blue graticule over the whole field
# so empty space has structure instead of flat black. This is what flood_fill will
# later erase, making its "large negative-space region" move visible.
# ---------------------------------------------------------------------------
cv = Canvas(W, H, fill_ch=' ', fill_fg=8, fill_bg=0)
for y in range(H):
    for x in range(W):
        if (x % 4 == 0) and (y % 3 == 0):
            cv.set(x, y, '\u2591', 4, 0)           # dim blue grid dots

# ---------------------------------------------------------------------------
# STEP 2 -- the flood_fill move: seed from a corner and flood the whole field to
# solid black. The fill spreads across every un-occupied cell (the graticule dots
# are a different char/fg so it stops at them, then we clear them) -- this defines
# the large surrounding negative-space region in one primitive call.
# ---------------------------------------------------------------------------
flood_fill(cv, 0, 0, ' ', fg=8, bg=0)             # flood the structured field to black void
for y in range(H):                                 # sweep away any grid dots the fill left behind
    for x in range(W):
        cell = cv.get(x, y)
        if cell[0] != ' ':
            cv.set(x, y, ' ', 8, 0)

# ---------------------------------------------------------------------------
# STEP 3 -- the metal mass: a filled cyborg head silhouette (cranium + jaw),
# shaded as a lit 3D curved surface by one directional light. Three tiers so it
# reads as METAL not a dim blob: white-hot highlight near the light, bright cyan
# body, dim blue on the far/shadow side -- capped so it shows a gradient, never a
# flat stripe (the same "lit surface" craft the traveler-robe v5 fix landed on).
# ---------------------------------------------------------------------------
def head_mass(x, y):
     cr = ((x - 40) / 15.0) ** 2 + ((y - 16) / 13.0) ** 2 <= 1.0     # cranium
     jaw = ((x - 40) / 11.0) ** 2 + ((y - 30) / 8.0) ** 2 <= 1.0     # jaw
     brow = 13 <= y <= 19 and abs(x - 40) <= 14                       # flat brow ridge band
     return cr or jaw or brow

def light_density(x, y):
    d = ((x - LIGHT_X) ** 2 + (y - LIGHT_Y) ** 2) ** 0.5 / LMAX
    return max(0.0, min(1.0, 1.0 - d))

dither_region(cv, head_mass, light_density, fg=94, bg=0)      # bright cyan metal body
for y in range(H):
    for x in range(W):
        if not head_mass(x, y):
            continue
        d = ((x - LIGHT_X) ** 2 + (y - LIGHT_Y) ** 2) ** 0.5 / LMAX
        if d > 0.62:                         # far/shadow side -> dim blue metal, still visible
            cv.set(x, y, '\u2588', 4, 0)

# white-hot catch light on the lit edge (thin bright rim just inside the top-left)
for y in range(3, 30):
    for x in range(24, 56):
        if head_mass(x, y) and not head_mass(x + 1, y - 1):
            cv.set(x, y, '\u2588', 15, 0)

# ---------------------------------------------------------------------------
# STEP 4 -- interior NEGATIVE-SPACE voids: clean black cavities with a thin bright
# rim (a beveled edge), reliable and crisp -- no fragile fills. These are the
# "carved voids" of the title: eye sockets + jaw grille punched through the metal.
# ---------------------------------------------------------------------------
def carve_ellipse(cx, cy, rx, ry, rim_fg=15):
      for y in range(int(cy - ry), int(cy + ry) + 1):           # thin bright rim ring
         for x in range(int(cx - rx), int(cx + rx) + 1):
             e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
             if 0.86 <= e <= 1.18 and head_mass(x, y):
                 cv.set(x, y, '\u2588', rim_fg, 0)
      for y in range(int(cy - ry + 1), int(cy + ry)):           # black interior cavity
         for x in range(int(cx - rx + 1), int(cx + rx)):
             e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
             if e < 0.86:
                 cv.set(x, y, ' ', 8, 0)

carve_ellipse(31, 19, 5.0, 4.0, rim_fg=15)      # left eye socket (light side)
carve_ellipse(49, 19, 5.0, 4.0, rim_fg=15)      # right eye socket (shadow side)

# jaw grille -- RECESSED INSIDE the jaw: short bright dashes that read as a vent
# without severing the mass (the v1.0 bug). Each dash is a small black cavity with
# a thin cyan rim, sitting well inside the jaw ellipse so the metal stays connected.
for gx in range(34, 47, 2):
    carve_ellipse(gx, 33, 1.0, 1.6, rim_fg=94)

# two small cranial recesses high on the temples -- secondary voids for rhythm
carve_ellipse(27, 12, 2.5, 2.0, rim_fg=94)
carve_ellipse(53, 12, 2.5, 2.0, rim_fg=94)

# ---------------------------------------------------------------------------
# STEP 5 -- BRIGHT ACCENTS against the mostly-black field: circuit traces + eye
# glints -- the "bright accents" of the high-contrast lean, sparse and loud,
# sitting in or around the voids so they read as energy inside the dark cavities.
# ---------------------------------------------------------------------------
cv.set(30, 20, '\u2588', 96, 0)      # left eye -- bright cyan glint deep in the socket
cv.set(31, 20, '\u2588', 107, 0)     # white-hot core
cv.set(49, 20, '\u2588', 96, 0)      # right eye -- bright cyan glint
cv.set(48, 20, '\u2588', 107, 0)     # white-hot core

# a magenta circuit bus down the center of the cranium (a "spine" wire) feeding the eyes
line(cv, 40, 10, 40, 30, ch='\u2588', fg=95, bg=0)
line(cv, 40, 16, 31, 19, ch='\u2588', fg=95, bg=0)      # branch into left socket
line(cv, 40, 16, 49, 19, ch='\u2588', fg=95, bg=0)      # branch into right socket

# a green sensor on the lit cheek + an amber one on the shadow cheek (asymmetry = life)
cv.set(27, 23, '\u2588', 102, 0)      # bright green
cv.set(53, 25, '\u2588', 103, 0)      # amber

# ---------------------------------------------------------------------------
# STEP 6 -- LOWER THIRD as deliberate anatomy (the v1.1 fix): a neck mount and a
# power core the head sits on, so the lower field is carved structure instead of
# scattered fragments. The spine wire already runs to y=30; continue it down the
# neck into the core. Everything here is lit metal / bright energy on true void.
# ---------------------------------------------------------------------------

# NECK MOUNT -- a tapered column of metal descending from the jaw center. Lit cyan
# near the jaw, dimming to blue as it recedes (continues the head's light logic).
for y in range(34, 42):
    half = 3 - (y - 34) // 4          # tapers: wide at top, narrow at bottom
    for x in range(40 - half, 40 + half + 1):
        lit = abs(x - LIGHT_X) < abs(x - 50)   # left side catches the light
        cv.set(x, y, '\u2588', 94 if lit else 4, 0)

# POWER CORE -- a small recessed ring at the base of the mount: black cavity with a
# bright rim and a hot energy glint at its center. The head's "heart".
core_cx, core_cy = 40, 43
for y in range(core_cy - 2, core_cy + 3):
    for x in range(core_cx - 3, core_cx + 4):
        e = ((x - core_cx) / 3.0) ** 2 + ((y - core_cy) / 2.0) ** 2
        if 0.7 <= e <= 1.25:
            cv.set(x, y, '\u2588', 95, 0)      # magenta rim ring
cv.set(core_cx, core_cy, '\u2588', 124, 0)     # hot red energy glint at the core center
cv.set(core_cx - 1, core_cy, '\u2588', 96, 0)  # cyan feed on the lit side of the core

out = []
cv.render(out)
import canvas as C
C.write_ans("scratch/_coghead.ans", out,
            title="COGHEAD v1.1 -- carved voids, neck mount + power core",
            handles="raze")
