"""duo3 session 3: the mouth, respelled the same way as the socket.

Session 2 gave this mouth corners, a vermilion border and a crease, and
all three were real improvements -- but they arrived as fg 0 for the
line and fg 11 for the lower lip, so in the colour-only render the mouth
was a black bar with a yellow bar under it, which is to say the mouth
was still legible with every glyph thrown away.

Same correction as the socket: one foreground (3), value carried by
ink. The lower lip is bright because it is a FULL cell; the line between
the lips is dark because it is the bottom half of a cell whose top half
is skin; the corners are dark because they are ·, two percent ink. The
lip's crown still sits a little past centre and still falls off before
the corner rather than at it -- that shape is what makes it a lip
instead of a cylinder, and none of it depended on the hue.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

U, D = '▀', '▄'
DOT, L1, L2, L3, FULL = '·', '░', '▒', '▓', '█'
SK = 3

F = []

# --- row 20: the line where the lips meet, over the upper lip ----------
# The line is the bottom half of the cell. It is broken at x37 by the
# tubercle of the upper lip, which is the one place a mouth line is
# interrupted, and it deepens to a full dark cell at both corners.
LINE = [(33, DOT, 0), (34, L2, 0), (35, U, 0), (36, U, 0), (37, L3, 0),
        (38, U, 0), (39, U, 0), (40, U, 0), (41, U, 1), (42, L2, 0),
        (43, DOT, 0)]
for x, g, bg in LINE:
    F.append((x, 20, g, SK, bg))

# --- row 21: the lower lip -------------------------------------------
# Crown past centre at x37-39 (full cells, the most ink in the lower
# face); a lit top edge over a dark under-turn toward each corner; the
# pocket at both ends carried down from row 20 so the ends of the mouth
# drop away instead of squaring off.
LIP = [(33, DOT, 0), (34, L2, 0), (35, U, 1), (36, U, 1), (37, FULL, 1),
       (38, FULL, 1), (39, FULL, 0), (40, U, 0), (41, U, 0), (42, L2, 0),
       (43, DOT, 0)]
for x, g, bg in LIP:
    F.append((x, 21, g, SK, bg))

# --- row 22: the crease under the lip, over the chin's lit front -------
for x, bg in [(35, 1), (36, 1), (37, 1), (38, 0), (39, 0), (40, 1), (41, 1)]:
    F.append((x, 22, D, SK, bg))

t.paint(F)
print('cells', len(F))
