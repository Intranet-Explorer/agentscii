import sys, math; sys.path.insert(0,".")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H

def make(name, Lfn, base_fg, hot_fg):
    cv = new_canvas(H, W)
    standing_figure(cv,40,30,Lfn,height=28.0,stance="contrapposto",base_fg=base_fg,hot_fg=hot_fg,iris_fg=96,one_eye=True)
    out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
    open("scratch/_vigil_tune_%s.ans"%name,"w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")

# A: dim base + bright hot, light close upper-left, big lmax so falloff spans the body
def LA(x,y): return light_field(x,y,28,12,lmax=40.0,ambient=0.10)
make("A", LA, 3, 14)

# B: directional left-bias (axial) + radial, mid base
def LB(x,y):
    r = light_field(x,y,30,12,lmax=35.0,ambient=0.10)
    axial = 0.5 + 0.5*(40-x)/20.0          # brighter on the left (x<40)
    return max(0.0,min(1.0, r*0.6 + axial*0.5))
make("B", LB, 3, 14)

# C: even closer light, strong falloff, dim base
def LC(x,y): return light_field(x,y,34,16,lmax=22.0,ambient=0.08)
make("C", LC, 3, 14)

print("done A/B/C")
