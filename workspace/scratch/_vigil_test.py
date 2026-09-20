import sys, math
sys.path.insert(0, ".")
import figure_common as F
from figure_common import (new_canvas, set_cell, shade_region, light_field,
                           standing_figure, render, c, RAMP, HUE, W)

OUT = "_vigil_test.ans"
cv = new_canvas(46, 80)
lx, ly = 28, 12                       # light upper-left, like warden
def L(x, y): return light_field(x, y, lx, ly, lmax=15.0, ambient=0.22)

# a saturated cycling dither field behind the figure (house ACiD periphery)
for y in range(46):
    for x in range(80):
        h = HUE[(x + y * 2) % len(HUE)]
        ch, fg = F.shade(0.5 + 0.5 * math.sin((x * 0.3 + y * 0.7)), base_fg=h & 7, hot_fg=(h & 7) | 8)
        set_cell(cv, x, y, ch, fg, 0)

# the standing sentinel -- controlled black core so the figure reads on the field
standing_figure(cv, 40, 30, L, height=26.0, stance="contrapposto",
                base_fg=93, hot_fg=15, iris_fg=96, one_eye=True)

out = []
render(cv, out)
open(OUT, "w").write("\n".join(out) + "\x1b[0m\n")
print("wrote", OUT)
