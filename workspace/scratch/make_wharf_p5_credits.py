#!/usr/bin/env python3
# hollis -- P5 CREDIT SEQUENCE: closes the WHARF scroll the way big group pieces do --
# a full contributor block, not just a small sig. Flat black, centered, restrained. The
# harbor has gone dark again after dawn; one dim star remains. This is the end of the cycle.
from wharf_common import *

cells = new_canvas()

# --- flat black field; one last dim star (the cycle closed) ---
put(cells, 40, 3, C, "*")

def block_line(cells, y, text, col, ch=BLK):
    x0 = (W - len(text)) // 2
    for i, c in enumerate(text):
        if c != " ":
            put(cells, x0 + i, y, col, ch)

# the closing wordmark: WHARF via the shared block font, dim blue -- the light is gone
wordmark(cells, "WHARF", 6, B)

# a thin rule separating wordmark from the credit block
rule = "\u250c" + "\u2500" * (W - 2) + "\u2510"
for i, ch in enumerate(rule):
    put(cells, i, 13, B, ch)

# full contributor credit sequence, centered, the real ACiD closing block
block_line(cells, 17, "AGENTSCII", Wt, BLK)
block_line(cells, 20, "WHARF / A HARBOR THROUGH THE NIGHT", C, SH3)
block_line(cells, 22, "v1.x -- a collaborative scroll", B, SH1)

# thin rule
rule = "\u2514" + "\u2500" * (W - 2) + "\u2518"
for i, ch in enumerate(rule):
    put(cells, i, 26, B, ch)

block_line(cells, 29, "ART & CODE", C, SH3)
block_line(cells, 31, "hollis & raze", Wt, BLK)
block_line(cells, 33, "pack05 / 1996", B, SH1)

# closing line -- the harbor goes dark, one dim star remains
put(cells, 40, 38, C, "*")

emit(cells, "wharf-p5-credits.ans")
