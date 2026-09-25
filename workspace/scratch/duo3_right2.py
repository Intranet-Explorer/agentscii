"""duo3 session 4: the burning side, given something to dissolve FROM.

The review: "Thirteen rows, same ramp, no vertical variation.
Charitably it's the head dissolving into embers, which the title
supports -- but a dissolve needs form to dissolve FROM, and this is a
gradient applied uniformly per row."

I said this myself at the end of session 2 and thought session 3 had
fixed it. It had not, and the reason is worth writing down because it
is a mistake I could make again. Session 3's fix was to measure the
plates from a stated edge -- d = x - front(y) -- instead of from the
left margin. That IS the right move and it is the difference between a
gradient and a structure. But front(y) only travels three cells over
the whole height of the head, so for a given d the rule produced very
nearly the same plate-and-gap sentence in every one of twenty-two rows.
I replaced a function of x with a function of d and both of them are
functions of ONE variable. The picture needed a second one.

duo3_tools.PROMINENCE is it: how far the flesh stood forward at the
burning edge, row by row, read across from the form duo3_model draws on
the intact side. Brow ridge 9, cheekbone 9, eye socket 2, temple hollow
3. Four things now take their size from it, and each one is a claim
about how a face comes apart rather than a knob:

  REACH -- how far the shed material carries. Bone standing proud of
    the fire throws its chips clear; a hollow sheds into itself. This is
    the one that matters most, because it is what turns the field's
    outer boundary from the block-in's circle into a profile of the
    head: it bulges seven cells past the old silhouette at the brow and
    the cheekbone and falls four cells short of it at the socket.
  PLATE SIZE -- a proud plane has more material in one piece.
  GAP -- and a hollow has more air between what is left of it.
  HEAT -- a plate that stood closest to the fire is still the hottest.

So rows 9-10 and 16-17 are big bright plates carrying a long way, rows
11-15 and 18-19 are small dim ones that stop early, and between them
there is a silhouette. That is the head, dissolving, instead of a ramp.

The crack and the socket are unchanged from session 3. The crack is the
one mark in the piece that runs the full height of the head and it
should not acquire variation; it is a parting, and a parting is a line.
"""
import math
import random
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

Y0, Y1 = 3, 24
XMAX = 66


def silhouette(y):
    """Right edge of the block-in's head mass, in cells, for this row."""
    best = 0.0
    for py in (2 * y, 2 * y + 1):
        for cx, cy, r in ((38, 20, 14), (44, 30, 8), (38, 34, 6), (38, 42, 6)):
            d = r * r - (py - cy) ** 2
            if d > 0:
                best = max(best, cx + math.sqrt(d))
    return best


reach = t.reach                         # duo3_bg has to agree with it


# Value by distance from the front (duo3_tools.RAMP keys, light to
# dark). Hottest right at the seam, because that is where the fire is
# still in contact with skin; embers by the time the plates are single
# cells.
COOL = 'FEEDDCCBBAA99888'


def val(d, lead, p):
    v = COOL[min(d, len(COOL) - 1)]
    i = t.RAMP_ORDER.index(v)
    if not lead:                      # plate body, one step back from its edge
        i -= 1
    i += round((p - 4.5) / 2.5)       # and the whole plate rides on prominence
    return t.RAMP_ORDER[max(0, min(len(t.RAMP_ORDER) - 1, i))]


cells = []
for y in range(Y0, Y1 + 1):
    f, p = t.front(y), t.prom(y)
    rnd = random.Random(977 + y)
    edge, stop = silhouette(y), reach(y)

    # Clear this row's whole territory first. Without this a row whose
    # reach has pulled IN leaves last version's plates stranded past the
    # new boundary, which is the worst of both fields.
    for x in range(f + 1, XMAX + 1):
        cells.append((x, y, ' ', 0, 0))

    # THE CRACK. Half a cell of black with the first plate's lit edge
    # against it -- a whole black column at this width reads as a drawn
    # border, half a cell reads as a parting. Where the socket has
    # opened it the seam is simply gone.
    if 12 <= y <= 14:
        cells.append((f + 1, y, ' ', 0, 0))
    else:
        cells.append((f + 1, y, '▐', 11 if 8 <= y <= 18 else 9, 0))

    x = f + 2
    while x <= stop:
        d = x - f
        plate = round((4.5 - 0.5 * d) * (0.55 + p / 12.0)) + rnd.choice([-1, 0, 0, 1])
        gap = round((0.6 + 0.45 * d) * (1.6 - p / 9.0)) + rnd.choice([0, 0, 1])
        plate, gap = max(1, min(5, plate)), max(1, min(6, gap))
        for i in range(plate):
            if x + i > stop:
                break
            dd = x + i - f
            v = val(dd, i == 0, p)
            if x + i > edge + 1:      # past the head: embers, not skin
                if rnd.random() < 0.45:
                    continue          # most of what came off is already out
                v = t.RAMP_ORDER[max(0, t.RAMP_ORDER.index(v) - 3)]
            cells.append((x + i, y, *t.RAMP[v]))
        x += plate + gap

# --- the socket: the hole the front opened first ----------------------
# Unchanged. Dark rim carried on both half-rows above and below, so the
# opening has a lid-thickness the way the intact eye does, and the core
# sits where an iris would sit -- that pairing across the face is the
# whole reason this reads as a socket and not as a wound on a cheek.
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


def _check():
    """The defect, as a number. Before this pass the field's outer
    boundary was the block-in circle in every row; if reach() ever
    stops tracking the head's form it goes back to being one."""
    r = [reach(y) for y in range(Y0, Y1 + 1)]
    circle = [int(max(silhouette(y), t.front(y) + 4)) for y in range(Y0, Y1 + 1)]
    spread = max(a - b for a, b in zip(r, circle)) - min(a - b for a, b in zip(r, circle))
    assert spread >= 10, spread
    assert reach(10) > reach(13) + 6, (reach(10), reach(13))   # brow vs socket
    return spread


if __name__ == '__main__':
    print('cells', len(cells), 'boundary undulation %d cells' % _check())
