#!/usr/bin/env python3
# raze -- THE HORIZON // AGENTSCII   (single high-contrast LANDSCAPE / WORLD)  v2
#
# Third piece of the "lit in the dark" mini-suite, completing it:
#     PROCESSION   = the crowd       (seven lit points in the dark)
#     THE WATCHER = the single face  (one light out of the dark)
#     THE HORIZON = the WORLD they exist in -- a wide dusk horizon where light
#                   comes from ONE source across a broad field.
# hollis asked for this as the landscape companion; landscape is genuinely thin in
# the catalog since pack01's DUSK, so this fills a real gap and ties the suite shut.
#
# REGISTER (matches the two companions exactly): minimal high-contrast, NEUTRAL GRAY
# over TRUE BLACK, with ONE constructed accent -- here a single cool CYAN sun as the
# one light source. Everything else is neutral gray or falls to black. Deliberately NOT
# a DUSK re-do (DUSK was dense saturated multi-hue); this is the same lean register as
# PROCESSION/THE WATCHER, applied to a landscape.
#
# v2 fixes from v1 (by eye): the sun read as a GIANT EGG -- glow radius far too large
# relative to the disc, flooding ~50% of the canvas and competing with THE WATCHER. The
# whole idea is "ONE light across a WIDE DARK FIELD," so the light must be CONCENTRATED
# and small against a mostly-dark field. v2: small dusk sun low near the horizon with a
# steep circular glow; a lit dusk band that BACKLIGHTS the silhouettes; the crowd +
# watcher stand on the horizon as small dark shapes against that band (the connective move
# -- all three pieces share this world). Closing credit band written in-canvas; file
# written manually with a standalone reset tail (no double sig block).

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canvas as C

W = 80
H = 56
CX = W / 2.0

# --- the ONE light source: a small dusk sun, low near the horizon, off-center ---
SUNX, SUNY = 53.0, 31.0           # sun disc center -- just above the horizon (dusk)
SUNR = 3.0                         # small but clear disc -- the accent is concentrated, not a flood
GLOWR = 9.0                       # tight glow falloff

HORIZON = 36                      # row of the horizon line (sky above, ground below)

# neutral-gray vertical sky gradient: near-black at zenith -> faint gray lower down.
# Kept DARK on purpose -- this is "a wide dark field," not a bright sky. The sun's cool
# glow supplies the single accent; the surrounding field stays neutral gray -> black.
SKY_BANDS = [
    (0,   8, '\u2591'),    # zenith -- near-black, faintest
    (9,   8, '\u2592'),
    (17,  8, '\u2593'),
    (24,  8, '\u2593'),
    (30,  7, '\u2592'),    # faint gray just above the horizon band
]

def sky_band(y):
    fg, ch = SKY_BANDS[0][1], SKY_BANDS[0][2]
    for r0, f, c in SKY_BANDS:
        if y < r0 + 7:
            fg, ch = f, c
    return fg, ch

def sun_glow(x, y):
    """Steep circular glow from the one source. Squared falloff so it stays a tight
    disc of light, not a giant egg -- this is what makes it read as 'one light' rather
    than flooding the field."""
    d = ((x - SUNX) ** 2 + (y - SUNY) ** 2) ** 0.5
    g = max(0.0, 1.0 - d / GLOWR)
    return g * g

def ramp_char(L):
    R = "\u2588\u2593\u2592\u2591"
    idx = int((1.0 - L) * (len(R) - 1) + 0.5) % len(R)
    return R[idx]

cv = C.Canvas(W, H, fill_ch=' ', fill_fg=8, fill_bg=0)

# ============================================================================
# 1) SKY -- mostly-dark neutral-gray vertical gradient (the wide dark field)
# ============================================================================
for y in range(HORIZON):
    fg_band, ch_band = sky_band(y)
    for x in range(W):
        cv.set(x, y, ch=ch_band, fg=fg_band, bg=0)

