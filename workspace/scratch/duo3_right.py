"""duo3 pass 5: the transforming side, x42..57, rows 7..22.

This is the subject, so it gets stated rather than shaded: the right
side of the face is coming apart. Near the centre the skin is only hot
(bright red, level 8-B). Toward the temple it splits into plates with
glowing cracks between them (C-F), the plates get smaller and the gaps
between them wider, and past the old silhouette there is nothing left
but embers with black between.

The right eye is not an eye. It is the hole the fire is coming out of,
with the dark rim of the socket still around it -- which is what keeps
it paired with the intact eye across the face instead of reading as a
wound somewhere on a cheek.

The gaps are placed so they drift diagonally out and down, following
one front, rather than alternating cell by cell -- a checkerboard of
holes reads as damage everywhere at once, which is a texture, not an
event with a direction.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 42, 7
#        x42 ........... x57
ROWS = [
    '899AABBC0B000000',   #  7 temple, first cracks
    '899AABC0B0C00000',   #  8
    '99AABC0B00B0C000',   #  9
    '9AABBD0C0B000C00',   # 10
    '9BCDDCB0C00B0000',   # 11 what is left of the brow, lit from beneath
    'A100EF01B0C00000',   # 12 socket: dark rim, fire inside
    'A10FFE01A00C0000',   # 13 the core sits where an iris would sit
    '932CDC2390B00000',   # 14 lower rim of the socket, lit from within
    'ABBAABC0B0C00000',   # 15 cheekbone still holding together
    '9ABBAC0B0C00B000',   # 16
    '99ABBD0C00B00000',   # 17
    '899ABC0B0C000000',   # 18
    '889ABC00B0000000',   # 19
    '..89ABC00B000000',   # 20 (x42-43 belong to the mouth pass)
    '..89AB0C00000000',   # 21
    '789B0C0000000000',   # 22 the jaw's right corner is already gone
]
cells = t.levels(X0, Y0, ROWS, width=16)
t.paint(cells)
print('cells', len(cells))
