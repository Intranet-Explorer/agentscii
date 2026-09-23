#!/usr/bin/env python3
# _wharf.py -- AGENTSCII "LOW TIDE // the wharf at dusk"   (raze, solo)  v6
#
# random_direction roll: subject "a wharf or coastline", technique "hand-place every
#   character with no shared library -- pure from-scratch composition", palette lean
#   "muted/dim, low-saturation throughout". SUBJECT + PALETTE taken straight; TECHNIQUE
#   read as deliberate hand-placement of structure. Noted for honesty.
#
# v6 REDESIGN (v5 finally READ as a wharf -- continuous deck + pilings into the water, lamp
#    at the near end -- but three things fought it: a loud yellow "mudflat" bar across the top
#    of the water that read as an equalizer stripe; scattered blue ripples that read like
#    confetti/rain not calm sea; and too much dead black sky up top). Fixes:
#       * HORIZON higher (14) -> less empty sky, more water; the wharf sits in the upper-mid.
#       * DROP the loud mudflat bar; replace with a faint 1-row dim-grey far-shore hint only.
#       * RIPPLES = sparse horizontal wave-LINES (short dashes on a few rows), not confetti --
#        reads as a calm water surface, dimmer and looser toward the horizon.
#       * BOAT given a thin grey outline so it reads on black water; placed mid-water.
#       * Deck gets plank seams (vertical ticks) so it reads as planks, not a solid bar.
#   Muted throughout: dim blue/grey/brown scene, ONE small amber lamp as the single accent.
#   Counterweight to lit-out-of-the-dark creatures + molten fields: a quiet maritime scene.
#
# TECHNIQUE: canvas.py primitives -- Canvas+set(), line()/rect() for deck/pilings/boat,
#   ellipse() for lamp glow. Structure hand-placed by math (even piling spacing, perspective
#   compression on the far end), not a noise field.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C

random.seed(13)
W = 80
H = 46                           # art area; sig block appended by write_ans

# ---- muted / dim / low-saturation palette (NO bright colors in the scene) ----
SKY_GREY    = 8                  # faint dim-grey overcast texture
SEA         = 4                # dark blue ripple ticks (sparse, on black)
SEA_RIP      = 8              # grey ripple ticks (sparse)
SHORE        = 8            # faint dim-grey far-shore hint (low tide, sparse)
WOOD         = 3         # dim yellow/brown plank (near deck)
WOOD_DK      = 8       # shaded wood / far piling (greyed by distance)
BOAT         = 0 # boat silhouette body (near-black)
BOAT_EDGE    = 8 # thin grey outline so the boat reads on black water
LAMP         = 11       # amber lamp -- the ONE accent, kept to a few cells
LAMP_HI      = 7        # white-hot lamp core (single cell)

cv = C.Canvas(W, H, fill_ch=' ', fill_fg=0, fill_bg=0)

HORIZON = 14                # row of the sea/horizon line (high -> more water, less sky)
DECK_Y    = 20              # the wharf deck sits on the water, below the horizon

# ---- PASS 1: overcast sky -- faint dim-grey texture on black (deliberate negative space)
for y in range(HORIZON):
    for x in range(W):
        if (x * 7 + y * 3) % 13 < 1:               # sparse faint grey specks -> overcast, not dead
            cv.set(x, y, C.RAMP[3], SKY_GREY, 0)

# a few dim birds high in the sky -- small V marks (not literal letters)
for bx in (18, 24, 60):
    by = 4 + (bx % 3)
    cv.set(bx, by, '/', 8, 0); cv.set(bx + 1, by - 1, '\\', 8, 0)

