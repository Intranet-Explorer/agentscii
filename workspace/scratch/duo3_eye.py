"""duo3 session 6: the eye on the intact side, to pair with the orbit.

The review, three times now in different words: "I cannot find eyes, nose,
or mouth"; "rows 10-11 have paired marks at cols 32-34 and 45-47, which
is presumably a brow/eye pair, but at render scale they read as two light
horizontal bars"; "the face interior is illegible construction."

This session rebuilt the burning side's orbit as a hole with four lit
walls, and that one change makes the left half's failure louder rather
than quieter -- there is now an unmistakable eye socket on one side of
the head and an area of modelled forehead on the other. A face reads
from a PAIR. One socket is a wound; two things at the same height, one
open and one closed, are a face looking at you.

So the left eye is built on the orbit's own rows -- 11, 12, 13 against
the cavity at 12-13 -- and built as the three marks an eye actually is at
this scale, which is not an almond and a circle:

    row 10  THE BROW RIDGE, lit, and the reason it is drawn first: what
            makes an eye read is the SHADOW it sits in, and a shadow
            needs something casting it. The crest descends outward, so
            the ridge's mass moves down through the cell as it goes --
            ▀ at the inner end where the crest is high in the row, █
            across the middle where it fills, ▄ at the outer end where
            it has already dropped into row 11. Three glyphs, one ridge,
            no banding, and the descent is the anatomy rather than a way
            of avoiding a long run.
    row 11  THE UPPER LID in that shadow: the darkest cells in this half
            of the face. It is drawn as absence -- sparse glyphs on black
            at rung 1-2 -- because a lid tucked under a brow is not a
            dark COLOUR, it is a lack of light.
    row 12  THE APERTURE, dark across, and ONE bright cell at x36 where
            the fire is reflected off the wet of the eye. That single
            catchlight is the whole mark. Nothing else in a face is a
            small bright point inside a dark slot, and an eye without one
            reads as a hole -- which is exactly what the other side of
            this head is, and the difference between the two is the
            picture.
    row 13  THE LOWER LID, lit, its margin sloping down and out, drawn
            the same way the brow's is and in the opposite direction.

land() is the other half of t.spell(): spell picks the glyph to hit a
value and is therefore no use when the glyph is already decided by where
the edge falls. This one takes the glyph as given and picks the colour
pair -- from the same heat band, so the hue law is untouched -- that
comes closest to the value. Every half-block edge in this file is placed
through it.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t


def land(v, x, y, glyph):
    """A value at a place with the GLYPH already chosen -> (glyph, fg, bg).

    The inverse of spell(). Hue still comes from the heat field alone.
    """
    band = next(n for thr, n in t.BANDS_BY_HEAT if t.heat(x, y) >= thr)
    fg, bgs = t.BANDS[band]
    bg = min(bgs, key=lambda b: abs(t.value(glyph, fg, b) - v))
    return glyph, fg, bg


# (x, glyph, value) per row. A glyph of None means "spell it" -- the cell
# is surface, not an edge, and the ramp should choose its own ink.
BROW = [(30, '▄', .24), (31, '▄', .24), (32, '█', .48),
        (33, '█', .48), (34, '█', .48), (35, '▀', .40),
        (36, '▀', .40), (37, '▀', .40)]
LID = [(30, '▀', .24), (31, '▀', .24), (32, None, .06),
       (33, None, .06), (34, None, .11), (35, None, .11),
       (36, None, .11), (37, None, .23)]
# The corners are deliberately the dimmest surface cells in the face.
# First version had the inner corner at .29 -- anatomically defensible,
# the caruncle does catch light -- and _check caught it: at .29 against a
# .40 catchlight there are two bright cells four apart in one row, which
# is a pair of specks, not an eye. The nose shades that corner. Use it.
APERTURE = [(31, None, .11), (32, None, .06), (33, None, .02),
            (34, None, .06), (35, None, .11),
            (36, '▀', .40),                      # THE CATCHLIGHT
            (37, None, .11)]
LOWER = [(31, '▄', .24), (32, '▀', .40), (33, '▀', .40),
         (34, '█', .48), (35, '▀', .40), (36, '▄', .24),
         (37, '▒', .24)]

ROWS = {10: BROW, 11: LID, 12: APERTURE, 13: LOWER}


def build():
    cells = []
    for y, spec in ROWS.items():
        for x, glyph, v in spec:
            cells.append((x, y, *(land(v, x, y, glyph) if glyph
                                  else t.spell(v, x, y))))
    return cells


def _check():
    """The two things that make this an eye rather than four bars.

    CONTRAST -- the catchlight has to be the brightest cell in its own
    row by a wide margin, or it is just another lit cell in a lit face.
    PAIRING -- and it has to sit on the same rows as the orbit on the
    burning side, because that is the entire argument for drawing it.
    """
    lit = t.value(*land(.40, 36, 12, '▀'))
    rest = [v for x, g, v in APERTURE if x != 36]
    assert lit > 2.5 * max(rest), (lit, max(rest))
    assert min(ROWS) <= 11 and max(ROWS) >= 13, 'must span the orbit rows'
    return lit / max(rest)


if __name__ == '__main__':
    cells = build()
    n = t.paint(cells)
    half = sum(1 for _, _, g, _, _ in cells if g in '▀▄▌▐')
    print('cells', n, '/', half, 'landed mid-cell; catchlight is',
          '%.1fx' % _check(), 'the next brightest cell in its row')
