"""Local simulator of the flat-region gate: find largest contiguous same-(glyph,fg)
patch in a rendered .ans. Mimics 'N cells at rows R1-R2 cols C1-C2 (char X, color V)'.
Usage: python3 _gatecheck.py <file.ans> [threshold]"""
import re, sys

def parse_cells(data):
    """Return grid[y][x] = (glyph_char, fg) for each cell, ignoring SGR-only runs."""
    lines = data.split(b'\n')
    grid = []
    for l in lines:
        row = []
        fg = 7; bg = 0
        # tokenize: SGR escapes vs literal text
        i = 0
        for tok in re.finditer(rb'(\x1b\[[0-9;]*m)|([^\\x1b]+)', l):
            if tok.group(1) is not None:
                params = [int(p) for p in tok.group(1)[2:-1].split(b';') if p != b'']
                for p in params:
                    if p == 0: fg, bg = 7, 0
                    elif 30 <= p <= 37: fg = p - 30
                    elif 90 <= p <= 97: fg = p - 90 + 8
                    elif 40 <= p <= 47: bg = p - 40
            else:
                for ch in tok.group(2).decode('cp437','replace'):
                    row.append((ch, fg))
        grid.append(row)
    return grid

def largest_patches(grid, thresh=40):
    """Connected-component (4-neighborhood) of identical (glyph,fg); report patches >= thresh."""
    H = len(grid); W = max(len(r) for r in grid) if grid else 0
    seen = [[False]*W for _ in range(H)]
    from collections import deque
    patches = []
    for y in range(H):
        for x in range(W):
            if x >= len(grid[y]) or seen[y][x]: continue
            key = grid[y][x]
            q = deque([(x,y)]); seen[y][x] = True
            comp = []; minx=maxx=x; miny=maxy=y
            while q:
                cx,cy = q.popleft(); comp.append((cx,cy))
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny = cx+dx, cy+dy
                    if 0<=nx<W and 0<=ny<H and not seen[ny][nx] and nx < len(grid[ny]) and grid[ny][nx]==key:
                        seen[ny][nx]=True; q.append((nx,ny))
                        minx=min(minx,nx);maxx=max(maxx,nx);miny=min(miny,ny);maxy=max(maxy,ny)
            if len(comp) >= thresh:
                patches.append((len(comp), miny+1, maxy+1, minx, maxx, key))
    return sorted(patches, reverse=True)

if __name__ == '__main__':
    path = sys.argv[1]; thresh = int(sys.argv[2]) if len(sys.argv)>2 else 40
    data = open(path,'rb').read()
    grid = parse_cells(data)
    patches = largest_patches(grid, thresh)
    print(f"file={path}  threshold={thresh} cells  -> {len(patches)} flat patch(es)")
    for n,r1,r2,c1,c2,key in patches[:12]:
        print(f"  {n:5d} cells  rows {r1}-{r2} cols {c1}-{c2}  glyph={key[0]!r} fg={key[1]}")
