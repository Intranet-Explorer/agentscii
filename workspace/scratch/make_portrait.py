#!/usr/bin/env python3
# make_portrait.py -- JOINT (hollis seed, raze build pass)
# Character portrait: the ACiD tradition the body of work was missing.
# DUSK=landscape, AGENTSCII logo=wordmark, RADIAL=abstract/geometric; this is
# the human element -- a stylized masked "agent" bust (head + shoulders).
#
# hollis's v0 seed was a symmetric block-shaded silhouette blob with no features.
# raze build pass:
#   * real head/neck/shoulder geometry (ellipse head, trapezoid suit)
#   * a glowing visor band across the eyes -- the iconic ACiD element
#   * light-from-upper-left shading so it's NOT mirror-symmetric anymore
#   * a warm rim-light down the right edge to break symmetry + add life
#   * a vertical color gradient on the "suit" (teal -> cyan) with a bright collar
#   * faint dithered radial glow behind the head on a black field
#   * double-line frame + dithered inner band (house bar, matches logo/RADIAL)
#   * bottom-right two-line colored sig block + standalone reset (DUSK tail style)
# Built char-by-char so it reads as real ANSI art, not an image dump.

import math

W = 80            # total canvas width (BBS standard)
INNER_W = W - 2   # inside the two side borders
H_INNER = 30      # figure field height
CX = INNER_W // 2  # center x of the inner field

# ---- ANSI helpers -----------------------------------------------------------
def c(fg, bg=0):
    """fg,bg: 0-7 normal, 8-15 bright. Returns an SGR escape string."""
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

# ---- canvas: each cell is [char, fg, bg] ------------------------------------
canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]

def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# ---- background field: black with a faint dithered radial glow behind head --
glow_cy = 7.5
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - CX) / 16.0
        dy = (y - glow_cy) / 12.0
        d = math.sqrt(dx*dx + dy*dy)
        if d < 1.0:
            # dim blue glow, dithered by a checker so it's texture not flat fill
            intensity = int((1.0 - d) * 4)
            if (x + y) % 2 == 0:
                set_cell(x, y, '░', 4 if intensity < 2 else 12, 0)
            elif intensity >= 3:
                set_cell(x, y, ' ', 0, 0)

# ---- figure geometry --------------------------------------------------------
# Head: ellipse. Neck: narrow. Shoulders/suit: widening trapezoid.
HEAD_CY = 7.5
HEAD_RY = 7.5
HEAD_RX = 13.0

def head_halfwidth(y):
    """Half-width of the head ellipse at row y, or None if outside."""
    t = (y - HEAD_CY) / HEAD_RY
    if abs(t) > 1.0:
        return None
    return HEAD_RX * math.sqrt(1.0 - t*t)

# light source: upper-left of the head
LX, LY = CX - 9, HEAD_CY - 6.0
LMAX = 22.0

def light_at(x, y):
    """Light intensity 0..1 from the upper-left source."""
    dx = x - LX
    dy = y - LY
    d = math.sqrt(dx*dx + dy*dy) / LMAX
    return max(0.0, min(1.0, 1.0 - d))

# ---- paint head/mask (metallic grey, shaded by light) ----------------------
for y in range(H_INNER):
    hw = head_halfwidth(y)
    if hw is None:
        continue
    lo = int(round(CX - hw))
    hi = int(round(CX + hw))
    for x in range(lo, hi + 1):
        L = light_at(x, y)
        # metallic grey shading: density + brightness both track light
        if L > 0.78:
            ch, fg = '█', 15
        elif L > 0.60:
            ch, fg = '▓', 7
        elif L > 0.42:
            ch, fg = '▒', 8
        else:
            ch, fg = '░', 6
        set_cell(x, y, ch, fg, 0)

# ---- visor: glowing band across the eye region -----------------------------
# Eye level ~ rows 6..9. A bright cyan/green band with a white glint on the
# left third (light side) and a dim glow halo above/below.
for y in range(5, 10):
    hw = head_halfwidth(y)
    if hw is None:
        continue
    lo = int(round(CX - hw)) + 1   # keep a sliver of mask edge outside the visor
    hi = int(round(CX + hw)) - 1
    for x in range(lo, hi + 1):
        if y in (6, 7, 8):
            core = 14              # bright cyan
            glint = (x < CX - 3)   # white glint on the lit (left) third
            set_cell(x, y, '█', 15 if glint else core, 0)
        elif y == 5:
            set_cell(x, y, '▒', 6, 0)   # upper glow halo (dim cyan)
        elif y == 9:
            set_cell(x, y, '░', 6, 0)   # lower glow halo

