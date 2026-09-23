import sys, math; sys.path.insert(0,".")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H

def make(name, Lfn, base_fg, hot_fg):
    cv=new_canvas(H,W)
    standing_figure(cv,40,30,Lfn,height=28.0,stance="contrapposto",base_fg=base_fg,hot_fg=hot_fg,iris_fg=96,one_eye=True)
    out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
    open("scratch/_vigil_tune3_%s.ans"%name,"w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")

# steep radial from upper-left corner + strong left bias; lmax small so falloff spans the body
def LS(x,y):
    r = light_field(x,y,30,8,lmax=16.0,ambient=0.12)
    axial = 0.5 + 0.7*(40-x)/18.0
    return max(0.0,min(1.0, r*0.5+axial*0.7))
make("steep", LS, 4, 15)

# monotone top-left light: brightest upper-left, dimmest lower-right (each limb shows its place)
def LM(x,y):
    t = 1.0 - (x/80.0*0.45 + y/46.0*0.55)
    return max(0.08, min(1.0, 0.12 + 0.95*t))
make("mono", LM, 4, 15)

# warden-style: central-ish source but steeper
def LW(x,y):
    return light_field(x,y,36,14,lmax=12.0,ambient=0.12)
make("warden", LW, 8, 15)
print("done")
