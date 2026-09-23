import re, math, random, sys
sys.path.insert(0,'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr

def render_grid(out_rows):
    grid={}; fg=7; bg=0; r=0
    for ln in out_rows:
        c=0; j=0
        while j<len(ln):
            ch=ln[j]
            if ch=='\x1b' and j+1<len(ln) and ln[j+1]=='[':
                k=j+2; numbuf=''
                while k<len(ln) and ln[k]!='m': numbuf+=ln[k]; k+=1
                params=[int(pp) for pp in numbuf.split(';') if pp!=''] if numbuf else [0]
                for pp in params:
                    if pp==0: fg,bg=7,0
                    elif 30<=pp<=37: fg=pp-30
                    elif 90<=pp<=97: fg=pp-90+8
                    elif 40<=pp<=47: bg=pp-40
                    elif 100<=pp<=107: bg=pp-100+8
                j=k+1
            else:
                grid[(r,c)]=(ch,fg,bg); c+=1; j+=1
        r+=1
    return grid

def analyze(out_rows):
    grid=render_grid(out_rows)
    DENS=set('▓▒░'); BOX=set("═║╔╗╚╝╠╣╦╩╬─│┌┐└┘├┤┬┴┼")
    rows={}
    for (rr,cc),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        rows.setdefault(rr,[]).append(ch)
    border_rows=set()
    for rr,chlist in rows.items():
        run=mx=0
        for ch in chlist:
            if ch in BOX: run+=1; mx=max(mx,run)
            else: run=0
        if mx>40: border_rows.add(rr)
    subject={}
    for (rr,cc),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        if rr in border_rows: continue
        if ch in DENS: continue
        subject[(rr,cc)]=(ch,fg,bg)
    # flat regions
    THRESH=40; large=[]; visited=set()
    for start in list(subject):
        if start in visited: continue
        key=subject[start]; stack=[start]; region=[]
        while stack:
            cur=stack.pop()
            if cur in visited: continue
            visited.add(cur); region.append(cur)
            rr,cc=cur
            for nxt in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                if nxt not in visited and subject.get(nxt)==key:
                    stack.append(nxt)
        if len(region)>THRESH: large.append((len(region),key))
    # half-block %
    HB=set('▀▄█'); total=0; hb=0
    for (rr,cc),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        total+=1
        if ch in HB: hb+=1
    pct=100*hb/max(total,1)
    return pct,hb,total,len(large),sorted([l[0] for l in large],reverse=True)[:5]

# build a test figure with a parameterized face ramp
def build(face_levels, jitter, cloak_levels):
    W,H=80,40
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
    BAYER=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
    def bayer(px,py): return BAYER[py%4][px%4]/16.0
    def ramp(levels,L):
        n=len(levels); idx=min(n-1,int(L*n)); return levels[idx]
    for py in range(cv.ph):
        for px in range(W):
            L=light(px,py)
            Lj=max(0.0,min(1.0,L+jitter*(bayer(px,py)-0.5)))
            if in_cranium(px,py) or in_neck(px,py):
                cv.set_pixel(px,py,ramp(face_levels,Lj))
            elif in_shoulder(px,py):
                t=(py-SHOULDER_TOP)/max(1,cv.ph-SHOULDER_TOP)
                wave=math.sin(px*0.95+py*0.10); fold=(wave+1.0)/2.0
                base=L*0.60+fold*0.40
                cv.set_pixel(px,py,ramp(cloak_levels,max(0.0,min(1.0,base+jitter*(bayer(px,py)-0.5)))))
    out=cv.render()
    out.insert(0,sgr(8)+"\u2550"*W); out.append(sgr(8)+"\u2550"*W)
    return out

configs=[
 ("pinned-4lvl", [7,8,4,0], 0.0),
 ("fine-grey6",  [15,7,8,4,3,0], 0.05),
 ("fine-grey8",  [15,11,7,8,4,3,0,0], 0.05),
 ("grey3-jit",   [7,8,4], 0.06),
 ("grey4-jit",   [15,7,8,4], 0.06),
]
for name,levels,jit in configs:
    out=build(levels,jit,[7,8,4])
    pct,hb,total,nflat,top=analyze(out)
    print("%-12s levels=%-16s jit=%.2f -> halfblock %.1f%% (%d/%d)  flat_regions=%d top=%s"%(name,levels,jit,pct,hb,total,nflat,top))

print("\n=== per-pixel-row offset variants (top/bottom differ -> high ▀ + smooth) ===")
def build2(face_levels, jit, cloak_levels, ppx):
    W,H=80,40
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
    BAYER=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
    def bayer(px,py): return BAYER[py%4][px%4]/16.0
    def ramp(levels,L):
        n=len(levels); idx=min(n-1,int(L*n)); return levels[idx]
    for py in range(cv.ph):
        # per-pixel-row offset: top pixel (even py) and bottom pixel (odd py) get
        # slightly different brightness so they land on adjacent shades -> ▀.
        for px in range(W):
            L=light(px,py)
            rowoff = ppx if (py%2==0) else -ppx
            Lj=max(0.0,min(1.0,L+jit*(bayer(px,py)-0.5)+rowoff))
            if in_cranium(px,py) or in_neck(px,py):
                cv.set_pixel(px,py,ramp(face_levels,Lj))
            elif in_shoulder(px,py):
                t=(py-SHOULDER_TOP)/max(1,cv.ph-SHOULDER_TOP)
                wave=math.sin(px*0.95+py*0.10); fold=(wave+1.0)/2.0
                base=L*0.60+fold*0.40
                Lj2=max(0.0,min(1.0,base+jit*(bayer(px,py)-0.5)+rowoff))
                cv.set_pixel(px,py,ramp(cloak_levels,Lj2))
    out=cv.render()
    out.insert(0,sgr(8)+"\u2550"*W); out.append(sgr(8)+"\u2550"*W)
    return out

for name,levels,jit,ppx in [
  ("grey6-ppx.03", [15,7,8,4,3,0], 0.05, 0.03),
  ("grey6-ppx.05", [15,7,8,4,3,0], 0.05, 0.05),
  ("grey8-ppx.04", [15,11,7,8,4,3,0,0], 0.05, 0.04),
  ("grey5-ppx.06", [15,7,8,4,0], 0.05, 0.06),
]:
    out=build2(levels,jit,[7,8,4],ppx)
    pct,hb,total,nflat,top=analyze(out)
    print("%-13s levels=%-16s jit=%.2f ppx=%.2f -> halfblock %.1f%% (%d/%d)  flat_regions=%d top=%s"%(name,levels,jit,ppx,pct,hb,total,nflat,top))
