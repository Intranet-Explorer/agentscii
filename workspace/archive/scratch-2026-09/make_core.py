#!/usr/bin/env python3
# make_core.py -- raze build (pack02 third piece, option (a): a machine/element).
#
# CORE v1.0 -- the cybernetic processing core: a glowing reactor orb housed in a
# hexagonal chassis, fed by energy conduits from the sides, with circuit traces
# radiating outward and a small AGENTSCI wordmark etched on the housing. It's the
# "machine" element of pack02 -- thematically the thing STREAM's data flows
# THROUGH (CITY = the city, CORE = the machine that powers it, STREAM = the data
# streaming through it), and it echoes pack01's PORTRAIT as the character/element
# tradition. Built char-by-char so it reads as real ANSI art, not an image dump.
#
# House conventions matched exactly to PORTRAIT/CITY/DUSK:
#   * double-line frame (bright white), dithered ░ inner edge band on side cols
#   * bottom-right two-line colored sig block + standalone \x1b[0m tail
#   * 80-col wide, 16-color ANSI, block-density dithering over flat fills
#   * AGENTSCI wordmark reused (etched small on the housing), not redesigned

import math

W = 80
INNER_W = W - 2
H_INNER = 34
CX = INNER_W // 2          # 39
CY = H_INNER // 2          # 17

def c(fg, bg=0):
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]
def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# ---------------------------------------------------------------------------
# Background: black with a faint dithered radial glow behind the core (the same
# move PORTRAIT used behind the head -- texture, not flat fill).
# ---------------------------------------------------------------------------
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - CX) / 18.0
        dy = (y - CY) / 14.0
        d = math.sqrt(dx*dx + dy*dy)
        if d < 1.0:
            intensity = int((1.0 - d) * 4)
            if (x + y) % 2 == 0:
                set_cell(x, y, '░', 5 if intensity < 2 else 13, 0)   # dim blue glow

# ---------------------------------------------------------------------------
# Hexagonal chassis housing around the core. A hexagon reads as "machine casing"
# far better than a circle; it's also geometrically distinct from RADIAL's rings
# and PORTRAIT's ellipse. Two nested hex outlines (outer bright, inner dim) with
# a dithered fill band between them = the housing shell.
# ---------------------------------------------------------------------------
def hex_halfwidth(y, cy, ry, rx):
    """Half-width of a pointy-top hexagon at row y (flat sides on left/right)."""
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return None
    # top/bottom thirds taper to points; middle third is full width
    if abs(t) < 0.5:
        return rx
    return rx * (1.0 - abs(abs(t) - 0.5) / 0.5)

RX_OUT, RY_OUT = 26.0, 14.0
RX_IN,  RY_IN  = 22.0, 11.0

for y in range(H_INNER):
    hw_out = hex_halfwidth(y, CY, RY_OUT, RX_OUT)
    hw_in  = hex_halfwidth(y, CY, RY_IN,  RX_IN)
    if hw_out is None:
        continue
    lo_out = int(round(CX - hw_out))
    hi_out = int(round(CX + hw_out))
    for x in range(lo_out, hi_out + 1):
        # outer shell edge (bright cyan outline)
        if abs(x - CX) >= hw_out - 0.6:
            set_cell(x, y, '█', 14, 0)
        elif hw_in is not None and abs(x - CX) <= hw_in + 0.6:
            continue   # leave the interior for the reactor core
        else:
            # housing band between inner & outer shell: dithered metallic grey,
            # light-from-upper-left so it's not flat / not mirror-symmetric
            L = max(0.0, 1.0 - math.sqrt((x-(CX-8))**2 + (y-(CY-7))**2) / 26.0)
            if L > 0.6:
                ch, fg = '▓', 7
            elif L > 0.35:
                ch, fg = '▒', 8
            else:
                ch, fg = '░', 6
            set_cell(x, y, ch, fg, 0)

# ---------------------------------------------------------------------------
# Energy conduits: two horizontal "pipes" feeding the core from the side edges
# of the canvas into the housing -- reads as power input. Bright, segmented.
# ---------------------------------------------------------------------------
for y in (CY - 3, CY + 3):
    for x in range(0, INNER_W):
        # stop where we hit the housing shell so the pipe "enters" it
        if canvas[y][x][0] != ' ':
            break
        seg = (x % 4)
        if seg == 0:
            set_cell(x, y, '▓', 6, 0)      # cyan pipe body
        elif seg == 3:
            set_cell(x, y, '█', 14, 0)     # bright joint
        else:
            set_cell(x, y, '░', 5, 0)

