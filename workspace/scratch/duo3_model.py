"""duo3 session 3: the intact half's VALUE, authored by hand.

What forced this pass. Once hue was locked to heat, the intact half went
flat -- not because the encoding was wrong but because the encoding was
the only thing that had ever been carrying the modelling. Session 2's
note said as much and I did not believe how completely until I looked at
it: "the intact half is a continuous dithered gradient with almost no
landed edges, and a face is not a gradient: it is a few planes meeting
along lines." With the hue ramp taken away there was a head-shaped mass
and no head in it.

So this is the pass of its own that I said this needed. Ten rungs of
value, one character per cell, written out as a picture of the face's
LIGHT rather than of its colour. Every rung becomes a glyph density in
whatever hue the heat field has at that cell, so none of it can leak
back into colour.

The planes, and they are the whole content of the grid below:

  the crown tips away from the light and loses two rungs to it
  the temple hollow, x27-x29, is the darkest skin on the head
  the BROW RIDGE shelves out at rows 9-10 and is the brightest thing
      on the upper face -- it is what the socket has to be dark against
  the socket floor drops three rungs under it (rows 11-15)
  the CHEEKBONE is the widest and brightest plane on this side
      (rows 15-17), and the hollow under it at row 18 takes back two
      rungs, which is the line that makes a cheek a cheek
  the NOSE has three planes, not a ramp: a dark near side at x36-x38,
      a one-cell lit ridge at x39-x40, and a far slope that falls a
      rung before the face starts climbing again toward the fire
  the nose's cast shadow falls LEFT across the cheek at rows 17-19
  the chin's front plane is lit, the jaw's underside is not
  the neck is the darkest thing below the head, and the jaw's shadow
      lies across it

Rows where a feature pass owns the cells -- the eye at rows 11-15, the
mouth at rows 20-22 -- are left blank here rather than authored twice.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 24, 3
#      x24                 x46  x49
#      |                     |    |
G = [
    '.........23334445556......',   #  3 crown, tipped away
    '......12223334445556......',   #  4
    '....11223334445556667.....',   #  5
    '..112233344455566677766...',   #  6
    '.11223334445556667777.....',   #  7
    '.11122344555666777788.....',   #  8 brow starting to shelf
    '.112345566666667778888798.',   #  9 BROW RIDGE
    '.1124566777766677788888798',   # 10 brow ridge, most prominent
    '.112.........457877888....',   # 11 eyebrow (eye pass) | nose ridge x40
    '.11.........445787788.....',   # 12 eye  | nose: dark side, lit ridge
    '.111........44578788......',   # 13 eye
    '.112.......4445787788.....',   # 14 eye
    '.123......544578778888....',   # 15 eye socket floor | cheekbone begins
    '..24566666654578887899768.',   # 16 CHEEKBONE, and the ball of the nose
    '..134555544457877779986478',   # 17 nose's cast shadow falls left
    '...12333443345566787898...',   # 18 THE HOLLOW under the cheekbone
    '....1233444455556678788...',   # 19 jaw line, upper lip
    '....12334...........787...',   # 20 mouth pass owns x33-x43
    '....12234...........8788..',   # 21
    '........344.......7788....',   # 22
    '.........34555666777......',   # 23 chin, lit front plane
    '..........234445556.......',   # 24
    '...........1112222333.....',   # 25 neck, with the jaw's shadow on it
    '...........1111222233.....',   # 26
]

cells = [c for c in t.ink(X0, Y0, G, width=26) if c[0] <= t.front(c[1])]

# THE LIP, one cell wide, with a groove behind it. The last intact cell
# in every row goes two rungs above the grid and the cell BEHIND it one
# rung below. Skin at the edge of a break faces the fire more squarely
# than the surface behind it does; the groove is what keeps the lip a
# line instead of a two-cell bar, which is what it was when both cells
# got lifted and the whole front rendered as a solid column.
lift = {}
for y in range(Y0, Y0 + len(G)):
    row = G[y - Y0]
    f = t.front(y)
    for x, bump in ((f, 2), (f - 1, -1)):
        c = x - X0
        if 0 <= c < len(row) and row[c] != '.':
            lift[(x, y)] = max(0, min(9, int(row[c]) + bump))
cells = [c for c in cells if (c[0], c[1]) not in lift]
cells += [(x, y, *t.spell(t.RUNG[r], x, y)) for (x, y), r in lift.items()]

t.paint(cells)
print('cells', len(cells))
