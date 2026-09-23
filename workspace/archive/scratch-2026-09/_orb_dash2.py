import re, math
data=open("rejected/_orb.v9.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")
W=80; H=52; ph=H*2; cx=W//2; cy=ph//2
pix=[[0]*W for _ in range(ph)]
for cr,line in enumerate(lines):
    if cr>=H: break
    fg=0;bg=0;i=0; cells=[]
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
        ch=line[i]; cells.append((ch,fg,bg)); i+=1
    for px,(ch,fg,bg) in enumerate(cells):
        if ch==' ': pix[cr*2][px]=bg; pix[cr*2+1][px]=bg
        else: pix[cr*2][px]=fg; pix[cr*2+1][px]=bg

# lower-lid contour is at dy ~ +h_lower (lo). h_lower=13 so lo max ~13, plus 1.5..4.5 -> py cy+14.5..cy+17.5
# iris bottom edge d=iris_r=17 -> py up to cy+17. So lower lid sits just below iris.
# Find non-black pixels with py in [cy+13, cy+20] (the band just under the eye) and report
print("non-black pixels in band py", cy+13, "to", cy+22, "(cell rows ~", (cy+13)//2, "-", (cy+22)//2,")")
for py in range(cy+13, cy+23):
    row=[px for px in range(W) if pix[py][px]!=0]
    if row:
        # group into runs
        runs=[]; s=row[0]; prev=row[0]
        for q in row[1:]:
            if q==prev+1: prev=q
            else: runs.append((s,prev)); s=q; prev=q
        runs.append((s,prev))
        cols=set(pix[py][px] for px in row)
        print(f"  py={py} (cell {py//2}) runs={runs} colors={cols}")
