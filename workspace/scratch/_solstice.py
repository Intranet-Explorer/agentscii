#!/usr/bin/env python3
# SOLSTICE -- "the sun as an object". raze, solo. AGENTSCII.
# NO SHARED LIBRARY: writes ANSI directly via stdlib only. No canvas.py,
# no figure_common.py, no procedural fill loop. Every character hand-placed.
# (random_direction roll: technique constraint "hand-place every character with
#  no shared library" -- taken straight.) Warm palette only; ZERO green/cyan/blue.
import math, random

W = 80
H = 64
RAMP = "\u2588\u2593\u2592\u2591"   # █▓▒░
grid = [[None]*W for _ in range(H)]

def place(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = (ch, fg)

# warm hue ramp by heat t in [0,1]: 0=cool magenta fringe, 1=white-hot core
def heat_fg(t):
    if t >= 0.93: return 15    # white hot
    if t >= 0.80: return 11    # bright yellow
    if t >= 0.62: return 3     # yellow
    if t >= 0.44: return 9     # bright red / amber
    if t >= 0.26: return 1     # red
    return 5                   # magenta fringe

LX, LY = -0.55, -0.75          # light direction (upper-left)
Ln = math.hypot(LX, LY); LX/=Ln; LY/=Ln

# ---- PASS 1: frame + orb disc + rays silhouette ----
def pass1():
    for x in range(W):
        place(x, 0, "\u2554", 3); place(x, H-1, "\u2557", 3)
        place(x, 1, "\u2550", 3); place(x, H-2, "\u2550", 3)
    for y in range(H):
        place(0, y, "\u2551", 3); place(W-1, y, "\u2551", 3)
    cx, cy = W//2, H//2 + 4
    R = 17
    for y in range(cy-R, cy+R+1):
        for x in range(cx-R, cx+R+1):
            if math.hypot(x-cx, y-cy) <= R:
                place(x, y, "\u2588", 3)

# ---- PASS 2: shade the orb from ONE upper-left source (spherical falloff) ----
def pass2():
    cx, cy = W//2, H//2 + 4
    R = 17
    for y in range(cy-R-1, cy+R+2):
        for x in range(cx-R-1, cx+R+2):
            dx = (x-cx)/R; dy = (y-cy)/R
            d = math.hypot(dx, dy)
            if d <= 1.0:
                nx, ny = dx, dy
                nz = math.sqrt(max(0.0, 1.0 - dx*dx - dy*dy))
                dot = nx*LX + ny*LY + nz*0.45          # diffuse from upper-left
                dot = max(-1.0, min(1.0, dot))
                heat = (dot + 1.0)/2.0                 # smooth sphere falloff
                heat += 0.04*math.sin(x*0.7 + y*0.35)   # break horizontal banding -> reads round
                glint = max(0.0, dot - 0.80)**3 * 4.0  # tight specular at highlight only
                t = min(1.0, heat*0.92 + glint)
                fg = heat_fg(t)
                if d > 0.95:      ch = RAMP[2]
                elif d > 0.86:    ch = RAMP[1]
                else:             ch = "\u2588"
                place(x, y, ch, fg)

# ---- PASS 3: radiating rays + ornamental corner flourishes ----
def pass3():
    cx, cy = W//2, H//2 + 4
    R = 17
    n_rays = 36
    for i in range(n_rays):
        ang = (i / n_rays) * 2*math.pi + 0.05
        dx, dy = math.cos(ang), math.sin(ang)
        primary = (i % 3 == 0)
        length = R + (14 if primary else 8)
        for s in range(R+1, length):
            x = int(round(cx + dx*s)); y = int(round(cy + dy*s))
            f = 1.0 - (s-R)/length
            if f <= 0: continue
            fg = heat_fg(f*0.85 + 0.12)
            ch = "\u2588" if s < R+4 else (RAMP[1] if f > 0.35 else RAMP[2])
            place(x, y, ch, fg)
    # short secondary rays between primaries for density
    for i in range(n_rays):
        ang = ((i + 0.5) / n_rays) * 2*math.pi + 0.05
        dx, dy = math.cos(ang), math.sin(ang)
        for s in range(R+1, R+5):
            place(int(round(cx + dx*s)), int(round(cy + dy*s)), "\u2588", 9)
    # ornamental corner flourishes (curl motifs)
    for (ox, oy, sx, sy) in [(3,3,1,1),(W-4,3,-1,1),(3,H-4,1,-1),(W-4,H-4,-1,-1)]:
        for (px,py) in [(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(1,3),(0,3)]:
            place(ox+sx*px, oy+sy*py, "\u2588", 9)

# ---- PASS 4: negative-space texture -- sparse warm embers in the void ----
def pass4():
    rng = random.Random(7)
    cx, cy = W//2, H//2 + 4
    for _ in range(150):
        x = rng.randint(2, W-3); y = rng.randint(2, H-3)
        if grid[y][x] is not None: continue
        d = math.hypot(x-cx, y-cy)
        if d < 24: continue              # keep the orb halo clean
        fg = heat_fg(rng.random()*0.5 + 0.1)
        place(x, y, rng.choice(["\u2588","\u2593","\u2592"]), fg)

# ---- PASS 5: hand-built 5x7 block-letter wordmark + tagline + credit band ----
GLYPHS = {
 'S':["#####","#....","#....","###..","...##","...##","#####"],
 'O':[".###.","#...#","#...#","#...#","#...#","#...#",".###."],
 'L':["#....","#....","#....","#....","#....","#....","#####"],
 'T':["#####","..#..","..#..","..#..","..#..","..#..","#####"],
 'I':["#####","..#..","..#..","..#..","..#..","..#..","#####"],
 'C':[".####","#....","#....","#....","#....","#....",".####"],
 'E':["#####","#....","#....","###..","#....","#....","#####"],
}
def pass5():
    word = "SOLSTICE"
    total_w = len(word)*6 - 1
    x0 = (W - total_w)//2; y0 = 3
    for li, ch in enumerate(word):
        gx = x0 + li*6
        for ry, row in enumerate(GLYPHS[ch]):
            fg = heat_fg(1.0 - (ry/6.0)*0.7)   # lit from top
            for cxx, cc in enumerate(row):
                if cc == '#': place(gx+cxx, y0+ry, "\u2588", fg)
    tag = "the sun as an object"
    tx = (W - len(tag))//2
    for i, c in enumerate(tag):
        place(tx+i, 12, c, 3 if i%2==0 else 9)
    cred = "raze / AGENTSCII / SOLSTICE v1.0"
    cxp = (W - len(cred))//2
    for i, c in enumerate(cred):
        place(cxp+i, H-4, c, 9 if i%3==0 else 3)
    for x in range(6, W-6):
        place(x, H-5, "\u2500", 1)

for fn in (pass1, pass2, pass3, pass4, pass5):
    fn()

# ---- RENDER -> ANSI, cp437 on disk ----
def sgr(fg=None, bg=0):
    out = []
    if fg is not None: out.append(30+fg if fg < 8 else 90+(fg-8))
    out.append(40+bg)
    return "\x1b[" + ";".join(map(str,out)) + "m"

def render():
    lines = []
    for y in range(H):
        row = ""; cur_fg = None
        for x in range(W):
            cell = grid[y][x]
            ch, fg = (cell[0], cell[1]) if cell else (" ", None)
            if fg != cur_fg:
                row += sgr(fg, 0); cur_fg = fg
            row += ch
        lines.append(row + "\x1b[0m")
    return "\n".join(lines) + "\n\x1b[0m"

with open("scratch/_solstice.ans", "w", encoding="cp437") as f:
    f.write(render())
print("wrote scratch/_solstice.ans")
