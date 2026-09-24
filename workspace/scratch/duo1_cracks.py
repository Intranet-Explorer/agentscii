#!/usr/bin/env python3
"""duo1 pass 3 -- CRACKS ONLY.

Four short hairlines radiating out of the break rim, two per side, each
with one fork.  Nothing else is touched.

Two rules are enforced by the walker, not by hand-picked endpoints:
  - a crack DIES the instant it meets the hand (6/14) or a bar (8/7).
    The hand is in front of the pane; a crack that crosses it kills the
    occlusion that makes this read as a window at all.
  - a crack only marks pixels that are currently pane.  Where it passes
    over the hole or an existing wedge it draws nothing and carries on,
    so the new lines read as continuations of the break, not as a second
    system of marks laid over it.

Short and few on purpose: texture spread over a whole surface is how a
subject gets lost.  Four lines and two forks, all inside the middle band
either side of the hand, none within 4 px of a jamb.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import canvas_tools as ct  # noqa: E402

W = str(Path(__file__).resolve().parents[1])
SLUG = "duo1"
PANE, VOID, LIT = 4, 0, 12
STOP = {6, 14, 8, 7}          # hand and casement both terminate a crack
DRAWABLE = {PANE, LIT}

d = ct.load_canvas(W, SLUG)
px = d["pixels"]
PH, CW = d["ph"], d["w"]

# (x0, y0, x1, y1) -- all four start on the break rim and run outward.
CRACKS = [
    (20, 68, 9, 57),     # up-left off the rim
    (14, 62, 8, 67),     # its fork, down-left
    (60, 64, 71, 53),    # up-right off the rim
    (66, 58, 72, 63),    # its fork, down-right
]

drawn = 0
for x0, y0, x1, y1 in CRACKS:
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2)
    for i in range(n + 1):
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if not (0 <= x < CW and 0 <= y < PH):
            break
        if px[y][x] in STOP:
            break                      # dies at the hand / at a bar
        if px[y][x] not in DRAWABLE:
            continue                   # over the void: no mark, keep going
        px[y][x] = VOID
        drawn += 1
        # glass bevel: hairline on the upper-left lip only, top-left light
        for lx, ly in ((x - 1, y), (x, y - 1)):
            if 0 <= lx < CW and 0 <= ly < PH and px[ly][lx] == PANE:
                px[ly][lx] = LIT

assert 25 < drawn < 90, f"crack budget blown: {drawn} px"
print("crack px:", drawn)
ct.save_canvas(W, SLUG, d)
ct.save_ans(W, SLUG, "scratch/duo1.ans", title=None, add_sig=False)
print(ct.metrics(W, SLUG))
