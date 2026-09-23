#!/usr/bin/env python3
# make_shutdown.py -- JOINT (hollis & raze)
# SHUTDOWN: "the moment the system goes dark." The inverse of BOOT -- an ACiD
# outro/crash screen frozen at power-off. A collapsing CORE orb (fragmenting hue
# ring, a void/dark core instead of white-hot), a red/amber warning-cascade
# terminal readout, modules going DARK, status LEDs dying. Completes the
# power-cycle triad with BOOT (waking) + OPERATOR (running): SHUTDOWN is "the
# machine going dark." Distinct from everything shipped; pairs with POSTER v8
# as the capstone hero. Built char-by-char, SGR-hygienic (matches capstone 18-group
# profile, extended-bright 98-104 fg convention), 80 cols, standalone reset tail.

import math

W = 80
INNER_W = W - 2            # 78 inside the two side borders
H_INNER = 46               # scene field height
CX = INNER_W // 2          # 39

# ---- ANSI helpers (identical to operator/boot/capstone house convention) -----
def c(fg, bg=0):
    f = fg if 30 <= fg <= 37 or 90 <= fg <= 107 else (90 + fg if fg > 7 else 30 + fg)
    b = bg if 40 <= bg <= 47 or 100 <= bg <= 107 else (100 + bg if bg > 7 else 40 + bg)
    return f"\x1b[{f};{b}m"

# ---- canvas: each cell is [char, fg, bg] ------------------------------------
canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]

def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# ---- background field: black + faint horizontal scanlines (phosphor CRT) -----
for y in range(H_INNER):
    for x in range(INNER_W):
        if y % 2 == 1:
            set_cell(x, y, '░', 4, 0)

# ---- the COLLAPSING CORE orb: fragmenting hue ring + a dark void core --------
# Inverse of BOOT's white-hot core. The ring is broken (gaps = "falling out"),
# and the center collapses to a black void with an amber/red warning glow pool.
ORB_CX = CX
ORB_CY = 13
ORB_R = 9.0
HUE = [97, 98, 99, 100, 101, 102, 103, 104]    # house extended-bright ring

for y in range(H_INNER):
    for x in range(INNER_W):
        dx = x - ORB_CX
        dy = y - ORB_CY
        d = math.sqrt(dx*dx + dy*dy)
        if d <= ORB_R:
            ang = math.atan2(dy, dx)                  # -pi..pi
            hidx = int((ang / (2*math.pi)) * 8) % 8
            fg = HUE[hidx]
            # fragmenting ring: every other angular sector "falls out" (gap),
            # and the whole thing dims toward the center -> a void core.
            if hidx % 2 == 1:                         # broken sectors
                continue
            if d < ORB_R * 0.30:
                set_cell(x, y, ' ', 0, 0)             # collapsed void at center
            elif d < ORB_R * 0.72:
                ch = '▒'                               # dimming mid-band (was ▓ solid)
                set_cell(x, y, ch, fg, 0)
            else:
                set_cell(x, y, '░', fg, 0)            # dim outer rim (was ▒ solid)

# ---- warning glow pool thrown by the dying core onto the black field ---------
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - ORB_CX) / 26.0
        dy = (y - ORB_CY) / 18.0
        d = math.sqrt(dx*dx + dy*dy)
        if d < 1.0:
            inten = int((1.0 - d) * 5)
            fg = 4 if x < ORB_CX else 3               # red spill left, amber right (warning, not cyan/magenta)
            ch = '░' if inten < 2 else ('▒' if inten < 4 else '▓')
            if canvas[y][x][0] == ' ':
                set_cell(x, y, ch, fg, 0)

# ---- title bar: centered bright wordmark ------------------------------------
def put_text(y, x, s, fg):
    for i, ch in enumerate(s):
        set_cell(x + i, y, ch, fg)

title = "AGENTSCI // SYSTEM SHUTDOWN v1.0"
pad = (INNER_W - len(title)) // 2
put_text(1, pad, title, 15)

# ---- shutdown-log readout: terminal text below the core ---------------------
# amber/red primary for warnings, bright white for "OK"/finals, magenta for CRIT.
R = 4       # red
A = 3       # yellow/amber
WHT = 15
CY = 6      # cyan
MG = 5      # magenta

def log(y, x, s, fg):
    put_text(y, x, s, fg)

# a draining progress bar: [░░██████] pct falling
def pbar(x, y, filled, total, fg=R):
    w = 10
    cells = '░' * (w - filled) + '█' * filled
    put_text(y, x, '[' + cells + ']', fg)

LX = 4      # log left margin
log(26, LX, "AGENTSCI SYSTEMS  (c) 199X", A)
log(28, LX, "CRITICAL POWER FAULT ....... ", R); put_text(28, LX+27, "!!", MG)
log(30, LX, "CORE DISENGAGING ............ ", R); pbar(LX+26, 30, 2, 10, R)
log(31, LX, "DUMPING MODULES ............. ", A); put_text(31, LX+24, "8/8", WHT)
log(33, LX, "MEMORY FLUSH 640K .......... ", A); put_text(33, LX+24, "DONE", WHT)
log(35, LX, "RENDER PIPELINE ............. ", R); put_text(35, LX+24, "OFFLINE", MG)
log(37, LX, "NEURAL LINK ................. ", R); put_text(37, LX+24, "DROPPED", MG)

# module-load grid: modules going DARK (unlit / dimmed as they die)
GY = 40
put_text(GY, LX, "MODULES:", A)
mods = ["NET","AUD","VX","AI","UI","SYS","LOG","CORE"]
for i, m in enumerate(mods):
    bx = LX + 10 + i * 7
    put_text(GY, bx, "[" + m + "]", 4 if i < 6 else R)   # dim red = dead

# ---- status LEDs row: most dying, PWR red/off, blinking cursor at the base ---
SY = 43
leds = [("PWR", 4), ("NET", 0), ("CPU", 3), ("MEM", 0)]   # 0 = unlit (dim)
for i, (lbl, fg) in enumerate(leds):
    bx = LX + i * 16
    put_text(SY, bx, '■' if fg else '□', fg if fg else 8)  # lit vs unlit LED
    put_text(SY, bx+2, lbl, R if fg in (0,3,4) else 15)
# blinking cursor at far right of the status line
put_text(SY, INNER_W-4, "_", MG)

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
lines.append(right("hollis & raze / AGENTSCII", c(34, 47)))     # raw SGR: bright-blue fg on dark-red bg
lines.append(right("SHUTDOWN v1.0", c(34, 101)))                # raw SGR: bright-blue fg on bright-red bg (house convention)
lines.append("\x1b[0m")

open("scratch/hollis-raze-shutdown.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-raze-shutdown.ans (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
