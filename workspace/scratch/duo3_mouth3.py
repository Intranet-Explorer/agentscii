"""duo3 session 4: the mouth rebuilt as a BARREL, not as a sandwich.

Same review line as duo3_eye3 answers. The eye is rebuilt as a sphere
in a hole; this has to be built out of a different fact or the two are
still one motif with different numbers in it.

The fact is: a mouth is TWO SOFT MASSES LYING ON A CYLINDER. Not set
into anything -- there is no socket, no rim, no ring of shadow round
it. It bulges OUT. Which changes four things, and each one is the
opposite of what the eye does:

  * The eye's dark is a HOLE (socket, iris, pupil): dark because light
    cannot reach in. The mouth's dark is a SEAM and two CORNER POCKETS:
    dark because two surfaces meet and because the cylinder turns away
    at its ends. So the corners go deep on BOTH sides -- x33 and x43
    are both · -- for a reason that has nothing to do with the light.
  * The two masses are not the same value. The upper lip faces DOWN and
    away and is the darker; the lower lip faces UP and toward and is
    the lighter. Before this pass the upper lip's cells were ▀ 3,0,
    whose top half is full-value skin -- there was no upper lip at all,
    only a line drawn under the philtrum. It is a mass now: .12 .24 .24
    .40 .24 .40 .36 .44, dark at the near end and lit at the far one.
  * The SEAM CHANGES HEIGHT. That is the whole difference between a
    mouth and a rule. It sits at row 21.0 under x34-35, lifts to 20.5
    across x36-39, and drops back to 21.0 at x40-43: the arc of the
    barrel seen from slightly off to one side. Where it is at 21.0 the
    upper lip is a whole cell and the seam is the top half of the cell
    below it; where it is at 20.5 the seam is the bottom half of the
    cell above. Two different cells doing the same edge at two
    different heights is what a curve is in this medium.
  * The highlight is a POINT and it is OFF CENTRE. The old lower lip
    was crowned █ █ █ at x37-39, centred on the midline, which is a
    highlight placed by symmetry rather than by the light. There is one
    █ now, at x39, on the side the fire is on.

The crease below keeps one deep note at x38, under the fullest part of
the lip, and is otherwise shallow. A mentolabial sulcus is a dent, not
a second mouth, and seven identical ▄ was reading as one.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

DOT, L1, L2, L3, FULL = '·', '░', '▒', '▓', '█'
U, D = '▀', '▄'
SK = 3

F = []


def c(x, y, g, fg, bg):
    F.append((x, y, g, fg, bg))


# --- row 20: THE UPPER LIP as a mass, and the seam's height ------------
# whole cell = the seam is at 21.0 and lives in the row below
# ▀          = the seam is at 20.5 and is this cell's bottom half
c(33, 20, DOT, SK, 0)                   # near corner pocket
c(34, 20, L1, SK, 0)                    # upper lip, near end, turned from the fire
c(35, 20, L2, SK, 0)                    # seam still at 21.0
c(36, 20, U, SK, 0)                     # seam LIFTS to 20.5
c(37, 20, U, SK, 1)                     # the tubercle comes forward and catches
c(38, 20, U, SK, 0)
c(39, 20, U, SK, 1)
c(40, 20, L3, SK, 0)                    # seam DROPS back to 21.0
c(41, 20, L3, SK, 1)                    # upper lip, far end, lit
c(42, 20, L2, SK, 0)
c(43, 20, DOT, SK, 0)                   # far corner pocket, as deep as the near one

# --- row 21: THE LOWER LIP, one highlight, placed by the light --------
c(33, 21, DOT, SK, 0)
c(34, 21, D, SK, 0)                     # seam in the top half, lip below
c(35, 21, D, SK, 1)
c(36, 21, L2, SK, 0)                    # seam is above this cell now: all lip
c(37, 21, L3, SK, 0)
c(38, 21, L3, SK, 1)
c(39, 21, FULL, SK, 0)                  # THE HIGHLIGHT -- one cell, off centre
c(40, 21, D, SK, 1)                     # seam back in the top half
c(41, 21, D, SK, 0)
c(42, 21, L2, SK, 0)
c(43, 21, DOT, SK, 0)

# --- row 22: the crease, a dent with one deep note --------------------
c(35, 22, L1, SK, 0)
c(36, 22, D, SK, 0)
c(37, 22, D, SK, 0)
c(38, 22, DOT, SK, 0)                   # deepest, under the fullest part of the lip
c(39, 22, D, SK, 0)
c(40, 22, D, SK, 1)
c(41, 22, D, SK, 1)

t.paint(F)


def _check():
    """The two claims that make this a barrel and not the eye's motif.

    One: both corners are deeper than anything between them -- the ends
    of a cylinder turn away regardless of where the light is, which is
    not true of a socket. Two: the single brightest cell is not on the
    midline. If a later edit re-centres the highlight, that is symmetry
    placing it again and this fails.
    """
    v = {(x, y): t.value(g, fg, bg) for x, y, g, fg, bg in F}
    for y in (20, 21):
        mid = [v[(x, y)] for x in range(34, 43)]
        assert v[(33, y)] < min(mid) and v[(43, y)] < min(mid), y
    bright = max(v, key=v.get)
    assert bright == (39, 21), bright
    assert bright[0] != 38, 'a highlight on the midline is symmetry, not light'
    return v[bright]


if __name__ == '__main__':
    print('cells', len(F), 'highlight %.2f at x39' % _check())
