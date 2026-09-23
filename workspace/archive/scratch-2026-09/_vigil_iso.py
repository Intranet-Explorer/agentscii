import sys; sys.path.insert(0,".")
import figure_common as F
from figure_common import new_canvas, standing_figure, light_field, render, c, W, H
def L(x,y):
    r = light_field(x,y,28,12,lmax=35.0,ambient=0.10)
    axial = 0.5 + 0.5*(40-x)/20.0
    return max(0.0,min(1.0, r*0.6+axial*0.5))
cv=new_canvas(H,W)
standing_figure(cv,40,30,L,height=28.0,stance="contrapposto",base_fg=4,hot_fg=12,iris_fg=96,one_eye=True)
out=[c(104,40)+"\u2550"*W]; body=[]; render(cv,body); out+=body; out.append(c(104,40)+"\u2550"*W)
open("scratch/_vigil_iso.ans","w",encoding="cp437").write("\n".join(out)+F.RESET+"\n")
print("ok base=4 hot=12")
