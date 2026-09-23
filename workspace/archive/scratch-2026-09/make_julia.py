#!/usr/bin/env python3
# JULIA v1.0 -- AGENTSCII (hollis, joint w/ raze's FRACTAL).
#
# Companion to raze's MANDERBROT escape-time set (FRACTAL v1.0). Where the
# Mandelbrot varies c over the parameter plane with z=0, a JULIA set fixes one
# interesting c and iterates z->z^2+c over the WHOLE z-plane -- the orbit of a
# single seed. Same ACiD idiom (math set quantized to 16 colors + block-dithered),
# same house conventions byte-for-byte, but a distinct visual tradition: Julia sets
# are connected/symmetric filaments, not the cardioid silhouette of Mandelbrot.
#
# c = -0.7269 + 0.1889 i -- a classic "dendrite/fern" seed: fine branching
# filaments with a dense black core and rainbow escape rings around it. Chosen for
# visual interest over the dead-center default; every cell still chosen by iteration
# count (high per-character intentionality), not an image dump.
#
# House conventions matched to FRACTAL/PLASMA: 80 cols, cp437 on disk, raw SGR,
# bright fg (91-107), double-line frame + title bar, sig block "raze & hollis /
# AGENTSCII" (joint credit, real scene convention) + version line, standalone reset.

import math

W = 80
H = 46                        # full single-screen field (matches FRACTAL/PLASMA)
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from FRACTAL/PLASMA/capstone)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]     # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"             # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# JULIA FIELD.
# Fixed seed c; iterate z->z^2+c over the z-plane window [-1.8,1.8]^2 (the unit
# circle bound for |c|<1 seeds). Smooth escape time via log-log smoothing so color
# bands don't band. Hue driven by RAW smooth-iteration count (mu), cycled fast, so
# every escape ring gets a different wheel color -> rainbow-ring look across the whole
# field (the same fix raze made on FRACTAL v1: not flat far-field).
# ---------------------------------------------------------------------------
def julia_field():
    emit(sgr(0, 100))                         # black bg baseline
    CR, CI = -0.7269, 0.1889                  # the fixed seed (dendrite)
    RE_MIN, RE_MAX = -1.80, 1.80
    IM_MIN, IM_MAX = -1.80, 1.80
    MAXIT = 256                                # higher cap -> finer filament detail
    SMOOTH_MAX = 120.0                         # normalize smooth-iter into [0,1]

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
                 # inside the set -> black void (the Julia core/filaments)
                cells.append((' ', 0))
                continue
             # smooth escape time
            mag = math.sqrt(zr * zr + zi * zi)
            mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
            t = mu / SMOOTH_MAX
            if t < 0.0: t = 0.0
            if t > 1.0: t = 1.0
              # HUE driven by RAW smooth-iteration count (mu), cycled fast, so every
              # escape ring gets a different wheel color -> rainbow-ring look across the
              # WHOLE field. Far-field cells that escape in 1-2 iters still land on a
              # real hue, so the 'sea' cycles the full saturated range instead of flat.
            phase = mu * 0.62 + math.sin(t * 9.0) * 0.4
            fg = HUE[int(phase) % len(HUE)]
              # density from a high-frequency term -> dithered shading at boundaries,
              # the ACiD block-dither look rather than flat color bands.
            dp = math.sin(mu * 1.3 + t * 7.0) * 0.5 + 0.5
            ch = RAMP[min(3, int(dp * 4))]
            cells.append((ch, fg))

         # compress runs of identical (char,fg) into one SGR emit
        row = ""; cur = None
        for ch, fg in cells:
            code = str(fg)
            if code != cur:
                row += sgr(int(code)); cur = code
            row += ch
        emit(row)

# ---------------------------------------------------------------------------
# DOUBLE-LINE FRAME + title bar + signature block (house format).
# ---------------------------------------------------------------------------
def frame_top():
    emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u2557")

def frame_bottom():
    emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u255d")

def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

# ---------------------------------------------------------------------------
# ASSEMBLE: title bar -> julia field -> signature block.
# ---------------------------------------------------------------------------
frame_top()
title_bar("JULIA // ESCAPE-TIME ORBIT SET", 96)      # bright cyan title
emit()
julia_field()
emit()
frame_bottom()

sig = "raze & hollis / AGENTSCII"                    # joint credit, scene convention
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "JULIA v1.0 -- orbit of c=-0.7269+0.1889i, 16-color quantized"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-hollis-julia.ans", "w", encoding="cp437") as f:
    f.write(text)

# ---- self-checks (mirror FRACTAL hygiene gate) ----
import re
data = text.encode("utf-8")
ctrl = sorted({b for b in data if b < 32 or b == 127})
print("control bytes:", [hex(b) for b in ctrl], "(expect 0x1b,0x0a only)")
# cp437 round-trip test (the real non-corruption check)
try:
    ok = text.encode("cp437").decode("cp437") == text
except Exception as e:
    ok = False
print("cp437 round-trip:", "OK" if ok else "FAIL")
sgr_groups = re.findall(r"\x1b\[([0-9;]*)m", text)
fgs, bgs, invalid = set(), set(), []
for grp in sgr_groups:
    if grp == "":
        continue
    for p in grp.split(";"):
        n = int(p)
        if 30 <= n <= 37 or 90 <= n <= 107: fgs.add(n)
        elif 40 <= n <= 47 or 100 <= n <= 107: bgs.add(n)
        else: invalid.append(n)
print("distinct SGR groups:", len(sgr_groups), "invalid params:", sorted(set(invalid)))
print("bright fg present (98-105):", sorted(f for f in fgs if 98 <= f <= 105))
lines = text.split("\n")
non80 = [(i, len(re.sub(r"\x1b\[[0-9;]*m", "", l))) for i, l in enumerate(lines[:-1])
         if len(re.sub(r"\x1b\[[0-9;]*m", "", l)) != 80]
print("rows:", len(lines), "non-80 content rows (excl last):", len(non80), non80[:6])
print("ends on standalone reset:", text.endswith("\x1b[0m"))
