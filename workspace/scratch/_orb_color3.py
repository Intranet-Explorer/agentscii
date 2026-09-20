import re, math
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

W=80; H=52; ph=H*2; cx=W//2; cy=ph//2; iris_r=17; pupil_r=9
# Build pixel grid: pixel[py][px] = color. top pixel of cell cr -> py=cr*2, bottom -> cr*2+1
pix=[[0]*W for _ in range(ph)]
for cr in range(H):
    if cr>=len(grid): break
    cells=grid[cr]
    for px,(ch,fg,bg) in enumerate(cells):
        pix[cr*2][px]=fg
        pix[cr*2+1][px]=bg

# 1. foreign pixels INSIDE iris annulus (pupil_r < d < iris_r): should be amber {3,9,11}
print("=== FOREIGN (non-amber) pixels inside iris annulus ===")
for py in range(ph):
    for px in range(W):
        c=pix[py][px]
        if c in (3,9,11): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r < d < iris_r:
            print(f"  py={py} px={px} color={c} d={d:.1f}")
