"""duo3 session 3, the burning side, rewritten from A FRONT.

What was wrong with session 1's version, in my own words from
duo3_NOTES.md: "The gap pattern in those sixteen rows is, cell for cell,
a function of x: more zeros the further right you go, in every row,
monotonically. That is a gradient of striation. There is no FRONT -- no
column where intact skin stops and coming-apart starts -- so there is
nothing for the density to be a distance FROM. Density that tracks x is
a rule. Density that tracks distance from a stated edge is structure."

So the edge gets stated first (duo3_tools.FRONT) and everything here is
measured from it:

  x <= front(y)      intact skin. Not touched by this pass at all.
  x == front(y)+1    THE CRACK. A half cell of black with the first
                     plate's lit edge against it, unbroken from the crown
                     to the jaw -- the seam the skin has come away along,
                     and the only thing in the piece that runs the full
                     height of the head. Half a cell, not a whole one,
                     because a whole black column at this width reads as
                     a drawn border; half reads as a parting.
  x == front(y)      THE LIP -- the last intact cell in the row. Written
                     by duo3_model, which runs after this pass and owns
                     every cell on the intact side.
  x >= front(y)+2    plates and gaps, both sized by d = x - front(y).
                     Plates shrink from five cells to one; gaps grow from
                     one to six. Past the old silhouette the plates are
                     embers with a lot of black between them.

The same d that sizes the plates cools them, and every plate is one step
brighter on its leading edge than in its body -- a plate is a chip of
skin standing slightly proud of the fire behind it, so its near edge
catches and its middle does not. That is also where most of this pass's
ink variation comes from: forty small edges rather than one smooth ramp.

The socket is placed by hand afterwards. It is not an eye. It is the
hole the front opened first, which is why the front notches inward at
rows 12-14 -- the break started there and the rest of the seam is still
catching up.
"""
import math
import random
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

Y0, Y1 = 3, 24
XMAX = 62


def silhouette(y):
    """Right edge of the block-in's head mass, in cells, for this row."""
    best = 0.0
    for py in (2 * y, 2 * y + 1):
        for cx, cy, r in ((38, 20, 14), (44, 30, 8), (38, 34, 6), (38, 42, 6)):
            d = r * r - (py - cy) ** 2
            if d > 0:
                best = max(best, cx + math.sqrt(d))
    return best


# value letter by distance from the front (duo3_tools.RAMP keys, light
# to dark). Hottest right at the seam, because that is where the fire is
# still in contact with skin; embers by the time the plates are single
# cells.
COOL = 'FEEDDCCBBAA99888'


def val(d, lead):
    v = COOL[min(d, len(COOL) - 1)]
    if not lead:                      # plate body, one step back from its edge
        i = t.RAMP_ORDER.index(v)
        v = t.RAMP_ORDER[max(0, i - 1)]
    return v


cells = []
for y in range(Y0, Y1 + 1):
    f = t.front(y)
    rnd = random.Random(977 + y)
    edge = silhouette(y)
    stop = int(max(edge, f + 4)) + 3

    # THE CRACK. Half a cell of black with the first plate's lit edge
    # against it -- a whole black column at this width reads as a drawn
    # border, half a cell reads as a parting. Where the socket has
    # opened it the seam is simply gone; that is what the notch in
    # duo3_tools.FRONT is recording.
    if 12 <= y <= 14:
        cells.append((f + 1, y, ' ', 0, 0))
    else:
        cells.append((f + 1, y, '▐', 11 if 8 <= y <= 18 else 9, 0))

    x = f + 2
    while x <= stop:
        d = x - f
        plate = max(1, min(5, round(4.5 - 0.5 * d) + rnd.choice([-1, 0, 0, 1])))
        gap = max(1, min(6, round(0.6 + 0.45 * d) + rnd.choice([0, 0, 1])))
        for i in range(plate):
            if x + i > stop:
                break
            dd = x + i - f
            v = val(dd, i == 0)
            if x + i > edge + 1:      # past the head: embers, not skin
                if rnd.random() < 0.45:
                    continue          # most of what came off is already out
                iv = max(0, t.RAMP_ORDER.index(v) - 3)
                v = t.RAMP_ORDER[iv]
            cells.append((x + i, y, *t.RAMP[v]))
        x += plate
        for i in range(gap):
            if x + i <= stop:
                cells.append((x + i, y, ' ', 0, 0))
        x += gap

# --- the socket: the hole the front opened first ----------------------
# Dark rim carried on both half-rows above and below, so the opening has
# a lid-thickness the way the intact eye does, and the core sits where an
# iris would sit -- that pairing across the face is the whole reason this
# reads as a socket and not as a wound somewhere on a cheek.
SOCKET = [
    (44, 11, '▄', 9, 0), (45, 11, '▄', 9, 0), (46, 11, '▄', 11, 0),
    (47, 11, '▄', 9, 0), (48, 11, '▄', 9, 0),
    (44, 12, '·', 9, 0), (45, 12, '░', 11, 0), (46, 12, '█', 11, 9),
    (47, 12, '█', 11, 9), (48, 12, '▒', 11, 9), (49, 12, '·', 9, 0),
    (44, 13, '·', 9, 0), (45, 13, '▒', 11, 9), (46, 13, '█', 15, 11),
    (47, 13, '█', 15, 11), (48, 13, '█', 11, 9), (49, 13, '░', 11, 0),
    (44, 14, '°', 9, 0), (45, 14, '▀', 11, 9), (46, 14, '▀', 11, 9),
    (47, 14, '▀', 15, 11), (48, 14, '▀', 11, 9), (49, 14, '·', 9, 0),
    (45, 15, '▀', 9, 0), (46, 15, '▀', 11, 0), (47, 15, '▀', 11, 0),
    (48, 15, '▀', 9, 0),
]
cells += SOCKET

t.paint(cells)
print('cells', len(cells))
