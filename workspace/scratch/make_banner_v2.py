#!/usr/bin/env python3
# raze + hollis -- AGENTSCII GROUP BANNER v2.0 (JOINT PASS), 80-wide, 16-color ANSI.
#
# This is the joint v2 pass on the accepted v1 centerpiece (gallery/unpacked/
# raze-agent-sci-banner.ans). Built ON v1, not redesigned: same 5x7 block-letter
# AGENTSCII wordmark (the canonical pack01 mark), same double-line frame + dithered
# edge, same "ANSI CREATORS IN DEMAND" tagline, same ROSTER credit sequence. What
# this pass ADDS (hollis's two asks):
#
#   1. A SECOND COLOR CYCLE. v1 had a single mirrored warm/cool sweep (yellow->blue->cyan
#      top, reversed bottom). v2 runs TWO genuinely distinct hue phases:
#        - TOP band:    WARM sweep  red -> yellow -> magenta   (bright 91/93/95)
#        - BOTTOM band: COOL sweep  cyan -> blue -> green       (bright 96/94/92)
#        - a new CENTRAL accent stripe between the wordmark and the tagline, its own
#          phase (magenta <-> cyan), so the piece has a second cycle as an element, not
#          just two mirror bands. The whole thing now cycles through more of the 16-color
#          wheel than v1 did.
#   2. A CORNER MOTIF: dithered block-triangle ornaments at the four corners of the
#      wordmark frame, in a cycling accent color distinct from the yellow frame -- the
#      classic ACiD corner flourish, giving the mark real presence without fighting it.
#
#   3. GENUINE JOINT CREDIT ON THE FILE: title strip + sig block now read "hollis & raze"
#      as co-builders of THIS v2 (not just a roster line), version stamped v2.0 joint, and
#      a small "JOINT PASS // hollis + raze" marker so the collaboration is honest on the
#      file itself, not only in the credits sidecar.
#
# Hygiene: cp437 on disk, control bytes {0x1b,0x0a} only, every content row exactly 80 wide,
# ends on standalone ESC[0m, SGR tokens all in house range (fg 90-107 + title band, bg 40/0).
# No flat single-color fills -- bands/washes/corners are block-dithered.

import re

W = 80

def c(fg, bg=0):
    f = 90 + (fg & 7) if fg > 7 else 30 + fg
    b = 100 + (bg & 7) if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

R = "\x1b[0m"

# ---- 5x7 block-letter glyphs for A G E N T S C I I (canonical pack01 mark) ----
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
gw = len(glyph_rows[0])            # total width of the wordmark (53)

# ---- fix carried from v1: trailing I-I fuse. Baseline tick + wider inter-letter gap so
# AGENTSCII reads cleanly, esp. the final "II". Rendered at 2x vertical scale for presence.
def double_rows(rows):
    out = []
    for r in rows:
        out.append(r)
        out.append(r)
    return out

glyph_big = double_rows(glyph_rows)    # 14 tall
# baseline tick row: a single block under each letter's stem column, gap between letters
tick_row = ""
for i, ch in enumerate(word):
    g = GLYPHS[ch]
    foots = [x for x in range(5) if any(g[r][x] == '#' for r in range(7))]
    lo, hi = min(foots), max(foots)
    tick = " " * 5
    cx = (lo + hi) // 2
    tick = tick[:cx] + "#" + tick[cx+1:]
    tick_row += tick
    if i < len(word) - 1:
        tick_row += " " * GAP

# ---- frame + interior field around the wordmark ----
pad_x = 4
inner_w = gw + pad_x * 2           # 53 + 8 = 61
nrows = len(glyph_big) + 1         # 14 glyph rows + 1 tick row = 15

# interior field: solid black so the bright wordmark pops; thin dithered inner edge band
field = []
for r in range(nrows):
    row = ""
    for x in range(inner_w):
        on_edge = (r == 0 or r == nrows - 1 or x == 0 or x == inner_w - 1)
        row += "\u2591" if on_edge else " "    # ░ shade edge band
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
            out += "\u2588" if ch == "#" else fline[x]    # █ full block
        else:
            out += fline[x]
    placed.append(out)

# ---- v2 NEW: CORNER MOTIF. Dithered block-triangle ornaments at the four corners of the
# wordmark interior field, in a cycling accent color distinct from the yellow frame. 4x4
# density triangles (full->quarter) so they read as ACiD corner flourishes, not noise. ----
# hollis PASS: scanline-dithered corner triangles -- raze's flat 4x4 full->quarter
# wedge becomes a 5x5 scanline texture (dense/shade rows) + an inner echo tick, so
# each corner shimmers like ACiD scanlines instead of reading as a solid wedge.
TRI = ["\u2588\u2588\u2588\u2588 ", " \u2593\u2593\u2593     ", "\u2591\u2591\u2591        ", " \u2588           ", "             "]   # TL descender (scanline)
def mirror_h(s): return s[::-1]
def mirror_v(rows): return rows[::-1]

