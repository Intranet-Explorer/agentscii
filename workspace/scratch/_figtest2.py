#!/usr/bin/env python3
# quick readability test: one standing figure, hard side light -> does it read as a person?
import sys; sys.path.insert(0, "scratch")
from figure_common import *

cv = new_canvas(h=46, w=80)
# hard light from the LEFT (the figure faces right toward us / toward a source on its left)
def L(x, y): return light_field(x, y, lx=12.0, ly=14.0, lmax=30.0, ambient=0.18)

standing_figure(cv, hipx=40.0, hipy=30.0, Lfn=L, height=30.0,
                stance="contrapposto", base_fg=7, hot_fg=15, iris_fg=96, one_eye=True)

out = []
render(cv, out)
open("scratch/_figtest2.ans", "w").write("\n".join(out) + "\n" + RESET)
print("rows:", len(out))
