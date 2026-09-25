"""duo2 shared: load the approved block-in, and the one glyph-mapping
rule every pass in this piece uses.

THE RULE (retrieved, not invented). find_patches_clip('directional
strokes following a cylinder') returned 1994/cnc-0494/HTF-PUBE.ANS,
which shades a lit tube like this, one fg/bg pair the whole way:

    r05  9:░ 10:▒ 11:░        12:▌
    r07  9:▒ 10:▓ 11:▓ 12:░   13:▌
    r08  9:▒ 10:▓ 11:█ 12:▓   13:█
    r09  9:░ 10:▒ 11:▓ 12:█ 13:▒ 14:░ 15:▀

A density ramp ACROSS the width, its peak MIGRATING along the form row
to row, and a half/quarter block at the silhouette. Same in
2003/evoke03/daisy2.ans ('shaded knuckles'): ▒ ▓ █ ▌ climbing across
the form, the run stepping one column per row so the band follows the
contour.

So: light value per PIXEL from the form's real geometry, then per cell

  - the two pixels quantize to different tiers  -> ▀ fg=top bg=bottom
    (a half-block, i.e. the tier boundary drawn at sub-cell resolution;
    these land in a line along the terminator, which is the contour)
  - same tier -> a shade glyph ░▒▓█ of the next tier's colour over this
    one, density = where in the tier the cell sits

Never a flat fill, and never noise: every glyph's density is the
surface value at that point. Boundary cells (the two pixels not both
in the form's block-in mask) are NEVER touched, so the silhouette that
carries the blind read cannot move.
"""
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import canvas_tools as ct  # noqa: E402

W = str(ROOT / "workspace")
SLUG = "duo2"
PANE, VOID, BAR, HAND = 4, 0, 8, 6
PH, CW, CH = 100, 80, 50

# one source, top-left, in front of the pane
LIGHT = (-0.55, -0.45, 0.70)
_m = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _m for c in LIGHT)


def load_blockin(src="scratch/duo2.blockin.ans", save=True):
    """Decode the approved block-in .ans back into a canvas.

    Always the pristine block-in copy, never scratch/duo2.ans:
    the passes write duo2.ans, and re-loading a shaded .ans
    reads its dither glyphs as pixel pairs, so the colour masks
    every pass clips against silently come back empty."""
    raw = (Path(W) / src).read_bytes().decode("cp437", "replace")
    fg, bg, content = 7, 0, []
    for line in [l for l in raw.split("\n") if l != ""]:
        cells = []
        for tok in re.finditer(r"(\x1b\[[0-9;]*m|.)", line):
            m = tok.group(1)
            if m.startswith("\x1b["):
                for c in m[2:-1].split(";"):
                    c = int(c) if c else 0
                    if c == 0:
                        fg, bg = 7, 0
                    elif c == 1:
                        fg |= 8
                    elif 30 <= c <= 37:
                        fg = (c - 30) | (fg & 8)
                    elif 40 <= c <= 47:
                        bg = c - 40
                    elif 90 <= c <= 97:
                        fg = c - 90 + 8
                    elif 100 <= c <= 107:
                        bg = c - 100 + 8
            else:
                cells.append((m, fg, bg))
        content.append(cells)

    def pix(ch, cf, cg):
        if ch == "█":
            return (cf, cf)
        if ch == "▀":
            return (cf, cg)
        if ch == "▄":
            return (cg, cf)
        if ch == " ":
            return (cg, cg)
        return (cf, cg)

    pixels = [[0] * CW for _ in range(PH)]
    for cr, row in enumerate(content[:CH]):
        for col, (ch, cf, cg) in enumerate(row[:CW]):
            t, b = pix(ch, cf, cg)
            pixels[cr * 2][col] = t
            pixels[cr * 2 + 1][col] = b
    if save:
        ct.save_canvas(W, SLUG, {"w": CW, "h_cells": CH, "ph": PH, "bg": 0,
                                 "pixels": pixels, "glyph_override": {}})
    return pixels


def load_mask():
    """The block-in's colour mask WITHOUT resetting the canvas -- passes
    after the first clip against this and must not wipe their
    predecessor's glyph work."""
    return load_blockin(save=False)


def hole_mask(mask):
    """The breach hole, as opposed to the crack spikes -- both are VOID
    black in the block-in, so they have to be told apart by connectivity.
    Taken as the LARGEST connected void mass rather than by flooding from
    the break centre: the forearm covers that centre, so a seeded flood
    there fills nothing and every caller silently gets an empty hole and
    treats the hole's own outline as crack directions."""
    from collections import deque
    seen = [[False] * CW for _ in range(PH)]
    best = []
    for sy in range(PH):
        for sx in range(CW):
            if seen[sy][sx] or mask[sy][sx] != VOID:
                continue
            comp, q = [], deque([(sx, sy)])
            seen[sy][sx] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < CW and 0 <= ny < PH and not seen[ny][nx] \
                            and mask[ny][nx] == VOID:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    out = [[False] * CW for _ in range(PH)]
    for x, y in best:
        out[y][x] = True
    return out


def dot(n):
    return n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]


