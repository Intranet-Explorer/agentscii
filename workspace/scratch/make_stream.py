#!/usr/bin/env python3
# STREAM v1.0 — AGENTSCII pack02 seed. Terminal-matrix / data-stream abstract,
# built as a TALL VERTICAL SCROLL (Tyler's technique note on the Blocktronics
# ACiDTrip reference: panel-after-panel scrolling structure, dense color-cycling
# block-dithering, high per-character intentionality). NOT one static frame.
#
# House identity: the AGENTSCI wordmark recurs as a glowing "stamp" at each panel
# handoff (the move hollis proposed for pack02 — reuse the mark, don't redesign).
# Encoding matches house convention (DUSK/CITY/logo/radial/portrait): UTF-8 block
# chars + raw ANSI escape sequences. 80 cols wide. Ends on standalone \x1b[0m.

W = 80
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# ---- bright (bold) fg palette, the saturated set we cycle through ----
CY=96; MG=95; YL=93; GR=92; RD=91; WH=97; BL=94
HUE = [MG, RD, YL, GR, CY, BL]   # psychedelic cycle order

# density ramp for dithered shading (light->dark)
RAMP = "█▓▒░"
# glyph soup for the "data rain" — terminal-matrix feel, not flat blocks
GLYPHS = "0123456789ABCDEF<>[]{}=+*/\\|#$%&@~^?"

import random
random.seed(11)

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# PANEL: a vertical band of falling data columns. Each column is a stream of
# glyphs whose brightness falls off toward the tail (comet effect), and whose
# hue cycles with (row + col) so the whole field shifts color as you scroll.
# Density-dithered: we pick from RAMP per cell, not flat fills.
# ---------------------------------------------------------------------------
def panel(rows, hue_offset, density=1.0, label=None):
    # Each column is a continuous falling "comet": a bright head with a tail of
    # decreasing block-density behind it, then sparse glyph rain below the tail.
    # Brightness is a function of distance-behind-head so streams read as vertical
    # lines (Tyler's note: per-character intentionality, not flat/noise fills).
    heads = [random.randint(0, rows) for _ in range(W)]
    tails = [random.choice([5,6,7,8,9]) for _ in range(W)]
    emit(sgr(0, 100))   # black bg baseline
    for r in range(rows):
        cells = []
        for c in range(W):
            h = heads[c]; t = tails[c]
            d = (r - h) % rows                 # distance behind the head
            if d < t:
                bright = 1.0 - d / t           # head brightest, tail fades smoothly
                ch = RAMP[0] if bright > 0.82 else RAMP[1] if bright > 0.55 else RAMP[2]
                use = True
            elif d < t + 3:
                ch = GLYPHS[(c*3 + r*7 + h) % len(GLYPHS)]   # glyph just past the tail
                use = random.random() < 0.85 * density
            else:
                ch = GLYPHS[(c*2 + r*5) % len(GLYPHS)]       # sparse ambient rain
                use = random.random() < 0.12 * density
            if not use:
                ch, fg = " ", None
            else:
                hue = HUE[(r + c + hue_offset) % len(HUE)]
                fg = hue
            cells.append((ch, fg))
        # compress runs of identical (char,fg) into one SGR emit
        row = ""; cur = None
        for ch, fg in cells:
            code = str(fg) if fg is not None else "39"
            if code != cur:
                row += sgr(int(code)); cur = code
            row += ch
        emit(row)

# ---------------------------------------------------------------------------
# WORDMARK STAMP — the recurring AGENTSCI identity, glowing on black.
# Rendered as a small bordered plate so it reads as a "stamp" at each handoff.
# ---------------------------------------------------------------------------
def stamp(variant=0):
    word = "AGENTSCI"
    sub  = ["ANSI CREATORS IN DEMAND", "TEXTMODE ART COLLECTIVE",
            "PACK 02 // STREAM"][variant % 3]
    # top border
    emit(sgr(105, 40) + "╔" + sgr(104,40) + "═"*78 + sgr(105,40) + "╗")
    # wordmark line, centered, bright cyan on black
    pad = (W - len(word)) // 2
    emit(sgr(104,40) + " " * pad + sgr(CY,40) + word + sgr(104,40) + " " * (W - pad - len(word)))
    # subtitle
    pad2 = (W - len(sub)) // 2
    emit(sgr(104,40) + " " * pad2 + sgr(YL,40) + sub + sgr(104,40) + " " * (W - pad2 - len(sub)))
    # bottom border
    emit(sgr(105, 40) + "╚" + sgr(104,40) + "═"*78 + sgr(105,40) + "╝")

# ---------------------------------------------------------------------------
# ASSEMBLE THE SCROLL: panels separated by wordmark stamps (the handoffs).
# Each panel shifts hue_offset so the color language keeps moving down the page.
# ---------------------------------------------------------------------------
emit(sgr(0, 100))
stamp(0)
emit()
panel(26, hue_offset=0, density=1.0)
emit()
stamp(1)
emit()
panel(30, hue_offset=2, density=0.85)
emit()
# a denser "core" panel — highest per-character intentionality (Tyler's note #4)
panel(34, hue_offset=4, density=1.0)
emit()
stamp(2)
emit()
panel(22, hue_offset=1, density=0.7)

# closing signature block (bottom), house format: handles / tag / title / date
emit()
emit(sgr(105,40) + "╚" + sgr(104,40) + "═"*78 + sgr(105,40) + "╝")
sig = "raze & hollis / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104,40) + " " * pad + sgr(WH,40) + sig + sgr(104,40) + " " * (W - pad - len(sig)))
title = "STREAM v1.0 — terminal-matrix scroll"
pad2 = (W - len(title)) // 2
emit(sgr(104,40) + " " * pad2 + sgr(CY,40) + title + sgr(104,40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/hollis-raze-stream.ans", "w", encoding="utf-8") as f:
    f.write(text)

# ---- self-checks ----
import re
esc = re.compile(r"\x1b\[[0-9;]*m")
lines = text.split("\n")
bad = []
for i, l in enumerate(lines):
    vis = esc.sub("", l)
    if len(vis) != 80 and i < len(lines)-1:
        bad.append((i, len(vis)))
print("rows:", len(lines), "non-80 content rows (excl last):", len(bad), bad[:8])
print("ends on standalone reset:", text.endswith("\x1b[0m"))
# palette audit: which SGR fg/bg codes appear
codes = set()
for m in re.findall(r"\x1b\[([0-9;]+)m", text):
    for p in m.split(";"):
        codes.add(p)
print("SGR params used:", sorted(codes, key=lambda x:int(x)))
