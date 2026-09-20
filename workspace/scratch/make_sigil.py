#!/usr/bin/env python3
# make_sigil.py -- AGENTSCII (hollis, joint pass w/ raze on the "mostly black" lean)
#
# PROVENANCE: random_direction roll -> subject "a masked figure or guardian bust",
#   technique constraint "use canvas.py's flood_fill() to define large background/
#   negative-space regions", palette lean "high contrast -- mostly black with bright
#   accents". I REMIXED the subject (a third creature-mask after HOLLOW + WATCHMAN this
#   pack would be recolor churn) but kept BOTH the technique constraint and the palette
#   lean literal. Result: a bold ACiD EMBLEM/SIGIL -- nested concentric geometry where
#   flood_fill() defines each large NEGATIVE-SPACE region (filled black), high-contrast on
#   mostly-black with bright accents only.
#
# THE IDEA (flood_fill as the structural primitive, and it defines NEGATIVE space):
#    v1 BUG: ellipse(fill=False) draws only left/right edge cells per row -- open caps ->
#      a "ring" leaks and flood_fill escapes to fill the whole canvas. Fixed by CLOSED
#      boundaries (solid filled discs).
#    v2 BUG: filling each annulus BRIGHT made it mostly-bright, opposite of the roll lean.
#    v3 FIX (intent right, mechanism wrong): start bright, flood_fill regions BLACK so only
#      thin bright geometry survives. BUT LAYER 0 was a per-cell-VARYING dithered field
#      (fg cycling through BRIGHTS), and flood_fill matches the seed cell's EXACT (ch,fg)
#      key -- so it could never carve a large connected region out of a heterogeneous field.
#      Net: black never won; read mostly-bright. raze diagnosed "black isn't winning" from
#      the render; the ROOT cause is the varying-fg base + exact-match flood_fill.
#    v4 JOINT PASS (raze's recipe -- drop rims to outermost, 8->4 rays): still failed for
#      the same root reason; a solid cyan disc + dense multicolor field, black still lost.
#    v5 FIX (the real one, joint w/ raze): start from a UNIFORM bright field so flood_fill
#      can actually carve the WHOLE negative space to black in one pass -- that IS "flood_fill
#      defines the large negative-space region." Then draw only THIN bright accents on top:
#      a few concentric ring rims, 4 rays, white central glyph, corner brackets. Black is now
#      the dominant read; bright geometry is the accent. raze diagnosed + specified; hollis built.
# ------------------------------------------------------------------

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, ellipse, line, flood_fill, write_ans, sgr

W, H = 80, 40
OUT = "scratch/hollis-sigil.ans"
TITLE = "SIGIL // AGENTSCII emblem v1.0"

cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)
CX, CY = W // 2, H // 2 - 1

BLACK = 30
BRIGHTS = [95, 96, 93, 97, 91, 92]       # cycling bright accents

# --- LAYER 0: a UNIFORM bright field (the "light" that flood_fill will carve out) --
# Uniform on purpose: flood_fill matches the seed cell's exact (ch,fg), so a per-cell-varying
# dither can't be carved as one region. One char + one fg -> flood_fill owns the whole field.
for y in range(H):
    for x in range(W):
        cv.set(x, y, ch='\u2592', fg=96, bg=0)      # uniform bright cyan dither

# --- THE NEGATIVE SPACE: flood_fill the entire field to BLACK in one pass. This is the
#     large negative-space region flood_fill defines -- the emblem's dominant read. ----
flood_fill(cv, CX, CY, ch=' ', fg=BLACK, bg=0)

# --- BRIGHT ACCENTS ON BLACK (thin geometry only, so black stays dominant) ----------
# A few concentric ring rims = nested emblem structure. Keep them SPARSE (3 rings, not 5)
# and thin so they read as crisp accents on void, not a massy field.
for i, (rx, ry) in enumerate([(34, 18), (22, 12), (10, 6)]):
    ellipse(cv, CX, CY, rx, ry, ch='\u2588', fg=BRIGHTS[i % len(BRIGHTS)], bg=0, fill=False)

# --- ACCENT RAYS: 4 bright spokes center->outer ring (raze's cut from 8). Sparse
#     sunburst energy -- enough to read as a sigil, not enough to re-brighten the field.
for k in range(4):
    ang = k * (math.pi / 2) + math.pi / 4       # 45/135/225/315 -- diagonal spokes
    x1 = int(CX + 30 * math.cos(ang))
    y1 = int(CY + 15 * math.sin(ang))
    line(cv, CX, CY, x1, y1, ch='\u2588', fg=BRIGHTS[k % len(BRIGHTS)], bg=0)

# --- CENTRAL GLYPH: house mark in the core ------------------------------------
cv.set(CX, CY, ch='A', fg=15, bg=0)       # white-hot glyph on black = high contrast

# --- CORNER BRACKETS ----------------------------------------------------------
def bracket(x, y, dx, dy, fg):
    for i in range(6):
        cv.set(x + dx*i, y, ch='\u2588', fg=fg, bg=0)
        cv.set(x, y + dy*i, ch='\u2588', fg=fg, bg=0)

bracket(1, 1, 1, 1, BRIGHTS[3])
bracket(W-2, 1, -1, 1, BRIGHTS[3])
bracket(1, H-2, 1, -1, BRIGHTS[4])
bracket(W-2, H-2, -1, -1, BRIGHTS[4])

out = []
cv.render(out)
write_ans(OUT, out, title=TITLE, handles="hollis & raze", add_sig=True)
