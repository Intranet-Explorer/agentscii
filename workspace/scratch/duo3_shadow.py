"""duo3 session 7: the far side of the skull, and the air behind it.

The dissolution is dropped. Four attempts over three sessions failed on
that region for one reason, and it is written in METHOD.md: a dissolve
is defined by what ISN'T there, so there is nothing behind the edge to
decide about, and every attempt collapsed back into a function
evaluated over a region -- the exact defect this whole run exists to
escape. A shadowed skull has something behind it. Every cell below is a
question with a real answer: what part of the head is this, which way
does it face, how much of the fire does it still see.

THE REGION THIS PASS OWNS: x >= 41, every row. Stated once, here, and
used for BOTH the clear and the write -- the bug I hit twice in session
6 was a pass that redrew a region without owning it, so the vacated
cells kept their old ink and the new ink went on top.

x41 is the left boundary and not x44, because the bright band the
reviewer called a pillar starts there: duo3_model's grid is pegged at
rungs 7-8 for its last six columns in almost every row, and the char
lip sat on top of that. Those six columns were the head's front while
the fire was eating it. They are now the last of the lit surface before
the head turns away, so they have to fall.

WHAT IS IN THE PICTURE BELOW, going outward from x41 in each row.

  rows 3-8    the crown and the forehead going over and back. The fire
              is LOW, so the top of the skull takes it at a grazing
              angle and there is no highlight up here -- it just falls.
  rows 7-13   THE TEMPLE. The deepest dark in the piece, rung 0, and the
              only rung 0 anywhere in it: the temporal fossa is a shell
              of bone over air, standing furthest back, shadowed by the
              brow in front of it and the parietal above it.
  rows 9-10   THE BROW RIDGE crest, the last thing up here the fire
              still reaches, ending at the lateral orbital angle where
              it rolls over into the temple. Bright, then nothing, in
              two cells.
  rows 11-14  THE FAR SOCKET. Almost no detail resolves in it and it is
              still a socket: a cavity at rung 0-1 with a rim around it
              that is one rung up -- the lateral orbital rim at x48 and
              the infraorbital margin along row 14. A socket in shadow
              is a dark hole with a lighter edge, not an absence.
  rows 15-17  THE ZYGOMATIC ARCH, and the one mark this session is
              actually for. The cheek's front plane is still lit at
              x41-42; it rolls over into shadow at x44-47; and then at
              x49-51 the arch's crest has turned far enough BACK that it
              sees the fire again and catches a RIM. Dark, bright, dark,
              across five cells. That is what proves there is a far side
              rather than the head stopping where the light does.
  rows 18-22  the hollow under the arch, the masseter, and the RAMUS
              running back and down to the ANGLE OF THE JAW at row 22.
              The outermost cell of every one of these rows is rung 0-1
              -- near black -- and the air immediately outside it is
              rung 3-4. The jaw is an edge you find by CONTRAST. There
              is no contour line anywhere on this side of the head.
  rows 23-26  the jaw sweeping forward to the chin, and the neck.

  x beyond FAR(y): THE SMOKE. Not a wash and not a halo. The fire is in
  front of the head and low, so the air is brightest LOW and near, and
  dies out by x60 and above row 6. Its inner edge is the head's own
  contour, so it is one connected mass with the head rather than a
  second object floating beside it, and it is the ground the jaw and
  the temple are read against.

Two layers, kept apart, as everywhere else in this piece: the digits
are VALUE (how the surface is turned), and hue comes from heat alone
via t.spell_lit -- which is heat() times sees(), the occlusion term
session 7 added. Nothing here picks a colour to mean a brightness.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

X0, Y0 = 41, 0
REGION_X = 41                      # this pass owns every cell at x >= 41

#     x41       x51       x61
#     |         |         |
G = [
    #     x41       x51       x61
    #     |         |         |
    '...........................',   #  0
    '...........................',   #  1
    '...........................',   #  2
    '5443211....................',   #  3 the crown going over and back
    '554433211..................',   #  4
    '65544332111................',   #  5
    '665443232121...............',   #  6
    '7654322332121..............',   #  7 a trace on the temporal line
    '76543212321221.............',   #  8 THE TEMPLE opens
    '887642112331221............',   #  9 BROW RIDGE crest, then nothing
    '877531112321211............',   # 10 temple: the deepest dark in the piece
    '764211232312221............',   # 11 the socket, and its outer rim at x48
    '532111232312211............',   # 12 THE APERTURE
    '532112332312221............',   # 13
    '6533334323312221...........',   # 14 the infraorbital margin
    '7643233323331222...........',   # 15 the cheek, turning over
    '87532223377321221..........',   # 16 ZYGOMATIC ARCH -- THE RIM
    '864322333662212221.........',   # 17
    '87532222333122211..........',   # 18 the hollow, the ramus behind it
    '76432232333121211..........',   # 19
    '643322333312221............',   # 20 the mouth-s far corner
    '554332333312211............',   # 21
    '654332333122211............',   # 22 the ANGLE OF THE JAW
    '654333312211...............',   # 23
    '54333112211................',   # 24 the chin-s far corner
    '222322312221...............',   # 25 the neck, in the jaw-s shadow
    '22322331221................',   # 26
    '...........................',   # 27
]

assert all(len(r) == 27 for r in G), [len(r) for r in G]
assert len(G) == 28

# The air ENDS. A rung-0 cell is one dot of dark red, and a trail of
# them out to x60 is a field fading to zero instead of stopping -- the
# exact failure signature the burning side kept producing and the one
# METHOD.md calls out first. Trimmed here rather than edited into the
# picture above so the rows stay readable as rows.
G = [r.rstrip('.').rstrip('0').ljust(27, '.') for r in G]


def clear(slug=t.SLUG):
    """Own the region: one predicate, used here and by the write below."""
    import canvas_tools as ct
    d = ct.load_canvas(t.W, slug)
    for key in [k for k in d['glyph_override']
                if int(k.split(',')[1]) >= REGION_X]:
        del d['glyph_override'][key]
    for row in d['pixels']:
        for x in range(REGION_X, d['w']):
            row[x] = 0
    ct.save_canvas(t.W, slug, d)


def cells():
    out = []
    for y, row in enumerate(G):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            x = X0 + i
            out.append((x, y, *t.spell_lit(t.RUNG[int(ch)], x, y)))
    return out


# ---------------------------------------------------------------------
# The checks, written as statements of intent rather than thresholds --
# each one fails if the REASON for a decision quietly stopped applying.
def _v(y, x):
    ch = G[y][x - X0]
    return None if ch == '.' else int(ch)


def _check():
    # 1. The far silhouette is not a ruler, and the head and the air are
    #    one connected mass: the air starts exactly one cell past bone.
    for y, f in t.FAR.items():
        assert _v(y, f) is not None, f'row {y}: no bone at FAR {f}'
        assert _v(y, f + 1) is not None, f'row {y}: air detached at {f + 1}'
        assert G[y][f + 1 - X0] != '.'
    assert max(t.FAR.values()) - min(t.FAR.values()) >= 8, 'FAR is a ruler'

    # 2. The two deepest darks on this head are the temple and the
    #    socket, they are one continuous dark because they are adjacent
    #    on a real skull, and nothing else on the head is down there.
    deep = {(x, y) for y in range(28) for x in range(X0, X0 + 27)
            if _v(y, x) is not None and _v(y, x) <= 1 and x <= t.far(y)}
    assert deep, 'nothing on this head is actually dark'
    assert all(44 <= x <= 48 and 8 <= y <= 13 for (x, y) in deep), sorted(deep)
    assert len(deep) >= 10, len(deep)

    # 3. THE RIM. It is the brightest thing on the dark side of its row
    #    and it is a JUMP, not the top of a ramp -- at least three rungs
    #    over the cell inboard of it and the cell outboard.
    for (x, y) in t.RIM:
        v = _v(y, x)
        inb = min(_v(y, xx) for xx in range(t.TERM[y] + 1, x)
                  if (xx, y) not in t.RIM and _v(y, xx) is not None)
        out = min(_v(y, xx) for xx in range(x + 1, t.far(y) + 2)
                  if (xx, y) not in t.RIM and _v(y, xx) is not None)
        assert v - inb >= 3, (x, y, v, inb)
        assert v - out >= 3, (x, y, v, out)
    # ...and it is not as bright as the lit front of the same face.
    assert max(_v(y, x) for (x, y) in t.RIM) < max(
        _v(16, x) for x in range(41, 44)), 'the rim outshines the lit half'

    # 4. The jaw is an EDGE and not a contour line. Bone runs solid to
    #    its last column and the smoke behind it is at half its value,
    #    so the silhouette is a break in DENSITY -- no cell down this
    #    side has being-the-outline as its job.
    def band(x, y):
        return next(n for thr, n in t.BANDS_BY_HEAT if t.lit_heat(x, y) >= thr)

    def val(x, y):
        return t.value(*t.spell_lit(t.RUNG[_v(y, x)], x, y))
    for y in range(18, 27):
        f = t.far(y)
        assert _v(y, f) >= 3, (y, _v(y, f))
        assert val(f, y) >= 1.9 * val(f + 1, y), (y, val(f, y), val(f + 1, y))

    # 5. Adjacent rows are not the same sentence. Two rows of the far
    #    side that read identically ARE the horizontal banding.
    for y in range(3, 27):
        assert G[y][:20] != G[y + 1][:20], f'rows {y},{y + 1} identical'

    # 6. TERM is a table in duo3_tools because sees() needs it before
    #    this picture is loaded, and a second table is a second place for
    #    the reason to stop applying. So: the terminator the light uses
    #    must be the column where THIS picture stops being lit.
    for y in range(3, 27):
        x = X0 - 1
        while _v(y, x + 1) is not None and _v(y, x + 1) >= 4:
            x += 1
        assert t.TERM[y] == x, f'row {y}: TERM says {t.TERM[y]}, picture says {x}'

    # 7. The bounce ladder does what it claims. Checked on the cells
    #    that actually exist, not on the formula.
    for y in range(3, 27):
        for x in range(t.TERM[y] + 1, t.far(y) + 1):
            if (x, y) in t.RIM or _v(y, x) is None:
                continue
            d = x - t.TERM[y]
            b = band(x, y)
            assert b in ('dark', 'cool'), (x, y, d, b, 'lit line on the dark side')
            if d >= 5:
                assert b == 'cool', (x, y, d, b)
    assert any(band(x, y) == 'cool' for y in range(8, 14)
               for x in range(44, 49)), 'the temple never runs out of bounce'
    assert sum(band(x, y) == 'dark' for y in range(3, 27)
               for x in range(t.TERM[y] + 1, t.far(y) + 1)) >= 40, 'no quiet range'
    # 8. No cell of smoke is hotter than the surface it sits behind.
    for y in range(3, 27):
        for x in range(t.far(y) + 1, X0 + 27):
            if _v(y, x) is not None:
                assert band(x, y) in ('dark', 'cool'), (x, y, band(x, y))


if __name__ == '__main__':
    _check()
    clear()
    n = t.paint(cells())
    print('checks passed; cleared x>=%d; painted %d cells' % (REGION_X, n))
