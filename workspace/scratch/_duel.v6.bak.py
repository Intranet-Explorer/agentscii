#!/usr/bin/env python3
# THE DUEL // "opposites, face to face" -- raze solo. AGENTSCI figurative/scene register.
#
# WHY NEW: the house has STANDING figures (VIGIL/TWO SENTINELS), a figure IN MOTION (THE LEAP),
#  and SCROLL sequences (ABYSS) -- but NO two-figure composition. THIS is the first scene with two
#  bodies in one frame, built on hollis's capsule()/joint_dot() lit-tube primitives as its CORE
#  (NOT hand-rolled shading -- the systemic defect Tyler flagged in OBSERVER_NOTES #2 was three pieces
#   each hand-rolling torso/limbs into flat bars; this uses the shared lit-capsule unit instead).
#
# THE MOVE: a WARM figure on the LEFT and its COOL OPPOSITE on the RIGHT, facing each other across a
#  charged void. Each is lit from ITS OWN side (warm light upper-left, cool light upper-right) so their
#  LIT fronts turn toward one another -- they illuminate each other's faces while their backs fall to
#  shadow. The two hues (amber vs cyan) are what separates them; the crackling void between them is the
#  tension of the standoff, textured not flat-black.
#
# THE TUBE READ (the fix for the flat-column defect): a capsule's cross-section is shaded so its CENTER
#  COLUMN is brightest and its EDGES fall to deep shadow -- a strong cylindrical color falloff on a SOLID
#  glyph. Color carries the rounded-tube read, NOT density (density collapses to full-block █ across any
#  lit region, which is exactly what made earlier legs read as stacked horizontal bars).
import sys, os, math, random
sys.path.insert(0, os.getcwd())
import figure_common as fc
import canvas as C

W, H = 80, 52
SEED = 13
RAMP = fc.RAMP
# SGR color codes (only 30-47 / 90-107 pass through fc.c() unchanged; 0-7 get remapped)
WARM_HOT=95; WARM_HI=93; WARM_MID=91          # white-hot -> bright amber -> orange
COOL_HOT=96; COOL_MID=96; COOL_LO=94           # bright-cyan highlight -> deep-blue shadow
def warm_wheel(li):
    if li > 0.85: return WARM_HOT
    if li < 0.32: return WARM_MID
    return WARM_HI
def cool_wheel(li):
    if li > 0.88: return COOL_HOT              # bright cyan highlight
    if li < 0.32: return 94                    # deep blue shadow (stays COOL, never yellow)
    return 96                            # mid = cyan

# directional light per figure -- uniform-ish along the body, so limbs aren't all in shadow
def Lw(x, y):    # warm source, upper-left of the LEFT figure
    return fc.light_field(x, y, 16.0, 8.0, lmax=46.0, ambient=0.30)
def Lc(x, y):    # cool source, upper-right of the RIGHT figure
    return fc.light_field(x, y, 64.0, 8.0, lmax=46.0, ambient=0.30)

def cap(cv, x0,y0,x1,y1,hw, Lfn, wheel):
       # solid-glyph tube; cylindrical COLOR falloff across the width gives the rounded read
    seg = math.hypot(x1-x0,y1-y0) or 1.0
    ux,uy=(x1-x0)/seg,(y1-y0)/seg; hw_i=int(round(hw))
    for y in range(int(min(y0,y1))-hw_i-1,int(max(y0,y1))+hw_i+2):
        for x in range(int(min(x0,x1))-hw_i-1,int(max(x0,x1))+hw_i+2):
            t=max(0.0,min(1.0,((x-x0)*ux+(y-y0)*uy)/seg))
            px,py=x0+t*(x1-x0),y0+t*(y1-y0)
            d=math.hypot(x-px,y-py)
            if d<=hw:
                cyl = 1.0 - 0.78*(d/hw)**1.25          # strong rounded falloff across the tube width
                Li=Lfn(x,y)*cyl
                ch,fg=fc.shade(Li,base_fg=wheel(Li),hot_fg=wheel(min(1.0,Li+0.2)),ramp=RAMP)
                fc.set_cell(cv,x,y,"\u2588",wheel(Li),0)    # solid block; color carries the tube

def joint(cv,cx,cy,r,Lfn,wheel):
    rr=int(round(r))
    for y in range(int(cy-rr),int(cy+rr)+1):
        for x in range(int(cx-rr),int(cx+rr)+1):
            if math.hypot(x-cx,y-cy)<=r:
                cyl=1.0-0.78*(math.hypot(x-cx,y-cy)/r)**1.25
                Li=Lfn(x,y)*cyl
                fc.set_cell(cv,x,y,"\u2588",wheel(Li),0)

