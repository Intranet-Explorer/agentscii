import numpy as np
SW,SH = 200,115
def lap5(a): return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)
f,k,dA,dB,dt,N = 0.035,0.062,1.0,0.5,0.01,4000
A=np.ones((SH,SW)); B=np.zeros((SH,SW))
B[SH//2-3:SH//2+3, SW//2-6:SW//2+7]=1.0
for i in range(N):
    la=lap5(A); lb=lap5(B)
    r=A*A*B*3.0
    A=A+dA*dt*la-r+f*(1-A)
    B=B+dB*dt*lb+r-(k+f)*B
    if i%800==0:
        print(i, "A",A.min(),A.mean(),A.max(), "B",B.min(),B.mean(),B.max())
