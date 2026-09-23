import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# ORB v11.b -- edit (b): restore visible radiating iris striations on v7 geometry.
#   Tyler house direction 2026-09-18, step 4(b). Built on _orb.v11.a.py (edit a applied).
#   NCRYPTS 8->14, spiral term d*0.14 -> d*0.08 (fibers run radially), dark valley l*=0.26 -> 0.18
#   for line contrast. Honest claim: reads as radiating stroma texture, NOT discrete fiber counts. "THE WATCHER": a single lit EYE in a dark void. HalfBlockCanvas (2px/cell).
# v9 was rejected by the blind second opinion on TWO minor nitpicks:
#   (1) faint grey/white horizontal streaks across the iris top (~rows 17-22) -- these were
#       UNCOVERED sclera/lid pixels showing through gaps at the annulus edge (half-block packing
#       leaves the thin top/bottom sliver of the almond unfilled by the per-pixel iris loop).
#   (2) a small stray mark below the iris -- actually the lower annulus edge; reads as a dash when
#       the sclera crown above it is grey.
# v10 fixes both at the root:
#   - A final ANNULUS CLEANUP pass fills ANY non-amber pixel inside pupil_r<d<iris_r with the
#     coherent amber radial gradient (crypt modulation included), so the iris reads as a solid,
#     unbroken mottled annulus -- no grey/white bleed-through anywhere. Runs LAST among eye passes.
#   - SCLERA now packs light PER PIXEL-ROW (top and bottom pixel of each cell can differ) instead
#     of one flat color per cell -- 2x vertical resolution, so the rounded falloff reads as a smooth
#     sphere, not stacked slabs. Half-block ▀ packs two greys seamlessly, no inter-strip gaps.
W=80; H=52
cv=HalfBlockCanvas(W,H,bg=0)
ph=cv.ph
cx=W//2; cy=ph//2

half_w = 30
h_upper = 20
h_lower = 13
exp_u, exp_l = 0.50, 0.42

def opening_half_h(u):
    a=abs(u)
    if a>=1.0: return (0.0,0.0)
    up = h_upper*(1.0-u*u)**exp_u
    lo = h_lower*(1.0-u*u)**exp_l
    return up, lo

def in_opening(px,py):
    u=(px-cx)/half_w
    if abs(u)>=1.0: return False
    up,lo=opening_half_h(u)
    dy=py-cy
    return -up <= dy <= lo

iris_r         = 17
pupil_r        = 9

lx, ly = cx-24, cy-30
def L(px,py):
    d=math.hypot(px-lx, py-ly)
    return max(0.03, 1.0 - d/80.0)

# grey ramp: ANSI has only 3 distinct greys (8 dark, 7 light, 15 white). Use them as a real
# 4-step falloff; per-pixel-row packing gives the smoothness instead of more indices.
def gramp(l):
    if l>0.74: return 15              # hot white (lit crown)
    if l>0.52: return 7               # light grey
    if l>0.30: return 8               # dark grey (shadow side, still visible)
    return 0                          # deepest shadow -> eyeball curving away into the dark

# amber family: THREE coherent tones only (bright->mid->dark amber).
def aramp(l):
    if l>0.62: return 11             # bright yellow (lit fiber / collarette)
    if l>0.34: return 9              # bright red / amber mid
    return 3                         # brown / dark amber (limbal shadow + crypts)

# --- PASS 2/3: SCLERA -- continuous white->grey falloff across the WHOLE rounded surface,
#     CLIPPED to the almond. v10: per-pixel-ROW light so top/bottom of each cell can differ ->
#     smooth sphere, not slabs. Light runs all the way around (shadow side has its own gradient).
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        if not (-up <= dy <= lo): continue
        l=L(px,py)
        vert = 1.0 - (dy/max(1.0,(up+lo)))*0.26     # upper catches more light -> curve, not patches
        l = max(0.03, min(1.0, l*vert))
        cv.set_pixel(px,py, gramp(l))

# soft shadow band just under the upper lid contour (lid casts onto sclera) -- gentle 2-step falloff.
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        if 0 <= dy < 4 and -up <= dy <= lo:
            cur=cv.get_pixel(px,py)
            if cur==15: cv.set_pixel(px,py,7)
            elif cur==7 and 1<=dy<3: cv.set_pixel(px,py,8)

