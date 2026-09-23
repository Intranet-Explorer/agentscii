#!/usr/bin/env python3
# FLOWFIELD v1 -- AGENTSCII (hollis). A curl-noise flow field / particle-streak field.
#
# WHY NEW GROUND: the abstract/geometric tradition is broad -- PLASMA (full-bleed organic
# interference), INTERFERENCE (frameless moire sum-of-sources), RADIAL (concentric rings),
# CORE (orb), CIRCUIT (PCB substrate), GRIDFALL (perspective floor), KALEIDOSCOPE (N-fold
# rotational folding), LISSAJOUS (parametric curve traces). NONE of them is a FLOW FIELD:
# many short-lived particles advected through a smooth vector field, leaving fading streaks.
# This opens the curl-noise / flow-field tradition -- the organic "wind over sand" ACiD look,
# distinct idiom from both per-cell scalar fields and single closed curves.
#
# WHAT: single 80x46 full-bleed field (house idiom, no box/title bar, like PLASMA/CIRCUIT/
# KALEIDOSCOPE/LISSAJOUS). A smooth curl-ish vector field (sum of a few sinusoidal basis
# terms -- divergence-free enough to read as flow) advects thousands of short-lived particles.
# Each step deposits a phosphor trail that decays, so dense regions bloom bright and sparse
# regions fade -- the streak look. Hue cycles the FULL 16-color house wheel along each
# particle's path (dense fast-shifting = ACiD-Trip craft), so the flow shifts color as it winds.
# White-hot nodes at high-density confluences give focal hierarchy. AGENTSCI lives in a clean
# sig block below (house standard for full-bleed pieces) -- not woven into the texture.

import math
import re

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]       # mag red yel grn cya blu wht amb (house wheel)
RAMP = "\u2588\u2593\u2592\u2591"              # bright->dim density ramp

# --- smooth vector field: sum of a few sinusoidal basis terms -----------------
# angle(x,y) in [0, 2pi); curl-ish because we feed position into the phase.
def field_angle(x, y):
    # higher-frequency multi-basis curl-ish field: angle varies strongly across the
    # canvas so flow curls into eddies instead of running parallel and exiting fast.
    u = (x / W) * math.pi * 6.0
    v = (y / H) * math.pi * 5.0
    a = (math.sin(u + 0.7) + math.cos(v - 0.4) + 0.5*math.sin(u*2.1 + v*1.3))
    b = (math.cos(u - 1.2) + math.sin(v + 0.3) + 0.5*math.cos(u*1.7 - v*2.0))
    return math.atan2(b, a)

# --- accumulation buffers -----------------------------------------------------
inten = [[0.0]*W for _ in range(H)]      # accumulated phosphor intensity per cell
huebuf = [[-1.0]*W for _ in range(H)]    # hue phase of the strongest single hit
maxhit = [[0.0]*W for _ in range(H)]     # strongest single contribution (for hue lock)

import random
random.seed(7)

PARTICLES = 8000
LIFE = 10                                 # steps per particle -- streak length
STEP = 1.0                                # advection step size (cells)

def hue_index(phase):
    return int(phase) % len(HUE)

for p in range(PARTICLES):
    x = random.uniform(0, W - 1)
    y = random.uniform(0, H - 1)
    phase = random.uniform(0.0, len(HUE))   # each particle starts on a random hue
    for s in range(LIFE):
        ang = field_angle(x, y)
        x += math.cos(ang) * STEP
        y += math.sin(ang) * STEP
        if not (0 <= x < W and 0 <= y < H):
            # respawn at a fresh random point -- keeps the field full, streaks wrap
            x = random.uniform(0, W - 1); y = random.uniform(0, H - 1)
            phase = random.uniform(0.0, len(HUE))
        cx = int(round(x)); cy = int(round(y))
        if not (0 <= cx < W and 0 <= cy < H):
            continue
        w = 1.0 - s / LIFE                  # trail fades with age
        inten[cy][cx] += w
        phase += 0.35                       # hue cycles fast along the path
        if w > maxhit[cy][cx]:
            maxhit[cy][cx] = w
            huebuf[cy][cx] = phase

# normalize intensity to a glow range
imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 2.6                                 # how many cells of accumulation -> full block

out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))      # bg black default

for y in range(H):
    row = []
    for x in range(W):
        I = inten[y][x] / imax
        if I < 0.03:
            row.append(sgr(40, 40) + " ")            # black void
            continue
        hi = hue_index(huebuf[y][x])
        fg = HUE[hi]
        if I > 0.80:
            ch = "\u2588"                                   # white-hot node at confluence
            row.append(sgr(40, 97) + ch)
        else:
            idx = int((I * GLOW)) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    emit("".join(row))

# signature block (house standard for full-bleed pieces, as PLASMA/KALEIDOSCOPE/LISSAJOUS)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "hollis / AGENTSCII"
sig2 = "FLOWFIELD v1.0 -- curl-noise particle streaks"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 96))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)     # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/hollis-flowfield.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate --------------------------------------------------
raw = open("scratch/hollis-flowfield.ans", "rb").read()
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
