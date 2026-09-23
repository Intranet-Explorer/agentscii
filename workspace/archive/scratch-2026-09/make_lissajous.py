#!/usr/bin/env python3
# LISSAJOUS v1 -- AGENTSCII (raze). A phosphor oscilloscope / Lissajous figure field.
#
# WHY NEW GROUND: the abstract/geometric tradition is broad (PLASMA full-bleed organic
# interference, INTERFERENCE frameless moire sum-of-sources, RADIAL concentric rings,
# CORE orb, CIRCUIT PCB substrate, GRIDFALL perspective floor, KALEIDOSCOPE N-fold
# rotational folding). NONE of them draws a PARAMETRIC CURVE -- a 1D path traced through
# the 2D field. This opens the Lissajous/oscilloscope tradition: x=A*sin(a*t+d), y=B*sin(b*t),
# the looping closed figures with self-intersections, rendered as a bright cycling phosphor
# trace over a faint scope graticule. Distinct idiom (a curve, not a per-cell field).
#
# WHAT: single 80x46 full-bleed field (house idiom, no box/title bar, like PLASMA/CIRCUIT/
# KALEIDOSCOPE). A faint dim graticule grid gives the "scope screen" structure to empty space.
# Three Lissajous harmonics (3:2, 5:4, 7:5 -- classic beautiful figures) are traced over many
# samples each; every cell they pass through ACCUMULATES intensity with a phosphor decay so
# overlapping nodes bloom bright and trails fade -- the oscilloscope look. Hue cycles the FULL
# 16-color house wheel along the parameter t (dense fast-shifting = ACiD-Trip craft), so the
# trace shifts color as it winds. White-hot nodes at high-intensity self-intersections give
# focal hierarchy. AGENTSCI lives in a clean sig block below (house standard for full-bleed
# pieces, as PLASMA/KALEIDOSCOPE) -- not woven into the texture.

import math
import re

W = 80
H = 46
CX = W / 2.0
CY = H / 2.0
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]      # mag red yel grn cya blu wht amb (house wheel)
RAMP = "\u2588\u2593\u2592\u2591"             # bright->dim density ramp

# --- faint scope graticule ----------------------------------------------------
GRID_STEP = 8                                    # grid line every N cells
def in_grid(x, y):
    return (x % GRID_STEP == 0) or (y % GRID_STEP == 0)

# --- Lissajous harmonics: (a, b, delta, hue_offset, amp_scale) ----------------
HARMONICS = [
    (3.0, 2.0, math.pi/2.0, 0.0, 0.86),   # 3:2 -- classic figure-8-ish loop
    (5.0, 4.0, math.pi/3.0, 1.0, 0.70),   # 5:4 -- denser weave
    (7.0, 5.0, math.pi/4.0, 2.0, 0.56),   # 7:5 -- fine lace overlay
]

# --- accumulation buffers -----------------------------------------------------
inten = [[0.0]*W for _ in range(H)]     # accumulated phosphor intensity per cell
huebuf = [[-1.0]*W for _ in range(H)]   # hue phase of the strongest single hit
maxhit = [[0.0]*W for _ in range(H)]    # strongest single contribution (for hue lock)

AX = CX * 0.92                            # horizontal amplitude (leave margin)
AY = CY * 0.90                            # vertical amplitude
SAMPLES = 4000                           # per harmonic -- dense enough for smooth curves

def hue_index(phase):
    return int(phase) % len(HUE)

for (a, b, delta, hoffset, amp) in HARMONICS:
    A = AX * amp
    B = AY * amp
    for i in range(SAMPLES):
        t = 2.0 * math.pi * i / SAMPLES
        x = CX + A * math.sin(a * t + delta)
        y = CY + B * math.sin(b * t)
        # phosphor decay: contribution falls off with distance from the exact point
        cx = int(round(x)); cy = int(round(y))
        if 0 <= cx < W and 0 <= cy < H:
            w = 1.0
            inten[cy][cx] += w
            phase = t * 3.0 + hoffset * 2.0   # hue cycles fast along the trace
            if w > maxhit[cy][cx]:
                maxhit[cy][cx] = w
                huebuf[cy][cx] = phase

# normalize intensity to a glow range
imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 3.2                                # how many cells of accumulation -> full block

out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))     # bg black default

for y in range(H):
    row = []
    for x in range(W):
        I = inten[y][x] / imax            # normalized [0,1]
        if I < 0.06:
            # empty space -> faint graticule or near-black vignette
            if in_grid(x, y):
                row.append(sgr(40, 94) + "\u2591")      # dim cyan grid tick
            else:
                row.append(sgr(40, 40) + " ")           # black void
            continue
        hi = hue_index(huebuf[y][x])
        fg = HUE[hi]
        if I > 0.78:
            ch = "\u2588"                                  # white-hot node at self-intersection
            row.append(sgr(40, 97) + ch)
        else:
            idx = int((I * GLOW)) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    emit("".join(row))

# signature block (house standard for full-bleed pieces, as PLASMA/KALEIDOSCOPE)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "raze / AGENTSCII"
sig2 = "LISSAJOUS v1.0 -- phosphor oscilloscope field"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 96))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)    # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/raze-lissajous.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate --------------------------------------------------
raw = open("scratch/raze-lissajous.ans", "rb").read()
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
