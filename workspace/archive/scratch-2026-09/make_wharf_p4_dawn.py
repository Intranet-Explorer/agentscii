#!/usr/bin/env python3
# hollis -- P4 DAWN: light returns. Mirror of P1 dusk -- the sun rises from the horizon
# (amber->cyan reflection column), and the pier lamp goes out as the sun comes up. The
# eye's continuous anchor moves: dusk sun -> lamp -> dawn sun, so the cycle closes.
from wharf_common import *

cells = new_canvas()

SUNX = 40             # single light source x -- the rising sun, centered (mirror of P1)
SUNY = PIER - 2       # just above the horizon, low -- dawn, not high noon
SUNR = 5              # disc radius

# --- SKY: flat black up top; a warm band only near the horizon (dawn glow), brighter
#     than dusk's because light is returning. Stars fading out (fewer, dimmer). ---
stars(cells, n=3, seed=29, ymax=PIER - 10)        # last stars, high up, mostly gone
for i, y in enumerate(range(PIER - 6, PIER)):     # warm glow band, last 6 rows above water
    g = i / 5.0                                    # 0 (top of band) -> 1 (waterline)
    col = A if g < 0.4 else (C if g < 0.75 else B)
    ch = SH3 if g < 0.5 else (SH2 if g < 0.85 else " ")
    for x in range(W):
        edge = 1 - abs(x - SUNX) / float(W / 2 + 1)
        if ch != " " and (x % 3 == 0 or edge > 0.45):
            put(cells, x, y, col, ch)

# --- SUN: a single warm disc just above the horizon, white-hot core (mirror of P1) ---
for dy in range(-SUNR, SUNR + 1):
    for dx in range(-SUNR, SUNR + 1):
        d = math.hypot(dx, dy * 1.4)              # slightly flattened disc
        if d > SUNR:
            continue
        x, y = int(SUNX + dx), int(SUNY + dy)
        if d < 1.6:
            put(cells, x, y, Wt, BLK)             # white-hot core
        elif d < 3.2:
            put(cells, x, y, A, BLK)              # amber body
        else:
            put(cells, x, y, A, SH3)              # soft amber edge

# --- PIER / WATER (shared structure) ---
pier_deck(cells)
water_shimmer(cells, band=4, seed=19)

# --- LAMP: the pier lamp is going OUT -- a dim ember only, no reflection column.
#     This is the handoff: as the sun's column takes over, the lamp dies. ---
put(cells, 58, PIER - 1, B, BAR)                 # post, dark now
put(cells, 58, PIER - 2, A, SH1)                # last dim ember (no white core, no halo)

# --- REFLECTION: sun column down the water, amber at top fading to cyan (dawn light) ---
reflection_column(cells, SUNX, warm_top=0.34, seed=6)

# --- SIG ---
sig_block(cells, [
     ("AGENTSCII", C),
     ("WHARF / DAWN", Wt),
     ("hollis / 1996", B),
])

emit(cells, "wharf-p4-dawn.ans")
