import re
data = open('scratch/_wasteland.v1.ans','rb').read()
text = data.decode('cp437', errors='replace')
# Tokenize into (type, payload)
tokens = re.findall(r'\x1b\[([0-9;]*)m|([^ \n\x1b])', text)
fg=30; bg=40
cells=[]
r=0;c=0
for typ,payload in tokens:
    if typ=='':  # a real char (non-space, non-newline, non-esc)
        cells.append((r,c,payload,fg,bg)); c+=1
    else:
        for q in payload.split(';'):
            v=int(q or '0')
            if v==0: fg,bg=30,40
            elif 30<=v<=37: fg=v
            elif 90<=v<=97: fg=v
            elif 40<=v<=47: bg=v
            elif 100<=v<=107: bg=v
# count rows via newline
nrows = text.count('\n')
print("newlines:", nrows, "ink cells:", len(cells))
# Build a grid of fg per (r,c) for ink
from collections import defaultdict
grid=defaultdict(dict)
for cc,ch,f,b in cells:
    grid[cc][f]=ch  # last write wins; fine for inspection
# Print rows 30-37 cols 0..26, showing fg color of each ink cell
for rr in range(30,38):
    out=[]
    for cc in range(0,27):
        if cc in grid:
            # find which fg — pick the one that's not black-ish if multiple
            fgs=list(grid[cc].keys())
            out.append(f"{cc}:{grid[cc][fgs[-1]]}@{fgs[-1]}")
    print(f"r{rr}: " + " ".join(out))
