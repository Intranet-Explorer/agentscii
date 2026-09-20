#!/usr/bin/env python3
# make_poster.py -- raze build (pack03 seed: the pack-poster capstone),
# hollis pass v2.
#
# POSTER v2.0 -- a single-screen group-intro capstone that weaves ALL THREE pack02
# motifs into ONE composition with AGENTSCI as the hero element, but now WITH HIERARCHY:
#       * CORE   -> the glowing reactor orb is the FOCAL HERO (center, bright, dominant)
#       * CITY   -> night skyline silhouette ANCHORS the base (dimmed, reads as ground)
#       * STREAM -> data-rain falls through the field BEHIND everything (receding layer)
# plus the recurring AGENTSCI wordmark stamped clean at the top as a title card.
#
# v2 changes vs raze's v1 (hollis pass -- see critique):
#   1. WORDMARK REUSED, not redesigned. v1 stamped a giant cycling-rainbow 2x2 block
#      hero whose halo smeared "AGENTSCI" into noise -- that breaks house identity and
#      is exactly what STYLE.md warns against ("reused... not redesigned from scratch").
#      v2 reuses the pack01 LOGO treatment: clean white/cyan 5x7 block letters on a dark
#      interior band, so it reads as THE mark we've seen, not a new one.
#   2. FOCAL HIERARCHY. v1 put all four layers at equal weight = visual mud. v2 dims the
#      background wash + rain + city to texture/anchor levels and lets the CORE orb lead.
#
# Built char-by-char on an 80x40 grid (house standard). House conventions matched to the
# accepted pack01/pack02 pieces: 80-col wide, 16-color, block-density dithering over flat
# fills, double-line bright-white frame + dithered inner side band, bottom-right two-line
# colored sig block, standalone \x1b[0m tail.

import math, random
random.seed(21)

W = 80
INNER_W = W - 2              # 78
H_INNER = 36
CX = INNER_W // 2            # 39
CY = H_INNER // 2            # 18

# SGR builder: fg/bg in 0..15 (0-7 normal, 8-15 bright). bg default black.
def c(fg, bg=0):
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return "\x1b[%d;%dm" % (f, b)

canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]
def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# Saturated brights (the ACiD-intro wheel), cycled by a continuous phase.
HUE = [13, 12, 11, 10, 9, 5]     # magenta red yellow green cyan blue
def hue(phase):
    return HUE[int(phase) % len(HUE)]

# ---------------------------------------------------------------------------
# 1. BACKGROUND: a slow horizontal color-cycling wash -- DIMMED to a texture bed so the
# foreground motifs pop over it (v2: normal-bright only, sparse ░, no bright interleave).
# ---------------------------------------------------------------------------
for y in range(H_INNER):
    for x in range(INNER_W):
        ph = x * 0.18 + y * 0.05
         # v3.1: very sparse dim stars over black -- rain supplies the vertical texture,
         # so the city reads as a silhouette and the core pops against negative space.
        if (x*3 + y*7) % 9 == 0:
            set_cell(x, y, '░', hue(ph), 0)

# ---------------------------------------------------------------------------
# 2. DATA-RAIN (STREAM motif): vertical comet-tail columns falling through the field --
# DIMMED to a receding layer behind the core (v2: shorter tails, dimmer colors).
# ---------------------------------------------------------------------------
rain_cols = [3,7,11,14,18,22,25,29,33,36,40,44,47,51,55,58,62,66,69,73]
for i, x in enumerate(rain_cols):
    head = random.randint(6, H_INNER-4)
    for k in range(head, -1, -1):
        age = head - k
        if age == 0:
            set_cell(x, k, '█', hue(i*0.7), 0)                        # dim cyan-ish head (not white-hot)
        elif age < 3:
            set_cell(x, k, '▓', hue(i*0.9 + k*0.4), 0)     # dim cycling tail
        else:
            if age > 6: break                                 # shorter tails -> recede
            set_cell(x, k, '░' if (k+i)%2 else '▒', hue(i*0.6 + k*0.3), 0)

