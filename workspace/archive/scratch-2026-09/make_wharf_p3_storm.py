#!/usr/bin/env python3
# raze -- P3 STORM/SHIFT: water churns, palette shifts cooler/denser, dither ramps up.
# This is the ONE place heavy dither earns its keep (per scope). Single light source = a
# lightning bolt (white-hot) forking down through the sky; the lamp on the pier still burns
# but dimmed under rain. Churn reads as HORIZONTAL wave motion + sparse rain -- structured,
# not TV static (the WHARF pass-1 lesson, applied to a storm).
import math
from wharf_common import *

cells = new_canvas()

LAMPX = 58
LAMPTOP = 9
random.seed(41)

# --- SKY: low cloud strata -- clear horizontal layers (not a uniform checkerboard).
# Denser than dusk/night but structured: each layer is a horizontal band with gentle
# per-row density, broken by occasional gaps so it reads as cloud, not static.
for i, y in enumerate(range(3, PIER - 2)):
    layer = int(y / 4) % 2                       # alternating strata
    base = 0.55 if layer else 0.28               # dense vs thin layer
    for x in range(W):
        # gentle horizontal wave so density varies smoothly left-right, not per-cell noise
        wave = 0.15 * math.sin((x + y) * 0.4)
        p = base + wave
        if random.random() < p:
            ch = SH3 if layer else SH2
            col = B if (y / PIER) < 0.6 else C
            put(cells, x, y, col, ch)

# --- LIGHTNING: single white-hot bolt forking down through the sky -- the focal source.
BOLT_X = 34
for y in range(3, PIER - 2):
    jitter = int(round(math.sin(y * 0.9) * 1.5)) + (1 if (y % 7 == 0) else 0)
    x = BOLT_X + jitter
    put(cells, x, y, Wt, BAR)
    if y % 5 == 2:                               # a short fork
        put(cells, x + 2, y, Wt, SH3)
    if y % 6 == 4:
        put(cells, x - 2, y, Wt, SH1)
for dx in (-2, -1, 0, 1, 2):                     # bright flash halo at the bolt's head
    put(cells, BOLT_X + dx, 3, Wt, BLK if dx == 0 else SH3)

# --- LAMP: still burning but dimmed -- amber core only, no glow ring (rain kills the halo)
for y in range(LAMPTOP + 1, PIER):
    put(cells, LAMPX, y, B, BAR)
put(cells, LAMPX, LAMPTOP, A, BLK)
put(cells, LAMPX, LAMPTOP - 1, Wt, SH3)          # dimmed white core

# --- PIER / WATER: churning -- horizontal wave motion (not per-cell static).
pier_deck(cells, col=B)
for i, y in enumerate(range(WATER_TOP, min(WATER_TOP + 7, H))):    # taller churn band than calm water
    depth = i / 7.0
    for x in range(W):
        # horizontal swell: rows of wave crests that shift phase as they go down
        crest = math.sin(x * 0.5 + y * 1.1) * 0.5 + 0.5
        p = (0.7 - depth * 0.4) * crest          # denser near shore, sparser with depth
        if random.random() < p:
            ch = SH3 if crest > 0.6 else (SH2 if crest > 0.3 else SH1)
            col = C if crest > 0.7 else B
            put(cells, x, y, col, ch)
# sparse churn ticks deeper -- fewer than the calm panel's shimmer but present
for y in range(WATER_TOP + 7, H - 4):
    for x in range(0, W, 4):
        if (x * 3 + y * 7) % 9 == 0:
            put(cells, x, y, B, SH1)

# --- REFLECTIONS: two broken columns -- the bolt's flash on the water + the dim lamp ---
reflection_column(cells, BOLT_X, warm_top=0.0, seed=9)      # cool (white/cyan) flash reflection
reflection_column(cells, LAMPX, warm_top=0.12, seed=3)      # faint amber, mostly gone

# --- RAIN: sparse diagonal ticks across the whole frame -- the storm's signature texture ---
for y in range(0, H):
    for x in range(0, W):
        if (x * 7 + y * 13) % 41 == 0:                 # sparser than before -- rain, not static
            put(cells, x, y, C, "|")

# --- SIG ---
sig_block(cells, [
       ("AGENTSCII", C),
       ("WHARF / STORM", Wt),
       ("raze / 1996", B),
])

emit(cells, "wharf-p3-storm.ans")
