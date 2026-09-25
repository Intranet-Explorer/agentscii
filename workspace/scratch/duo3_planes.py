"""duo3 session 2, pass 4: two plane breaks on the intact half.

canvas_metrics says half_block 7.2% against a corpus median of 15%, and
shade 78.7% against a median of 10%. That is the shape STYLE.md warns
about by name -- "78% dither and 0% half-block" -- and it is not a
scoring problem, it is a description of what the intact half is made of:
a continuous dithered gradient with almost no landed edges. A face is not
a gradient. It is a small number of planes meeting along lines, and the
lines are where the cell budget should go.

Eleven cells here, which is not a fix. It is the two breaks I am most
confident about geometrically, placed as half-blocks so the edge lands
mid-cell instead of stair-stepping on a cell boundary:

  the zygomatic -- the shadow under the cheekbone, running from the
  widest point of the head down and in toward the corner of the mouth

  the mandible -- where the front of the cheek turns under into the jaw

The rest of the deficit is a pass of its own and goes in NEXT rather than
getting rushed at the end of a session.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

# Under the cheekbone: lit bone in the top half, the hollow beneath it in
# the bottom half. One cell per column, dropping a row every second
# column, so the line runs diagonally instead of along a row.
ZYGOMATIC = [(29, 16), (30, 17), (31, 17), (32, 18), (33, 18), (34, 19)]

# The jaw: the cheek's front plane in the top half, the underside turning
# away in the bottom half.
MANDIBLE = [(30, 20), (31, 21), (32, 21), (33, 22), (34, 22)]

# A break only reads if BOTH sides of it move. The zygomatic cells on
# their own were a half-step against neighbours already sitting at the
# same value and did nothing; the cell directly above each one goes up a
# rung, which is what a bone catching light does.
LIT = [(29, 15), (30, 16), (31, 16), (32, 17), (33, 17), (34, 18)]

cells = ([(x, y, '▄', 1, 3) for x, y in ZYGOMATIC]
         + [(x, y, '▀', 3, 1) for x, y in MANDIBLE]
         + [(x, y, '█', 3, 1) for x, y in LIT])
t.paint(cells)
print('cells', len(cells))
