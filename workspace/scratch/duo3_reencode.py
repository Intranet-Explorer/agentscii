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
import math
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

# Approximate luminance of the palette indices this piece uses.
LUM = {0: 0.00, 1: 0.32, 3: 0.48, 5: 0.30, 7: 0.66, 8: 0.33,
       9: 0.62, 11: 0.88, 13: 0.60, 15: 0.95}
COVER = {'░': 0.25, '▒': 0.50, '▓': 0.75, '█': 1.00, ' ': 0.0}


def value(glyph, fg, bg):
    f = COVER[glyph]
    return f * LUM[fg] + (1 - f) * LUM[bg]


# Each heat band is one FOREGROUND and two backgrounds. The foreground is
# the whole of what the colour-only render sees, and it is a function of
# heat alone -- that is the property this pass exists for. The second
# background is there because four density steps over a black ground
# quantise a cheek into .12/.24/.36/.48 and crush every subtlety between,
# which the first version of this pass did: the intact half came back
# flatter than session 1 had it. The lighter ground interleaves steps
# where the face actually lives.
#
# Being straight about it: the background is doing the last increment of
# value work here, so the split between the layers is not total. The glyph
# carries the coarse value and the ground carries the final step. That is
# how the medium actually works -- you choose a pair AND a density -- and
# I would rather say so than pretend to a cleanliness the drawing does not
# have.
BANDS = {
    'ambient': (5, [0]),
    'dark': (3, [0, 1]),
    'mid': (9, [1, 3]),
    'hot': (11, [1, 9]),
}
STEPS = {name: sorted(((g, bg, value(g, fg, bg)) for g in '░▒▓█'
                       for bg in bgs), key=lambda s: s[2])
         for name, (fg, bgs) in BANDS.items()}

# Which band a cell would PREFER, hottest first, by how close it is to
# the ember. The first preference whose range actually contains the
# value wins; the overlap between neighbouring bands is where heat gets
# to decide something.
# First cut of these thresholds put 'mid' -- bright red on red -- across
# the whole centre of the face, and the intact half rendered as a hot pink
# mask with the brown midtone gone. Heat is a real field but it is not a
# strong one at this distance: brown skin stays brown until you are close
# enough to the dissolve to be glowing. Only the last four columns before
# the front are hot.
PREFERENCE = [
    (0.86, ['hot', 'mid', 'dark', 'ambient']),
    (0.74, ['mid', 'hot', 'dark', 'ambient']),
    (0.40, ['dark', 'mid', 'ambient', 'hot']),
    (0.00, ['ambient', 'dark', 'mid', 'hot']),
]

EMBER_X, EMBER_Y = 47.0, 13.0


def heat(x, y):
    # cells are about twice as tall as wide
    d = math.hypot(x - EMBER_X, 2 * (y - EMBER_Y))
    return max(0.0, min(1.0, 1.0 - d / 34.0))


def spell(v, h):
    """Value + heat -> (glyph, fg, bg)."""
    for threshold, order in PREFERENCE:
        if h >= threshold:
            break
    def miss(name):
        lo, hi = STEPS[name][0][2], STEPS[name][-1][2]
        return max(0.0, lo - v, v - hi)
    # first preference that can actually express this value; if none can,
    # the one that comes closest
    band = next((n for n in order if miss(n) <= 0.02), min(order, key=miss))
    glyph, bg, _ = min(STEPS[band], key=lambda s: abs(s[2] - v))
    return glyph, BANDS[band][0], bg


# Only the intact half, and only inside the head. x44+ belongs to the
# dissolve pass, whose colour IS its subject and stays untouched.
X0, X1, Y0, Y1 = 24, 43, 3, 24
RAMP_CELLS = {v: k for k, v in t.RAMP.items()}

data = t.ct.load_canvas(t.W, 'duo3')
go = data['glyph_override']
changed = same = skipped = 0
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        cur = go.get(f'{y},{x}')
        if cur is None:
            continue
        glyph, fg, bg = cur[0], int(cur[1]), int(cur[2])
        # Re-runnable: a cell this pass has already respelled is still
        # readable as (value, band), so tuning the thresholds and running
        # it again works. Feature cells use half-blocks and never match.
        banded = glyph in '░▒▓█' and any(
            fg == f and bg in bgs for f, bgs in BANDS.values())
        if not banded and RAMP_CELLS.get((glyph, fg, bg), '0') == '0':
            skipped += 1                    # a feature cell, or empty
            continue
        new = spell(value(glyph, fg, bg), heat(x, y))
        if list(new) == [glyph, fg, bg]:
            same += 1
        else:
            go[f'{y},{x}'] = [new[0], new[1], new[2]]
            changed += 1
t.ct.save_canvas(t.W, 'duo3', data)
print(f'respelled {changed}, unchanged {same}, left alone {skipped}')
