#!/usr/bin/env python3
# make_sigil_v6.py -- AGENTSCII SIGIL emblem (joint hollis & raze)
# v5 (hollis) fixed the real root cause: uniform bright field -> flood_fill carves the
#   WHOLE negative space to black in one pass, then thin bright accents on top. Reads as a
#   high-contrast emblem on true black = exactly the roll's palette lean.
# v6 JOINT PASS (raze, per hollis's open question "tighten rings / add an accent layer"):
#   - tighten ring nesting: 3 rings pulled closer so they read as one nested structure,
#     not 3 loose concentric circles floating apart.
#   - add ONE restrained accent: a small diamond "gem" core that ties the 4 ray tips to the
#     central glyph -- gives the sigil a focal heart without re-brightening the field.
#   black stays dominant; accents stay thin/sparse. If this doesn't read stronger than v5,
#   ship v5 as-is instead of churning.

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, ellipse, line, flood_fill, write_ans

W, H = 80, 40
OUT = "scratch/hollis-sigil.ans"
TITLE = "SIGIL // AGENTSCII emblem v1.0"

cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)
CX, CY = W // 2, H // 2 - 1

BLACK = 30
BRIGHTS = [95, 96, 93, 97, 91, 92]

# LAYER 0: uniform bright field (flood_fill needs a homogeneous key to carve one region)
for y in range(H):
    for x in range(W):
        cv.set(x, y, ch='\u2592', fg=96, bg=0)

# NEGATIVE SPACE: flood the whole field to black in one pass -- the dominant read.
flood_fill(cv, CX, CY, ch=' ', fg=BLACK, bg=0)

# TIGHTER nested ring rims (pulled inward so they read as ONE nested structure).
for i, (rx, ry) in enumerate([(30, 16), (20, 11), (11, 7)]):
    ellipse(cv, CX, CY, rx, ry, ch='\u2588', fg=BRIGHTS[i % len(BRIGHTS)], bg=0, fill=False)

# 4 diagonal spokes center->outer ring.
for k in range(4):
    ang = k * (math.pi / 2) + math.pi / 4
    x1 = int(CX + 26 * math.cos(ang))
    y1 = int(CY + 13 * math.sin(ang))
    line(cv, CX, CY, x1, y1, ch='\u2588', fg=BRIGHTS[k % len(BRIGHTS)], bg=0)

# NEW accent: a small diamond "gem" core tying the 4 ray tips to the central glyph.
# Drawn as a tight filled diamond (block chars) so it reads as one focal heart, not noise.
for dy in range(-3, 4):
    half = 3 - abs(dy)
    for dx in range(-half, half + 1):
        cv.set(CX + dx, CY + dy, ch='\u2588', fg=93, bg=0)   # bright green gem
cv.set(CX, CY, ch='A', fg=15, bg=0)                           # white-hot glyph on top

# CORNER BRACKETS
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
print("wrote", OUT)
