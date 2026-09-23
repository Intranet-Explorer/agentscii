import re, math
data=open("scratch/_orb.v10.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")
W=80; H=52; ph=H*2; cx=W//2; cy=ph//2; iris_r=17; pupil_r=9
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
from collections import Counter
cnt=Counter()
for py in range(ph):
    for px in range(W):
        c=pix[py][px]
        if c in (3,9,11): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r<d<iris_r: cnt[c]+=1
print("v10 non-amber inside annulus:", dict(cnt))
# also check sclera slab: count distinct grey transitions in a vertical column through the lit side
col=20  # left of center, lit side
trans=0; prev=None
for py in range(30,74):
    c=pix[py][col]
    if c!=prev and c in (7,8,15,0): trans+=1
    prev=c
print(f"grey transitions down column px={col} (lit side): {trans}")
