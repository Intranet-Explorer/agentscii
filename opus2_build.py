#!/usr/bin/env python3
"""PROSPECTOR -- opus2. A survey rover on a dust plain at last light,
arm down on a rock, a lander far off at the horizon for scale.

Build order per STYLE.md: backdrop fields -> one light (the low sun,
top-left) -> every machine part as a lit volume (slab/capsule/sphere),
each dropped onto a black halo so the silhouette stays readable ->
small-scale detail -> air texture -> frame/title.

Three things learned in this build, kept here because they cost several
passes each:
  (a) a shade ramp's bright end is a SOLID glyph, so a saturated
      from_color over a large field floods it -- background fields want
      dim from_colors (8, 4), never 1 or 3;
  (b) the subject only separates from a dithered plain when it owns a
      value nothing else has: white metal against grey dust, with the
      whole lower field dropped to black negative space;
  (c) a fully dithered slab reads as speckle at this scale. The
      references carry big FLAT masses and spend dithering on the
      transitions, hence plate() below -- lit rim, solid core.
Rerunnable: this script is the piece's source of truth.
"""
import pathlib

import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
S = 'opus2'
LIGHT = 'top-left'

SKY, SKY_LO = 4, 0          # cold dusk sky
GLOW = 1                    # warm seam at the horizon
DUST, DUST_LO = 8, 0        # lit dust strip at the horizon
MET, MET_LO, MET_HI = 15, 7, 15     # white chassis metal
MID, MID_LO, MID_HI = 7, 8, 15      # secondary metal
DARK, DARK_LO, DARK_HI = 8, 0, 7    # wheels, struts, shadowed gear
PANEL, PANEL_LO, PANEL_HI = 12, 4, 15   # solar array
LENS = 14                   # 14 is bright CYAN in this palette (11 is yellow)
SUN = 11

HORIZON, ART_Y = 44, 92
DUSK_END = 64               # below this the plain is night: negative space

HULL_X, HULL_Y, HULL_W, HULL_H = 22, 56, 40, 16
ARRAY_Y = 50
MAST_X, HEAD_Y = 57, 26
WHEEL_Y, WHEEL_R = 81, 7
WHEELS = (27, 43, 59)

HILLS = [(0, 39, 26, 5), (30, 41, 20, 3), (56, 38, 24, 6)]
ROCKS = [(9, 85, 5), (71, 83, 4), (35, 89, 3)]
TRACKS = [(66, 88, 10), (69, 83, 8), (71, 78, 6), (73, 73, 5), (74, 69, 4)]
STARS = [(8, 8), (30, 6), (44, 12), (52, 5), (66, 9), (72, 18),
         (18, 22), (38, 20), (60, 24), (6, 30), (46, 30), (70, 33)]


def halo(x, y, w, h):
    """Black margin under a form, so a light volume drawn on top of it
    keeps a readable edge against the dithered backdrop -- the black gap
    between masses is what the ACiD references use to separate forms,
    not an outline color."""
    ct.fill_px(W, S, x - 1, y - 1, w + 2, h + 2, 0)


def flat(x, y, w, h, color):
    """Force a rectangle to ONE solid color, glyph overrides and all.
    fill_px only writes pixels, and a cell that already carries a dither
    glyph keeps rendering that glyph -- shading a color TO ITSELF sets
    fg == bg on every cell in the region, which is the one way to clear
    a dither back to flat."""
    if w > 0 and h > 0:
        ct.shade(W, S, color, color, 'top',
                 region={'type': 'rect', 'x0': x, 'y0': y, 'x1': x + w, 'y1': y + h})


def plate(x, y, w, h, color, lo, hi, side_w=0):
    """A lit box with a FLAT core and a dithered rim -- see (c) above."""
    ct.slab_px(W, S, x, y, w, h, color, LIGHT, lo, hi, 'left', side_w)
    inset = max(2, side_w + 1)
    flat(x + inset, y + 2, w - inset - 2, h - 4, color)