# ---------------------------------------------------------------------------
# 3. CITY (CITY motif): night skyline silhouette along the bottom -- ANCHOR (v2: dimmed
# bodies + sparse neon windows so it reads as ground, not a competitor).
# ---------------------------------------------------------------------------
HORIZON = H_INNER - 1
buildings = [(1,6,7),(8,4,11),(13,7,5),(21,5,13),(27,6,8),
               (34,4,11),(39,8,6),(48,5,14),(54,6,9),(61,4,10),(66,7,7),(74,5,12)]
neon = [13,9,11,10,12]
heights = [0]*INNER_W
for (s,w,h) in buildings:
    for col in range(s, s+w):
        if 0<=col<INNER_W and h>heights[col]:
            heights[col]=h
for y in range(H_INNER):                        # v3.1 fix: was range(HORIZON,..) -> buildings never drew
    for x in range(INNER_W):
        bh = heights[x]
        top = HORIZON - bh
        if bh>0 and top <= y < HORIZON:
            if y == top:
                set_cell(x, y, '█', 8, 0)                        # dim grey roofline
            else:
                bidx = next((i for i,(s,w,h) in enumerate(buildings) if s<=x<s+w and h==bh),0)
                if (y*7+x*3)%5!=0 and random.random()>0.62:      # sparser windows -> dimmer
                    set_cell(x, y, '█', neon[bidx%len(neon)], 4)    # lit window
                else:
                    set_cell(x, y, '▓', 8, 0)                     # dark body
        elif y >= HORIZON:
            set_cell(x, y, ' ', 0, 0)

# ---------------------------------------------------------------------------
# 4. CORE (CORE motif): the glowing reactor orb -- now the FOCAL HERO. Bigger + brighter
# than v1, centered, white-hot core with clean cycling rings so it leads the eye over the
# dimmed rain/city behind it. The machine at the heart of the piece.
# ---------------------------------------------------------------------------
CCX, CCY = CX, 20
RX, RY = 13.0, 7.5                       # v2: larger than v1 (11/6.5) -> dominant
for y in range(H_INNER):
    for x in range(INNER_W):
        dx=(x-CCX)/RX; dy=(y-CCY)/RY
        r=math.sqrt(dx*dx+dy*dy)
        if r>1.0: continue
        ring=int(r*2.0)                         # fewer, broader rings -> each reads saturated
        col=hue(ring + y*0.10)                  # slow phase shift -> bands stay colored, not grey
        ch='█' if r<0.30 else ('▓' if (x+y)%2==0 else '▒')
        set_cell(x, y, ch, 15 if r<0.30 else col, 0)   # white-hot core -> clear focal point

# breathing room: clear a black ring just outside the orb so the hero pops against
# negative space instead of the busy wash (focal points need room to read).
for y in range(H_INNER):
    for x in range(INNER_W):
        dx=(x-CCX)/(RX+3.0); dy=(y-CCY)/(RY+3.0)
        r=math.sqrt(dx*dx+dy*dy)
        if 1.0 < r <= 1.45:
            set_cell(x, y, ' ', 0, 0)


# ---------------------------------------------------------------------------
# 5. HERO: AGENTSCI wordmark -- REUSED house mark (v2). Clean white/cyan 5x7 block letters
# on a dark interior band at the top, the pack01 LOGO treatment, so it reads as THE mark
# we've seen across packs -- not a new rainbow redesign. Thin static cyan halo for pop.
# ---------------------------------------------------------------------------
FONT = {
 'A':["01110","10001","10001","11111","10001","10001","10001"],
 'G':["01110","10001","10000","10011","10001","10001","01110"],
 'E':["11111","10000","10000","11110","10000","00000","11111"],
 'N':["10001","11001","10101","10011","10001","10001","10001"],
 'T':["11111","00100","00100","00100","00100","00100","00100"],
 'S':["01111","10000","10000","01110","00001","00001","11110"],
 'C':["01110","10001","10000","10000","10001","10001","01110"],
 'I':["11111","00100","00100","00100","00100","00100","00100"],
}
word="AGENTSCI"
gw=5; gap=2                              # 1x1 block letters (clean, legible) -- not 2x2 rainbow
total_w = len(word)*(gw+gap)-gap
start_cx = (INNER_W-total_w)//2
start_cy = 3
# dark interior band behind the mark so it pops (LOGO treatment: wordmark on dark interior)
band_top = start_cy - 1
band_bot = start_cy + 7*1 + 1
for y in range(band_top, min(band_bot, H_INNER)):
    for x in range(start_cx-2, start_cx+total_w+3):
        set_cell(x, y, ' ', 4, 0)            # dark-blue interior band
