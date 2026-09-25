"""duo3 working helpers. Not a drawing library -- a view + a batch writer.

ct.stamp() does one load/save of the whole canvas JSON per call, which is
fine for a patch and absurd for 2,000 hand-placed cells. paint() takes a
list of cells and does one load/save. grid() is the other half of the
loop: read what is already under a region so the next cell's glyph can be
chosen from the value that is actually there.
"""
import math
import base64
import sys

sys.path.insert(0, '/Users/octo/agentscii')
import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
SLUG = 'duo3'
SHOT = W + '/scratch/duo3_look.png'


def paint(cells, slug=SLUG):
    """cells: iterable of (x, y, ch, fg, bg) in CELL space. One save."""
    data = ct.load_canvas(W, slug)
    go = data['glyph_override']
    cw, ch_ = data['w'], data['h_cells']
    n = 0
    for x, y, g, fg, bg in cells:
        if 0 <= x < cw and 0 <= y < ch_:
            go[f'{y},{x}'] = [g, int(fg), int(bg)]
            n += 1
    ct.save_canvas(W, slug, data)
    return n


def grid(x, y, w, h, slug=SLUG):
    """Cells as they currently render: [[(ch, fg, bg), ...], ...]."""
    rows = ct.render_canvas_cells(ct.load_canvas(W, slug))
    return [r[x:x + w] for r in rows[y:y + h]]


def px(x, y, w, h, slug=SLUG):
    """Raw pixel colours under a CELL region: [[top, bot], ...] per cell."""
    d = ct.load_canvas(W, slug)
    p = d['pixels']
    return [[(p[2 * (y + r)][x + c], p[2 * (y + r) + 1][x + c])
             for c in range(w)] for r in range(h)]


def _write(b64, path):
    open(path, 'wb').write(base64.b64decode(b64))
    return path


def look(x=0, y=0, w=None, h=None, scale=6, path=SHOT, slug=SLUG):
    d = ct.load_canvas(W, slug)
    w = d['w'] if w is None else w
    h = d['h_cells'] if h is None else h
    b64, dump = ct.crop(W, slug, x, y, w, h, scale=scale)
    return _write(b64, path), dump


def check(slug=SLUG):
    g, c, dens = ct.self_check(W, slug)
    return (_write(g, W + '/scratch/duo3_glyphs.png'),
            _write(c, W + '/scratch/duo3_colour.png'), dens)


def block(x0, y0, G, F, B, slug=SLUG):
    """Hand-authored cell block: three aligned layers, one char per cell.

    G glyph ('.' = leave this cell alone), F fg hex, B bg hex. Authoring
    a region this way keeps every cell a deliberate choice that is still
    readable as a picture in the source -- which is the whole point of
    per-cell work over a region rule.
    """
    cells = []
    for r, (g, f, b) in enumerate(zip(G, F, B)):
        assert len(g) == len(f) == len(b), f'row {r} layers misaligned: {len(g)},{len(f)},{len(b)}'
        for c, ch in enumerate(g):
            if ch != '.':
                cells.append((x0 + c, y0 + r, ch, int(f[c], 16), int(b[c], 16)))
    return paint(cells, slug)


# The piece's value ramp, dark -> light, written one char per cell.
#
# Sixteen steps over four hue pairs. The first version jumped brown (3)
# straight to bright yellow (11), and every lit edge came out as a
# glowing line -- there was no rung between flesh and fire, so anything
# lit read as emitting. Bright red (9) is that rung, and it is the right
# hue for skin lit by an ember besides. Magenta stays reserved for the
# ambient on surfaces turned fully away from the light.
#
# No step is a flat background fill: each is a real glyph over a second
# colour, so value is carried by ink.
RAMP = {
    '0': (' ', 0, 0),
    'm': ('░', 5, 0), 'M': ('▒', 5, 0), 'N': ('▓', 5, 0),
    '1': ('░', 1, 0), '2': ('▒', 1, 0), '3': ('▓', 1, 0),
    '4': ('░', 3, 1), '5': ('▒', 3, 1), '6': ('▓', 3, 1),
    '7': ('█', 3, 1),
    '8': ('░', 9, 3), '9': ('▒', 9, 3), 'A': ('▓', 9, 3),
    'B': ('█', 9, 3),
    'C': ('░', 11, 9), 'D': ('▒', 11, 9), 'E': ('▓', 11, 9),
    'F': ('█', 11, 9),
}


# ---------------------------------------------------------------------
# THE TWO FIELDS (moved here in session 3 from duo3_reencode, because a
# second pass now needs them: a face's value has to be AUTHORED, not
# only respelled).
#
#   GLYPH DENSITY -> VALUE. How the surface is turned relative to the
#   light. Sixteen colours, intermediate brightness faked with density:
#   the actual craft of the medium.
#
#   COLOUR PAIR   -> HEAT.  How close that patch is to the ember. A
#   cheekbone facing away from the fire and a jaw facing into it can be
#   the same brightness and are not the same colour.
#
# The band is chosen from heat ALONE. The first version picked the first
# band that could express the cell's value, which let hue read value
# back out through the side door and showed up as stripes of alternating
# hue down the shadow side.
LUM = {0: 0.00, 1: 0.32, 3: 0.48, 5: 0.30, 7: 0.66, 8: 0.33,
       9: 0.62, 11: 0.88, 13: 0.60, 15: 0.95}