def head(cv,cx,cy,r,Lfn,wheel,iris):
    for y in range(int(cy-r),int(cy+r)+1):
        t=(y-cy)/r
        if abs(t)<=1.0:
            hwx=r*1.15*math.sqrt(1.0-t*t)
            for x in range(int(cx-hwx),int(cx+hwx)+1):
                if cv[y][x][0]!=' ': continue
                d=math.hypot(x-cx,y-cy)/r
                cyl=1.0-0.55*min(1.0,d)**1.2
                Li=Lfn(x,y)*cyl
                fc.set_cell(cv,x,y,"\u2588",wheel(Li),0)
    fc.brow_ridge(cv,cx,cy-r*0.35,r*0.9,Lfn,base_fg=wheel(0.6),hot_fg=wheel(1.0))
    fc.eye(cv,cx+ (r*0.2 if iris>0 else -r*0.2),cy+r*0.1,r=r*0.45,iris_fg=iris,glint=True)

def figure(cv, hipx, hipy, facing_right, Lfn, wheel, iris):
       # full body: torso + two splayed legs + two arms + head. Legs SPLAY outward so they read as
       # limbs not stacked bars; strong cylindrical color shading rounds every tube.
    sh_y = hipy - 12.0; head_cy = sh_y - 5.0
    sgn = 1 if facing_right else -1
    cap(cv, hipx-3,hipy, hipx+3,hipy, 2.6, Lfn,wheel)                   # pelvis bar
    joint(cv,hipx,hipy,3.4,Lfn,wheel)
    cap(cv, hipx,hipy, hipx+sgn*1.5,sh_y, 4.0, Lfn,wheel)              # spine leans toward light
    joint(cv,hipx+sgn*0.7,(hipy+sh_y)/2,3.4,Lfn,wheel)
    cap(cv, hipx-3.5,sh_y, hipx+3.5,sh_y, 1.8, Lfn,wheel)              # shoulders bar
        # LEGS splay with BENT knees: thigh down-inboard, shin angles OUT -- the bend breaks the
        # vertical stacking that reads as flat bars (the systemic defect). Weight leg near-straight,
        # free leg kicks wide.
    cap(cv, hipx-2.5,hipy, hipx-1.0,hipy+12, 2.3, Lfn,wheel)           # weight thigh (down-inboard)
    joint(cv,hipx-1.5,hipy+12,1.7,Lfn,wheel)                            # weight knee
    cap(cv, hipx-1.0,hipy+12, hipx-3.5,hipy+24, 2.0, Lfn,wheel)        # weight shin angles out
    cap(cv, hipx+2.5,hipy, hipx+sgn*4.0,hipy+11, 2.3, Lfn,wheel)       # free thigh kicks out
    joint(cv,hipx+sgn*3.2,hipy+11,1.7,Lfn,wheel)                        # free knee
    cap(cv, hipx+sgn*4.0,hipy+11, hipx+sgn*7.5,hipy+23, 1.9, Lfn,wheel)# free shin angles wide
       # ARMS: front arm reaches toward the opponent (toward center), back arm flares out
    cap(cv, hipx-3.0,sh_y+1, hipx-sgn*5.0,sh_y+8, 2.2, Lfn,wheel)     # back arm flares out
    joint(cv,hipx-sgn*4.0,sh_y+4.5,1.3,Lfn,wheel)
    cap(cv, hipx+3.0,sh_y+1, hipx+sgn*7.0,sh_y+2, 2.2, Lfn,wheel)     # front arm reaches in
    joint(cv,hipx+sgn*5.0,sh_y+1.5,1.3,Lfn,wheel)
       # HEAD toward the light (toward center), facing the opponent
    head(cv, hipx+sgn*1.5, head_cy, 3.6, Lfn, wheel, iris)

def main():
    cv = fc.new_canvas(H, W)
       # P1: two figures facing each other -- warm left (faces right), cool right (faces left)
    figure(cv, 27.0, 34.0, True,  Lw, warm_wheel, 91)                  # warm, faces right/center
    figure(cv, 53.0, 34.0, False, Lc, cool_wheel, 94)                  # cool opposite, faces left/center

       # P2: the charged void between them -- a crackling vertical seam at center
    rng = random.Random(SEED+1)
    def is_sub(x,y): return cv[y][x][0]!=' '
    for y in range(6,H-4):
        if rng.random()<0.5:
            cx=W//2+rng.randint(-1,1)
            ch,fg=fc.shade(rng.random(),base_fg=96,hot_fg=94,ramp=RAMP)
            if not is_sub(cx,y): fc.set_cell(cv,cx,y,ch,fg,0)

       # P3: texture the negative space -- warm dust left, cool dust right (thin, reads as void)
    for y in range(H):
        for x in range(W):
            if is_sub(x,y): continue
            if rng.random()>0.22: continue
            Li = Lw(x,y) if x<W//2 else Lc(x,y)
            idx=rng.randint(len(RAMP)//2,len(RAMP)-1)
            fc.set_cell(cv,x,y,RAMP[idx], (warm_wheel(Li) if x<W//2 else cool_wheel(Li)),0)

       # P4: frame + title card
    out=[]
    out.append(fc.c(13)+"\u2554"*W)
    fc.render(cv,out)
    out.append(fc.c(13)+"\u2557"*W)
    C.write_ans("_duel.ans",out,title="THE DUEL v0.5 // opposites, face to face",handles="raze")
    C.write_ans("_duel.ans",out,title="THE DUEL v0.4 // opposites, face to face",handles="raze")

if __name__=="__main__":
    main()