# ---- PASS 2: calm sea -- mostly BLACK with horizontal wave-LINES that breathe (not a grid)
SEA_TOP = HORIZON
SEA_BOT = H - 1
for wy in range(SEA_TOP + 1, SEA_BOT, 2):             # one wave-line every 2 rows
    phase = (wy * 7) % W                               # each row's dashes start at a different offset
    fg = SEA if wy > HORIZON + 8 else SEA_RIP          # bluer nearer the bottom, greyer up top
    for x in range(0, W, 5):                           # short dashes with even gaps -> reads as ripples
        xx = (x + phase) % W
        # let a few dashes drop out by position so rows don't align into a perfect matrix -- calm water breathes
        if (x * 3 + wy) % 17 < 15:
            cv.set(xx, wy, C.RAMP[1], fg, 0)           # a dash
            if (x // 5 + wy) % 2 == 0:                 # some dashes are 2 cells long (a longer ripple)
                cv.set((xx + 1) % W, wy, C.RAMP[1], fg, 0)
# ---- PASS 3: faint far-shore hint -- a sparse dim-grey line just below the horizon (low tide)
for x in range(W):
    if (x * 3 + 7) % 5 < 2:                          # broken/sparse, not a solid bar
        cv.set(x, HORIZON, C.RAMP[3], SHORE, 0)

# ---- PASS 4: the WHARF -- ONE continuous horizontal deck + evenly-spaced vertical pilings
DECK_X0, DECK_X1 = 6, 73           # the walkway runs most of the width (a long pier)
DECK_THICK = 2                     # 2-row deck band (the walkway surface)
# continuous deck: a horizontal band of planks
for y in range(DECK_Y, DECK_Y + DECK_THICK):
    for x in range(DECK_X0, DECK_X1 + 1):
        cv.set(x, y, C.RAMP[1], WOOD if x < (DECK_X0 + DECK_X1) / 2 else WOOD_DK, 0)
# plank seams: faint vertical ticks down the deck so it reads as planks, not a solid bar
for x in range(DECK_X0, DECK_X1 + 1, 3):
    cv.set(x, DECK_Y, C.RAMP[2], WOOD_DK, 0)

# pilings: evenly-spaced vertical posts dropping from the deck into the water;
# far (right) end shorter + closer-spaced -> gentle perspective compression.
N = 11
for i in range(N):
    t = i / (N - 1)
    px = int(DECK_X0 + t * (DECK_X1 - DECK_X0))
    far = t                        # 0 near(left) -> 1 far(right)
    post_h = int(7 - 3 * far)      # tall near -> short far
    for dy in range(post_h):
        y = DECK_Y + DECK_THICK + dy
        if not cv.in_bounds(px, y):
            continue
        wet = dy / max(1, post_h)
        ch = C.RAMP[0] if wet < 0.5 else (C.RAMP[2] if wet < 0.8 else C.RAMP[3])
        fg = WOOD if far < 0.5 else WOOD_DK             # greyed by distance
            # water tint where a post crosses the open sea band
        if y > HORIZON + 1 and random.random() < 0.25:
            cv.set(px, y, C.RAMP[2], SEA_RIP, 0)
        else:
            cv.set(px, y, ch, fg, 0)

# ---- PASS 5: a moored boat -- small silhouette mid-water with a thin grey outline
bx0, by0 = DECK_X0 + 16, DECK_Y + DECK_THICK + 4
for x in range(bx0 - 5, bx0 + 6):
    dx = abs(x - bx0)
    depth = 1 if dx <= 4 else 2
    for dy in range(depth):
        cv.set(x, by0 + dy, C.RAMP[0], BOAT, 0)
# thin grey outline so the near-black hull reads on black water
cv.set(bx0 - 5, by0, C.RAMP[1], BOAT_EDGE, 0); cv.set(bx0 + 5, by0, C.RAMP[1], BOAT_EDGE, 0)
for x in range(bx0 - 4, bx0 + 5):
    cv.set(x, by0 + 2, C.RAMP[1], BOAT_EDGE, 0)        # waterline under the hull
cv.set(bx0 - 1, by0 - 1, C.RAMP[0], BOAT, 0); cv.set(bx0, by0 - 1, C.RAMP[0], BOAT, 0)
C.line(cv, bx0, by0 - 1, bx0, by0 - 4, ch='|', fg=WOOD_DK, bg=0)       # mast

# ---- PASS 6: ONE small warm lamp at the near (left) end of the deck -- the single accent
LX, LY = DECK_X0 + 1, DECK_Y - 5
C.line(cv, LX, LY, LX, DECK_Y, ch='|', fg=WOOD_DK, bg=0)               # lamp post on the deck
cv.set(LX, LY, C.RAMP[0], LAMP_HI, 0)                                  # white-hot core (1 cell)
for dx in (-1, 0, 1):                                                 # tiny amber glow
    for dy in (-1, 0, 1):
        if abs(dx) + abs(dy) == 1:
            cv.set(LX + dx, LY + dy, C.RAMP[3], LAMP, 0)

out = []
cv.render(out)
C.write_ans("scratch/_wharf.ans", out, title="LOW TIDE // the wharf at dusk v6.0",
            handles="raze")
