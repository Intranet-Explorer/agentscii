"""duo3 session 3: the socket, rebuilt so the DARK is made of ink.

The measurement that forced this. self_check's colour-only render --
every glyph flattened to a solid block, hue alone -- still came back a
legible face after session 2, and it read MORE clearly than after
session 1, because I had given the eye a grey sclera and the mouth a
yellow lip. Feature work that arrives as colour work is the rejection
this project keeps collecting, verbatim: "remove the color and nothing
survives".

The cause here was exact. The lash line was fg 0 on bg 0 and the sclera
was fg 7 and 8. Black and grey are not in this face's palette for any
physical reason; they were there because I wanted those cells dark and
those cells light and I reached for a hue to say so. A shadow under a
brow is not a different colour of skin. It is the same skin with less
light reaching it, which in this medium is LESS INK.

So the whole socket is now spelled in ONE foreground -- 3, the brown the
cheek beside it is spelled in -- and every value in it is a glyph
choice:

    · 3,0   .02   the corner pockets, as near black as a cell gets
    ░ 3,0   .12   the socket floor
    ▒ 3,0   .24   brow hair
    ▓ 3,0   .36
    █ 3,0   .48   sclera: the brightest ink in the piece's dark half
    ▀ 3,0         lash line -- black in the BOTTOM half of the cell,
                 skin in the top, so the line lands mid-cell and the
                 cell's colour is still skin

Flatten every glyph here and the socket becomes the same brown as the
cheek, which is the point. The eye survives the glyph-only render and
disappears from the colour-only one -- that is the way round it is
supposed to be.

The catchlight keeps its yellow. It is the ember reflected in a wet eye:
that cell IS a colour event, it is one cell, and I would rather leave
one honest one than launder it.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

U, D, LH, RH = '▀', '▄', '▌', '▐'
DOT, L1, L2, L3, FULL = '·', '░', '▒', '▓', '█'
SK = 3                                   # the one hue in this region

F = []

# --- row 11: the eyebrow, an arch --------------------------------------
# Tail low, peak riding up over the middle of the eye, inner end dropping
# again. Where the hair sits in the BOTTOM half the cell is ▀ (skin above,
# hair below); where it rides into the top half it is ▄.
# L1 rather than L2 where the whole cell is hair: at .12 it is a quarter
# of the brow ridge's value directly above it, which is the contrast the
# socket hangs from. At .24 it was a soft band and the brow read as a
# smudge.
for x, g in zip(range(28, 37), [U, L1, L1, D, D, L1, L1, U, U]):
    F.append((x, 11, g, SK, 0))

# --- row 12: lid skin over the lash line --------------------------------
F.append((27, 12, DOT, SK, 0))                    # outer corner pocket
for x in [28, 29, 30, 31, 32, 34]:
    F.append((x, 12, U, SK, 0))
F.append((33, 12, U, SK, 11))                     # the catchlight
F.append((35, 12, RH, SK, 0))                     # inner corner notch

# --- row 13: the aperture over the lower lid's rim ----------------------
# Top half is what you see through the opening, bottom half is the lit
# rim beneath it. Sclera is a full cell of ink; the iris is a cell whose
# top half has none.
# The iris is a WHOLE dark cell, not the dark half of one. Half a cell
# of black between two half cells of light is a line; a whole one is a
# pupil, and at four cells across it is the only chance this eye has.
# sclera, limbus, PUPIL, limbus, sclera. Three cells of black was a
# hole; one is an eye looking at you, and the two mid cells either side
# are what makes the one dark cell read as round.
APERTURE = [(28, L1), (29, FULL), (30, FULL), (31, L2), (32, DOT),
            (33, L2), (34, FULL)]
for x, g in APERTURE:
    F.append((x, 13, g, SK, 0))
F.append((35, 13, RH, SK, 0))                     # caruncle

# --- row 14: the lower lid and the shadow it throws ---------------------
# Deepest at the outer corner, furthest from the ember; the bottom half
# of each cell is skin, the top half is the shadow the lid casts on it.
# bg 1 rather than 0: the shadow the lid throws is a shadow, not a hole,
# and with black here the socket became one black pool with the eye
# somewhere in it.
F.append((28, 14, DOT, SK, 0))
for x, bg in [(29, 0), (30, 1), (31, 1), (32, 1), (33, 1), (34, 1)]:
    F.append((x, 14, D, SK, bg))

# --- row 15: the socket floor, so the eye sits in a recess --------------
# Without this the socket was three dark rows with full-value cheek
# immediately under them, which reads as a mask, not a hollow.
for x, g in zip(range(28, 34), [L1, L1, L2, L2, L3, L3]):
    F.append((x, 15, g, SK, 0))

t.paint(F)
print('cells', len(F))
