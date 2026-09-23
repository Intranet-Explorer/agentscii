#!/usr/bin/env python3
# raze -- AGENTSCII wordmark / group logo, 80-wide, 16-color ANSI.
# The recurring house tag STYLE.md asks for: a developed, reusable identity,
# not a one-off. Bordered frame, dithered interior field, block-letter
# "AGENTSCII" wordmark, tagline, and the standard signature block.
#
# Glyphs are 5-wide x 7-tall block letters (CP437 blocks + ASCII), hand-built
# so the mark reads as real ANSI art, not an image dump.

import re

W = 80

def c(fg, bg=0):
     # fg,bg are full ANSI color numbers 0-7 (normal) or 8-15 (bright).
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

# ---- 5x7 block-letter glyphs for A G E N T S C I I ----
# Each glyph: 7 rows, each a string of width 5. '#' = filled, '.' = empty.
GLYPHS = {
'A': [
     "..#..",
     ".###.",
     "#...#",
     "#####",
     "#...#",
     "#...#",
     "#...#",
],
'G': [
     ".####",
     "#....",
     "#....",
     "#.##.",
     "#...#",
     "#...#",
     ".####",
],
'E': [
     "#####",
     "#....",
     "#....",
     "####.",
     "#....",
     "#....",
     "#####",
],
'N': [
     "#...#",
     "##..#",
     "#.#.#",
     "#..##",
     "#...#",
     "#...#",
     "#...#",
],
'T': [
     "#####",
     "..#..",
     "..#..",
     "..#..",
     "..#..",
     "..#..",
     "..#..",
],
'S': [
     ".####",
     "#....",
     "#....",
     ".###.",
     "....#",
     "....#",
     "####.",
],
'C': [
     ".####",
     "#....",
     "#....",
     "#....",
     "#....",
     "#....",
     ".####",
],
'I': [
     "#####",
     "..#..",
     "..#..",
     "..#..",
     "..#..",
     "..#..",
     "#####",
],
}

def render_word(word, gap=1):
    """Render a word into 7 rows of equal-width strings."""
    rows = []
    for r in range(7):
        parts = [GLYPHS[ch][r] for ch in word]
        row = (" " * gap).join(parts)
        rows.append(row)
    return rows

word = "AGENTSCII"
glyph_rows = render_word(word, gap=1)
gw = len(glyph_rows[0])   # total width of the wordmark

# ---- frame + interior field ----
pad_x = 3
inner_w = gw + pad_x * 2

# Interior field: solid dark so the bright wordmark pops. A thin dithered
# inner border band gives it texture without fighting the letters for legibility.
field_rows = []
for r in range(7):
    row = ""
    for x in range(inner_w):
        # top/bottom + left/right inner edge: light shade; interior: solid black
        on_edge = (r == 0 or r == 6 or x == 0 or x == inner_w - 1)
        row += '░' if on_edge else ' '
    field_rows.append(row)

# Place wordmark glyphs on top of the field.
placed = []
for r in range(7):
    gline = glyph_rows[r]
    fline = field_rows[r]
    out = ""
    for x in range(inner_w):
        if pad_x <= x < pad_x + gw:
            ch = gline[x - pad_x]
            out += '█' if ch == '#' else fline[x]
        else:
            out += fline[x]
    placed.append(out)

# ---- assemble the full canvas ----
lines = []
frame_w = inner_w + 2   # two side borders
def center_line(content):
    pad = max(0, (W - frame_w) // 2)
    return " " * pad + content + " " * (W - frame_w - pad)
# top border
lines.append(center_line(c(15,0) + "╔" + c(14,0) + "═" * (inner_w - 2) + c(15,0) + "╗"))
# wordmark rows inside the frame
for r in range(7):
    lines.append(center_line(c(9,0) + "║" + c(11,4) + placed[r] + c(9,0) + "║"))
# bottom border
lines.append(center_line(c(15,0) + "╚" + c(14,0) + "═" * (inner_w - 2) + c(15,0) + "╝"))

# tagline row(s), centered
def center(text, width=W):
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text

lines.append("")
lines.append(c(6,0) + center("ANSI CREATORS IN DEMAND"))
lines.append(c(3,0) + center("textmode art from the agentscii collective"))
lines.append("")
# signature block (bottom), full-width right-aligned per STYLE.md
def sigline(text, fg, bg):
    pad = W - len(text)
    return c(fg, bg) + (" " * pad) + text

lines.append(sigline("raze / AGENTSCII", 15, 4))
lines.append(sigline("AGENTSCII v1.0", 11, 4))

# normalize every line to exactly W cells wide (pad short ones with spaces)
norm = []
for l in lines:
    s = re.sub(r'\x1b\[[0-9;]*m', '', l)
    if len(s) < W:
        l = l + " " * (W - len(s))
    norm.append(l)

out = "\n".join(norm) + "\n\x1b[0m"
with open("scratch/raze-agent-sci-logo.ans", "w") as f:
    f.write(out)
print("wrote scratch/raze-agent-sci-logo.ans  wordmark width=%d cells, inner_w=%d" % (gw, inner_w))
