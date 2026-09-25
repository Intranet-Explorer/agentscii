"""duo3 session 5: the head has to END, and then something has to be
under it.

The review: "Flat unshaded jaw/neck. Rows 26-27 are eight and nine
identical cells. The head doesn't terminate in a jaw; it fades into a
uniform wash." Both halves of that are true and they are different
faults. duo3_contour does the first half -- the mandible's lower border
is now lit bone above and black below, all the way from the angle of the
jaw to the chin. This pass is the second half: what the head is sitting
in front of.

The wash was ░ 1,0 at every cell from x31 to x45 in all three rows. One
value, one glyph, forty-odd cells. It was not a neck; it was the region
tool's leftover, and it had survived four sessions because I kept
working on the face.

THREE FACTS, and everything here is one of them.

1. THE JAW CASTS A SHADOW, and it is the strongest value in the lower
   third of the picture. The light is the ember, up and to the RIGHT, so
   the shadow is thrown down and to the LEFT -- the same direction as the
   nose's cast shadow in session 4, because it is the same light. Under
   the chin, at x34-38, the jaw occludes it completely and row 25 is
   simply black: a chin reads against a throat because there is NOTHING
   between them. Going right the light gets in under the jaw and the
   shadow shortens, so by x43 row 25 is already the lit side of the neck.
   Its lower boundary crosses row 26 mid-cell, which is what ▄ is for.

2. A NECK IS A CYLINDER. It has a terminator on the left, a body, and a
   fall-off at its own right contour -- the brightest cell is x43, not
   x45, because at x45 the surface has turned away again. Both contours
   are landed: ▐ on the left, ▌ on the right.

3. THE STERNOCLEIDOMASTOID. The one piece of anatomy that makes a neck
   read as a neck rather than a pipe: a rope of muscle from behind the
   ear to the sternal notch, so it runs down and FORWARD, crossing the
   cylinder diagonally. Its near edge is a groove, and a groove on a form
   this small is one cell of ▐ -- black on the left, lit on the right --
   which is the whole edge in one character. Three of them, stepping
   x32, x32, x36 as the muscle travels.

Everything here is in the cool band, fg 1 on black, because heat() says
so at every cell of it: the neck is the furthest part of the subject
from the fire and it is in the shade of the jaw besides. That leaves
five levels -- · ░ ▒ ▓ █ -- plus the half blocks at 0.16. It is enough,
and being honest about how little light is down there is better than
reaching for a hue that would say the throat is on fire.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0 = 29

# x29 ..................................... x45
G = [
    # 25: under the mandible. Black under the chin; the shadow shortens
    #     to the right as the light gets in under the jaw.
    ' ▐░··    ··░░▒▓▌ ',
    # 26: the cast shadow's lower boundary crosses this row, and where it
    #     crosses mid-cell the cell is ▄ -- shadow above, neck below.
    '▐░░▐··▄▄░▒▒▓██▓▌ ',
    # 27: out of the shadow. The cylinder, with the SCM crossing it.
    '·░░▐▒▒▓▐▒▓▓███▓▒▌',
]


def apply():
    cells = []
    for r, row in enumerate(G):
        y = 25 + r
        for c, g in enumerate(row):
            x = X0 + c
            cells.append((x, y, ' ', 0, 0) if g == ' ' else (x, y, g, 1, 0))
        # the old wash ran from x31; clear what is left of the new neck
        for x in range(20, X0):
            cells.append((x, y, ' ', 0, 0))
        for x in range(X0 + len(row), 47):
            cells.append((x, y, ' ', 0, 0))
    return cells


if __name__ == '__main__':
    cells = apply()
    n = t.paint(cells)
    landed = sum(1 for _, _, g, _, _ in cells if g in '▀▄▌▐')
    ink = [[g for g in row if g != ' '] for row in G]
    for r, row in enumerate(ink):
        assert len(set(row)) >= 4, (25 + r, 'this row is a wash again')
    print('cells', n, '/', landed, 'landed mid-cell;',
          [len(set(r)) for r in ink], 'distinct glyphs per row')
