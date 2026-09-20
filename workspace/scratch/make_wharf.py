#!/usr/bin/env python3
# raze -- WHARF v1.0: restrained-palette block-dithered night-harbor scene.
# The ACiD idiom we've never done (grounded in acdu0896 / GD-SPYDR / SM-WHARF):
# a deliberately SMALL palette on black, dither carrying shading ONLY at transitions.
#
# Fixes across three passes (hollis's critique + my own preview reads):
#   1. NO full-width vertical gradients -- they render as hard scanlines/stripes. Sky is flat
#      black with a faint 2-row horizon glow; water is mostly flat black with a thin shimmer
#      band under the shore + sparse ripple ticks. Dither shows ONLY at real transitions.
#   2. reflection is a VERTICAL column under ONE light source, broken into short horizontal
#      ripple bands that fragment with depth -- tiny jitter so it stays under the lamp, not diagonal.
#   3. one focal light source: a single warm-amber lamp on the pier; everything lit by it.
#   4. sig block bottom-right per STYLE.md.
#
# ENCODING: cp437, not utf-8. Every box-drawing char is a single CP437 byte -- the exact
# bug that bit PLASMA/GRIDFALL at pack04 review, fixed here at the source.

import math
import random

W = 80
H = 40
LAMPX = 58             # single light source x -- the lamp on the pier (upper-right)
LAMPTOP = 9            # row of the lamp head (focal point)
PIER = 19              # waterline / pier deck row
WATER_TOP = PIER + 1

# --- restrained palette: deep blue / cyan / white + ONE warm amber accent on black ---
K = "\x1b[0;0m"        # black (background)
B = "\x1b[0;4m"        # deep blue      -- structure, water shimmer
C = "\x1b[1;6m"        # bright cyan -- horizon glow, water highlights
Wt= "\x1b[1;7m"        # white          -- lamp core, stars, brightest reflection
A = "\x1b[1;3m"        # bright red/amber -- warm lamp accent (warm vs cool contrast)
R = "\x1b[0m"

# grid of (color, char) cells
cells = [[(K, " ") for _ in range(W)] for _ in range(H)]

def put(x, y, col, ch):
    if 0 <= x < W and 0 <= y < H:
        cells[y][x] = (col, ch)