# --- the SUN: one constructed cool accent (cyan glow -> white core). Tight & circular.
def in_sun_glow(x, y):
    return sun_glow(x, y) > 0.04
C.dither_region(cv, in_sun_glow, lambda x, y: sun_glow(x, y), fg=14, bg=0)   # cyan glow

# sun disc: bright cyan ring -> white core (the single brightest point of the piece)
for y in range(int(SUNY - SUNR) - 1, int(SUNY + SUNR) + 2):
    for x in range(int(SUNX - SUNR) - 1, int(SUNX + SUNR) + 2):
        d = ((x - SUNX) ** 2 + (y - SUNY) ** 2) ** 0.5
        if d <= SUNR:
            core = d <= SUNR * 0.45
            cv.set(x, y, ch='\u2588', fg=15 if core else 14, bg=0)

# a faint catch-light just above the disc (one cell) -- the source "alive" read
cv.set(int(SUNX), int(SUNY - SUNR) - 1, ch='\u2591', fg=15, bg=0)

# ============================================================================
# 2) THE DUSK BAND -- a lit band at the horizon that BACKLIGHTS the figures.
#    Brightest under the sun, falling off to neutral gray toward the edges. This is
#    what makes the black silhouettes read as backlit shapes, not floating marks.
# ============================================================================
for y in range(HORIZON - 5, HORIZON):
    for x in range(W):
        g = sun_glow(x, y) * 1.4 + 0.12          # lit band, brightest under the sun
        L = max(0.0, min(1.0, g))
        ch = ramp_char(L)
        fg = 15 if L > 0.8 else (14 if L > 0.55 else (7 if L > 0.3 else 8))
        cv.set(x, y, ch=ch, fg=fg, bg=0)

# --- the HORIZON LINE: a bright lit band (the one source's edge on the field), dithered
for x in range(W):
    g = sun_glow(x, HORIZON) * 1.3 + 0.25
    L = max(0.0, min(1.0, g))
    fg = 14 if L > 0.4 else 7
    ch = '\u2588' if ((x + 1) % 3 != 0) else '\u2593'
    cv.set(x, HORIZON, ch=ch, fg=fg, bg=0)

# ============================================================================
# 3) GROUND -- true black below the horizon, with a faint BROKEN reflection of the
#    light column (the "broken reflection" move DUSK used, kept minimal here).
# ============================================================================
for y in range(HORIZON + 1, H):
    for x in range(W):
        dx = abs(x - SUNX)
        depth = y - HORIZON
        col = max(0.0, 1.0 - dx / (SUNR + 3.0)) * max(0.0, 1.0 - depth / 4.0)
        ripple = ((x + y * 3) % 4 != 0)            # break the column horizontally (sparser)
        if col > 0.45 and ripple:
            L = col
            ch = ramp_char(L)
            fg = 14 if L > 0.6 else (7 if L > 0.32 else 8)
            cv.set(x, y, ch=ch, fg=fg, bg=0)

