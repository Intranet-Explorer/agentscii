#!/usr/bin/env python3
import numpy as np
W,H=80,46; SW,SH=320,184
def lap_fixed(a):
    p=np.pad(a,1,mode="edge")
    return p[0:-2,1:-1]+p[2:,1:-1]+p[1:-1,0:-2]+p[1:-1,2:]-4*a
def run(f,k,dA,dB,steps,nseed,rng):
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    for _ in range(nseed):
        sy=rng.integers(SH//3,2*SH//3); sx=rng.integers(SW//3,2*SW//3)
        B[sy-3:sy+4,sx-3:sx+4]=1.0
    for _ in range(steps):
        la=lap_fixed(A);lb=lap_fixed(B);r=A*B*B
        An=A+dA*la-r+f*(1-A); Bn=B+dB*lb+r-(k+f)*B
        np.clip(An,0,1,out=An);np.clip(Bn,0,1,out=Bn)
        A,B=An,Bn
    sx,sy=SW//W,SH//H
    Bd=B[:sy*H,:sx*W].reshape(H,sy,W,sx).mean(axis=(1,3))
    return Bd
for f,k in [(0.028,0.058),(0.037,0.060),(0.035,0.062),(0.030,0.062)]:
    for nseed in [1,2,3,4,6]:
        rng=np.random.default_rng(7)
        Bd=run(f,k,0.20,0.10,3000,nseed,rng)
        lo,hi=float(Bd.min()),float(Bd.max())
        if hi>lo: Bn=(Bd-lo)/(hi-lo)
        else: Bn=Bd
        # check right-edge column max vs interior -- streak diagnostic
        colmax_right=Bn[:, -6:].max(); colmax_mid=Bn[:, 30:50].max()
        print(f"f={f:.3f} k={k:.3f} nseed={nseed}: f>0.25={(Bn>0.25).mean():.3f} rightcolmax={colmax_right:.2f} midcolmax={colmax_mid:.2f}")
