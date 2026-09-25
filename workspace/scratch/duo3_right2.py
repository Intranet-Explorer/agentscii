"""duo3 session 4: the burning side, given something to dissolve FROM.

The review: "Thirteen rows, same ramp, no vertical variation.
Charitably it's the head dissolving into embers, which the title
supports -- but a dissolve needs form to dissolve FROM, and this is a
gradient applied uniformly per row."

I said this myself at the end of session 2 and thought session 3 had
fixed it. It had not, and the reason is worth writing down because it
is a mistake I could make again. Session 3's fix was to measure the
plates from a stated edge -- d = x - front(y) -- instead of from the
left margin. That IS the right move and it is the difference between a
gradient and a structure. But front(y) only travels three cells over
the whole height of the head, so for a given d the rule produced very
nearly the same plate-and-gap sentence in every one of twenty-two rows.
I replaced a function of x with a function of d and both of them are
functions of ONE variable. The picture needed a second one.

duo3_tools.PROMINENCE is it: how far the flesh stood forward at the
burning edge, row by row, read across from the form duo3_model draws on
the intact side. Brow ridge 9, cheekbone 9, eye socket 2, temple hollow
3. Four things now take their size from it, and each one is a claim
about how a face comes apart rather than a knob:

  REACH -- how far the shed material carries. Bone standing proud of
    the fire throws its chips clear; a hollow sheds into itself. This is
    the one that matters most, because it is what turns the field's
    outer boundary from the block-in's circle into a profile of the
    head: it bulges seven cells past the old silhouette at the brow and
    the cheekbone and falls four cells short of it at the socket.
  PLATE SIZE -- a proud plane has more material in one piece.
  GAP -- and a hollow has more air between what is left of it.
  HEAT -- a plate that stood closest to the fire is still the hottest.

So rows 9-10 and 16-17 are big bright plates carrying a long way, rows
11-15 and 18-19 are small dim ones that stop early, and between them
there is a silhouette. That is the head, dissolving, instead of a ramp.

The crack and the socket are unchanged from session 3. The crack is the
one mark in the piece that runs the full height of the head and it
should not acquire variation; it is a parting, and a parting is a line.
"""
import math
import random
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

Y0, Y1 = 3, 24
XMAX = 66


def silhouette(y):
    """Right edge of the block-in's head mass, in cells, for this row."""
    best = 0.0
    for py in (2 * y, 2 * y + 1):
        for cx, cy, r in ((38, 20, 14), (44, 30, 8), (38, 34, 6), (38, 42, 6)):
            d = r * r - (py - cy) ** 2
            if d > 0:
                best = max(best, cx + math.sqrt(d))
    return best


reach = t.reach                         # duo3_bg has to agree with it


# Value by distance from the front (duo3_tools.RAMP keys, light to
# dark). Hottest right at the seam, because that is where the fire is
# still in contact with skin; embers by the time the plates are single
# cells.
COOL = 'FEEDDCCBBAA99888'


def val(d, lead, p):
    v = COOL[min(d, len(COOL) - 1)]
    i = t.RAMP_ORDER.index(v)
    if not lead:                      # plate body, one step back from its edge
        i -= 1
    i += round((p - 4.5) / 2.5)       # and the whole plate rides on prominence
    return t.RAMP_ORDER[max(0, min(len(t.RAMP_ORDER) - 1, i))]


# THE FRAGMENT (session 6). The defect that survived three rewrites of
# this pass, because all three were rewrites of its VALUES.
#
# The loop was `for y: while x <= stop: place a run of `plate` cells in
# row y`, with an independent random stream per row. So every mark on
# the burning side was ONE CELL TALL, and no two rows were related to
# each other by anything at all. Zoomed in, the whole side reads as
# horizontal scan lines -- a raster of a field rather than a picture of
# anything -- and the two long rows at the brow and the cheekbone read
# as lines shooting sideways out of the head, because reach() steps
# eleven cells between row 10 and row 11 and there was nothing to carry
# that vertically. I had been answering "no vertical variation" with
# more variation ALONG the row for three sessions.
#
# A chip off a skull has two dimensions. So a fragment is a small quad
# now: a width as before; a HEIGHT from the same prominence, because the
# brow ridge that throws its material furthest also comes off in the
# biggest pieces, and the socket sheds one-row flakes; and a RISE. What
# is still attached does not move. What came off goes UP, because the
# only light in this picture is a fire and a fire takes its material
# with it -- about a row for every three cells out, past the point where
# the surface stops being a sheet. That is what turns the outer boundary
# from a profile into a plume.
#
# Two things follow that a row-run could not do.
#
# A fragment that straddles rows can land its top and bottom edges
# MID-CELL: ▄ under the top, ▀ over the bottom, ink over black, so a
# chip in black air has a real boundary instead of a square cell corner.
# That spelling costs value -- half a cell of the brightest ink there is
# comes to 0.44 -- so it is only available where the body is dimmer than
# that, which is exactly the outer ember field and not the hot sheet at
# the seam. A sheet has no top edge anyway.
#
# And a fragment CLAIMS its footprint, so the row below does not
# regenerate through it. A big chip suppresses the wash underneath
# itself, which is the whole reason it stays one object instead of
# dissolving back into rows.
# Three, not six. The dissolve is only ten to sixteen cells deep at its
# widest, so a sheet zone of six swallowed nearly all of it and the
# quads came out h=1 anyway -- the old pass, reproduced exactly, by a
# constant. The seam's continuous skin is the first few cells and no
# more; the assert below is what caught it.
ATTACHED = 3


