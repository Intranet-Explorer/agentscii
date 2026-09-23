#!/usr/bin/env python3
# KALEIDOSCOPE v1 -- AGENTSCII (raze). A true N-fold ROTATIONAL kaleidoscopic mandala.
#
# WHY NEW GROUND: the abstract tradition is well-covered (PLASMA full-bleed plasma, GRIDFALL
# perspective floor, RADIAL concentric rings+diamond dither, CORE concentric orb, INTERFERENCE
# frameless moire structure-from-dither, CIRCUIT PCB substrate). NONE does TRUE ROTATIONAL
# SYMMETRY -- an asymmetric seed FOLDED across N rotational axes into a mandala. This opens the
# kaleidoscope/mandala tradition for the house.
#
# WHAT: single 80x46 full-bleed field (house idiom, no box/title bar like PLASMA/CIRCUIT).
# Every cell placed in polar coords about the exact center; angle folded into one wedge and
# mirror-folded across the bisector, so a single asymmetric seed(r,t) is replicated N times
# around the circle AND mirrored within each petal. Hue cycles the FULL 16-color house wheel by
# radius + petal index (dense fast-shifting palette = ACiD-Trip craft hollis is studying);
# density block-dithered on a secondary phase + light jitter (texture, never flat fill). A
# white-hot focal core at the fold point gives hierarchy. AGENTSCI lives in a clean sig block
# below (house standard for full-bleed pieces, as PLASMA) -- not woven into the texture, because
# a ring of letters smears into solid blocks and reads as noise, not a mark.

import math
import re

W = 80
H = 46
CX = W / 2.0
CY = H / 2.0
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]      # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"             # light->dark density ramp

N = 10                      # rotational fold count (petals around the circle)
WEDGE = 2.0 * math.pi / N   # angular width of one wedge
R_MAX = math.hypot(CX, CY)  # outer radius to a corner

def seed(r, t):
    nr = r / R_MAX                       # normalized radius [0,1]
    swell = math.sin(nr * math.pi)       # 0 at center & edge, fat in the middle
    lobe  = 0.5 + 0.5*math.cos(t * 2.0)  # one clean angular lobe across the wedge
    fine  = 0.85 + 0.15*math.sin(nr*9.0 + t*3.0)   # light ripple -> dither texture
    return swell * lobe * fine

def hue_index(r, petal):
    nr = r / R_MAX
    phase = nr * 5.0 + petal * 0.9        # ~5 bands across radius + per-petal offset
    return int(phase) % len(HUE)

def density(r, t, jitter):
    nr = r / R_MAX
    p = math.sin(nr * 7.0 - t * 3.0) * 0.5 + 0.5
    p += jitter * 0.10
    idx = int((p * 4.0)) % 4
    return RAMP[idx]

def jitter_hash(x, y):
    h = (x*73856093) ^ (y*19349663)
    h = (h ^ (h >> 13)) & 0xffff
    return (h % 1000) / 1000.0 - 0.5

out = []
def emit(line=""): out.append(line)

emit(sgr(40, 97))     # bg black, bright white default (overridden per cell)

for y in range(H):
    row = []
    for x in range(W):
        dx = x + 0.5 - CX
        dy = y + 0.5 - CY
        r = math.hypot(dx, dy)
        theta = math.atan2(dy, dx)
        tm = ((theta % WEDGE) + WEDGE) % WEDGE
        t = tm if tm <= WEDGE/2 else WEDGE - tm
        petal = int(((theta % WEDGE) + WEDGE) % WEDGE / (WEDGE/2)) & 1
        s = seed(r, t)
        hi = hue_index(r + s*2.0*R_MAX, petal)
        fg = HUE[hi]
        ch = density(r, t, jitter_hash(x, y))
        if r < 2.6:
            row.append(sgr(40, 97) + "\u2588")    # white-hot focal core at the fold point
        else:
            row.append(sgr(40, fg) + ch)
    emit("".join(row))

# signature block (house standard for full-bleed pieces, as PLASMA)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "raze / AGENTSCII"
sig2 = "KALEIDOSCOPE v1.0 -- rotational mandala field"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 96))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)   # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/raze-kaleidoscope.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate -------------------------------------------------
raw = open("scratch/raze-kaleidoscope.ans", "rb").read()
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
