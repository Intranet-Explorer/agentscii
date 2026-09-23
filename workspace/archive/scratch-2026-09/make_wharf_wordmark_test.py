#!/usr/bin/env python3
# hollis -- build a legible WHARF block-letter wordmark from a clean 5-row block font,
# render it standalone so I can verify it reads before committing to P0/P5.
from wharf_common import *

FONT = {
     "W": ["###   ###", "###   ###", "###   ###", " ## # ## ", "  ###   "],
     "H": ["#     #", "#     #", "#####", "#     #", "#     #"],
     "A": [" #####", "#     #", "#     #", "#######", "#     #"],
     "R": ["#####", "#    #", "#####", "#  ##", "#   #"],
     "F": ["#######", "#", "#", "####", "#"],
}

def wordmark(cells, text, y0, col, ch=BLK):
     # each letter 7 wide + 1 space gap; center the whole word
    rows = 5
    width = len(text) * 8 - 1
    x0 = (W - width) // 2
    for li, letter in enumerate(text):
        art = FONT[letter]
        for r in range(rows):
            for c, cell in enumerate(art[r]):
                if cell == "#":
                    put(cells, x0 + li * 8 + c, y0 + r, col, ch)

cells = new_canvas()
wordmark(cells, "WHARF", 14, Wt)
emit(cells, "wharf-wordmark-test.ans")
