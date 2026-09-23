import re, math
data=open("rejected/_orb.v9.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")
W=80; H=52; ph=H*2; cx=W//2; cy=ph//2; iris_r=17; pupil_r=9
half_w=30; h_upper=20; h_lower=13; exp_u,exp_l=0.50,0.42
def opening_half_h(u):
    a=abs(u)
    if a>=1.0: return (0.0,0.0)
    return h_upper*(1-u*u)**exp_u, h_lower*(1-u*u)**exp_l
# Find non-black pixels in the void BELOW the iris annulus (d>iris_r+2, py>cy), that are isolated
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

# print the lower-lid band region in detail (cell rows 30-38), showing color index per pixel
def m(c): return 'A' if c in (3,9,11) else ('.' if c==0 else str(c))
print("=== LOWER LID band, cell rows 30-38 ===")
for cr in range(30,39):
    print(f"{cr:2d} T {''.join(m(pix[cr*2][px]) for px in range(W))}")
    print(f"   B {''.join(m(pix[cr*2+1][px]) for px in range(W))}")
