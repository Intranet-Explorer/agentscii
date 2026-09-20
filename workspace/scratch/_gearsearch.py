#!/usr/bin/env python3
# quick param search: render several hypotrochoid/epitrochoid gears as tiny ascii thumbnails
# so I can eyeball which (R,r,d) sets look like clean centered rosettes before committing.
import math

def gear_pts(R, r, dfrac, kind, samples=20000):
    g = math.gcd(int(R), int(r)); revs = int(r)//g
    roll = (R-r) if kind=="hypo" else (R+r); f=(R-r)/r if kind=="hypo" else (R+r)/r
    d = dfrac*r
    pts=[]
    for i in range(samples):
        t=2*math.pi*i/samples
        if kind=="hypo":
            x=roll*math.cos(t)+d*math.cos(f*t); y=roll*math.sin(t)-d*math.sin(f*t)
        else:
            x=roll*math.cos(t)-d*math.cos(f*t); y=roll*math.sin(t)+d*math.sin(f*t)
        pts.append((x,y))
    return pts

def thumb(pts, w=40, h=22):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    mx=max(abs(min(xs)),abs(max(xs))); my=max(abs(min(ys)),abs(max(ys)))
    sc=min((w/2-1)/mx,(h/2-1)/my)
    grid=[[" "]*w for _ in range(h)]
    for x,y in pts:
        cx=int(round(w/2+x*sc)); cy=int(round(h/2-y*sc))
        if 0<=cx<w and 0<=cy<h: grid[cy][cx]="*"
    return "\n".join("".join(r) for r in grid)

for R,r,dfrac,kind in [
    (5,3,0.6,"hypo"),(7,3,0.6,"hypo"),(11,3,0.6,"hypo"),
    (5,2,0.5,"epi"),(7,4,0.5,"epi"),(9,4,0.5,"epi"),
    (8,3,0.5,"hypo"),(13,5,0.6,"hypo"),(11,4,0.7,"epi"),
]:
    pts=gear_pts(R,r,dfrac,kind)
    print(f"--- {kind} R={R} r={r} d={dfrac} cusps={int(R)//math.gcd(int(R),int(r))} ---")
    print(thumb(pts))
    print()