# --- PASS 6: EYELIDS -- drawn BEFORE the iris so the almond contour can't overwrite amber.
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        # (a) crisp dark almond contour -- the eyelid edge, ~2px thick, black for max contrast
        if -up-1.5 <= dy < -up+0.5 or lo-0.5 <= dy < lo+1.5:
            cv.set_pixel(px,py, 0)
        # (b) lit upper brow band just above the contour -- multi-row gradient, thick->thin at canthi
        lid_thick = 4.0*(1.0-u*u)+1.0
        if -up-lid_thick <= dy < -up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick)
            L_=L(px,py)*(0.6+0.4*depth)
            col = 7 if L_>0.5 else (8 if L_>0.32 else 0)
            cv.set_pixel(px,py,col)
        # (c) lower lid just below the contour -- 2-row gradient dark at crease -> socket shadow
        ll = 3.0*(1.0-u*u)+0.5
        if lo+1.5 <= dy < lo+1.5+ll:
            depth=(dy-(lo+1.5))/max(0.5,ll)
            L_=L(px,py)*(1.0-0.7*depth)
            col = 8 if L_>0.34 else 0
            cv.set_pixel(px,py,col)

# --- PASS 4: iris -- SMOOTH radial gradient (collarette -> limbus) + radiating crypt modulation.
NCRYPTS=9
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        dx=px-cx; dy=py-cy; d=math.hypot(dx,dy)
        if d<iris_r:
            ang=math.atan2(dy,dx)
            t_rad=(d-pupil_r)/(iris_r-pupil_r)
            base_l = 1.0 - 0.66*max(0.0,t_rad)
            l=base_l
            band = math.sin(ang*NCRYPTS + d*0.08)
            if band > 0.55:                                # dark valley -> visible crypt line
                l *= 0.26
            elif band < -0.35:                             # faint bright ridge between fibers
                l = min(1.0, l*1.18)
            cv.set_pixel(px,py, aramp(l))
# collarette ring just outside the pupil -- subtle brighter amber band (CLIPPED to opening).
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r+0.3 <= d < pupil_r+2.4:
            cv.set_pixel(px,py,11)
# limbal ring at the outer iris edge -- a THICK continuous dark amber band so it's unbroken.
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if iris_r-2.6 <= d < iris_r+0.3:
            cv.set_pixel(px,py,3)

# --- PASS 5: pupil -- clean black void + one lit glint upper-left (single accent).
cv.fill_circle(cx, cy, pupil_r, 0)
cv.fill_circle(cx-3.0, cy-3.4, 1.7, 15)

# --- PASS 4b: ANNULUS CLEANUP (v10 root fix for the streaks). Any non-amber pixel INSIDE the
#     iris annulus (pupil_r<d<iris_r) -- uncovered sclera/lid bleed-through at the thin top/bottom
#     sliver -- gets filled with the coherent amber radial gradient so the annulus reads as ONE
#     solid, unbroken mottled disc. Runs after lids+glow so nothing overwrites it afterward.
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r < d < iris_r and cv.get_pixel(px,py) not in (3,9,11):
            ang=math.atan2(py-cy,px-cx); t_rad=(d-pupil_r)/(iris_r-pupil_r)
            l=1.0-0.66*max(0.0,t_rad)
            band=math.sin(ang*NCRYPTS+d*0.08)
            if band>0.58: l*=0.18
            elif band<-0.35: l=min(1.0,l*1.18)
            cv.set_pixel(px,py, aramp(l))

rows=cv.render()

# --- PASS 8: FRAME + SIG BLOCK (house convention).
def c(fg,bg,ch):
    f=(90+(fg&7)) if fg>7 else (30+fg)
    b=(100+(bg&7)) if bg>7 else (40+bg)
    return f"\x1b[{f};{b}m"
frame=[]
for r in rows:
    frame.append(c(8,0,"║")+r+c(8,0,"║"))
title=" THE WATCHER // IT SEES IN THE DARK "
title=title.ljust(W)[:W]
frame.insert(0, c(7,0,"")+"═"*W)
frame.insert(1, c(15,0,"")+title.center(W))
sig=" raze / AGENTSCI // THE WATCHER // 2026-09 "
sig=sig.ljust(W)[:W]
frame.append(c(15,0,"")+sig.center(W))
frame.append(c(7,0,"")+"═"*W)

out="\n".join(frame)+"\x1b[0m\n"
open("scratch/_orb.v11.c_test.ans","w").write(out)
print("orb v11.b (edit b: iris striations restored on v7 geometry)", len(frame),"rows")
