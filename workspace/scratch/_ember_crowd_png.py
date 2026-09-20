#!/usr/bin/env python3
# EMBER CROWD -- dusk landscape, built as a real PNG then chafa'd to 16-color ANSI.
# Sidesteps the per-cell "no dim-warm color" limit by letting diffusion dithering
# fake the warm gradient via block density (the honest ceiling the .note flagged).
import numpy as np
from PIL import Image

W, H = 80, 42            # char cells
PX = 12                  # px per cell -> image is W*PX x H*PX
IW, IH = W * PX, H * PX

img = np.zeros((IH, IW, 3), dtype=np.uint8)
Y, X = np.mgrid[0:IH, 0:IW]
ny = Y / (IH - 1.0)              # 2D vertical axis (for sun/crowd indexing)
nx = X / (IW - 1.0)

# ---- SKY: vertical dusk gradient, warm-dominant (built from a 1D column) ----
def lerp(a, b, t): return a + (b - a) * t
ycol = np.arange(IH) / (IH - 1.0)            # 1D, shape (IH,)
sky = np.zeros((IH, IW, 3), dtype=np.float64)
stops = [
    (0.00, (18, 12, 40)),        # deep indigo night
    (0.35, (60, 24, 70)),        # violet
    (0.55, (150, 40, 60)),       # crimson band
    (0.68, (220, 90, 40)),       # orange
    (0.76, (245, 160, 60)),      # amber glow at horizon
]
for i in range(len(stops) - 1):
    t0, c0 = stops[i]; t1, c1 = stops[i + 1]
    mask = ((ycol >= t0) & (ycol < t1)).astype(np.float64)
    col = np.clip((ycol - t0) / max(t1 - t0, 1e-6), 0, 1)
    for ch in range(3):
        val = lerp(c0[ch], c1[ch], col)            # 1D, shape (IH,)
        sky[:, :, ch] += (mask * val)[:, None]      # broadcast across width

img[..., 0] = np.clip(sky[..., 0], 0, 255)
img[..., 1] = np.clip(sky[..., 1], 0, 255)
img[..., 2] = np.clip(sky[..., 2], 0, 255)

# ---- SUN: bright disc clearly ABOVE the crowd silhouette ----
sun_cx, sun_cy = 0.50, 0.62        # just above horizon (~0.74)
r = 0.10
d = np.sqrt((nx - sun_cx) ** 2 + ((ny - sun_cy) / 1.3) ** 2)
sun = np.clip(1.0 - d / r, 0, 1) ** 1.5
img[..., 0] = np.clip(img[..., 0].astype(np.int16) + sun * 230, 0, 255).astype(np.uint8)
img[..., 1] = np.clip(img[..., 1].astype(np.int16) + sun * 200, 0, 255).astype(np.uint8)
img[..., 2] = np.clip(img[..., 2].astype(np.int16) + sun * 150, 0, 255).astype(np.uint8)

# ---- CROWD: bumpy black silhouette of many heads/shoulders along lower third ----
horizon = 0.74
xcol = np.arange(IW) / (IW - 1.0)
head_y = horizon + 0.012 * np.sin(xcol * 38.0) + 0.006 * np.sin(xcol * 91.0 + 1.7) \
              + 0.004 * np.sin(xcol * 157.0 + 0.3)
for i in range(0, IW, PX):
    cx = (i + PX // 2) / IW
    phase = (i // PX) * 1.3
    hy = horizon + 0.018 * np.sin(cx * 38.0 + phase)
    for j in range(IW):
        dx = abs(j - cx * IW) / (IW * 0.022)
        if dx < 1.0:
            bump = (1 - dx ** 2) ** 1.2
            yy = hy - bump * 0.030
            for y in range(IH):
                if ycol[y] >= yy and ycol[y] < horizon + 0.06:
                    img[y, j] = [0, 0, 0]

# ---- backlit RIM on the crowd top edge (warm light catching shoulders/heads) ----
for y in range(IH):
    for x in range(IW):
        if abs(ycol[y] - head_y[x]) < 0.012 and ycol[y] > horizon - 0.02:
            img[y, x] = np.clip(img[y, x].astype(np.int16) + [255, 150, 70], 0, 255).astype(np.uint8)

# ---- dim receding GROUND below the crowd (true black field, sparse warm glints) ----
for y in range(IH):
    if ycol[y] >= horizon + 0.06:
        img[y, :] = [0, 0, 0]
rng = np.random.default_rng(7)
for _ in range(40):
    gx = rng.integers(0, IW); gy = rng.integers(int((horizon + 0.06) * IH), IH - 1)
    img[gy, gx] = [120, 50, 20]

Image.fromarray(img).save('scratch/_ember_crowd_src.png')
print('saved scratch/_ember_crowd_src.png', (IW, IH))
