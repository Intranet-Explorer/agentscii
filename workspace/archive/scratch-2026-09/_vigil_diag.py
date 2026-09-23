import sys; sys.path.insert(0,".")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H
cv = new_canvas(H, W)
# pure black bg, figure only -- see the TRUE form + gradient
def L(x,y): return light_field(x,y,26,9,lmax=15.0,ambient=0.24)
standing_figure(cv,40,30,L,height=28.0,stance="contrapposto",base_fg=93,hot_fg=15,iris_fg=96,one_eye=True)
out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
open("scratch/_vigil_diag.ans","w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")
print("ok")
