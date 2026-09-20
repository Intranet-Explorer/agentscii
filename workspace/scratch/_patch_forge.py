#!/usr/bin/env python3
# hollis -- FORGE joint pass (pack34 direction #1, raze's build).
# Three improvements raze flagged in the note, taken as a coherent single pass:
#   (a) EMBER CASCADE rises ALONG the channel centerlines instead of uniform-random x,
#       so the upward tail reads as connected flow out of each magma ridge.
#   (b) CHANNEL WANDER gets more amplitude/phase variation so the 7 ridges read less like a comb.
#   (c) TOP TITLE CARD matching MONOLITH's framing (framed_into + warm subtitle), since FORGE
#       is the explicit mirror of MONOLITH and should frame identically.
# Reuses raze's engine verbatim; only the channel loop, ember pass, and emit splice change.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, render, sig_block, c, RAMP, W

OUT = "scratch/_forge.ans"
H2 = 64
POOL_TOP = 38
CX = W / 2.0
RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}

WARM = [15, 11, 9, 3, 1]   # white-hot / bright-yellow / bright-red / red / dark-red -- NO green/cyan

def heat_to_density(h):
    i = int((1.0 - max(0.0, min(1.0, h))) * (len(RAMP) - 1))
    return RAMP[min(len(RAMP) - 1, i)]

def warm_fg(h, phase):
    pos = int((1.0 - max(0.0, min(1.0, h))) * len(WARM)) + int(phase)
    return WARM[pos % len(WARM)]

random.seed(7)
_NOISE = [[random.random() for _ in range(W)] for _ in range(H2)]
def noise(x, y):
    return _NOISE[y][x]

cv = new_canvas(H2, W)
for y in range(H2):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# PASS 1 -- MOLTEN POOL (unchanged from raze's build).
for y in range(POOL_TOP, H2 - 4):
    for x in range(W):
        d = min(1.0, abs(x - CX) / (W * 0.5))
        h = max(0.0, 1.0 - d * d)
        flow = 0.18 * math.sin(x * 0.25 + y * 0.6) + 0.12 * (noise(x, y) - 0.5)
        h = max(0.0, min(1.0, h + flow))
        if h < 0.14:
            continue
        fg = warm_fg(h, y * 0.28 + x * 0.06)
        if h > 0.90 and noise(x, y) > 0.55:
            fg = 15
        set_cell(cv, x, y, heat_to_density(h), fg)

# PASS 2+3 -- CHANNELS. (b): more amplitude/phase variation so ridges don't read as a comb.
# Store each channel's centerline so the ember pass can rise ALONG it (a).
NCH = 7
CHANNELS = []   # list of (centerline_fn, reach)
for ci in range(NCH):
    base_x = (ci + 0.5) * W / NCH
    amp = 3.0 + 4.5 * abs(math.sin(ci * 1.7 + 0.6))          # (b) wider amplitude spread
    ph = ci * 1.3 + 0.7 * math.sin(ci * 2.3)                 # (b) phase no longer a clean comb
    reach = POOL_TOP - (4 + int(11 * abs(math.sin(ci * 2.1 + 0.4))))   # (b) more varied climb height

    def cx_at(y, base_x=base_x, amp=amp, ph=ph):
        return base_x + amp * math.sin(y * 0.16 + ph) + 2.5 * math.sin(y * 0.05 + ph * 2.0)
    CHANNELS.append((cx_at, reach))

    for y in range(reach, POOL_TOP + 1):
        t = (y - reach) / max(1, POOL_TOP - reach)
        height_decay = t ** 1.4
        cx = cx_at(y)
        for x in range(W):
            d = abs(x - cx)
            if d > 4.0:
                continue
            h = (1.0 - d / 4.0) * height_decay
            h = max(0.0, min(1.0, h + 0.10 * (noise(x, y) - 0.5)))
            if h < 0.12:
                continue
            fg = warm_fg(h, y * 0.30 + x * 0.08 + ci)
            if h > 0.86 and d < 1.2:
                fg = 15
            set_cell(cv, x, y, heat_to_density(h), fg)

# PASS 4 -- EMBER CASCADE (a): embers rise ALONG the channel centerlines so the tail reads as
#   connected flow out of each ridge, not uniform-random scatter. A few free embers remain for
#   the "dissolving into void" feel, but most follow a channel's path and cool as they climb.
for ci in range(NCH):
    cx_at, reach = CHANNELS[ci]
    n_embers = 16 + (ci % 3) * 5          # per-channel ember count, slightly varied
    for _ in range(n_embers):
        ey = random.randint(2, POOL_TOP - 2)
        t = (POOL_TOP - ey) / max(1, POOL_TOP - 2)           # 0 near pool -> 1 high up
        h = max(0.0, 1.0 - t * 0.9)                          # cools as it rises
        if h < 0.18:
            continue
        cx = cx_at(ey)                                       # ride the channel centerline
        drift = round(2.5 * math.sin(ey * 0.3 + ci))         # lateral wobble as it climbs
        x = int(cx + drift + random.uniform(-1.5, 1.5))
        if not (0 <= x < W):
            continue
        fg = 15 if h > 0.82 else warm_fg(h, ey * 0.4 + ci)
        if random.random() < 0.62:
            set_cell(cv, x, ey, RAMP[0] if h > 0.7 else heat_to_density(h), fg)

# a handful of free embers dissolving into the void (not tied to any channel)
for _ in range(40):
    ex = random.randint(2, W - 3)
    ey = random.randint(2, POOL_TOP // 2)
    t = (POOL_TOP - ey) / max(1, POOL_TOP - 2)
    h = max(0.0, 1.0 - t * 0.95)
    if h < 0.22:
        continue
    fg = 15 if h > 0.85 else warm_fg(h, ey * 0.4 + ex)
    if random.random() < 0.5:
        set_cell(cv, ex, ey, heat_to_density(h), fg)

# ===========================================================================
# emit -- (c): top title card matching MONOLITH's framing, then canvas, then sig block.
#   FORGE is the explicit mirror of MONOLITH; frame it identically so the pair reads as a set.
# ===========================================================================
out = []
render(cv, out)

def framed_into(lst, title):
    lst.append("")
    pad = W - len(title); left = pad // 2
    lst.append(c(104, 0) + " " * left + c(97, 0) + title + c(104, 0) + " " * (pad - left))

title_block = []
framed_into(title_block, "FORGE // molten field rising out of the dark")
title_block.append(c(94, 0) + ("  heat climbing, embers dissolving upward -- lit out of the dark").center(W).ljust(W) + "\x1b[0m")
title_block.append("")

sig = []
sig_block(sig, "FORGE // MOLTEN FIELD v2.0", handles="raze & hollis (joint)")

final = title_block + out + sig
raw = "\n".join(final) + "\x1b[0m\n"
with open(OUT, "w", encoding="cp437") as f:
    f.write(raw)
print("wrote", OUT, "rows:", len(final))
