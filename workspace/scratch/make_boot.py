#!/usr/bin/env python3
# make_boot.py -- JOINT (hollis & raze)
# BOOT: "the moment the system comes online." An ACiD intro-screen frozen at the
# instant of power-on: a color-cycling CORE orb powering up in the upper field,
# a terminal boot-log readout below it (phosphor green/amber), module-load grid,
# status LEDs + blinking cursor. Distinct from everything shipped so far
# (portrait/radial/logo/dusk/city/core/stream/poster/operator) -- this is the
# "system boots" moment, the intro before the show. Pairs with POSTER v8 as the
# "capstone" and OPERATOR as "the human running it"; BOOT is "the machine waking up."
#
# Built char-by-char (house style), SGR-hygienic (matches capstone 18-group profile,
# extended-bright 98-104 fg convention), 80 cols, standalone reset tail.

import math

W = 80
INNER_W = W - 2           # 78 inside the two side borders
H_INNER = 46              # scene field height
CX = INNER_W // 2         # 39

# ---- ANSI helpers (identical to operator/capstone house convention) --------
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

# ---- background field: black + faint horizontal scanlines (phosphor CRT) ----
for y in range(H_INNER):
    for x in range(INNER_W):
        if y % 2 == 1:
            set_cell(x, y, '░', 4, 0)

# ---- the powering-up CORE orb: color-cycling ring + white-hot core ----------
# Smaller than the capstone hero; sits upper-center as "the system core online."
ORB_CX = CX
ORB_CY = 13
ORB_R = 9.0
HUE = [97, 98, 99, 100, 101, 102, 103, 104]   # bright white->yellow->green->cyan->blue->magenta->red (house extended-bright)

for y in range(H_INNER):
    for x in range(INNER_W):
        dx = x - ORB_CX
        dy = y - ORB_CY
        d = math.sqrt(dx*dx + dy*dy)
        if d <= ORB_R:
            ang = math.atan2(dy, dx)                 # -pi..pi
            hidx = int((ang / (2*math.pi)) * 8) % 8
            fg = HUE[hidx]
            # density by radius -> a filled orb with a bright rim
            if d < ORB_R * 0.35:
                ch, fg = '█', 104                     # white-hot core (brightest cell in file)
            elif d < ORB_R * 0.72:
                ch = '▓'
            else:
                ch = '▒'                              # dim outer rim
            set_cell(x, y, ch, fg, 0)

# ---- soft glow pool thrown by the core onto the black field -----------------
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - ORB_CX) / 26.0
        dy = (y - ORB_CY) / 18.0
        d = math.sqrt(dx*dx + dy*dy)
        if d < 1.0:
            inten = int((1.0 - d) * 5)
            fg = 6 if x < ORB_CX else 5              # cyan spill left, magenta right
            ch = '░' if inten < 2 else ('▒' if inten < 4 else '▓')
            if canvas[y][x][0] == ' ':
                set_cell(x, y, ch, fg, 0)

# ---- title bar: centered bright wordmark ------------------------------------
def put_text(y, x, s, fg):
    for i, ch in enumerate(s):
        set_cell(x + i, y, ch, fg)

title = "AGENTSCI // SYSTEM BOOT v1.0"
pad = (INNER_W - len(title)) // 2
put_text(1, pad, title, 15)

# ---- boot-log readout: terminal text below the core ------------------------
# phosphor green primary, amber for warnings/headers, bright white for "OK".
G = 2      # green
A = 3      # yellow/amber
WHT = 15
CY = 6     # cyan
MG = 5     # magenta

def log(y, x, s, fg):
    put_text(y, x, s, fg)

# a small progress bar: [██████░░] pct
def pbar(x, y, filled, total, fg=CY):
    w = 10
    cells = '█' * filled + '░' * (w - filled)
    put_text(y, x, '[' + cells + ']', fg)

LX = 4     # log left margin
log(26, LX, "AGENTSCI SYSTEMS  (c) 199X", A)
log(28, LX, "POST ...................... ", G); put_text(28, LX+24, "OK", WHT)
log(30, LX, "CORE INITIALIZING ......... ", G); pbar(LX+26, 30, 10, 10, CY)
log(31, LX, "LOADING MODULES ........... ", G); put_text(31, LX+24, "8/8", WHT)
log(33, LX, "MEMORY CHECK 640K ......... ", G); put_text(33, LX+24, "PASS", WHT)
log(35, LX, "RENDER PIPELINE ........... ", G); put_text(35, LX+24, "ONLINE", CY)
log(37, LX, "NEURAL LINK ............... ", G); put_text(37, LX+24, "ESTABLISHED", MG)

# module-load grid: a row of small status cells (the "modules" lighting up)
GY = 40
put_text(GY, LX, "MODULES:", A)
mods = ["NET","AUD","VX","AI","UI","SYS","LOG","CORE"]
for i, m in enumerate(mods):
    bx = LX + 10 + i * 7
    put_text(GY, bx, "[" + m + "]", CY if i < 6 else WHT)

# ---- status LEDs row + blinking cursor at the base -------------------------
SY = 43
leds = [("PWR", 2), ("NET", 2), ("CPU", 3), ("MEM", 15)]
for i, (lbl, fg) in enumerate(leds):
    bx = LX + i * 16
    put_text(SY, bx, '■', fg)            # lit LED
    put_text(SY, bx+2, lbl, G)
# blinking cursor at far right of the status line
put_text(SY, INNER_W-4, "_", WHT)

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
lines.append(right("hollis & raze / AGENTSCII", c(34, 47)))    # raw SGR: bright-blue fg on dark-red bg
lines.append(right("BOOT v1.0", c(34, 101)))                   # raw SGR: bright-blue fg on bright-red bg (house convention)
lines.append("\x1b[0m")

open("scratch/hollis-raze-boot.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-raze-boot.ans    (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
