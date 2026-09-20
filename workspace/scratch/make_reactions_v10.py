#!/usr/bin/env python3
# REACTIONS v10 -- AGENTSCII (raze). Gray-Scott reaction-diffusion / Turing field.
#
# v9 PROBLEM: still a noisy filled mass with horizontal smear bands on the right edge. Root cause is
# now clear and structural, not parametric:
#     - mean-pool downsample of a dense Turing field smears vertical filament structure into horizontal
#       bands (the yellow streaks) -- that's a rendering artifact, not the reaction.
#     - 38% lit cells is not "sparse coral", it's a filled mass; no black breathing room.
#
# v10 FIX:
#     - MAX-pool downsample instead of mean: thin filaments survive intact, no horizontal smear.
#     - maze/coral regime (f=0.034 k=0.061) -> branching corridors with large empty regions, not a spot
#       field that fills everything.
#     - high threshold so only filament cores paint on true black -- sparse, breathing tissue.
#     - density-driven hue, no white in ramp (stays saturated ACiD-trip on black).

import numpy as np
W, H = 80, 46
SW, SH = 320, 184                # fine sim grid (4x)
ESC = "\x1b["
def sgr(*c): return ESC + ";".join(str(x) for x in c) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 107, 103]       # ACiD-trip wheel, NO white -- saturated on black
RAMP = "\u2588\u2593"                      # bright->dim density ramp (no faint wash)

def lap_fixed(a):
    p = np.pad(a, 1, mode="edge")              # Neumann/reflecting boundary -- no wrap-around
    return p[0:-2,1:-1] + p[2:,1:-1] + p[1:-1,0:-2] + p[1:-1,2:] - 4*a

feed, kill = 0.034, 0.061
dA, dB = 0.20, 0.09
steps = 5000
rng = np.random.default_rng(23)
A = np.ones((SH, SW), dtype=np.float64)
B = np.zeros((SH, SW), dtype=np.float64)
for _ in range(11):                       # scattered seeds -> branching corridors
    sy_ = rng.integers(SH//5, 4*SH//5)
    sx_ = rng.integers(SW//5, 4*SW//5)
    B[sy_-2:sy_+3, sx_-2:sx_+3] = 1.0
for _ in range(steps):
    la = lap_fixed(A); lb = lap_fixed(B); r = A*B*B
    An = A + dA*la - r + feed*(1.0-A)
    Bn = B + dB*lb + r - (kill+feed)*B
    np.clip(An, 0.0, 1.0, out=An); np.clip(Bn, 0.0, 1.0, out=Bn)
    A, B = An, Bn

sx, sy = SW // W, SH // H
# MAX-pool: thin filaments survive intact, no horizontal smear from averaging
Bd = B[:sy*H, :sx*W].reshape(H, sy, W, sx).max(axis=(1,3))
lo, hi = float(Bd.min()), float(Bd.max())
if hi > lo: Bd = (Bd - lo) / (hi - lo)

THRESH = 0.78                        # high threshold -> only filament cores on true black
lines = []
for y in range(H):
    row = sgr(40)
    for x in range(W):
        v = Bd[y, x]
        if v < THRESH:
            row += " "; continue
        d = int((v - THRESH) / (1.0 - THRESH) * (len(RAMP)-1))
        hue = HUE[int(v * len(HUE)) % len(HUE)]    # density-driven hue
        row += sgr(hue) + RAMP[d]
    lines.append(row + RESET)

def hline(ch="\u2500"): return sgr(97) + ch*W + RESET
out = [hline(), *lines, hline()]
sig1 = "raze / AGENTSCII"
sig2 = "REACTIONS v10.0 -- gray-scot coral filaments"
out.append(sgr(97) + "\u2510" + sgr(37) + sig1.center(W-2) + RESET + "\u2518")
out.append(sgr(97) + "\u2514" + sgr(37) + sig2.center(W-2) + RESET + "\u2518")
out.append(hline())

data = ("\n".join(out) + "\n").encode("cp437", "replace")
open("raze-reactions-v10.ans", "wb").write(data)
print(f"wrote raze-reactions-v10.ans {len(data)} bytes; frac>thr={(Bd>THRESH).mean():.3f} lit-cells={int((Bd>THRESH).sum())}")
