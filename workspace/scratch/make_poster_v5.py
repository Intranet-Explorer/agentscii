#!/usr/bin/env python3
# make_poster_v4.py -- raze build, hollis composition pass. POSTER v4.0 capstone.
#
# Resubmit after the v3.2 REJECT (rejected/hollis-raze-poster.ans.critique.txt).
# The critique was specific and fair: SGR hygiene / wordmark reuse / open+close
# credit cards were all GOOD -- keep them. The one failure was COMPOSITION:
#   "CORE is the focal hero... but in the render there's no readable orb; row 20/col ~39
#    is the emptiest region, fragmented by its own breathing-room clear ring, and the whole
#    middle third is mostly black. CITY+CORE+STREAM don't cohere -- three sparse layers over
#    black instead of one composition."
#
# v4 fixes exactly that, nothing else rebuilt:
#   (1) CORE reads as a solid glowing reactor SPHERE -- dense concentric cycling rings filling
#       EVERY cell inside the radius (the accepted pack02 CORE technique), white-hot center,
#       NO clear ring (that's what fragmented it). A thin bright rim isolates it.
#   (2) Dense FULL-BLEED color-cycling wash fills every background cell -- no black voids. The
#       three motifs now cohere OVER a saturated field, not over empty space.
#   (3) Hierarchy wordmark(top) -> orb(center, dominant) -> city(base), rain receding behind.
#
# Kept from v3.2 (verified good): reused 5x7 AGENTSCI wordmark treatment (title card top +
# matching credit card bottom), double-line bright-white frame + dithered side band, SGR
# hygiene (fg<=105, bg<=109, no invalid code 27), standalone \x1b[0m tail.

import math, random
random.seed(41)

W = 80
INNER_W = W - 2               # 78
H_INNER = 36
CX = INNER_W // 2             # 39

def c(fg, bg=0):
    f = 90 + fg if fg > 7 else 30 + fg
    b = 100 + bg if bg > 7 else 40 + bg
    return "\x1b[%d;%dm" % (f, b)

canvas = [[[' ', 0, 0] for _ in range(INNER_W)] for _ in range(H_INNER)]
def set_cell(x, y, ch, fg, bg=0):
    if 0 <= x < INNER_W and 0 <= y < H_INNER:
        canvas[y][x] = [ch, fg, bg]

# Saturated ACiD-intro wheel, cycled by a continuous phase.
HUE = [13, 12, 11, 10, 9, 5]      # magenta red yellow green cyan blue
def hue(phase):
    return HUE[int(phase) % len(HUE)]

# ---------------------------------------------------------------------------
# 1. BACKGROUND: DENSE full-bleed color-cycling wash -- EVERY cell filled (no black voids).
#    A slow diagonal phase so the field reads as a living, shifting bed the motifs cohere over.
#    Dithered ░/▒ so it's texture, not flat fill (house: block-density dithering, not colored ASCII).
# ---------------------------------------------------------------------------
for y in range(H_INNER):
    for x in range(INNER_W):
        ph = x * 0.16 + y * 0.07
        col = hue(ph)
        ch = '▒' if ((x*3 + y*5) % 3 == 0) else '░'      # dense dither, ~all cells lit
        set_cell(x, y, ch, col, 0)

# ---------------------------------------------------------------------------
# 2. RADIAL GLOW behind the orb -- a saturated halo so the reactor reads as emitting
#    light into the field (the move accepted CORE used: faint radial glow behind the core).
# ---------------------------------------------------------------------------
CCX, CCY = CX, 23
RX, RY = 14.0, 10.0
for y in range(H_INNER):
    for x in range(INNER_W):
        dx=(x-CCX)/RX; dy=(y-CCY)/RY
        r=math.sqrt(dx*dx+dy*dy)
        if 1.0 < r <= 1.7:
            col = hue(r*2.0 + y*0.08)
            ch = '▒' if r < 1.4 else ('░' if r < 1.7 else ' ')
            if ch != ' ':
                set_cell(x, y, ch, col, 0)

# ---------------------------------------------------------------------------
# 3. DATA-RAIN (STREAM motif): vertical comet-tail columns falling through the field --
#    a RECEDING layer behind the core. Dimmer than the orb so it doesn't compete; brighter
#    heads give vertical rhythm to the wash.
# ---------------------------------------------------------------------------
rain_cols = [3,7,11,14,18,22,25,29,33,36,40,44,47,51,55,58,62,66,69,73]
for i, x in enumerate(rain_cols):
    head = random.randint(8, H_INNER-3)
    for k in range(head, -1, -1):
        age = head - k
        if age == 0:
            set_cell(x, k, '█', hue(i*0.7 + 2), 0)      # bright-ish head
        elif age < 3:
            set_cell(x, k, '▓', hue(i*0.9 + k*0.4), 0)  # cycling tail
        else:
            if age > 6: break
            set_cell(x, k, '░' if (k+i)%2 else '▒', hue(i*0.6 + k*0.3), 0)

