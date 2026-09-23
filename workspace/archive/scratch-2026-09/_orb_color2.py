import re
data=open("rejected/_orb.v9.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")
grid=[]
for line in lines:
    fg=0;bg=0;cells=[];i=0
    while i<len(line):
        if line[i]=='\x1b' and i+1<len(line) and line[i+1]=='[':
            m=re.match(r'\x1b\[([0-9;]*)m', line[i:])
            if m:
                for p in [int(x) for x in m.group(1).split(';') if x!='']:
                    if p==0: fg=0;bg=0
                    elif 30<=p<=37: fg=p-30
                    elif 90<=p<=97: fg=p-89
                    elif 40<=p<=47: bg=p-40+8
                    elif 100<=p<=107: bg=p-100+8
                i+=m.end(); continue
        cells.append((line[i],fg,bg)); i+=1
    grid.append(cells)

# amber family = {3,9,11}; show top pixel (fg) and bottom pixel (bg). 
# Mark: 'A'=amber(3/9/11), 'W'=white(15), 'G'=grey(7/8), 'B'=black(0), '?'=other
def mark(c):
    if c in (3,9,11): return 'A'
    if c==15: return 'W'
    if c in (7,8): return 'G'
    if c==0: return '.'
    return str(c)
for r in range(14,40):
    if r>=len(grid): break
    cells=grid[r]
    top="".join(mark(fg) for ch,fg,bg in cells)
    bot="".join(mark(bg) for ch,fg,bg in cells)
    print(f"{r:2d} T {top}")
    print(f"   B {bot}")
