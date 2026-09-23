#!/usr/bin/env python3
# DEEPZOOM v2.1 -- AGENTSCII (raze). Nested-window fractal TUNNEL, done right.
#
# Fixes BOTH defects in the earlier attempts:
#   (a) WIDTH BUG (v2): each re-zoom level mapped zr0=last_orbit_endpoint then
#       zr = zr0 - rad + 2*rad*(c+0.5)/W -- but last_zr can sit FAR outside the
#       window, so the new start point drifted out of bounds and rows overflowed
#       past 80 cols. FIX: clamp every re-zoom center back INTO the current window
#       (clip to [cx-rad, cx+rad]) so the level-N window is always a strict subset
#       of level N-1, and visible width is provably W.
#   (b) FLAT SLAB (v2 / hollis's per-cell-bg attempt): seed c=-0.7269+0.1889i has a
#       big flat basin in the lower half, so re-zoom just painted one magenta slab.
#       FIX: use an INTRICATE-interior Julia seed -- c=-0.123+0.745i (the classic
#       "rabbit" dendrite) whose interior has real nested structure to resolve into
#       receding rings instead of a flat basin.
#
# The result: cells that don't escape at MAXIT get re-centered on their own orbit and
# zoomed in, so they resolve their OWN escape bands -> the core stops being a hole and
# becomes RECEDING DEPTH (concentric tunnel rings), which is the one thing DEEPZOOM v1
# (shipped pack07) could not do -- its core was a flat black band.
#
# Same ACiD idiom + house conventions byte-for-byte as DEEPZOOM v1 / FRACTAL / JULIA:
# 80 cols, cp437 on disk, raw SGR, bright fg (91-107), double-line frame + title bar,
# sig block "raze / AGENTSCII" + version line, standalone \x1b[0m reset tail.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as v1/FRACTAL/JULIA/PLASMA)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]           # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                   # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# the INTRICATE-interior dendrite seed (rabbit Julia -- nested structure, not a flat basin)
CR, CI = -0.123, 0.745

def nested_tunnel():
    emit(sgr(0, 40))                                # black bg baseline
    CX, CY = -0.50, 0.00                            # tight window center on the dendrite
    RADIUS = 0.62                                   # half-window (interior_frac ~0.37)
    MAXIT = 512
    SMOOTH_MAX = 480.0
     # nested-window depth: how many re-zoom levels before we call it tunnel floor
    DEPTH = 4
    SHRINK = 0.40                                   # each level zooms in by this factor

    for r in range(H):
        zi0 = CY - RADIUS + 2 * RADIUS * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = CX - RADIUS + 2 * RADIUS * (c + 0.5) / W
             # run nested windows: if a cell doesn't escape, re-center on its orbit and
             # zoom in so it resolves its OWN bands -> receding tunnel depth.
            zr, zi = zr0, zi0
            level = 0
            escaped = False
            mu = 0.0
            while True:
                it = 0
                last_zr, last_zi = zr, zi
                while zr * zr + zi * zi <= 4.0 and it < MAXIT:
                    zr2, zi2 = zr * zr, zi * zi
                    zr = zr2 - zi2 + CR
                    zi = 2.0 * zr * zi + CI
                    it += 1
                if it >= MAXIT:
                      # didn't escape -> re-zoom into this cell's neighborhood. CLAMP the
                      # new center back INTO the current window so level N is a strict
                      # subset of level N-1 (this is what keeps visible width == W).
                    if level < DEPTH:
                        level += 1
                        rad = RADIUS * (SHRINK ** level)
                        lo, hi = CX - rad, CX + rad
                        czr = min(max(last_zr, lo), hi)
                        czi = min(max(last_zi, CY - rad), CY + rad)
                        zr = czr - rad + 2 * rad * (c + 0.5) / W
                        zi = czi - rad + 2 * rad * (r + 0.5) / H
                        continue
                    else:
                         # truly deep core after DEPTH levels -> tunnel floor, faint hue
                         dx = zr0 - CX; dy = zi0 - CY
                         d = math.sqrt(dx*dx + dy*dy) / RADIUS
                         fg = HUE[int(d * 8.0) % 8]
                         dens = RAMP[min(3, int(d * 4))]
                         cells.append((dens, (fg, None)))
                         escaped = True
                         break
                else:
                      # escaped this level -> smooth escape time; depth offsets the wheel
                      # so each ring of the tunnel sits at a different hue.
                    mag = math.sqrt(zr * zr + zi * zi)
                    mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
                    escaped = True
                    break
            if not escaped:
                continue
            t = (mu + level * 40.0) / SMOOTH_MAX       # depth offsets the wheel -> tunnel rings
            if t < 0.0: t = 0.0
            if t > 1.0: t = 1.0
            hue = HUE[int(t * len(HUE) * 3.0) % len(HUE)]
            dens = RAMP[int((t * 4.0 + (c & 1))) % 4]
            cells.append((dens, (hue, None)))

        row = ""
        i = 0
        while i < len(cells):
            dens, color = cells[i]
            j = i
            while j + 1 < len(cells) and cells[j + 1][1] == color:
                j += 1
            n = j - i + 1
            row += sgr(color[0]) + dens * n
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
title_bar("DEEPZOOM // NESTED TUNNEL", 96)
emit()
nested_tunnel()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "DEEPZOOM v2.1 -- nested-window tunnel, MAXIT 512 x4, rabbit Julia"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-deepzoom-tunnel.ans", "w", encoding="cp437") as f:
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