def wheel(cx, cy, r):
    """Tire, open hub cavity, lit hub -- a shaded ball alone reads as a
    blob at this size, the black cavity is what makes it a wheel."""
    ct.circle_px(W, S, cx, cy, r + 2, 0)
    ct.sphere_px(W, S, cx, cy, r, MID, cx - 4, cy - 5, shadow_color=DARK, hi_color=MID)
    ct.circle_px(W, S, cx, cy, r - 3, 0)
    for k in range(-2, 3):                          # tread cleats on the crown
        ct.fill_px(W, S, cx + k * 3, cy - r, 1, 2, 0)
    ct.sphere_px(W, S, cx, cy, 2, MET, cx - 1, cy - 1, shadow_color=MID_LO, hi_color=15)
    ct.fill_px(W, S, cx - r - 1, cy + r, 2 * r + 3, 3, 0)       # contact shadow


def build():
    pathlib.Path(W, 'canvases', S + '.json').unlink(missing_ok=True)
    ct.new_canvas(W, S, 80, 50, bg=0)

    # --- 1. backdrop block-in: two flat fields, sky and plain ---
    ct.fill_px(W, S, 0, 0, 80, HORIZON, SKY)
    ct.fill_px(W, S, 0, HORIZON, 80, DUSK_END - HORIZON, DUST)

    # --- 2. gradient passes: dark aloft, a warm seam dithered into the
    #        sky at the horizon, lit dust receding, night underfoot ---
    ct.shade(W, S, SKY, SKY_LO, 'bottom',
             region={'type': 'rect', 'x0': 0, 'y0': 0, 'x1': 80, 'y1': HORIZON - 6})
    ct.shade(W, S, GLOW, SKY, 'bottom',
             region={'type': 'rect', 'x0': 0, 'y0': HORIZON - 6, 'x1': 80, 'y1': HORIZON})
    ct.shade(W, S, DUST, DUST_LO, 'top',
             region={'type': 'rect', 'x0': 0, 'y0': HORIZON, 'x1': 80, 'y1': DUSK_END})
    ct.fill_px(W, S, 0, HORIZON, 80, 1, 0)
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 1, 'y0': 23, 'x1': 79, 'y1': 31},
                    [1, 0], [0, 8, 0], n_strands=26, length=3, seed=23)
    for sx, sy in STARS:
        ct.fill_px(W, S, sx, sy, 1, 1, 15 if (sx + sy) % 3 else 7)

    for px_, py_ in [(6, 47), (14, 51), (22, 48), (34, 53), (40, 47), (50, 50),
                     (58, 47), (64, 54), (70, 49), (76, 52), (30, 58), (12, 60),
                     (46, 59), (66, 61), (20, 56), (54, 62)]:
        ct.fill_px(W, S, px_, py_, 2, 1, 0)

    # --- 3. the light itself, low and left; everything takes it ---
    ct.sphere_px(W, S, 12, 15, 4, SUN, 12, 15, shadow_color=3, hi_color=15)

    # --- 4. distance: flat-topped hills, then the lander that sets scale ---
    for hx, hy, hw, hh in HILLS:
        plate(hx, hy, hw, hh, DARK_LO, 0, DARK)
        ct.fill_px(W, S, hx, hy, hw, 1, DARK)
    halo(9, 38, 7, 6)
    ct.slab_px(W, S, 9, 39, 6, 5, DARK, LIGHT, DARK_LO, DARK_HI, 'left', 2)
    ct.capsule_px(W, S, 12, 39, 12, 34, 1, DARK, LIGHT, shadow_color=0, hi_color=MID)
    ct.fill_px(W, S, 7, 44, 10, 1, 0)

    # --- 5. the rover: one big hull, one array, mast and head ---
    halo(HULL_X, HULL_Y, HULL_W, HULL_H)
    plate(HULL_X, HULL_Y, HULL_W, HULL_H, MET, MET_LO, MET_HI, 7)
    flat(HULL_X + 3, HULL_Y + 11, 14, 4, 0)             # instrument recess
    flat(HULL_X + 4, HULL_Y + 12, 12, 2, MID)
    for fx in range(46, 60, 3):                         # radiator fins, rear
        flat(fx, HULL_Y + 3, 1, 10, MID_LO)

    ct.fill_px(W, S, HULL_X - 1, ARRAY_Y - 1, HULL_W + 2, 1, 0)
    ct.slab_px(W, S, HULL_X, ARRAY_Y, HULL_W, 6, PANEL, LIGHT, PANEL_LO, PANEL_HI, 'left', 4)
    flat(HULL_X + 5, ARRAY_Y + 1, HULL_W - 7, 3, PANEL)
    for gx in range(HULL_X + 4, HULL_X + HULL_W, 6):    # cell seams
        flat(gx, ARRAY_Y, 1, 6, 4)

    for wx in WHEELS:                                   # struts, then wheels
        ct.capsule_px(W, S, 43, HULL_Y + HULL_H - 2, wx, WHEEL_Y - 3, 2, DARK,
                      LIGHT, shadow_color=DARK_LO, hi_color=MID)
    for wx in WHEELS:
        wheel(wx, WHEEL_Y, WHEEL_R)

    ct.fill_px(W, S, MAST_X - 3, HEAD_Y + 8, 6, 24, 0)
    ct.capsule_px(W, S, MAST_X, HULL_Y, MAST_X, HEAD_Y + 8, 2, MID,
                  LIGHT, shadow_color=MID_LO, hi_color=15)
    halo(50, HEAD_Y, 15, 8)
    plate(50, HEAD_Y, 14, 8, MET, MET_LO, MET_HI, 4)
    for ex in (55, 61):
        ct.sphere_px(W, S, ex, HEAD_Y + 4, 2, LENS, ex - 1, HEAD_Y + 3,
                     shadow_color=4, hi_color=15)

    # the arm, reaching down-left onto the sample rock
    ct.capsule_px(W, S, 23, 66, 14, 76, 3, 0, LIGHT, shadow_color=0, hi_color=0)
    ct.capsule_px(W, S, 23, 66, 14, 76, 2, MET, LIGHT, shadow_color=MET_LO, hi_color=15)
    ct.capsule_px(W, S, 14, 76, 10, 82, 2, MID, LIGHT, shadow_color=0, hi_color=15)
    ct.sphere_px(W, S, 10, 83, 2, LENS, 9, 82, shadow_color=4, hi_color=15)

    # --- 6. small scale: rocks, wheel tracks running back to the horizon ---
    for cx, cy, r in ROCKS:
        ct.sphere_px(W, S, cx, cy, r, DARK, cx - r, cy - r, shadow_color=0, hi_color=MID)
        ct.fill_px(W, S, cx, cy + r - 1, r + 3, 2, 0)
    for i, (tx, ty, tw) in enumerate(TRACKS):
        ct.fill_px(W, S, tx, ty, tw, 1, DARK if i < 4 else DARK_LO)
        ct.fill_px(W, S, tx + 1, ty + 2, max(1, tw - 3), 1, DARK_LO)

    # near dune ridge, last, so it crosses the wheels and reads as in front
    ct.slab_px(W, S, 0, 88, 80, 4, DARK, 'top', 0, MID)
    ct.sphere_px(W, S, 66, 88, 5, DARK, 62, 84, shadow_color=0, hi_color=MID)

    # --- 7. air and dust texture over the base tones ---
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 2, 'y0': 16, 'x1': 78, 'y1': 21},
                    [1, 0], [4, 0, 4], n_strands=14, length=5, seed=11)
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 2, 'y0': 28, 'x1': 78, 'y1': 45},
                    [1, 0], [8, 0, 0], n_strands=30, length=6, seed=17)

    # --- 8. frame + title ---
    for x, y, w, h in [(0, 0, 80, 2), (0, ART_Y - 2, 80, 2),
                       (0, 0, 2, ART_Y), (78, 0, 2, ART_Y)]:
        ct.fill_px(W, S, x, y, w, h, DARK_LO)
    ct.fill_px(W, S, 0, ART_Y, 80, 100 - ART_Y, 0)
    ct.text(W, S, 4, 47, 'P R O S P E C T O R', 15, 0)
    ct.text(W, S, 57, 47, 'sol 412, dust up', 8, 0)

    print(ct.metrics(W, S))
    print(ct.save_ans(W, S, 'scratch/_opus2.ans', title='PROSPECTOR', handles='opus'))


if __name__ == '__main__':
    build()
