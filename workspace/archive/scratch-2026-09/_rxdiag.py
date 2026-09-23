import math, numpy as np
W,H=80,46; SW,SH=320,184
def lap(a): return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)
for f,k,dA,dB,steps in [(0.037,0.060,0.15,0.075,6000),(0.037,0.062,0.16,0.08,4000),(0.025,0.060,0.16,0.08,5000),(0.030,0.062,0.14,0.07,3000)]:
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    cy,cx=SH//2,SW//2; B[cy-3:cy+4,cx-3:cx+4]=1.0
    for _ in range(steps):
        la=lap(A);lb=lap(B);r=A*B*B
        A=A+dA*la-r+f*(1-A); B=B+dB*lb+r-(k+f)*B
        np.clip(A,0,1,out=A);np.clip(B,0,1,out=B)
    sx,sy=SW//W,SH//H
    Bd=B[:sy*H,:sx*W].reshape(H,sy,W,sx).mean(axis=(1,3))
    lo,hi=float(Bd.min()),float(Bd.max())
    if hi>lo: Bd=(Bd-lo)/(hi-lo)
    print(f"f={f} k={k} dA={dA} dB={dB} steps={steps}: var={Bd.var():.4f} frac>0.3={(Bd>0.3).mean():.3f} frac>0.6={(Bd>0.6).mean():.3f} max={Bd.max():.2f}")
    # column profile to spot the right-edge streaks
    col=Bd.mean(axis=0)
    print("   col means (every 10):", " ".join(f"{col[x]:.2f}" for x in range(0,80,10)))
