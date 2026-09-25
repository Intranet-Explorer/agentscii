"""duo3 session 2, pass 2: the mouth, rebuilt at cell level.

Magnified, the session-1 mouth was one black bar, eleven cells, dead
straight, square at both ends, with a lit lip under it. Four things were
missing and all four are cheap:

  CORNERS.  A mouth corner is a pocket, not the end of a line. It sits
  deeper than the line and it goes DOWN -- below the level the lower lip
  occupies. That is drawn here by taking the corner cell dark through
  BOTH half-rows (the line's row and the lip's row), at x33 and x43. The
  side effect is the one I actually wanted: the ends of the line now drop
  away from the middle, so the bar stops being a bar.

  THE UPPER LIP AS A MASS.  It was the same value as the cheek above it,
  which means there was no lip up there at all -- just a line drawn on
  skin. It goes a step darker than the skin it sits in, keeping the
  left-to-right grade, because the light is still the ember.

  THE LOWER LIP IS ROUND.  It graded monotonically left to right, which
  is a cylinder, not a lip. It now rises to its brightest a little past
  centre and falls again at x42-43, because that corner is turning back
  and away however much fire is over there.

  THE CREASE.  A shadow under the lower lip, shorter than the mouth and
  sitting under its middle only, so the lip has something to sit proud
  of. Kept to the top half of row 22 so it cannot read as a fourth
  horizontal bar -- the chin's lit surface is directly under it.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

U, D = '▀', '▄'
F = []

# --- row 20: the line where the lips meet, over the upper lip ---------
# ▓ over red at the corners: a 75%-black cell is a deeper pocket than the
# line itself is, and it still carries ink rather than going flat black.
F.append((33, 20, '▓', 0, 1))                      # near corner
for x, bg in zip(range(34, 43), [1, 1, 3, 3, 3, 3, 3, 9, 9]):
    F.append((x, 20, D, 0, bg))
F.append((43, 20, '▓', 0, 3))                      # far corner

# --- row 21: the lower lip's lit top surface over its body ------------
LIP = [
    (33, 0, 1),     # no lip at the corner -- the pocket continues down
    (34, 3, 1), (35, 3, 1), (36, 9, 1),
    (37, 9, 3), (38, 9, 3),
    (39, 11, 3), (40, 11, 3), (41, 11, 3),
    (42, 9, 3),     # falling off before the corner, not at it
    (43, 0, 3),     # far corner: a dark note against the lit cheek
]
for x, fg, bg in LIP:
    F.append((x, 21, U, fg, bg))

# --- row 22: the crease under the lip, over the chin's lit front ------
for x, fg, bg in [(35, 1, 3), (36, 1, 3), (37, 1, 3), (38, 1, 3),
                  (39, 1, 3), (40, 3, 9), (41, 3, 9)]:
    F.append((x, 22, U, fg, bg))

t.paint(F)
print('cells', len(F))
