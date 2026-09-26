"""duo3 session 7, second pass: the landed edges on the far side.

duo3_shadow lays the VALUE of the dark half. It cannot lay its edges,
because a value grid has one number per cell and an edge does not fall
on cell boundaries -- it falls inside them. Every mark below keeps the
value duo3_shadow decided and changes only WHERE IN THE CELL the ink
sits, which is the whole difference between a run of ▒ and a ridge.

This is my own NEXT line from last session, carried over and pointed at
the shadow side:

    the horizontal banding at rows 9-10, 16-18 and 21-24, fixed the way
    both vertical walls were fixed -- make the run's glyph carry where
    the surface crosses the cell boundary while its value stays put, so
    brow, arch and jaw read as ridges seen edge-on rather than as bars.

The rule, from METHOD.md and unchanged:

    A shade char says HOW MUCH light this cell returns. A half-block
    says WHERE INSIDE THIS CELL the boundary is. Reach for a half-block
    when you know which side of the cell the ink belongs on.

So the question for every mark here is not "how bright" -- that is
already answered -- but "which way is this surface crossing this cell".
Two adjacent rows of the same value with the ink landed on opposite
halves are a ridge. Two adjacent rows of the same value with the ink
scattered through both are a bar. That is the entire banding defect and
this is the entire fix.

Each entry is (x, y, glyph, why). The rung comes from duo3_shadow's
picture, untouched, so nothing here can brighten anything.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t
import duo3_shadow as sh

U, D, L, R, F = '▀', '▄', '▌', '▐', '█'

MARKS = [
    # -----------------------------------------------------------------
    # THE BROW RIDGE, rows 9-10. The crest starts high at the glabella
    # and DESCENDS as it runs out to the lateral orbital angle -- over
    # five columns it drops a full row. Written as two bars it is two
    # bars; written as ink that moves down through the cell it is the
    # ridge it actually is.
    (43, 9, U, 'crest still high in the row: ink on the roof of the cell'),
    (44, 9, D, 'and now it has dropped to the floor of row 9'),
    (45, 9, D, ''),
    (43, 10, U, 'row 10 catches what row 9 dropped: same ridge, one row on'),
    (44, 10, U, ''),
    (45, 10, U, 'the lateral orbital angle, where the crest rolls over'),

    # -----------------------------------------------------------------
    # THE FAR SOCKET, rows 11-14. Almost nothing resolves inside it and
    # it is still a socket, because a socket is a hole WITH A RIM. The
    # rim is the only thing drawn.
    #
    # The aperture itself takes no mark, and the reason is a property of
    # the medium worth writing down: a half-block is half a cell of ink,
    # so the darkest value it can express is half its foreground's -- in
    # the cool band, 0.16. The aperture sits at 0.11 and the temple at
    # 0.06. THE DARKEST CELLS IN A PIECE CANNOT CARRY A LANDED EDGE.
    # Their edge has to be drawn on the lit cell beside them, which is
    # what the rim and the margin below are doing.
    (47, 11, R, 'the lateral orbital rim -- a half-cell wide, which is'),
    (47, 12, R, 'what a narrow bony ridge is at this scale'),
    (47, 13, D, 'and there it turns down into the infraorbital margin'),
    (45, 14, U, 'THE INFRAORBITAL MARGIN: the socket\'s floor, landed on'),
    (46, 14, U, 'the top of the row so the dark of row 13 sits ON it'),
    (47, 14, U, ''),
    (48, 14, D, 'and the margin drops away toward the arch'),

    # -----------------------------------------------------------------
    # THE ZYGOMATIC ARCH, rows 16-17. The single most important mark in
    # this session: the crest of the arch turns far enough back that it
    # sees the fire again, and that is what proves the head has a far
    # side rather than stopping where the light does. It is a BRIDGE of
    # bone with air under it, running back and down, so it crosses the
    # row-16/17 boundary and must be drawn crossing it.
    (49, 16, U, 'the crest comes up into row 16 off the cheek, and x50 is'),
    #                 left alone: it is the one cell the arch FILLS, the
    #                 brightest thing on the dark side, and a half-block
    #                 there would say the bone stops halfway across it.
    (51, 16, D, 'and immediately starts down: ink on the floor of the row'),
    (50, 17, U, 'row 17 takes it up again -- these two half-blocks meet'),
    (51, 17, U, 'across the boundary and read as one bar of bone, not two'),
    (52, 17, D, 'the arch\'s back end, dropping toward the ear'),
    (53, 17, D, 'the arch is a BRIDGE with air under it, and rows 17-18'),
    (51, 18, U, 'are the only place in the piece that says so'),

    # -----------------------------------------------------------------
    # THE FAR SILHOUETTE, rows 3-26. Not a contour line: at every row
    # this is the cell the bone stops INSIDE, so the glyph says which
    # part of that cell is still head. Its weight comes from
    # PROMINENCE -- the same table that drives the left contour, because
    # a brow ridge and a cheekbone are the width of a skull and not a
    # feature of one side of it.
    #
    #   prom >= 7   heavy bone turning hard: it fills the OUTER half of
    #               its last cell, so the edge lands as far out as the
    #               cell can put it.  ▐
    #   prom 4-6    the edge falls inside the cell, bone on the left. ▌
    #   prom <= 3   the form is hardly turning, so there is hardly a
    #               silhouette: NO MARK, the dither just stops.
    #
    # The first version of this pass put ▌ on nineteen of twenty-four
    # rows and rendered as a dashed vertical line down the right of the
    # head -- one glyph down a whole edge, which is a ruler however
    # carefully each cell was chosen, and the same defect session 5 took
    # out of the left contour.
    (45, 3, D, 'the crown runs HORIZONTALLY here -- 45 to 47 in one row'),
    (47, 4, L, 'prom 5: the edge falls inside this cell, bone on the left'),
    (48, 5, L, ''),
    (49, 6, L, ''),
    (50, 7, L, ''),
    #    ROW 8 TAKES NO MARK. prom 3, the temple fossa -- the skull is
    #    barely turning there, so there is barely a silhouette, and the
    #    dither simply stops. An edge drawn where the form does not turn
    #    is the ruler line I took out of the left contour in session 5.
    (51, 9, R, 'prom 8, the parietal eminence: heavy bone turning hard,'),
    (51, 10, R, 'so the bone fills the OUTER half of its last cell'),
    #    ROWS 11-14 TAKE NO MARK. prom 2-3 the whole way down: the
    #    temporal fossa pinching the cranium in. Four soft rows between
    #    two hard ones is what makes either of them read as hard.
    (52, 15, L, ''),
    (53, 16, R, 'prom 8, the arch: the widest point of the whole head'),
    #    ROW 19 TAKES NO MARK, prom 3.
    (50, 20, L, ''),
    (50, 21, L, ''),
    (49, 22, L, 'THE ANGLE OF THE JAW -- a corner, and drawn as one'),
    (46, 25, L, 'the neck comes back out from under it'),
    (46, 26, L, ''),

    # -----------------------------------------------------------------
    # The rest of the bone that crosses a cell. Nothing here is new
    # form -- each is a place duo3_shadow's picture already says a
    # surface turns, written down as WHERE in the cell it turns.
    (48, 7, R, 'THE TEMPORAL LINE: a ridge running down the side of the'),
    (48, 8, D, 'and down -- x47 alongside it is the temple itself, too'),
    #                 dark to carry a half-block at all (see above)
    (49, 15, R, 'where the zygomatic arch starts off the cheekbone'),
    (48, 16, U, 'and climbs into row 16 to become the crest'),
    (50, 18, U, 'the arch\'s underside, two cells of it'),
    (44, 18, U, 'the hollow under the cheekbone: its roof'),
    (42, 20, D, 'the far end of the upper lip, turning down'),
    (43, 21, D, 'the corner of the mouth -- a fold, so it has a side'),
    (47, 22, D, 'THE LOWER BORDER OF THE MANDIBLE leaves the angle here'),
    (46, 23, D, 'and runs forward and down'),
    (45, 23, D, 'to meet the chin, which is where row 24 picks it up'),
    (44, 25, U, 'the jaw\'s shadow landing on the neck: it has a top edge'),
    (45, 25, U, ''),
]


def cells():
    out = []
    for m in MARKS:
        x, y, g = m[:3]
        r = m[4] if len(m) > 4 else sh._v(y, x)
        assert r is not None, f'nothing at {x},{y} to land'
        out.append((x, y, *t.land_lit(t.RUNG[r], x, y, g)))
    return out


def _check():
    import collections
    rows = t.ct.render_canvas_cells(t.ct.load_canvas(t.W, t.SLUG))

    # 1. Every mark kept its value. This pass is allowed to move ink
    #    inside a cell and nothing else -- if it can also brighten, it
    #    is a second value pass wearing a half-block.
    for m in MARKS:
        x, y = m[0], m[1]
        want = t.RUNG[m[4] if len(m) > 4 else sh._v(y, x)]
        got = t.value(*rows[y][x])
        assert abs(got - want) <= 0.10, (x, y, round(got, 3), round(want, 3))

    # 2. The far silhouette is not one glyph repeated. A single glyph
    #    down an edge is a ruler line however carefully it is placed.
    sil = [rows[y][t.far(y)][0] for y in range(3, 27)]
    assert len(set(sil)) >= 4, sil

    # 3. THE BANDING TEST, stated the way the defect was reported: at
    #    the brow, the arch and the jaw, the two rows the reviewer read
    #    as bars must no longer be the same sentence as each other.
    for a, b in ((9, 10), (16, 17), (21, 22), (23, 24)):
        wa = ''.join(c[0] for c in rows[a][41:54])
        wb = ''.join(c[0] for c in rows[b][41:54])
        assert wa != wb, (a, b, wa)

    # 4. A ridge crosses the row boundary. At the arch and at the brow
    #    there is a column where the lower half of one row and the upper
    #    half of the next are both ink -- which is a surface passing
    #    between two cells, and is the thing a bar cannot do.
    assert sum(len(m) > 4 for m in MARKS) <= 2, 'this pass is moving ink, not adding it'
    joins = [(x, y) for x in range(41, 54) for y in range(3, 26)
             if rows[y][x][0] == D and rows[y + 1][x][0] == U]
    assert len(joins) >= 3, joins
    assert any(y == 16 for _x, y in joins), 'the arch does not cross the boundary'


if __name__ == '__main__':
    n = t.paint(cells())
    _check()
    print('landed %d edges; checks passed' % n)
