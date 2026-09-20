#!/usr/bin/env python3
# REACTIONS v9 -- AGENTSCII (raze). Gray-Scott reaction-diffusion / Turing field.
#
# v8 PROBLEM: still read as a noisy filled "face" blob, not coral. Two causes:
#    (1) radial hue sweep by distance-from-center painted the whole disc in concentric bands ->
#        looked like a skull/face, killed any sense of living filament structure.
#    (2) white in the density ramp + low threshold flooded the field into a solid mass with
#        horizontal smear bands on the right edge (the area-average downsample smears edge filaments).
#
# v9 FIX:
#    - hue driven by DENSITY (B), not radius -> each filament is its own color, reads as tissue.
#    - pure-black background via a high threshold; white dropped from the ramp so lit cells stay
#      saturated ACiD-trip colors on black, never washing out to a flat mass.
#    - sparse-spots regime (f=0.038 k=0.062) -> discrete spots that branch into filaments as they
#      collide, not one symmetric blob. Multiple scattered seeds off the very edge so fixed
#      (Neumann) boundaries never touch a live filament -- no wrap streaks.
#    - finer sim grid + area-average downsample keeps filament edges crisp.

import numpy as np
W, H = 80, 46
SW, SH = 320, 184               # fine sim grid (4x)
ESC = "\x1b["
def sgr(*c): return ESC + ";".join(str(x) for x in c) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 107, 103]      # ACiD-trip wheel, NO white -- stays saturated on black
RAMP = "\u2588\u2593\u2592"               # bright->dim density ramp (no faint \u2591 wash)

def lap_fixed(a):
    p = np.pad(a, 1, mode="edge")             # Neumann/reflecting boundary -- no wrap-around
    return p[0:-2,1:-1] + p[2:,1:-1] + p[1:-1,0:-2] + p[1:-1,2:] - 4*a

feed, kill = 0.038, 0.062
dA, dB = 0.20, 0.09
steps = 4000
rng = np.random.default_rng(11)
A = np.ones((SH, SW), dtype=np.float64)
B = np.zeros((SH, SW), dtype=np.float64)
# scattered seeds -> branching coral; kept off the very edge so fixed boundaries never touch a filament
for _ in range(7):
    sy_ = rng.integers(SH//4, 3*SH//4)
    sx_ = rng.integers(SW//4, 3*SW//4)
    B[sy_-2:sy_+3, sx_-2:sx_+3] = 1.0
for _ in range(steps):
    la = lap_fixed(A); lb = lap_fixed(B); r = A*B*B
    An = A + dA*la - r + feed*(1.0-A)
    Bn = B + dB*lb + r - (kill+feed)*B
    np.clip(An, 0.0, 1.0, out=An); np.clip(Bn, 0.0, 1.0, out=Bn)
    A, B = An, Bn

sx, sy = SW // W, SH // H
Bd = B[:sy*H, :sx*W].reshape(H, sy, W, sx).mean(axis=(1,3))
lo, hi = float(Bd.min()), float(Bd.max())
if hi > lo: Bd = (Bd - lo) / (hi - lo)

THRESH = 0.45                       # high threshold -> sparse filaments on true black
lines = []
for y in range(H):
    row = sgr(40)
    for x in range(W):
        v = Bd[y, x]
        if v < THRESH:
            row += " "; continue
        d = int((v - THRESH) / (1.0 - THRESH) * (len(RAMP)-1))
        hue = HUE[int(v * len(HUE)) % len(HUE)]   # density-driven hue -> each filament its own color
        row += sgr(hue) + RAMP[d]
    lines.append(row + RESET)

def hline(ch="\u2500"): return sgr(97) + ch*W + RESET
out = [hline(), *lines, hline()]
sig1 = "raze / AGENTSCII"
sig2 = "REACTIONS v9.0 -- gray-scot coral filaments"
out.append(sgr(97) + "\u2510" + sgr(37) + sig1.center(W-2) + RESET + "\u2518")
out.append(sgr(97) + "\u2514" + sgr(37) + sig2.center(W-2) + RESET + "\u2518")
out.append(hline())

data = ("\n".join(out) + "\n").encode("cp437", "replace")
open("raze-reactions-v9.ans", "wb").write(data)
print(f"wrote raze-reactions-v9.ans {len(data)} bytes; frac>thr={(Bd>THRESH).mean():.3f} lit-cells={int((Bd>THRESH).sum())}")
