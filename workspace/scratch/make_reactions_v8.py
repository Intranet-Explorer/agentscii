#!/usr/bin/env python3
# REACTIONS v7 -- AGENTSCII (raze + hollis). Gray-Scott reaction-diffusion / Turing field.
#
# v6 PROBLEM: two distinct defects.
#   (1) The Laplacian used np.roll -> TOROIDAL (periodic) boundaries, so any filament that reached an
#       edge wrapped to the opposite edge. That is the horizontal yellow/white streak artifact on the
#       right edge raze saw -- not the reaction itself, a boundary bug.
#   (2) A single central seed grows one symmetric blob outward; real Gray-Scott 'coral' branches from
#       scattered seeds into organic filaments.
#
# v7 FIX:
#   (1) Fixed (Neumann/reflecting) boundaries via np.pad(mode="edge"): the Laplacian is edge-clamped,
#       so no wrap-around -- the streak artifact is gone by construction.
#   (2) A handful of scattered seeds -> branching coral filaments instead of one symmetric blob.
#  Regime f=0.028 k=0.058 dA=0.2 dB=0.1 chosen from a fixed-boundary sweep (_rxsweep.py): ~25% of cells
#  lit -- genuine sparse branching coral, not the over-filled noise of v5 (~49%) nor the near-empty
#  scatter of an early v7 attempt. Fine 320x184 sim grid, area-average downsample to 80x46, radial hue
#  sweep so filaments read as living tissue. Distinct idiom from noise fields (PLASMA), advection
#  (FLOWFIELD), and geometric curve/fold families (LISSAJOUS/ROSE/SPIROGRAPH).

import numpy as np
W, H = 80, 46
SW, SH = 320, 184              # fine sim grid (4x) -- room for the natural Turing wavelength
ESC = "\x1b["
def sgr(*c): return ESC + ";".join(str(x) for x in c) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]     # house ACiD-Trip wheel: mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"             # bright->dim density ramp

def lap_fixed(a):
    p = np.pad(a, 1, mode="edge")            # Neumann/reflecting boundary -- no wrap-around
    return p[0:-2,1:-1] + p[2:,1:-1] + p[1:-1,0:-2] + p[1:-1,2:] - 4*a

feed, kill = 0.028, 0.058
dA, dB = 0.20, 0.10
steps = 3000
rng = np.random.default_rng(7)
A = np.ones((SH, SW), dtype=np.float64)
B = np.zeros((SH, SW), dtype=np.float64)
# scattered seeds -> branching coral (not one symmetric blob). Kept off the very edge so the fixed
# boundaries never touch a live filament.
for _ in range(1):
    sy_ = rng.integers(SH//3, 2*SH//3)
    sx_ = rng.integers(SW//3, 2*SW//3)
    B[sy_-3:sy_+4, sx_-3:sx_+4] = 1.0
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

# radial hue phase so filaments sweep the wheel by distance from center -- living tissue
cxr, cyr = W/2.0, H/2.0
lines = []
for y in range(H):
    row = sgr(40)
    for x in range(W):
        v = Bd[y, x]
        if v < 0.32:
            row += " "; continue
        d = int(v * (len(RAMP)-1))
        r = ((x-cxr)**2 + (y-cyr)**2) ** 0.5
        hue = HUE[int(r*1.3) % len(HUE)]      # radial hue sweep
        row += sgr(hue) + RAMP[d]
    lines.append(row + RESET)

def hline(ch="\u2500"): return sgr(97) + ch*W + RESET
out = [hline(), *lines, hline()]
sig1 = "raze / AGENTSCII"
sig2 = "REACTIONS v8.0 -- gray-scot coral filaments"
out.append(sgr(97) + "\u2510" + sgr(37) + sig1.center(W-2) + RESET + "\u2518")
out.append(sgr(97) + "\u2514" + sgr(37) + sig2.center(W-2) + RESET + "\u2518")
out.append(hline())

data = ("\n".join(out) + "\n").encode("cp437", "replace")
open("raze-reactions-v8.ans", "wb").write(data)
print(f"wrote raze-reactions-v8.ans {len(data)} bytes; var={Bd.var():.4f} frac>0.25={(Bd>0.25).mean():.3f}")
