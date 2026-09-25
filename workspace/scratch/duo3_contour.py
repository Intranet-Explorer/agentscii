"""duo3 session 5: the head gets a width profile.

My own NEXT from session 4, and the review's "the silhouette is
straight-edged on both sides", are the same sentence. The head was
exactly the same width from row 7 to row 15 -- a straight nine-row wall
-- because the block-in is a SPHERE, and the flank of a circle of radius
14 is vertical to within half a cell over eight rows either side of its
equator. The wall is not a rendering failure. It is the block-in showing
through, and it was always going to, because a skull is not a ball.

Placement first, quality second, in that order, because quality work on
a misplaced edge is wasted.

PLACEMENT. Where the edge IS, per row, to half a cell.

    crown        narrow, falling away fast over the top
    forehead     widening
    parietal     24.5 -- the cranium, near its full width
    TEMPLE       25.5 -- the temporal fossa, a real PINCH back inward.
                 One cell, but it is the cell that says skull rather
                 than egg: the only place on a head where the outline
                 reverses direction on the way down.
    ZYGOMATIC    22.5 at rows 16-17 -- the WIDEST POINT OF THE FACE,
                 wider than the cranium above it.
    under it     falls away; the cheek hollow
    MANDIBLE     the angle of the jaw at x26, and from there the lower
                 border runs down and forward to the chin as a curve,
                 authored per column at half-row resolution. The jaw
                 TERMINATES: lit bone above the border, black below it,
                 nothing in between.

QUALITY, second. Every cell of the vertical contour is one of two
glyphs and both are the same value, 0.16: ▐ where the edge lands
mid-cell, ▒ where it lands on the boundary between two columns. Same
ink, one landed and one scattered. Under the jaw the edge is horizontal
rather than vertical, so there it is ▀, landing between two ROWS.

The rim is spelled fg 1 the whole way down, against the piece's law that
hue comes from the heat field alone. Session 3 wrote the exemption --
"the silhouette rim is an edge, not surface; its colour is doing edge
work" -- and this is the case it was written for. heat() is a distance in
the picture plane, and by that measure the rim at the temple came out
one band warmer than the rim at the cheekbone, so the contour changed
hue halfway down and stopped reading as one line. The far side of a head
cannot be hotter than its own cheek: the head is in the way.

The rim is a touch BRIGHTER than the cells just inside it. Not a second
light sneaking in -- the entire right half of this picture is on fire and
the air around the head has embers in it, so a surface turned fully away
still catches the field. What sits just inside is the core shadow, and a
core shadow inboard of a lit edge is how a silhouette reads as a turning
form rather than a cut-out.

THE FLANK. The other half of why the wall was invisible: the old edge
faded out through five cells of rung-0 ·, two percent ink, so there was
no last cell at all. Nothing on the flank is allowed below rung 2 now.
Rung 1 is 0.06 and the nearest thing the ladder has to it is · at 0.02 --
which is how the fade got written in the first place, honestly, one rung
at a time.

What varies row to row is not the rim's value -- a contour that changes
brightness stops being a contour -- but how the value behaves inward,
which is what curvature is. The zygomatic arch is a narrow ridge of bone
under thin skin: it crests two cells in and falls off BEHIND itself into
the cheek before the lit front picks up again, and that little dip is
the whole reason a cheekbone reads as a cheekbone. The temple and the
cheek hollow are flat and recessed and just stay dark.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

RIM_FG = 1          # see the exemption in the docstring

# Where the edge is, rows 3..21. Rows 22-24 are the mandible's business.
PROFILE = {
    # Row 3 has no rim of its own: up there the edge is the CROWN, which
    # is horizontal, and planes2 already landed it as a dome at three
    # heights. A vertical rim cell on top of that puts full-height ink
    # beside a half-height dome, and the skull grows a corner.
    3: None,
    4: 30.5, 5: 28.5, 6: 27.0, 7: 25.5, 8: 25.0,
    9: 24.5, 10: 24.5,                 # parietal
    11: 25.5, 12: 25.5,                # TEMPLE -- the pinch
    13: 24.5, 14: 23.5, 15: 23.0,      # zygomatic arch coming forward
    16: 22.5, 17: 22.5,                # CHEEKBONE -- widest point
    18: 23.5, 19: 24.5,                # falling away under the arch
    20: 25.0, 21: 25.5,                # the cheek hollow, then the masseter
}

# The mandible's lower border: edge ROW per column, half-row resolution.
# x36-42 are planes2's and stay its business; this is the angle of the
# jaw forward to where that pass picks up.
MANDIBLE = {
    26: 22.5, 27: 22.5,                # THE ANGLE OF THE JAW -- the corner
    28: 23.0, 29: 23.5, 30: 23.5,
    31: 24.0, 32: 24.5, 33: 24.5, 34: 24.5, 35: 24.5,
}

# Rungs inward from the first whole cell inside the rim; '.' leaves a
# cell alone. Each row ends where session 3's model already has real
# values to meet.
FLANK = {
    3: '',
    4: '', 5: '',
    6: '.22', 7: '223', 8: '22',
    9: '235', 10: '235',               # parietal: firm bone, climbs
    11: '23', 12: '23',                # TEMPLE HOLLOW: stays dark
    13: '222',
    14: '2222',
    15: '2332',
    16: '24433', 17: '24433',          # CHEEKBONE: crest, then the dip
    18: '2332',
    19: '222', 20: '222',              # CHEEK HOLLOW: flattest on the head
    21: '23',
}

# The masseter, filling the space between the arch and the jaw angle --
# a rounded mass, so it crests in its middle rather than ramping. Only
# ever written into cells that are empty: rows 22-23 also carry the
# mouth's crease and the chin's shadow, which are somebody else's pass.
MASSETER = {(28, 22): 3, (29, 22): 4, (30, 22): 4, (31, 22): 3,
            (32, 22): 4, (31, 23): 4, (32, 23): 3}

# The lower-left cheek came out of the flank pass as sixteen cells of
# ░ 1,0 -- the same thing the neck was, at a quarter the size, and put
# there by me this session while taking it out of somewhere else. A
# hollow in deep shade IS flat, so the fix is not to dither it. It is
# that a hollow has to be bounded by the two forms it sits between, and
# both of those boundaries land mid-cell:
#   row 18  the ZYGOMATIC ARCH's underside -- the darkest line on this
#           half of the face, because it is what the cheekbone shades
#   row 21  the MASSETER's upper edge, coming the other way
# Between them three rows of nothing, which is a statement rather than a
# leftover. The last cell is a rung-0 speck the old fade left behind in
# the middle of the hollow.
BOUNDS = [(24, 18, '▀', 1), (25, 18, '▀', 1),
          (26, 18, '▀', 3), (27, 18, '▀', 3),
          (26, 21, '▄', 1), (27, 21, '▄', 1), (28, 21, '▄', 1),
          (28, 19, '░', 3)]


def build():
    cells, blank = [], []
    for y in range(3, 22):
        e = PROFILE[y]
        x0 = 33 if e is None else int(e)
        blank += [(x, y) for x in range(20, x0)]
        if e is not None:
            cells.append((x0, y, '▐' if e % 1 else '▒', RIM_FG, 0))
        for i, d in enumerate(FLANK[y]):
            if d != '.':
                x = x0 + 1 + i
                cells.append((x, y, *t.spell(t.RUNG[int(d)], x, y)))
    cells += [(x, y, g, fg, 0) for x, y, g, fg in BOUNDS]

    for x, e in MANDIBLE.items():
        y = int(e)
        if e % 1:
            cells.append((x, y, '▀', 3, 0))       # lit bone, black below
        else:
            blank.append((x, y))
        blank += [(x, yy) for yy in range(y + 1, 25)]
    lo = min(MANDIBLE)
    for y in (22, 23, 24):
        blank += [(x, y) for x in range(20, lo)]
    return cells, blank


def apply():
    cells, blank = build()
    for (x, y), rung in MASSETER.items():
        ch, _, bg = t.grid(x, y, 1, 1)[0][0]
        if ch == ' ' and bg == 0:
            cells.append((x, y, *t.spell(t.RUNG[rung], x, y)))
    return t.paint(cells + [(x, y, ' ', 0, 0) for x, y in blank]), cells


if __name__ == '__main__':
    n, cells = apply()
    landed = sum(1 for _, _, g, _, _ in cells if g in '▀▄▌▐')
    widths = [v for v in PROFILE.values() if v is not None]
    assert PROFILE[16] == min(widths), 'the cheekbone must be the widest point'
    assert PROFILE[11] > PROFILE[9], 'the temple must pinch back in'
    assert len(set(widths)) > 8, 'a profile with few distinct widths is a wall'
    print('cells', n, '/', landed, 'landed mid-cell; widest', min(widths))
