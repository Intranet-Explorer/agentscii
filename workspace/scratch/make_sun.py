import math, random
random.seed(1)
w,h=80,24
cells=[]
yc=[6.5+3*math.sin(math.pi*x/w) for x in range(w)]
def dith(v):
    if v>=yc[x]: return 7
    t=yc[x]-v
    if abs(t-1)<0.5: return 7
    # 2nd px up from y = cyan; 3rd+ dark blue (cyan shows only at 4th)
    if abs(t-2)<=1e-9 or abs(t-2)>abs(t): pass
    # simpler: t in [0.5,1] white? no — use discrete steps of 0.5
    n=round(t*2)/2
    if abs(n-0)<1e-9: return 7
    if abs(n-1)<1e-9: pass # never happens (y row is v<yc)
    if abs(n-1.5)<1e-9 or abs(t-n)<=abs(t-(n+0)): return 6
    # t>=2 -> dark blue, except t==? just: cyan at ?
    # fix: n = ceil?
EOF