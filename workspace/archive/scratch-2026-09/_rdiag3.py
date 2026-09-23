import numpy as np
W,H=80,46; SW,SH=320,184
def lap9(a):
    return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)
def sim(feed,kill,steps,seed,dA=1.0,dB=0.5,dt=0.02):
    rng=np.random.default_rng(seed)
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    cy0,cy1=SH//2-6,SH//2+7; cx0,cx1=SW//2-10,SW//2+11
    B[cy0:cy1,cx0:cx1]=1.0
    for _ in range(steps):
        la=lap9(A); lb=lap9(B)
        r=A*B*B
        A=A+dA*dt*la-r+feed*(1-A)
        B=B+dB*dt*lb+r-(kill+feed)*B
        np.clip(A,0,1,out=A); np.clip(B,0,1,out=B)
    return B
for name,f,k in [("coral",.037,.060),("spots",.035,.065),("mazes",.029,.057),
                  ("worms",.046,.058),("holes",.034,.062),("rings",.030,.062)]:
    B=sim(f,k,4000,11,dt=0.02)
    sx,sy=SW//W,SH//H
    Bd=B[:sy*H,:sx*W].reshape(H,sy,W,sx).mean(axis=(1,3))
    print(f"{name:6s} var={Bd.var():.4f} fracB>0.25={float((Bd>0.25).mean()):.2f} maxB={B.max():.3f}")
