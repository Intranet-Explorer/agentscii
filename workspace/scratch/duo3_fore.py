"""duo3 pass 6: forehead and crown, rows 3..8.

The block-in left the top of the skull as one flat brown fill -- in the
glyph-only render it was a solid grey slab, the largest single region in
the piece carrying no ink information at all.

Two blocks, because the two halves are different problems:
  A  x25..x41, the intact forehead. A broad curved surface, so a broad
     gradient is honest here -- but not a pure left-to-right ramp: the
     frontal eminence above the left eye sits proud of it (a local step
     up at x30-32), the midline furrow runs one step down at x36-37,
     and the temple recedes hard at x27-29. The furrow matters more
     than it sounds: without it the forehead's brightest ramp step ran
     unbroken into the nose pass below and the two together rendered as
     one flat slab down the centre of the face.

     Second look, at the cell dump rather than the render: x36 and x37
     were an identical cell repeated down eight rows, and so were x38
     and x39 -- a value that varies only with x IS a vertical-striped
     field, however carefully each row was chosen. So the furrow
     wanders a column between rows, the crown sits a step darker than
     the brow because the dome tilts away up there, and the flush near
     the burning side is uneven cell to cell, the way heat in skin
     actually is.
  B  was the crown on the burning side. Removed in session 3: that
     block and duo3_right were two different rules writing the same
     cells, and the seam between them was one of the reasons the
     dissolve had no readable edge. Everything right of the front is
     now authored in one place, from the front.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

A_X, A_Y = 25, 3
A = [
    '0' * 8 + '344556878',              # 3 crown, tilted away: a step darker
    '0' * 5 + '234556667789',           # 4
    '0' * 3 + '23' + '345666657788',    # 5
    '0' * 1 + '1234' + '456666567799',  # 6 eminence at x30-32
    'm' + '1234' + '567666656889',      # 7
    'm' + '1234' + '566656567789',      # 8 hollow above the brow's inner end
]

cells = t.levels(A_X, A_Y, A, width=17)
t.paint(cells)
print('cells', len(cells))
