#!/usr/bin/env python3
# ROSE v1 -- AGENTSCII (raze). A phosphor POLAR rose-curve field. Companion to LISSAJOUS in the
# "parametric curve" mini-family: same phosphor-decay trace, same 16-color house hue wheel cycled
# along the curve parameter, same white-hot nodes and framed sig block -- but a DIFFERENT curve
# family (polar r=cos(k*theta) petal bloom) AND a different backdrop (faint concentric polar rings
# instead of a Cartesian graticule), so it reads as its own "scope," not a copy of lissajous.

import math
from curve_common import *

out = []
inten = [[0.0]*W for _ in range(H)]
huebuf = [[-1.0]*W for _ in range(H)]

# rose harmonics: (k, phase, amp_scale). k odd -> k petals; even -> 2k petals.
ROSES = [
    (3, 0.0, 0.90),       # 3-petal bloom -- the dominant figure
    (5, math.pi/5.0, 0.78),# 10-petal weave
    (7, math.pi/7.0, 0.64),# 7-petal lace
    (11, math.pi/3.0, 0.50),# fine 22-petal overlay
]

AX = CX * 0.94
AY = CY * 0.92
SAMPLES = 6000            # dense -- polar curves wind fast, need more samples to stay smooth

for (k, phase0, amp) in ROSES:
    R = min(AX, AY) * amp
    for i in range(SAMPLES):
        th = 2.0 * math.pi * i / SAMPLES
        r = R * math.cos(k * th + phase0)      # signed radius -> symmetric petal bloom
        x = CX + r * math.cos(th)
        y = CY + r * math.sin(th)
        cx = int(round(x)); cy = int(round(y))
        if 0 <= cx < W and 0 <= cy < H:
            inten[cy][cx] += 1.0
            ph = th * 2.5 + k                  # hue cycles fast along the petal
            if huebuf[cy][cx] < 0:            # first-hit hue lock (matches lissajous)
                huebuf[cy][cx] = ph

imax = max(max(v for row in inten for v in row), 1e-9)
GLOW = 3.2

out.append(sgr(40, 97))                        # bg black default
phosphor_render(inten, huebuf, imax, GLOW, backdrop_rings, out)
sig_block(out, "ROSE v1.0 -- phosphor polar bloom")
out.append(RESET)

text = "\n".join(out)
with open("scratch/raze-rose.ans", "w", encoding="cp437") as f:
    f.write(text)

hygiene_gate("scratch/raze-rose.ans")
