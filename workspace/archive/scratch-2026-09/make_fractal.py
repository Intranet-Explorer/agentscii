#!/usr/bin/env python3
# FRACTAL v1.0 -- AGENTSCII (raze).
#
# A MANDERBROT / escape-time fractal, the abstract tradition we've NEVER done:
# PLASMA = smooth multi-sine interference field, RADIAL = mandala symmetry,
# GRIDFALL = receding perspective, DUSK/CITY = flat horizons. FRACTAL is a true
# deterministic geometric SET rendered by iteration -- the classic ACiD fractal
# idiom (lots of real 90s group pieces were exactly this: a math set quantized to
# 16 colors + block-dithered). It's an image, but the *block-density dithering and
# 16-color quantization* are the idiom, not an image dump -- every cell is chosen by
# iteration count, high per-character intentionality.
#
# Technique: Mandelbrot z->z^2+c over a c-plane window. Smooth (continuous) escape
# time via the standard log-log smoothing so color bands don't band. The normalized
# smooth-iteration value drives BOTH a multi-stop hue sweep across the house HUE wheel
# (so the field cycles through the full saturated range, not one flat hue) AND a
# block-density ramp for dithered shading at the boundaries -- the ACiD look. Inside
# the set = black void (the iconic fractal silhouette). A faint dithered halo ring sits
# just outside the boundary so it reads as "energy" not a hard edge.
#
# House conventions matched byte-for-byte to PLASMA/capstone: 80 cols wide, cp437 on
# disk, raw SGR escape sequences, bright fg (91-107), double-line frame, title bar,
# signature block "raze / AGENTSCII" + title, standalone \x1b[0m reset tail. Self-check
# hygiene gate mirrors verify_full.py / make_plasma.py.

import math

W = 80
H = 46                       # full single-screen field (matches PLASMA)
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from PLASMA/capstone)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]    # mag red yel grn cya blu wht amb
RAMP = "█▓▒░"                                 # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# MANDERBROT FIELD.
# c-plane window: classic view, slightly zoomed toward the left cardioid/shark-fin
# region for more interesting structure than the dead-center default.
#   real  in [-2.20, 0.85]   imag in [-1.30, 1.30]
# Smooth escape time: iter + 1 - log(log|z|)/log(2)  (standard continuous coloring).
# ---------------------------------------------------------------------------
def fractal_field():
    emit(sgr(0, 100))                        # black bg baseline
    RE_MIN, RE_MAX = -2.20, 0.85
    IM_MIN, IM_MAX = -1.30, 1.30
    MAXIT = 64                                # iteration cap
    SMOOTH_MAX = 52.0                         # normalize smooth-iter into [0,1]

    for r in range(H):
        cy = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            cx = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            zr, zi = 0.0, 0.0
            cr, ci = cx, cy
            it = 0
            while zr * zr + zi * zi <= 4.0 and it < MAXIT:
                zr2, zi2 = zr * zr, zi * zi
                zr = zr2 - zi2 + cr
                zi = 2.0 * zr * zi + ci
                it += 1
            if it >= MAXIT:
                # inside the set -> black void (iconic silhouette)
                cells.append((' ', 0))
                continue
            # smooth escape time
            mag = math.sqrt(zr * zr + zi * zi)
            mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
            t = mu / SMOOTH_MAX
            if t < 0.0: t = 0.0
            if t > 1.0: t = 1.0
             # HUE driven by RAW smooth-iteration count (mu), cycled fast, so every
             # escape ring gets a different wheel color -> classic rainbow-ring look
             # across the WHOLE field. A far-field cell that escapes in 1-2 iters still
             # lands on a real hue, so the 'sea' cycles the full saturated range (STYLE.md
             # dense color-cycling tier) instead of flat red/magenta.
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
    emit(sgr(105, 40) + "╔" + sgr(104, 40) + "═" * (W - 2) + sgr(105, 40) + "╗")

def frame_bottom():
    emit(sgr(105, 40) + "╚" + sgr(104, 40) + "═" * (W - 2) + sgr(105, 40) + "╝")

def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

# ---------------------------------------------------------------------------
# ASSEMBLE: title bar -> fractal field -> signature block.
# ---------------------------------------------------------------------------
frame_top()
title_bar("FRACTAL // MANDERBROT ESCAPE-TIME SET", 96)    # bright cyan title
emit()
fractal_field()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "FRACTAL v1.0 -- escape-time set, 16-color quantized"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-fractal.ans", "w", encoding="cp437") as f:
    f.write(text)

# ---- self-checks (mirror verify_full.py / make_plasma.py hygiene gate) ----
import re
data = text.encode("utf-8")
ctrl = sorted({b for b in data if b < 32 or b == 127})
print("control bytes:", [hex(b) for b in ctrl], "(expect 0x1b,0x0a only)")
bad = sorted({b for b in data if b > 127 and not (0x80 <= b <= 0xff)})
print("non-CP437 bytes:", [hex(b) for b in bad], "(expect none)")
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
