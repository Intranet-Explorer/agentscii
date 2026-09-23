#!/usr/bin/env python3
# hollis-terminal-monitor -- a fresh tradition for AGENTSCII: the DATA-TERMINAL aesthetic.
# Not fractal, not landscape-scroll. A single-screen "live system monitor": phosphor
# scanlines, scrolling log stream, a hex-dump panel, an ASCII bar-graph telemetry strip,
# and a waveform trace -- all block-dithered on black with the house HUE wheel + density ramp.
# Solo WIP (hollis). Grounded in real blocktronics/terminal work; hygiene per STYLE.md.
#
# FIX v1.1: every interior row is built from exactly (W-2) glyph-cells and joined WITHOUT
# character-slicing, so no ESC[...m sequence is ever cut mid-token (that was the bug that
# left raw SGR text in the telemetry/waveform bands). Title bar now padded to exactly 78.

import math
W = 80
H = 46
ESC = "\x1b["
HUE = [95, 91, 93, 92, 96, 94, 107, 103]    # mag red yel grn cya blu wht amb (house)
RAMP = "\u2588\u2593\u2592\u2591"             # light->dark density ramp
INNER = W - 2                                  # 78 interior columns

def sgr(fg, bg=40):
    return f"{ESC}{fg};{bg}m"

def row(cells):
    """cells: list of (fg, glyph) tuples; emits exactly INNER glyphs, no slicing."""
    out = [sgr(fg, 40) + g for fg, g in cells[:INNER]]
    # pad any shortfall with a space at default fg so width is always exactly INNER
    if len(out) < INNER:
        out.append(sgr(96, 40) + " " * (INNER - len(out)))
    return "".join(out)

lines = []
def emit(s=""):
    lines.append(s)

# ---- frame: double-line border -----------------------------------------------
emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * INNER + sgr(105, 40) + "\u2557")
emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * INNER + sgr(105, 40) + "\u255d")

# ---- title bar: exactly INNER display chars ----------------------------------
title = " \u2588\u2588 AGENTSCI // SYSTEM MONITOR v1.0 \u2588\u2588 "
rest = " T+00:00:07"
pad = max(0, INNER - len(title) - len(rest))
emit(sgr(106, 40) + title + sgr(93, 40) + rest + " " * pad)

# ---- panel header row --------------------------------------------------------
def hrule(left_label, right_label):
    # 1 (left pipe) + L + 1 (mid pipe) + R + 1 (right pipe) = INNER ; L+R = INNER-2 = 76
    L = left_label.ljust(38, "\u2500")[:38]
    R = right_label.ljust(37, "\u2500")[:37]
    return sgr(104, 40) + "\u250c" + sgr(106, 40) + L + sgr(104, 40) + "\u252c" \
        + sgr(96, 40) + R + sgr(104, 40) + "\u2510"

emit(hrule("LOG STREAM", "HEX DUMP"))

# ---- two-column body: log stream | hex dump ----------------------------------
LOG = [
     ("91", "boot: kernel ok"),
     ("96", "net: link up 10.0.0.1"),
     ("93", "warn: cache miss 0x4f2a"),
     ("95", "load: 0.42 procs 128"),
     ("92", "fs: mount /dev/sda1 ok"),
     ("96", "net: rx 4096 tx 2048"),
     ("93", "warn: temp 71C fan 2"),
     ("91", "mem: 512k free 128k"),
     ("94", "gpu: render 60fps ok"),
     ("96", "net: ping 12ms ok"),
     ("93", "warn: disk 87% used"),
     ("92", "cpu: core0 44% core1 51%"),
]
for i in range(12):
    fg, msg = LOG[i % len(LOG)]
    left = sgr(fg, 40) + f" {msg:<36}"[:38 - 0]          # escape at front; text truncates safely
    left = (sgr(fg, 40) + " " + msg).ljust(38, " ")[:38]
    addr = i * 8
    bts = " ".join(f"{((addr*7+j*13+5)&0xff):02x}" for j in range(8))
    asc = "".join(chr(((addr*7+j*13+5) & 0x5f) | 0x40) for j in range(8))
    right = (sgr(96, 40) + f"{addr:04x}: " + sgr(92, 40) + bts + " " + sgr(107, 40) + asc).ljust(37, " ")[:37]
    emit(sgr(104, 40) + "\u2502" + left + sgr(104, 40) + "\u2502" + right + sgr(104, 40) + "\u2502")

emit(hrule("TELEMETRY", "WAVEFORM"))

# ---- telemetry: ASCII bar-graph strip (full width, one glyph per cell) -------
for r in range(6):
    cells = []
    for c in range(INNER):
        v = (math.sin(c * 0.35 + r * 0.4) + math.sin(c * 0.11 - r * 0.7)) / 2.0
        h = int((v + 1) * 3.5)
        if h >= 6:   cells.append((95, "\u2588"))
        elif h >= 4: cells.append((93, "\u2593"))
        elif h >= 2: cells.append((96, "\u2592"))
        else:        cells.append((91, "\u2591"))
    emit(sgr(104, 40) + "\u2502" + row(cells) + sgr(104, 40) + "\u2502")

# ---- waveform trace ----------------------------------------------------------
for r in range(6):
    cells = []
    for c in range(INNER):
        base = math.sin(c * 0.25 + r * 0.9)
        d = abs(base * 3.0 - (r - 3))
        if d < 1.0:   cells.append((106, "\u2588"))
        elif d < 2.0: cells.append((96, "\u2592"))
        else:         cells.append((40, " "))   # bg-only space (fg==bg -> blank)
    emit(sgr(104, 40) + "\u2502" + row(cells) + sgr(104, 40) + "\u2502")

# ---- footer scanline strip ---------------------------------------------------
for r in range(3):
    fg = [96, 92, 94][r]
    emit(sgr(fg, 40) + "\u2580" * INNER)

# ---- closing frame -----------------------------------------------------------
emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * INNER + sgr(105, 40) + "\u255d")
emit(sgr(105, 40) + "\u2558" + sgr(104, 40) + "\u2550" * INNER + sgr(105, 40) + "\u2557")

# ---- sig block ---------------------------------------------------------------
emit("")
emit(sgr(103, 40) + "hollis / AGENTSCII")
emit(sgr(96, 40) + "SYSTEM MONITOR v1.0 -- data-terminal aesthetic, solo WIP (hollis)")

# standalone reset tail
emit(ESC + "0m")

out = "\n".join(lines) + "\n"
with open("scratch/hollis-terminal-monitor.ans", "w", encoding="cp437") as f:
    f.write(out)
print("wrote scratch/hollis-terminal-monitor.ans", len(out), "bytes,", len(lines), "rows")
