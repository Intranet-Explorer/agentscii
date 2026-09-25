"""duo3 session 2, pass 1: the left eye, rebuilt at cell level.

Magnified, the session-1 eye was two parallel black bars with a yellow
square between them. The diagnosis in duo3_NOTES.md: there is no sclera.
The whole aperture was black, so the iris had nothing to be dark against,
and the lash line and the aperture rendered as the same value, the same
width and the same square-ended rectangle. An eye reads because a dark
iris sits between two lit whites -- at this scale that is the only thing
in the socket worth the cells.

Four half-rows is the entire budget for an eye here, so each one has to
do exactly one job:

  row 12 top   lid skin, the fold above the lashes
  row 12 bot   LASH LINE, the darkest value in the piece
  row 13 top   THE APERTURE: sclera, iris, sclera
  row 13 bot   the lower lid's lit rim
  row 14 top   the lid's under-plane
  row 14 bot   the shadow the lid casts on the cheek

Grey (7 and 8) appears here and nowhere else in the face. That is
deliberate: sclera is a different material from skin and the one thing
that says so in a sixteen-colour palette of reds is desaturation. 8 on
the temple side, 7 on the side the ember is on, so the two whites are not
the same white.

The iris sits at x31..x33, off centre toward the fire. The eye that is
still an eye is looking at the half of its own face that is going.

The catchlight moved up a half-row, out of the middle of the aperture and
into the bottom of row 12, which is where a catchlight actually sits: the
top of the iris, tucked under the lid, on the light's side. It breaks the
lash line in exactly one cell, which is what a glint does.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

U, D, LH, RH, FULL = '▀', '▄', '▌', '▐', '█'

F = []

# --- row 12: lid skin over the lash line -----------------------------
# The lash is black under every cell of the opening except the one the
# glint takes. Lid skin above it warms toward the nose, which is the
# side the fire is on.
F.append((28, 12, D, 0, 1))                       # outer corner, lash starts
for x, fg in [(29, 1), (30, 1), (31, 1), (32, 3), (34, 3)]:
    F.append((x, 12, U, fg, 0))
F.append((33, 12, U, 3, 11))                      # the catchlight
F.append((35, 12, LH, 0, 3))                      # inner corner notch

# --- row 13: the aperture over the lower lid's rim -------------------
# fg is what you see through the opening, bg is the lit rim beneath it.
APERTURE = [
    (28, 0, 1),    # outer corner: the deep pocket where the lids meet
    (29, 8, 1),    # sclera, temple side, barely lit
    (30, 8, 3),
    (31, 0, 3),    # limbus -- the iris starts
    (32, 0, 3),
    (33, 0, 9),    # iris, and the rim under it is taking the ember
    (34, 7, 9),    # sclera, fire side: the brighter of the two whites
]
for x, fg, bg in APERTURE:
    F.append((x, 13, U, fg, bg))
F.append((35, 13, LH, 1, 3))                      # caruncle, warm not black

# --- row 14: the lower lid and the shadow it throws -------------------
# Deepest at the outer corner, furthest from the ember; lifting to a warm
# reflected tone by the nose.
for x, fg, bg in [(29, 0, 1), (30, 1, 3), (31, 1, 3), (32, 1, 3),
                  (33, 3, 9), (34, 3, 9)]:
    F.append((x, 14, D, fg, bg))

t.paint(F)
print('cells', len(F))
