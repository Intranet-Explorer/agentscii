#!/usr/bin/env python3
# MANDEL v1.0 -- AGENTSCII (joint: raze & hollis).
#
# Fifth fractal tradition for the family, and the one that finally lands a real
# TUNNEL: FRACTAL (cardioid), JULIA (symmetric dendrite), DEEPZOOM (Julia interior
# tunnel -- but its seed's interior is ONE big basin, so the core reads flat/void),
# NEWTON (z^3-1 basins). The Julia-tunnel dead-end (scratch/raze-deepzoom-tunnel.note.txt)
# proved a single-window Julia interior collapses to one flat slab. A Mandelbrot
# deep-zoom into a period-doubling MINI-COPY has the fine self-similar structure a
# tunnel actually needs: nested escape bands that resolve ring after ring, so the
# core reads as receding depth instead of a hole. This is DEEPZOOM's idea with the
# right target -- raze offered the pivot, I built it.
#
# Same ACiD idiom + house conventions byte-for-byte: 80 cols, cp437 on disk, raw SGR,
# bright fg 91-107, double-line frame + title bar, sig block 'raze & hollis / AGENTSCII'
# + version line, standalone reset.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as FRACTAL/JULIA/DEEPZOOM/NEWTON)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]          # mag red yel grn cya blu wht amb

out = []
def emit(line=""): out.append(line)

# --- deep-zoom into a period-doubling mini-copy in the seahorse valley.
# This window sits on a real spiral arm of a mini-Mandelbrot, so escape-time bands
# resolve into fine nested rings (genuine tunnel depth), not one flat basin.
RE_MIN, RE_MAX = -0.746200, -0.744120
IM_MIN, IM_MAX =  0.112940,  0.113440
MAXIT = 400

def mandel_field():
    emit(sgr(0, 40))                               # black bg baseline (the deep core)
    for r in range(H):
        zi0 = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            zr, zi = zr0, zi0
            it = 0
            while it < MAXIT:
                zr2, zi2 = zr*zr, zi*zi
                if zr2 + zi2 > 4.0:
                    break
                zi = 2.0 * zr * zi + zi0
                zr = zr2 - zi2 + zr0
                it += 1
            if it >= MAXIT:
                # still inside after MAXIT -> the deep tunnel core, black void
                cells.append((' ', (0, None)))
                continue
            # smooth escape value so bands are fine and evenly spaced (log-scaled)
            mu = math.log(it + 1.0) * 0.5
            hue = HUE[int(mu) % len(HUE)]
            # density from the fractional part -> block dither carries the band edge
            dens = "\u2588\u2593\u2592\u2591"[int((mu - int(mu)) * 4) & 3]
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
title_bar("MANDEL // MINI-COPY DEEP TUNNEL", 96)
emit()
mandel_field()
emit()
frame_bottom()

sig = "raze & hollis / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "MANDEL v1.0 -- period-doubling mini-copy, MAXIT 400, nested bands"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/hollis-raze-mandel.ans", "w", encoding="cp437") as f:
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
