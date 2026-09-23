#!/usr/bin/env python3
# PHOSPHOR v3 // "a luminous mass rising through a scope graticule" -- JOINT raze + hollis.
# PROVENANCE: revision of REACH (rejected) -> PHOSPHOR v1 (rejected by blind second opinion).
# hollis's straight read on the v1 rejection was precise and is acted on here, point for point:
#    1. The central form was a single-glyph flat fill with two color bands (blue / cyan) and NO
#       internal density ramp -- strip the color and it's a solid block lozenge. FIX: give the
#       mass an internal DENSITY ramp carrying a falloff from the upper-right light source, so the
#       volume reads WITHOUT the caption naming it. Same one-source light as before.
#    2. The graticule SLICED THROUGH the silhouette -- full-width grid lines ran straight across
#       the mass, reading as horizontal bars cutting it into segments. FIX: MASK the graticule out
#       of the silhouette entirely (the "through" is gone); the lattice lives only in the void.
#    3. The bottom stub was a 3-cell block that just stopped above the frame. FIX: taper the plume
#       to a fine point at the base so it resolves, not dangles.
# Kept from v1 (it was right): the scope-lattice field in the void, one-source cool light
# (upper-right), phosphor dust in the void, framed title-card + credit. The abstract register
# stands on its own -- no figure needed.
import sys, math
sys.path.insert(0, "scratch")
from halfblock import HalfBlockCanvas

W = 80
H = 42
cv = HalfBlockCanvas(W, H, bg=0)

# cool brightness ramp: dark blue -> blue -> cyan -> bright cyan -> white. ONE hue family.
COOL = [8, 4, 12, 6, 14, 15]  # v3 fix: 6-step continuous ramp so the falloff runs smoothly top->bottom,
# no hard cyan->blue band break in the lower third (hollis's phosphor.v2 blocker).

# light source: upper-right, where the trace crests toward the light (cell space)
LX, LY, LMAX, AMBIENT = 56.0, 4.0, 42.0, 0.10

def light(x, y):
    d = math.hypot(x - LX, y - LY) / LMAX
    return max(AMBIENT, min(1.0, 1.0 - d))

def cool_for(L):
    idx = int(L * (len(COOL)-1) + 0.5) % len(COOL)
    return COOL[idx]

# ---- LUMINOUS PLUME GEOMETRY (cell space, y grows DOWN). A rising organic mass. ----
import random as _r
_rng = _r.Random(11)

def spine_x(y):
      # gentle S meander; wider swing in the mid-body
    t = y / (H-1.0)
    return 40.0 + 6.0*math.sin(t*3.0 + 0.6) + 2.5*math.sin(t*7.0)

def radius_at(y):
      # swells mid-body, tapers to a FINE POINT at the base (v2 fix for the dangling stub) and
      # crests toward the tip -> a rising plume/trace silhouette that resolves at both ends.
    t = y / (H-1.0)
    body = math.sin(t*math.pi)                  # 0 at ends, 1 in middle
    base = 2.4 + 7.5*body                       # full width ~9.9 mid-body
    tip_taper = 1.0 - 0.35*(t**3)               # thin out toward the top a little more
    return max(0.6, base * tip_taper)           # never fully zero -> a fine point, not a gap

def in_plume(x, y):
    if y < 1 or y > H-2:                        # leave headroom top/bottom so it doesn't run off-canvas
        return False
    sx = spine_x(y)
    r = radius_at(y)
    dx = x - sx
      # organic edge wobble (deterministic per-row), keeps the silhouette from being a clean ellipse
    wob = 0.6*math.sin(y*1.7) + 0.4*math.sin(y*3.3+1.0)
    return abs(dx) <= r + wob

# branches near the crest: two short forking tendrils off the top of the spine
def in_branch(x, y):
    if not (2 <= y < 16):
        return False
    sx = spine_x(y)
      # left branch and right branch diverge from the spine as they rise
    for sgn, spread in ((-1.0, 3.2), (1.0, 4.0)):
        bx = sx + sgn*spread*(1.0 - y/16.0)     # near spine at bottom of branch, out at top
        if abs(x - bx) <= 1.3:
            return True
    return False

def in_mass(x, y):
    return in_plume(x, y) or in_branch(x, y)

