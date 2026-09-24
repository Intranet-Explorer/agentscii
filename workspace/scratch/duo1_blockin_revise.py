#!/usr/bin/env python3
"""duo1 block-in, revision 2 -- give the pane a PLANE CUE.

Blind viewer read v1 as "a hand reaching up from the ground": the pane was
a featureless blue field, so radiating cracks defaulted to cracked earth.
This rebuilds everything EXCEPT the hand (the hand is snapshotted by colour
and pasted back untouched at the end):

  - window casement: two jambs + a transom + one vertical mullion, in flat
    grey 8.  The transom passes BEHIND the four fingers and the mullion
    BEHIND the thumb -- occlusion by the hand is the depth cue, and it is
    pure silhouette, no shading needed.
  - the mullion is destroyed where the hole is, and reappears as a stub in
    the pane below the hole's closed lower rim.
  - shards hang DOWN off the hole's upper rim into the void: glass hangs,
    ground does not.
  - cracks re-aimed: they now radiate UP the pane as well as sideways, and
    each one dies where it meets a bar (separate light = separate glass).

Still block-in: flat single-colour regions only, no shading, no texture,
no frame pass, no signature.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import canvas_tools as ct  # noqa: E402

W = str(Path(__file__).resolve().parents[1])
SLUG = "duo1_blockin"
PANE, VOID, BAR, HAND = 4, 0, 8, 6

# --- keep the hand ---------------------------------------------------------
hand = [(x, y)
        for y, row in enumerate(ct.load_canvas(W, SLUG)["pixels"])
        for x, c in enumerate(row) if c == HAND]
assert len(hand) > 2000, f"hand mask looks wrong: {len(hand)} px"

ct.fill_px(W, SLUG, 0, 0, 80, 100, PANE)   # wipe back to bare pane

# --- cracks (drawn first: bars and void cut them) --------------------------
CRACKS = [  # (x0, y0, x1, y1, w0, w1)
    (56, 55, 60, 30, 3, 1),   # up, dies at the transom
    (63, 59, 73, 33, 4, 1),   # up-right, dies at the transom
    (14, 64, 6, 40, 3, 1),    # up-left, left of the mullion
    (11, 72, 0, 76, 4, 1),    # lateral, dies at the jamb
    (68, 71, 79, 66, 4, 1),   # lateral, dies at the jamb
    (22, 92, 8, 99, 3, 1),    # down-left
    (60, 93, 74, 99, 3, 1),   # down-right
]
for x0, y0, x1, y1, w0, w1 in CRACKS:
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2)
    for i in range(n + 1):
        t = i / n
        w = max(1, round(w0 + (w1 - w0) * t))
        ct.fill_px(W, SLUG, round(x0 + (x1 - x0) * t - w / 2),
                   round(y0 + (y1 - y0) * t), w, 1, VOID)

# --- casement: jambs, transom, mullion -------------------------------------
ct.fill_px(W, SLUG, 0, 0, 5, 100, BAR)     # left jamb
ct.fill_px(W, SLUG, 75, 0, 5, 100, BAR)    # right jamb
ct.fill_px(W, SLUG, 0, 26, 80, 4, BAR)     # transom, behind the fingers
ct.fill_px(W, SLUG, 20, 0, 3, 100, BAR)    # mullion, behind the thumb

# --- the break: jagged hole, teeth alternating long/short ------------------
CX, CY, RX, RY = 40.0, 74.0, 31.0, 22.0
JIT = [0.02, -.06, .08, -.03, .05, .09, -.07, .03,
       .06, -.04, .02, .07, -.05, .04, .08, -.02]
verts = []
for i in range(16):
    a = 2 * math.pi * i / 16
    r = (1.0 if i % 2 == 0 else 0.70) + JIT[i]
    verts.append((CX + RX * r * math.cos(a), CY + RY * r * math.sin(a)))

for y in range(0, 100):
    xs = []
    for i in range(16):
        (ax, ay), (bx, by) = verts[i], verts[(i + 1) % 16]
        if (ay <= y < by) or (by <= y < ay):
            xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
    if len(xs) >= 2:
        lo, hi = round(min(xs)), round(max(xs))
        ct.fill_px(W, SLUG, lo, y, hi - lo + 1, 1, VOID)

# --- shards hanging off the upper rim --------------------------------------
# (x, hang length, half-width at the rim) -- kept clear of the forearm.
px = ct.load_canvas(W, SLUG)["pixels"]
for sx, length, hw in [(12, 9, 3), (19, 14, 4), (26, 10, 3),
                       (53, 12, 4), (61, 8, 3), (67, 13, 4)]:
    rim = next((y for y in range(40, 97) if px[y][sx] == VOID), None)
    if rim is None:
        continue
    for d in range(length):
        w = max(1, round(2 * hw * (1 - d / length)))
        ct.fill_px(W, SLUG, sx - w // 2, rim + d, w, 1, PANE)

# --- hand back on top, unchanged -------------------------------------------
d = ct.load_canvas(W, SLUG)
for x, y in hand:
    d["pixels"][y][x] = HAND
ct.save_canvas(W, SLUG, d)

ct.save_ans(W, SLUG, "scratch/duo1.blockin.ans", title=None, add_sig=False)
print(ct.metrics(W, SLUG))
