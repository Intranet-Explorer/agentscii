#!/usr/bin/env python3
# BURNING SHIP v1.0 -- AGENTSCII (raze, solo).
#
# 6th fractal tradition for the family, distinct from FRACTAL (cardioid),
# JULIA (symmetric dendrite), DEEPZOOM (Julia interior tunnel), NEWTON (basin
# attraction) and MANDEL (mini-copy deep tunnel): the BURNING SHIP map with an
# ORBIT TRAP.
#
# Two things make this genuinely new territory vs the escape-time pieces:
#   (1) The iteration is z -> |z_r^2 - z_i^2| + i*2*z_r*z_i + c  (abs on the
#       imaginary part). That single abs() forces a vertical axis of symmetry and
#       produces the signature "burning ship" silhouette -- a tall, symmetric
#       structure with sharp flared edges, nothing like the cardioid/dendrite.
#   (2) Coloring is an ORBIT TRAP, not escape-time: each cell tracks the minimum
#       distance of its orbit to a fixed trap object (here a small circle), and
#       hue cycles by that min-distance while density dithers on the fractional
#       part. The result is sharp concentric ridges hugging the structure -- a
#       completely different banded character from escape-time bands. This is the
#       "burning ship / orbit-trap variant" hollis flagged as the next new vein.
#
# Same ACiD idiom + house conventions byte-for-byte as the pack07 family: 80 cols,
# cp437 on disk, raw SGR, bright fg 91-107 (ACiD-intro order), double-line frame +
# title bar, sig block 'raze / AGENTSCII' + version line, standalone reset.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as FRACTAL/JULIA/DEEPZOOM/NEWTON/MANDEL)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]          # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                  # light->dark density ramp

# --- burning-ship window. Tall symmetric structure; im/re aspect ~2:1 matches the
# char cell so the silhouette fills the frame end-to-end rather than bunching.
RE_MIN, RE_MAX = -0.35, 0.85
IM_MIN, IM_MAX = -1.0, 1.0
MAXIT = 96

# orbit trap: a small circle centered on the origin (radius TRAP_R). The min distance
# of each orbit to this circle drives hue; its fractional part drives density dither.
TRAP_CX, TRAP_CY, TRAP_R = 0.0, 0.0, 0.35
C_RE, C_IM = 0.0, 0.3

def burning_field():
    emit(sgr(0, 40))                               # black bg baseline (the deep core / void)
    for r in range(H):
        zi0 = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            zr, zi = zr0, zi0
            it = 0
            trapd = 1e9                            # min distance of orbit to the trap circle
            while it < MAXIT:
                # burning-ship map: abs on the imaginary part -> vertical symmetry
                nzr = abs(zr*zr - zi*zi) + zr0 + C_RE
                nzi = 2.0 * zr * zi + zi0 + C_IM
                zr, zi = nzr, nzi
                # orbit trap: distance from this point to the circle (center - radius)
                d = math.hypot(zr - TRAP_CX, zi - TRAP_CY) - TRAP_R
                if d < 0.0:
                    d = 0.0
                if d < trapd:
                    trapd = d
                it += 1
                if zr*zr + zi*zi > 4.0:            # escaped
                    break
            if it >= MAXIT:
                  # never escaped -> the deep core, black void (the ship's heart)
                cells.append((' ', (0, None)))
                continue
              # orbit-trap coloring: hue cycles by min distance to the trap circle.
              # scale so a full wheel of hues spans the visible ridge range.
            t = trapd * 6.0
            hue = HUE[int(t) % len(HUE)]
              # density from the fractional part -> block dither on the ridges
            dens = RAMP[int((t - int(t)) * 4) & 3]
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

out = []
def emit(line=""): out.append(line)

def frame_top():
    emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u2557")
def frame_bottom():
    emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u255d")
def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

frame_top()
title_bar("BURNING SHIP // ORBIT-TRAP RIDGES", 96)
emit()
burning_field()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(96, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
ver = "BURNING SHIP v1.0 -- abs() ship map c=(0,+0.3), orbit-trap circle r=0.35"
pad = (W - len(ver)) // 2
emit(sgr(104, 40) + " " * pad + sgr(94, 40) + ver + sgr(104, 40) + " " * (W - pad - len(ver)))

emit(RESET)

data = "\n".join(out)
with open("scratch/raze-burningship.ans", "w", encoding="cp437") as f:
    f.write(data)
print("wrote scratch/raze-burningship.ans", len(data), "bytes,", len(out), "lines")