def clamp01(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def capsule_light(x, y, ax, ay, bx, by, r):
    """(value, t) for a lit tube, or None if the point is off it.
    t is position along the axis, 0 at A -> 1 at B."""
    dx, dy = bx - ax, by - ay
    ln2 = dx * dx + dy * dy or 1.0
    t = clamp01(((x - ax) * dx + (y - ay) * dy) / ln2)
    ox, oy = x - (ax + t * dx), y - (ay + t * dy)
    d = math.hypot(ox, oy) / r
    if d > 1.0:
        return None
    nz = math.sqrt(max(0.0, 1.0 - d * d))
    # /1.10, not /0.92: dividing by the true peak clamps a wide tube's
    # lit flank flat, and a plateau is exactly the flat fill this piece
    # was rejected for.
    return clamp01((dot((ox / r, oy / r, nz)) + 0.10) / 1.10), t


def sphere_light(x, y, cx, cy, r):
    nx, ny = (x - cx) / r, (y - cy) / r
    q = nx * nx + ny * ny
    if q > 1.0:
        return None
    return clamp01(dot((nx, ny, math.sqrt(1.0 - q))))


DENSITY = "░▒▓█"  # ░▒▓█


# 4x4 ordered dither. A tier boundary quantized straight off the value
# is a hard contour line; real work breaks the change over a band, which
# is where half-blocks actually come from -- one pixel of a cell over the
# line and one under it IS a ▀. Applied to the QUANTIZATION only, never
# to the density, so the ramp underneath stays smooth.
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
# 0.08, not 0.20. At 0.20 the whole pane checkerboards between its
# two tiers -- half_block triples and the piece becomes exactly the
# uniform dither STYLE.md warns about. This is sized so only cells
# genuinely within a fifteenth of a tier of the boundary break up,
# i.e. a transition band, not a field.
DITHER = 0.05


def cell_from_values(vt, vb, tiers, x=0, yt=0, dither=DITHER):
    """The rule in the module docstring. vt/vb are the top and bottom
    pixel's light values; tiers is the 3-colour ramp darkest first."""
    jt = dither * (BAYER[yt % 4][x % 4] / 15.0 - 0.5)
    jb = dither * (BAYER[(yt + 1) % 4][x % 4] / 15.0 - 0.5)
    qt, qb = min(2, max(0, int((vt + jt) * 3))), min(2, max(0, int((vb + jb) * 3)))
    if qt != qb:
        return ("▀", tiers[qt], tiers[qb])          # ▀ tier boundary
    v = (vt + vb) / 2.0
    # Solid cores at BOTH ends of the ramp. Measured against
    # references/study: the archive runs shade-of-ink 0-41%, and a
    # mapping where every interior cell is a shade glyph came out at
    # 69% -- busy everywhere, which is flat-everywhere wearing a
    # different costume. Real work is solid masses with dithered
    # TRANSITIONS between them, so the ramp gets a solid top and a
    # solid bottom and the dither is spent on the turn.
    if v >= 0.84:
        return ("\u2588", tiers[2], tiers[1])             # solid highlight
    if v <= 0.05:
        return ("\u2588", tiers[0], tiers[1])             # solid shadow
    # 0.05, not 0.11: the hand's shadow tier IS the pane colour, so a
    # solid-shadow cell on a finger's dark flank is a pane-coloured cell
    # inside the figure and the finger dissolves into the background.
    # Only the crack grooves go this dark, and a crack SHOULD be a solid
    # black line.
    p = 0 if v < 0.5 else 1                               # which pair band
    s = (v - 0.5 * p) / 0.5
    # capped at ▓ deliberately: letting a band top out at █ puts a solid
    # plate of the upper colour right at mid-value, which is a flat fill
    # wearing a glyph. ▓ hands off to the next band's ░ instead.
    return (DENSITY[min(2, int(s * 3))], tiers[p + 1], tiers[p])


def paint(mask, color, values, tiers, dither=DITHER):
    """Glyph every cell whose BOTH pixels are `color` in the block-in
    mask and carry a light value, via canvas_stamp, one call per
    contiguous run. Mixed cells (the silhouette) are left alone, so no
    pass in this piece can move an edge the blind read depends on."""
    n = 0
    for row in range(CH):
        yt, yb = row * 2, row * 2 + 1
        run, start = [], 0
        for col in range(CW + 1):
            ok = (col < CW and mask[yt][col] == color and mask[yb][col] == color
                  and values[yt][col] is not None and values[yb][col] is not None)
            if ok:
                if not run:
                    start = col
                run.append(cell_from_values(values[yt][col], values[yb][col],
                                            tiers, col, yt, dither))
            elif run:
                ct.stamp(W, SLUG, start, row,
                         [[ord(c[0]) for c in run]],
                         [[c[1] for c in run]], [[c[2] for c in run]])
                n += len(run)
                run = []
    return n


def demo():
    """The mapping rule is the whole piece; check it can't go flat."""
    tiers = (4, 6, 14)
    assert cell_from_values(0.1, 0.9, tiers)[0] == "▀"   # straddles -> ▀
    band = {cell_from_values(0.65, 0.65, tiers, x, y)[0]
            for x in range(4) for y in range(4)}
    assert "▀" in band and len(band) > 1, band   # tier edge dithers, not a line
    far = {cell_from_values(0.50, 0.50, tiers, x, y)[0]
           for x in range(4) for y in range(4)}
    assert far == {"░"}, far          # ...and only AT the edge, not everywhere
    assert cell_from_values(0.96, 0.96, tiers) == ("█", 14, 6)
    assert cell_from_values(0.02, 0.02, tiers) == ("█", 4, 6)
    assert cell_from_values(0.45, 0.45, tiers)[0] != "█"  # no mid plate
    assert cell_from_values(0.13, 0.13, tiers) == ("░", 6, 4)
    # and the ramp climbs monotonically end to end: █ ░ ▒ ▓ ░ ▒ ▓ █
    seq = [cell_from_values(v / 20, v / 20, tiers)[0] for v in range(21)]
    assert seq[0] == "█" and seq[-1] == "█" and len(set(seq)) >= 4, seq
    for a in range(11):                    # no value anywhere is bg-carried
        ch, fg, bg = cell_from_values(a / 10, a / 10, tiers)
        assert ch != " " and fg != bg, (a, ch, fg, bg)
    print("duo2_common ok")


if __name__ == "__main__":
    demo()