COVER = {'\u00b7': 0.04, '\u2591': 0.25, '\u2592': 0.50,
         '\u2593': 0.75, '\u2588': 1.00, ' ': 0.0,
         # The four half blocks are half a cell of ink, same as the
         # medium shade -- the difference is that the ink is LANDED on
         # one side of the cell instead of scattered through it, which
         # is how an edge falls BETWEEN two cells rather than on the
         # line between them.
         '\u2580': 0.50, '\u2584': 0.50, '\u258c': 0.50, '\u2590': 0.50}
GLYPHS = '\u00b7\u2591\u2592\u2593\u2588'
# Session 4, the review: "the hue breaks the palette: violet against an
# otherwise red/orange/yellow fire scheme. Embers don't go purple."
# There was an 'ambient': (5, [0]) band here for surfaces turned fully
# away from the fire, and magenta was the wrong answer to a real
# question. A surface facing away from the only light in a picture does
# not change hue; it runs out of light. 'cool' already spells that in
# the right hue and the far side of the head simply clamps to it now.
BANDS = {
    'cool': (1, [0]),
    'dark': (3, [0, 1]),
    'mid': (9, [0, 1, 3]),
    'hot': (11, [0, 1, 9]),
}
BANDS_BY_HEAT = [(0.90, 'hot'), (0.72, 'mid'), (0.30, 'dark'),
                 (0.00, 'cool')]
EMBER_X, EMBER_Y = 47.0, 13.0


def value(glyph, fg, bg):
    f = COVER[glyph]
    return f * LUM[fg] + (1 - f) * LUM[bg]


def _allowed(glyph, bg):
    # Over a non-black ground a \u00b7 is four percent ink and ninety-six
    # percent background -- a flat fill wearing a speck. Sparse glyphs
    # earn their place against black; over a lit ground a cell has to be
    # at least half ink or it is not spelling anything.
    return bg == 0 or COVER[glyph] >= 0.5


STEPS = {name: sorted(((g, bg, value(g, fg, bg)) for g in GLYPHS
                       for bg in bgs if _allowed(g, bg)), key=lambda s: s[2])
         for name, (fg, bgs) in BANDS.items()}


def heat(x, y):
    import math
    d = math.hypot(x - EMBER_X, 2 * (y - EMBER_Y))   # cells are 2x tall
    return max(0.0, min(1.0, 1.0 - d / 34.0))


def spell(v, x, y):
    """A value at a place -> (glyph, fg, bg). Hue from heat, ink from value."""
    band = next(n for thr, n in BANDS_BY_HEAT if heat(x, y) >= thr)
    glyph, bg, _ = min(STEPS[band], key=lambda s: abs(s[2] - v))
    return glyph, BANDS[band][0], bg


# Ten rungs, dark to light, for writing a value field by hand. The top
# rung is 0.58 and not 0.88: nothing on the intact half of this head is
# as bright as the fire coming out of the other half, and a ramp that
# can reach the fire will be used to reach it.
RUNG = [0.02, 0.06, 0.11, 0.17, 0.23, 0.29, 0.35, 0.42, 0.50, 0.58]


def ink(x0, y0, rows, width=None):
    """Hand-written value rows ('0'-'9', '.' = leave alone) -> cells."""
    out = []
    for r, row in enumerate(rows):
        assert width is None or len(row) == width, (y0 + r, len(row))
        for c, d in enumerate(row):
            if d != '.':
                x, y = x0 + c, y0 + r
                out.append((x, y, *spell(RUNG[int(d)], x, y)))
    return out


# THE FRONT. One column per row where intact skin stops.
#
# Session 3 made it a stated edge instead of a function of x, which is
# the difference between a gradient and a structure. Session 4 said what
# was still wrong with it and did not fix it: the LEAN alone travels
# three cells over the whole height of the head, a straighter line than
# the silhouette I spent session 5 calling a wall. And it is not an
# abstract edge -- duo3_model draws a LIP at front(y) in every row, two
# rungs above the surface behind it, so a front that does not move is a
# bright vertical bar three cells wide down the middle of the face. That
# bar is the first thing you see in the render. It was the ruler line.
#
# Session 6: PROMINENCE drives it, the way it already drives the plates,
# the gaps, the heat and the reach.
#
# Which way it drives it is the whole content of the fix, and the answer
# is not "the fire eats what is closest to it". Fire goes through what is
# THIN. The brow ridge and the zygomatic arch are the two buttresses of
# the facial skeleton -- the thickest bone in the face, which is exactly
# why they are what is left of a skull -- so intact surface SURVIVES
# further into the burn there and the front bulges out to meet it. The
# orbital plate behind the socket is a wafer and the temporal fossa is
# the thinnest bone on the whole skull, and the front notches back where
# they gave way. The socket is a hole in this picture for the same
# reason, which is a story session 3 already told; this makes the rest of
# the edge agree with it.
#
# So the brow ridge at row 10 stands at x49 with the socket at x42 three
# rows under it, and the arch at rows 16-17 overhangs the burnt cheek
# hollow the same way. Those two overhangs are the drawing: a face coming
# apart along its own structure, instead of a region fading out.
FRONT_LEAN = {
    3: 43, 4: 43, 5: 43, 6: 44, 7: 44, 8: 44, 9: 45, 10: 45, 11: 45,
    12: 44, 13: 43, 14: 44, 15: 45, 16: 45, 17: 45, 18: 46, 19: 46,
    20: 46, 21: 46, 22: 45, 23: 44, 24: 43,
}


