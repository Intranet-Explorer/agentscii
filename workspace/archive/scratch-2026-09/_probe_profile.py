import math
from curve_common import W,H,sgr,RESET,hue_index,phosphor_render,hygiene_gate
inten=[[0.0]*W for _ in range(H)]; huebuf=[[0.0]*W for _ in range(H)]
def trace(pts,h0,h1,d=1.0):
    n=len(pts)-1
    for i in range(n):
        x0,y0=pts[i];x1,y1=pts[i+1]
        steps=max(2,int(math.hypot(x1-x0,y1-y0)*3))
        for s in range(steps+1):
            t=s/steps;xi=int(round(x0+(x1-x0)*t));yi=int(round(y0+(y1-y0)*t))
            if 0<=xi<W and 0<=yi<H: inten[yi][xi]+=d; huebuf[yi][xi]=h0+(h1-h0)*t
GRID=6
def bd(x,y):
    return sgr(40,94)+"\u2591" if (x%GRID==0 or y%GRID==0) else sgr(40,40)+" "
# WIDER, SHORTER skull. Face side RIGHT (nose+chin bumps), back LEFT (round occiput).
prof=[(36,8),(45,9),(52,13),(55,18),(59,22),(52,25),(54,28),(49,30),(52,33),(46,35),(41,37)]
trace(prof,0.0,2.6,1.0)
back=[(36,8),(28,10),(23,16),(22,23),(24,30),(29,35)]
trace(back,2.6,4.2,0.9)
# visor band across eye region
for i in range(15):
trace(visor,4.2,6.0,1.4) if False else None
    t=i/14.0; x=40+t*13; y=17+math.sin(t*math.pi)*1.2
    visor.append((x,y))
# eye node
for r in range(-1,2):
    for c in range(-1,2):
        xi,yi=46+c,18+r
        if 0<=xi<W and 0<=yi<H: inten[yi][xi]+=2.8
imax=max(max(r) for r in inten); out=[]
phosphor_render(inten,huebuf,imax,4,bd,out)
open("_probe_profile.ans","w",encoding="cp437").write("\n".join(out)+RESET)
print("ok")