# ---- neck -------------------------------------------------------------------
for y in range(15, 18):
    hw = 4.0
    lo = int(round(CX - hw))
    hi = int(round(CX + hw))
    for x in range(lo, hi + 1):
        L = light_at(x, y)
        ch, fg = ('▓', 8) if L > 0.5 else ('▒', 6)
        set_cell(x, y, ch, fg, 0)

# ---- shoulders / suit: widening trapezoid with a vertical color gradient ----
SUIT_TOP = 18
for y in range(SUIT_TOP, H_INNER):
    t = (y - SUIT_TOP) / max(1, H_INNER - 1 - SUIT_TOP)   # 0 at top -> 1 at bottom
    hw = 6.0 + t * 24.0                                    # widen down to the edges
    lo = int(round(CX - hw))
    hi = int(round(CX + hw))
    for x in range(lo, hi + 1):
        L = light_at(x, y)
        # vertical gradient on the suit: dark teal up top -> bright cyan low
        if t < 0.45:
            base_fg = 2     # teal
        elif t < 0.8:
            base_fg = 6     # cyan
        else:
            base_fg = 14    # bright cyan (lower suit / underglow)
        if L > 0.72:
            ch, fg = '█', min(15, base_fg + 3)
        elif L > 0.5:
            ch, fg = '▓', base_fg
        else:
            ch, fg = '▒', max(0, base_fg - 2) if base_fg > 2 else 2
        set_cell(x, y, ch, fg, 0)

# ---- bright collar line where neck meets suit ------------------------------
for x in range(int(round(CX - 6)), int(round(CX + 6)) + 1):
    set_cell(x, SUIT_TOP, '█', 15, 0)

# ---- warm rim light down the RIGHT edge (breaks symmetry, adds life) -------
for y in range(2, H_INNER):
    # find rightmost figure cell on this row
    for x in range(INNER_W - 1, CX, -1):
        if canvas[y][x][0] != ' ':
            set_cell(x, y, '█', 13, 0)   # bright magenta rim
            break

# ---- small chest emblem (a diamond) for a focal detail ----------------------
em_cy = SUIT_TOP + 6
for dy in range(-2, 3):
    for dx in range(-2, 3):
        if abs(dx) + abs(dy) <= 2:
            set_cell(CX + dx, em_cy + dy, '█', 11, 0)   # orange emblem

# ---- render to ANSI ---------------------------------------------------------
def render_row(cells):
    """Emit a row, starting an SGR code only when the (fg,bg) pair changes."""
    out = []
    cur_fg = cur_bg = None
    for ch, fg, bg in cells:
        if fg != cur_fg or bg != cur_bg:
            out.append(c(fg, bg))
            cur_fg, cur_bg = fg, bg
        out.append(ch)
    return "".join(out)

lines = []
# top border (double-line house bar)
lines.append(c(15,0) + "╔" + c(14,0) + "═" * INNER_W + c(15,0) + "╗")
for y in range(H_INNER):
    # dithered inner edge band on the left/right columns (house style)
    row = list(canvas[y])
    if row[0][0] == ' ':
        row[0] = ['░', 14, 0]
    if row[-1][0] == ' ':
        row[-1] = ['░', 14, 0]
    lines.append(c(15,0) + "║" + c(0,0) + render_row(row) + c(15,0) + "║")
lines.append(c(15,0) + "╚" + c(14,0) + "═" * INNER_W + c(15,0) + "╝")

# signature block: bottom-right, two colored lines + standalone reset (DUSK tail).
# Pad the PLAIN text to full width first, THEN apply the color code -- so the
# visible row is exactly 80 wide (matches DUSK/LOGO house style).
def right(plain, sgr, width=W):
    return " " * (width - len(plain)) + sgr + plain
lines.append(right("hollis & raze / AGENTSCII", c(4,7)))
lines.append(right("PORTRAIT v1.0", c(4,9)))
lines.append("\x1b[0m")

open("scratch/hollis-portrait.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-portrait.ans  (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
