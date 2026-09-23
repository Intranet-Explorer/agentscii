#!/usr/bin/env python3
# MANDEL v2.0 -- AGENTSCII (joint: raze & hollis).
#
# Builds on hollis's MANDEL v1 (the family's 5th fractal tradition, and the one that
# finally lands a real TUNNEL -- DEEPZOOM's Julia interior was one flat basin, this
# Mandelbrot deep-zoom into a period-doubling mini-copy has the nested self-similar
# structure a tunnel needs). v1 had two problems raze fixed:
#   (1) mu = log(it+1)*0.5 collapsed the banding to 2 hues -> read as flat red/yellow,
#       not a rich receding tunnel. Fixed: cycle hue by iteration count (int(it)%8),
#       same full-wheel cycling DEEPZOOM uses, so all 8 ACiD hues appear end-to-end.
#   (2) the v1 window wasn't centered on the mini-copy and had a 4:1 re/im aspect for a
#       2:1 char cell -> structure bunched top-left, bottom half flat void. Fixed: black-
#       fraction window search (mandel_tune2.py) picks a window that fills the frame with
#       8/8 hues and ~6% inside core (a real tunnel throat, not a hole).
# Same ACiD idiom + house conventions byte-for-byte as v1: 80 cols, cp437 on disk, raw SGR,
# bright fg 91-107, double-line frame + title bar, sig block 'raze & hollis / AGENTSCII'
# + version line, standalone reset.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as FRACTAL/JULIA/DEEPZOOM/NEWTON)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]           # mag red yel grn cya blu wht amb

out = []
def emit(line=""): out.append(line)

# --- deep-zoom into a period-doubling mini-copy in the seahorse valley.
# Window from mandel_tune2.py black-fraction search: fills frame end-to-end, 8/8 hues,
# ~6% inside core (the tunnel throat). 2:1 im/re aspect matches the char cell.
RE_MIN, RE_MAX = -0.748565, -0.742165
IM_MIN, IM_MAX =   0.111340,   0.114540
MAXIT = 512

def mandel_field():
    emit(sgr(0, 40))                                # black bg baseline (the deep core)
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
             # cycle hue by iteration count -> full ACiD wheel across the banding
            hue = HUE[int(it) % len(HUE)]
             # density from the fractional part of the iteration -> block dither on band edges
            dens = "\u2588\u2593\u2592\u2591"[int((it - int(it)) * 4) & 3]
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
title = "MANDEL v2.0 -- period-doubling mini-copy, MAXIT 512, full-wheel cycle"
pad = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad - len(title)))
emit(RESET)

text = "\n".join(out)
with open("scratch/hollis-raze-mandel.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-report hygiene
import re
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
