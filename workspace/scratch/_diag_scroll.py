import sys, importlib.util
spec = importlib.util.spec_from_file_location("mfs", "scratch/make_fractal_scroll.py")
# We can't exec the whole thing cleanly (it writes a file + uses global panel_h mid-script).
# Instead just measure per-panel lit-cell density by replicating field calls.
import math
INNER_W = 78
HUE = [95, 91, 93, 92, 96, 94, 107, 103]
RAMP = "▓▒░"

def density(field_fn, h):
    lit=0; tot=h*INNER_W
    for y in range(h):
        for x in range(INNER_W):
            hi,ch,fg = field_fn(x,y)
            if fg is not None: lit+=1
    return lit/tot

# replicate the three fields with panel_h set
import types
mod = types.SimpleNamespace()
def make_field(fn_name, h):
    # crude: exec the function bodies is hard; just re-implement counts via import of module funcs
    pass

# Easier: import the module's functions by executing it but neutralize the write.
src = open("scratch/make_fractal_scroll.py").read()
src = src.replace('open("scratch/hollis-raze-fractal-scroll.ans","w")','open("/dev/null","w")')
g = {"__name__":"notmain"}
exec(compile(src,"mfs","exec"), g)
# now g has deepzoom_field, mandel_field, newton_field, and panel_h is whatever last set
for name,h in [("deepzoom",42),("mandel",42),("newton",40)]:
    g["panel_h"]=h
    fn=g[name+"_field"]
    d=density(fn,h)
    print(f"{name:9s} h={h:3d}  lit={d*100:5.1f}%")
