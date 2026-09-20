#!/usr/bin/env python3
# raze -- shared helpers for the hollis-raze WHARF scroll (pack05 joint).
# Carries WHARF v1.0's discipline through every panel:
#   - 80 wide, CP437 encoding (NOT utf-8 -- the pack04 bug, fixed at source)
#   - restrained palette on black: deep blue / cyan / white + ONE warm amber accent
#   - dither ONLY at real transitions; flat regions stay flat single-char/color
#   - one light source per panel; it moves through the cycle (dusk sun -> lamp -> dawn sun)
#   - run-length compressed emit like real ACiD, hygiene self-check on every write

import math
import re
import random

W = 80
H = 40
PIER = 19                 # waterline / pier deck row (shared across panels)
WATER_TOP = PIER + 1

# --- restrained palette: deep blue / cyan / white + ONE warm amber accent on black ---
K = "\x1b[0;0m"          # black (background)
B = "\x1b[0;4m"          # deep blue       -- structure, water shimmer
C = "\x1b[1;6m"          # bright cyan     -- horizon glow, water highlights
Wt= "\x1b[1;7m"          # white           -- lamp core / sun core, stars, brightest reflection
A = "\x1b[1;3m"          # bright red/amber -- warm light accent (warm vs cool contrast)
R = "\x1b[0m"

# block/shade glyphs as single CP437 bytes (NOT utf-8 multibyte -- the pack04 lesson)
BLK = "\u2588"   # full block
HVF = "\u2584"   # lower half
HTF = "\u2580"   # upper half
SH3 = "\u2593"   # 3/8 shade
SH2 = "\u2592"   # 1/2 shade
SH1 = "\u2591"   # 1/8 shade
BAR = "\u2502"   # vertical bar
HRZ = "\u2500"   # horizontal line

def new_canvas():
    return [[(K, " ") for _ in range(W)] for _ in range(H)]

def put(cells, x, y, col, ch):
    if 0 <= x < W and 0 <= y < H:
        cells[y][x] = (col, ch)

def emit(cells, path, note=""):
    """Run-length compress + write CP437 + hygiene self-check. Returns the bytes."""
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
    with open(path, "w", encoding="cp437") as f:      # <-- cp437, the fix
        f.write(out)

    b = out.encode("cp437")
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
    utf8_box = b.count(b"\xe2\x94") + b.count(b"\xe2\x96")   # 3-byte utf8 box/shade prefixes
    highs = sorted({c for c in b if c > 0x7f})
    widths = {len(l) for l in out.split("\n") if l}
    ok = (not ctrl and not bad and utf8_box == 0)
    print(f"[{path}] bytes={len(b)} rows={H} "
          f"ctrl-bad={ctrl} badSGR={bad[:3]} utf8-box={utf8_box} "
          f"highs={[hex(h) for h in highs]} widths={widths} HYGIENE={'OK' if ok else 'FAIL'}")
    return b, ok

def stars(cells, n=9, seed=7, ymax=None):
    """Sparse white points in the upper sky -- deliberately sparse, never a band."""
    random.seed(seed)
    ytop = ymax if ymax is not None else PIER // 2
    for _ in range(n):
        put(cells, random.randint(2, W - 3), random.randint(1, ytop), Wt, "*")

def horizon_glow(cells, rows=2, col=C):
    """Faint glow only on the last `rows` above the waterline -- never full-width solid."""
    for i, y in enumerate(range(PIER - rows, PIER)):
        g = i / max(1, rows)
        ch = SH1 if g < 0.5 else SH2
        c = col if g > 0.4 else B
        for x in range(W):
            put(cells, x, y, c, ch)

def pier_deck(cells, col=B):
    """Pier deck at the waterline + support posts dropping into the water."""
    for x in range(W):
        put(cells, x, PIER, col, HVF)
    for x in range(0, W, 6):
        for y in range(PIER + 1, min(PIER + 3, H)):
            put(cells, x, y, col, BAR)

def water_shimmer(cells, band=4, seed=11):
    """Mostly flat black water; a thin shimmer band just under the deck + sparse ripple ticks."""
    random.seed(seed)
    for i, y in enumerate(range(WATER_TOP, min(WATER_TOP + band, H))):
        g = i / max(1, band)
        for x in range(W):
            if (x + y) % 7 == 0:
                put(cells, x, y, B, SH1)
            elif g < 0.6:
                put(cells, x, y, B, SH1)
    for y in range(WATER_TOP + 6, H - 4):
        for x in range(0, W, 5):
            if (x * 3 + y * 7) % 11 == 0:
                put(cells, x, y, B, SH1)

def reflection_column(cells, lx, warm_top=0.18, seed=3):
    """Vertical light column under a source at column `lx`, broken into short horizontal
    ripple bands that fragment with depth -- wavy water, not a diagonal streak."""
    random.seed(seed)
    for y in range(WATER_TOP, H):
        depth = (y - WATER_TOP) / max(1, (H - WATER_TOP))     # 0 -> 1
        jit = int(round(math.sin(y * 1.3) * (0.6 + depth)))   # tiny wobble, grows slowly
        cx = lx + jit
        half = max(1, int(2.5 * (1 - depth)))                  # band shrinks with depth
        frag = 0.7 - depth * 0.45                              # deeper rows drop more cells
        for dx in range(-half, half + 1):
            x = cx + dx
            if x < 0 or x >= W:
                continue
            intensity = (1 - depth) * (1 - abs(dx) / (half + 1))
            if random.random() > frag and depth > 0.3:
                continue
            col = A if depth < warm_top else C                  # warm at the source, cool below
            ch = BLK if intensity > 0.6 else (SH3 if intensity > 0.3 else SH1)
            put(cells, x, y, col, ch)

def sig_block(cells, lines, col=C):
    """Small credit block bottom-right per STYLE.md."""
    for i, (txt, c) in enumerate(lines):
        yy = H - len(lines) + i
        for j, ch in enumerate(txt):
            put(cells, W - len(txt) - 1 + j, yy, c, ch)

# --- hollis: shared block-letter wordmark so the title (P0) and credit (P5) cards
#     carry one consistent, legible AGENTSCII/WHARF mark -- a recurring group logo,
#     not a hand-drawn scribble. 5-row solid block font, CP437 full blocks. ---
FONT = {
      "W": ["###    ###", "###    ###", "###    ###", " ## # ## ", "   ###    "],
      "H": ["#       #", "#       #", "#######", "#       #", "#       #"],
      "A": [" #####", "#      #", "#      #", "#######", "#      #"],
      "R": ["#####", "#     #", "#####", "#   ##", "#    #"],
      "F": ["#######", "#", "#", "####", "#"],
}

def wordmark(cells, text, y0, col, ch=BLK):
    rows = 5
    width = len(text) * 8 - 1
    x0 = (W - width) // 2
    for li, letter in enumerate(text):
        art = FONT[letter]
        for r in range(rows):
            for c, cell in enumerate(art[r]):
                if cell == "#":
                    put(cells, x0 + li * 8 + c, y0 + r, col, ch)
