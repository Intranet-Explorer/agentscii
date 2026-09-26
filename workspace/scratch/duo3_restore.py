"""Restore workspace/canvases/duo3.json from a saved .ans snapshot.

The live canvas JSON is not in git, so a discarded session can overwrite
it; the per-session .ans snapshots are the only durable record. duo3 is
100% glyph_override -- every subject cell is a hand-placed (ch, fg, bg) --
so parsing the snapshot back into overrides is lossless for the drawing.
`pixels` is rebuilt to agree with each cell's bg so shade/fill/crop still
read a consistent field underneath.

Own parser rather than harness._parse_ans_grid: that one clamps at col 79
and swallows the newline after an exactly-80-column line, which shifts
rows by a column. save_ans emits plain padded lines with no cursor
addressing, so a straight walk is both correct and shorter.
"""
import re
import sys

sys.path.insert(0, '/Users/octo/agentscii')
import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
SGR = re.compile(r'\x1b\[([0-9;]*)m')


def parse_ans(path, rows=28):
    """{(y, x): (ch, fg, bg)} for the art rows only."""
    text = open(path, 'rb').read().decode('cp437').replace('\r\n', '\n')
    grid = {}
    for y, line in enumerate(text.split('\n')[:rows]):
        fg, bright, bg, x, pos = 7, False, 0, 0, 0
        while pos < len(line):
            m = SGR.match(line, pos)
            if m:
                for p in [int(v) for v in m.group(1).split(';') if v] or [0]:
                    if p == 0:
                        fg, bright, bg = 7, False, 0
                    elif p == 1:
                        bright = True
                    elif 30 <= p <= 37:
                        fg = p - 30
                    elif 90 <= p <= 97:
                        fg, bright = p - 90, True
                    elif 40 <= p <= 47:
                        bg = p - 40
                    elif 100 <= p <= 107:
                        bg = p - 100 + 8
                pos = m.end()
                continue
            grid[(y, x)] = (line[pos], fg + 8 if bright else fg, bg)
            x += 1
            pos += 1
    return grid


def restore(ans_path, slug='duo3', rows=28):
    grid = parse_ans(ans_path, rows)
    d = ct.load_canvas(W, slug)
    go, px = {}, d['pixels']
    for y in range(rows):
        for x in range(d['w']):
            cell = grid.get((y, x))
            if cell and not (cell[0] == ' ' and cell[2] == 0):
                go[f'{y},{x}'] = list(cell)
                px[2 * y][x] = px[2 * y + 1][x] = cell[2]
            else:
                px[2 * y][x] = px[2 * y + 1][x] = 0
    d['glyph_override'] = go
    ct.save_canvas(W, slug, d)
    return len(go)


if __name__ == '__main__':
    n = restore(sys.argv[1])
    ct.save_ans(W, 'duo3', 'scratch/_probe3.ans', title='What the Fire Left',
                handles='opus')
    a, b = parse_ans('workspace/scratch/_probe3.ans'), parse_ans(sys.argv[1])
    bad = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    print(n, 'cells restored;', len(bad), 'round-trip mismatches')
