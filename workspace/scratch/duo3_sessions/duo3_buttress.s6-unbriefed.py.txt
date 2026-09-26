"""duo3 session 6: the two buttresses, now that the front has uncovered them.

Moving FRONT off its ruler line put intact surface out at x48-49 at the
brow ridge and the zygomatic arch -- eight cells of face that had been
inside the burn for five sessions and had never been drawn. duo3_model
filled them from its value grid and they came out as four and five
identical cells in a row: the same flat-band defect planes2 was written
to fix on the LEFT half of this same brow ridge, reappearing on the
right the moment the fire let go of it.

So this is planes2's pass, mirrored, for the half of the head that was
under the fire. The arch of the supraorbital rim is the drawing:

  RIGHT_RIM is planes2's RIM reflected about x38.5. It lands at 9.5
  across the crest (x44-46) and at 10.5 either side, so row 9 reads
  ▓ ▓ ▀ ▀ ▀ ▓ and row 10 reads ▀ ▀ ░ ░ ░ ▀ -- the rim riding UP over
  the crest and the socket's shadow appearing underneath it exactly
  where it does. It is an arch because both rows move.

  The shelf's own top plane is clipped away at x44-46: front(8) is 42,
  so the fire has taken the top of the ridge and left the rim. That is
  not a workaround for a missing cell -- it is why a burnt brow ridge
  reads as a flange of bone standing out of the burn rather than as a
  shelf. The three ░ under the crest run straight into the burnt socket
  at rows 11-15, which is the same overhang the intact side has and the
  reason the two halves are one head.

Every cell here stops one column SHORT of front(y). The last intact
column is duo3_model's LIP and it stays its business: skin at the edge
of a break faces the fire more squarely than the surface behind it.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

SK = 3
# planes2 RIM = {28:10, 29:10, 30:10, 31:9, 32:9, 33:9, 34:10, 35:10},
# reflected about x38.5. r means the rim lands at r + 0.5.
RIGHT_RIM = {42: 10, 43: 10, 44: 9, 45: 9, 46: 9, 47: 10, 48: 10, 49: 10}

cells = []
for x, r in RIGHT_RIM.items():
    if x < t.front(r):
        cells.append((x, r, '▀', SK, 1))        # lit bone above, its shadow below
    if x < t.front(r - 1):
        cells.append((x, r - 1, '▓', SK, 1))    # the ridge's top plane, a step up
    if r + 1 <= 11 and x < t.front(r + 1):
        cells.append((x, r + 1, '░', SK, 0))    # socket shadow, deepest under the crest

t.paint(cells)


def _check():
    """An arch, as a number: the rim cannot be one row. If a later edit
    flattens RIGHT_RIM this is a band again and the count goes to 1."""
    rows = sorted({r for r in RIGHT_RIM.values()})
    assert len(rows) == 2, rows
    landed = sum(1 for _, _, g, _, _ in cells if g in '▀▄▌▐')
    assert landed >= 7, landed   # 8 columns less the lip at x49
    return landed


if __name__ == '__main__':
    print('cells', len(cells), '/', _check(), 'landed mid-cell')