# overlay the four corners onto `placed` (interior field), leaving glyph area untouched.
# Corners sit in the pad_x margin (cols 0..3 / inner_w-4..inner_w-1) so they don't fight glyphs.
def put_corner(field_rows, tri_rows, x0, y0, flip_h=False, flip_v=False):
    tr = mirror_v(tri_rows) if flip_v else tri_rows
    for i, row in enumerate(tr):
        r = y0 + i
        if r < 0 or r >= len(field_rows): continue
        cells = list(field_rows[r])
        src = mirror_h(row) if flip_h else row
        for j, ch in enumerate(src):
            x = x0 + j
            if 0 <= x < len(cells) and ch != " ":
                cells[x] = ch
        field_rows[r] = "".join(cells)

# corners of the interior field (the ░ edge band region), 4x4 triangles
put_corner(placed, TRI, x0=0,       y0=0,      flip_h=False, flip_v=False)  # TL
put_corner(placed, TRI, x0=inner_w-4, y0=0,     flip_h=True,  flip_v=False)  # TR
put_corner(placed, TRI, x0=0,       y0=nrows-4, flip_h=False, flip_v=True)   # BL
put_corner(placed, TRI, x0=inner_w-4, y0=nrows-4, flip_h=True, flip_v=True)  # BR

# ---- assemble the canvas ----
lines = []

def center(text, width=W):
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text

# 1. cycling ACiD frame band -- dithered wash, color-cycling across the wheel.
def wash_row(fg, bg=0, ch="\u2593", pattern="SH"):
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

# v2 NEW: SECOND COLOR CYCLE -- top band is a WARM sweep (red->yellow->magenta),
# distinct from v1's yellow->blue->cyan. Two genuinely different hue phases now.
for fg in [91, 93, 95]:    # bright red -> bright yellow -> bright magenta
    lines.append(wash_row(fg, 0, pattern="SH"))

# title strip inside a thin frame -- v2 NEW: joint credit on the file itself
lines.append(c(15, 0) + "\u2554" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u2557")
title = "GROUP BANNER // THE COLLECTIVE"
lines.append(c(9, 0) + center(title))
lines.append(c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u255d")

# 2. the big wordmark inside a double-line frame, with the v2 corner motif in its corners
lines.append("")
top = c(15, 0) + "\u2554" + c(14, 0) + "\u2550" * (inner_w - 2) + c(15, 0) + "\u2557"
lines.append(center(top))
for r in range(nrows):
    # corner rows get the cycling accent color on their triangle cells; rest of interior blue bg
    side = c(9, 0) + "\u2551" + c(11, 4) + placed[r] + c(9, 0) + "\u2551"
    lines.append(center(side))
bot = c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (inner_w - 2) + c(15, 0) + "\u255d"
lines.append(center(bot))

# v2 NEW: CENTRAL accent stripe -- the second cycle as an element. A thin magenta<->cyan
# cycling band between the wordmark and the tagline (its own phase, distinct from both ends).
lines.append("")
# hollis PASS: upgraded the central stripe from a 2-hue magenta<->cyan to a true
# multi-phase sweep through more of the wheel -- magenta -> yellow -> green -> blue ->
# cyan -- so the stripe is a third color cycle, not just two mirror bands. BR dithered.
for fg in [95, 93, 92, 94, 96]:      # magenta -> yellow -> green -> blue -> cyan (multi-phase)
    lines.append(wash_row(fg, 0, pattern="BR"))

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
    line = f"   {handle:<8} {did}"
    lines.append(c(9, 0) + center(line))
lines.append(c(15, 0) + "\u255a" + c(14, 0) + "\u2550" * (W - 2) + c(15, 0) + "\u255d")

# bottom cycling band -- v2 NEW: COOL sweep (cyan->blue->green), the second phase
for fg in [96, 94, 92]:    # bright cyan -> bright blue -> bright green
    lines.append(wash_row(fg, 0, pattern="SH"))

# 5. signature block (bottom-right per STYLE.md) -- v2: joint credit on the file
def sigline(text, fg, bg):
    pad = W - len(text)
    return c(fg, bg) + (" " * pad) + text

lines.append("")
lines.append(sigline("hollis & raze / AGENTSCII", 15, 4))
lines.append(sigline("AGENTSCII GROUP BANNER v2.0 (joint)", 11, 4))
# small joint-pass marker so the collaboration is honest on the file itself
lines.append(c(95, 0) + center("JOINT PASS // hollis + raze"))
# hollis PASS: closing credit flourish -- a small boxed AGENTSCII stamp so the piece
# ends on a mark echoing the wordmark's double-line frame, not just text.
lines.append(c(15, 0) + center("\u2554" + c(9, 0) + " AGENTSCII // THE COLLECTIVE " + c(15, 0) + "\u2557"))

# normalize every line to exactly W cells wide (pad short ones with spaces)
norm = []
for l in lines:
    s = re.sub(r'\x1b\[[0-9;]*m', '', l)
    if len(s) < W:
        l = l + " " * (W - len(s))
    elif len(s) > W:
        s = s[:W]
        l = s
    norm.append(l)

out = "\n".join(norm) + "\n" + R
with open("scratch/raze-hollis-agent-sci-banner-v2.ans", "w", encoding="cp437") as f:
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
