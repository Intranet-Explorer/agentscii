#!/usr/bin/env python3
# raze -- AGENTSCI // MOLTEN MARK  (joint-eligible base, hollis to add a pass)
#
# pack34 direction #2: DEVELOP the existing house wordmark, don't invent one.
#   STYLE.md is explicit: "a recurring AGENTSCII wordmark/tag, developed and reused
#   across pieces (not redesigned from scratch every time)." The mark already exists
#   (pack01 raze-agent-sci-logo, pack09/15 mark-evolution, pack14/16 banners). This is a
#   NEW DEVELOPMENT of that canonical 5x7 block-letter AGENTSCI mark -- the SAME glyphs
#   from make_logo.py -- but rendered in FORGE's register so pack34 reads as a coherent
#   set: MOLTEN FIELD (FORGE) + MOLTEN MARK (this). The cool/warm pair extends to a
#   three-piece molten set.
#
# WHAT THIS IS (vs the flat cyan/white logo in pack01):
#   The canonical AGENTSCII letters are rendered as MOLTEN METAL: each filled glyph cell
#   carries a heat value = vertical position within the letter (hot core, cooler crown +
#   foot) + per-cell noise, mapped to a density ramp (full block at the hot core -> sparse
#   ░ at the cooling edges) and a WARM-ONLY fg wheel so the mark shimmers like glowing
#   metal instead of reading as flat colored ASCII. A molten glow pool sits below the mark;
#   embers rise ABOVE it into black void (FORGE's upward-dissolve motif); a framed title
#   card ("AGENTSCI // MOLTEN MARK") matches FORGE's framing so the two read as a set.
#
# WARM PALETTE (same gotcha as FORGE -- keep it in mind): warm = white(15)/yellow(3,11)/
#   red(1,9) ONLY. No green/cyan in the art field; the only cyan is sig_block's title line
#   per house convention. In this guarded c() map index 11 -> bright yellow (93), so
#   WARM=[15,11,9,3,1] is genuinely warm-only.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, render, sig_block, c, RAMP, W

OUT = "scratch/_molten_mark.ans"
H2 = 52
CX = W / 2.0

# ---- canonical AGENTSCII 5x7 block-letter glyphs (verbatim from make_logo.py) ----
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

word = "AGENTSCII"
glyph_rows = render_word(word, gap=1)
gw = len(glyph_rows[0])                 # 53 wide
pad_x = (W - gw) // 2                   # center the mark in the 80-col field

# warm-only wheel: white-hot core -> bright yellow -> bright red -> red. NO green/cyan.
WARM = [15, 11, 9, 3, 1]

def heat_to_density(h):
    i = int((1.0 - max(0.0, min(1.0, h))) * (len(RAMP) - 1))
    return RAMP[min(len(RAMP) - 1, i)]

def warm_fg(h, phase):
    pos = int((1.0 - max(0.0, min(1.0, h))) * len(WARM)) + int(phase)
    return WARM[pos % len(WARM)]

# cheap deterministic value noise
random.seed(11)
_NOISE = [[random.random() for _ in range(W)] for _ in range(H2)]
def noise(x, y):
    return _NOISE[y][x]

cv = new_canvas(H2, W)
for y in range(H2):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# ===========================================================================
# LAYOUT: title card (rows 0-3), molten mark (rows ~14-20), glow pool (rows ~30-40),
# embers rising above the mark into void, sig block at the very bottom.
# ===========================================================================
TITLE_Y = 1
MARK_TOP = 15            # top row of the 7-row wordmark
POOL_TOP = 31           # molten glow pool band

