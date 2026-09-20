import math, sys
sys.path.insert(0,'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr
W,H=80,40
BAYER=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
def bayer(px,py): return BAYER[py%4][px%4]/16.0

def build(face_levels, jit, amp_fn):
    cv=HalfBlockCanvas(W,H,bg=0)
    BLACK,DGREY,MGREY,BLUE,TEAL=0,8,7,4,6
    CX=W//2; CRAN_CY=26; CRAN_R=18; NECK_Y=CRAN_CY+CRAN_R-3; SHOULDER_TOP=NECK_Y+6
    LX,LY=14.0,10.0
    def light(px,py):
        d=math.hypot(px-LX,py-LY); return max(0.0,1.0-d/72.0)
    def in_cranium(px,py): return math.hypot(px-CX,py-CRAN_CY)<=CRAN_R
    def in_neck(px,py):
        if not (NECK_Y-2<=py<=SHOULDER_TOP+3): return False
        t=(py-NECK_Y)/max(1.0,SHOULDER_TOP+3-NECK_Y); half=6.5+t*4.0
        return abs(px-CX)<=half
    def in_cloak(px,py):
        if not (SHOULDER_TOP<=py<cv.ph): return False
        t=(py-SHOULDER_TOP)/max(1,cv.ph-SHOULDER_TOP); half=16+t*t*30
        return abs(px-CX)<=half
    in_shoulder=in_cloak
    def ramp(levels,L):
        n=len(levels); idx=min(n-1,int(L*n)); return levels[idx]
    for py in range(cv.ph):
        sign = 1 if py%2==0 else -1
        for px in range(W):
            L=light(px,py)
            amp = amp_fn(px,py)
            jt = jit*(bayer(px,py)-0.5) + sign*amp
            Lj=max(0.0,min(1.0,L+jt))
            if in_cranium(px,py) or in_neck(px,py):
                cv.set_pixel(px,py,ramp(face_levels,Lj))
            elif in_shoulder(px,py):
                t=(py-SHOULDER_TOP)/max(1,cv.ph-SHOULDER_TOP)
                wave=math.sin(px*0.95+py*0.10); fold=(wave+1.0)/2.0
                base=L*0.60+fold*0.40
                cv.set_pixel(px,py,ramp([7,8,4],max(0.0,min(1.0,base+jt))))
    out=cv.render()
    out.insert(0,sgr(8)+"\u2550"*W); out.append(sgr(8)+"\u2550"*W)
    return out

# fine ramp (7 levels, subtle steps) + per-column-varying offset amplitude
FINE=[15,7,8,4,3,0]
configs=[
 ("gentle-colhash", FINE, 0.06, lambda px,py: 0.05+0.05*((px*7+3)%3)/2.0),
 ("mild-uniform",   FINE, 0.06, lambda px,py: 0.06),
]
for name,levels,jit,ampf in configs:
    out=build(levels,jit,ampf)
    open('scratch/_q_%s.ans'%name,'w',encoding='cp437').write('\n'.join(out))
print("built")
