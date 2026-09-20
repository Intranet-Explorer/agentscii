import sys; sys.path.insert(0,"/Users/octo/agentscii/workspace/scratch")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H

def L(x,y):
    t = 1.0 - ((x-34)/12.0*0.5 + (y-8)/30.0*0.5)
    return max(0.0, min(1.0, t))

cv=new_canvas(H,W)
info=standing_figure(cv,40,30,L,height=28.0,stance="contrapposto",base_fg=4,hot_fg=15,iris_fg=96,one_eye=True)

# RIM LIGHT: bright highlight on the lit (left/upper) edge of each limb -> sells "lit steel form".
# Walk each capsule's left contour and paint a 1-cell bright rim. Reuse standing_figure's geometry
# by re-deriving the same segment endpoints it used (mirror its internal layout).
def rim_segment(x0,y0,x1,y1,halfw,fg):
    import math
    seg=math.hypot(x1-x0,y1-y0) or 1.0; ux,uy=(x1-x0)/seg,(y1-y0)/seg
    for t in range(0,101,2):
        tt=t/100.0
        px,py=x0+tt*(x1-x0), y0+tt*(y1-y0)
        # left edge = perpendicular to the left (toward the light at upper-left)
        ex,ey=px-uy*halfw, py+ux*halfw     # one side
        F.set_cell(cv,int(round(ex)),int(round(ey)),"\u2588",fg,0)

# approximate the figure's limbs (same as standing_figure internals) and rim their lit edges
hipx,hipy=40,30; torso_h=28*0.34; leg_h=28*0.46; head_r=max(2.0,28*0.11)
shoulder_y=hipy-torso_h; neck_y=shoulder_y-head_r*0.4; head_cy=neck_y-head_r
sh_dx=(torso_h*0.30); hip_dx=(leg_h*0.10)
sh_lx,sh_rx=hipx-sh_dx,hipx+sh_dx; hip_lx,hip_rx=hipx-hip_dx,hipx+hip_dx
rim=97  # bright white rim
# torso + limbs lit-edge rims
rim_segment(hipx,hipy,hipx,shoulder_y,4.0,rim)            # torso centerline->rim
rim_segment(sh_lx,shoulder_y,sh_rx,shoulder_y,2.0,93)     # shoulders bar
rim_segment(sh_lx,shoulder_y,hipx-1,shoulder_y+torso_h*0.7,2.0,96)  # across arm
rim_segment(hip_lx,hipy,hip_lx-1.5,hipy+leg_h,2.6,93)    # weight leg
rim_segment(hip_rx,hipy,hip_rx+2.0,hipy+leg_h*0.94,2.4,93)  # free leg
# head rim (lit left edge of skull)
for y in range(int(head_cy-head_r),int(head_cy+head_r)+1):
    hw=head_r*1.25*((1-((y-head_cy)/head_r)**2)**0.5 if abs((y-head_cy)/head_r)<=1 else 0)
    F.set_cell(cv,int(round(hipx-hw)),y,"\u2588",97,0)

out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
open("scratch/_vigil_rim.ans","w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")
print("done")
