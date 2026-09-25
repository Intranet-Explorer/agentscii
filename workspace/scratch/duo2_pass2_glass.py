#!/usr/bin/env python3
"""duo2 pass 2 -- the pane: fracture, facets, bevel, void.

Retrieval before this pass:
  find_patches_clip('cracked glass surface texture')
    -> 1996/gvt-0196/SH-LOGO1.ANS, 2024/fire-40/SF-INC.ANS
  find_patches_clip('shattered glass shards radiating from an impact')
    -> 1996/gvt-0196/SH-LOGO1.ANS, 1995/spas9510/PK-TSA.ANS

SH-LOGO1 is the whole lesson. Its fracture is ONE fg/bg pair the entire
way (80, grey on black) and carries everything with glyph CHOICE:

  r02  3:▐ 4:▌   7:▓ 8:░   11:▐ 12:▌  14:▐ 15:▌  17:▄▄  22:▄
  r03  0:░░ 3:▄ 4:▓ 5:▀ 6:▐ 7:▌ 9:▀ 10:▄▄  14:▄ 15:▓ 16:▀▀ 20:▀
  r04  0:▄ 1:▒ 2:▓ 3:▀ 4:▐ 5:▌ 6:█  8:░  10:▄ 11:▓ 12:█ 13:▀

Short runs, one to three cells, the orientation flipping cell to cell --
▐▌ where the break runs vertically through the cell, ▀▄ where it runs
horizontally, ░▒▓ where a facet is just catching less light. It is not a
dither field; every glyph is a piece of an edge.

Reproduced here by making the fracture a VALUE feature and letting the
same mapping rule pick the glyph:

  - the pane is divided into FACETS by the cracks already in the
    block-in -- angular sectors off the break centre, each tilted a
    little differently and so each catching the light at its own value.
    That is what shattered glass actually looks like, and it means the
    pane's texture is organised BY the break instead of being a gradient
    laid over it.
  - every crack is a bright ridge (light on the fresh fracture lip) with
    a dark groove immediately down-right of it. A ridge crossing a cell
    horizontally lands as ▀ or ▄, vertically as a hard ░▒▓ step -- the
    orientation flip in SH-LOGO1 falls out of the geometry.
  - the pane FIELD never leaves the blue band. Only the 1px crack
    grooves go dark. The previous attempt ramped the whole field to
    black and the break-hole stopped reading as a hole; that is the one
    mistake this pass is built not to repeat.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duo2_common as D  # noqa: E402

mask = D.load_mask()   # pass 1 already owns the canvas
BREAK = (40.0, 74.0)
BARS = [(0, 0, 5, 100), (75, 0, 5, 100), (0, 26, 80, 4), (20, 0, 3, 100)]


def in_bar(x, y):
    return any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh in BARS)


# --- separate the breach hole from the crack spikes -------------------
# Both are VOID black in the block-in. The hole is the one big connected
# mass around the break centre; everything else black in the pane is a
# crack, and the cracks are what the facets are built from.
hole = D.hole_mask(mask)

crack_px = [(x, y) for y in range(D.PH) for x in range(D.CW)
            if mask[y][x] == D.VOID and not hole[y][x]]

# the block-in's own crack directions, off the break centre -- the facet
# boundaries are the real cracks, not invented ones.
angles = sorted({round(math.atan2(y - BREAK[1], x - BREAK[0]), 2)
                 for x, y in crack_px})
seeds, last = [], -9.0
for a in angles:                       # thin to ONE angle per spike
    if a - last > 0.55:
        seeds.append(a)
        last = a
# three hairlines run UP the pane, continuing the spikes that go up
seeds += [-2.42, -1.98, -1.22]
seeds = sorted(set(round(a, 3) for a in seeds))


def facet_bias(ang):
    """Which angular facet a point falls in, and how that facet is
    tilted. Deterministic off the seed angles, so the value steps land
    exactly on the cracks."""
    i = 0
    for k, a in enumerate(seeds):
        if ang >= a:
            i = k + 1
    return i, ((i * 37) % 11 - 5) / 58.0     # +-0.086, stable per facet


val = [[None] * D.CW for _ in range(D.PH)]
for y in range(D.PH):
    for x in range(D.CW):
        if mask[y][x] != D.PANE:
            continue
        dx, dy = x - BREAK[0], y - BREAK[1]
        ang = math.atan2(dy, dx)
        dist = math.hypot(dx, dy)
        _, bias = facet_bias(ang)
        # top-left lit, and the glass brightens toward the break where
        # the fresh edges catch the source
        # Kept LOW and narrow on purpose. The field is the background;
        # when it was bright the hand stopped being the lightest thing on
        # the canvas and the composition went flat. Most of the pane is
        # ░ or ▒ of 12 over 4 -- blue glass with a sparkle in it, and the
        # brightness is spent where the glass has a reason to be bright.
        v = 0.79 - 0.17 * (x / 79.0) - 0.19 * (y / 99.0) + bias
        v += 0.10 * math.exp(-((dist - 24) / 13.0) ** 2)   # glow at the break
        # two steep reflection bands -- a pane without a reflection in it
        # reads as a blue wall
        for c, wdt in ((24, 7.0), (57, 5.5)):
            v += 0.10 * math.exp(-(((x - y * 0.55) - c) / wdt) ** 2)
        val[y][x] = min(0.90, max(0.50, v))     # never leaves the blue band

# --- contact shadow / contour ----------------------------------------
# Studied against references/study/blocktronics-ra_mindseye.ANS: every
# form in that piece is separated from its neighbour by a hard dark
# contour, and the dither is spent INSIDE the forms. This piece had the
# dither and none of the contour, so the fingers were separated from the
# pane by value alone and the ring and little finger kept dissolving
# into it.
#
# Drawn on the PANE side only -- "do not change" #1 says nothing
# overdraws the fingers -- which makes it a contact shadow as well as a
# contour: the hand is PRESSED on the glass, so it occludes the top-left
# source and drops a tight shadow down-right onto the pane. One cue,
# two jobs, and the silhouette that carries the blind read is untouched.
for y in range(D.PH):
    for x in range(D.CW):
        if val[y][x] is None:
            continue
        hit = None
        for dy in range(-4, 2):
            for dx in range(-4, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < D.CW and 0 <= ny < D.PH) \
                        or mask[ny][nx] != D.HAND:
                    continue
                d = max(abs(dx), abs(dy))
                cast = dx <= 0 and dy <= 0      # hand up-light of here
                if d <= (4 if cast else 1):
                    # the cast side goes near black and falls off over four
                    # pixels; the lit side gets only a one-pixel contour, and
                    # a lighter one -- an even black keyline all the way round
                    # reads as a sticker cut out and laid on the glass
                    v = (0.09 + 0.11 * (d - 1)) if cast else 0.27
                    hit = v if hit is None else min(hit, v)
        if hit is not None:
            val[y][x] = min(val[y][x], hit)

# --- the fracture itself ---------------------------------------------
# bevel: pane touching a crack spike or the hole rim from its up-left
# side takes the bright lip. Same light as everything else.
for y in range(D.PH):
    for x in range(D.CW):
        if val[y][x] is None:
            continue
        for ox, oy, amt in ((1, 0, 0.30), (0, 1, 0.26), (1, 1, 0.20),
                            (-1, 0, -0.22), (0, -1, -0.18)):
            nx, ny = x + ox, y + oy
            if 0 <= nx < D.CW and 0 <= ny < D.PH and mask[ny][nx] == D.VOID:
                val[y][x] = min(0.99, max(0.18, val[y][x] + amt))

# The fracture network. Two families, because that is what a real
# impact leaves: RADIAL cracks running out from the break, and LATERAL
# arcs running between them concentric to it.
#
# Drawn DARK, with the bright lip broken up and intermittent. A crack
# drawn as a continuous bright line reads as a scanline glitch -- the
# first version of this pass did exactly that and the pane looked like a
# corrupted file. A fracture is a dark split with the light catching it
# only here and there, and a dark 1px line against the lit field lands
# on a tier boundary, so the mapping rule renders it as ▀ or ▄ -- the
# half-blocks come out of the drawing, not out of chasing the metric.
def fracture(xi, yi, k):
    if not (0 <= xi < D.CW and 0 <= yi < D.PH) or val[yi][xi] is None:
        return
    val[yi][xi] = 0.02                               # the split itself
    lx, ly = xi - 1, yi - 1                          # lip toward the light
    if k % 3 and 0 <= lx < D.CW and 0 <= ly < D.PH and val[ly][lx] is not None:
        val[ly][lx] = 0.95


RIM = 22.0
for k, a in enumerate(seeds):
    r = RIM
    while r < 150:
        r += 0.5
        # a crack wanders; a perfectly straight radius reads as a drawn
        # ray, not as glass giving way
        aa = a + 0.10 * math.sin(r / 11.0 + k) + 0.04 * math.sin(r / 3.7)
        xi = int(round(BREAK[0] + math.cos(aa) * r))
        yi = int(round(BREAK[1] + math.sin(aa) * r))
        if not (0 <= xi < D.CW and 0 <= yi < D.PH) or in_bar(xi, yi):
            break                                    # dies at the bar
        fracture(xi, yi, int(r * 2))

# lateral arcs, each spanning only two or three radial cracks -- glass
# breaks between the radials, it does not draw a full circle.
for ri, (rad, a0, a1) in enumerate(((31, -3.05, -1.75), (44, -1.30, 0.55),
                                    (38, 1.35, 2.70), (57, -2.85, -2.05))):
    steps = int((a1 - a0) * rad * 2)
    for i in range(steps + 1):
        aa = a0 + (a1 - a0) * i / steps
        rr = rad + 2.2 * math.sin(aa * 3.1 + ri)
        xi = int(round(BREAK[0] + math.cos(aa) * rr))
        yi = int(round(BREAK[1] + math.sin(aa) * rr))
        if not (0 <= xi < D.CW and 0 <= yi < D.PH) or in_bar(xi, yi):
            continue
        fracture(xi, yi, i)

n = D.paint(mask, D.PANE, val, (0, 4, 12))

# --- the void ---------------------------------------------------------
# Not lit -- nothing inside the hole catches the source. It gets depth
# instead: dim green flecks at the rim only, thinning inward, so the
# hole reads as an opening with something behind it rather than a hole
# punched in the file. Interior stays true black and stays the darkest
# thing in the piece.
vval = [[None] * D.CW for _ in range(D.PH)]
for y in range(D.PH):
    for x in range(D.CW):
        if not hole[y][x]:
            continue
        d = min((abs(x - nx) + abs(y - ny)
                 for ny in range(max(0, y - 6), min(D.PH, y + 7))
                 for nx in range(max(0, x - 6), min(D.CW, x + 7))
                 if not hole[ny][nx]), default=9)
        if d <= 4 and (x * 7 + y * 3) % 5 < 2:
            vval[y][x] = 0.34 - 0.06 * d
nv = D.paint(mask, D.VOID, vval, (0, 2, 2))

D.ct.save_ans(D.W, D.SLUG, "scratch/duo2.ans", title=None, add_sig=False)
print("crack spikes:", len(crack_px), "px,", len(seeds), "facet seeds")
print("pane cells:", n, " void cells:", nv)
print(D.ct.metrics(D.W, D.SLUG))