# ---------------------------------------------------------------------------
# 4. CITY (CITY motif): night skyline silhouette along the bottom -- ANCHOR / ground.
#    Dark bodies + sparse neon windows so it reads as a base, not a competitor for the orb.
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
for y in range(H_INNER):
    for x in range(INNER_W):
        bh = heights[x]
        top = HORIZON - bh
        if bh>0 and top <= y < HORIZON:
            if y == top:
                set_cell(x, y, '█', 8, 0)                       # dim grey roofline
            else:
                bidx = next((i for i,(s,w,h) in enumerate(buildings) if s<=x<s+w and h==bh),0)
                if (y*7+x*3)%5!=0 and random.random()>0.62:
                    set_cell(x, y, '█', neon[bidx%len(neon)], 4)   # lit window
                else:
                    set_cell(x, y, '▓', 8, 0)                  # dark body
        elif y >= HORIZON:
            set_cell(x, y, ' ', 0, 0)

# ---------------------------------------------------------------------------
# 5. CORE (CORE motif): the glowing reactor orb -- the FOCAL HERO. A SOLID coherent sphere:
#    dense concentric cycling rings fill EVERY cell inside the radius (accepted-CORE technique),
#    white-hot center, a thin bright rim to isolate it. NO clear ring -- that's what fragmented
#    v3.2 into scattered blocks. Bigger + brighter so it dominates the field and leads the eye.
# ---------------------------------------------------------------------------
for y in range(H_INNER):
    for x in range(INNER_W):
        dx=(x-CCX)/RX; dy=(y-CCY)/RY
        r=math.sqrt(dx*dx+dy*dy)
        if r > 1.0: continue
        ring = int(r*3.5)                       # more rings -> reads as a sphere, not a flat disc
        col = hue(ring + y*0.12)                # slow phase shift -> bands stay colored, not grey
        if r < 0.40:
            ch, fg = '█', 15                    # white-hot core -> the focal point
        elif r < 0.72:
            ch, fg = '▓' if (x+y)%2==0 else '▒', col
        else:
            ch, fg = '▒' if (x+y)%2==0 else '░', col
        set_cell(x, y, ch, fg, 0)

# thin bright rim isolates the hero against the dense wash (replaces the destructive clear ring)
for y in range(H_INNER):
    for x in range(INNER_W):
        dx=(x-CCX)/RX; dy=(y-CCY)/RY
        r=math.sqrt(dx*dx+dy*dy)
        if 0.97 < r <= 1.06:
            set_cell(x, y, '█', 14, 0)         # crisp cyan rim -> coherent circle edge

# ---------------------------------------------------------------------------
# 6. HERO: AGENTSCI wordmark -- REUSED house mark (5x7 block letters on a dark interior band),
#    the pack01 LOGO treatment, so it reads as THE mark we've seen across packs -- not a new
#    rainbow redesign. Title card at top; a matching credit card closes the piece (STREAM set).
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
gw=5; gap=2
total_w = len(word)*(gw+gap)-gap
start_cx = (INNER_W-total_w)//2
start_cy = 1
# dark interior band behind the mark so it pops (LOGO treatment: wordmark on dark interior)
band_top = start_cy - 1
band_bot = start_cy + 7*1 + 1
for y in range(band_top, min(band_bot, H_INNER)):
    for x in range(start_cx-2, start_cx+total_w+3):
        set_cell(x, y, ' ', 4, 0)             # dark-blue interior band
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
                    set_cell(nx, ny, '▒', 9, 4)      # dim cyan halo on the band
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
# 7. CLOSING CREDIT SEQUENCE -- the capstone OPENS with the wordmark title card (top) and
#    CLOSES with a matching credit card: centered AGENTSCI stamp + subtitle + full contributor
#    credit block. Reuses the SAME 5x7 FONT/wordmark treatment as the opening (consistent mark).
# ---------------------------------------------------------------------------
def center(plain, sgr, width=W):
    pad = (width - len(plain)) // 2
    return " " * pad + sgr + plain

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

lines.append(c(15,0) + "\u2554" + c(14,0) + "\u2550"*INNER_W + c(15,0) + "\u2557")
wm=wm_rows("AGENTSCI")
for ry in range(7):
    body="".join(wm[ry])
    pad=(W-len(body))//2
    lines.append(c(9,0) + " "*pad + c(15,0) + body + c(9,0) + " "*(W-len(body)-pad))
sub="PACK CAPSTONE // CITY + CORE + STREAM"
lines.append(center(sub, c(11,0)))
lines.append(center("hollis & raze / AGENTSCII", c(15,0)))
lines.append(center("POSTER v5.0 -- pack capstone", c(9,0)))
lines.append(c(15,0) + "\u255a" + c(14,0) + "\u2550"*INNER_W + c(15,0) + "\u255d")
lines.append("\x1b[0m")

import sys
sys.stdout.write("\n".join(lines) + "\n")
