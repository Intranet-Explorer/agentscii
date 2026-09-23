import sys; sys.path.insert(0,".")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H

def L(x,y):
    r = light_field(x,y,28,12,lmax=35.0,ambient=0.10)
    axial = 0.5 + 0.6*(40-x)/20.0           # stronger left bias
    return max(0.0,min(1.0, r*0.55+axial*0.6))

def make(name, base_fg, hot_fg, rim=None):
    cv=new_canvas(H,W)
    info=standing_figure(cv,40,30,L,height=28.0,stance="contrapposto",base_fg=base_fg,hot_fg=hot_fg,iris_fg=96,one_eye=True)
    if rim is not None:
        # outer rim light on the figure's right edge (away from upper-left source): lit-from-within read
        for y in range(int(info["head_cy"])-3, int(info["hip"][1])+int(28*0.46)):
            pass
    out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
    open("scratch/_vigil_tune2_%s.ans"%name,"w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")

make("steel", 4, 15)        # blue shadow -> white-hot highlight
make("warm",  6, 15)        # orange shadow -> white
make("gray",  8, 15)        # warden-like gray -> white
print("done")
