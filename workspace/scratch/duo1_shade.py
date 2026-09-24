#!/usr/bin/env python3
"""duo1 pass 2 -- light-source shading ONLY. One light: top-left, high.

The binding constraint is that the block-in reads blind as "a hand pressed
against a window", and that read is carried entirely by SILHOUETTE
(occlusion of the transom by the fingers, of the mullion by the thumb).
So this pass is built so it *cannot* move a silhouette edge: every lit
volume is drawn with the real canvas_* tool, then every pixel the tool
touched OUTSIDE that element's block-in colour mask is restored from a
snapshot taken immediately before the call.  Value changes, shape does not.

The pane itself is NOT touched here.  It is the background field, and
field texture is a later pass -- and the first attempt proved why: a
4 -> 0 slab over the full pane dithered its lower-right to black, the
black break-hole stopped being a hole, and the piece went to "a shape on
a noisy field".  That is the lighthouse failure exactly.  The hand is the
only form in this pass that gains light; the bars keep a solid body and
gain only a lit top/left edge.
"""
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import canvas_tools as ct  # noqa: E402

W = str(Path(__file__).resolve().parents[1])
SRC, SLUG = "duo1_blockin", "duo1"
PANE, VOID, BAR, HAND = 4, 0, 8, 6
LIGHT = "top-left"

src = ct.load_canvas(W, SRC)
ORIG = deepcopy(src["pixels"])
PH, CW = src["ph"], src["w"]
ct.save_canvas(W, SLUG, deepcopy(src))


def lit(keep_color, fn, *a, **kw):
    """Run a lit-volume tool, then clip its result to `keep_color`'s
    block-in mask -- restoring colour AND dropping any dither glyph on a
    cell that straddles the mask edge (a flat glyph_override there would
    wipe the half-block boundary that carries the occlusion)."""
    before = deepcopy(ct.load_canvas(W, SLUG))
    fn(W, SLUG, *a, **kw)
    after = ct.load_canvas(W, SLUG)
    for y in range(PH):
        for x in range(CW):
            if ORIG[y][x] != keep_color:
                after["pixels"][y][x] = before["pixels"][y][x]
    for key in list(after["glyph_override"]):
        if before["glyph_override"].get(key) == after["glyph_override"][key]:
            continue
        row, col = (int(v) for v in key.split(","))  # glyph_override is "row,col"
        if not all(ORIG[row * 2 + i][col] == keep_color for i in (0, 1)):
            after["glyph_override"].pop(key, None)
            if key in before["glyph_override"]:
                after["glyph_override"][key] = before["glyph_override"][key]
    ct.save_canvas(W, SLUG, after)


# 1. casement bars -- lit top/left edge in 7, body stays solid 8.  Letting
#    them fall to black instead dissolved them into dashes and the bar a
#    finger interrupts has to stay a bar for the occlusion to read.
for bx, by, bw, bh in [(0, 0, 5, 100), (75, 0, 5, 100),
                       (0, 26, 80, 4), (20, 0, 3, 100)]:
    lit(BAR, ct.slab_px, bx, by, bw, bh, BAR,
        light_direction=LIGHT, shadow_color=BAR, hi_color=7)

# 2. the hand -- the one lit thing.  Forearm first (deepest, inside the
#    hole, shaded by the pane), then palm, then thumb and fingers on top.
# forearm: no highlight at all -- it is inside the hole, shaded by the
# pane, so it stays the dimmest hand form.  Its shadow also stops at the
# base cyan: ramping it to 4 split the arm into a cyan half and a blue
# half that read as two objects.
lit(HAND, ct.capsule_px, 40, 66, 40, 100, 8, HAND,
    light_direction=LIGHT, shadow_color=HAND, hi_color=HAND)
lit(HAND, ct.sphere_px, 40, 52, 14, HAND, 26, 38,
    shadow_color=HAND, hi_color=14)
for ax, ay, bx, by, r in [(28, 57, 15, 43, 4),   # thumb
                          (32, 43, 28, 12, 3),   # index
                          (39, 42, 38, 8, 3),    # middle
                          (46, 43, 48, 13, 3),   # ring
                          (52, 45, 57, 21, 3)]:  # pinky
    # shadow_color=HAND, not PANE: shading the dark flank toward 4 dithers
    # the finger's right side into the pane colour and the fingers shred.
    # Highlight-only keeps the hand's floor at its own base value, so no
    # part of the figure can dissolve into the field behind it.
    lit(HAND, ct.capsule_px, ax, ay, bx, by, r, HAND,
        light_direction=LIGHT, shadow_color=HAND, hi_color=14)

out = ct.load_canvas(W, SLUG)
assert out["pixels"] != ORIG, "nothing changed"
flat = sum(1 for y in range(PH) for x in range(CW)
           if ORIG[y][x] == HAND and out["pixels"][y][x] == HAND
           and f"{y // 2},{x}" not in out["glyph_override"])
print("hand px left flat:", flat, "/", sum(r.count(HAND) for r in ORIG))
ct.save_ans(W, SLUG, "scratch/duo1.ans", title=None, add_sig=False)
print(ct.metrics(W, SLUG))
