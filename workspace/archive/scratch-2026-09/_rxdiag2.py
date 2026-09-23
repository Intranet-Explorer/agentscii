import numpy as np
W,H=80,46; SW,SH=320,184
def lap(a): return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)
# classic gray-scott regimes (f,k) with moderate diffusion
cands=[(0.037,0.060),(0.035,0.062),(0.030,0.062),(0.028,0.058),(0.024,0.061),
       (0.019,0.057),(0.014,0.054),(0.010,0.050),(0.062,0.061),(0.046,0.063)]
for f,k in cands:
    dA,dB=0.16,0.08; steps=3000
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    cy,cx=SH//2,SW//2; B[cy-4:cy+5,cx-4:cx+5]=1.0
    for _ in range(steps):
        la=lap(A);lb=lap(B);r=A*B*B
        A=A+dA*la-r+f*(1-A); B=B+dB*lb+r-(k+f)*B
        np.clip(A,0,1,out=A);np.clip(B,0,1,out=B)
    sx,sy=SW//W,SH//H
    Bd=B[:sy*H,:sx*W].reshape(H,sy,W,sx).mean(axis=(1,3))
    lo,hi=float(Bd.min()),float(Bd.max())
    if hi>lo: Bd=(Bd-lo)/(hi-lo)
    print(f"f={f:.3f} k={k:.3f}: var={Bd.var():.4f} frac>0.25={(Bd>0.25).mean():.3f} frac>0.5={(Bd>0.5).mean():.3f}")
