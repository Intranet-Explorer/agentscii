"""duo3 session 4: the plane breaks I put in NEXT at the end of session 3.

My own note, and the review's "the forehead is terraced bands" and "the
silhouette is straight-edged on both sides", are the same observation
from two directions: the intact half is a value field that steps from
one WHOLE CELL to the next, and a real edge lands in the middle of one.
Seventeen cells of duo3_planes were the only landed edges in it.

Three breaks here, plus the crown. Each one is a place where the head
genuinely changes plane, and each is placed so BOTH sides of it move --
the lesson duo3_planes recorded the hard way, that a half-step against
neighbours already sitting at the same value does nothing at all.

THE BROW RIDGE. Rows 9-10 were seven identical ▓ 3,0 in a row: the
heaviest bone on the upper face, drawn as a flat band. Its lower edge
is a supraorbital rim and it ARCHES -- it rides up at 9.5 across the
crown of the arch (x31-33) and hangs at 10.5 either side of it. Under
the crown, where the rim is highest, the socket's shadow is deepest;
that is the one place in this head where a run of three identical cells
is correct, because it is a shadow and not a surface.

THE JAW. Row 24 was five identical ▒ 3,0 under the chin. The mandible's
lower border is the hardest edge on a face -- it is where lit bone stops
and the throat's shadow starts, with nothing in between -- so it gets a
▀ all the way along, dropping at 24.5 under the chin and rising to 23.5
as it runs back to the jaw angle, and the cells under it go dark.

THE CROWN. The top of the skull was a dead straight row boundary from
x33 to x44. It is a dome now, landed at 3.5 on the shadow side, 3.0
across the top, 3.5 again as it turns toward the front.

THE FOREHEAD. Different defect, so a different fix: the bands there are
not plane breaks, they are quantisation. A forehead has no edges in it.
What it has is a frontal eminence -- the bump above each brow -- so the
boundary between two density levels is pushed left over the bump at
rows 5-7 and pulled back above and below it, and notched by a cell here
and there so no band edge is a clean line. Interlocking a band edge is
what dithering IS in this medium; a perfectly straight one is the
defect.

Not in this pass, and it is the next real one: the head is exactly the
same width from row 7 to row 15. A straight vertical wall nine rows
long is not a silhouette, and no amount of half-block landing fixes a
contour that is in the wrong place -- the skull has to get wider at the
temple and narrower at the jaw first.
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


# --- THE BROW RIDGE: an arch, not a band -----------------------------
# rim row per column; 9 means the rim lands at 9.5, 10 means 10.5
RIM = {28: 10, 29: 10, 30: 10, 31: 9, 32: 9, 33: 9, 34: 10, 35: 10}
for x, r in RIM.items():
    c(x, r, U, SK, 1)                   # bone lit in the top half, its shadow below
    c(x, r - 1, L3, SK, 1)              # the ridge's own top plane, a step up
    if r + 1 <= 10:                     # row 11 belongs to the eyebrow pass
        c(x, r + 1, L1, SK, 0)          # socket shadow, deepest under the arch's crown

# --- THE JAW: lit bone above, the throat below, no step between -------
JAW = {36: 24, 37: 24, 38: 24, 39: 24, 40: 24, 41: 23, 42: 23}
for x, r in JAW.items():
    c(x, r, U, SK, 1 if x > 36 else 0)  # near corner of the chin stays in shadow
    c(x, r - 1, L3, SK, 1)              # the jaw's front plane, lit
for x in (41, 42):
    c(x, 24, L1, SK, 0)                 # under the angle of the jaw

# --- THE CROWN: a dome, landed at three heights -----------------------
for x in (33, 34, 35):
    c(x, 3, D, 1, 0)                    # falling away on the side from the fire
for x in (41, 42):
    c(x, 3, D, SK, 0)                   # and again as it turns toward it
#   x36-x40 keep their whole cells: the top of the dome sits at 3.0

# --- THE FOREHEAD: interlock the band edges ---------------------------
# The frontal eminence pushes the ░/▒ boundary left at rows 5-7 and it
# pulls back above and below. The three lone cells after it are notches
# -- a band edge with no notches in it is a contour line, not a surface.
for x, y, g in [(34, 5, L2), (32, 6, L2), (31, 7, L2),      # over the eminence
                (37, 4, L1), (31, 8, L1),                   # pulling back
                (36, 5, L1), (35, 6, L1), (33, 7, L1),      # notches
                (39, 6, L2), (38, 7, L2), (36, 8, L2)]:     # ▒/▓ edge, same idea
    c(x, y, g, SK, 0)

t.paint(F)


def _check():
    """What the pass is for, as a number: landed edges. Every ▀ and ▄
    here is a plane break that falls inside a cell instead of on the
    line between two. If a later edit spells these as dither again the
    count drops and the intact half is a gradient again."""
    landed = sum(1 for _, _, g, _, _ in F if g in '▀▄▌▐')
    assert landed >= 20, landed
    return landed


if __name__ == '__main__':
    print('cells', len(F), '/', _check(), 'of them landed mid-cell')
