"""Restore workspace/canvases/duo3.json from a saved .ans snapshot.

Needed because the live canvas JSON is not in git and the discarded
session-6 control overwrote it. duo3 is 100% glyph_override -- every
subject cell is a hand-placed (ch, fg, bg) -- so a round-trip through
harness._parse_ans_grid is lossless for the drawing. `pixels` is
rebuilt to agree with each cell's bg so shade/fill/crop still read a
consistent field under the overrides.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii')
import harness, canvas_tools as ct

W = '/Users/octo/agentscii/workspace'


def restore(ans_path, slug='duo3', rows=28):
    grid = harness._parse_ans_grid(ans_path)
    if isinstance(grid, tuple):
        grid = grid[0]
    d = ct.load_canvas(W, slug)
    go, px = {}, d['pixels']
    for (r, c), (ch, fg, bg) in grid.items():
        if r >= rows:            # signature block below the art
            continue
        if ch == ' ' and bg == 0:
            continue
        go[f'{r},{c}'] = [ch, fg, bg]
        px[2 * r][c] = bg
        px[2 * r + 1][c] = bg
    for r in range(rows):        # clear anything the snapshot doesn't cover
        for c in range(d['w']):
            if f'{r},{c}' not in go:
                px[2 * r][c] = 0
                px[2 * r + 1][c] = 0
    d['glyph_override'] = go
    ct.save_canvas(W, slug, d)
    return len(go)


if __name__ == '__main__':
    print(restore(sys.argv[1]), 'cells restored')
