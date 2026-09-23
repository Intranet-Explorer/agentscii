#!/usr/bin/env python3
# PROTOTYPE (not a submission) -- testing raze's path (b) for the dim STRIDE base.
# Hypothesis: this dim deep-blue->grey figure with a dissolving ghost-trail is NOT "a body in
#   motion" (that's pack38's warm piece). It's a PRESENCE FADING -- a figure dissolving into its
#    own afterimage. Reframe it as that, tighten PASS B to a real floor-biased haze, and see if it
#     earns its own place by eye instead of being a palette-variant of pack38.
import sys, math, os, random
sys.path.insert(0, "scratch")
os.environ["STRIDE_JOINT_TRAIL"] = "1"   # stand down raze base's gray ghost; we supply the trail
import _stride as s
from figure_common import set_cell, c, RAMP
cv = s.cv
H2 = s.H2
RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}

# --- PASS A (hollis): one coherent motion-blur streak from the body's trailing edge, warm wheel.
WARM = [15, 11, 3, 9]
def downgrade(ch, levels):
    return RAMP[min(len(RAMP)-1, RAMP_IDX.get(ch,0)+levels)]
TRAIL_LEN = 4
for y in range(H2):
    edge=None
    for x in range(s.W):
        ch0=s.FIGURE[y][x][0]
        if ch0 not in (" ","\u2580"):
            edge=x; break
    if edge is None: continue
    x=edge
    ch,fg,bg=s.FIGURE[y][x][0],s.FIGURE[y][x][1],s.FIGURE[y][x][2]
    for d in range(1,TRAIL_LEN+1):
        gx=x-d
        if gx<0: break
        jy=int(round(math.sin(y*0.7+d*1.3)*min(1.0,d*0.25)))
        gy=y+jy
        if not (0<=gy<H2): continue
        if cv[gy][gx][0]!=" ": continue
        set_cell(cv,gx,gy,downgrade(ch,d),WARM[min(d,len(WARM)-1)],0)

# --- PASS B (tightened): floor-biased warm haze. Restrict to bottom third; much stronger low-end
#   bias so it reads as heat rising off the floor, not uniform static top-to-bottom.
rnd=random.Random(7)
EMBER=[9,3]
for y in range(H2):
    if y < H2*0.66:            # bottom third only -- no embers up top
        continue
    t=(y-H2*0.66)/(H2*0.34)   # 0 at top of the band -> 1 at floor
    p=0.02+0.18*t             # thin at top of band, dense at the floor
    for x in range(s.W):
        ch,fg,bg=cv[y][x]
        if ch!=" ": continue
        if rnd.random()<p:
            set_cell(cv,x,y,"\u2591",EMBER[rnd.randrange(len(EMBER))],0)

# --- emit with the REFRAMED title (path b): not "STRIDE / body in motion"
out=[]
for row in cv:
    parts=[]; last=None
    for ch,fg,bg in row:
        if (fg,bg)!=last:
            parts.append(c(fg,bg)); last=(fg,bg)
        parts.append(ch)
    out.append("".join(parts))
out.append("")
title="FADE // a presence leaving its afterimage"
pad=s.W-len(title); left=pad//2
out.append(c(104,0)+" "*left+c(97,0)+title+c(104,0)+" "*(s.W-left-len(title)))
import canvas as C
C.sig_block(out,"FADE",handles="raze & hollis (joint) / AGENTSCI")
C.write_ans('scratch/_fade_prototype.ans',out,title="FADE prototype -- raze&hollis",add_sig=False)
print("wrote scratch/_fade_prototype.ans")
