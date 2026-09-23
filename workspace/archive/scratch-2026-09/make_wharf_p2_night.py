#!/usr/bin/env python3
# raze -- P2 WHARF-NIGHT: the accepted WHARF v1.0 panel, kept intact as the heart of the scroll.
# Single warm-amber lamp on the pier; vertical reflection column; dither only at transitions.
from wharf_common import *

cells = new_canvas()

LAMPX = 58            # single light source x -- the lamp on the pier (upper-right)
LAMPTOP = 9           # row of the lamp head (focal point)

# --- SKY: flat black, sparse stars, faint cyan glow only at the horizon ---
stars(cells, n=9, seed=7)
horizon_glow(cells, rows=2, col=C)

# --- LAMP: single warm-amber focal source on a pier post ---
for y in range(LAMPTOP + 1, PIER):               # vertical post from head down to deck
    put(cells, LAMPX, y, B, BAR)
put(cells, LAMPX, LAMPTOP, A, BLK)              # amber lamp head
put(cells, LAMPX - 1, LAMPTOP, A, SH3)          # halo left
put(cells, LAMPX + 1, LAMPTOP, A, SH3)          # halo right
put(cells, LAMPX, LAMPTOP - 1, Wt, BLK)         # white hot center above
for dx in (-2, 2):                               # soft amber glow ring -- one row only
    put(cells, LAMPX + dx, LAMPTOP, A, SH1)

# --- PIER / WATER ---
pier_deck(cells)
water_shimmer(cells, band=4, seed=11)

# --- REFLECTION: vertical column under the lamp, horizontal ripples that fragment ---
reflection_column(cells, LAMPX, warm_top=0.18, seed=3)

# --- SIG ---
sig_block(cells, [
     ("AGENTSCII", C),
     ("WHARF v1.0", Wt),
     ("raze / 1996", B),
])

emit(cells, "wharf-p2-night.ans")
