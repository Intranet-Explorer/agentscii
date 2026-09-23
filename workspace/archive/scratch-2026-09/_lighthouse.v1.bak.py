#!/usr/bin/env python3
# raze -- LIGHTHOUSE // "a beam across the dark water"   (AGENTSCI maritime/night register)
#
# The 3rd piece of hollis's maritime/night batch she's holding a pack for:
#    LOW TIDE (the wharf at dusk, quiet) + MOTION SEED (the procession walking)
#    + LIGHTHOUSE (the light that guides them). No lighthouse exists in the catalog --
#    this is genuinely new, not a re-drop. Grounded in del-jaws.ans's scene tradition
#    (wordmark banner -> gradient-shaded water -> focal silhouette rising into frame ->
#    tagline), executed in the lean "one light across a wide dark field" register of the
#    lit-in-the-dark suite (THE HORIZON / PROCESSION / THE WATCHER).
#
# WORLD-COHERENCE: reuses THE HORIZON / MOTION SEED's exact open/close idiom -- a boxed
#   title card up top + a dimmed closing credit band below, single in-canvas credit
#   sequence, manual \x1b[0m tail (no auto sig_block -> no double credits). Shares the
#   "one light across a wide dark field" idea; here that one light is WARM amber (the
#   keeper's lamp) against COLD blue-black night -- complementary contrast that gives this
#   piece its own identity while staying in the suite's register.
#
# COMPOSITION:
#   - faint dim night sky with a small cool moon up high (gives the upper field texture,
#     not dead void -- addresses MOTION SEED's "top void" ding)
#   - a lighthouse tower on a rocky point at left, dark silhouette with two band stripes,
#     lamp glowing warm at its crown
#   - TWO opposing beams from the lamp (the classic rotating double-cone): one dominant
#     sweeping down-right ACROSS THE WATER, one fainter up-right into the sky -- reads as
#     "rotating light," not a single static ray. Tight decay so it doesn't flood the frame
#     (MOTION SEED's v1 mistake was a sun that swallowed the top 2/3).
#   - calm sea: sparse horizontal ripple LINES (reused from _wharf's v7 technique), with a
#     broken warm reflection path under the down-beam tying the lamp into the water.
#
# TECHNIQUE: figure_common primitives (set_cell / shade / light_field) + canvas idiom,
#   beam cones built by ray-projection math (widening wedge, cylindrical falloff).

import sys, math
sys.path.insert(0, 'scratch')
from figure_common import (new_canvas, set_cell, shade, light_field,
                          render as fc_render, hygiene_gate)

W = 80
H = 52
cv = new_canvas(H, W)

# ---- the keeper's lamp: ONE warm light source, low on a point at left --------
LX, LY = 13.0, 16.0                       # lamp crown position
HORIZON = 34                              # sea line; tower base sits here

# ---- PASS 1: night sky -- faint dim texture + a small cool moon up high ------
for y in range(H):
    for x in range(W):
        if y < HORIZON:
            # sparse faint grey specks -> overcast night, not dead void
            if (x * 5 + y * 11) % 29 < 1:
                set_cell(cv, x, y, '\u00b7', 8, 0)

# small dim moon high-right -- a cool secondary cue, kept faint so the lamp is hero
MX, MY, MR = 64.0, 7.0, 2.0
for y in range(int(MY - MR) - 1, int(MY + MR) + 2):
    for x in range(int(MX - MR) - 1, int(MX + MR) + 2):
        d = math.hypot(x - MX, y - MY)
        if d <= MR:
            core = d <= MR * 0.5
            set_cell(cv, x, y, '\u2588' if core else '\u2593', 15 if core else 7, 0)

# ---- PASS 2: calm sea -- sparse horizontal ripple LINES (from _wharf v7) -----
# short undulating runs of blue ticks; density + brightness grow toward the bottom
# (nearer = more visible), thin out near the horizon (far = faint).
for wy in range(HORIZON + 1, H - 6, 2):
    depth = (wy - HORIZON) / max(1.0, (H - 7 - HORIZON))     # 0 at horizon -> 1 near bottom
    fg = 4 if depth < 0.5 else 12                            # far dim blue -> near bright blue
    ch = '\u2593' if depth > 0.6 else ('\u2591' if depth > 0.3 else '\u00b7')
    for x in range(0, W, 1):
        # gentle undulation + sparse: only some columns light up per row
        phase = math.sin((x * 0.5) + wy * 1.3)
        if (x % 3 == (wy % 3)) and phase > -0.2 and ((x + wy) % 7 < 4):
            set_cell(cv, x, wy, ch, fg, 0)

# ---- PASS 3: the lighthouse tower -- dark silhouette on a rocky point --------
# tapering structure: wider at base (sea level), narrower at crown (lamp). Two band
# stripes for legibility. A small rocky point under it drops into the water.
def tower(x, y):
    """True if (x,y) is inside the tapering tower body."""
    top_y, bot_y = LY + 1.0, HORIZON            # crown just below lamp -> base at sea
    t = (y - top_y) / max(1.0, (bot_y - top_y))   # 0 at crown -> 1 at base
    halfw = 1.0 + t * 3.5                          # narrow up top, wide at base
    return abs(x - LX) <= halfw and top_y <= y <= bot_y

for y in range(int(LY), HORIZON + 1):
    for x in range(int(LX - 5), int(LX + 6)):
        if tower(x, y):
            # two warm-grey band stripes near the middle (classic lighthouse bands)
            band = (abs(y - (LY + 4)) <= 0.5) or (abs(y - (HORIZON - 3)) <= 0.5)
            fg = 11 if band else 8               # warm-grey stripe vs dark body
            set_cell(cv, x, y, '\u2588', fg, 0)