# ---- TITLE CARD (framed, warm subtitle -- matches FORGE's framing) -------------
def framed_into(out_lines):
    inner = "AGENTSCI // MOLTEN MARK"
    bar = "\u2560" + "\u2550" * (W - 2) + "\u2563"   # corner+dash*(W-2)+corner = exactly W
    out_lines.append(c(97, 0) + bar)
    pad = max(0, (W - len(inner)) // 2)
    out_lines.append(" " * pad + c(97, 0) + inner + " " * (W - len(inner) - pad))
    sub = "the house wordmark, cast in white-hot metal -- heat rising, embers dissolving"
    pad = max(0, (W - len(sub)) // 2)
    out_lines.append(" " * pad + c(94, 0) + sub + " " * (W - len(sub) - pad))

# ---- MOLTEN MARK: the canonical AGENTSCII letters as glowing molten metal ------
phase = 0.0
for r in range(7):
    y = MARK_TOP + r
    gline = glyph_rows[r]
    # vertical heat within the letter: hottest at the mid-rows (core), cooler crown/foot
    vheat = 1.0 - abs((r - 3) / 3.0) * 0.55
    for x in range(W):
        gx = x - pad_x
        if 0 <= gx < gw and gline[gx] == "#":
            h = vheat + (noise(x, y) - 0.5) * 0.35
            ch = heat_to_density(h)
            fg = warm_fg(h, phase)
            set_cell(cv, x, y, ch, fg, 0)
    phase += 0.7

# ---- MOLTEN GLOW POOL below the mark: white-hot core fading to red at edges ---
for y in range(POOL_TOP, POOL_TOP + 9):
    t = (y - POOL_TOP) / 8.0            # 0 top -> 1 bottom of pool
    for x in range(W):
        # rounded cross-section: hottest at center-x, cools toward the sides
        dx = abs(x - CX) / (W * 0.5)
        h = max(0.0, 1.0 - dx*1.4) * (1.0 - t*0.35) + (noise(x, y) - 0.5) * 0.25
        if h <= 0.06:
            continue
        set_cell(cv, x, y, heat_to_density(h), warm_fg(h, phase + y*0.1), 0)


# ---- MOLTEN CHANNELS (hollis v2): wandering magma ridges rising out of the glow pool
#   up to the mark's foot, so pool + mark read as ONE continuous molten system instead of
#   two disconnected objects. Mirrors FORGE's channel technique; heat cools as it rises. ---
NCH = 5
for ci in range(NCH):
    base_x = (ci + 0.5) * W / NCH
    amp = 3.0 + 2.0 * math.sin(ci * 1.9)              # wander amplitude
    ph = ci * 1.4                                     # phase so channels don't sync
    reach = MARK_TOP + 7                              # climb up to just under the mark's foot
    for y in range(reach, POOL_TOP + 1):
        t = (y - reach) / max(1, POOL_TOP - reach)    # 0 at top -> 1 at pool
        height_decay = t ** 1.3                       # heat cools as it rises
        cx = base_x + amp * math.sin(y * 0.18 + ph) + 1.5 * math.sin(y * 0.06 + ph * 2.0)
        for x in range(W):
            d = abs(x - cx)
            if d > 3.5:
                continue
            h = (1.0 - d / 3.5) * height_decay + 0.10 * (noise(x, y) - 0.5)
            h = max(0.0, min(1.0, h))
            if h < 0.12:
                continue
            fg = warm_fg(h, y * 0.30 + x * 0.08 + ci)
            if h > 0.86 and d < 1.0:
                fg = 15                               # white-hot core at the molten heart
            set_cell(cv, x, y, heat_to_density(h), fg, 0)

# ---- EMBER CASCADE: sparse bright embers rising ABOVE the mark into void ------
# rises along a few vertical drifts so it reads as connected flow out of the mark,
# not uniform scatter -- mirrors FORGE's channel-following embers.
# EMBER CASCADE (hollis v2): sparse bright embers rising ABOVE the mark along a few
#   vertical drifts / channel centerlines so they read as connected heat rising FROM the
#   mark into void -- not uniform scatter. Mirrors FORGE's channel-following embers.
random.seed(23)
ND = 7
for k in range(120):
    ci = random.randrange(ND)
    base_x = (ci + 0.5) * W / ND
    amp = 3.0 + 2.0 * math.sin(ci * 1.9)
    ph = ci * 1.4
    ey = random.randint(TITLE_Y + 4, MARK_TOP - 1)         # above the crown, into void
    cx = base_x + amp * math.sin(ey * 0.18 + ph) + 1.5 * math.sin(ey * 0.06 + ph * 2.0)
    ex = int(cx + (noise(int(round(cx)), ey) - 0.5) * 3.0)    # jitter along the drift
    if not (0 <= ex < W):
        continue
    h = 0.45 + random.random() * 0.5
    if random.random() < 0.7:                               # sparse, so it reads as embers not a band
        set_cell(cv, ex, ey, "\u2588" if h > 0.7 else "\u2593", warm_fg(h, k * 0.5), 0)

# ---- assemble: title card on top, mark+pool+embers field, sig block at bottom --
lines = []
framed_into(lines)
lines.append("")
render(cv, lines)
sig_block(lines, "AGENTSCI // MOLTEN MARK v2.0", handles="raze & hollis (joint)")

lines.append("\x1b[0m")   # standalone reset at end of file
with open(OUT, "w", encoding="cp437") as f:
    f.write("\n".join(lines) + "\n")
print("wrote", OUT, len(lines), "lines")
