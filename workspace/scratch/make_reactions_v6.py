#!/usr/bin/env python3
# REACTIONS v6 -- AGENTSCII (raze). Gray-Scott reaction-diffusion / Turing field.
#
# v5 PROBLEM: dA=0.15/dB=0.075 + 6k steps over-filled the field (~49% of cells bright) so it
# read as dense noise, not coral. v6 FIX: dA=0.16/dB=0.08, 3k steps -> a genuine sparse
# branching 'coral/maze' regime (~18% of cells lit) on a dark background -- the organic
# reaction-diffusion idiom, distinct from noise fields (PLASMA), advection (FLOWFIELD), and
# geometric curve/fold families (LISSAJOUS/ROSE/SPIROGRAPH). Single central seed -> symmetric
# growth. Downsample by area-average; hue cycles the house wheel along a slow radial sweep so
# filaments read as living tissue, not static noise.

import numpy as np
W, H = 80, 46
SW, SH = 320, 184            # fine sim grid (4x) -- room for the natural Turing wavelength
ESC = "\x1b["
def sgr(*c): return ESC + ";".join(str(x) for x in c) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]   # house ACiD-Trip wheel: mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"           # bright->dim density ramp

def lap(a): return (np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1)-4*a)

feed, kill = 0.037, 0.060
dA, dB = 0.16, 0.08
steps = 3000
A = np.ones((SH, SW), dtype=np.float64)
B = np.zeros((SH, SW), dtype=np.float64)
cy, cx = SH//2, SW//2
B[cy-4:cy+5, cx-4:cx+5] = 1.0             # single central seed -> symmetric growth
for _ in range(steps):
    la = lap(A); lb = lap(B); r = A*B*B
    A = A + dA*la - r + feed*(1.0-A)
    B = B + dB*lb + r - (kill+feed)*B
    np.clip(A, 0.0, 1.0, out=A); np.clip(B, 0.0, 1.0, out=B)

sx, sy = SW // W, SH // H
Bd = B[:sy*H, :sx*W].reshape(H, sy, W, sx).mean(axis=(1,3))
lo, hi = float(Bd.min()), float(Bd.max())
if hi > lo: Bd = (Bd - lo) / (hi - lo)

# radial hue phase so filaments sweep the wheel by distance from center -- living tissue
cxr, cyr = W/2.0, H/2.0
lines = []
for y in range(H):
    row = sgr(40)
    for x in range(W):
        v = Bd[y, x]
        if v < 0.14:
            row += " "; continue
        d = int(v * (len(RAMP)-1))
        r = ((x-cxr)**2 + (y-cyr)**2) ** 0.5
        hue = HUE[int(r*1.3) % len(HUE)]    # radial hue sweep
        row += sgr(hue) + RAMP[d]
    lines.append(row + RESET)

def hline(ch="\u2500"): return sgr(97) + ch*W + RESET
out = [hline(), *lines, hline()]
sig1 = "raze / AGENTSCII"
sig2 = "REACTIONS v6.0 -- gray-scott 'coral' regime"
out.append(sgr(97) + "\u2510" + sgr(37) + sig1.center(W-2) + RESET + "\u2518")
out.append(sgr(97) + "\u2514" + sgr(37) + sig2.center(W-2) + RESET + "\u2518")
out.append(hline())

data = ("\n".join(out) + "\n").encode("cp437", "replace")
open("raze-reactions.ans", "wb").write(data)
print(f"wrote raze-reactions.ans {len(data)} bytes; var={Bd.var():.4f} frac>0.25={(Bd>0.25).mean():.3f}")
