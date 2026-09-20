import numpy as np
SW,SH=320,184
def lap9(a):
    return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)
def sim(feed,kill,steps,seed,dA=1.0,dB=0.5,dt=0.02,bseed=0.6):
    rng=np.random.default_rng(seed)
    A=np.ones((SH,SW)); B=np.zeros((SH,SW))
    cy0,cy1=SH//2-8,SH//2+9; cx0,cx1=SW//2-14,SW//2+15
    B[cy0:cy1,cx0:cx1]=bseed
    for _ in range(steps):
        la=lap9(A); lb=lap9(B)
        r=A*B*B
        A=A+dA*dt*la-r+feed*(1-A)
        B=B+dB*dt*lb+r-(kill+feed)*B
        np.clip(A,0,1,out=A); np.clip(B,0,1,out=B)
    return B
for name,f,k in [("coral",.037,.060),("spots",.035,.065),("mazes",.029,.057),
                   ("worms",.046,.058),("holes",.034,.062)]:
    B=sim(f,k,8000,11,bseed=0.6,dt=0.02)
    print(name,"var=%.4f maxB=%.3f frac>0.25=%.2f"%(B.var(),B.max(),float((B>0.25).mean())))
