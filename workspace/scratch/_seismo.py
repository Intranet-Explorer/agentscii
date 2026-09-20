#!/usr/bin/env python3
# SEISMOGRAPH v2 -- AGENTSCII (raze). A wasteland read as a seismic event-trace on a phosphor scope.
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
# with a quiet baseline and violent EVENTS (the quakes). Different curve family AND different backdrop
# structure (a time graticule + baseline, not a polar ring or Cartesian loop lattice). Reads as the
# fourth member of the scope family: the ground's own heartbeat.
#
# v2 -- hollis's critique on v1 acted on, non-destructively:
#   (a) REAL time-graticule across the full field: faint vertical time ticks + horizontal amplitude
#       gridlines + a baseline rule, so empty space has STRUCTURE instead of dead black. v1's
#       backdrop returned flat black everywhere except the baseline -- bumped density here.
#   (b) SUBSTRATE-style bezel + top title card (amber outer / dim-blue inner), matching the accepted
#       scope-family precedent, so it reads as a framed instrument, not a bare sig block.
#   (c) a SECOND + THIRD event pulse so the trace reads as a SERIES of quakes, not a one-off spike.
#   Also fixed a latent v1 bug: the sweep spanned only the LEFT HALF of the 80-col field
#   (AX = CX*0.94 ~= 37), clustering every event left-of-center and leaving the right side dead.
#   The sweep now spans the full field width inside the bezel.

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
HUE = [91, 93, 95, 103]           # bright red / yellow / magenta / amber
RAMP = "\u2588\u2593\u2592\u2591"   # bright->dim density ramp (full block first)

# --- scope screen region (inside the bezel) -----------------------------------
X0, X1 = 2, W - 3                 # left/right inner edges of the phosphor screen
Y0, Y1 = 2, H - 3                 # top/bottom inner edges
SX0, SX1 = float(X0), float(X1)   # sweep spans this full width (fixes v1's half-field bug)
SY0, SY1 = float(Y0), float(Y1)
BASELINE = (Y0 + Y1) / 2.0        # the quiet ground level, centered in the screen

# --- faint time graticule: structure for the empty space ----------------------
GRID_X = 4                         # vertical time ticks every N cells (bumped from 8 -> denser)
GRID_Y = 4                         # horizontal amplitude gridlines every N cells
def backdrop_graticule(x, y):
    """Time-scope grid -- a baseline rule + faint warm/cyan ticks so empty space has structure."""
    if abs(y - BASELINE) < 0.5:                       # the resting ground line (full-width rule)
        return sgr(40, 91) + "\u2591"                 # dim red baseline
    on_v = (x % GRID_X == 0)                          # vertical time ticks
    on_h = (y % GRID_Y == 0)                          # horizontal amplitude lines
    if on_v and on_h:                                 # intersections read slightly brighter
        return sgr(40, 97) + "\u2591"                  # gray node
    if on_v or on_h:
        return sgr(40, 96) + " "                      # faint dim-cyan tick (structure, not flat black)
    return sgr(40, 40) + " "

# --- accumulation buffers -----------------------------------------------------
inten = [[0.0]*W for _ in range(H)]
huebuf = [[-1.0]*W for _ in range(H)]
maxhit = [[0.0]*W for _ in range(H)]

AY = (SY1 - SY0) / 2.0 * 0.94        # vertical amplitude headroom for the event spikes
SAMPLES = 7000                       # dense enough that the trace is continuous, not dotted

def hue_index(phase):
    return int(phase) % len(HUE)

# --- the signal: a quiet baseline with a SERIES of violent events -------------
# amplitude(t): low-frequency tremor + high-frequency noise on the ground, then THREE decaying
# oscillations = main shock + aftershock + a second independent quake. This is what makes it read as
# an EVENT SERIES (a sequence of quakes), not static and not a single one-off spike.
def _shock(t, t0, sigma, amp, freq, phase):
    d = t - t0
    env = math.exp(-(d*d) / (2.0 * sigma*sigma))
    return env * amp * math.sin((t * math.pi * 2.0) * freq + phase)

def amplitude(t):
    u = t * math.pi * 2.0
    ramp = min(1.0, max(0.0, (t - 0.05) / 0.25))     # tremor swells in from the left edge
    tremor = ramp * (0.07 * math.sin(u * 7.0) + 0.035 * math.sin(u * 19.0 + 1.3))
    e1 = _shock(t, 0.30, 0.040, 0.92, 31.0, 0.7)     # main shock (biggest, left-of-center)
    e2 = _shock(t, 0.46, 0.028, 0.50, 37.0, 2.1)     # aftershock trailing it
    e3 = _shock(t, 0.74, 0.034, 0.66, 29.0, 4.0)     # second independent quake (right side)
    return tremor + e1 + e2 + e3

for i in range(SAMPLES):
    t = i / SAMPLES
    x = SX0 + (SX1 - SX0) * t              # monotone time sweep, full field width left -> right
    y = BASELINE - amplitude(t) * AY       # up = positive displacement
    cx = int(round(x)); cy = int(round(y))
    if X0 <= cx <= X1 and Y0 <= cy <= Y1:
        inten[cy][cx] += 1.0
        phase = t * 30.0                   # hue cycles fast along the sweep (dense ACiD shift)
        if 1.0 > maxhit[cy][cx]:
            maxhit[cy][cx] = 1.0
            huebuf[cy][cx] = phase

# normalize intensity to a glow range
imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 2.6                                 # how many cells of accumulation -> full block

# --- render the phosphor screen into a cell buffer (char, fg) -----------------
cell = [[None]*W for _ in range(H)]        # each entry: (ch, fg) or None (unwritten -> backdrop)
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        I = inten[y][x] / imax
        if I < 0.06:
            continue                       # leave as backdrop graticule
        fg = HUE[hue_index(huebuf[y][x])]
        if I > 0.78:
            cell[y][x] = ("\u2588", 97)    # white-hot node at the event peak
        else:
            idx = int((I * GLOW)) % 4
            cell[y][x] = (RAMP[idx], fg)

# --- bezel + title card (SUBSTRATE-style frame, Pass 6) ----------------------
def setc(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        cell[y][x] = (ch, fg)

# outer amber rule + inner dim-blue rule around the whole field
for x in range(W):
    setc(x, 0, "\u2550", 93); setc(x, H - 1, "\u2550", 93)
    setc(x, 1, "\u2591", 94);   setc(x, H - 2, "\u2591", 94)
for y in range(H):
    setc(0, y, "\u2551", 93); setc(W - 1, y, "\u2551", 93)
    setc(1, y, "\u2591", 94);   setc(W - 2, y, "\u2591", 94)
# bright corners on the outer rule
for (cx, cy) in [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)]:
    setc(cx, cy, "\u2588", 93)

# top title card (inside the top border row 1)
title = "SEISMOGRAPH // a wasteland read as the ground's own pulse"
tx = (W - len(title)) // 2
for i, ch in enumerate(title):
    setc(tx + i, 1, ch, 93)

# --- emit --------------------------------------------------------------------
out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))                          # bg black default
for y in range(H):
    row = []
    for x in range(W):
        c = cell[y][x]
        if c is None:
            row.append(backdrop_graticule(x, y))
        else:
            ch, fg = c
            row.append(sgr(40, fg) + ch)
    emit("".join(row))

# signature block (house standard for full-bleed pieces, as SUBSTRATE/LANTERNKEEPER)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "raze / AGENTSCII"
sig2 = "SEISMOGRAPH v2.0 -- the ground's own pulse"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 93))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)                               # standalone reset tail (house idiom)

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
print("blank runs >=3:", blank_runs if blank_runs else "none")
