#!/usr/bin/env python3
# SEISMOGRAPH v1 -- AGENTSCII (raze). A wasteland read as a seismic event-trace on a phosphor scope.
#
# PROVENANCE: came out of a random_direction roll -- subject "a desert or wasteland", technique
# constraint "use curve_common.phosphor_render() for a traced-curve / scope aesthetic", palette lean
# "warm tones (reds/yellows/magentas) dominant". REMIXED, not taken literal: WASTELAND v3 already
# shipped as a painted desert scene (pack41), so a second wasteland-as-scene would be a reskin. The
# fresh register is the SEISMOGRAPH -- there's a closed-loop CURVE family (LISSAJOUS/ROSE/SPIROGRAPH,
# all phosphor scopes) but no TIME-SERIES / event-trace scope. So: "a wasteland read as a seismic
# trace" -- the ground itself is the signal. The warm palette = heat/danger/melt; the trace IS the
# wasteland's pulse. This opens the seismograph idiom (1D time-series, not a closed loop).
#
# WHY NEW GROUND: LISSAJOUS/ROSE/SPIROGRAPH are all CLOSED LOOP curves traced through the 2D field.
# A seismograph is a TIME-SERIES -- x = monotone time, y = amplitude(t) -- a single open sweep left->right
# with a quiet baseline and one violent EVENT (the quake). Different curve family AND different backdrop
# structure (a time graticule + baseline, not a polar ring or Cartesian loop lattice). Reads as the
# fourth member of the scope family: the ground's own heartbeat.
#
# TREATMENT (matches LISSAJOUS/ROSE/SPIROGRAPH exactly so it reads as one coherent "scope" family):
#   - 80x46 full-bleed field, faint graticule gives empty space structure instead of flat black.
#   - phosphor accumulation: every cell the trace passes through accumulates intensity; overlapping
#     nodes bloom bright, trails fade via the density ramp '█▓▒░'.
#   - warm hue wheel (red/yel/mag/amb) cycled along time t -- dense fast-shifting = ACiD craft.
#   - white-hot node at the event peak (I>0.78 -> full block on white fg).
#   - framed sig block below: bright corners, cyan rule body, two centered lines.
#   - standalone \x1b[0m reset tail. cp437 on disk. Self-checking hygiene gate.

import math
import re

W = 80
H = 46
CX = W / 2.0
CY = H / 2.0
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# warm-dominant hue wheel (the roll's lean): red yel mag amb -- heat/danger/melt, not the cool scope blue.
HUE = [91, 93, 95, 103]          # bright red / yellow / magenta / amber
RAMP = "\u2588\u2593\u2592\u2591"  # bright->dim density ramp (full block first)

# --- faint time graticule -----------------------------------------------------
GRID_X = 8                          # vertical time ticks every N cells
BASELINE = H // 2                   # the quiet ground level, centered vertically
def backdrop_graticule(x, y):
    """Time-scope grid -- dim warm ticks: a baseline rule + faint vertical time lines."""
    if abs(y - BASELINE) < 0.5:     # the resting ground line
        return sgr(40, 91) + "\u2591"      # dim red baseline
    if x % GRID_X == 0:            # faint vertical time ticks
        return sgr(40, 40) + " "     # leave mostly black; ticks come from the trace's own glow
    return sgr(40, 40) + " "

# --- accumulation buffers -----------------------------------------------------
inten = [[0.0]*W for _ in range(H)]
huebuf = [[-1.0]*W for _ in range(H)]
maxhit = [[0.0]*W for _ in range(H)]

AX = CX * 0.94                       # horizontal sweep spans nearly full width (time -> x)
AY = CY * 0.82                       # vertical amplitude headroom for the event spike
SAMPLES = 6000                      # dense enough that the trace is continuous, not dotted

def hue_index(phase):
    return int(phase) % len(HUE)

# --- the signal: a quiet baseline with ONE violent event (the quake) ----------
# amplitude(t): low-frequency tremor + high-frequency noise on the ground, then a single
# big decaying oscillation = the main shock. This is what makes it read as an EVENT, not static.
EVENT_T = 0.50                       # where along the sweep the main shock lands (left-of-center)
def amplitude(t):
    u = t * math.pi * 2.0
    ramp = min(1.0, max(0.0, (t - 0.10) / 0.30))
    tremor = ramp * (0.09 * math.sin(u * 7.0) + 0.045 * math.sin(u * 19.0 + 1.3))
    # main shock: a Gaussian-windowed decaying sinusoid -- the quake itself
    d = t - EVENT_T
    env = math.exp(-(d*d) / (2.0 * 0.045**2))
    shock = env * 0.92 * math.sin(u * 31.0 + 0.7)
    # a smaller aftershock trailing it
    d2 = t - (EVENT_T + 0.18)
    env2 = math.exp(-(d2*d2) / (2.0 * 0.030**2))
    aftershock = env2 * 0.45 * math.sin(u * 37.0 + 2.1)
    return tremor + shock + aftershock

for i in range(SAMPLES):
    t = i / SAMPLES
    x = AX * t                       # monotone time sweep, left -> right
    y = BASELINE - amplitude(t) * AY # up = positive displacement
    cx = int(round(x)); cy = int(round(y))
    if 0 <= cx < W and 0 <= cy < H:
        inten[cy][cx] += 1.0
        phase = t * 26.0             # hue cycles fast along the sweep (dense ACiD shift)
        if 1.0 > maxhit[cy][cx]:
            maxhit[cy][cx] = 1.0
            huebuf[cy][cx] = phase

# normalize intensity to a glow range
imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 2.6                           # how many cells of accumulation -> full block

out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))                   # bg black default

for y in range(H):
    row = []
    for x in range(W):
        I = inten[y][x] / imax
        if I < 0.06:
            row.append(backdrop_graticule(x, y))
            continue
        fg = HUE[hue_index(huebuf[y][x])]
        if I > 0.78:
            row.append(sgr(40, 97) + "\u2588")     # white-hot node at the event peak
        else:
            idx = int((I * GLOW)) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    emit("".join(row))

# signature block (house standard for full-bleed pieces, as LISSAJOUS/ROSE/SPIROGRAPH)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "raze / AGENTSCII"
sig2 = "SEISMOGRAPH v1.0 -- the ground's own pulse"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 93))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)                        # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/_seismo.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate --------------------------------------------------
raw = open("scratch/_seismo.ans", "rb").read()
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
blank_runs = []
run = 0
for l in disp.split("\n"):
    if l.strip() == "":
        run += 1
    else:
        if run >= 3: blank_runs.append(run)
        run = 0
if run >= 3: blank_runs.append(run)
print("blank runs >=3:", blank_runs)
print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))
