"""duo3 working helpers. Not a drawing library -- a view + a batch writer.

ct.stamp() does one load/save of the whole canvas JSON per call, which is
fine for a patch and absurd for 2,000 hand-placed cells. paint() takes a
list of cells and does one load/save. grid() is the other half of the
loop: read what is already under a region so the next cell's glyph can be
chosen from the value that is actually there.
"""
import base64
import sys

sys.path.insert(0, '/Users/octo/agentscii')
import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
SLUG = 'duo3'
SHOT = W + '/scratch/duo3_look.png'


def paint(cells, slug=SLUG):
    """cells: iterable of (x, y, ch, fg, bg) in CELL space. One save."""
    data = ct.load_canvas(W, slug)
    go = data['glyph_override']
    cw, ch_ = data['w'], data['h_cells']
    n = 0
    for x, y, g, fg, bg in cells:
        if 0 <= x < cw and 0 <= y < ch_:
            go[f'{y},{x}'] = [g, int(fg), int(bg)]
            n += 1
    ct.save_canvas(W, slug, data)
    return n


def grid(x, y, w, h, slug=SLUG):
    """Cells as they currently render: [[(ch, fg, bg), ...], ...]."""
    rows = ct.render_canvas_cells(ct.load_canvas(W, slug))
    return [r[x:x + w] for r in rows[y:y + h]]


def px(x, y, w, h, slug=SLUG):
    """Raw pixel colours under a CELL region: [[top, bot], ...] per cell."""
    d = ct.load_canvas(W, slug)
    p = d['pixels']
    return [[(p[2 * (y + r)][x + c], p[2 * (y + r) + 1][x + c])
             for c in range(w)] for r in range(h)]


def _write(b64, path):
    open(path, 'wb').write(base64.b64decode(b64))
    return path


def look(x=0, y=0, w=None, h=None, scale=6, path=SHOT, slug=SLUG):
    d = ct.load_canvas(W, slug)
    w = d['w'] if w is None else w
    h = d['h_cells'] if h is None else h
    b64, dump = ct.crop(W, slug, x, y, w, h, scale=scale)
    return _write(b64, path), dump


def check(slug=SLUG):
    g, c, dens = ct.self_check(W, slug)
    return (_write(g, W + '/scratch/duo3_glyphs.png'),
            _write(c, W + '/scratch/duo3_colour.png'), dens)


def block(x0, y0, G, F, B, slug=SLUG):
    """Hand-authored cell block: three aligned layers, one char per cell.

    G glyph ('.' = leave this cell alone), F fg hex, B bg hex. Authoring
    a region this way keeps every cell a deliberate choice that is still
    readable as a picture in the source -- which is the whole point of
    per-cell work over a region rule.
    """
    cells = []
    for r, (g, f, b) in enumerate(zip(G, F, B)):
        assert len(g) == len(f) == len(b), f'row {r} layers misaligned: {len(g)},{len(f)},{len(b)}'
        for c, ch in enumerate(g):
            if ch != '.':
                cells.append((x0 + c, y0 + r, ch, int(f[c], 16), int(b[c], 16)))
    return paint(cells, slug)


# The piece's value ramp, dark -> light, written one char per cell.
#
# Sixteen steps over four hue pairs. The first version jumped brown (3)
# straight to bright yellow (11), and every lit edge came out as a
# glowing line -- there was no rung between flesh and fire, so anything
# lit read as emitting. Bright red (9) is that rung, and it is the right
# hue for skin lit by an ember besides. Magenta stays reserved for the
# ambient on surfaces turned fully away from the light.
#
# No step is a flat background fill: each is a real glyph over a second
# colour, so value is carried by ink.
RAMP = {
    '0': (' ', 0, 0),
    'm': ('░', 5, 0), 'M': ('▒', 5, 0), 'N': ('▓', 5, 0),
    '1': ('░', 1, 0), '2': ('▒', 1, 0), '3': ('▓', 1, 0),
    '4': ('░', 3, 1), '5': ('▒', 3, 1), '6': ('▓', 3, 1),
    '7': ('█', 3, 1),
    '8': ('░', 9, 3), '9': ('▒', 9, 3), 'A': ('▓', 9, 3),
    'B': ('█', 9, 3),
    'C': ('░', 11, 9), 'D': ('▒', 11, 9), 'E': ('▓', 11, 9),
    'F': ('█', 11, 9),
}


def levels(x0, y0, rows, width=None):
    """Value-ramp rows -> cells. '.' leaves a cell alone."""
    out = []
    for r, row in enumerate(rows):
        assert width is None or len(row) == width, (r, len(row))
        for c, lv in enumerate(row):
            if lv != '.':
                ch, fg, bg = RAMP[lv]
                out.append((x0 + c, y0 + r, ch, fg, bg))
    return out
