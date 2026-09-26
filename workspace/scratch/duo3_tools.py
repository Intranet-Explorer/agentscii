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


# THE FRONT (session 3). One column per row where intact skin stops.
#
# Session 2's note said the dissolve was a gradient of striation because
# the gap pattern was a function of x: more zeros the further right, in
# every row, monotonically. Density that tracks x is a rule. Density that
# tracks distance from a stated edge is structure. This is the stated
# edge, and everything on the burning side is measured from it now.
#
# It leans out and down -- 43 at the crown, 46 at the jaw -- because the
# burn started at the temple and is working down across the face. The
# notch at rows 12-14 is the socket: the front broke inward there first,
# which is why there is a hole in that place and not in any other.
#
# SESSION 6. That version travelled three cells over the whole height of
# the head and the reviewer read it, correctly, as "a hard vertical seam
# through the face, perfectly straight, full-height, a red pillar.
# Nothing in a face does that." It is the same defect session 5 took out
# of the left silhouette, and it has the same cause: an edge whose
# position was written as a LEAN rather than cut from a skull.
#
# PROMINENCE already drove the plates, the gaps, the heat and the reach
# on this side. It drives the front now too, and the direction is the
# part that carries the meaning: FIRE GOES THROUGH WHAT IS THIN. The brow
# ridge and the zygomatic arch are the two buttresses of the facial
# skeleton -- the heaviest bone in the face, which is exactly why they
# are what is left of a burnt skull -- so intact surface survives
# FURTHEST FORWARD at them. The temple fossa, the orbit and the cheek
# hollow are a shell of bone over air, so the burn is furthest BACK
# there.
#
# Authored per row rather than computed from prom(), the way PROFILE is
# on the left: prominence is the reason, the table is the drawing.
# _check() holds the two together so the reason cannot quietly stop
# applying while the numbers stay.
FRONT = {
    3: 43, 4: 44, 5: 44, 6: 44,        # crown and forehead, the mild part
    7: 43, 8: 41,                      # TEMPLE FOSSA -- where it started
    9: 46, 10: 49,                     # the BROW RIDGE, standing proud
    11: 45, 12: 41, 13: 40, 14: 42,    # the ORBIT -- eaten through first
    15: 45,
    16: 48, 17: 50,                    # the ZYGOMATIC ARCH, furthest out
    18: 45, 19: 42,                    # the hollow under it
    20: 45, 21: 47, 22: 46,            # the barrel of the mouth
    23: 48, 24: 46,                    # the JAW LINE and the chin's corner
}


def front(y):
    return FRONT.get(y, 44)


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
    3: 4, 4: 5, 5: 5,          # crown, curving away over the top
    6: 5, 7: 4, 8: 3,          # forehead falling into the TEMPLE HOLLOW
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


# =====================================================================
# SESSION 7. THE FAR SIDE.
#
# FRONT, PROMINENCE and reach() above describe a head being eaten by
# fire, and four attempts across three sessions failed to make that edge
# read. The diagnosis, written in METHOD.md and correct: a dissolve is
# defined by what ISN'T there, so there is nothing behind the edge to
# decide about, and every attempt collapsed into a function evaluated
# over a region. They are kept because the LEFT half of the head is
# still measured from them, and because reach() is how the old
# background knew where not to glow.
#
# The fire is now a LIGHT and not a consumer. It sits in front of the
# head, low and to the right, close enough that its falloff is steep.
# The right of the picture is the same skull turned away from it.
#
#   FAR   the far silhouette, per row. Cut from a skull: the parietal
#         eminence bulges at 9-10, the temporal fossa PINCHES the
#         cranium in at 11-13, the zygomatic arch is the widest point of
#         the whole head at 16-17, and the jaw runs back to its angle at
#         22 before sweeping forward to the chin. The left contour
#         travels eleven columns; this one travels eight, because the
#         head is turned a few degrees away and the far side is
#         foreshortened.
#
#   TERM  the terminator: the last column the fire reaches directly.
#         Not a lean and not a gradient -- the brow ridge and the
#         zygomatic arch carry light FURTHEST out because they stand
#         proudest, and the socket and the hollow under the arch are in
#         the shadow their own rims cast, which is why TERM notches in
#         at 11-14 and 18-21 and bulges at 9-10 and 15-17. Same two
#         buttresses PROMINENCE names; the light agrees with the bone.
#
#   RIM   the four cells where the zygomatic arch's crest has turned far
#         enough back that it sees the fire AGAIN. This is the only
#         place on the dark side that does. It is the mark that proves
#         the head has a far side rather than stopping at the light.
FAR = {
    3: 45, 4: 47, 5: 48, 6: 49,        # the crown going over and back
    7: 50, 8: 50,
    9: 51, 10: 51,                     # PARIETAL EMINENCE, widest cranium
    11: 50, 12: 50, 13: 50,            # the temporal fossa pinches in
    14: 51, 15: 52,
    16: 53, 17: 53,                    # ZYGOMATIC ARCH, widest of the head
    18: 51, 19: 51,                    # the hollow under it
    20: 50, 21: 50,
    22: 49,                            # the ANGLE OF THE JAW
    23: 47, 24: 45,                    # the jaw sweeping to the chin
    25: 47, 26: 47,                    # the neck
}
TERM = {
    3: 43, 4: 44, 5: 45, 6: 45,        # the forehead's last lit column
    7: 44, 8: 44,
    9: 45, 10: 44,                     # the BROW RIDGE carries it furthest
    11: 43, 12: 41, 13: 41,            # into the shadow the brow casts
    14: 42, 15: 43, 16: 43, 17: 43,    # the cheek; the arch is RIM, below
    18: 43, 19: 43, 20: 42, 21: 43,
    22: 43, 23: 43, 24: 42,
    25: 40, 26: 40,                    # the neck is wholly under the jaw
}
RIM = {(50, 16), (51, 16), (50, 17), (51, 17)}


