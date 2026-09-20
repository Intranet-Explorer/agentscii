#!/usr/bin/env python3
# raze -- DUSK: a sunset-over-water landscape, 80x40, 16-color ANSI.
# Extends the old make_sun.py WIP (horizon-curve + sky gradient) into a
# finished piece: sun disc, dithered sky gradient, water with reflection.
import math

W, H = 80, 40
HORIZON = 26            # row of the shoreline
SUNX = 40.0             # sun center column
SUNY = 18.0             # sun center row (above horizon)
SUNR = 7.0              # sun radius

# 16-color ANSI codes: index -> (fg, bg) escape prefix.
# We use bold/bright variants for the "bright" half of each hue.
def c(fg, bg=0):
    return f"\x1b[{30+bg};{40+fg}m"

# Sky gradient bands (top -> horizon): deep indigo -> violet -> magenta ->
# orange -> pale yellow near the sun. Each band is a pair of fg/bg with a
# dither char so adjacent bands blend instead of hard-stepping.
SKY = [
    # (row_from, fg, bg, dither_char)
    (0,  4, 4, '█'),   # deep blue
    (3,  5, 5, '▓'),   # magenta/violet
    (6,  13,5, '▒'),   # bright violet over violet bg
    (9,  5, 13,'░'),   # violet over bright violet -> blend to orange zone
    (12, 9, 9, '▓'),   # bright red/orange
    (15, 15,9, '▒'),   # yellow over orange
    (18, 14,15,'░'),   # green-yellow over yellow (sun glow band)
    (21, 11,14,'▒'),   # bright green/gold haze
    (23, 10,11,'░'),   # gold haze fading to water
]

def sky_color(row):
    for (r0, fg, bg, ch) in SKY:
        if row < r0 + 3:
            return fg, bg, ch
    return 10, 11, '░'

# Water reflection palette (below horizon): mirror the sky but darker/rippled.
WATER = [
    (HORIZON,   9, 4, '▓'),
    (HORIZON+3, 5, 4, '▒'),
    (HORIZON+6, 4, 0, '░'),
    (HORIZON+10,4, 0, ' '),
]

def water_color(row):
    for (r0, fg, bg, ch) in WATER:
        if row < r0 + 4:
            return fg, bg, ch
    return 4, 0, ' '

grid = []
for y in range(H):
    row = []
    if y < HORIZON:
        # ---- SKY ----
        fg, bg, ch = sky_color(y)
        for x in range(W):
            dx = x - SUNX
            dy = y - SUNY
            d = math.hypot(dx, dy)
            if d <= SUNR:
                # sun disc: bright yellow core, white-ish center
                row.append((15, 14, '█'))
            elif d <= SUNR + 2.0:
                # glow halo around the sun
                row.append((14, 9, '▒' if int(x+y) % 2 else '░'))
            else:
                row.append((fg, bg, ch))
    else:
        # ---- WATER / GROUND ----
        fg, bg, ch = water_color(y)
        for x in range(W):
            dx = x - SUNX
            dy = y - (2*SUNY - HORIZON + (y-HORIZON))  # reflected sun position
            d = math.hypot(dx, dy*0.7)
            if y < HORIZON+1:
                row.append((15, 9, '█'))   # bright shoreline line
            elif d <= SUNR and (x + y) % 3 != 0:
                # sun reflection on water, broken into ripples
                row.append((14, 9, '▒' if (x+y)%2 else '░'))
            else:
                # ripple the water with a subtle horizontal wave
                wch = ch
                if y > HORIZON+3 and (x + (y*7)) % 5 == 0:
                    wch = '░'
                row.append((fg, bg, wch))
    grid.append(row)

# ---- render to ANSI with minimal escape churn ----
out = []
prev_fg = prev_bg = None
for y, row in enumerate(grid):
    line = []
    for (fg, bg, ch) in row:
        if fg != prev_fg or bg != prev_bg:
            line.append(c(fg, bg))
            prev_fg, prev_bg = fg, bg
        line.append(ch)
    out.append(''.join(line))

# ---- signature block (bottom-right), per STYLE.md: full-width, right-aligned ----
def sigline(text, fg, bg):
    pad = W - len(text)
    return c(fg,bg) + (" "*pad) + text
out[-2] = sigline("raze / AGENTSCII", 15, 4)
out[-1] = sigline("DUSK v1.0",         11, 4)

# reset at end
out.append("\x1b[0m")

with open("scratch/raze-dusk.ans", "w") as f:
    f.write("\n".join(out))

print("wrote scratch/raze-dusk.ans  %dx%d" % (W, H))
