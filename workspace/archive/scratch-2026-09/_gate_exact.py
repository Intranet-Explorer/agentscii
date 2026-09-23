import re, math, random, sys
sys.path.insert(0,'scratch')
from halfblock import HalfBlockCanvas
from canvas import sgr

def parse_grid(path):
    raw=open(path,'rb').read().decode('cp437','replace')
    grid={}; fg=7; bg=0; r=0
    for ln in raw.split('\n'):
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

def gate_metrics(path):
    grid=parse_grid(path)
    HB=set('▀▄'); SH=set('▓▒░')
    subj=0; hbs=0; shs=0; colors=set()
    for (r,c),(ch,fg,bg) in grid.items():
        if ch==' ' and bg==0: continue
        subj+=1
        if ch in HB: hbs+=1
        if ch in SH: shs+=1
        vi = bg if (ch==' ' and bg!=0) else fg
        colors.add(vi)
    return dict(half_block_pct=100.0*hbs/max(subj,1),
                shade_char_pct=100.0*shs/max(subj,1),
                distinct_colors=len(colors), subject_cells=subj)

for p in ['scratch/_guardian.ans','scratch/_guardian.v19.ans']:
    m=gate_metrics(p)
    print("%-28s half_block=%.1f%%  shade_char=%.1f%%  distinct=%d  subj=%d"%(p,m['half_block_pct'],m['shade_char_pct'],m['distinct_colors'],m['subject_cells']))

print("\n=== per-pixel-row offset variants: EXACT gate metrics (subject-only) ===")
def build3(face_levels, jit, cloak_levels, ppx):
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
        rowoff = ppx if (py%2==0) else -ppx
        for px in range(W):
            L=light(px,py)
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
   ("grey6-ppx.04", [15,7,8,4,3,0], 0.05, 0.04),
   ("grey6-ppx.06", [15,7,8,4,3,0], 0.05, 0.06),
   ("grey6-ppx.08", [15,7,8,4,3,0], 0.05, 0.08),
   ("grey7-ppx.05", [15,11,7,8,4,3,0], 0.05, 0.05),
   ("grey5-ppx.06", [15,7,8,4,0], 0.05, 0.06),
]:
    out=build3(levels,jit,[7,8,4],ppx)
    tmp='scratch/_probe_%s.ans'%name
    open(tmp,'w',encoding='cp437').write('\n'.join(out))
    m=gate_metrics(tmp)
    ok = m['half_block_pct']>=42.2 and m['distinct_colors']>=7
    print("%-13s half_block=%.1f%%  shade_char=%.1f%%  distinct=%d  subj=%d  %s"%(name,m['half_block_pct'],m['shade_char_pct'],m['distinct_colors'],m['subject_cells'],'OK>=42.2/7' if ok else 'FAIL'))

print("\n=== independent per-pixel jitter (top/bottom differ locally, no stripe) ===")
def build4(face_levels, jit):
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
        # top pixel (even) and bottom pixel (odd) get INDEPENDENT jitter -> differ locally
        jtop = jit*(bayer(px,py)-0.5) if False else 0
        for px in range(W):
            L=light(px,py)
            jt = jit*(bayer(px,py)-0.5) + (0.03 if py%2==0 else -0.03)
            jb = jit*(bayer(px,py+1)-0.5) + (-0.03 if py%2==0 else 0.03)
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

for name,jit in [("indep-jit.06",0.06),("indep-jit.10",0.10),("indep-jit.14",0.14)]:
    out=build4([15,7,8,4,3,0],jit)
    tmp='scratch/_probe_%s.ans'%name
    open(tmp,'w',encoding='cp437').write('\n'.join(out))
    m=gate_metrics(tmp)
    print("%-13s half_block=%.1f%%  shade_char=%.1f%%  distinct=%d"%(name,m['half_block_pct'],m['shade_char_pct'],m['distinct_colors']))
