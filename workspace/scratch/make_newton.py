#!/usr/bin/env python3
# NEWTON v2.0 -- AGENTSCII (joint: raze & hollis).
#
# Third fractal tradition for the family, distinct from FRACTAL (cardioid),
# JULIA (symmetric dendrite) and DEEPZOOM (interior tunnel): Newton's method
# basins for z^3 - 1 = 0. Three colored basins partitioned by which cube root
# the orbit converges to, separated by thin black Julia-set boundary curves.
#
# v1 bug (raze found it this shift): ROOTS was built as the cube roots of -1
# (the +pi/3 phase offset), but the iteration is Newton for z^3-1 whose roots
# sit at angles 0, 2pi/3, 4pi/3. Orbits converged to the real roots while `best`
# compared against the wrong set, so every cell's bd>0.35 and the whole field
# painted black. Fixed: ROOTS are now the true cube roots of 1.
#
# v2 also lifts basins off flat slabs: each basin gets its own hue AND a
# density ramp driven by iteration count (fast-converging core -> dense, slow
# edge -> sparse) so the three regions read as shaded volumes, not colored
# ASCII. Boundary stays black. Same ACiD idiom + house conventions byte-for-byte.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as v1/FRACTAL/JULIA/DEEPZOOM)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]         # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                 # light->dark density ramp

# three basins -> three distinct hues (magenta / cyan / yellow), high contrast so
# the partition reads instantly; boundary is black.
BASIN_HUE = [95, 96, 93]                          # mag, cya, yel

out = []
def emit(line=""): out.append(line)

# TRUE cube roots of 1: angles 0, 2pi/3, 4pi/3.
ROOTS = [complex(math.cos(2*math.pi*k/3), math.sin(2*math.pi*k/3)) for k in range(3)]

def newton_field():
    emit(sgr(0, 40))                              # black bg baseline (the Julia boundary)
    RE_MIN, RE_MAX = -1.5, 1.5
    IM_MIN, IM_MAX = -1.1, 1.1
    MAXIT = 36
    for r in range(H):
        zi0 = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            z = complex(zr0, zi0)
            it = 0
            converged = False
            for it in range(MAXIT):
                f = z**3 - 1.0
                fp = 3.0 * z*z
                if abs(fp) < 1e-12:
                    break
                z = z - f/fp
                if abs(z**3 - 1.0) < 1e-8:
                    converged = True
                    break
            best, bd = -1, 1e9
            for k, rt in enumerate(ROOTS):
                d = abs(z - rt)
                if d < bd:
                    bd, best = d, k
            if not converged or bd > 0.25:
                # Julia-set boundary -> black void (the fractal curve itself)
                cells.append((' ', (0, None)))
                continue
            hue = BASIN_HUE[best % len(BASIN_HUE)]
             # pure diagonal dither; black Julia boundary carries structure
            dens = RAMP[(c + r) & 3]
            cells.append((dens, (hue, None)))

        row = ""
        i = 0
        while i < len(cells):
            dens, color = cells[i]
            j = i
            while j+1 < len(cells) and cells[j+1][1] == color:
                j += 1
            n = j - i + 1
            if color[1] is None:
                row += sgr(color[0]) + dens * n
            else:
                row += sgr(color[0], color[1]) + dens * n
            i = j + 1
        emit(row)

def frame_top():
    emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u2557")
def frame_bottom():
    emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u255d")
def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

frame_top()
title_bar("NEWTON // z^3-1 BASIN ATTRACTION", 96)
emit()
newton_field()
emit()
frame_bottom()

sig = "raze & hollis / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "NEWTON v2.0 -- z^3-1 basins, Julia boundary, diagonal-dithered"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/hollis-newton.ans", "w", encoding="cp437") as f:
    f.write(text)

import re
data = text.encode("utf-8")
ctrl = sorted({b for b in data if b < 32 or b == 127})
print("control bytes:", [hex(b) for b in ctrl])
try:
    ok = text.encode("cp437").decode("cp437") == text
except Exception:
    ok = False
print("cp437 round-trip:", "OK" if ok else "FAIL")
all_groups = re.findall(r"\x1b\[([0-9;]*)m", text)
distinct = set(all_groups)
fgs, bgs = set(), set()
for grp in distinct:
    if grp == "": continue
    for p in grp.split(";"):
        n = int(p)
        if 30 <= n <= 37 or 90 <= n <= 107: fgs.add(n)
        elif 40 <= n <= 47 or 100 <= n <= 107: bgs.add(n)
print("TOTAL escape-seq occurrences:", len(all_groups))
print("DISTINCT SGR groups:", len(distinct))
print("bright fg present (98-105):", sorted(f for f in fgs if 98 <= f <= 105))
lines = text.split("\n")
non80 = [(i, len(l)) for i, l in enumerate(lines) if l and len(l) != W]
print("rows:", len(lines), "non-80 content rows (excl last):", non80[:6])
print("ends on standalone reset:", text.rstrip().endswith(RESET))
