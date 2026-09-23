#!/usr/bin/env python3
# PROTOTYPE ONLY -- does a hand silhouette read as a legible hand on halfblock?
# Hand reaching up-forward, 4 fingers + thumb. Flat fill first (composition check).
import sys
sys.path.insert(0, "scratch")
from halfblock import HalfBlockCanvas

W = 80
HCELLS = 40
hb = HalfBlockCanvas(W, HCELLS, bg=0)
PH = hb.ph  # pixel height = 80

# Hand reaching up. Palm center ~ (px 38, py 52). Fingers point up (decreasing py).
# Pixel space is square-ish. Let's lay out in a coordinate where y grows DOWN.
PALM_CX = 40
PALM_CY = 50   # pixel-space

def palm():
    # rounded palm: an ellipse-ish region
    for py in range(38, 66):
        for px in range(28, 52):
            dx = (px - PALM_CX) / 12.0
            dy = (py - PALM_CY) / 14.0
            if dx*dx + dy*dy <= 1.0:
                hb.set_pixel(px, py, 7)

# Fingers: 4 fingers from top of palm, spreading slightly. Each finger a thin capsule.
def finger(cx_base, tip_x, length, width):
    # interpolate a tapered line from base (py=42) up to tip
    n = int(length)
    for i in range(n):
        t = i / max(1, n-1)
        cx = cx_base + (tip_x - cx_base) * t
        w = width * (1.0 - 0.35*t)   # taper toward tip
        py = 42 - int(t * length)
        for d in range(-int(w), int(w)+1):
            hb.set_pixel(int(cx)+d, py, 7)

# index, middle, ring, pinky -- tips spread outward
finger(35, 30, 26, 3.0)   # index
finger(40, 40, 30, 3.2)   # middle (longest)
finger(45, 50, 27, 3.0)   # ring
finger(49, 56, 22, 2.8)   # pinky
# thumb -- off to the left side of palm, angled out
def thumb():
    for i in range(18):
        t = i/17.0
        px = 30 - int(t*14)
        py = 56 + int(t*6)
        w = 2.6*(1-0.3*t)
        for d in range(-int(w), int(w)+1):
            hb.set_pixel(int(px)+d, py, 7)
thumb()

# wrist / forearm stub at bottom
for py in range(64, 80):
    for px in range(34, 46):
        hb.set_pixel(px, py, 5)   # dim blue wrist

rows = hb.render()
out = "\n".join(rows) + "\x1b[0m"
open("scratch/_hand_proto.ans", "w").write(out)
print("wrote scratch/_hand_proto.ans")