# ---------------------------------------------------------------------------
# The reactor core: concentric rings cycling the color wheel (STREAM's language),
# diamond-lattice dither between rings so they don't hard-step, a bright white
# center. This is the "energy" -- distinct from RADIAL because it's small,
# contained in a housing, and surrounded by circuitry rather than filling the
# whole field.
# ---------------------------------------------------------------------------
HUE = [13, 12, 11, 10, 6, 5]   # magenta->red->yellow->green->cyan->blue cycle
for y in range(H_INNER):
    for x in range(INNER_W):
        dx = (x - CX) / 1.0
        dy = (y - CY) / 1.0
        r = math.sqrt(dx*dx + dy*dy)
        if r > RY_IN:
            continue
        ring = int(r * 1.4)
        fg = HUE[ring % len(HUE)]
        # diamond-lattice dither: alternate density by (x+y) parity so rings
        # blend instead of hard-stepping
        if r < 0.9:
            ch, fgc = '█', 15          # white-hot center
        elif (x + y) % 2 == 0:
            ch, fgc = '▓', fg
        else:
            ch, fgc = '▒', fg
        set_cell(x, y, ch, fgc, 0)

# bright core glint
for dy in range(-1, 2):
    for dx in range(-1, 2):
        if abs(dx) + abs(dy) <= 1:
            set_cell(CX + dx, CY + dy, '█', 15, 0)

# ---------------------------------------------------------------------------
# Circuit traces: short radiating lines from the housing outward at cardinal /
# diagonal points -- reads as "wiring" leaving the core. Bright, segmented.
# ---------------------------------------------------------------------------
def trace(dx, dy, length, fg):
    for i in range(1, length + 1):
        x = int(round(CX + dx * i))
        y = int(round(CY + dy * i))
        if not (0 <= x < INNER_W and 0 <= y < H_INNER):
            break
        if canvas[y][x][0] != ' ':
            continue
        ch = '█' if i % 3 == 0 else '▒'   # segmented trace
        set_cell(x, y, ch, fg, 0)

for ang in range(0, 360, 45):
    a = math.radians(ang)
    dx, dy = round(math.cos(a)), round(math.sin(a))
    if dx == 0 and dy == 0:
        continue
    trace(dx, dy, 8, 12 if ang % 90 else 6)

# ---------------------------------------------------------------------------
# AGENTSCI wordmark etched small on the housing (reused house identity, not a
# redesign). Placed just below the core in the lower housing band.
# ---------------------------------------------------------------------------
word = "AGENTSCI"
x0 = CX - len(word)//2
for i, ch in enumerate(word):
    set_cell(x0 + i, CY + 13, ch, 15, 0)

# ---------------------------------------------------------------------------
# Render to ANSI (house frame + dithered inner band + sig block + reset tail).
# ---------------------------------------------------------------------------
def render_row(cells):
    out = []
    cur_fg = cur_bg = None
    for ch, fg, bg in cells:
        if fg != cur_fg or bg != cur_bg:
            out.append(c(fg, bg))
            cur_fg, cur_bg = fg, bg
        out.append(ch)
    return "".join(out)

lines = []
lines.append(c(15,0) + "╔" + c(14,0) + "═" * INNER_W + c(15,0) + "╗")
for y in range(H_INNER):
    row = list(canvas[y])
    if row[0][0] == ' ':
        row[0] = ['░', 14, 0]
    if row[-1][0] == ' ':
        row[-1] = ['░', 14, 0]
    lines.append(c(15,0) + "║" + c(0,0) + render_row(row) + c(15,0) + "║")
lines.append(c(15,0) + "╚" + c(14,0) + "═" * INNER_W + c(15,0) + "╝")

def right(plain, sgr, width=W):
    return " " * (width - len(plain)) + sgr + plain
lines.append(right("hollis & raze / AGENTSCII", c(4,7)))
lines.append(right("CORE v1.0", c(4,9)))
lines.append("\x1b[0m")

open("scratch/hollis-raze-core.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-raze-core.ans  (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
