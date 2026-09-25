#!/usr/bin/env python3
"""duo2 pass 1 -- shading, with the glyph layer carrying the form.

Retrieval before this pass:
  find_patches_clip('shaded knuckles and finger contours')
    -> 2003/evoke03/daisy2.ans, 1995/uni-0395/KS-BLA01.ANS
  find_patches_clip('directional strokes following a cylinder')
    -> 1994/cnc-0494/HTF-PUBE.ANS
See duo2_common for the technique those three share and how it is
reproduced here.

What is modelled, beyond "a lit tube":

The hand is PALM-FORWARD and PRESSED ON GLASS. So there are no knuckles
to shade -- the palm-side forms are the thenar mound at the thumb base,
the hypothenar along the little-finger edge, and the hollow between
them; the flexion creases fall ACROSS each finger at the joints; and
every pad actually touching the pane blanches -- flattens and goes pale
where the blood is pushed out. That last one is the only thing in the
piece that says the hand is in contact rather than floating, and it is
glyph work: a bright flat core inside a still-round finger.

The pane is not touched here (pass 2). Ramping the field to black is
what killed the previous attempt -- the hole stopped reading as a hole.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duo2_common as D  # noqa: E402

mask = D.load_blockin()
val = [[None] * D.CW for _ in range(D.PH)]

# --- forms, in depth order: later ones own the pixels they share ------
# (ax, ay, bx, by, r, lo, hi, creases, blanch)
#   lo/hi   remap the tube's own 0..1 into the piece's value range --
#           the forearm is inside the hole and never catches the source.
#   creases positions along t of the flexion folds.
#   blanch  t of the pad pressed flat on the glass (fingertips, thumb).
FINGERS = [
    (28, 57, 15, 43, 4, 0.10, 0.92, (0.30, 0.68), 0.93),   # thumb
    (32, 43, 28, 12, 3, 0.12, 1.00, (0.34, 0.70), 0.90),   # index
    (39, 42, 38, 8, 3, 0.12, 1.00, (0.32, 0.68), 0.90),    # middle
    (46, 43, 48, 13, 3, 0.10, 0.96, (0.33, 0.69), 0.90),   # ring
    (52, 45, 57, 21, 3, 0.08, 0.90, (0.35, 0.72), 0.90),   # pinky
]


HAND_FLOOR = 0.13     # see cell_from_values: below ~0.05 a hand cell goes
                      # solid pane-colour and the finger dissolves into the
                      # field; the floor keeps every hand cell a cyan-over-
                      # blue shade glyph, so the figure always reads.


def put(x, y, v):
    if 0 <= x < D.CW and 0 <= y < D.PH and mask[y][x] == D.HAND:
        val[y][x] = max(HAND_FLOOR, D.clamp01(v))


# 1. forearm -- deepest, held near shadow throughout, and the ONE place
#    the piece can say "through" with value: the broken pane's upper rim
#    sits in front of the arm and drops a shadow across it around y 70.
#    Without it the arm is a perfectly repeating column of identical
#    rows, which is a fill with a ramp painted on it.
for y in range(D.PH):
    for x in range(D.CW):
        r = D.capsule_light(x, y, 40, 66, 40, 101, 8)
        if r:
            v = 0.04 + 0.40 * r[0]
            v -= 0.16 * 2.718 ** (-((y - 72) / 7.0) ** 2)   # rim shadow
            v -= 0.09 * (y - 66) / 34.0                     # falls off down
            put(x, y, v)

# 2. palm -- a sphere, then the three palm-side masses on top of it.
#    thenar/hypothenar are raised pads, the hollow between them is the
#    only part of a pressed palm NOT touching the glass, so it stays
#    the darkest thing on the front plane.
for y in range(D.PH):
    for x in range(D.CW):
        v = D.sphere_light(x, y, 40, 52, 14)
        if v is None:
            continue
        v = 0.16 + 0.80 * v
        for cx, cy, rr, amt in ((31, 59, 9, 0.26),    # thenar (thumb base)
                                (50, 60, 7, 0.17),    # hypothenar
                                (41, 51, 7, -0.16)):  # palm hollow
            d = ((x - cx) ** 2 + ((y - cy) * 0.8) ** 2) ** 0.5 / rr
            if d < 1.0:
                v += amt * (1.0 - d * d)
        put(x, y, v)

# 3. thumb and fingers -- lit tubes, each with its flexion creases and
#    its blanched contact pad.
for ax, ay, bx, by, r, lo, hi, creases, blanch in FINGERS:
    for y in range(D.PH):
        for x in range(D.CW):
            res = D.capsule_light(x, y, ax, ay, bx, by, r)
            if not res:
                continue
            v, t = res
            v = lo + (hi - lo) * v
            for tc in creases:                       # fold across the tube
                v -= 0.34 * 2.718 ** (-((t - tc) / 0.05) ** 2)
            if t > blanch - 0.16:                    # pad flat on the glass
                k = min(1.0, (t - (blanch - 0.16)) / 0.16)
                v += 0.30 * k
            put(x, y, v)

n = D.paint(mask, D.HAND, val, (4, 6, 14), dither=0.02)

# 4. casement bars -- the only forms in the PANE plane with thickness,
#    so they are what sells the surface. A bar is a box: its lit face is
#    the one turned to the source, top for the transom, left for the
#    uprights, and the value falls straight across the width. No
#    silhouette moves; the bars stay solid bars, because a bar a finger
#    interrupts has to stay a bar for the occlusion to read.
bval = [[None] * D.CW for _ in range(D.PH)]
for bx, by, bw, bh, vert in [(0, 0, 5, 100, True), (75, 0, 5, 100, True),
                             (0, 26, 80, 4, False), (20, 0, 3, 100, True)]:
    for y in range(by, by + bh):
        for x in range(bx, bx + bw):
            if not (0 <= x < D.CW and 0 <= y < D.PH):
                continue
            f = (x - bx) / max(1, bw - 1) if vert else (y - by) / max(1, bh - 1)
            # held inside the TOP band only (░▒▓ of 7 over 8): let a bar
            # ramp down through the tiers and it dissolves into a dashed
            # ladder, and the occlusion cue needs it to stay a solid bar.
            # The single tier crossing at the lit edge is the thickness.
            bval[y][x] = D.clamp01(0.82 - 0.31 * f)
nb = D.paint(mask, D.BAR, bval, (0, 8, 7), dither=0.02)

D.ct.save_ans(D.W, D.SLUG, "scratch/duo2.ans", title=None, add_sig=False)
print("hand cells glyphed:", n, " bar cells:", nb)
print(D.ct.metrics(D.W, D.SLUG))
