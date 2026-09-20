import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas
# Re-run v10 build inline and check the ACTUAL canvas after cleanup
W=80; H=52
cv=HalfBlockCanvas(W,H,bg=0)
ph=cv.ph; cx=W//2; cy=ph//2
half_w=30; h_upper=20; h_lower=13; exp_u,exp_l=0.50,0.42
def opening_half_h(u):
    a=abs(u)
    if a>=1.0: return (0.0,0.0)
    return h_upper*(1-u*u)**exp_u, h_lower*(1-u*u)**exp_l
def in_opening(px,py):
    u=(px-cx)/half_w
    if abs(u)>=1.0: return False
    up,lo=opening_half_h(u); dy=py-cy
    return -up<=dy<=lo
iris_r=17; pupil_r=9
lx,ly=cx-24,cy-30
def L(px,py): return max(0.03,1.0-math.hypot(px-lx,py-ly)/80.0)
def gramp(l):
    if l>0.74: return 15
    if l>0.52: return 7
    if l>0.30: return 8
    return 0
def aramp(l):
    if l>0.62: return 11
    if l>0.34: return 9
    return 3
NCRYPTS=8

for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u); dy=py-cy
        if not(-up<=dy<=lo): continue
        l=L(px,py); vert=1.0-(dy/max(1.0,(up+lo)))*0.26; l=max(0.03,min(1.0,l*vert))
        cv.set_pixel(px,py,gramp(l))
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u); dy=py-cy
        if 0<=dy<4 and -up<=dy<=lo:
            cur=cv.get_pixel(px,py)
            if cur==15: cv.set_pixel(px,py,7)
            elif cur==7 and 1<=dy<3: cv.set_pixel(px,py,8)
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u); dy=py-cy
        if -up-1.5<=dy<-up+0.5 or lo-0.5<=dy<lo+1.5: cv.set_pixel(px,py,0)
        lid_thick=4.0*(1.0-u*u)+1.0
        if -up-lid_thick<=dy<-up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick); L_=L(px,py)*(0.6+0.4*depth)
            col=7 if L_>0.5 else (8 if L_>0.32 else 0); cv.set_pixel(px,py,col)
        ll=3.0*(1.0-u*u)+0.5
        if lo+1.5<=dy<lo+1.5+ll:
            depth=(dy-(lo+1.5))/max(0.5,ll); L_=L(px,py)*(1.0-0.7*depth)
            col=8 if L_>0.34 else 0; cv.set_pixel(px,py,col)
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        dx=px-cx; dy=py-cy; d=math.hypot(dx,dy)
        if d<iris_r:
            ang=math.atan2(dy,dx); t_rad=(d-pupil_r)/(iris_r-pupil_r)
            base_l=1.0-0.66*max(0.0,t_rad); l=base_l
            band=math.sin(ang*NCRYPTS+d*0.14)
            if band>0.55: l*=0.26
            elif band<-0.35: l=min(1.0,l*1.18)
            cv.set_pixel(px,py,aramp(l))
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r+0.3<=d<pupil_r+2.4: cv.set_pixel(px,py,11)
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if iris_r-2.6<=d<iris_r+0.3: cv.set_pixel(px,py,3)
cv.fill_circle(cx,cy,pupil_r,0); cv.fill_circle(cx-3.0,cy-3.4,1.7,15)
# annulus cleanup
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r<d<iris_r and cv.get_pixel(px,py) not in (3,9,11):
            ang=math.atan2(py-cy,px-cx); t_rad=(d-pupil_r)/(iris_r-pupil_r)
            l=1.0-0.66*max(0.0,t_rad)
            band=math.sin(ang*NCRYPTS+d*0.14)
            if band>0.55: l*=0.26
            elif band<-0.35: l=min(1.0,l*1.18)
            cv.set_pixel(px,py,aramp(l))

# NOW check the actual canvas state inside annulus
from collections import Counter
cnt=Counter()
for py in range(ph):
    for px in range(W):
        c=cv.get_pixel(px,py)
        if c in (3,9,11): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r<d<iris_r: cnt[c]+=1
print("CANVAS non-amber inside annulus after cleanup:", dict(cnt))
# show the top of iris on the actual canvas (cell rows 15-26)
def m(c): return 'A' if c in (3,9,11) else ('.' if c==0 else str(c))
print("=== CANVAS top-of-iris cell rows 15-26 ===")
for cr in range(15,27):
    print(f"{cr:2d} T {''.join(m(cv.get_pixel(px,cr*2)) for px in range(W))}")