# rocky point under the tower -- a few jagged grey cells dropping into the water
for (rx, ry) in [(LX - 4, HORIZON + 1), (LX - 3, HORIZON + 2), (LX - 1, HORIZON + 1),
                 (LX + 1, HORIZON + 2), (LX + 3, HORIZON + 1), (LX + 4, HORIZON + 1)]:
    set_cell(cv, int(rx), int(ry), '\u2592', 8, 0)

# ---- PASS 4: the lamp -- warm core + glow at the crown ----------------------
for y in range(int(LY - 2), int(LY + 3)):
    for x in range(int(LX - 2), int(LX + 3)):
        d = math.hypot(x - LX, y - LY)
        if d <= 1.8:
            core = d <= 0.6
            set_cell(cv, x, y, '\u2588', 15 if core else 11, 0)   # white-hot core, amber ring

# ---- PASS 5: the BEAMS -- two opposing cones from the lamp (rotating light) ---
def beam(angle_deg, length, hw_end, decay, fg_hot=15, fg_warm=11):
    """A widening wedge of warm light along a ray. Ray-projection math: project each
    cell onto the axis (t = distance along), keep it if its perpendicular offset p is
    within the half-width at that t (grows linearly -> a cone). Brightness falls off with
    distance (exp decay) and across the width (cylindrical term)."""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)            # screen y is down
    for y in range(0, H - 5):
        for x in range(0, W):
            dx, dy = x - LX, y - LY
            t = dx * ux + dy * uy                # distance along the beam axis
            if t < 0.5 or t > length:
                continue
            p = abs(-dx * uy + dy * ux)          # perpendicular offset from the ray
            hw = 0.4 + (hw_end - 0.4) * (t / length)   # widening wedge
            if p <= hw:
                b = math.exp(-t / decay) * (1.0 - 0.5 * (p / hw))
                if b < 0.12:
                    continue
                ch = '\u2588' if b > 0.7 else ('\u2593' if b > 0.4 else '\u2591')
                fg = fg_hot if b > 0.6 else (fg_warm if b > 0.3 else 3)
                # don't overwrite the tower body / lamp core with beam
                cur = cv[y][x]
                if not (cur[1] in (8, 11) and cur[0] == '\u2588' and y >= int(LY)):
                    set_cell(cv, x, y, ch, fg, 0)

# dominant beam: down-right ACROSS THE WATER (the one that casts the reflection)
beam(28.0, 70.0, hw_end=6.0, decay=34.0)
# fainter opposing beam: up-right into the SKY (reads as "rotating," not static)
beam(-18.0, 58.0, hw_end=4.0, decay=30.0, fg_hot=11, fg_warm=3)

# ---- PASS 6: broken warm REFLECTION on the water under the down-beam ---------
# a vertical-ish shimmering path of amber ticks, broken (gaps), thinning downward --
# the lamp's light caught on the sea surface. Ties the single warm accent into the water.
for ry in range(HORIZON + 1, H - 5):
    depth = (ry - HORIZON) / max(1.0, (H - 6 - HORIZON))
    # reflection drifts right as it goes down (beam angle) and breaks up with distance
    cx = int(LX + depth * 9.0 + math.sin(ry * 1.7) * 1.5)
    if (ry % 2 == 0) and ((ry * 3) % 5 != 0):       # broken: skip some rows
        for dx in (-1, 0, 1):
            xx = cx + dx
            if 0 <= xx < W and abs(dx) <= (1 if depth < 0.5 else 2):
                fg = 11 if depth < 0.4 else (3 if depth < 0.7 else 8)
                set_cell(cv, xx, ry, '\u2593' if depth < 0.6 else '\u2591', fg, 0)

# ---- PASS 7: boxed title card + dimmed closing credit band (THE HORIZON idiom) --
RULE = '\u2550'
QUAD = '\u2592'
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        set_cell(cv, x + i, y, ch, fg, 0)

x0, x1 = 3, W - 4
y0, y1 = 1, 7
for x in range(x0, x1 + 1):
    set_cell(cv, x, y0, RULE, 12, 0)
    set_cell(cv, x, y1, RULE, 12, 0)
for y in range(y0, y1 + 1):
    set_cell(cv, x0, y, RULE, 12, 0)
    set_cell(cv, x1, y, RULE, 12, 0)
for x in range(x0 + 1, x1):
    set_cell(cv, x, y0 + 1, QUAD, 8, 0)
    set_cell(cv, x, y1 - 1, QUAD, 8, 0)
for y in range(y0 + 2, y1 - 1):
    set_cell(cv, x0 + 1, y, QUAD, 8, 0)
    set_cell(cv, x1 - 1, y, QUAD, 8, 0)
put_centered("LIGHTHOUSE", y0 + 2, 15)
put_centered("// a beam across the dark water //", y0 + 4, 8)

cy = H - 6
for x in range(W):
    set_cell(cv, x, cy, RULE, 12, 0)
put_centered("LIGHTHOUSE", cy + 2, 11)
put_centered("// the light that guides them //", cy + 3, 8)
put_centered("raze / AGENTSCII", cy + 4, 14)
for x in range(W):
    set_cell(cv, x, cy + 5, RULE, 12, 0)

# ---- render + write: ONE credit sequence (in-canvas), standalone reset tail ---
out = []
fc_render(cv, out)
path = 'scratch/_lighthouse.ans'
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print('wrote', path, '-- LIGHTHOUSE v1; rows:', len(out))
