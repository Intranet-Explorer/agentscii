"""duo3 pass 7: background base tone, plus embers off the dissolve.

STYLE.md's rule for backgrounds is base tone first, texture on top --
marks straight onto black read as streaks on black, not as air. So this
pass is the base tone only, and it is the one place in the piece where a
computed field is the right tool: the light falls off from the burning
side the way light does, and hand-placing 500 background cells to
approximate an inverse-square would be worse, not more authored.

The first version of this covered the whole canvas in a lavender oval
that competed with the face -- a computed field is the right tool only
while it stays a base TONE, and that one had become a second subject.
It is much tighter now, and it does not exist at all on the dark side.

SESSION 6, and this is the pass that was wrong the whole time. The
review has rejected the right third three times in three vocabularies:
"a gradient applied uniformly per row", "a dissolve needs form to
dissolve FROM", "a structureless wash, roughly 40% of the subject's
bounding box doing no drawing work". I spent sessions 3, 4 and 5
answering all three on duo3_right2, the dissolve -- and duo3_right2
stops at reach(y), x47 to x60. Everything from there out to x68 was
THIS pass: concentric rings of dark red around the ember, thirteen
columns wide, on an eighty-column canvas. The structureless wash was
never the dissolve. It was the background, and I had been tuning the
wrong thing since session 3.

So the rings are gone and what replaces them is a MARGIN: a band that
follows the dissolve's own outer boundary, a few cells deep, and then
black. It is deeper at the brow and the cheekbone and shallow at the
socket, from the same PROMINENCE as everything else on this side --
air that has more burning material in it is brighter air. Two things
fall out of that which the rings could never do: the head gets a
SILHOUETTE against negative space on its burning side for the first
time in six sessions, and the hand-placed embers now sit in black air
instead of in a haze the same colour as themselves.

Two things keep it from being a clean set of rings:
  - the head OCCLUDES it. Cells to the left of the face get knocked
    down a band, because the head is between them and the only light
    source in the picture.
  - the embers are hand-placed, not scattered by the field. They rise
    and drift right off the temple, which is where the dissolve is
    actually shedding, and they thin out with height.

Only cells that are still empty black get written, so nothing here can
touch the face.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

EMBER_X, EMBER_Y = 47.0, 13.0      # the socket -- the piece's only light
HEAD_L, HEAD_R = 24, 52

def env(y):
    """The plume's outline, not one row's. Session 6.

    The margin was measured out from t.reach(y), which is what each row
    of material does on its own -- and reach() steps ELEVEN cells
    between row 10 and row 11, brow ridge to eye socket. So the lit air
    jumped eleven cells too, and the two prominent rows read as a pair
    of horizontal dashes flung out sideways with black above and below
    them. Air does not have an eleven-cell step in it. Glowing air is a
    continuous medium and it takes the shape of the plume AS A WHOLE, so
    this is a cone: the furthest any row within two rows of here throws
    its material, less two cells for every row of separation. The brow
    and the cheekbone still bulge -- they are still doing the driving --
    but the bulge now has a shoulder instead of a cliff.
    """
    return max(t.reach(min(24, max(3, y + dy))) - 2 * abs(dy)
               for dy in (-2, -1, 0, 1, 2))


grid = t.grid(0, 0, 80, 28)
cells = []
for y, row in enumerate(grid):
    for x, (ch, fg, bg) in enumerate(row):
        if not (ch == ' ' and bg == 0):
            continue                         # occupied -- leave it alone
        # The head is between this light and everything on its far
        # side, so there is no glow over there at all -- the intact
        # half keeps the dark it was modelled against.
        if x < HEAD_L + 16 and 1 <= y <= 26:
            continue
        # AND no glow anywhere inside the dissolve. The field has to
        # end against black or its gaps are not gaps -- they are a
        # slightly darker lavender, and the face simply fades into the
        # air it is supposed to be leaving. Session 4: this was a flat
        # front+11 and the dissolve now reaches past that at the brow
        # and the cheekbone, so it asks reach() where the row ends.
        if 3 <= y <= 24 and x <= env(y) + 2:
            continue
        # THE MARGIN. Depth measured out from where this row's shed
        # material actually stops -- not a radius from the ember, which
        # is what made it a set of rings. The brow ridge and the
        # zygomatic arch throw the most material clear, so the air
        # outside them is the brightest and the band is deepest there;
        # the socket sheds almost nothing and its margin is two cells.
        # Depth off the same cone, not off this row's prominence alone.
        # Smoothing only the margin's INNER edge left the outer one
        # stepping six cells between the brow and the socket -- the same
        # cliff, moved four cells right and no less of a horizontal line
        # for having been half fixed.
        yy = min(24, max(3, y))
        deep = max(t.prom(min(24, max(3, yy + dy))) - abs(dy)
                   for dy in (-2, -1, 0, 1, 2))
        depth = 5 + round(deep - 4.5)
        if not 3 <= y <= 24:
            depth = depth // 2            # off the top and bottom of the head
        d = x - (env(yy) + 3)
        if not 0 <= d < depth:
            continue
        if d < depth * 0.35:
            cells.append((x, y, '\u2592', 1, 0))
        elif d < depth * 0.7:
            cells.append((x, y, '\u2591', 1, 0))
        elif (x + y) % 2 == 0:
            # The outermost band is thinned on a checker AND spelled in
            # the dimmest glyph there is: \u00b7 over black is four percent
            # ink, a sixth of \u2591, so it is a real step further out
            # without being a step into another hue. It was \u2591 in
            # magenta, which is the violet the review caught -- I had
            # reached for a colour to say 'less light' when less ink
            # says it in the palette the fire is already in.
            cells.append((x, y, '\u00b7', 1, 0))

# Embers off the temple: a plume, not a scatter. Bright and dense where
# they leave the face, cooling and thinning as they rise.
EMBERS = [
    (54, 6, '▒', 9), (56, 5, '░', 9), (55, 8, '▓', 11),
    (58, 4, '░', 1), (57, 7, '▒', 9), (59, 6, '░', 9),
    (53, 3, '░', 9), (55, 2, '░', 1), (60, 3, '░', 1),
    (58, 10, '▒', 9), (61, 8, '░', 9), (60, 11, '░', 1),
    (56, 12, '▓', 11), (59, 14, '▒', 9), (62, 12, '░', 9),
    (57, 16, '▒', 9), (61, 17, '░', 1), (55, 19, '░', 9),
    (58, 20, '░', 1), (54, 22, '░', 1), (63, 5, '░', 1),
    (64, 10, '░', 1), (62, 20, '░', 1), (52, 25, '░', 1),
]
cells += [(x, y, ch, fg, 0) for x, y, ch, fg in EMBERS]

t.paint(cells)
print('cells', len(cells))