def _spell(v, h, j):
    """A fragment cell: ramp char, the fragment's height, its row in it."""
    g, fg, bg = t.RAMP[v]
    if h == 1 or 0 < j < h - 1:
        return g, fg, bg
    lvl = t.value(g, fg, bg)
    if lvl > 0.50:
        return g, fg, bg              # too hot to spell in half a cell
    ink = min((1, 3, 9, 11), key=lambda c: abs(0.5 * t.LUM[c] - lvl))
    return ('▄' if j == 0 else '▀'), ink, 0


cells = []
for y in range(Y0, Y1 + 1):
    # Clear every row's whole territory first, before any fragment is
    # placed. Without this a row whose reach has pulled IN leaves last
    # version's plates stranded past the new boundary, which is the
    # worst of both fields -- and it has to happen for ALL rows up front
    # now, because a fragment rises into rows above its own.
    for x in range(t.front(y) + 1, XMAX + 1):
        cells.append((x, y, ' ', 0, 0))

    # THE CRACK. Half a cell of black with the first plate's lit edge
    # against it -- a whole black column at this width reads as a drawn
    # border, half a cell reads as a parting. Where the socket has
    # opened it the seam is simply gone.
    if 12 <= y <= 14:
        cells.append((t.front(y) + 1, y, ' ', 0, 0))
    else:
        cells.append((t.front(y) + 1, y, '▐', 11 if 8 <= y <= 18 else 9, 0))

taken = set()
frags = []
for y in range(Y0, Y1 + 1):
    f, p = t.front(y), t.prom(y)
    rnd = random.Random(977 + y)
    edge, stop = silhouette(y), reach(y)

    x = f + 2
    while x <= stop:
        d = x - f
        # The gap used to grow at 0.45 a cell and the field is only ten
        # to sixteen cells deep, so the walk ran out of room after two
        # steps and every row was one wide plate at the seam and one
        # chip far out. Slower gap growth is not a density knob -- it is
        # what gives the outer field enough fragments to BE a field.
        w = round((4.2 - 0.40 * d) * (0.55 + p / 12.0)) + rnd.choice([-1, 0, 0, 1])
        gap = round((0.6 + 0.30 * d) * (1.4 - p / 10.0)) + rnd.choice([0, 0, 1])
        w, gap = max(1, min(5, w)), max(1, min(6, gap))
        if d <= ATTACHED:
            h, rise = 1, 0
        else:
            # Prominence sets how big a piece came off; distance breaks
            # it up again, because what is furthest out has been in the
            # fire longest. A hollow sheds one-row flakes at any range.
            # 0.25 and not 0.12. At 0.12 a brow-ridge chip was still
            # three rows tall at the very end of its reach, so the
            # biggest pieces in the picture were the ones that had
            # travelled furthest and been in the fire longest -- two
            # of them ended up standing in open air at the outer edge
            # reading as a pair of posts. Big near the bone, small far
            # out; that ordering is the whole claim.
            h = max(1, min(3, round(p / 2.5 - (d - ATTACHED) * 0.25)))
            rise = round((d - ATTACHED) * 0.3)
        # Past the head's own silhouette most of what came off is
        # already gone. That thinning used to drop random cells INSIDE a
        # plate, which is a hole in a chip; it drops whole fragments now,
        # because what is out there is fewer pieces, not holey ones --
        # and at the old 0.45 that took out half the outer field, which
        # is the only place in this pass where a chip is a separate
        # object at all. Thinning cells and thinning objects are not the
        # same rate.
        if x > edge + 1 and rnd.random() < 0.28:
            x += w + gap
            continue
        top = max(Y0, y - rise)
        foot = [(x + i, top + j) for i in range(w) for j in range(h)
                if x + i <= stop and top + j <= Y1
                and x + i > t.front(top + j) + 1]
        if not foot or 2 * sum(c in taken for c in foot) > len(foot):
            x += w + gap
            continue
        frags.append((x, top, w, h))
        # THE CHIP TURNS. val() is a function of the column only, so the
        # first version of this gave every row of a fragment the same
        # value and a three-row chip rendered as a solid domino -- a
        # worse mark than the dash it replaced, because a dash at least
        # did not claim to be a slab. A chip is a plate of bone at an
        # angle and the ember is at row 13: the row of it nearest that
        # row faces the fire most squarely and is the brightest, and
        # each row further away drops a step. Same light as the nose's
        # cast shadow, the throat and the contour -- there is only one.
        tilt = {j: -k for k, j in
                enumerate(sorted(range(h), key=lambda j: abs(top + j - 13)))}
        for cx, cy in foot:
            taken.add((cx, cy))
            v = val(cx - f, cx == x, p)
            i = t.RAMP_ORDER.index(v) + tilt[cy - top]
            if cx > edge + 1:
                i -= 3
            v = t.RAMP_ORDER[max(0, i)]
            cells.append((cx, cy, *_spell(v, h, cy - top)))
        x += w + gap

