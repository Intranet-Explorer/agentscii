# Local replica of the flat-region gate: parse .ans, decode SGR per-cell color,
# find contiguous same-(char,color) regions >40 cells; flag if a hue family (fg&7)
# spans <3 distinct brightness steps across its large regions. Iterate locally here.
import re, sys
from collections import defaultdict

def parse(path):
    data=open(path,'rb').read().decode('utf-8','replace')
    # split into lines, track SGR state
    lines=data.split('\n')
    grid=[]  # list of rows; each row = list of (ch, fg, bg)
    fg=7; bg=0
    for ln in lines:
        row=[]
        i=0
        # tokenize: escape sequences vs literal chars
        toks=re.findall(r'\x1b\[([0-9;]*)m|.', ln)
        for t in toks:
            m=re.match(r'\x1b\[([0-9;]*)m', t) if False else None
        # simpler: iterate char by char
        i=0
        cur=[]
        buf=''
        j=0
        while j<len(ln):
            ch=ln[j]
            if ch=='\x1b' and j+1<len(ln) and ln[j+1]=='[':
                # parse SGR
                k=j+2
                numbuf=''
                while k<len(ln) and ln[k]!='m':
                    numbuf+=ln[k]; k+=1
                params=[int(p) for p in numbuf.split(';') if p!=''] if numbuf else [0]
                for p in params:
                    if p==0: fg=7; bg=0
                    elif 30<=p<=37: fg=p-30
                    elif 90<=p<=97: fg=p-90+8
                    elif 40<=p<=47: bg=p-40
                    elif 100<=p<=107: bg=p-100+8
                j=k+1
            else:
                cur.append((ch,fg,bg)); j+=1
        row=cur
        grid.append(row)
    return grid

def analyze(path):
    grid=parse(path)
    # build a 2D array of (char, fg, bg); pad to uniform width
    W=max(len(r) for r in grid) if grid else 0
    H=len(grid)
    cells=[[None]*W for _ in range(H)]
    for y,row in enumerate(grid):
        for x,(ch,fg,bg) in enumerate(row):
            cells[y][x]=(ch,fg,bg)
    # "visible color" = fg if char is a glyph (non-space), else bg
    def vis(c):
        ch,fg,bg=c
        return bg if ch==' ' else fg
    # connected components of same visible color
    seen=[[False]*W for _ in range(H)]
    regions=[]  # (size, set_of_vis_colors_in_region, bbox)
    from collections import deque
    for y in range(H):
        for x in range(W):
            if seen[y][x] or cells[y][x] is None: continue
            v=vis(cells[y][x])
            q=deque([(x,y)]); seen[y][x]=True
            comp=[]; minx=maxx=x; miny=maxy=y
            while q:
                cx,cy=q.popleft(); comp.append((cx,cy))
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=cx+dx,cy+dy
                    if 0<=nx<W and 0<=ny<H and not seen[ny][nx] and cells[ny][nx] is not None:
                        if vis(cells[ny][nx])==v:
                            seen[ny][nx]=True; q.append((nx,ny))
                            minx=min(minx,nx);maxx=max(maxx,nx);miny=min(miny,ny);maxy=max(maxy,ny)
            regions.append((len(comp),v,(minx,miny,maxx,maxy)))
    # group large regions by hue family fg&7
    big=[r for r in regions if r[0]>40]
    fam=defaultdict(list)
    for size,v,bbox in big:
        fam[v&7].append((size,v,bbox))
    print(f"  {path}: {len(regions)} components, {len(big)} >40-cell")
    ok=True
    for hue in sorted(fam):
        vs=sorted(set(v for _,v,_ in fam[hue]))
        nsteps=len(vs)
        total=sum(s for s,_,_ in fam[hue])
        flag = nsteps<3
        if flag: ok=False
        print(f"    hue {hue}: {len(fam[hue])} regions, {total} cells, distinct vis colors {vs} -> {nsteps} steps {'FAIL' if flag else 'ok'}")
    return ok

for p in sys.argv[1:]:
    print(p)
    analyze(p)
