# THE LAST LIGHT v14 — joint raze+hollis.
# Deliberate revisit of _lastlight (pinned best = v2, 16.9% hb / 26.3% shade).
# v2's one real failure: the lone figure read as a broken gray column/mast, not a human.
# This rebuilds the figure with standing_figure() (tested gradient-anatomy primitive) so it
# RESOLVES as a person; keeps v2's sun + ground-ramp structure that carried its shade density.
import sys, math
sys.path.insert(0, 'scratch')
from figure_common import (new_canvas, render, sig_block, standing_figure,
                           light_field, shade_region, joint_dot, capsule)

W = 80
H = 42
cv = new_canvas(H, W)

# ---- LIGHT: the dying sun is the point source, low on the right horizon ----
sun_cx, sun_cy = 56.0, 27.0
def L(x, y):
    return light_field(x, y, sun_cx, sun_cy, lmax=34.0, ambient=0.18)

# ---- SKY: void black (deliberate mood), a few sparse stars ----
import random
random.seed(11)
for _ in range(14):
    sx = random.randint(2, 77); sy = random.randint(1, 16)
    cv[sy][sx] = [' ', 95, 0]   # dim white star

# ---- DYING SUN: large lit warm sphere half-set on the low horizon ----
sun_r = 13.0
def sun_region(x, y):
    return math.hypot(x - sun_cx, (y - sun_cy) * 1.0) <= sun_r
# mottled surface: shade from the light, with a hot white core near the top-left lit side
shade_region(cv, sun_region, L, base_fg=9, hot_fg=15)
# hotter inner core (white-hot center, like v2's best element)
def core(x, y):
    return math.hypot(x - (sun_cx - 3), (y - (sun_cy - 3))) <= sun_r * 0.45
shade_region(cv, core, L, base_fg=15, hot_fg=15)

# ---- GROUND: warm red/orange ramp, bright at horizon fading down (carries shade density) ----
horizon_y = 33
for y in range(horizon_y, H):
    t = (y - horizon_y) / float(H - horizon_y)          # 0 at horizon -> 1 at bottom
    for x in range(W):
        # horizontal mottle so it's a textured plane, not a flat stripe-dump
        m = 0.5 + 0.35 * math.sin((x * 0.7) + y * 0.9)
        Lv = max(0.05, min(1.0, (1.0 - t) * 0.85 + 0.15 * m))
        from figure_common import shade
        ch, fg = shade(Lv, base_fg=9, hot_fg=6)
        cv[y][x] = [ch, fg, 0]

# ---- LONE FIGURE: a RESOLVED standing human on the left, backlit by the sun ----
# contrapposto stance + big head_scale so it reads as a person at this small scale.
fig = standing_figure(cv, hipx=16.0, hipy=27.0, Lfn=L,
                      height=15.0, stance="contrapposto",
                      base_fg=8, hot_fg=14, head_scale=1.9)

# warm backlit rim on the sun-facing (right) edge of the figure -- the right idea from v2,
# now tracing an actual body contour rather than the edge of a gray mass.
def rim(x, y):
    # thin band on the right side of the figure's silhouette
    return (14 <= x <= 20) and (fig['head_cy'] - 3 <= y <= fig.get('foot_lx', 32))
# paint a warm rim by re-shading the figure's right edge hotter
for y in range(int(fig['head_cy']) - 3, H):
    for x in range(W):
        cell = cv[y][x]
        if cell[0] != ' ' and 15 <= x <= 21:
            # warm backlit edge
            from figure_common import shade
            ch, fg = shade(0.95, base_fg=6, hot_fg=3)   # orange rim
            cv[y][x] = [ch, 3, 0]

# ---- render + signature ----
out = []
render(cv, out)
sig_block(out, "THE LAST LIGHT // a lone figure on the dying horizon", "raze,hollis / AGENTSCII")
raw = "\n".join(out) + "\x1b[0m\n"
open('scratch/_lastlight.v14.ans', 'w').write(raw)
print("wrote _lastlight.v14.ans, figure:", fig)
