#!/usr/bin/env python3
# REACH v4 // "a hand reaching through something" -- solo raze.
# PROVENANCE: random_direction roll -> subject "a hand reaching through something",
# technique "curve_common.py phosphor_render() scope aesthetic", palette "cool tones dominant".
#
# v4: switched from HalfBlockCanvas to the standard Canvas (0-15 indices, uniform per-cell
# shading) -- half-block cross-hue at silhouette edges was emitting fg=96 (bright-magenta)
# where top pixel=cyan + bottom=blue, a warm artifact in an otherwise cool piece. The hand is
# large enough that whole-cell shading is clean; the resolution problem half-blocks solve is for
# tiny features (eyes/cranium), not a full hand. Also fixed title text 114->94 (out of range).
import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas

W = 80
H = 40
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

# cool brightness ramp: dark blue -> blue -> cyan -> bright cyan -> white. ONE hue family.
COOL = [4, 6, 12, 15]

# light source: upper-right, above the hand (cell space)
LX, LY, LMAX, AMBIENT = 58.0, 3.0, 40.0, 0.12

def light(x, y):
    d = math.hypot(x - LX, y - LY) / LMAX
    return max(AMBIENT, min(1.0, 1.0 - d))

def cool_for(L):
    idx = int(L * (len(COOL)-1) + 0.5) % len(COOL)
    return COOL[idx]

# ---- HAND GEOMETRY (cell space, y grows DOWN). Reaching up + slightly forward. ----
PALM_CX, PALM_CY = 38.0, 24.0

def in_palm(x, y):
    dx = (x - PALM_CX)/11.0
    dy = (y - PALM_CY)/13.0
    return dx*dx + dy*dy <= 1.0

# fingers: base at palm top (~y=12), tips spread up-outward. (base_x, tip_x, length)
FINGERS = [(34,30,11),(38,38,13),(42,46,12),(45,51,9)]      # index middle ring pinky
def in_finger(x, y):
    for bx,tx,ln in FINGERS:
        for i in range(ln+1):
            t=i/ln; cx=bx+(tx-bx)*t; w=2.4*(1.0-0.30*t); cy=12-int(t*ln)
            if abs(y-cy)<=1 and abs(x-cx)<=w+0.3: return True
    return False

def in_thumb(x, y):
     # off the LEFT side of palm, angling out-down
    for i in range(11):
        t=i/10.0; tx=28-int(t*9); ty=24+int(t*7); w=2.2*(1-0.3*t)
        if abs(y-ty)<=1 and abs(x-tx)<=w+0.3: return True
    return False

def in_wrist(x, y):
     # joined to palm base, down toward bottom
    return 36 <= y < H and 32 <= x < 45

def in_hand(x, y):
    return in_palm(x,y) or in_finger(x,y) or in_thumb(x,y) or in_wrist(x,y)

# ---- PASS 1: shade hand from one light source (volume), uniform per cell ----
for y in range(H):
    for x in range(W):
        if in_hand(x, y):
            L = light(x, y)
            cv.set(x, y, ch='\u2588', fg=cool_for(L))

# ---- PASS 2: SPARSE + DIM background graticule (faint scope lattice) ----
GRID = 8
for y in range(H):
    for x in range(W):
        if in_hand(x, y): continue
        on_grid = (x % GRID == 0) or (y % GRID == 0)
        if not on_grid: continue
        inter = (x % GRID == 0 and y % GRID == 0)
        cv.set(x, y, ch='\u2591', fg=6 if inter else 4)

# ---- PASS 3: the "through" -- grid continues ACROSS the hand body, BRIGHTER than bg ----
for y in range(H):
    for x in range(W):
        if not in_hand(x, y): continue
        on_grid = (x % GRID == 0) or (y % GRID == 0)
        if not on_grid: continue
        inter = (x % GRID == 0 and y % GRID == 0)
        cv.set(x, y, ch='\u2588', fg=12 if inter else 6)

# ---- PASS 4: tight specular crest where light hits hardest ----
for y in range(H):
    for x in range(W):
        if in_hand(x, y) and light(x,y) > 0.93:
            cv.set(x, y, ch='\u2588', fg=15)

# ---- PASS 4b: faint phosphor dust in the VOID -- gives the negative space life
# without competing with the hand. Deterministic scatter of very dim cyan/blue ticks,
# denser toward the light source (phosphor glow falloff). Keeps the scope aesthetic but
# kills the dead-flat black that a pure lattice leaves behind.
import random as _r
_rng=_r.Random(7)
for y in range(H):
    for x in range(W):
        if in_hand(x, y): continue
        # already on a grid line? skip -- let the lattice stay clean
        if (x % GRID == 0) or (y % GRID == 0): continue
        L = light(x, y)
        p = 0.10 + 0.18*L            # dust denser near the light
        if _rng.random() < p:
            cv.set(x, y, ch='.', fg=6 if L>0.45 else 4)

# ---- PASS 5: frame + title-card + credit (house standard) ----
out=[]; ESC="\x1b["
def sgr(*codes): return ESC+";".join(str(c) for c in codes)+"m"
top = sgr(104,40)+ "\u2550"*W
bot = sgr(104,40)+ "\u2550"*W
body=[]
for row in cv.cells:
    parts=[]; last=None
    for ch,fg,bg in row:
        if (fg,bg)!=last:
            parts.append(sgr(90+(fg&7) if fg>7 else 30+fg, 100+(bg&7) if bg>7 else 40+bg))
            last=(fg,bg)
        parts.append(ch)
    body.append("".join(parts))

title="R E A C H"; card_w=len(title)+4
card=[
    sgr(107,40)+"\u256d"+sgr(104,40)+"\u2550"*(card_w-2)+sgr(107,40)+"\u256e",
    sgr(104,40)+"\u2551"+" "+sgr(94,40)+title+" "+sgr(104,40)+"\u2551",
    sgr(107,40)+"\u2570"+sgr(104,40)+"\u2550"*(card_w-2)+sgr(107,40)+"\u256f",
]
for i,line in enumerate(card):
    if i < len(body): body[i]=line+" "*(W-len(line))

credit=sgr(94,40)+"raze / AGENTSCII"+" "*8+sgr(92,40)+"reach through the lattice"
body[-1]=credit+" "*(W-len(credit))

final=[top]+body+[bot]
data="\n".join(final)+"\x1b[0m\n"
open("scratch/_reach.ans","w").write(data)
print("wrote scratch/_reach.ans     (%d rows)"%len(final))
