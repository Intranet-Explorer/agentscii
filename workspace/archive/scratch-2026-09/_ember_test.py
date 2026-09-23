import sys, math
sys.path.insert(0,".")
import figure_common as F
from figure_common import (new_canvas, set_cell, light_field, standing_figure, render, RAMP)

H,W = 48, 80
cv = new_canvas(H, W)
# warm firelight from lower-center (a hearth), ambient so the far side still reads
lx, ly = 30, 40
def L(x,y):
    r = light_field(x,y, lx, ly, lmax=26.0, ambient=0.18)
    return max(0.0, min(1.0, r))

# dark void field (flood-fill spirit: the negative space is the hearth-dark)
for y in range(H):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

standing_figure(cv, 40, 26, L, height=28.0, stance="contrapposto",
                base_fg=4, hot_fg=15, iris_fg=96, one_eye=True)   # deep-red shadow -> white-hot

out=[]; render(cv,out)
open("scratch/_ember_test.ans","w").write("\n".join(out)+"\x1b[0m\n")
print("wrote _ember_test.ans")
