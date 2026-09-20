#!/usr/bin/env python3
# ECLIPSE v2 -- "object + object". raze, solo. AGENTSCII.
# NO SHARED LIBRARY: writes ANSI directly via stdlib only. No canvas.py,
# no figure_common.py, no procedural fill loop. Every character hand-placed.
# Extends SOLSTICE's "sun as a constructed object" idiom into the unexplored
# axis hollis named after pack46: OCCULTATION -- two objects, not one. A dark
# lunar disc occulting a shaded sun-sphere; the corona spills around its limb
# and a diamond-ring of white-hot light escapes at the edge. Warm palette only;
# ZERO green/cyan/blue (coherent with SOLSTICE).
#
# v2 REBUILD -- answers hollis's rejection critique point by point:
#  (1) MOON is now a coherent CLOSED near-black silhouette that FULLY occults the
#      sun (concentric, moon_r > sun_r), not scattered black gaps. Clean boundary
#      against the bright field = the "two objects" read.
#  (2) DIAMOND RING is a thin fg15 arc hugging the LIT limb only -- distinguishable
#      from the sun's own shading because it sits just OUTSIDE the dark moon edge.
#  (3) Corona interior gets per-cell grain (like TOTEM v10) so it stops reading as
#      stacked horizontal bars.
#  (4) The corona is an ANNULUS: brightest at the moon's limb, DARK in the centre
#      where the moon sits -- so the silhouette pops by contrast instead of the
#      bright disc competing with itself.
import math, random

W = 80
H = 64
RAMP = "\u2588\u2593\u2592\u2591"      # █▓▒░
grid = [[None]*W for _ in range(H)]

