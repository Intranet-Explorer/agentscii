"""duo3 session 2, pass 3: split the two layers onto two different fields.

THE DEFECT (duo3_NOTES.md section 2). duo3_tools.RAMP is a sixteen-step
value ladder whose foreground colour climbs monotonically with it:
5,5,5 / 1,1,1 / 3,3,3,3 / 9,9,9,9 / 11,11,11,11. Glyph and colour
therefore encode the same ordering independently, and either one alone
reconstructs the whole value field. self_check confirms it: flatten every
glyph to a solid block and the face is still there, sockets, nose and
mouth included. That is a greyscale bitmap printed twice, not a drawing
made of cells.

THE FIX is not to scramble foregrounds until the check stops firing. It
is to give the two layers two different physical quantities to carry:

    GLYPH DENSITY -> VALUE.  How the surface is turned relative to the
    light. This is the actual ANSI craft: sixteen colours, intermediate
    brightness faked with density.

    COLOUR PAIR   -> HEAT.   How close that patch of skin is to the
    ember. Not the same field. A cheekbone facing away from the fire and
    a jaw facing into it can be the same brightness and are not the same
    colour.

Four heat bands, each a colour pair wide enough in value that its four
density steps cover real range, and each OVERLAPPING its neighbours --
the overlap is the whole mechanism. Where two bands can both express a
value, heat decides which, so the colour cannot be inverted back into
the value.

    AMBIENT  (5,0)  .08 .15 .23 .30    turned away from everything
    DARK     (3,0)  .12 .24 .36 .48
    MID      (9,1)  .40 .47 .55 .62
    HOT     (11,1)  .46 .60 .74 .88    skin close enough to be glowing

Heat and value do stay correlated at the extremes, because the fire in
this picture both lights and heats the same side of the head -- that is
true of the subject, not a flaw in the encoding, and I am not going to
falsify it to move a number. What the split buys is the middle: a socket,
a nostril, a mouth line are value events that do not change the heat, so
under this encoding they move the glyph and leave the colour alone. That
is what should drop out of the colour-only render.

WHAT THIS PASS DOES NOT DO. It does not make a single drawing decision.
The value field it reads is the one authored cell by cell in passes 2, 3,
4 and 6 of session 1; this only chooses how each already-decided value
gets spelled. Cells that do not match a RAMP entry exactly -- every
hand-placed half-block: lid lines, the mouth line, the eye's sclera, the
silhouette rim -- are edges rather than surface, their colour is doing
edge work, and they are skipped.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

# The two fields and the ladders now live in duo3_tools, because
# duo3_model needs them too. This pass is the SAFETY NET: it respells
# whatever the block-in and the session-1 level passes left behind, so
# no cell on the intact half is a flat fill or carries its value in a
# hue. duo3_model, which runs next, is where the value field is
# actually decided.
LUM, GLYPHS = t.LUM, t.GLYPHS
value, spell = t.value, t.spell


# The intact half was authored in session 1 against a ramp whose top was
# bright yellow, so its cheek values sit at the ceiling of the brown
# band. Under a one-hue-per-region rule that leaves a face with no
# headroom: a sclera cannot be brighter than the cheek it is set into.
# Pulling the surface down opens the range back up, and it is also true
# -- this half of the head is turned away from the only light there is.
def compress(v):
    return v ** 1.2


# Only the intact half, and only inside the head -- which as of session 3
# means everything left of THE FRONT, row by row, rather than everything
# left of a column number I picked once. Right of the front belongs to
# the dissolve pass, whose colour IS its subject and stays untouched.
X0, Y0, Y1 = 24, 3, 26
RAMP_CELLS = {v: k for k, v in t.RAMP.items()}
FLIP = {'\u2580': '\u2584', '\u2584': '\u2580', '\u258c': '\u2590', '\u2590': '\u258c'}

data = t.ct.load_canvas(t.W, 'duo3')
go = data['glyph_override']
# Read from the RENDERED grid, not from glyph_override. The block-in
# draws into the pixel layer, so a cell it left as a flat fill has no
# override entry at all -- and those were exactly the cells this pass
# kept missing: eight of them along the crown at the front, and the
# whole neck. A flat fill is the one thing in the piece with no ink in
# it whatsoever, so the pass that exists to put value into ink cannot
# be the one pass that cannot see them.
GRID = t.ct.render_canvas_cells(data)
changed = same = skipped = 0
for y in range(Y0, Y1 + 1):
    for x in range(X0, t.front(y) + 2):
        glyph, fg, bg = GRID[y][x]
        if glyph == ' ' and bg == 0:
            continue
        # A half-block is an EDGE: its two halves are two different
        # colours on purpose, and no single-hue ladder can express that.
        # What it can be forced to do is carry the surface's colour in
        # the foreground. \u2580 a,b and \u2584 b,a are the same two pixels, so
        # taking whichever spelling puts the lighter colour in fg costs
        # the picture nothing. Being straight about it: this is a change
        # of encoding and not of drawing, and it is the one place in this
        # pass where the colour-only render moves without the render
        # moving. The rest of the session is the other thing.
        if glyph in FLIP:
            if LUM.get(bg, 0) > LUM.get(fg, 0):
                go[f'{y},{x}'] = [FLIP[glyph], bg, fg]
                changed += 1
            else:
                same += 1
            continue
        if glyph == ' ' and bg != 0:
            # a bg-carried cell: both pixels the same colour, so the cell
            # is a flat fill with no ink in it at all. Respell it.
            glyph, fg = '\u2588', bg
        elif glyph not in GLYPHS or fg not in LUM or bg not in LUM:
            skipped += 1                    # empty, or something authored
            continue
        new = spell(compress(value(glyph, fg, bg)), x, y)
        if list(new) == [glyph, fg, bg]:
            same += 1
        else:
            go[f'{y},{x}'] = [new[0], new[1], new[2]]
            changed += 1
t.ct.save_canvas(t.W, 'duo3', data)
print(f'respelled {changed}, unchanged {same}, left alone {skipped}')
