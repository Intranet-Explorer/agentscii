#!/usr/bin/env python3
# hollis -- P0 TITLE CARD: opens the WHARF scroll like a real ACiD group piece.
# Big centered block-letter "WHARF" wordmark + AGENTSCII tag on flat black, restrained.
# A thin waterline echo low down ties it to every panel below so the title reads as the
# top of one continuous piece, not a separate screen. One amber accent stroke = the warm
# light source that moves through the cycle (dusk sun -> lamp -> dawn sun).
from wharf_common import *

cells = new_canvas()

# --- flat black field; a thin waterline echo at PIER so the title sits in the harbor ---
for x in range(W):
    put(cells, x, PIER, B, SH1)

# two dim stars -- high and sparse, not a band
put(cells, 60, 4, Wt, "*")
put(cells, 21, 7, C, "*")

def block_line(cells, y, text, col, ch=BLK):
    x0 = (W - len(text)) // 2
    for i, c in enumerate(text):
        if c != " ":
            put(cells, x0 + i, y, col, ch)

# AGENTSCII tag line: thin caps, cyan, centered -- above the big wordmark
block_line(cells, 9, "A G E N T S C I I", C, SH3)

# WHARF: the shared block-letter wordmark, white core with ONE amber accent stroke.
wordmark(cells, "WHARF", 14, Wt)
# amber accent on the leading stroke of the first letter (the warm light source)
x0 = (W - (len("WHARF") * 8 - 1)) // 2
put(cells, x0 + 1, 15, A, BLK)

# subtitle: the cycle this scroll walks through
block_line(cells, 23, "A HARBOR THROUGH THE NIGHT", C, SH1)

# a thin framed rule under the title (box-drawing, CP437), restrained
rule = "\u250c" + "\u2500" * (W - 2) + "\u2510"
for i, ch in enumerate(rule):
    put(cells, i, 26, B, ch)

# opening credit -- full contributor sequence lives at P5; here just tag + version.
block_line(cells, 33, "AGENTSCII / WHARF v1.x", C, SH2)
block_line(cells, 35, "hollis & raze / 1996", B, SH1)

emit(cells, "wharf-p0-title.ans")
