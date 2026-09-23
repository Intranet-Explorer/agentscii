import re
data=open("rejected/_orb.v9.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")

def sgr_to_idx(code):
    # 30-37 -> 0-7 ; 40-47 -> 8-15 ; 90-97 -> 1-8 (bright) ; 100-107 -> 9-16(bright bg)
    if 30<=code<=37: return code-30
    if 90<=code<=97: return code-89   # 90->1 ... 97->8
    if 40<=code<=47: return code+8-40+8  # not used for fg
    return None

# Build a per-cell color grid. Track current fg/bg as we scan each line.
grid=[]
for line in lines:
    fg=0;bg=0
    cells=[]
    i=0
    while i<len(line):
        if line[i]=='\x1b' and i+1<len(line) and line[i+1]=='[':
            m=re.match(r'\x1b\[([0-9;]*)m', line[i:])
            if m:
                params=[int(p) for p in m.group(1).split(';') if p!='']
                for p in params:
                    if p==0: fg=0;bg=0
                    elif 30<=p<=37: fg=p-30
                    elif 90<=p<=97: fg=p-89
                    elif 40<=p<=47: bg=p-40+8
                    elif 100<=p<=107: bg=p-100+8
                i+=m.end()
                continue
        ch=line[i]
        cells.append((ch,fg,bg))
        i+=1
    grid.append(cells)

# Print color index per cell for rows 14-38 (use fg as the "ink" since bg mostly 0/black)
for r in range(14,40):
    if r>=len(grid): break
    cells=grid[r]
    s=""
    for ch,fg,bg in cells:
        # show fg index; '.' for black space
        if fg==0 and ch==' ': s+='.'
        else: s+=f"{fg}"
    print(f"{r:2d} {s}")
