"""duo3 session 6: the front cut from the skull, and given a char line.

Two defects, one mark. The reviewer's "hard vertical seam through the
face, perfectly straight, full-height -- renders as a red pillar
bisecting the head" and my own note that FRONT travelled three cells over
the whole height are the same sentence, and duo3_tools.FRONT is where the
placement half is fixed: the front now bulges to x49-50 at the brow ridge
and the zygomatic arch and notches back to x40-41 at the temple fossa and
the orbit, because fire goes through what is thin and those two buttresses
are the heaviest bone in the face.

Placement was the easy half. The hard half is that the seam was BRIGHT.
Everything from x44 rightward sat pegged at the top two rungs for all
twenty-two rows -- not one column, a six-column band of salmon and yellow
running the full height -- so there was no value event at the front at
all. Moving a bright band onto a curve gives a curved bright band.

THE CHAR. What actually ends a burning surface is carbon. The last
millimetre of skin before the fire is the darkest thing on the head, not
the brightest, and it sits between modelled flesh on one side and open
flame on the other. So the front is drawn as a dark red lip -- fg 1, the
darkest solid this palette has -- and the value goes 8, 9, 9, char, black,
fire across four cells. That is a drawn edge in the one sense that
matters: a reviewer tracing the boundary finds a mark there, not the place
where one field stops and another starts.

The char is not uniform either, and what varies is thickness, because
thickness is a statement about the bone under it:

    proud bone      two and three cells of char. The fire stood against
                    the brow and the arch longest because they are what
                    it met first, and they had the material to char
                    rather than go through.
    thin bone       a single ▒ of char, or none. The temple fossa and the
                    orbit did not char, they perforated; the skin there
                    simply stops and the next thing is the hole.

THE OVERHANG, rows 11 and 18. The two cells that make this a skull rather
than a profile line. A brow ridge overhangs its orbit and a zygomatic arch
overhangs the hollow under it, so on the row BELOW each crest the surface
continues four cells further out than the front does -- as ▀, ink in the
upper half of the cell only, because that underside is a ceiling and a
ceiling lands between two rows rather than on one. Dark, because it faces
down into a cavity, with the fire below and outside it.

Sub-cell landing, same law as the left contour: ▐ where the surface ends
mid-cell, ▌ where the cell's outer half is already gone, ▄ where the front
swings so far between two rows that its edge is running more horizontally
than vertically (rows 9 and 16, where the brow and the arch sweep out).
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

CHAR_FG = 1                 # the darkest solid in the palette; see docstring
CHAR = {'#': '█', ']': '▐', '[': '▌', '^': '▀',
        '_': '▄', '~': '▓', ',': '▒'}

X0 = 40                     # the strip starts here; everything left of it
                            # is duo3_model's face and stays its business.

# One row per line, x40 through front(y). Digits are RUNG values spelled
# through the heat field; the symbols in CHAR are the lip. Each row's
# length is asserted against front(y) below -- that assertion is the only
# thing keeping the two tables honest with each other.
STRIP = {
    3:  '567]',                 # the crown, barely touched
    4:  '5667]',
    5:  '5677]',
    6:  '5677]',
    7:  '566]',                 # the forehead falling back
    8:  '4,',                   # TEMPLE FOSSA: perforated, not charred
    9:  '67789~_',              # the brow coming up; its top edge lands
                                # mid-row against row 10's longer reach
    10: '678999~##[',           # BROW CREST -- three cells of char
    11: '6653,[',               # the orbit's upper wall, in its own shadow
    12: '3,',                   # THE ORBIT: gone
    13: ',',
    14: '32,',
    15: '66774]',               # the cheek climbing to the arch
    16: '678998~#_',            # the arch sweeping out
    17: '6789999~##[',          # ARCH CREST -- furthest forward on the head
    18: '6653,[',               # the hollow under it
    19: '43,',                  # CHEEK HOLLOW: the deepest bite below the eye
    20: '66764]',
    21: '678875~#',             # the masseter
    22: '67764,[',
    23: '678875 3~#'.replace(' ', ''),   # THE JAW LINE
    24: '67764,[',              # the chin's corner
}

# The undersides. x range per row, drawn as ▀: a ceiling lands between
# rows, and both of these are ceilings over a cavity the fire has opened.
OVERHANG = {11: range(46, 50), 18: range(46, 49)}

# THE ORBIT, redrawn. Session 3 built this as a bright core on a hot
# ground -- a full block of fg 15 over fg 11, the ember burning in the
# eye -- and the reviewer read it exactly as it is: "a single pure-white
# block with no falloff, an isolated blowout." It was also the only cell
# in the piece using white at all.
#
# A socket is a HOLE. It is the one part of a head that stays dark
# wherever the light is, because it is a cavity and its own rim shades
# it. What catches light is the BONE AROUND IT -- and with the front now
# eaten back to x40 on these rows there is no skin here at all, so what
# gets drawn is the orbital rim itself, four walls of it, each taking its
# value from which way it faces the fire:
#
#   superior   the brow's underside, a ceiling: dark, and ▀ because a
#              ceiling lands between two rows rather than on one.
#   medial     x43, the nasal side, turned toward the fire: lit, and
#              brighter on the lower row where the brow stops shading it.
#   lateral    x48-49, the outer wall, square to the fire and level with
#              the ember at row 13 -- the hottest bone on the head.
#   inferior   the floor, row 14, a ledge seen from above.
#
# The cavity between them is left black. Four lit walls around a hole is
# the entire drawing; nothing whatever is placed inside it.
ORBIT = ([(x, 11, '▀', 1) for x in range(44, 50)]
         + [(43, 12, '▐', 3), (48, 12, '▌', 9), (49, 12, '▒', 9)]
         + [(43, 13, '▐', 9), (48, 13, '▌', 11), (49, 13, '▓', 9)]
         + [(x, 14, '▀', 3) for x in range(44, 49)]
         + [(47, 15, '▀', 3), (48, 15, '▀', 3)])
ORBIT_HOLE = [(x, y) for y in (12, 13) for x in range(44, 48)]


def build():
    cells, blank = [], []
    for y, spec in STRIP.items():
        f = t.front(y)
        assert len(spec) == f - X0 + 1, (y, len(spec), f - X0 + 1)
        for i, s in enumerate(spec):
            x = X0 + i
            if s in CHAR:
                cells.append((x, y, CHAR[s], CHAR_FG, 0))
            elif s != '.':
                cells.append((x, y, *t.spell(t.RUNG[int(s)], x, y)))
        # One cell of black outside the char, so the fire never abuts it.
        # This replaces duo3_right2's bright crack at f+1, which was the
        # lit half of the pillar; the char is the parting now.
        blank.append((f + 1, y))
    blank += ORBIT_HOLE
    return cells, blank


def apply():
    """Blanks go down BEFORE the marks that sit outside the front, not
    after: the black gap at f+1 and the orbit's cavity are CLEARINGS, and
    the overhang and the orbital rim are drawn into the ground they
    clear. Getting this backwards cost the brow its first four cells of
    underside without erroring -- the blank simply landed last."""
    cells, blank = build()
    over = [(x, y, '▀', CHAR_FG, 0)
            for y, xs in OVERHANG.items() for x in xs]
    over += [(x, y, g, fg, 0) for x, y, g, fg in ORBIT]
    n = t.paint(cells + [(x, y, ' ', 0, 0) for x, y in blank] + over)
    return n, cells + over


def _check():
    """The defect as a number, both halves of it.

    TRAVEL -- the front spanned three cells and read as a ruler. VALUE --
    and it was the brightest thing on the head for its whole length, so
    even on a curve it would have read as a band rather than an edge. The
    char has to be DARKER than the surface it ends, in every row.
    """
    f = [t.front(y) for y in range(3, 25)]
    assert max(f) - min(f) >= 9, max(f) - min(f)
    assert t.front(10) - t.front(13) >= 8                  # brow vs orbit
    assert t.front(17) - t.front(19) >= 7                   # arch vs hollow
    peak, lip = [], []
    for y, spec in STRIP.items():
        body = [int(s) for s in spec if s.isdigit()]
        if not body:
            continue                    # the orbit: no surface left to end
        peak.append(t.RUNG[max(body)])
        lip.append(t.value(CHAR[spec[-1]], CHAR_FG, 0))
        assert lip[-1] <= peak[-1], (y, lip[-1], peak[-1])
    assert sum(lip) < 0.55 * sum(peak), (sum(lip), sum(peak))
    return max(f) - min(f)


if __name__ == '__main__':
    n, cells = apply()
    landed = sum(1 for _, _, g, _, _ in cells if g in '▀▄▌▐')
    print('cells', n, '/', landed, 'landed mid-cell; front travels',
          _check(), 'cells (was 3)')
