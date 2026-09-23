import numpy as np
SW,SH=320,184
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
for name,f,k in [("coral",.037,.060),("worms",.046,.058)]:
    B=sim(f,k,6000,11,dt=0.02)
    print(name,"full-res var=%.4f maxB=%.3f fracB>0.25=%.2f"%(B.var(),B.max(),float((B>0.25).mean())))
    # ascii preview downsampled 8x
    sx,sy=SW//40,SH//24
    Bd=B[:sy*24,:sx*40].reshape(24,sy,40,sx).mean(axis=(1,3))
    for row in Bd:
        print("".join(" .:-=+*#@"[min(8,int(v*9))] for v in row))
    print()