# ---------- SKY: flat black with sparse stars; a faint cyan glow right at the horizon ----------
random.seed(7)
for _ in range(9):                       # a few white points, deliberately sparse
    put(random.randint(2, W - 3), random.randint(1, PIER // 2), Wt, "*")
for y in range(PIER - 2, PIER):          # only the last two rows above the waterline glow
    g = (y - (PIER - 2)) / 2.0           # 0..1 across those two rows
    ch = "\u2591" if g < 0.5 else "\u2592"     # ░ then ▒ -- faint, never solid
    col = C if g > 0.4 else B
    for x in range(W):
        put(x, y, col, ch)

# ---------- LAMP: single warm-amber focal source on a pier post ----------
for y in range(LAMPTOP + 1, PIER):       # vertical post from head down to deck
    put(LAMPX, y, B, "\u2502")           # thin post (deep blue)
put(LAMPX, LAMPTOP, A, "\u2588")         # amber lamp head
put(LAMPX - 1, LAMPTOP, A, "\u2593")     # halo left
put(LAMPX + 1, LAMPTOP, A, "\u2593")     # halo right
put(LAMPX, LAMPTOP - 1, Wt, "\u2588")    # white hot center above
for dx in (-2, 2):                       # soft amber glow ring -- one row only
    put(LAMPX + dx, LAMPTOP, A, "\u2591")

# ---------- PIER / WHARF structure at the waterline ----------
deck = PIER
for x in range(W):
    put(x, deck, B, "\u2584")            # half-block deck top
for x in range(0, W, 6):                 # support posts dropping into the water
    for y in range(deck + 1, min(deck + 3, H)):
        put(x, y, B, "\u2502")

# ---------- WATER: mostly flat black (deep night water); faint shimmer just below the shore ----------
for y in range(WATER_TOP, min(WATER_TOP + 4, H)):       # a thin shimmer band under the deck
    g = (y - WATER_TOP) / 4.0
    for x in range(W):
        if (x + y) % 7 == 0:                 # per-column jitter -> shimmer, not a hard stripe
            put(x, y, B, "\u2591")
        elif g < 0.6:
            put(x, y, B, "\u2591")
# a few scattered ripple ticks deeper down -- sparse, never banded
for y in range(WATER_TOP + 6, H - 4):
    for x in range(0, W, 5):
        if (x * 3 + y * 7) % 11 == 0:
            put(x, y, B, "\u2591")

# ---------- REFLECTION: vertical column under the lamp, horizontal ripples that fragment ----------
# Light falls STRAIGHT DOWN from LAMPX. Each row is a short horizontal ripple band; deeper
# rows get shorter + more broken (fragmentation). Jitter is TINY so the column stays under
# the lamp -- it reads as wavy water, not a diagonal streak.
for y in range(WATER_TOP, H):
    depth = (y - WATER_TOP) / max(1, (H - WATER_TOP))         # 0 -> 1
    jit = int(round(math.sin(y * 1.3) * (0.6 + depth)))       # tiny wobble, grows slowly
    cx = LAMPX + jit
    half = max(1, int(2.5 * (1 - depth)))                      # band shrinks with depth
    frag = 0.7 - depth * 0.45                                  # deeper rows drop more cells
    for dx in range(-half, half + 1):
        x = cx + dx
        if x < 0 or x >= W:
            continue
        intensity = (1 - depth) * (1 - abs(dx) / (half + 1))
        if random.random() > frag and depth > 0.3:
            continue                         # fragmentation deeper down
        col = A if depth < 0.18 else C       # warm at the source, cool below
        ch = "\u2588" if intensity > 0.6 else ("\u2593" if intensity > 0.3 else "\u2591")
        put(x, y, col, ch)

# ---------- SIG BLOCK: bottom-right credit per STYLE.md ----------
SIG = [
     ("AGENTSCII", C),
     ("WHARF v1.0", Wt),
     ("raze / 1996", B),
]
for i, (txt, col) in enumerate(SIG):
    yy = H - 3 + i
    for j, ch in enumerate(txt):
        put(W - len(txt) - 1 + j, yy, col, ch)

# ---------- emit (run-length compressed like real ACiD) ----------
lines = []
for y in range(H):
    line = ""
    x = 0
    while x < W:
        col, ch = cells[y][x]
        run = 1
        while x + run < W and cells[y][x + run] == (col, ch):
            run += 1
        line += f"{col}{ch * run}"
        x += run
    lines.append(line + R)

out = "\n".join(lines) + "\n"
with open("scratch/raze-wharf.ans", "w", encoding="cp437") as f:      # <-- cp437, the fix
    f.write(out)

# ---------- hygiene self-check (the way hollis checks pack04) ----------
b = out.encode("cp437")
import re
ctrl = [c for c in set(b) if c < 0x20 and c not in (0x0a, 0x1b)]
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
utf8_box = b.count(b"\xe2\x94") + b.count(b"\xe2\x96")      # 3-byte utf8 box/shade prefixes
highs = sorted({c for c in b if c > 0x7f})
widths = {len(l) for l in out.split("\n") if l}
print("bytes", len(b))
print("ctrl-bad", ctrl, "badSGR", bad[:5])
print("utf8-box-sequences", utf8_box, "(must be 0)")
print("high bytes (all valid CP437):", [hex(h) for h in highs])
print("col-widths unique:", widths)
print("tail", b.rstrip()[-6:])
print("rows", H, "palette: deep-blue/cyan/white + amber accent on black (restrained 4+1)")
