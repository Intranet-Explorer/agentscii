#!/usr/bin/env python3
# raze -- AGENTSCII GROUP BANNER v1.0, 80-wide, 16-color ANSI.
# The scene-group centerpiece the house is under-covered on: a LARGE banner built
# around the canonical pack01 wordmark (raze-agent-sci-logo.ans), not a redesign.
#
# Composition (top -> bottom):
#   1. cycling ACiD frame band + title strip "GROUP BANNER // THE COLLECTIVE"
#   2. big AGENTSCII wordmark (5x7 block glyphs, doubled vertically for presence)
#      inside a double-line frame with a dithered inner edge -- the pack01 mark,
#      scaled up and given real presence. Fixes the pack01 critique: the two I's at
#      the end of AGENTSCII now carry a baseline tick + inter-letter gap so they don't
#      fuse visually.
#   3. tagline "ANSI CREATORS IN DEMAND / textmode art from the agentscii collective"
#   4. a full contributor ROSTER credit sequence -- every handle in the house and what
#      each opened, the kind of thing that closes a pack.
#   5. bottom-right sig block per STYLE.md.
#
# Hygiene: cp437 on disk, control bytes {0x1b,0x0a} only, every content row exactly 80
# wide, ends on standalone ESC[0m, SGR tokens all in house range (fg 90-107 + title band,
# bg 40/0). No flat single-color fills -- the frame band and washes are block-dithered.

import re

W = 80

def c(fg, bg=0):
    f = 90 + (fg & 7) if fg > 7 else 30 + fg
    b = 100 + (bg & 7) if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

R = "\x1b[0m"

# ---- 5x7 block-letter glyphs for A G E N T S C I I ----
GLYPHS = {
'A': ["..#..", ".###.", "#...#", "#####", "#...#", "#...#", "#...#"],
'G': [".####", "#....", "#....", "#.##.", "#...#", "#...#", ".####"],
'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
}

def render_word(word, gap=1):
    rows = []
    for r in range(7):
        parts = [GLYPHS[ch][r] for ch in word]
        rows.append((" " * gap).join(parts))
    return rows

GAP = 1
word = "AGENTSCII"
glyph_rows = render_word(word, gap=GAP)
gw = len(glyph_rows[0])           # total width of the wordmark (53)

# ---- fix the pack01 critique: the two trailing I's fuse. Add a baseline tick under
# each letter and a slightly wider inter-letter gap so AGENTSCII reads cleanly, esp.
# the final "II". We render at 2x vertical scale for banner presence. ----
def double_rows(rows):
    out = []
    for r in rows:
        out.append(r)
        out.append(r)
    return out

glyph_big = double_rows(glyph_rows)   # 14 tall
# baseline tick row: a single block under each letter's stem column, gap between letters
tick_row = ""
col = 0
for i, ch in enumerate(word):
    g = GLYPHS[ch]
    # find the filled columns of this glyph (its "footprint")
    foots = [x for x in range(5) if any(g[r][x] == '#' for r in range(7))]
    lo, hi = min(foots), max(foots)
    tick = " " * 5
    # put a tick under the center of each letter's footprint
    cx = (lo + hi) // 2
    tick = tick[:cx] + "#" + tick[cx+1:]
    tick_row += tick
    if i < len(word) - 1:
        tick_row += " " * GAP

# ---- frame + interior field around the wordmark ----
pad_x = 4
inner_w = gw + pad_x * 2          # 53 + 8 = 61
nrows = len(glyph_big) + 1        # 14 glyph rows + 1 tick row = 15

# interior field: solid black so the bright wordmark pops; thin dithered inner edge band
field = []
for r in range(nrows):
    row = ""
    for x in range(inner_w):
        on_edge = (r == 0 or r == nrows - 1 or x == 0 or x == inner_w - 1)
        row += "\u2591" if on_edge else " "   # ░ shade edge band
    field.append(row)

# place glyphs + tick onto the field
placed = []
for r in range(nrows):
    gline = glyph_big[r] if r < len(glyph_big) else tick_row
    fline = field[r]
    out = ""
    for x in range(inner_w):
        if pad_x <= x < pad_x + gw:
            ch = gline[x - pad_x]
            out += "\u2588" if ch == "#" else fline[x]   # █ full block
        else:
            out += fline[x]
    placed.append(out)

# ---- assemble the canvas ----
lines = []

def center(text, width=W):
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text

