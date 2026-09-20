#!/usr/bin/env python3
# _substrate -- "SUBSTRATE // a circuit mandala, lit from its own core"
# SOLO raze.  register: hardware-substrate field, BILATERALLY SYMMETRIC via mirror().
#
# PROVENANCE: came out of a random_direction roll (subject = circuit/hardware-substrate
#   field; technique constraint = canvas.mirror() for bilateral symmetry -- face/creature/mandala;
#   palette lean = muted/dim, low-saturation throughout). Taken straight. The catalog has machines
#   as 3D BODIES (reactor/turbine/console/ghost_engine) but nothing SYMMETRIC / mandala -- this is
#   the missing register: a circuit substrate read as a radial mandala, not an object.
#
# METHOD (house passes, METHODOLOGY.md):
#  P1 silhouette: concentric rings + radial spokes of trace, painted on the LEFT HALF only.
#  P2 light: ONE central core light L(x,y) at canvas center -- every surface shaded through the SAME
#    field via density ramp '█▓▒░', so brightness falls off radially from the hot heart to dim edges.
#    This is the "lit from its own core" idea: emissive, not an external sun.
#  P3 detail: nodes (pads) at ring/spoke intersections as bright dots; trace strands follow the
#    radial direction (strand_shade), alternating dim hues -- grain, not a flat wash.
#  P4 texture: faint substrate scatter over the whole field so the negative space reads as a PCB
#    board, not flat black (Pass 5).
#  P5 frame + title card (Pass 6) + house sig block via write_ans(add_sig=True).
#  mirror(axis='v') folds the painted left half onto the right -- bilateral symmetry for free.
#
# MEDIUM HONESTY: muted/dim palette = base ANSI codes {1,2,3,4,5,6,7} (dim blue/green/yellow/
#   magenta/cyan/red/white) + a single hot accent (bright amber 11 / bright white 15) reserved for
#   the core heart only. Low saturation throughout per the roll; the warm core is the one loud note.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, mirror, texture_fill, strand_shade, write_ans, RAMP

SEED = 7
W, H = 80, 42
cv = Canvas(W, H)
CX, CY = W // 2, H // 2           # core at center -- the light source

# ---- P1+P2: rings & spokes on the LEFT HALF, shaded by ONE central light field ----
def L(x, y):
    """Emissive core light: 1.0 at the heart, falling off radially. Single source."""
    d = math.hypot(x - CX, y - CY)
    lmax = max(CX, CY) * 1.25
    return max(0.0, 1.0 - d / lmax)

def ramp_for(v):
    """Map light value -> density char (bright core dense, dim edge sparse)."""
    v = min(1.0, max(0.0, v))
    i = int(v * (len(RAMP) - 1) + 0.5)
    return RAMP[i]

# concentric rings: radii in cells; each ring is a thin annulus of trace glyphs
RING_RADII = [3, 6, 9, 12, 15, 18, 21]
SPOKES = 16                   # radial spokes (full circle worth; left half paints half)

def on_ring(x, y, r, tol=0.7):
    d = math.hypot(x - CX, y - CY)
    return abs(d - r) < tol

# paint rings -- only x < CX (left half); mirror folds it right
for r in RING_RADII:
    for x in range(0, CX):
        for y in range(H):
            if on_ring(x, y, r):
                v = L(x, y)
                 # ring hue: cool steel/cyan substrate, dimmer with radius (further from core = cooler/dimmer)
                base = 4 if r % 2 == 0 else 6           # dim blue / dim cyan alternate
                ch = ramp_for(v)
                cv.set(x, y, ch, fg=base)

# radial spokes -- short trace segments along each spoke angle
for s in range(SPOKES):
    ang = (s / SPOKES) * 2 * math.pi
     # only paint the left half of each spoke; mirror handles the rest
    for t in range(3, 21):
        x = int(CX + math.cos(ang) * t)
        y = int(CY + math.sin(ang) * t * 0.95)          # slight vertical squash -> oval mandala
        if not cv.in_bounds(x, y):
            continue
        if x >= CX:
            continue
        v = L(x, y)
        ch = ramp_for(v)
        cv.set(x, y, ch, fg=3 if (s % 2 == 0) else 5)    # dim yellow / dim magenta spokes

# ---- P3: nodes (pads) at ring/spoke intersections -- bright dots on the lit side ----
for s in range(SPOKES):
    ang = (s / SPOKES) * 2 * math.pi
    for r in RING_RADII[1::2]:
        x = int(CX + math.cos(ang) * r)
        y = int(CY + math.sin(ang) * r * 0.95)
        if not cv.in_bounds(x, y) or x >= CX:
            continue
        v = L(x, y)
         # a pad reads as a small bright square; brightness tracks the core light
        fg = 11 if v > 0.7 else (7 if v > 0.45 else 8)    # amber near core -> white mid -> dim out
        cv.set(x, y, '\u2588', fg=fg)

# ---- the hot heart: a small emissive core at center ----
for x in range(CX - 1, CX + 1):
    for y in range(CY - 1, CY + 1):
        if cv.in_bounds(x, y):
            cv.set(x, y, '\u2588', fg=15)

# ---- P4: substrate texture over the WHOLE field (PCB board, not flat black) ----
def in_field(x, y):
    return 0 <= x < W and 0 <= y < H
texture_fill(cv, in_field, fg=8, density=0.12, seed=3)    # faint dim-white solder-mask scatter

# ---- fold the left half onto the right: bilateral symmetry ----
mirror(cv, axis='v')

# re-stamp the heart after mirror (center column may have been overwritten by its own mirror)
for x in range(CX - 1, CX + 1):
    for y in range(CY - 1, CY + 1):
        if cv.in_bounds(x, y):
            cv.set(x, y, '\u2588', fg=15)

# ---- P5: frame + title card (Pass 6) ----
C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=11, bg=0, fill=False)   # outer rule (amber)
C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=4, bg=0, fill=False)    # inner dim-blue rule

title = "SUBSTRATE // a circuit mandala, lit from its own core"
tx = (W - len(title)) // 2
for i, ch in enumerate(title):
    cv.set(tx + i, 1, ch, 11, 0)

out = []
cv.render(out)
write_ans("scratch/_substrate.ans", out, title="SUBSTRATE v1.0", handles="raze")
print("wrote scratch/_substrate.ans -- SUBSTRATE circuit mandala; rows:", len(out))
