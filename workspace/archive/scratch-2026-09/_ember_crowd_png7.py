#!/usr/bin/env python3
# EMBER CROWD v7 -- clean image->ANSI pass. Drop the fine rim + bumpy sub-cell
# detail that chafa's diffusion dither destroys; keep only structure chafa can
# render cleanly: flat warm sky bands, a solid sun disc ABOVE the crowd, a solid
# black stepped silhouette (a row of shoulders/heads) sitting on the horizon.
import numpy as np
from PIL import Image

W, H = 80, 40
PX = 16                      # bigger cells -> chafa keeps structure, less noise
IW, IH = W * PX, H * PX

img = np.zeros((IH, IW, 3), dtype=np.uint8)
yy, xx = np.mgrid[0:IH, 0:IW]
ycol = yy / (IH - 1.0)
xcol = xx / (IW - 1.0)

# ---- SKY: a few clean solid warm bands (dusk atmosphere, not smooth gradient) ----
bands = [
    (0.00, 0.30, (26, 14, 52)),     # deep indigo
    (0.30, 0.52, (96, 30, 84)),     # violet
    (0.52, 0.66, (176, 44, 56)),    # crimson
    (0.66, 0.74, (232, 110, 44)),   # orange at horizon
]
for t0, t1, c in bands:
    m = (ycol >= t0) & (ycol < t1)
    img[m] = c

# ---- SUN: solid bright disc clearly ABOVE the crowd top ----
sun_cx, sun_cy, r = 0.50, 0.60, 0.085
d = np.sqrt((xcol - sun_cx) ** 2 + ((ycol - sun_cy) / 1.4) ** 2)
sun = d < r
img[sun] = [255, 236, 190]

# ---- CROWD: solid black stepped silhouette of shoulders/heads on the horizon ----
horizon = 0.78
# a row of head-bumps: step function so chafa renders clean blocks, not noise
n = 26
step = np.floor(xx / IW * n).astype(int) % 2
top = horizon - 0.012 * step          # alternating high/low -> bumpy head-line
crowd = ycol >= top
img[crowd] = [0, 0, 0]

Image.fromarray(img).save('scratch/_ember_crowd_src7.png')
print('saved', (IW, IH))
