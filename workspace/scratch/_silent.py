#!/usr/bin/env python3
# SILENT // "the one left standing" -- hollis solo. AGENTSCI architectural register, DIM/low-saturation.
#
# PROVENANCE (honest): random_direction roll -> subject "a full-body figure in motion", technique
#    "canvas.flood_fill() as the primary negative-space tool", palette "full saturated 16-color cycling".
# I took ONLY the technique straight and REJECTED the other two: a moving full-body figure is STRIDE /
# MOTION_SEED (shipped, pack38/39) and saturated cycling is the inverse of the dim register. What's
# genuinely new + pairs with ERASURE for a coherent batch = an ARCHITECTURAL piece in the DIM register,
# built on flood_fill as the primary NEGATIVE-SPACE tool (only DEMON shipped it so far).
#
# WHAT THIS IS: a tall lit OBELISK standing in rising fog -- "the one left standing." A monolith that
# outlasted everything around it. Lit upper-left, density falls off down its length; the void is NOT flat
# black but a GRADED FOG FIELD (thick at the ground, thinning up) flood-filled as the primary negative-space
# pass. One rare white glint at the apex -- "the last light." Dim greys + one amber accent, like ERASURE.
#
# BUILT IN PASSES (METHODOLOGY), verified by eye with preview_piece at each:
#   P1 flat silhouette -> P2 shade from ONE upper-left source -> P3 fog field via flood_fill ->
#    P4 the apex glint + a faint ground line -> P5 frame + title card.

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, RAMP, texture_fill, write_ans, hygiene_gate, sig_block, flood_fill

W = 80
H = 46
MID = W // 2                        # 40 -- vertical axis of the obelisk
ACCENT = 11                         # bright amber -- ONE accent (the apex glint)

TOP_Y = 7                           # apex row (just under the title card)
BASE_Y = 39                         # where it meets the ground

def half_width(y):
    """Linear-ish taper: wide at the base, ~0 at the apex. Slight concave so it reads as carved stone."""
    if y < TOP_Y or y > BASE_Y:
        return None
    t = (y - TOP_Y) / (BASE_Y - TOP_Y)       # 0 at apex -> 1 at base
    return 2.5 + 9.5 * (t ** 1.35)           # ~2.5 wide near the top, ~12 at the base

def in_obelisk(x, y):
    hw = half_width(y)
    if hw is None:
        return False
    return abs(x - MID) <= hw


# ---- P1: flat silhouette (verify composition reads before any shading) ----
cv = Canvas(w=W, h=H, fill_ch=' ', fill_fg=0, fill_bg=0)
for y in range(H):
    for x in range(W):
        if in_obelisk(x, y):
            cv.set(x, y, '\u2588', 7, 0)


# ---- P2: shade from ONE upper-left source ---------------------------------
# Directional light, NOT distance-from-point (that rings = flat bars). Two terms:
#    (a) horizontal -- left face catches the light and peaks white, right turns away to grey.
#    (b) vertical    -- brightest at the apex, falling toward the base (the "last light" up top).
def obelisk_light(x, y):
    hw = half_width(y)
    if hw is None or hw < 1e-6:
        return 0.0
    t = (y - TOP_Y) / (BASE_Y - TOP_Y)           # 0 apex -> 1 base
    u = (x - MID) / hw                           # -1 left edge .. +1 right edge
    horiz = 0.5 * (1.0 - u)                      # left bright, right dark
    vert = 1.0 - 0.72 * t                        # apex bright, base dim
    L = 0.62 * horiz + 0.38 * vert
    return max(0.08, min(1.0, L))

RAMP4 = '\u2588\u2593\u2592\u2591'              # full -> sparse density ramp
def shade(L, base_fg=7, hot_fg=15):
    L = max(0.0, min(1.0, L))
    idx = int(L * (len(RAMP4) - 1) + 0.5) % len(RAMP4)
    fg = hot_fg if L > 0.86 else base_fg
    return RAMP4[idx], fg

for y in range(H):
    for x in range(W):
        if in_obelisk(x, y):
            ch, fg = shade(obelisk_light(x, y), base_fg=7, hot_fg=15)
            cv.set(x, y, ch, fg, 0)


# ---- P3: the void is a GRADED FOG FIELD, not flat black --------------------
# flood_fill seeds the whole surrounding void (the primary negative-space pass), then we grade it:
# fog is THICK near the ground and THINS as it rises -- so the obelisk reads as standing IN something.
def void_region(x, y):
    return not in_obelisk(x, y)

flood_fill(cv, MID, H - 2, '\u2591', 0, bg=0)      # seed: fill the open black field with a thin mark
# now grade that field by height: denser (fuller glyph + brighter grey) low, sparse up high.
import random
rng = random.Random(7)
for y in range(H):
    for x in range(W):
        if void_region(x, y):
            # keep the cell only with a probability that rises toward the ground
            t = (y - TOP_Y) / (BASE_Y - TOP_Y + 1.0)
            p = 0.12 + 0.36 * max(0.0, min(1.0, t))       # ~12% up top -> ~48% at the ground
            if rng.random() > p:
                cv.set(x, y, '\u2591', 8, 0)           # thin fog high up: faint dim-grey floor, not empty void
                continue
            # among kept cells, density tracks height too: fuller low, sparse high
            dens = int(max(0.0, min(1.0, t)) * (len(RAMP4) - 1) + 0.5) % len(RAMP4)
            fg = 8 if t > 0.55 else 7                    # ground fog a touch brighter than the upper haze
            cv.set(x, y, RAMP4[dens], fg, 0)


# ---- P4: the apex glint + a faint ground line -----------------------------
# one rare white cell at the very top -- "the last light."
cv.set(MID, TOP_Y, '\u2588', 15, 0)
cv.set(MID - 1, TOP_Y + 1, '\u2593', 15, 0)
# a faint ground line where the obelisk meets the fog -- anchors it to the earth
for x in range(6, W - 6):
    if rng.random() < 0.5:
        cv.set(x, BASE_Y + 1, '\u2591', 7, 0)


# ---- P5: frame + title card -----------------------------------------------
RULE = "\u2550"
def put_centered(text, y, fg):
    for x in range(W):
        cv.set(x, y, ' ', 0, 0)
    left = (W - len(text)) // 2
    for i, ch in enumerate(text):
        cv.set(left + i, y, ch, fg)

for x in range(W):
    cv.set(x, 0, RULE, 12, 0); cv.set(x, H - 1, RULE, 12, 0)
for y in range(H):
    cv.set(0, y, RULE, 12, 0); cv.set(W - 1, y, RULE, 12, 0)

put_centered("SILENT", 1, 15)
put_centered("// the one left standing //", 2, 8)

out = []
cv.render(out)
sig_block(out, "SILENT v1 (fog-flood obelisk)", handles="hollis")
raw = "\n".join(out) + "\x1b[0m\n"
with open('_silent.ans', 'w', encoding='cp437') as fh:
    fh.write(raw)
hygiene_gate('_silent.ans')
print("P5 written -- fog-flood obelisk")