def far(y):
    return FAR.get(y, -1)


# What reaches the dark side is BOUNCE off the lit half of the same
# head, which is a few cells away, so it falls with distance from the
# terminator. One rung per cell past it. The three things this ladder
# has to be true of, all asserted in duo3_shadow._check():
#
#   d = 1  must NOT land in 'mid'. A hot band one cell wide running the
#          height of the head is a bright contour line drawn along the
#          terminator, which is the defect, not the fix.
#   d<= 3  must stay in 'dark'. This is the quiet range the shadow is
#          made of -- brown over black, warm because the only light in
#          the picture is warm.
#   d>= 4  must fall to 'cool'. The temple and the deep socket are the
#          furthest any surface here gets from lit bone, and they are
#          the only places that run out of bounce.
BOUNCE = [1.0, 0.74, 0.60, 0.46, 0.32, 0.25]
# Behind the head is not empty air, it is SMOKE off the same fire, and
# smoke is a medium dense enough to return real light -- which is why
# it can be the ground the jaw is read against. The first version of
# this pass treated it as thin air at 0.45, and the whole lower right
# came back as one flat field of dark-red dither with the jaw somewhere
# inside it and no findable edge anywhere.
SMOKE = 0.8
# Air is a MEDIUM, not a surface. It is thin, so it sends back a
# fraction of what a surface in the same place would -- which is why
# the first version of this pass came back with bright red bars of
# empty space lying across the dark side of the head: sees() was
# handing open air the same view of the fire a cheekbone gets.


def sees(x, y):
    """How much of the fire this cell sends back.

    heat() is distance falloff and nothing else, which is only the whole
    story where nothing is in the way. On the far side of a head the
    head itself is in the way, so heat there is genuinely low despite
    the short distance -- this is the missing term, not a second value
    channel. Hue still comes from heat alone; heat is now correct.
    """
    if x > far(y):
        return SMOKE
    if (x, y) in RIM:
        return 1.0                      # the crest, turned back into it
    d = x - TERM.get(y, 44)
    return BOUNCE[min(d, len(BOUNCE) - 1)] if d > 0 else 1.0


def lit_heat(x, y):
    return heat(x, y) * sees(x, y)


def spell_lit(v, x, y):
    """spell() with the occlusion term. Value -> ink, heat -> hue."""
    band = next(n for thr, n in BANDS_BY_HEAT if lit_heat(x, y) >= thr)
    glyph, bg, _ = min(STEPS[band], key=lambda s: abs(s[2] - v))
    return glyph, BANDS[band][0], bg


def land_lit(v, x, y, glyph):
    """spell_lit() inverted: the glyph is already decided by where the
    edge falls, so pick the colour pair in that cell's band closest to
    the value. Every half-block on the far side goes through this.
    """
    band = next(n for thr, n in BANDS_BY_HEAT if lit_heat(x, y) >= thr)
    fg, bgs = BANDS[band]
    bg = min((b for b in bgs if _allowed(glyph, b)),
             key=lambda b: abs(value(glyph, fg, b) - v))
    return glyph, fg, bg
