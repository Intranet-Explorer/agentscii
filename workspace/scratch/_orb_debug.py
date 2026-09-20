import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas
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

# Check specific pixels that the file-decoder reported as white at top of iris
for (px,py) in [(40,33),(40,35),(40,37),(40,39),(40,41),(40,43),(40,45),(30,33),(50,33)]:
    u=(px-cx)/half_w
    up,lo=opening_half_h(u); dy=py-cy
    d=math.hypot(px-cx,py-cy)
    inop=in_opening(px,py)
    print(f"px={px} py={py}: u={u:.2f} up={up:.1f} lo={lo:.1f} dy={dy:.1f} d={d:.1f} in_opening={inop} in_annulus={pupil_r<d<iris_r}")
