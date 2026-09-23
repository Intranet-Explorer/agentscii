#!/usr/bin/env python3
# quick window search: for c=-0.7269+0.1889i, scan candidate windows and report
# fraction of cells that are "black core" (inside set after MAXIT) vs colored bands.
# We want a window that's mostly structure (low black fraction), near the boundary.
import math
CR, CI = -0.7269, 0.1889
MAXIT = 512
W, H = 80, 46

def stats(cx, cy, rad):
    black = 0; total = 0
    for r in range(H):
        zi0 = (cy - rad) + (2*rad) * (r + 0.5) / H
        for c in range(W):
            zr0 = (cx - rad) + (2*rad) * (c + 0.5) / W
            zr, zi = zr0, zi0; it = 0
            while zr*zr + zi*zi <= 4.0 and it < MAXIT:
                zr2, zi2 = zr*zr, zi*zi
                zr = zr2 - zi2 + CR; zi = 2.0*zr*zi + CI; it += 1
            total += 1
            if it >= MAXIT: black += 1
    return black/total

# scan a grid of centers/radii, print black fraction
for rad in [0.06, 0.09, 0.12]:
    for cx in [-0.60, -0.50, -0.40, -0.30, -0.20, 0.0]:
        for cy in [0.0, 0.15, 0.30, 0.45, 0.60]:
            b = stats(cx, cy, rad)
            if 0.05 < b < 0.45:   # mostly structure, some core
                print(f"cx={cx:+.2f} cy={cy:+.2f} r={rad:.2f}  black={b*100:5.1f}%")