# --- the socket: the hole the front opened first ----------------------
# Unchanged. Dark rim carried on both half-rows above and below, so the
# opening has a lid-thickness the way the intact eye does, and the core
# sits where an iris would sit -- that pairing across the face is the
# whole reason this reads as a socket and not as a wound on a cheek.
SOCKET = [
    (44, 11, '▄', 9, 0), (45, 11, '▄', 9, 0), (46, 11, '▄', 11, 0),
    (47, 11, '▄', 9, 0), (48, 11, '▄', 9, 0),
    (44, 12, '·', 9, 0), (45, 12, '░', 11, 0), (46, 12, '█', 11, 9),
    (47, 12, '█', 11, 9), (48, 12, '▒', 11, 9), (49, 12, '·', 9, 0),
    (44, 13, '·', 9, 0), (45, 13, '▒', 11, 9), (46, 13, '█', 15, 11),
    (47, 13, '█', 15, 11), (48, 13, '█', 11, 9), (49, 13, '░', 11, 0),
    (44, 14, '°', 9, 0), (45, 14, '▀', 11, 9), (46, 14, '▀', 11, 9),
    (47, 14, '▀', 15, 11), (48, 14, '▀', 11, 9), (49, 14, '·', 9, 0),
    (45, 15, '▀', 9, 0), (46, 15, '▀', 11, 0), (47, 15, '▀', 11, 0),
    (48, 15, '▀', 9, 0),
]
cells += SOCKET

t.paint(cells)


def _check():
    """Two defects, as numbers.

    The outer boundary was the block-in circle in every row before
    session 4; if reach() stops tracking the head's form it goes back to
    being one.

    And every mark was one cell tall before session 6. A field of
    fragments that all come out h=1 is that pass again wearing this
    pass's code, and it would not look different from the outside until
    somebody zoomed in -- which is how it lasted three sessions. So:
    real quads, and real mid-cell edges to go with them.
    """
    r = [reach(y) for y in range(Y0, Y1 + 1)]
    circle = [int(max(silhouette(y), t.front(y) + 4)) for y in range(Y0, Y1 + 1)]
    spread = max(a - b for a, b in zip(r, circle)) - min(a - b for a, b in zip(r, circle))
    assert spread >= 10, spread
    assert reach(10) > reach(13) + 6, (reach(10), reach(13))   # brow vs socket
    # Five, and it is deliberately far under what the pass actually
    # makes. I tuned two parameters toward this number when it was set
    # at 25 and again at 10 before noticing what I was doing: an assert
    # I adjust the drawing to satisfy is a target, and I wrote down last
    # session that every one of these is only good as a detector of
    # ABSENCE. All-flat scores 0. That is the whole job of this line.
    tall = sum(1 for _, _, _, h in frags if h > 1)
    assert tall >= 5, tall
    landed = sum(1 for _, _, g, _, _ in cells if g in '▀▄')
    assert landed >= 10, landed
    return spread, tall, landed


if __name__ == '__main__':
    sp, tall, landed = _check()
    print('cells %d  undulation %d  fragments %d (%d span rows)  %d mid-cell edges'
          % (len(cells), sp, len(frags), tall, landed))