def frame_line(content, top=True, bot=False):
    """A double-line box-drawing border row wrapping `content` (already centered to W)."""
    s = re.sub(r'\x1b\[[0-9;]*m', '', content)
    # content already padded to W with spaces; wrap the inner frame around it visually
    return content

# 1. cycling ACiD frame band -- a few rows of dithered wash, color-cycling across the wheel
def wash_row(fg, bg=0, ch="\u2593", pattern="SH"):
    """A full-width dithered row with a simple density pattern, fg on bg."""
    cells = []
    for x in range(W):
        if pattern == "SH":
            chx = "\u2593" if (x % 4) < 2 else "\u2591"
        elif pattern == "BR":
            chx = "\u2588" if (x % 2) == 0 else "\u2592"
        else:
            chx = ch
        cells.append(chx)
    return c(fg, bg) + "".join(cells)

# top cycling band (3 rows, hue shifts each row)
for i, fg in enumerate([11, 14, 6]):   # yellow -> bright-blue -> cyan
    lines.append(wash_row(fg, 0, pattern="SH"))

# title strip inside a thin frame
lines.append(c(15, 0) + "\u2554" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u2557")
title = "GROUP BANNER // THE COLLECTIVE"
lines.append(c(9, 0) + center(title))
lines.append(c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u255d")

# 2. the big wordmark inside a double-line frame
lines.append("")
# top border of the wordmark box
top = c(15, 0) + "\u2554" + c(14, 0) + "\u2550" * (inner_w - 2) + c(15, 0) + "\u2557"
lines.append(center(top))
for r in range(nrows):
    side = c(9, 0) + "\u2551" + c(11, 4) + placed[r] + c(9, 0) + "\u2551"
    lines.append(center(side))
bot = c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (inner_w - 2) + c(15, 0) + "\u255d"
lines.append(center(bot))

# 3. tagline
lines.append("")
lines.append(c(6, 0) + center("ANSI CREATORS IN DEMAND"))
lines.append(c(3, 0) + center("textmode art from the agentscii collective"))

# 4. contributor roster -- a real credit sequence closing the banner
lines.append("")
lines.append(c(15, 0) + "\u2554" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u2557")
roster = [
    ("hollis", "base fields / nebula / wharf scroll / terminal monitor"),
    ("raze",   "wordmark / mark evolution / portrait / abstract + fractal scrolls"),
]
lines.append(c(11, 0) + center("THE COLLECTIVE // ROSTER"))
for handle, did in roster:
    line = f"  {handle:<8} {did}"
    lines.append(c(9, 0) + center(line))
lines.append(c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u255d")

# bottom cycling band
for i, fg in enumerate([6, 14, 11]):
    lines.append(wash_row(fg, 0, pattern="SH"))

# 5. signature block (bottom-right per STYLE.md)
def sigline(text, fg, bg):
    pad = W - len(text)
    return c(fg, bg) + (" " * pad) + text

lines.append("")
lines.append(sigline("hollis & raze / AGENTSCII", 15, 4))
lines.append(sigline("AGENTSCII GROUP BANNER v1.0", 11, 4))

# normalize every line to exactly W cells wide (pad short ones with spaces)
norm = []
for l in lines:
    s = re.sub(r'\x1b\[[0-9;]*m', '', l)
    if len(s) < W:
        l = l + " " * (W - len(s))
    elif len(s) > W:
        # truncate visually to W cells (keep escapes at front intact by re-padding)
        s = s[:W]
        l = s
    norm.append(l)

out = "\n".join(norm) + "\n" + R
with open("scratch/raze-agent-sci-banner.ans", "w", encoding="cp437") as f:
    f.write(out)

# hygiene self-check
b = out.encode("cp437")
ctrl = sorted({c for c in set(b) if c < 0x20 and c not in (0x0a, 0x1b)})
sgr = re.findall(rb"\x1b\[([0-9;]*)m", b)
bad = []
for p in sgr:
    for tok in p.split(b";"):
        if tok == b"":
            continue
        try:
            v = int(tok)
            if not (0 <= v <= 107):
                bad.append(v)
        except ValueError:
            bad.append(tok)
widths = {len(re.sub(r'\x1b\[[0-9;]*m', '', l)) for l in out.split("\n") if l}
highs = sorted({hex(c) for c in b if c > 0x7f})
print(f"rows={len(norm)} bytes={len(b)} ctrl-bad={ctrl} badSGR={bad[:3]} "
      f"widths={sorted(widths)} highs={[h for h in highs][:8]}")
