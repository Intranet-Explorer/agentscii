# Faithful replica of harness._flat_region_check (2026-09-19).
import re, sys

THRESH = 40
DITHER = set("\u2593\u2592\u2591")
BOX = set("═║╔╗╚╝╠╣╦╩╬─│┌┐└┘├┤┬┴┼")

def parse(path):
    data=open(path,'rb').read().decode('cp437','replace')
    grid={}; fg=7; bg=0; r=0
    for ln in data.split('\n'):
        c=0; j=0
        while j<len(ln):
            ch=ln[j]
            if ch=='\x1b' and j+1<len(ln) and ln[j+1]=='[':
                k=j+2; numbuf=''
                while k<len(ln) and ln[k]!='m': numbuf+=ln[k]; k+=1
                params=[int(p) for p in numbuf.split(';') if p!=''] if numbuf else [0]
                for p in params:
                    if p==0: fg,bg=7,0
                    elif 30<=p<=37: fg=p-30
                    elif 90<=p<=97: fg=p-90+8
                    elif 40<=p<=47: bg=p-40
                    elif 100<=p<=107: bg=p-100+8
                j=k+1
            else:
                grid[(r,c)]=(ch,fg,bg); c+=1; j+=1
        r+=1
    return grid

def analyze(path):
    grid=parse(path)
    rows={}
    for (rr,cc),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        rows.setdefault(rr,[]).append(ch)
    border_rows=set()
    for rr,chlist in rows.items():
        run=mx=0
        for ch in chlist:
            if ch in BOX: run+=1; mx=max(mx,run)
            else: run=0
        if mx>40: border_rows.add(rr)

    subject_cells={}; dither_cells=set()
    for (rr,cc),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        if rr in border_rows: continue
        if ch in DITHER:
            dither_cells.add((rr,cc)); continue
        visible_idx = bg if (ch==' ' and bg!=0) else fg
        subject_cells[(rr,cc)]=(ch,visible_idx)

    if len(subject_cells)<THRESH: return True, "too small"
    visited=set(); large=[]
    for start in subject_cells:
        if start in visited: continue
        key=subject_cells[start]
        stack=[start]; region=[]; visited.add(start)
        while stack:
            cur=stack.pop(); region.append(cur); rr,cc=cur
            for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                nxt=(nr,nc)
                if nxt not in visited and subject_cells.get(nxt)==key:
                    visited.add(nxt); stack.append(nxt)
        if len(region)>THRESH:
            rs=[r for r,c in region]; cs=[c for r,c in region]
            large.append({"size":len(region),"char":key[0],"visible_idx":key[1],
                           "rows":(min(rs),max(rs)),"cols":(min(cs),max(cs))})
    if not large: return True, "no large regions"
    large.sort(key=lambda x:-x["size"])
    ex="; ".join(f"{r['size']} cells rows {r['rows'][0]}-{r['rows'][1]} cols {r['cols'][0]}-{r['cols'][1]} char {r['char']!r} vis={r['visible_idx']}" for r in large[:3])
    print(f"   {path}: {len(large)} >40-cell regions: {ex}")
    return False, ex

for p in sys.argv[1:]:
    ok,msg=analyze(p)
    print(f"   -> {'PASS' if ok else 'FAIL'}")
