"""duo3 pass 3: the nose, x35..44, rows 9..18.

This band was a bright vertical stripe: the left-half pass ran its value
ramp to the same brightest step in every row, and ten identical rows of
it read as a glowing column, not a form. The ramp was doing the work a
rule does. Replaced here with the actual anatomy, which is what breaks
the column: the ridge's lit edge is ONE cell wide and wanders, the eye
socket beside it drops back into shadow, the ball of the nose bulges
brighter at rows 15-16, and the tip's underside cuts a hard edge with
the cast shadow falling LEFT, away from the ember.

Second fix, after looking at the glyph-only render: the nose had
vanished there entirely. Its ridge was ONE colour step over its
surroundings at the same ink density, so with colour stripped the whole
feature disappeared -- the nose was being carried by hue alone. The
ridge is now a solid glyph flanked by lighter-density ones on both
sides, so the ridge line exists in ink as well as in colour.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 35, 9
#         x35 .. x44
ROWS = [
    '6556778889',   #  9 forehead above the root
    '6556778899',   # 10 brow shelf carries over the root
    '5556677889',   # 11 nose root, in the brow's shadow
    '.5566BA556',   # 12 upper bridge: lit edge x40, socket falls off at x42
    '.5566BA545',   # 13 the socket beside the bridge is the darkest step here
    '65666BA656',   # 14
    '65666BA767',   # 15 bridge widening toward the ball
    '45666BA767',   # 16 ball of the nose -- the bulge takes the light
    '2.3.....56',   # 17 nostrils and the tip's underside (features)
    '2345677567',   # 18 upper lip, with the nose's cast shadow at x35-36
]
cells = t.levels(X0, Y0, ROWS, width=10)

U, D = '▀', '▄'
F = [
    # the tip's underside: a hard edge mid-cell, lit on the ember side.
    (38, 17, U, 3, 1), (39, 17, U, 3, 1), (40, 17, U, 11, 1), (41, 17, U, 11, 1),
    # nostrils -- holes, so they sit in the lower half of the cell
    (36, 17, D, 0, 1), (42, 17, D, 0, 3),
    # the cast shadow off the nose, falling left across the cheek
    (34, 17, '▒', 1, 0), (33, 17, '░', 1, 0),
    (34, 18, '░', 1, 0), (35, 19, '▒', 1, 0),
]
t.paint(cells + F)
print('cells', len(cells) + len(F))
