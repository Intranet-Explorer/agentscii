"""duo3 pass 4: mouth and jaw, x28..48, rows 18..24.

The block-in's chin capsule tapered to a narrow column below row 19 --
from the cheekbone out at x24..x52 it dropped straight to x32..x44, a
step, not a jaw. Rebuilt here per cell: the jaw angle stays wide under
the ear and narrows over six rows to a chin that is broad, not pointed.

The mouth is two hand-placed rows. The line where the lips meet falls
BETWEEN cell rows, so it is drawn as the lower half of row 20 -- the
upper lip above it, the lit top surface of the lower lip in the upper
half of row 21 directly beneath. That is the whole read: a dark line
with a lit edge under it. Both lips grade left to right, dark corner to
ember-lit corner, because the light is still the same light.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 28, 18
#      x28..x34  x35..x41  x42..x48
ROWS = [
    '1244555' '2345677' '5677889',   # 18 under the nose, lip shelf
    '1244455' '2344567' '6677889',   # 19 philtrum, upper lip rising
    '12445' + '.' * 11 + '77899',    # 20 mouth          (feature row)
    '11445' + '.' * 11 + '67889',    # 21 lower lip      (feature row)
    '0000445' '5667776' '6770000',   # 22 chin, jaw angle gone
    '0000044' '5566776' '6000000',   # 23 chin
    '0000001' '2244554' '1000000',   # 24 underside of the chin, in shadow
]
cells = t.levels(X0, Y0, ROWS, width=21)

U, D, LH, RH = '▀', '▄', '▌', '▐'
F = []

# row 20: the mouth line, in the lower half of the cell. Above it the
# upper lip, which turns away from us and stays dark even on the lit
# side -- an upper lip almost never catches light a lower lip does.
for x, bg in zip(range(33, 44), [1, 1, 1, 3, 3, 3, 3, 3, 9, 9, 3]):
    F.append((x, 20, D, 0, bg))

# row 21: the lower lip's lit top surface, shadow under it.
for x, fg, bg in zip(range(33, 44),
                     [3, 3, 3, 9, 9, 9, 9, 9, 11, 11, 3],
                     [1, 1, 1, 1, 1, 3, 3, 3, 3, 3, 1]):
    F.append((x, 21, U, fg, bg))

# jaw and chin silhouette: ink on the half of the cell the head is
# actually on, so the outline curves instead of stepping. The right
# edge takes a rim off the ember; the left edge dies into the ambient.
for y, x in [(19, 28), (20, 29), (21, 30), (22, 32), (23, 33), (24, 35)]:
    F.append((x, y, RH, 5 if y < 24 else 1, 0))
for y, x, fg in [(19, 48, 9), (20, 48, 9), (21, 47, 9), (22, 45, 9),
                 (23, 43, 9), (24, 41, 3)]:
    F.append((x, y, LH, fg, 0))

t.paint(cells + F)
print('cells', len(cells) + len(F))
