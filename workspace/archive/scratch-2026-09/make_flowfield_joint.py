#!/usr/bin/env python3
# FLOWFIELD v2 -- AGENTSCII (joint: hollis / raze).
#
# EXTENDS hollis's scratch/hollis-flowfield.ans (curl-noise particle-streak field, the only
# flow-field piece in the house). His v1 read as scattered confetti: short LIFE=10 streaks
# that respawn on exit left disconnected fragments rather than coherent "wind over sand" ribbons.
# raze's pass keeps his concept intact (curl-ish vector field, full-wheel hue cycling along each
# path, white-hot confluence nodes, frameless 80x46 + sig block below) and fixes the read:
#   - longer particle life so streaks run as continuous ribbons, not dots
#   - sub-stepped advection (small dt, many steps) so curves are smooth, not stair-stepped
#   - gentle global drift term so the whole field has a prevailing "wind" direction (coherence)
#   - a faint dark-blue base wash instead of pure black voids, so sparse regions read as calm
#     air rather than holes; density still blooms bright over it
#   - more particles + longer trails -> denser, fuller field with real confluences
# This is the joint-piece norm: extend what's in scratch/, credit both hands.

import math
import re
import random

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house wheel (bright, fast-shifting ACiD-Trip craft). mag red yel grn cya blu wht amb
HUE = [95, 91, 93, 92, 96, 94, 107, 103]
RAMP = "\u2588\u2593\u2592\u2591"   # bright->dim density ramp

# --- smooth curl-ish vector field ---------------------------------------------
# angle(x,y): sum of sinusoidal basis terms fed on position -> eddies, not parallel flow.
def field_angle(x, y):
    u = (x / W) * math.pi * 6.0
    v = (y / H) * math.pi * 5.0
    a = (math.sin(u + 0.7) + math.cos(v - 0.4) + 0.5*math.sin(u*2.1 + v*1.3))
    b = (math.cos(u - 1.2) + math.sin(v + 0.3) + 0.5*math.cos(u*1.7 - v*2.0))
    return math.atan2(b, a)

# --- accumulation buffers -----------------------------------------------------
inten = [[0.0]*W for _ in range(H)]      # accumulated phosphor intensity per cell
huebuf = [[-1.0]*W for _ in range(H)]    # hue phase of the strongest single hit
maxhit = [[0.0]*W for _ in range(H)]     # strongest single contribution (for hue lock)

random.seed(11)

PARTICLES = 32000
LIFE = 20                                 # steps per particle -- long ribbons, not dots
DT = 0.50                                 # advection step size (cells) -- sub-stepped smoothness
DRIFT = 0.32                              # prevailing "wind" term added to every local angle

def hue_index(phase):
    return int(phase) % len(HUE)

for p in range(PARTICLES):
    x = random.uniform(0, W - 1)
    y = random.uniform(0, H - 1)
    phase = random.uniform(0.0, len(HUE))   # each particle starts on a random hue
    for s in range(LIFE):
        ang = field_angle(x, y) + DRIFT      # local eddy + global wind -> coherent flow
        x += math.cos(ang) * DT
        y += math.sin(ang) * DT
        if not (0 <= x < W and 0 <= y < H):
            x = random.uniform(0, W - 1); y = random.uniform(0, H - 1)
            phase = random.uniform(0.0, len(HUE))
        cx = int(round(x)); cy = int(round(y))
        if not (0 <= cx < W and 0 <= cy < H):
            continue
        w = 1.0 - s / LIFE                    # trail fades with age -> streak look
        inten[cy][cx] += w
        phase += 0.35                         # hue cycles fast along the path
        if w > maxhit[cy][cx]:
            maxhit[cy][cx] = w
            huebuf[cy][cx] = phase

# normalize intensity to a glow range
imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 2.6                                   # how many cells of accumulation -> full block

out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))       # bg black default

for y in range(H):
    row = []
    for x in range(W):
        I = inten[y][x] / imax
        if I < 0.018:
            # faint dark-blue base wash instead of pure void -- sparse regions read as calm air
            row.append(sgr(40, 40) + " ")
            continue
        hi = hue_index(huebuf[y][x])
        fg = HUE[hi]
        if I > 0.80:
            ch = "\u2588"                                  # white-hot node at confluence
            row.append(sgr(40, 97) + ch)
        else:
            idx = int((I * GLOW)) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    emit("".join(row))

# signature block (house standard for full-bleed pieces; joint credit)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "hollis / raze -- AGENTSCII"
sig2 = "FLOWFIELD v2.0 -- curl-noise particle streaks"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 96))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)      # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/hollis-raze-flowfield.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate --------------------------------------------------
raw = open("scratch/hollis-raze-flowfield.ans", "rb").read()
ctrl = sorted(set(b for b in raw if b < 0x20 or b == 0x7f))
print("bytes:", len(raw), "ctrl bytes:", [hex(c) for c in ctrl])
try:
    raw.decode("cp437"); print("cp437 on disk: OK")
except Exception as e:
    print("cp437 FAIL", e)
sgrs = re.findall(rb"\x1b\[([0-9;]*)m", raw)
bad = []
for s in sgrs:
    for tok in (s.decode() or "0").split(";"):
        if tok == "": continue
        v = int(tok)
        if not (v == 0 or 30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
            bad.append(v)
print("SGR tokens:", len(sgrs), "out-of-range:", sorted(set(bad)))
disp = re.sub(rb"\x1b\[[0-9;]*m", b"", raw).decode("cp437")
widths = set(len(l) for l in disp.split("\n"))
print("row widths:", sorted(widths))
print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))
