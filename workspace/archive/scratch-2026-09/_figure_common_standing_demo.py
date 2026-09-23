# scratch/_figure_common_standing_demo.py -- PROOF that figure_common.py now builds a
# full STANDING figure (not just a bust). This is the joint-VIGIL scaffold demo: hollis
# takes this body/pose layer and adds the field + framing; raze's standing-figure layer
# (capsule/joint_dot/standing_figure) is what makes it possible. See _joint-vigil.proposal.txt.
import sys, math
sys.path.insert(0, ".")
import figure_common as F
from figure_common import (new_canvas, set_cell, light_field, standing_figure,
                           render, c, RAMP, HUE, W)

OUT = "_figure_common_standing_demo.ans"
cv = new_canvas(46, 80)
lx, ly = 26, 10                       # light upper-left (warden idiom)
def L(x, y): return light_field(x, y, lx, ly, lmax=15.0, ambient=0.22)

# controlled black core so the figure reads; saturated cycling field at the periphery
for y in range(46):
    for x in range(80):
        h = HUE[(x + y * 2) % len(HUE)]
        ch, fg = F.shade(0.5 + 0.5 * math.sin(x * 0.3 + y * 0.7), base_fg=h & 7, hot_fg=(h & 7) | 8)
        set_cell(cv, x, y, ch, fg, 0)

standing_figure(cv, 40, 28, L, height=26.0, stance="contrapposto",
                base_fg=93, hot_fg=15, iris_fg=96, one_eye=True)

out = []
render(cv, out)
open(OUT, "w").write("\n".join(out) + "\x1b[0m\n")
print("wrote", OUT)
