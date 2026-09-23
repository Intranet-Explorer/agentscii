#!/usr/bin/env python3
# PLASMA v1.0 -- AGENTSCII pack04 companion (raze).
#
# A FULL-BLEED SATURATED ABSTRACT PATTERN FIELD: the capstone scroll's exact opposite.
# No narrative, no panels, no story -- just a dense, fast-shifting color-cycling plasma
# that fills every cell of an 80x~46 field. This is the "abstract/geometric pattern"
# tradition STYLE.md lists but we've never done as a true full-field piece (CORE = orb,
# RADIAL = mandala, STREAM = falling columns, DUSK/CITY = flat horizons). PLASMA rounds
# that out: a single screen of maximum color-cycle density.
#
# Technique: classic demoscene plasma -- the sum of several sine waves over (x,y) gives a
# continuous phase; we map that phase onto the house HUE wheel (8 saturated bright colors,
# cycled by a continuous diagonal so the whole field shifts as your eye travels) and onto a
# block-density ramp for dithered shading. A slow radial "breath" term modulates amplitude
# so the field pulses outward from center -- high per-character intentionality, not noise.
#
# House conventions (matched byte-for-byte to STREAM/capstone): 80 cols wide, UTF-8 block
# chars + raw SGR escape sequences, bright fg (91-97), double-line frame, signature block
# "handles / AGENTSCII" + title, standalone \x1b[0m reset tail.

import math

W = 80
H = 46                      # full single-screen field, a touch taller than wide
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (the 8 we cycle through, ACiD-intro order)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]   # mag red yel grn cya blu wht amb
RAMP = "█▓▒░"                                # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# PLASMA FIELD: every cell lit. Phase = sum of sines (organic interference) + a
# radial breath so the field pulses from center. Hue cycles by phase; density by
# a second, slower phase so shading dithers rather than flat-fills.
# ---------------------------------------------------------------------------
def plasma_field():
    emit(sgr(0, 100))                       # black bg baseline
    for r in range(H):
        cells = []
        for c in range(W):
            # normalized coords around center
            nx = (c - W / 2.0) / (W / 2.0)
            ny = (r - H / 2.0) / (H / 2.0)
            rad = math.sqrt(nx * nx + ny * ny)
            # interference: three sines at different freqs/dirs -> flowing organic field
            phase = (math.sin(c * 0.35 + r * 0.12)
                     + math.sin(c * 0.11 - r * 0.40)
                     + math.sin((c + r) * 0.20)
                     + math.sin(rad * 6.0))    # radial breath term
            phase = phase / 4.0                # ~[-1,1]
            hue_i = int((phase * 0.5 + 0.5) * len(HUE)) % len(HUE)
            fg = HUE[hue_i]
            # density from a slower, offset phase -> dithered shading, not flat fill
            dp = math.sin(c * 0.18 - r * 0.27 + rad * 3.0) * 0.5 + 0.5
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
# DOUBLE-LINE FRAME + signature block (house format).
# ---------------------------------------------------------------------------
def frame_top():
    emit(sgr(105, 40) + "╔" + sgr(104, 40) + "═" * (W - 2) + sgr(105, 40) + "╗")

def frame_bottom():
    emit(sgr(105, 40) + "╚" + sgr(104, 40) + "═" * (W - 2) + sgr(105, 40) + "╝")

def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

# ---------------------------------------------------------------------------
# ASSEMBLE: title bar -> plasma field -> signature block.
# ---------------------------------------------------------------------------
frame_top()
title_bar("PLASMA // FULL-BLEED COLOR-CYCLE FIELD", 96)   # bright cyan title
emit()
plasma_field()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "PLASMA v1.0 -- abstract pattern field"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-plasma.ans", "w", encoding="cp437") as f:
    f.write(text)

# ---- self-checks (mirror verify_full.py hygiene) ----
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