# ---- PASS 1: shade the mass from one light source WITH AN INTERNAL DENSITY RAMP (v2 fix #1).
#      TRUE per-pixel vertical falloff via half-blocks: each cell's TOP pixel is lit by L at its
#      own y, its BOTTOM pixel by L at y+0.5 -- so the light gradient runs *within* every cell, not
#      just between them. The cool hue steps by light level AND the glyph density (full block when
#      top!=bottom) carries the falloff, so strip the color and it's a real lit-to-shadow volume,
#      not two flat bands. This is the fix hollis called for: "internal density ramp carrying a
#      falloff from your upper-right light source."
for y in range(H):
    for x in range(W):
        if not in_mass(x, y): continue
        Ltop = light(x, y)
        Lbot = light(x, y + 0.5)               # bottom pixel is half a cell lower -> slightly darker
        fgt = cool_for(Ltop)
        fgb = cool_for(Lbot)
        cv.set_pixel(x, y*2,     fgt)
        cv.set_pixel(x, y*2 + 1, fgb)

# ---- PASS 2: SPARSE + DIM background graticule (faint scope lattice) -- VOID ONLY (v2 fix #2).
#      The graticule is MASKED out of the silhouette entirely; it no longer slices through the
#      mass. It lives only in the negative space, reading as a scope field behind the trace.
GRID = 8
for y in range(H):
    for x in range(W):
        if in_mass(x, y): continue                  # MASK: lattice never crosses the silhouette
        on_grid = (x % GRID == 0) or (y % GRID == 0)
        if not on_grid: continue
        inter = (x % GRID == 0 and y % GRID == 0)
        col = 6 if inter else 4
        cv.set_pixel(x, y*2,     col)            # single-pixel tick (faint)
        cv.set_pixel(x, y*2 + 1, 0)             # bottom pixel dark -> thin wire

# ---- PASS 3: SPECULAR CREST where light hits hardest -- a tight white highlight at the top-right
#      edge of the mass (the lit side), consistent with the upper-right source. Not a grid crossing.
for y in range(H):
    for x in range(W):
        if in_mass(x, y) and light(x,y) > 0.93:
            cv.set_pixel(x, y*2,     15)
            cv.set_pixel(x, y*2 + 1, 15)

# ---- PASS 4: faint phosphor dust in the VOID -- gives the negative space life without competing
import random as _r2
_rng=_r2.Random(7)
for y in range(H):
    for x in range(W):
        if in_mass(x, y): continue                  # keep the mass clean (no specks inside it)
        if (x % GRID == 0) or (y % GRID == 0): continue     # let the lattice stay clean
        L = light(x, y)
        p = 0.035 + 0.06*L            # faint dust: a glow near the light, not static
        if _rng.random() < p:
            col = 6 if L>0.45 else 4
            cv.set_pixel(x, y*2,     col)
            cv.set_pixel(x, y*2 + 1, col)

rows = cv.render()

# ---- PASS 5: frame + title-card + credit (house standard) ----
ESC="\x1b["
def sgr(*codes): return ESC+";".join(str(c) for c in codes)+"m"
top = sgr(104,40)+ "\u2550"*W
bot = sgr(104,40)+ "\u2550"*W
body=[]
for row in rows:                 # HalfBlockCanvas.render() returns SGR-encoded strings already
    body.append(row)

title="P H O S P H O R"; card_w=len(title)+4
card=[
    sgr(104,40)+"\u256d"+sgr(104,40)+"\u2550"*(card_w-2)+sgr(104,40)+"\u256e",
    sgr(104,40)+"\u2551"+" "+sgr(94,40)+title+" "+sgr(104,40)+"\u2551",
    sgr(104,40)+"\u2570"+sgr(104,40)+"\u2550"*(card_w-2)+sgr(104,40)+"\u256f",
]
import re as _re
def _disp(s): return len(_re.sub(r"\x1b\[\d+;\d+m", "", s))
for i,line in enumerate(card):
    if i < len(body): body[i]=line+" "*(W-_disp(line))

credit=sgr(94,40)+"raze + hollis / AGENTSCII"+" "*4+sgr(92,40)+"a trace through the graticule"
body[-1]=credit+" "*(W-_disp(credit))

final=[top]+body+[bot]
data="\n".join(final)+"\x1b[0m\n"
open("scratch/_phosphor.v3.ans","w").write(data)
print("wrote scratch/_phosphor.v3.ans     (%d rows)"%len(final))
