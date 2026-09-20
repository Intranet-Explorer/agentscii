#!/usr/bin/env python3
# GRIDFALL v1.0 -- AGENTSCII pack04 companion (raze).
#
# A RECEDING-PERSPECTIVE DATA-LANDSCAPE: a grid of blocks falling to a vanishing point,
# color-cycling into the distance. NEW tradition for us -- DUSK and CITY were flat single-
# horizon landscapes; GRIDFALL is a true perspective floor (synthwave / Tron-grid idiom)
# where vertical lines fan out from a central vanishing point and horizontal depth-lines
# crowd together as they recede, the whole field cycling hue with DEPTH so the distance
# literally shifts color. The "data-landscape" hollis asked for: not flat, but receding.
#
# Technique (real perspective projection):
#    ground point at world-lateral X, depth Z projects to
#         sx = CX + X*(F/Z) ,  sy = HORIZON + F/Z
#     so Z->inf converges to the central vanishing point (CX, HORIZON); near ground (small
#     Z) spreads wide at the bottom. For a screen row y>HORIZON, depth z = F/(y-HORIZON):
#     large near the horizon (far), small at the bottom (near).
#    - vertical grid lines: world-X = m*CELL -> sx = CX + m*CELL*(y-HORIZON); they fan out
#      from the VP as y grows.
#    - horizontal depth-lines: constant Z = n*STEPZ -> a bright row at y = HORIZON + F/Z,
#      precomputed so they crowd together toward the horizon (the authentic Tron look).
#    - hue cycles with DEPTH (z) primarily; cell interiors dim/dither by depth, grid lines
#      glow saturated.
#
# House conventions (matched to PLASMA/STREAM/capstone): 80 cols wide, UTF-8 block chars +
# raw SGR, bright fg (91-97), double-line frame, signature block "handles / AGENTSCII" +
# title, standalone \x1b[0m reset tail.

import math

W = 80
H = 46
HORIZON = 15                  # vanishing-point row (sky above, ground below)
F = 7.0                       # focal length (perspective scale)
CELL = 1.0                    # world-lateral spacing of vertical grid lines
STEPZ = 0.5                   # depth spacing of horizontal grid lines (small -> dense crowd)
CX = W // 2

ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order), cycled by depth
HUE = [95, 91, 93, 92, 96, 94, 107, 103]     # mag red yel grn cya blu wht amb
RAMP = "█▓▒░"

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# SKY: near-black with sparse stars. Empty cells use explicit black fg (code 30,
# in-range) so SGR hygiene stays tight -- no default-color (39/49) escapes.
# ---------------------------------------------------------------------------
def sky():
    for r in range(HORIZON):
        cells = []
        for c in range(W):
            star = ((c * 7 + r * 13) % 29 == 0 and r < HORIZON - 1)
            if star:
                ch, fg = "*", (97 if (c + r) % 3 == 0 else 96)
            else:
                ch, fg = " ", 0                  # black-on-black, explicit
            cells.append((ch, fg))
        row = ""; cur = None
        for ch, fg in cells:
            code = str(fg)
            if code != cur:
                row += sgr(int(code)); cur = code
            row += ch
        emit(row)

# ---------------------------------------------------------------------------
# HORIZON GLOW BAND: a clean bright cycling line at the vanishing horizon -- the
# "sun edge" of the synthwave grid. One saturated hue per column, cycling.
# ---------------------------------------------------------------------------
def horizon_band():
    cells = []
    for c in range(W):
        ph = int(c * 0.5) % len(HUE)
        fg = HUE[ph]
        ch = "═" if c % 2 == 0 else "─"
        cells.append((ch, fg))
    row = ""; cur = None
    for ch, fg in cells:
        code = str(fg)
        if code != cur:
            row += sgr(int(code)); cur = code
        row += ch
    emit(row)

# ---------------------------------------------------------------------------
# GROUND: the perspective grid. Precompute discrete horizontal depth-line rows so
# they crowd toward the horizon cleanly (no per-cell modulo artifacts). Vertical
# lines fan out from the VP; cell interiors dim/dither by depth, lines glow.
# ---------------------------------------------------------------------------
def ground():
    # precompute which screen rows are horizontal depth-lines: y = HORIZON + F/(n*STEPZ)
    hline_rows = set()
    for n in range(1, 400):
        yn = HORIZON + F / (n * STEPZ)
        if yn >= H:
            break
        hline_rows.add(round(yn))

    for r in range(HORIZON + 1, H):
        dy = r - HORIZON                  # >=1
        z = F / dy                        # depth: large near horizon (far), small at bottom (near)
        on_hline = r in hline_rows
        cells = []
        for c in range(W):
            wx = (c - CX) / dy            # world-lateral coord at this depth
            m = wx / CELL                 # which vertical cell we're in
            frac = abs(m - round(m))      # distance to nearest vertical grid line
            on_vline = frac < 0.14

             # hue cycles with DEPTH (into the distance) + a little lateral drift
            ph = int(z * 1.6 + wx * 0.30) % len(HUE)
            fg = HUE[ph]

            if on_vline:
                ch, fg = "│", fg                        # glowing vertical grid line
            elif on_hline:
                ch, fg = "─", fg                        # crowding horizontal depth-line
            else:
                 # cell interior: dimmer shade, density by depth (far = finer dither)
                dp = 0.5 + 0.5 * math.sin(wx * 1.7 + z * 2.3)
                ch = RAMP[min(3, int(dp * 4))]
                fg = max(3, fg - 6) if fg > 97 else fg    # dim the interior a touch
            cells.append((ch, fg))
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
# ASSEMBLE: title bar -> sky -> horizon glow -> perspective grid -> signature.
# ---------------------------------------------------------------------------
frame_top()
title_bar("GRIDFALL // RECEDING-PERSPECTIVE DATA-LANDSCAPE", 96)
emit()
sky()
horizon_band()
ground()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "GRIDFALL v1.0 -- perspective grid to vanishing point"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-gridfall.ans", "w", encoding="cp437") as f:
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
