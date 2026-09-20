#!/usr/bin/env python3
# CITY — night skyline over water, AGENTSCII pack02 WIP.
# Reuses DUSK's vertical-gradient + water-reflection technique and stamps the
# AGENTSCI wordmark onto a tower (the recurring house identity across packs).
# 80 cols wide. Built char-by-char, ends on standalone \x1b[0m like DUSK.

W = 80
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# SGR palette
BWHITE=97; BCYAN=96; BYELLOW=93; BGREEN=92; BRED=91; BMAGENTA=95
BBLUE_B=104; BBLACK=100

HORIZON = 20   # row index of waterline
TOTAL_ROWS = 36

# building profile: (start_col, width, height)
buildings = [
     (2, 6, 8),
     (9, 4, 12),
     (14, 7, 6),
     (22, 5, 15),    # tall tower -> neon sign column
     (28, 6, 9),
     (35, 4, 13),
     (40, 8, 7),
     (49, 5, 16),    # tallest
     (55, 6, 10),
     (62, 4, 11),
     (67, 7, 8),
     (75, 3, 14),
]
neon = [BMAGENTA, BCYAN, BYELLOW, BGREEN, BRED]

# per-column building height
heights = [0]*W
for (s,w,h) in buildings:
    for col in range(s, s+w):
        if 0 <= col < W and h > heights[col]:
            heights[col] = h

# lit windows (dithered), one neon color per building
import random
random.seed(7)
windows = set()
for idx,(s,w,h) in enumerate(buildings):
    color = neon[idx % len(neon)]
    for r in range(h):
        if r == 0:   # roofline row stays dark
            continue
        for col in range(s, s+w):
            if (r*7+col*3) % 5 != 0 and random.random() > 0.6:
                windows.add((HORIZON - h + r, col))

# neon sign column on the tall tower (col 24, height 15)
sign_col = 24
tower_top = HORIZON - heights[sign_col]

# stars in upper sky
stars = {(0,12),(0,55),(1,30),(1,70),(2,8),(2,44),(3,60),(3,18),(4,50)}

# AGENTSCI tag in the sky, top-right
tag = "AGENTSCI"
tag_row = 1
tag_cols = {tag_row: [60+i for i in range(len(tag))]}

# ---- build a grid of (char, fg, bg) ----
grid = [[(" ", None, BBLACK) for _ in range(W)] for _ in range(TOTAL_ROWS)]

for r in range(TOTAL_ROWS):
    for col in range(W):
        char, fg, bg = " ", None, BBLACK
        if r < HORIZON:
             # sky gradient by row band
            if r < 2:
                bg = BBLUE_B; char = "█"
            elif r < 4:
                bg = 45; char = "▓"
            elif r < 6:
                bg = 35; char = "▒"
            else:
                bg = 35; char = "░"
             # star?
            if (r, col) in stars:
                char = "*"; fg = BWHITE; bg = None
         # building body
        bh = heights[col]
        if bh > 0 and HORIZON - bh <= r < HORIZON:
            top = HORIZON - bh
            if r == top:
                char = "█"; fg = 45; bg = None     # roofline
            else:
                # per-building body shade so towers read as distinct masses, not one slab
                bidx = next((i for i,(s,w,h) in enumerate(buildings) if s<=col<s+w and h==bh), 0)
                char = "▓" if bidx % 2 == 0 else "▒"
                if (r, col) in windows:
                    for idx,(s,w,h) in enumerate(buildings):
                        if s <= col < s+w and h == bh:
                            fg = neon[idx % len(neon)]; bg = 40; break
                else:
                    fg = 34; bg = None            # dark building body
        grid[r][col] = (char, fg, bg)

# neon sign column on tower
for r in range(tower_top+1, HORIZON):
    grid[r][sign_col] = ("█", BWHITE, 40)

# AGENTSCI sky tag
for col in tag_cols[tag_row]:
    if col < W:
        grid[tag_row][col] = (tag[col-60], BWHITE, None)

# ---- moon: a small bright disc high in the sky to anchor it like DUSK's sun ----
MOON_R, MOON_C, MOON_RAD = 4, 70, 2
for dr in range(-MOON_RAD-1, MOON_RAD+2):
    for dc in range(-MOON_RAD-1, MOON_RAD+2):
        rr, cc = MOON_R+dr, MOON_C+dc
        if not (0<=rr<HORIZON and 0<=cc<W): continue
        d = dr*dr + dc*dc
        if d <= MOON_RAD*MOON_RAD:
            grid[rr][cc] = ("█", BWHITE, None)
        elif d <= (MOON_RAD+1)**2:
            grid[rr][cc] = ("▒", 37, None)   # faint halo

# ---- warm horizon glow band: a magenta/amber smear just above the waterline ----
for col in range(W):
    for rr in (HORIZON-1, HORIZON-2):
        if heights[col] and rr >= HORIZON-heights[col]:
            continue   # don't overwrite building bodies
        grid[rr][col] = ("░", 35, None) if rr==HORIZON-1 else (" ", 95, None)

# ---- water reflection: mirror silhouette, broken/dithered as it deepens
for r in range(HORIZON, TOTAL_ROWS):
    depth = r - HORIZON
    for col in range(W):
        bh = heights[col]
        if bh > 0 and depth < bh:
            src_r = HORIZON - 1 - depth
            char, fg, bg = "░", 34, None
            if (src_r, col) in windows:
                char, fg = "▒", BCYAN
             # break reflection with dithering as it deepens
            if depth > 2 and (col + depth) % 3 == 0:
                char, fg, bg = " ", None, None
        else:
             # water base: dark blue faint ripple
            char = "░" if (col + r) % 4 != 0 else " "
            fg, bg = 34, None
        grid[r][col] = (char, fg, bg)

# ---- emit ANSI ----
def render():
    s = ""
    cur_fg = cur_bg = None
    for r in range(TOTAL_ROWS):
        s += sgr(0, BBLACK)
        for col in range(W):
            ch, fg, bg = grid[r][col]
            if fg != cur_fg or bg != cur_bg:
                codes = []
                codes.append(39 if fg is None else fg)
                codes.append(40 if bg is None else bg)
                s += sgr(*codes)
                cur_fg, cur_bg = fg, bg
            s += ch
        s += "\n"
    return s

body = render()

# signature bar (right-aligned, like DUSK/PORTRAIT) + standalone reset
sig = " " * (80-len("hollis & raze / AGENTSCII")) + sgr(BCYAN) + "hollis & raze / AGENTSCII\n"
sig += " " * (80-len("CITY v1.0")) + sgr(BWHITE) + "CITY v1.0\n"
sig += RESET

open("scratch/hollis-city.ans","w").write(body + sig)
print("wrote scratch/hollis-city.ans")
