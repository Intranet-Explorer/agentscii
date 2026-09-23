#!/usr/bin/env python3
# raze -- P1 DUSK: harbor at last light. Warm horizon glow fading to blue.
# The sun is the single light source (upper-center, low on the horizon). Its reflection
# column runs amber->cyan down the water -- the dusk-to-night handoff made visible.
import math
from wharf_common import *

cells = new_canvas()

SUNX = 40            # single light source x -- the setting sun, centered
SUNY = PIER - 3      # low on the horizon
SUNR = 5             # disc radius

# --- SKY: flat black up top, a warm band only near the horizon (dusk glow) ---
stars(cells, n=4, seed=21, ymax=PIER - 8)        # few stars, high up only -- dusk, not night
for i, y in enumerate(range(PIER - 6, PIER)):    # warm glow band, last 6 rows above water
    g = i / 5.0                                   # 0 (top of band) -> 1 (waterline)
    col = A if g < 0.35 else (C if g < 0.7 else B)
    ch = SH2 if g < 0.4 else (SH1 if g < 0.8 else " ")
    for x in range(W):
        # fade the band toward the edges so it's a glow, not a full-width stripe
        edge = 1 - abs(x - SUNX) / float(W / 2 + 1)
        if ch != " " and (x % 3 == 0 or edge > 0.5):
            put(cells, x, y, col, ch)

# --- SUN: a single warm disc low on the horizon, white-hot core ---
for dy in range(-SUNR, SUNR + 1):
    for dx in range(-SUNR, SUNR + 1):
        d = math.hypot(dx, dy * 1.4)             # slightly flattened disc
        if d > SUNR:
            continue
        x, y = int(SUNX + dx), int(SUNY + dy)
        if d < 1.6:
            put(cells, x, y, Wt, BLK)            # white-hot core
        elif d < 3.2:
            put(cells, x, y, A, BLK)             # amber body
        else:
            put(cells, x, y, A, SH3)             # soft amber edge

# --- PIER / WATER (shared structure) ---
pier_deck(cells)
water_shimmer(cells, band=4, seed=17)

# --- REFLECTION: sun column down the water, amber at top fading to cyan (dusk->night) ---
reflection_column(cells, SUNX, warm_top=0.30, seed=5)

# --- SIG ---
sig_block(cells, [
    ("AGENTSCII", C),
    ("WHARF / DUSK", Wt),
    ("raze / 1996", B),
])

emit(cells, "wharf-p1-dusk.ans")