def front(y):
    # No gain below row 21. PROMINENCE there ("the JAW LINE and the
    # chin's corner") is how far the mandible projects toward the VIEWER,
    # and the front is a width: the head's own silhouette has already run
    # in to the chin by row 22, so a bulge there would hang a lip and a
    # seam in open air beside the jaw with black in between.
    g = (prom(y) - 4.5) * 0.85 if y <= 21 else 0.0
    return int(round(FRONT_LEAN.get(y, 44) + g))


# The ramp written out in order, dark to light. Session 3 needs to step
# a cell one rung up or down without knowing which rung it is on.
RAMP_ORDER = '0mMN1234567' + '89AB' + 'CDEF'


def levels(x0, y0, rows, width=None):
    """Value-ramp rows -> cells. '.' leaves a cell alone."""
    out = []
    for r, row in enumerate(rows):
        assert width is None or len(row) == width, (r, len(row))
        for c, lv in enumerate(row):
            if lv != '.':
                ch, fg, bg = RAMP[lv]
                out.append((x0 + c, y0 + r, ch, fg, bg))
    return out


# PROMINENCE (session 4). How far the flesh stood FORWARD at the burning
# edge, row by row. The reviewer on the burning side: "Thirteen rows,
# same ramp, no vertical variation. Charitably it's the head dissolving
# into embers -- but a dissolve needs form to dissolve FROM, and this is
# a gradient applied uniformly per row."
#
# That is right, and FRONT was not enough on its own. FRONT says where
# the skin stops; it says nothing about what KIND of skin stopped there,
# and it only moves three cells over the whole height of the head, so a
# rule written in terms of it alone comes out the same in every row.
# This is the missing term. A brow ridge is bone standing proud of the
# fire and it comes off in big hot chips that carry a long way; a temple
# hollow and an eye socket have less material, stand further back, and
# the burn went through them first, so they shed small and thin and the
# field falls short there.
#
# Nothing here is a number chosen to make a texture. Each one is a
# statement about the head that duo3_model already draws on the intact
# side, read across to the side that is coming apart.
PROMINENCE = {
    # Session 6. These six were 4,5,5,5,4,3 -- near-flat, on the
    # reasoning that a forehead is a smooth plane. It is, and that was
    # still the wrong reading, because PROMINENCE is not smoothness: it
    # is how far the flesh stood forward AT THE BURNING EDGE, and the
    # burning edge runs up the side of the forehead, not across its
    # middle. Mirror planes2's own FRONTAL EMINENCE -- which it draws at
    # x31-33, rows 5-7 -- about the centre line at x38 and it lands at
    # x43-45, which is exactly where the front is. So the bump is ON the
    # seam and the front has to ride over it.
    3: 3, 4: 4,                # crown, curving away over the top
    5: 6, 6: 7,                # the FRONTAL EMINENCE, square on the seam
    7: 5, 8: 2,                # the forehead's lateral edge turning back
    9: 8, 10: 9,               # the BROW RIDGE: the most proud bone up here
    11: 3, 12: 2, 13: 2,       # the SOCKET -- a hole. The front notches
    14: 3, 15: 4,              # inward at 12-14 for the same reason.
    16: 8, 17: 9,              # the CHEEKBONE: widest plane on the face
    18: 4, 19: 3,              # the hollow under it
    20: 5, 21: 6, 22: 5,       # the barrel of the mouth and jaw
    23: 7, 24: 6,              # the JAW LINE and the chin's corner
}


def prom(y):
    return PROMINENCE.get(y, 4)


def _silhouette(y):
    """Right edge of the block-in's head mass, in cells, for this row."""
    best = 0.0
    for py in (2 * y, 2 * y + 1):
        for cx, cy, r in ((38, 20, 14), (44, 30, 8), (38, 34, 6), (38, 42, 6)):
            d = r * r - (py - cy) ** 2
            if d > 0:
                best = max(best, cx + math.sqrt(d))
    return best


def reach(y):
    """Last column this row's shed material gets to: the block-in's
    silhouette, pushed out or pulled in by how proud the form was. Lives
    here rather than in duo3_right2 because duo3_bg has to agree with it
    -- the background may not glow inside the dissolve, or the gaps stop
    being gaps and become a slightly darker lavender, which is the exact
    thing that made session 2's version have no readable edge.
    """
    return int(max(_silhouette(y), front(y) + 4) + round((prom(y) - 4.5) * 1.6))
