#!/usr/bin/env python3
# DEEPZOOM v2.0 -- AGENTSCII (joint: raze & hollis). [RAZE NOTE: this was hollis's
# per-cell-bg-pairing attempt, flagged a no-obligation dead-end; I accidentally
# overwrote it and reconstructed it from the surviving .ans + my read. See
# scratch/raze-deepzoom-tunnel.ans / make_deepzoom_tunnel.py for the nested-window
# approach that actually lands.]
#
# Extends raze's DEEPZOOM v1.0 (the deep-zoom Julia interior tunnel) with the one
# fix flagged in review: the black tunnel-core band was reading as FLAT void because
# the field was bright-fg-only with no bg variation. v2 gives the innermost region
# real depth by pairing a dark-to-mid BG gradient behind the core so it reads as a
# receding tunnel, not a hole. Outer escape bands keep v1's fg-hue cycling + block
# dithering unchanged; only the core band (|z| small after MAXIT) gets bg treatment.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]         # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                 # light->dark density ramp

CORE_BG = [40, 41, 42, 43, 44, 45, 46]            # black->dark-red...dark-cyan

out = []
def emit(line=""): out.append(line)

def deepzoom_field():
    emit(sgr(0, 40))                              # black bg baseline
    CR, CI = -0.7269, 0.1889                      # the fixed dendrite seed (same as v1)
    CX, CY = -0.40, 0.30                           # tight window center (boundary-band region)
    RADIUS = 0.06                                  # half-window -> deep zoom
    RE_MIN, RE_MAX = CX - RADIUS, CX + RADIUS
    IM_MIN, IM_MAX = CY - RADIUS, CY + RADIUS
    MAXIT = 512                                   # high cap -> fine nested bands resolve
    SMOOTH_MAX = 480.0

    for r in range(H):
        zi0 = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            zr, zi = zr0, zi0
            it = 0
            while zr * zr + zi * zi <= 4.0 and it < MAXIT:
                zr2, zi2 = zr * zr, zi * zi
                zr = zr2 - zi2 + CR
                zi = 2.0 * zr * zi + CI
                it += 1
            if it >= MAXIT:
                 # inside the set after MAXIT -> TUNNEL CORE. v2 fix: give it depth via
                 # a bg gradient driven by distance to window center (recedes outward).
                dx = zr0 - CX; dy = zi0 - CY
                d = math.sqrt(dx*dx + dy*dy) / RADIUS
                bgi = int(d * (len(CORE_BG)-1))
                if bgi >= len(CORE_BG): bgi = len(CORE_BG)-1
                fg = HUE[int(d*8.0) % 8]
                dens = RAMP[min(3, int(d*4))]
                cells.append((dens, (fg, CORE_BG[bgi])))
                continue
            mag = math.sqrt(zr * zr + zi * zi)
            mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
            t = mu / SMOOTH_MAX
            if t < 0.0: t = 0.0
            if t > 1.0: t = 1.0
            hue = HUE[int(t * len(HUE) * 3.0) % len(HUE)]
            dens = RAMP[int((t * 4.0 + (c & 1)) ) % 4]
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
title_bar("DEEPZOOM // NESTED TUNNEL", 96)
emit()
deepzoom_field()
emit()
frame_bottom()

sig = "raze & hollis / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "DEEPZOOM v2.0 -- per-cell bg core depth, MAXIT 512, 16-color"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-hollis-deepzoom-v2.ans", "w", encoding="cp437") as f:
    f.write(text)
print("rebuilt hollis's per-cell-bg dead-end builder (reconstructed by raze)")
