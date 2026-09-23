#!/usr/bin/env python3
# make_operator.py -- JOINT (hollis & raze)
# OPERATOR: the PORTRAIT tradition, but as "the person running CORE" -- a back-view
# operator hunched at a glowing CRT whose screen shows the dense color-cycling CORE orb
# (echoes pack02 core + the capstone's hero). Distinct from pack01's frontal symmetric
# masked bust: this is figure-IN-environment with narrative light spill, depth via the
# head occluding the lower orb, and a console/keyboard at the base.
#
# Built char-by-char (house style), SGR-hygienic, 80 cols, standalone reset tail.

import math

W = 80
INNER_W = W - 2          # 78 inside the two side borders
H_INNER = 46             # scene field height
CX = INNER_W // 2        # 39

# ---- ANSI helpers -----------------------------------------------------------
def c(fg, bg=0):
    """fg,bg: 0-7 normal, 8-15 bright. Raw SGR passthrough so 97/104 land as written;
    a value already in the 30-37 / 90-107 range is emitted verbatim (house convention, v8)."""
    f = fg if 30 <= fg <= 37 or 90 <= fg <= 107 else (90 + fg if fg > 7 else 30 + fg)
    b = bg if 40 <= bg <= 47 or 100 <= bg <= 107 else (100 + bg if bg > 7 else 40 + bg)
    return f"\x1b[{f};{b}m"

# ---- canvas: each cell is [char, fg, bg] ------------------------------------
canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]

def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# ---- background field: black control room + faint horizontal scanlines ------
for y in range(H_INNER):
    for x in range(INNER_W):
        # dim scanline every other row, very low density so it reads as texture not fill
        if y % 2 == 1:
            set_cell(x, y, '░', 4, 0)

# ---- soft glow pool on the "wall" behind/around the screen ------------------
# The CRT throws light onto the room. A wide, dim cyan/magenta halo centered on the screen.
SCR_CX = CX
SCR_CY = 12
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - SCR_CX) / 30.0
        dy = (y - SCR_CY) / 22.0
        d = math.sqrt(dx*dx + dy*dy)
        if d < 1.0:
            inten = int((1.0 - d) * 5)
            # left half of the pool leans cyan, right half magenta (ambient spill)
            fg = 6 if x < SCR_CX else 5
            ch = '░' if inten < 2 else ('▒' if inten < 4 else '▓')
            if canvas[y][x][0] == ' ':
                set_cell(x, y, ch, fg, 0)

# ---- the CRT screen: rounded box frame + dense color-cycling CORE orb -------
SCR_X0, SCR_X1 = 23, 56        # screen interior x-range (inside frame)
SCR_Y0, SCR_Y1 = 4, 23         # screen interior y-range
# frame (bright cyan double-ish border around the screen)
for x in range(SCR_X0 - 1, SCR_X1 + 2):
    set_cell(x, SCR_Y0 - 1, '═', 6, 0)
    set_cell(x, SCR_Y1 + 1, '═', 6, 0)
for y in range(SCR_Y0 - 1, SCR_Y1 + 2):
    set_cell(SCR_X0 - 1, y, '║', 6, 0)
    set_cell(SCR_X1 + 1, y, '║', 6, 0)
# corners
for (cx, cy) in [(SCR_X0-1, SCR_Y0-1), (SCR_X1+1, SCR_Y0-1),
                 (SCR_X0-1, SCR_Y1+1), (SCR_X1+1, SCR_Y1+1)]:
    set_cell(cx, cy, '╬', 6, 0)

# the orb inside the screen: dense color-cycling field (the CORE motif).
# Hue wheel sweeps the full bright range; a white-hot core leads by luminance.
ORB_CX = (SCR_X0 + SCR_X1) / 2.0
ORB_CY = (SCR_Y0 + SCR_Y1) / 2.0
HUE = [97, 98, 99, 100, 101, 102, 103, 104]   # bright white->yellow->green->cyan->blue->magenta->red
for y in range(SCR_Y0, SCR_Y1 + 1):
    for x in range(SCR_X0, SCR_X1 + 1):
        dx = (x - ORB_CX) / 14.0
        dy = (y - ORB_CY) / 9.0
        r = math.sqrt(dx*dx + dy*dy)
        if r > 1.0:
            continue   # outside the orb -> black screen background
        ang = math.atan2(dy, dx)
        # diagonal phase so the field visibly cycles, not a static gradient
        phase = (x * 0.35 + y * 0.55 + ang * 1.6)
        hidx = int(phase) % len(HUE)
        fg = HUE[hidx]
        # density dithers the transition between hue bands
        frac = abs((phase % 1.0) - 0.5) * 2.0
        ch = '█' if frac < 0.34 else ('▓' if frac < 0.67 else '▒')
        # white-hot core: brightest cell in the whole file, leads the eye
        if r < 0.28:
            set_cell(x, y, '█', 15, 0)
        elif r < 0.46:
            set_cell(x, y, ch, 104, 0)   # bright cyan halo ring
        else:
            set_cell(x, y, ch, fg, 0)

# scanlines over the orb (CRT feel): dim every other row slightly darkens it
for y in range(SCR_Y0, SCR_Y1 + 1, 2):
    for x in range(SCR_X0, SCR_X1 + 1):
        cell = canvas[y][x]
        if cell[0] != ' ':
            # nudge density down one step on scanline rows for a flicker feel
            if cell[0] == '█':
                set_cell(x, y, '▓', cell[1], 0)

