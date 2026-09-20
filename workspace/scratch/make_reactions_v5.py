#!/usr/bin/env python3
# REACTIONS v5 -- AGENTSCII (raze + hollis). Gray-Scott reaction-diffusion / Turing field.
#
# v1-v4 PROBLEM: the explicit scheme never ignited -- B stayed ~0 everywhere (var=0, fracB=0),
# so every regime rendered blank except border+signature. Root cause: D_A=1.0 diffusion dominated
# and collapsed every regime to the same checkerboard attractor; undamped reaction blew up & clipped.
#
# v5 FIX: moderate diffusion (D_A=0.15, D_B=0.075) so the natural Turing wavelength resolves and
# regimes actually diverge; single central seed on a fine 320x184 grid, ~6k steps, then downsample
# to 80x46 by area-averaging B. 'coral' regime (f=0.037 k=0.060) -> sparse organic branching.
# Distinct from noise fields (PLASMA), advection (FLOWFIELD), geometric folding (LISSAJOUS).

import math, numpy as np
W, H = 80, 46
SW, SH = 320, 184             # fine sim grid (4x) -- room for natural wavelength
ESC = "\x1b["
def sgr(*c): return ESC + ";".join(str(x) for x in c) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]    # house ACiD-Trip wheel: mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"             # bright->dim density ramp

def lap(a): return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)

feed, kill = 0.037, 0.060
dA, dB = 0.15, 0.075
steps = 6000
rng = np.random.default_rng(11)
A = np.ones((SH, SW), dtype=np.float64)
B = np.zeros((SH, SW), dtype=np.float64)
cy, cx = SH//2, SW//2
B[cy-3:cy+4, cx-3:cx+4] = 1.0               # single central seed -> symmetric growth
for _ in range(steps):
    la = lap(A); lb = lap(B); r = A*B*B
    A = A + dA*la - r + feed*(1.0-A)
    B = B + dB*lb + r - (kill+feed)*B
    np.clip(A, 0.0, 1.0, out=A); np.clip(B, 0.0, 1.0, out=B)

sx, sy = SW // W, SH // H
Bd = B[:sy*H, :sx*W].reshape(H, sy, W, sx).mean(axis=(1,3))
lo, hi = float(Bd.min()), float(Bd.max())
if hi > lo: Bd = (Bd - lo) / (hi - lo)

lines = []
for y in range(H):
    row = sgr(40)
    for x in range(W):
        v = Bd[y, x]
        if v < 0.12:
            row += " "; continue
        d = int(v * (len(RAMP)-1))
        hue = HUE[(x + y*3) % len(HUE)]      # diagonal color wheel across the field
        row += sgr(hue) + RAMP[d]
    lines.append(row + RESET)

def hline(ch="\u2500"): return sgr(97) + ch*W + RESET
out = [hline(), *lines, hline()]
sig1 = "raze / AGENTSCII"
sig2 = "REACTIONS v5.0 -- gray-scott 'coral' regime"
out.append(sgr(97) + "\u2510" + sgr(37) + sig1.center(W-2) + RESET + "\u2518")
out.append(sgr(97) + "\u2514" + sgr(37) + sig2.center(W-2) + RESET + "\u2518")
out.append(hline())

data = ("\n".join(out) + "\n").encode("cp437", "replace")
open("raze-reactions.ans", "wb").write(data)
print(f"wrote raze-reactions.ans {len(data)} bytes; var={Bd.var():.4f} frac>0.25={(Bd>0.25).mean():.3f}")
