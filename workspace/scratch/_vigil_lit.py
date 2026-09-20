import sys, math; sys.path.insert(0,"/Users/octo/agentscii/workspace/scratch")
import figure_common as F
from figure_common import new_canvas, set_cell, capsule, joint_dot, light_field, render, c, W, H

# A full standing figure built from the SAME capsule/joint_dot primitives standing_figure uses,
# but with a per-cell LIGHT->HUE map so each limb gets a real value range (deep-blue shadow ->
# cyan mid -> white highlight). This is what sells "lit steel form" that fixed base/hot can't.
cv=new_canvas(H,W)

def L(x,y):
    # lit from upper-left: radial falloff + left bias, full 0..1 range across the body bbox
    r = light_field(x,y,32,8,lmax=20.0,ambient=0.05)
    axial = 0.5 + 0.6*(40-x)/16.0
    return max(0.0,min(1.0, r*0.45+axial*0.7))

# light -> (glyph, fg): a multi-hue lit-steel ramp so density AND hue both track the light
def steel(L):
    L=max(0.0,min(1.0,L))
    idx=int(L*3+0.5)%4
    glyph="\u2588\u2593\u2592\u2591"[idx]
    if L>0.86: fg=15            # white-hot highlight
    elif L>0.70: fg=12         # bright cyan
    elif L>0.45: fg=6          # normal blue
    else: fg=4                 # deep-blue shadow
    return glyph,fg

def cap(x0,y0,x1,y1,halfw):
    seg=math.hypot(x1-x0,y1-y0) or 1.0; ux,uy=(x1-x0)/seg,(y1-y0)/seg; hw=int(round(halfw))
    for y in range(int(min(y0,y1))-hw-1,int(max(y0,y1))+hw+2):
        for x in range(int(min(x0,x1))-hw-1,int(max(x0,x1))+hw+2):
            t=max(0.0,min(1.0,((x-x0)*ux+(y-y0)*uy)/seg))
            px,py=x0+t*(x1-x0),y0+t*(y1-y0); d=math.hypot(x-px,y-py)
            if d<=halfw:
                Lv=L(x,y)*(1.0-0.35*(d/halfw))     # cylindrical falloff -> rounded tube shading
                ch,fg=steel(Lv); set_cell(cv,x,y,ch,fg,0)

def joint(cx,cy,r):
    rr=int(round(r))
    for y in range(int(cy)-rr,int(cy)+rr+1):
        for x in range(int(cx)-rr,int(cx)+rr+1):
            if math.hypot(x-cx,y-cy)<=r:
                ch,fg=steel(L(x,y)); set_cell(cv,x,y,ch,fg,0)

hipx,hipy=40,30; torso_h=28*0.34; leg_h=28*0.46; head_r=max(2.0,28*0.11)
shoulder_y=hipy-torso_h; neck_y=shoulder_y-head_r*0.4; head_cy=neck_y-head_r
sh_dx=torso_h*0.30; hip_dx=leg_h*0.10
sh_lx,sh_rx=hipx-sh_dx,hipx+sh_dx; hip_lx,hip_rx=hipx-hip_dx,hipx+hip_dx
# torso
cap(hipx,hipy,hipx,shoulder_y,4.0)
joint(hipx,(hipy+shoulder_y)/2,3.5)
# shoulders bar
cap(sh_lx,shoulder_y,sh_rx,shoulder_y,1.6)
# arms: one across body (watch), one at side
elbow_y=shoulder_y+torso_h*0.45
cap(sh_lx,shoulder_y,hipx-1,shoulder_y+torso_h*0.7,2.0); joint((sh_lx+hipx-1)/2,elbow_y,1.4)
cap(sh_rx,shoulder_y,sh_rx+1,shoulder_y+torso_h*0.85,1.9)
# legs: contrapposto (weight on left, free leg back)
foot_lx=hip_lx-1.5; foot_rx=hip_rx+2.0
cap(hip_lx,hipy,foot_lx,hipy+leg_h,2.6); joint((hip_lx+foot_lx)/2,hipy+leg_h*0.5,1.6)
cap(hip_rx,hipy,foot_rx,hipy+leg_h*0.94,2.4); joint((hip_rx+foot_rx)/2,hipy+leg_h*0.5,1.5)
# head: shaded skull + brow + one constructed eye (3/4 read)
for y in range(int(head_cy-head_r),int(head_cy+head_r)+1):
    t=(y-head_cy)/head_r
    if abs(t)>1.0: continue
    hw=head_r*1.25*math.sqrt(1-t*t)
    for x in range(int(hipx-hw),int(hipx+hw)+1):
        ch,fg=steel(L(x,y)); set_cell(cv,x,y,ch,fg,0)
# brow ridge (lit crest -> socket shadow)
for y in range(int(head_cy-head_r*0.35)-1,int(head_cy-head_r*0.35)+2):
    hw=head_r*0.9*math.sqrt(max(0.0,1-((y-(head_cy-head_r*0.35))/1.5)**2))
    for x in range(int(hipx-hw),int(hipx+hw)+1):
        Lv=L(x,y)*(0.95 if y<=head_cy-head_r*0.35 else 0.7)
        ch,fg=steel(Lv); set_cell(cv,x,y,ch,fg,0)
# one constructed eye: dark socket -> cyan iris -> white glint
ex,ey=head_r*0.25+hipx, head_cy+head_r*0.1
for dy in range(-1,2):
    for dx in range(-1,2):
        set_cell(cv,int(ex)+dx,int(ey)+dy,"\u2588",30,0)   # dark socket ring
set_cell(cv,int(ex),int(ey),"\u2588",96,0)                 # cyan iris
set_cell(cv,int(ex)-1,int(ey)-1,"\u2588",15,0)             # white glint

out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
open("scratch/_vigil_lit.ans","w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")
print("done")
