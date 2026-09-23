#!/usr/bin/env python3
"""CROSSING -- opus3. A cable car mid-span over a gorge: a big lattice
tower on the near rim, a smaller one on the far rim, the cabin hanging
alone between them, fog and a river down in the throat.

Three scales in one frame on purpose -- the near tower and its rim carry
the left third, the cabin is a hand-sized warm mass at centre, the far
tower and the peaks behind it are a few pixels of value each.

Carried forward from opus2, at the cost of several renders each:
  (a) big fields want DIM from_colors -- a ramp's bright end is a solid
      glyph, so shading from a saturated colour floods the field;
  (b) the subject reads only when it owns a value nothing else has --
      here the cabin is the one warm mass in an all-cold landscape;
  (c) dither belongs on transitions and rims, not inside a mass. Every
      find_patches hit for this arrangement is big FLAT silhouettes with
      the dithering spent where two masses meet.

Learned on this piece, and it cost four renders: a cell that already
carries a dither glyph KEEPS RENDERING THAT GLYPH, so every fill_px mark
laid on top of a shaded field is invisible -- the mountains, the rim
lines, the river and the window frames were all being drawn into
nothing. mark() below writes through a dither by shading a colour to
itself (which also sets fg == bg) and is what every pass after the first
gradient uses. fill_px is only safe on virgin canvas.

Rerunnable: this script is the piece's source of truth.
"""
import pathlib

import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
S = 'opus3'
LIGHT = 'top-left'

SKY_LO = 0
BLUE = 4                             # the air: cold, dithering out to black
FAR, FAR_HI = 0, 7                   # far peaks: black rock, lit snow crest
ROCK, ROCK_LO, ROCK_HI = 8, 0, 8     # gorge walls: rock never goes
                                     # brighter than 8, so 7/15 reads as steel
FOG = 8                              # fog bank in the throat
STEEL, STEEL_LO, STEEL_HI = 7, 8, 15
CAB, CAB_LO, CAB_HI = 3, 1, 11       # the cabin -- the only warm value
GLASS, GLASS_HI = 4, 14

ART_Y = 92
RIDGE = 40                           # far peaks stand on this line
L_RIM, R_RIM = 50, 44                # cliff tops: near wall lower and closer
L_X, R_X = 26, 54                    # gorge mouth
FOG_TOP, FOG_BOT = 70, 82

CABLE = [(12, 32), (41, 45), (66, 27)]
HAUL = [(12, 38), (41, 51), (66, 33)]

CAB_X, CAB_Y, CAB_W, CAB_H = 30, 50, 22, 14
HANG_X = 41

PEAKS = [(0, 20, 30), (28, 12, 22), (54, 17, 28)]   # few and big: the blue
                                                    # between them is the shape
BIRDS = [(47, 18), (51, 20), (56, 17)]
SCRUB = [(2, 50), (6, 49), (11, 50), (17, 51), (21, 52), (24, 53),
         (56, 45), (61, 44), (66, 44), (71, 45), (75, 46), (78, 47)]


def mark(x, y, w, h, color):
    """Write a flat mark THROUGH whatever is already there. Both halves are
    needed and each fixes a different leak: fill_px alone leaves any dither
    glyph already in the cell rendering on top of the new pixels, and
    shading a colour to itself alone (which does set fg == bg) DELETES the
    glyph on the ramp's empty steps and lets the stale pixels underneath
    show through -- that was the grey speckle crawling over every black
    mass in the first six renders of this piece."""
    if w > 0 and h > 0:
        ct.fill_px(W, S, x, y, w, h, color)
        ct.shade(W, S, color, color, 'top',
                 region={'type': 'rect', 'x0': x, 'y0': y, 'x1': x + w, 'y1': y + h})


