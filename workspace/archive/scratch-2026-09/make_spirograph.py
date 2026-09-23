#!/usr/bin/env python3
# SPIROGRAPH v1 -- AGENTSCII (raze). A phosphor SPIROGRAPH field. Third member of the "parametric
# curve" mini-family: same phosphor-decay trace, same 16-color house hue wheel cycled along the
# curve parameter, same white-hot nodes and framed sig block -- but a DIFFERENT curve family
# (interlaced hypotrochoid + epitrochoid gear-lace) AND a different backdrop (pure black void; the
# lace itself is the structure, no graticule/rings), so it reads as its own "scope."
#
# KEY: a gear curve closes only after t runs 0 -> 2*pi * (r/gcd(R,r)) -- one turn of t is just a
# tiny arc. We trace each gear's FULL closed period, center it on its own centroid (so no lopsided
# drift), then overlay several gears at rotation offsets so the whole lace is radially balanced into
# a centered mandala-like rosette. Standard CENTERED formulas, pen offset d as fraction of rolling r.

import math
from curve_common import *

out = []
inten = [[0.0]*W for _ in range(H)]
huebuf = [[-1.0]*W for _ in range(H)]

# gear-lace: (R, r, d_frac, kind, amp_scale, rot_offset). coprime R,r -> clean symmetric rosette.
GEARS = [
        (13.0, 5.0, 0.60, "hypo", 0.94, 0.0),       # 13-cusp rosette -- dominant interlace
        (11.0, 4.0, 0.72, "epi",    0.84, math.pi/6.0),   # 11-cusp counter-weave
        (7.0,   3.0, 0.55, "hypo", 0.70, math.pi/3.0),    # 7-cusp overlay lace
]

AX = CX * 0.96
AY = CY * 0.94

for (R, r, dfrac, kind, amp, rot) in GEARS:
    g = math.gcd(int(R), int(r))
    revs = int(r) // g                              # full closed period = revs revolutions of t
    if kind == "hypo":
        roll = R - r; f = (R - r) / r
    else:
        roll = R + r; f = (R + r) / r
    d = dfrac * r

     # pass 1: sample the full closed period in raw unit space, find centroid + extent
    SAMPLES = 4000 * revs
    pts = []
    for i in range(SAMPLES):
        t = 2.0 * math.pi * i / SAMPLES
        if kind == "hypo":
            x = roll * math.cos(t) + d * math.cos(f * t)
            y = roll * math.sin(t) - d * math.sin(f * t)
        else:
            x = roll * math.cos(t) - d * math.cos(f * t)
            y = roll * math.sin(t) + d * math.sin(f * t)
        pts.append((t, x, y))
    cxm = sum(p[1] for p in pts) / len(pts)         # centroid -> center the gear on origin
    cym = sum(p[2] for p in pts) / len(pts)
    maxx = max(abs(p[1] - cxm) for p in pts)
    maxy = max(abs(p[2] - cym) for p in pts)
    sc = min(AX / maxx, AY / maxy)                  # uniform scale -> preserve true rosette shape

     # pass 2: stamp into the field (rotated by `rot`), phosphor accumulation + first-hit hue lock
    cr = math.cos(rot); sr = math.sin(rot)
    for (t, x, y) in pts:
        ux = (x - cxm) * sc; uy = (y - cym) * sc
        rx = ux * cr - uy * sr                      # rotate about field center
        ry = ux * sr + uy * cr
        cx = int(round(CX + rx)); cy = int(round(CY + ry))
        if 0 <= cx < W and 0 <= cy < H:
            inten[cy][cx] += 1.0
            ph = t * 0.7 + R                         # hue cycles along the gear turn
            if huebuf[cy][cx] < 0:
                huebuf[cy][cx] = ph

imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 3.4

out.append(sgr(40, 97))                              # bg black default
phosphor_render(inten, huebuf, imax, GLOW, backdrop_void, out)
sig_block(out, "SPIROGRAPH v1.0 -- phosphor gear-lace")
out.append(RESET)

text = "\n".join(out)
with open("scratch/raze-spirograph.ans", "w", encoding="cp437") as f:
    f.write(text)

hygiene_gate("scratch/raze-spirograph.ans")
