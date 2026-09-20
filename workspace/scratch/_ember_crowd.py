#!/usr/bin/env python3
# raze -- EMBER CROWD v5.0 // AGENTSCI        (landscape/scene register)
#
# v1->v5: the scene kept breaking on the medium's limits (16 colors + block chars can't do a
# smooth gradient; base fg indices render as their BRIGHT variants via sgr masking). Final
# pass, fixing the two real bugs that made it read as broken stripes:
#     - GROUND was bright cyan/blue: fg 6 -> ESC[96m (bright cyan), fg 4 -> ESC[94m (bright blue).
#       Warm dim ground needs LOW-DENSITY blocks on a warm base hue, so the cell reads dark.
#       Now: near = low-density amber (dim brown), far = even lower density (darker).
#     - SUN was hidden behind the crowd band. Now it sits clearly ABOVE the horizon with the
#       crowd silhouetted against its lower edge -- a real backlit-crowd-at-dusk read.
#     - Sky: clean solid warm bands, minimal dither only at boundaries so they read as dusk
#       atmosphere not stripes.
#
# random_direction roll: subject="a crowd or group scene", technique=
# "canvas.py ellipse()+gradient_fill() for core shape + shading", palette lean=
# "warm tones (reds/yellows/magentas) dominant". Taken, remixed toward a legible scene.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, sgr, RAMP, ellipse, write_ans

random.seed(19)      # deterministic / reproducible

W = 80
H = 46
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

HORIZON = 30         # row where the sun sits and the crowd stands

# ---- SKY: clean solid warm bands, top->bottom deep magenta -> red -> amber -> white-hot.
BANDS = [
    (0, 11, 95),      # deep magenta high up
    (11, 18, 91),     # red mid-band
    (18, 25, 93),     # amber low band
     (25, HORIZON, 107),   # white-hot at the horizon line
]
for y in range(HORIZON):
    fg = None
    for lo, hi, c in BANDS:
        if lo <= y < hi:
            fg = c
            break
    for x in range(W):
        cv.set(x, y, '\u2588', fg, 0)

# light dither at each band boundary (1 row) so adjacent hues visually blend, not stripe
for lo, hi, c in BANDS:
    nxt = None
    for lo2, hi2, c2 in BANDS:
        if lo2 == hi:
            nxt = c2
            break
    if nxt is None:
        continue
    for x in range(W):
        cv.set(x, hi - 1, '\u2593', c, 0)      # half-block transition row

# ---- LOW SUN: a radial gradient disc sitting just above the horizon, clearly visible so the
# crowd reads as backlit silhouettes against its lower edge. Hot white core -> amber -> red halo.
SUN_X, SUN_Y = 52, HORIZON - 6
C.gradient_fill(cv, lambda x, y: (x - SUN_X) ** 2 / 84 + (y - SUN_Y) ** 2 / 70 < 1.0,
                SUN_X, SUN_Y, fg_near=107, fg_far=93, max_dist=8)
ellipse(cv, SUN_X, SUN_Y, 8, 6, ch='\u2591', fg=91, fill=False)      # thin red halo ring

# ---- GROUND: warm dim field. Low-density blocks on a warm base hue read as dark brown/maroon
# (a high-density block on a bright hue reads as the bright color -- that was the v4 bug).
for y in range(HORIZON, H):
    t = (y - HORIZON) / max(1, (H - HORIZON))      # 0 at horizon -> 1 at bottom
    fg = 6 if t < 0.5 else 4                        # amber near, red far (both warm bases)
    for x in range(W):
        n = math.sin(x * 1.1 + y * 0.6) * 0.5 + 0.5
        d = 0.18 + 0.12 * t + 0.08 * n              # LOW density -> dim warm ground, not bright
        idx = int((1.0 - max(0.0, min(1.0, d))) * (len(RAMP) - 1))
        cv.set(x, y, RAMP[idx], fg, 0)

# ---- THE CROWD: distinct backlit heads/shoulders along the horizon, silhouetted against the
# sun/sky. Each person = a small filled ellipse head on a wider shoulder line, at a slightly
# varying height so the top edge is bumpy (a sea of heads, not one arch). Near-black body with
# a bright amber rim where the sun grazes the crown -- classic backlit-crowd-at-dusk.
def person(cx, head_y, r):
    C.ellipse(cv, cx, head_y + r + 1, r + 2, r + 1, ch='\u2588', fg=0, fill=True)     # near-black body
    C.ellipse(cv, cx, head_y, r, r, ch='\u2588', fg=0, fill=True)
    for x in range(cx - r, cx + r + 1):          # warm rim catch on the crown
        if 0 <= x < W:
            cv.set(x, head_y - r, '\u2588', 93, 0)

# two depth rows spaced out so each reads as its own silhouette; near row bigger + lower.
for i in range(13):
    cx = int((i + 0.5) * (W / 13)) + random.randint(-1, 1)
    person(cx, HORIZON - random.choice([2, 3]), 2)
for i in range(8):
    cx = int((i + 0.5) * (W / 8)) + random.randint(-1, 1)
    person(cx, HORIZON - random.choice([4, 5]), 3)

# a few bright "life" sparks -- warm dots that read as faces catching the light / torches
for sx, sy in [(18, HORIZON - 4), (40, HORIZON - 5), (70, HORIZON - 3), (30, HORIZON - 3)]:
    cv.set(sx, sy, '\u2588', 107, 0)

# ---- signature block (house standard) -----------------------------------------
out = []
cv.render(out)
C.write_ans("scratch/_ember_crowd.ans", out, title="EMBER CROWD v5.0", handles="raze")