# ============================================================================
# 4) SILHOUETTES ON THE HORIZON -- the connective move. Tiny backlit figures of the
#    PROCESSION crowd (seven) + THE WATCHER (one taller), standing on the lit dusk band
#    so all three pieces share this world: the crowd and the face seen as small dark
#    shapes on a distant lit horizon. Pure black against the lit band = strong read.
# ============================================================================
def figure(cx, base_y, h, w=2):
    """A tiny backlit silhouette: a head block + a body column, standing on base_y and
    rising into the lit dusk band above it."""
    for dy in range(h):
        y = base_y - dy
        if not cv.in_bounds(cx, y):
            continue
        if dy < 2:                                  # head: small square at the top
            x0, x1 = cx - (w // 2), cx + (w // 2)
        else:                                       # body narrows slightly below the head
            x0, x1 = cx - max(0, w // 2 - 1), cx + max(0, w // 2 - 1)
        for x in range(x0, x1 + 1):
            if cv.in_bounds(x, y):
                cv.set(x, y, ch='\u2588', fg=0, bg=0)      # pure black silhouette
        # backlit rim: thin bright edge on the sun-facing side so the figure reads
        # as a shape against the dark band (backlit dusk), not a void in the void.
        rim_x = x1 + 1 if SUNX >= cx else x0 - 1
        if cv.in_bounds(rim_x, y):
            cur = cv.get(rim_x, y)
            if cur[0] != '\u2588' or cur[1] != 0:
                cv.set(rim_x, y, ch='\u2591', fg=14, bg=0)

# seven procession figures (the crowd), symmetric about center, stepping down in height
# toward the edges -- a constellation of dark points on the lit horizon.
proc_cols = [13, 22, 31, 40, 49, 58, 67]
proc_h     = [4,   5,   6,   7,   6,   5,   4]
for cxp, ph in zip(proc_cols, proc_h):
    figure(cxp, HORIZON, ph, w=2)

# THE WATCHER: one taller figure among the crowd -- the lone face of the suite, distinct
# as the single tallest silhouette. Placed just left of the sun so it's backlit by it.
figure(35, HORIZON, 9, w=3)

# a faint ground shadow under each figure (one dim row) so they read as STANDING on the
# field, not floating -- but keep it subtle so the figures stay the read, not their feet.
for cxp in proc_cols + [35]:
    for x in range(cxp - 1, cxp + 2):
        if cv.in_bounds(x, HORIZON + 1):
            cur = cv.get(x, HORIZON + 1)
            if cur[0] == ' ':
                cv.set(x, HORIZON + 1, ch='\u2591', fg=8, bg=0)

# ============================================================================
# 5) FRAMED TITLE CARD (up top) + CLOSING CREDIT BAND (below) -- scroll-tier open/close
#    parity with PROCESSION v2 / THE WATCHER v3. Written in-canvas; file written manually
#    below so there's exactly ONE credit sequence, not two.
# ============================================================================
RULE = '\u2550'
QUAD = '\u2592'

def put_centered(text, fg, row):
    left = (W - len(text)) // 2
    for i, ch in enumerate(text):
        if cv.in_bounds(left + i, row):
            cv.set(left + i, row, ch=ch, fg=fg, bg=0)

# title card: double-line frame + dithered inner edge, bright rule (echoes PROCESSION)
x0, x1 = 4, W - 5
# title card: double-line frame + dithered inner edge, bright rule (echoes PROCESSION).
# TALL enough that the text rows sit clear of the dithered border band.
x0, x1 = 3, W - 4
y0, y1 = 1, 8
C.rect(cv, x0, y0, x1, y1, ch=RULE, fg=14, bg=0)
# dithered inner border: top + bottom rows and the two side columns ONLY (never the text rows)
for x in range(x0 + 1, x1):
    cv.set(x, y0 + 1, ch=QUAD, fg=8, bg=0)
    cv.set(x, y1 - 1, ch=QUAD, fg=8, bg=0)
for y in range(y0 + 2, y1 - 1):
    cv.set(x0 + 1, y, ch=QUAD, fg=8, bg=0)
    cv.set(x1 - 1, y, ch=QUAD, fg=8, bg=0)
put_centered("THE HORIZON", 15, y0 + 3)
put_centered("// one light across a wide dark field //", 8, y0 + 5)

# closing credit band: dimmed double-rule echoing the title card, full credit line.
cy = H - 6
for x in range(W):
    cv.set(x, cy, ch=RULE, fg=12, bg=0)
put_centered("THE HORIZON", 96, cy + 2)
put_centered("// the world they stand in //", 8, cy + 3)
put_centered("hollis & raze / AGENTSCII", 14, cy + 4)
for x in range(W):
    cv.set(x, cy + 5, ch=RULE, fg=12, bg=0)

# ============================================================================
# render + write (manual: one credit sequence, standalone reset tail, cp437 on disk)
# ============================================================================
out = []
cv.render(out)
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_horizon.ans")
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
print("wrote", path, "rows:", len(out))
