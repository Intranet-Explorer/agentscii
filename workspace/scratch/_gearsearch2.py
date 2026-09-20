#!/usr/bin/env python3
# v2 search: overlay low-cusp gears, each scaled to its OWN radius (concentric nesting), centered.
import math
W=80; H=46; CX=W/2.0; CY=H/2.0

def gear_pts(R,r,dfrac,kind,samples):
    g=math.gcd(int(R),int(r)); revs=int(r)//g
    roll=(R-r) if kind=="hypo" else (R+r); f=(R-r)/r if kind=="hypo" else (R+r)/r
    d=dfrac*r; pts=[]
    for i in range(samples):
        t=2*math.pi*i/samples
        if kind=="hypo": x=roll*math.cos(t)+d*math.cos(f*t); y=roll*math.sin(t)-d*math.sin(f*t)
        else:            x=roll*math.cos(t)-d*math.cos(f*t); y=roll*math.sin(t)+d*math.sin(f*t)
        pts.append((x,y))
    return pts

AX=CX*0.96; AY=CY*0.94
def try_set(GEARS):
    grid=[[" "]*W for _ in range(H)]
    for R,r,dfrac,kind,amp in GEARS:
        pts=gear_pts(R,r,dfrac,kind,12000)
        mx=max(max(abs(p[0]) for p in pts),max(abs(p[1]) for p in pts))
        sc=min(AX/mx,AY/mx)*amp
        for x,y in pts:
            cx=int(round(CX+x*sc)); cy=int(round(CY-y*sc))
            if 0<=cx<W and 0<=cy<H: grid[cy][cx]="*"
    print("====", GEARS)
    for row in grid: print("".join(row))
    print()

try_set([(5,3,0.6,"hypo",0.94),(7,4,0.5,"epi",0.80),(11,3,0.6,"hypo",0.62)])
try_set([(5,3,0.6,"hypo",0.96),(9,4,0.5,"epi",0.78),(13,3,0.6,"hypo",0.60)])
try_set([(7,3,0.6,"hypo",0.96),(5,2,0.5,"epi",0.74),(11,4,0.6,"hypo",0.55)])
