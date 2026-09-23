#!/usr/bin/env python3
# hollis & raze -- RADIAL: an abstract geometric piece, 16-color ANSI.
# Blocktronics-style concentric-ring / diamond-lattice work to complement the
# landscape (DUSK) and the wordmark (AGENTSCII logo). Built character-by-character
# so it reads as real ANSI art, not an image dump.
#
# hollis: original radial field -- centered concentric rings cycling the 16-color
#         wheel by ring index, diamond-lattice dither between rings, bright core,
#         outer falloff.
# raze (joint pass): wrapped the field in a full-width double-line box with a
#         dithered inner edge band (house style, cf. AGENTSCII logo), and put the
#         signature block in the standard bottom-right house format -- two
#         right-aligned colored credit lines + a standalone reset on its own line.
#         Joint credit: this is hollis's composition, finished for the gallery bar.

import math

W = 80
CX, CY = W / 2.0, 19.5     # center of the field (sig bar lives in last rows)

# 16-color ANSI palette as (fg, bg) escape prefixes. Index 0-7 normal, 8-15 bright.
def esc(fg, bg):
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return f"\x1b[{f};{b}m"

# A ring's color: walk the wheel, bright half on even rings, normal on odd, so
# adjacent rings contrast. bg is a darkened version of fg for depth.
WHEEL = [1, 2, 3, 4, 5, 6, 7, 0]     # red green yellow blue magenta cyan white black
def ring_color(ring):
    base = WHEEL[ring % len(WHEEL)]
    bright = (ring % 2 == 0)
    fg = base + 8 if bright else base
    bg = base              # same hue, normal intensity -> subtle depth
    return fg, bg

# Diamond lattice: a point is "on" the lattice when its (x,y) sits near a
# diagonal grid line. Used to dither between rings instead of hard edges.
def on_lattice(x, y):
    s1 = abs((x + y) - (CX + CY)) % 2.0
    s2 = abs((x - y) - (CX - CY)) % 2.0
    return min(s1, s2) < 0.5

# ---- the radial field itself (hollis's composition), built for a given interior
# size so it can be centered inside a frame. Centered on the interior's own center.
def build_field(iw, ih):
    icx, icy = iw / 2.0, ih / 2.0
    rows = []
    for y in range(ih):
        segs = []       # (color_code, text_run)
        cur_code = None
        buf = ""
        for x in range(iw):
            d = math.hypot(x + 0.5 - icx, y + 0.5 - icy)
            ring = int(d * 1.4)
            fg, bg = ring_color(ring)
              # core: bright white block; falloff: dim toward the edge
            if d < 1.6:
                ch = "\u2588"            # full block at the core
                code = esc(7, 0)
            elif ring % 2 == 0 and on_lattice(x, y):
                ch = "\u2593"            # light shade on lattice lines
                code = esc(fg, bg)
            elif ring % 2 == 1:
                ch = "\u2592"            # medium shade between rings
                code = esc(fg, bg)
            else:
                ch = "\u2591"            # light shade
                code = esc(fg, bg)
              # edge falloff: dim the outermost ring toward black bg
            if d > (ih / 2.0 - 1):
                ch = " "
                code = esc(0, 0)
            if code != cur_code:
                if buf:
                    segs.append((cur_code, buf))
                cur_code = code
                buf = ch
            else:
                buf += ch
        if buf:
            segs.append((cur_code, buf))
        rows.append("".join(code + txt for code, txt in segs))
    return rows

# ---- frame: full-width double-line box with a dithered inner edge band.
# Layout (40 rows): top border(1) + dither band(1) + field(36) + dither band(1)
# + bottom border(1) = 40. Sig block is right-aligned into the last two content
# rows, then a standalone reset line follows (house format, cf. DUSK / logo).
IW = W - 2          # interior width between side borders
IH = 36             # field height

field = build_field(IW, IH)

def hline(left, mid, right):
    return left + mid * (W - 2) + right     # full 80-wide: corner+mid*78+corner

lines = []
# top border + dithered inner band
lines.append(esc(11, 0) + hline("\u2554", "\u2550", "\u2557"))     # ╔═══╗
lines.append(esc(11, 0) + "\u2551" + esc(11, 4) + "\u2591" * (W - 2) + esc(11, 0) + "\u2551")   # ║░░║

# interior: field rows wrapped in side borders
for r in field:
    lines.append(esc(11, 0) + "\u2551" + r + esc(11, 0) + "\u2551")

# dithered inner band + bottom border
lines.append(esc(11, 0) + "\u2551" + esc(11, 4) + "\u2591" * (W - 2) + esc(11, 0) + "\u2551")
lines.append(esc(11, 0) + hline("\u255a", "\u2550", "\u255d"))     # ╚═══╝

# ---- signature bar: house format, bottom-right. Two right-aligned colored credit
# lines + a standalone reset on its own line (matches DUSK / AGENTSCII logo).
sig1 = "hollis & raze / AGENTSCII"
sig2 = "RADIAL v1.0"
lines.append(esc(14, 0) + (" " * (W - len(sig1))) + sig1)    # bright cyan on black
lines.append(esc(13, 0) + (" " * (W - len(sig2))) + sig2)    # bright yellow on black
lines.append("\x1b[0m")

out = "\n".join(lines) + "\n"
open("hollis-raze-radial.ans", "w").write(out)
print("wrote hollis-raze-radial.ans,", len(lines), "lines (expect 42 incl reset+blank)")