# ---- the operator: back of head + shoulders, seated, in FRONT of the screen -
# The head occludes the lower-center of the orb -> depth. Lit by the screen glow.
HEAD_CY = 27.0
HEAD_RY = 5.5
HEAD_RX = 8.5

def head_halfwidth(y):
    t = (y - HEAD_CY) / HEAD_RY
    if abs(t) > 1.0:
        return None
    return HEAD_RX * math.sqrt(1.0 - t*t)

# light source: the screen, up and slightly left of the head
LX, LY = ORB_CX - 4, SCR_CY
LMAX = 26.0
def light_at(x, y):
    dx = x - LX
    dy = y - LY
    d = math.sqrt(dx*dx + dy*dy) / LMAX
    return max(0.0, min(1.0, 1.0 - d))

# head (dark silhouette catching screen light as a rim on the upper-left)
for y in range(H_INNER):
    hw = head_halfwidth(y)
    if hw is None:
        continue
    lo = int(round(CX - hw))
    hi = int(round(CX + hw))
    for x in range(lo, hi + 1):
        L = light_at(x, y)
        if L > 0.82:
            ch, fg = '▓', 6          # bright cyan screen-light on the lit edge
        elif L > 0.66:
            ch, fg = '▒', 4
        else:
            ch, fg = '░', 3          # dark back of head in shadow
        set_cell(x, y, ch, fg, 0)

# neck
for y in range(32, 35):
    for x in range(CX - 3, CX + 4):
        L = light_at(x, y)
        set_cell(x, y, '▒' if L > 0.6 else '░', 4 if L > 0.6 else 3, 0)

# shoulders / torso: widening trapezoid, screen-light gradient (cyan left -> magenta right)
TORSO_TOP = 35
for y in range(TORSO_TOP, H_INNER - 3):
    t = (y - TORSO_TOP) / max(1, H_INNER - 3 - TORSO_TOP)
    hw = 7.0 + t * 26.0
    lo = int(round(CX - hw))
    hi = int(round(CX + hw))
    for x in range(lo, hi + 1):
        L = light_at(x, y)
        # screen light spills: left side cyan, right side magenta (asymmetric ambient)
        if x < CX:
            base = 6      # cyan
        else:
            base = 5      # magenta
        if L > 0.78:
            ch, fg = '█', min(14, base + 2)
        elif L > 0.55:
            ch, fg = '▓', base
        else:
            ch, fg = '▒', max(3, base - 2)
        set_cell(x, y, ch, fg, 0)

# ---- console / desk at the base --------------------------------------------
DESK_Y = H_INNER - 4
for x in range(INNER_W):
    set_cell(x, DESK_Y, '═', 7, 0)
    set_cell(x, DESK_Y + 1, '▒', 8, 0)   # desk surface, lit

# keyboard: a row of small key blocks on the desk
for x in range(20, INNER_W - 20):
    if x % 3 == 0:
        set_cell(x, DESK_Y + 2, '█', 6, 0)
    else:
        set_cell(x, DESK_Y + 2, '▒', 4, 0)

# status LEDs (blinking indicators) on the right of the desk
for i, col in enumerate([10, 12, 13, 11]):
    set_cell(INNER_W - 18 + i * 3, DESK_Y + 2, '█', col, 0)

# a blinking cursor on the left of the desk (the operator is mid-command)
set_cell(16, DESK_Y + 2, '█', 14, 0)
set_cell(17, DESK_Y + 2, '▒', 14, 0)

# ---- title bar at top -------------------------------------------------------
title = "OPERATOR // RUNNING CORE"
# center it on a dim band
ty = 1
for x in range(INNER_W):
    set_cell(x, ty, ' ', 0, 0)
pad = (INNER_W - len(title)) // 2
for i, ch in enumerate(title):
    set_cell(pad + i, ty, ch, 15, 0)

# ---- render to ANSI ---------------------------------------------------------
def render_row(cells):
    out = []
    cur_fg, cur_bg = None, None
    for ch, fg, bg in cells:
        if (fg, bg) != (cur_fg, cur_bg):
            out.append(c(fg, bg))
            cur_fg, cur_bg = fg, bg
        out.append(ch)
    return "".join(out)

lines = []
# top border (double-line house bar)
lines.append(c(15, 0) + "╔" + c(14, 0) + "═" * INNER_W + c(15, 0) + "╗")
for y in range(H_INNER):
    row = list(canvas[y])
    if row[0][0] == ' ':
        row[0] = ['░', 14, 0]
    if row[-1][0] == ' ':
        row[-1] = ['░', 14, 0]
    lines.append(c(15, 0) + "║" + c(0, 0) + render_row(row) + c(15, 0) + "║")
lines.append(c(15, 0) + "╚" + c(14, 0) + "═" * INNER_W + c(15, 0) + "╝")

# signature block: bottom-right, two colored lines + standalone reset (house tail).
def right(plain, sgr, width=W):
    return " " * (width - len(plain)) + sgr + plain
lines.append(right("hollis & raze / AGENTSCII", c(34, 47)))   # raw SGR: bright-blue fg on dark-red bg
lines.append(right("OPERATOR v1.0", c(34, 101)))   # raw SGR: bright-blue fg on bright-red bg (house convention)
lines.append("\x1b[0m")

open("scratch/hollis-raze-operator.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-raze-operator.ans   (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
