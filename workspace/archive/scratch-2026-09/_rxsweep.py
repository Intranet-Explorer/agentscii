#!/usr/bin/env python3
# Sweep Gray-Scott regimes + seed configs under FIXED (non-wrapping) boundaries.
import numpy as np, math
W,H=80,46; SW,SH=320,184
def lap_fixed(a):
    p=np.pad(a,1,mode="edge")          # Neumann/reflecting boundary -- no wrap-around
    return p[0:-2,1:-1]+p[2:,1:-1]+p[1:-1,0:-2]+p[1:-1,2:]-4*a
def run(f,k,dA,dB,steps,seedmode,rng):
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    cy,cx=SH//2,SW//2
    if seedmode=="center":
        B[cy-4:cy+5,cx-4:cx+5]=1.0
    elif seedmode=="scatter":
        for _ in range(9):
            sy=rng.integers(SH//3,2*SH//3); sx=rng.integers(SW//3,2*SW//3)
            B[sy-3:sy+4,sx-3:sx+4]=1.0
    elif seedmode=="ring":
        for ang in range(0,360,30):
            sy=int(cy+(SH//3)*math.sin(math.radians(ang)))
            sx=int(cx+(SW//3)*math.cos(math.radians(ang)))
            B[sy-2:sy+3,sx-2:sx+3]=1.0
    for _ in range(steps):
        la=lap_fixed(A);lb=lap_fixed(B);r=A*B*B
        An=A+dA*la-r+f*(1-A); Bn=B+dB*lb+r-(k+f)*B
        np.clip(An,0,1,out=An);np.clip(Bn,0,1,out=Bn)
        A,B=An,Bn
    sx,sy=SW//W,SH//H
    Bd=B[:sy*H,:sx*W].reshape(H,sy,W,sx).mean(axis=(1,3))
    lo,hi=float(Bd.min()),float(Bd.max())
    if hi>lo: Bd=(Bd-lo)/(hi-lo)
    return Bd
cands=[(0.037,0.060),(0.035,0.062),(0.030,0.062),(0.028,0.058),(0.024,0.061),
        (0.019,0.057),(0.014,0.054),(0.010,0.050),(0.062,0.061),(0.046,0.063),
        (0.038,0.061),(0.034,0.062),(0.032,0.060)]
rows=[]
for f,k in cands:
    for dA,dB in [(0.16,0.08),(0.20,0.10),(0.14,0.07)]:
        rng=np.random.default_rng(7)
        Bd=run(f,k,dA,dB,3000,"center",rng)
        rows.append(((Bd>0.25).mean(),f,k,dA,dB,Bd.var(),(Bd>0.5).mean()))
for fr,f,k,dA,dB,var,fh in sorted(rows,reverse=True):
    print(f"f={f:.3f} k={k:.3f} dA={dA} dB={dB}: f>0.25={fr:.3f} var={var:.4f} f>0.5={fh:.3f}")
