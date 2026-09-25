"""duo3 pass 7: background base tone, plus embers off the dissolve.

STYLE.md's rule for backgrounds is base tone first, texture on top --
marks straight onto black read as streaks on black, not as air. So this
pass is the base tone only, and it is the one place in the piece where a
computed field is the right tool: the light falls off from the burning
side the way light does, and hand-placing 500 background cells to
approximate an inverse-square would be worse, not more authored.

The first version of this covered the whole canvas in a lavender oval
that competed with the face -- a computed field is the right tool only
while it stays a base TONE, and that one had become a second subject.
It is much tighter now, and it does not exist at all on the dark side.

Two things keep it from being a clean set of rings:
  - the head OCCLUDES it. Cells to the left of the face get knocked
    down a band, because the head is between them and the only light
    source in the picture.
  - the embers are hand-placed, not scattered by the field. They rise
    and drift right off the temple, which is where the dissolve is
    actually shedding, and they thin out with height.

Only cells that are still empty black get written, so nothing here can
touch the face.
"""
import math
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

EMBER_X, EMBER_Y = 47.0, 13.0      # the socket -- the piece's only light
HEAD_L, HEAD_R = 24, 52

grid = t.grid(0, 0, 80, 28)
cells = []
for y, row in enumerate(grid):
    for x, (ch, fg, bg) in enumerate(row):
        if not (ch == ' ' and bg == 0):
            continue                         # occupied -- leave it alone
        # The head is between this light and everything on its far
        # side, so there is no glow over there at all -- the intact
        # half keeps the dark it was modelled against.
        if x < HEAD_L + 16 and 1 <= y <= 26:
            continue
        # AND no glow within ten cells of the front, on either side of
        # it. The dissolve has to end against black or its gaps are not
        # gaps -- they are a slightly darker lavender, and the face
        # simply fades into the air it is supposed to be leaving.
        if 3 <= y <= 24 and x < t.front(y) + 11:
            continue
        # cells are about twice as tall as wide, so vertical distance
        # counts double or the falloff comes out as an ellipse
        d = math.hypot(x - EMBER_X, 2 * (y - EMBER_Y))
        if d < 12:
            cells.append((x, y, '▒', 1, 0))
        elif d < 18:
            cells.append((x, y, '░', 1, 0))
        elif d < 22 and (x + y) % 2 == 0:
            # the outermost band is thinned on a checker -- a solid
            # ring of magenta read as a lavender edge around the glow,
            # where what it should do is run out of light
            cells.append((x, y, '░', 5, 0))

# Embers off the temple: a plume, not a scatter. Bright and dense where
# they leave the face, cooling and thinning as they rise.
EMBERS = [
    (54, 6, '▒', 9), (56, 5, '░', 9), (55, 8, '▓', 11),
    (58, 4, '░', 1), (57, 7, '▒', 9), (59, 6, '░', 9),
    (53, 3, '░', 9), (55, 2, '░', 1), (60, 3, '░', 1),
    (58, 10, '▒', 9), (61, 8, '░', 9), (60, 11, '░', 1),
    (56, 12, '▓', 11), (59, 14, '▒', 9), (62, 12, '░', 9),
    (57, 16, '▒', 9), (61, 17, '░', 1), (55, 19, '░', 9),
    (58, 20, '░', 1), (54, 22, '░', 1), (63, 5, '░', 1),
    (64, 10, '░', 1), (62, 20, '░', 1), (52, 25, '░', 1),
]
cells += [(x, y, ch, fg, 0) for x, y, ch, fg in EMBERS]

t.paint(cells)
print('cells', len(cells))