def void(x, y, w, h):
    """Clear a pixel rect to real black CELLS (spaces), rounding out to
    whole cells. Needed because a dither glyph whose fg is colour 0 comes
    out of save_ans as BOLD black -- grey 8 -- so every "black" mass laid
    down with shade() was rendering as grey speckle. Spaces are the only
    mark that is actually black, and canvas_stamp is the one tool that
    writes literal cells."""
    if w <= 0 or h <= 0:
        return
    r0, r1 = y // 2, -(-(y + h) // 2)
    c0, c1 = max(0, x), min(80, x + w)
    rows, cols = max(0, r1 - r0), max(0, c1 - c0)
    if rows and cols:
        ct.stamp(W, S, c0, r0, [[32] * cols] * rows,
                 [[0] * cols] * rows, [[0] * cols] * rows)


def halo(x, y, w, h):
    """Black margin under a form so a lit volume keeps a readable edge --
    the references separate masses with a black gap, not an outline."""
    void(x - 1, y - 1, w + 2, h + 2)


def wall(x0, x1, rim, step, face, lit_face):
    """A gorge wall. Two parts, and the second is what makes a gorge read
    as depth instead of two dark edges: a staircase of lit rim bands, then
    a vertical inner face plunging from the rim into the fog. Light is
    top-left for the whole piece, so the right-hand wall's inner face
    catches it and the left-hand wall's inner face is in shadow."""
    n, band = 3, 8
    for i in range(n):
        a = min(x0 + (x1 - x0) * i // n, x0 + (x1 - x0) * (i + 1) // n)
        b = max(x0 + (x1 - x0) * i // n, x0 + (x1 - x0) * (i + 1) // n)
        y = rim + i * step
        void(a, y, b - a, ART_Y - y)                       # the mass
        ct.slab_px(W, S, a, y, b - a, band, ROCK, LIGHT, ROCK_LO, ROCK_HI,
                   face, 3)                                # lit rim band
        mark(a, y, b - a, 1, ROCK_HI if i < 2 else ROCK)   # rim line
        void(a, y + band, b - a, ART_Y - y - band)         # black below it
    inner_x = x1                                           # gorge-facing edge
    top = rim + (n - 1) * step
    if lit_face:
        ct.slab_px(W, S, inner_x, top, 8, FOG_BOT - top, ROCK, LIGHT,
                   ROCK_LO, ROCK_HI, 'left', 4)
        mark(inner_x, top, 1, FOG_BOT - top, ROCK_HI)
        for k in range(3):                                 # ledges, lit tops
            ct.slab_px(W, S, inner_x + 2 + k, top + 6 + k * 8, 9 - k, 3,
                       ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 2)
    else:
        ct.slab_px(W, S, inner_x - 6, top, 6, FOG_BOT - 4 - top, ROCK_LO,
                   LIGHT, 0, ROCK, 'left', 3)
        mark(inner_x - 1, top, 1, FOG_BOT - 4 - top, ROCK)
        for k in range(3):                                 # ledges, in shadow
            ct.slab_px(W, S, inner_x - 12 - k * 2, top + 4 + k * 8, 8, 3,
                       ROCK_LO, LIGHT, 0, ROCK, 'left', 2)


def tower(x, top, base, w):
    """Lattice pylon: two lit legs, X bracing, a saddle across the top."""
    halo(x - 2, top - 4, w + 4, base - top + 6)
    span = max(6, (base - top) // 3)
    for y in range(top + 3, base - span, span):            # bracing, behind
        ct.capsule_px(W, S, x, y, x + w, y + span, 1, STEEL_LO, LIGHT,
                      shadow_color=0, hi_color=STEEL)
        ct.capsule_px(W, S, x + w, y, x, y + span, 1, STEEL_LO, LIGHT,
                      shadow_color=0, hi_color=STEEL)
    for lx in (x, x + w):                                  # legs, in front
        ct.capsule_px(W, S, lx, top, lx, base, 2, STEEL, LIGHT,
                      shadow_color=STEEL_LO, hi_color=STEEL_HI)
    ct.slab_px(W, S, x - 2, top - 4, w + 5, 4, STEEL, LIGHT,
               STEEL_LO, STEEL_HI, 'left', 2)


def rope(pts, r, color, hi):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ct.capsule_px(W, S, ax, ay, bx, by, r, color, LIGHT,
                      shadow_color=STEEL_LO, hi_color=hi)


def build():
    pathlib.Path(W, 'canvases', S + '.json').unlink(missing_ok=True)
    ct.new_canvas(W, S, 80, 50, bg=0)

    # --- 1. block-in: black ground, one air field in the lower sky ---
    ct.fill_px(W, S, 0, 0, 80, ART_Y, 0)
    ct.fill_px(W, S, 0, 6, 80, RIDGE - 6, BLUE)

    # --- 2. one gradient, dim from-colour: the air brightens toward the
    #        ridge and dissolves to black aloft ---
    ct.shade(W, S, BLUE, SKY_LO, 'bottom',
             region={'type': 'rect', 'x0': 0, 'y0': 6, 'x1': 80, 'y1': RIDGE})

    # --- 3. far peaks: black silhouettes on the air, lit snow on the
    #        side facing the light, feet dissolving into haze ---
    for px, ph, pw in PEAKS:
        for k in range(ph):
            wk = max(1, (pw * (k + 1)) // ph)              # narrow at the summit
            x = px + (pw - wk) // 2
            mark(x, RIDGE - ph + k, wk, 1, FAR)
            if 0 < k < 5:
                mark(x, RIDGE - ph + k, max(1, wk // 3), 1, FAR_HI)
    ct.shade(W, S, FOG, SKY_LO, 'top',
             region={'type': 'rect', 'x0': 0, 'y0': RIDGE - 3, 'x1': 80, 'y1': RIDGE + 3})

    # --- 4. the gorge throat: black void, fog bank in it, river at the foot ---
    void(0, RIDGE + 4, 80, ART_Y - RIDGE - 4)
    for i in range(6):
        inset = abs(i - 2) * 3
        ct.fill_px(W, S, L_X - 4 + inset, FOG_TOP + i * 2,
                   R_X - L_X + 8 - 2 * inset, 2, FOG)
    ct.shade(W, S, FOG, 0, 'top',
             region={'type': 'rect', 'x0': L_X - 4, 'y0': FOG_TOP,
                     'x1': R_X + 4, 'y1': FOG_BOT})
    for i, (rx, rw) in enumerate([(32, 18), (34, 14), (36, 10), (38, 7)]):
        mark(rx, FOG_BOT + i * 2, rw, 1, ROCK if i < 2 else STEEL)

    # --- 5. the two walls: near wall left and low, far wall right ---
    wall(0, L_X, L_RIM, 6, 'right', False)
    wall(80, R_X, R_RIM, 4, 'left', True)
    for sx, sy in SCRUB:                    # rim scrub, sets the rock's scale
        void(sx, sy - 4, 1, 4)
        mark(sx, sy - 5, 1, 1, ROCK)

    # --- 5b. the near shelf: the closest rock in the frame, lit top and
    #         a dark body, with pines standing ON it so they read as
    #         silhouettes against lit stone rather than black on black ---
    void(0, 74, 34, ART_Y - 74)
    mark(0, 76, 34, 2, ROCK)                              # lit shelf edge
    for tx, th in ((5, 12), (11, 16), (18, 10), (25, 14)):
        for k in range(th):                               # pines, dim grey on
            wk = max(1, (6 * (k + 1)) // th)              # black: silhouettes
            mark(tx - wk // 2, 76 - th + k, max(1, wk), 1, ROCK_LO if k < 2 else ROCK)
        void(tx + 3, 76 - th, 2, th)                      # gap to the next tree

    # --- 6. towers on the rims, then the span across the sky ---
    tower(8, 30, L_RIM + 2, 8)
    tower(63, 25, R_RIM + 1, 6)
    rope(HAUL, 1, STEEL_LO, STEEL)
    rope(CABLE, 1, STEEL, STEEL_HI)

    # --- 7. the cabin: the one warm mass, hung in the gorge mouth ---
    halo(CAB_X - 2, CAB_Y - 4, CAB_W + 5, CAB_H + 8)
    ct.capsule_px(W, S, HANG_X, 44, HANG_X, CAB_Y + 2, 2, STEEL, LIGHT,
                  shadow_color=STEEL_LO, hi_color=STEEL_HI)
    ct.sphere_px(W, S, HANG_X, 45, 3, STEEL, HANG_X - 2, 43,
                 shadow_color=STEEL_LO, hi_color=15)
    ct.slab_px(W, S, CAB_X, CAB_Y, CAB_W, CAB_H, CAB, LIGHT, CAB_LO, CAB_HI,
               'left', 3)
    mark(CAB_X + 3, CAB_Y + 2, CAB_W - 6, CAB_H - 4, CAB)          # flat core
    mark(CAB_X, CAB_Y + 2, 2, CAB_H - 4, CAB_HI)                   # lit face
    mark(CAB_X + CAB_W - 2, CAB_Y + 2, 2, CAB_H - 4, CAB_LO)       # shadow face
    ct.slab_px(W, S, CAB_X - 2, CAB_Y - 4, CAB_W + 4, 4, STEEL, LIGHT,
               STEEL_LO, STEEL_HI, 'left', 2)                      # roof cap
    mark(CAB_X + 2, CAB_Y + CAB_H - 2, CAB_W - 4, 2, CAB_LO)       # skirt
    mark(CAB_X + 3, CAB_Y + 4, CAB_W - 6, 4, GLASS)                # window band
    mark(CAB_X + 4, CAB_Y + 4, 4, 2, GLASS_HI)                     # one glint

    # --- 7b. the other car, small and far up the span: same object,
    #         a third of the size, which is what sets the distance ---
    halo(57, 28, 9, 9)
    ct.capsule_px(W, S, 61, 29, 61, 32, 1, STEEL, LIGHT,
                  shadow_color=STEEL_LO, hi_color=STEEL_HI)
    ct.slab_px(W, S, 57, 32, 8, 5, CAB, LIGHT, CAB_LO, CAB_HI, 'left', 2)
    mark(58, 33, 6, 2, GLASS)

    # --- 7c. river bed, then boulders standing in it ---
    mark(28, FOG_BOT + 2, 26, 2, ROCK_LO)
    for bx, by, br in ((36, 86, 3), (45, 88, 2)):
        ct.sphere_px(W, S, bx, by, br, ROCK, bx - br, by - br,
                     shadow_color=0, hi_color=STEEL)

    # --- 7d. hardware: two grips riding the cable, small enough to read
    #         as fittings rather than as blobs in the air ---
    for gx, gy in ((26, 38), (54, 39)):
        ct.sphere_px(W, S, gx, gy, 1, STEEL, gx - 1, gy - 1,
                     shadow_color=STEEL_LO, hi_color=STEEL_HI)

    # --- 7e. rock grain on the two wall faces: strand_shade used the way
    #         it actually works -- a narrow region, strokes one value off
    #         the field, combed with the fall of the rock. Over a big field
    #         the same call reads as rain (learned on opus2) ---
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 62, 'y0': 28, 'x1': 78, 'y1': 42},
                    [-1, 3], [0, ROCK, 0], n_strands=16, length=3, seed=9)

    # --- 8. small marks last: birds against the far air ---
    for bx, by in BIRDS:
        void(bx, by, 3, 1)

    # --- 9. frame + title ---
    for x, y, w, h in [(0, 0, 80, 2), (0, ART_Y - 2, 80, 2),
                       (0, 0, 2, ART_Y), (78, 0, 2, ART_Y)]:
        mark(x, y, w, h, ROCK_LO)
    void(0, ART_Y, 80, 100 - ART_Y)
    ct.text(W, S, 4, 47, 'C R O S S I N G', 15, 0)
    ct.text(W, S, 58, 47, 'span 4, wind rising', 8, 0)

    print(ct.metrics(W, S))
    print(ct.save_ans(W, S, 'scratch/_opus3.ans', title='CROSSING', handles='opus'))


if __name__ == '__main__':
    build()
