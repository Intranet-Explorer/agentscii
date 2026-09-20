#!/usr/bin/env python3
# v2 block-in: CONNECTED hand, clean. One color family (cool). Composition check only.
import sys, math
sys.path.insert(0, "scratch")
from halfblock import HalfBlockCanvas

W = 80
HCELLS = 40
hb = HalfBlockCanvas(W, HCELLS, bg=0)
PH = hb.ph   # 80

# Hand reaching UP and slightly forward (toward viewer). Palm center.
PALM_CX = 40.0
PALM_CY = 52.0

def setc(px, py, c):
    hb.set_pixel(int(round(px)), int(round(py)), c)

# --- palm: rounded region ---
for py in range(36, 70):
    for px in range(27, 54):
        dx = (px - PALM_CX)/13.0
        dy = (py - PALM_CY)/15.0
        if dx*dx + dy*dy <= 1.0:
            setc(px, py, 6)   # cyan-ish palm base

# --- fingers: tapered capsules from top of palm upward, spreading ---
def finger(cx_base, tip_x, length, width):
    n = int(length)+1
    for i in range(n):
        t = i/(n-1)
        cx = cx_base + (tip_x - cx_base)*t
        w = width*(1.0 - 0.30*t)
        py = 40 - int(t*length)
        for d in range(-int(round(w)), int(round(w))+1):
            setc(cx+d, py, 6)

finger(35, 29, 28, 3.2)   # index
finger(40, 40, 32, 3.4)   # middle (longest)
finger(45, 51, 29, 3.2)   # ring
finger(49, 57, 24, 3.0)   # pinky

# --- thumb: connected to LEFT side of palm, angling out-down ---
def thumb():
    for i in range(20):
        t = i/19.0
        px = 28 - int(t*16)
        py = 54 + int(t*10)
        w = 3.0*(1-0.3*t)
        for d in range(-int(round(w)), int(round(w))+1):
            setc(px+d, py, 6)
thumb()

# --- wrist / forearm: connected to bottom of palm, same family (dimmer cyan) ---
for py in range(68, 80):
    for px in range(34, 47):
        setc(px, py, 4)   # blue wrist

rows = hb.render()
out = "\n".join(rows) + "\x1b[0m"
open("scratch/_hand_v2.ans", "w").write(out)
print("wrote scratch/_hand_v2.ans")