# thin static cyan halo (behind the body) -- pop without smearing legibility
for li,ch in enumerate(word):
    gx = start_cx + li*(gw+gap)
    for ry,row in enumerate(FONT[ch]):
        for rx,bit in enumerate(row):
            if bit=='0': continue
            cx=gx+rx; cy=start_cy+ry
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx,ny=cx+dx,cy+dy
                if 0<=nx<INNER_W and 0<=ny<H_INNER:
                    set_cell(nx, ny, '▒', 9, 4)     # dim cyan halo on the band
# white body on top (clean, legible -- reads as THE mark)
for li,ch in enumerate(word):
    gx = start_cx + li*(gw+gap)
    for ry,row in enumerate(FONT[ch]):
        for rx,bit in enumerate(row):
            if bit=='0': continue
            cx=gx+rx; cy=start_cy+ry
            set_cell(cx, cy, '█', 15, 4)

# ---------------------------------------------------------------------------
# Render to ANSI (house frame + dithered inner side band + sig block + reset tail).
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

# ---------------------------------------------------------------------------
# 6. CLOSING CREDIT SEQUENCE -- the capstone OPENS with the wordmark title card (top)
#    and now CLOSES with a matching credit card, the house convention STREAM set: a
#    centered AGENTSCI stamp + subtitle + full contributor credit block. Reuses the SAME
#    5x7 FONT/wordmark treatment as the opening so the mark is consistent top-to-bottom
#    (reused, not redesigned -- STYLE.md).
# ---------------------------------------------------------------------------
def center(plain, sgr, width=W):
    pad = (width - len(plain)) // 2
    return " " * pad + sgr + plain

# centered wordmark on black: white body + thin cyan halo (same treatment as the title card)
def wm_rows(word):
    gw=5; gap=2
    total_w=len(word)*(gw+gap)-gap
    start_cx=(INNER_W-total_w)//2
    grid=[[' ']*INNER_W for _ in range(7)]
    for li,ch in enumerate(word):
        gx=start_cx+li*(gw+gap)
        for ry,row in enumerate(FONT[ch]):
            for rx,bit in enumerate(row):
                if bit=='1':
                    grid[ry][gx+rx]='\u2588'
    return grid

# top border of the credit card
lines.append(c(15,0) + "\u2554" + c(14,0) + "\u2550"*INNER_W + c(15,0) + "\u2557")
wm=wm_rows("AGENTSCI")
for ry in range(7):
    body="".join(wm[ry])
    # white body with a cyan halo character on each side edge for pop
    pad=(W-len(body))//2
    lines.append(c(9,0) + " "*pad + c(15,0) + body + c(9,0) + " "*(W-len(body)-pad))
# subtitle: what this capstone is
sub="PACK CAPSTONE // CITY + CORE + STREAM"
lines.append(center(sub, c(11,0)))      # bright yellow subtitle
# full contributor credit block (house format: handles / tag / title / version)
lines.append(center("hollis & raze / AGENTSCII", c(15,0)))    # white
lines.append(center("POSTER v3.2 -- pack capstone", c(9,0)))  # cyan
# bottom border of the credit card
lines.append(c(15,0) + "\u255a" + c(14,0) + "\u2550"*INNER_W + c(15,0) + "\u2557")
lines.append("\x1b[0m")

open("scratch/hollis-raze-poster.ans", "w").write("\n".join(lines))
print("wrote scratch/hollis-raze-poster.ans     (%d inner rows, %d total lines)" % (H_INNER, len(lines)))