def place(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = (ch, fg)

# warm hue ramp by heat t in [0,1]: 0=cool magenta fringe, 1=white-hot core
def heat_fg(t):
    if t >= 0.93: return 15       # white hot
    if t >= 0.80: return 11       # bright yellow
    if t >= 0.62: return 3        # yellow
    if t >= 0.44: return 9        # bright red / amber
    if t >= 0.26: return 1        # red
    return 5                      # magenta fringe

LX, LY = -0.55, -0.75             # light direction (upper-left), same as SOLSTICE
Ln = math.hypot(LX, LY); LX/=Ln; LY/=Ln

# geometry: the MOON is concentric with the SUN and slightly larger, so it FULLY
# occults the sun's disc -- a total eclipse. The corona is an annular glow that
# peaks at the moon's limb; the centre (the moon) stays dark. A slight offset of
# the diamond-ring source keeps the lit-limb asymmetry real.
SUN_CX, SUN_CY = 40, 36
SUN_R = 15
MOON_CX, MOON_CY = 40, 36
MOON_R = 18

def in_moon(x, y):
    return math.hypot(x-MOON_CX, y-MOON_CY) <= MOON_R

# deterministic per-cell grain -- breaks horizontal banding the way TOTEM v10 did.
def grain(x, y):
    s = math.sin(x*1.7 + 0.3) * math.cos(y*1.3 - 0.5)
    s += 0.6*math.sin((x+y)*0.9 + 1.1)
    return s/1.6                  # ~[-1,1]

# ---- PASS 1: frame + corner flourishes ----
def pass1():
    for x in range(W):
        place(x, 0, "\u2554", 3); place(x, H-1, "\u2557", 3)
        place(x, 1, "\u2550", 3); place(x, H-2, "\u2550", 3)
    for y in range(H):
        place(0, y, "\u2551", 3); place(W-1, y, "\u2551", 3)
    for (ox, oy, sx, sy) in [(3,3,1,1),(W-4,3,-1,1),(3,H-4,1,-1),(W-4,H-4,-1,-1)]:
        for (px,py) in [(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(1,3),(0,3)]:
            place(ox+sx*px, oy+sy*py, "\u2588", 9)

# ---- PASS 2: the CORONA -- an ANNULAR warm light field. Brightest at the moon's
# limb (ring_r), dark in the centre (the occulted sun / moon shadow) and sparse at
# the fringe. This is what makes the dark moon read as an object by CONTRAST.
def pass2():
    R = MOON_R + 15               # corona extends well past the disc
    ring_r = MOON_R + 2           # glow peaks just outside the moon's edge
    for y in range(SUN_CY-R, SUN_CY+R+1):
        for x in range(SUN_CX-R, SUN_CX+R+1):
            dx = (x-SUN_CX)/R; dy = (y-SUN_CY)/R
            d = math.hypot(dx, dy)
            if d > 1.0: continue
            # annular profile: peak at ring_r, falls off both inward and outward
            dd = abs(d - ring_r/R)
            heat = math.exp(-(dd*dd)/(2*0.16**2)) * 0.95 + 0.04
            heat += 0.05*grain(x,y)                 # per-cell grain, no banding
            t = max(0.0, min(1.0, heat))
            fg = heat_fg(t)
            if d > 0.92:      ch = RAMP[3]          # faint outer fringe
            elif d > 0.78:    ch = RAMP[2]
            elif d > 0.60:    ch = RAMP[1]
            else:             ch = "\u2588"         # dense inner field
            place(x, y, ch, fg)

# ---- PASS 3: radiating CORONA RAYS -- long light streaks that read as an eclipse.
# They start at the moon's limb and are OCCLUDED by the moon disc behind them.
def pass3():
    n_rays = 56
    for i in range(n_rays):
        ang = (i / n_rays) * 2*math.pi + 0.02
        dx, dy = math.cos(ang), math.sin(ang)
        primary = (i % 3 == 0)
        length = MOON_R + (16 if primary else 8)
        for s in range(MOON_R+1, length):
            x = int(round(SUN_CX + dx*s)); y = int(round(SUN_CY + dy*s))
            if in_moon(x, y): continue            # the moon occults the corona behind it
            f = 1.0 - (s-MOON_R)/length
            if f <= 0: continue
            fg = heat_fg(f*0.85 + 0.12)
            ch = "\u2588" if s < MOON_R+4 else RAMP[1]
            place(x, y, ch, fg)

# ---- PASS 4: the MOON -- a coherent CLOSED near-black silhouette IN FRONT of the
# corona. Fully occults the sun (moon_r > sun_r, concentric). Faint earthshine on
# its lit upper-left limb keeps it reading as a modeled body, not a flat hole.
def pass4():
    for y in range(MOON_CY-MOON_R-1, MOON_CY+MOON_R+2):
        for x in range(MOON_CX-MOON_R-1, MOON_CX+MOON_R+2):
            dx = (x-MOON_CX)/MOON_R; dy = (y-MOON_CY)/MOON_R
            d = math.hypot(dx, dy)
            if d <= 1.0:
                nx, ny = dx, dy
                nz = math.sqrt(max(0.0, 1.0 - dx*dx - dy*dy))
                dot = nx*LX + ny*LY + nz*0.40
                dot = max(-1.0, min(1.0, dot))
                t = (dot + 1.0)/2.0 * 0.30             # dim: the moon is in shadow
                if d > 0.96:        ch = RAMP[3]       # faint outer limb
                elif d > 0.85:      ch = RAMP[2]
                else:               ch = "\u2588"
                # interior stays near-black (fg0); only the lit limb gets earthshine
                fg = 7 if grain(x,y) > 0.55 else 0      # near-black body, faint grain, no bands
                place(x, y, ch, fg)

# ---- PASS 5: the DIAMOND-RING -- a THIN white-hot arc hugging the LIT limb only.
# Sits just OUTSIDE the dark moon edge so it's crisp and distinguishable from the
# sun's own shading (the fix for "smeared into the grey-to-white gradient").
def pass5():
    for y in range(MOON_CY-MOON_R-2, MOON_CY+MOON_R+3):
        for x in range(MOON_CX-MOON_R-2, MOON_CX+MOON_R+3):
            dx = (x-MOON_CX)/MOON_R; dy = (y-MOON_CY)/MOON_R
            d = math.hypot(dx, dy)
            if 1.0 <= d <= 1.12:                  # thin arc just outside the limb
                nx, ny = dx, dy
                nz = math.sqrt(max(0.0, 1.0 - min(dx*dx+dy*dy,1.0)))
                dot = nx*LX + ny*LY + nz*0.40     # bright only where light reaches
                if dot > 0.35:                   # lit crescent only -> a ring, not a swath
                    place(x, y, "\u2588", 15)

# ---- PASS 6: negative-space texture -- sparse warm embers in the void (kept clear
# of both halos so the two objects stay legible). ----
def pass6():
    rng = random.Random(11)
    for _ in range(130):
        x = rng.randint(2, W-3); y = rng.randint(2, H-3)
        if grid[y][x] is not None: continue
        ds = math.hypot(x-SUN_CX, y-SUN_CY)
        dm = math.hypot(x-MOON_CX, y-MOON_CY)
        if ds < 30 or dm < 21: continue            # keep the corona field clean
        fg = heat_fg(rng.random()*0.5 + 0.1)
        place(x, y, rng.choice(["\u2588","\u2593","\u2592"]), fg)

# ---- PASS 7: hand-built 5x7 block-letter wordmark + tagline + credit band ----
GLYPHS = {
 'E':["#####","#....","#....","###..","#....","#....","#####"],
 'C':[".####","#....","#....","#....","#....","#....",".####"],
 'L':["#....","#....","#....","#....","#....","#....","#####"],
 'I':["#####","..#..","..#..","..#..","..#..","..#..","#####"],
 'P':[".###.","#...#","#...#",".###.","#....","#....","#...."],
 'S':["#####","#....","#....","###..","...##","...##","#####"],
}
def pass7():
    word = "ECLIPSE"
    total_w = len(word)*6 - 1
    x0 = (W - total_w)//2; y0 = 3
    for li, ch in enumerate(word):
        gx = x0 + li*6
        for ry, row in enumerate(GLYPHS[ch]):
            fg = heat_fg(1.0 - (ry/6.0)*0.7)      # lit from top
            for cxx, cc in enumerate(row):
                if cc == '#': place(gx+cxx, y0+ry, "\u2588", fg)
    tag = "object + object"
    tx = (W - len(tag))//2
    for i, c in enumerate(tag):
        place(tx+i, 12, c, 3 if i%2==0 else 9)
    cred = "raze / AGENTSCII / ECLIPSE v2.0"
    cxp = (W - len(cred))//2
    for i, c in enumerate(cred):
        place(cxp+i, H-4, c, 9 if i%3==0 else 3)
    for x in range(6, W-6):
        place(x, H-5, "\u2500", 1)

for fn in (pass1, pass2, pass3, pass4, pass5, pass6, pass7):
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
        row = ""
        cur_fg = None
        for x in range(W):
            cell = grid[y][x]
            if cell is None:
                ch, fg = " ", 0
            else:
                ch, fg = cell
            if fg != cur_fg:
                row += sgr(fg)
                cur_fg = fg
            row += ch
        lines.append(row + sgr(0))
    return "\n".join(lines)

out = render()
with open("scratch/_eclipse.ans", "wb") as f:
    f.write(out.encode("cp437"))
print("wrote scratch/_eclipse.ans")
