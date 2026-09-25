"""duo3 pass 2: the intact half, worked cell by cell.

x 24..41, rows 9..18 -- brow ridge, eyebrow, eye, under-eye, cheekbone,
the left contour. Light comes from the ember on the far side of the
face, so this half is the SHADOW half: it turns away to the left and
dies into an ambient magenta rim at the silhouette.

Two layers of authorship, both per cell:
  LEVELS  an 11-step value ramp written one char per cell. Every step is
          a real glyph/colour pair (no cell where fg == bg), so the
          value is carried by ink density, not by a background fill.
  FEATURES  cells where a form edge falls INSIDE a cell -- lid lines,
          the brow's arch, the eye corners, the silhouette. Those get a
          half-block placed by hand, which is the only way the edge
          lands on a half-cell instead of stair-stepping.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 24, 9
# x24..x41, written in groups of six so a miscount is visible in source.
LEVELS = [
    '0m1124' '455666' '77779A',   #  9 forehead, temple hollow at x26-28
    '0m1245' '566677' '77789A',   # 10 brow ridge starting to shelf out
    '0m12..' '......' '.7789A',   # 11 eyebrow          (feature row)
    '0m12..' '......' '67899A',   # 12 eye              (feature row)
    '0m14..' '......' '67899A',   # 13 eye, lower lid   (feature row)
    '0m145.' '.....6' '7789AB',   # 14 under-eye shadow (feature row)
    '0m1456' '677766' '7789AB',   # 15 cheekbone -- widest point of the head
    '00m245' '566665' '6789AB',   # 16 cheek turning under the bone
    '00m124' '455666' '7789AB',   # 17 cheek toward the nose base
    '000m12' '445556' '6789AB',   # 18 jaw line begins
]
cells = t.levels(X0, Y0, LEVELS, width=18)

# --- features: edges that fall inside a cell -------------------------
U, L, LH, RH = '▀', '▄', '▌', '▐'   # top, bottom, left, right half
FULL = '█'

F = []
# left silhouette: ink on the RIGHT half of the edge cell, so the head's
# outline sits on a half-cell and the ambient rim is a line, not a step.
for y, x, fg in [(9, 25, 5), (10, 25, 5), (11, 25, 5), (12, 25, 5),
                 (13, 25, 5), (14, 25, 5), (15, 25, 13), (16, 26, 5),
                 (17, 26, 5), (18, 27, 5)]:
    F.append((x, y, RH, fg, 0))

# eyebrow, row 11: an arch. Tail low (lower half), peak riding up into
# the top half over the middle of the eye, inner end dropping again.
for x, g in zip(range(28, 37), [L, L, FULL, U, U, FULL, L, L, L]):
    F.append((x, 11, g, 1, 3))

# eye, row 12: brow shadow in the top half, the opening below it.
F.append((28, 12, L, 0, 1))                      # outer corner
for x in range(29, 35):
    F.append((x, 12, U, 1, 0))
F.append((35, 12, LH, 0, 3))                     # inner corner notch

# eye, row 13: the opening's lower edge against a lit lower lid.
F.append((28, 13, L, 1, 0))
for x, bg in [(29, 1), (30, 1), (31, 3), (32, 3), (34, 3)]:
    F.append((x, 13, U, 0, bg))
F.append((33, 13, U, 11, 3))                     # catchlight -- the ember,
#   reflected in the eye that is still an eye. It sits on the light's
#   side of the iris, not the middle.
F.append((35, 13, LH, 0, 3))

# row 14: the lower lid's own shadow, sitting low in the cell.
for x in range(29, 35):
    F.append((x, 14, L, 1, 3))

t.paint(cells + F)
print('cells', len(cells) + len(F))
