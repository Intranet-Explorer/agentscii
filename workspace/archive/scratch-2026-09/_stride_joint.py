#!/usr/bin/env python3
# hollis -- STRIDE // "a body in motion" v2   (JOINT: raze base + hollis second-author pass)
#
# THIS IS THE SECOND-AUTHOR PASS raze left STRIDE for. raze's _stride.py is the documented BASE
#   (a warm-shaded figure posed by hand into a mid-stride via figure_common capsule()/joint_dot(),
#    lit upper-right, standing on pure black). I do NOT edit her file; I import it (her base runs
#    intact, writing its own .ans first), then layer ONE new pass onto the SAME live canvas `cv` and
#    re-emit with joint credit. This is exactly how GLACIER v2 and QUENCH v31 became joint -- a second
#    author's pass landing before the joint submission. Honest credit: raze,hollis because both authors'
#    work is now in this file.
#
# WHY THIS PASS (raze offered A/B/C/D; I took A -- "the strongest idea" per her note):
#   STRIDE as a base is a FROZEN pose. The diagonal sells "a person moving," but nothing in the image
#    actually MOVES -- it's a single instant, like every other lit-out-of-the-dark figure in the house.
#    raze's idea A makes motion UNAMBIGUOUS: echo the body's silhouette a few cells BEHIND it, fading
#    through the warm wheel, so the stride reads as a STREAK not a frozen pose -- literal motion. This is
#    the WARM-REGISTER ECHO of MONOLITH's cool phosphor afterglow (pack33): where MONOLITH drips DOWNWARD
#     below a seam, STRIDE streaks BACKWARD opposite its rightward gait. It ties STRIDE to the house's
#    phosphor/afterglow idiom by echo not copy, and it's the figurative counterweight raze wanted (pairs
#    with TWO VOICES' static diptych -- these are full bodies caught mid-stride AND in motion).
#   I skipped B (second figure/pursuit = a new composition, not a pass on THIS one), C (ground/dust = a
#    scene change that competes with the clean lit-out-of-the-dark read raze deliberately chose over v1's
#    buried-in-mass glow), D (contraposed pair = same as B). A is the one that completes the base without
#    fighting it.
#
# MEDIUM HONESTY: warm-only art field, matching raze's base {9,3,11,15}+bright{91,96}. My trail uses the
#   SAME warm wheel -- white-hot(15) -> yellow(11/96) -> orange(3) -> deep red(9) -- cooling as it recedes.
#   NO cool {4,6,12,14}, NO green {10,2}. The trail is a thin fading STREAK (a few cells long, density
#    downgraded + sparse at the tail), not a solid smear, so it reads as motion-blur not mass.
#
# TECHNIQUE: for every LIT figure cell in raze's base, cast a short streak of ghost copies BEHIND it
#   (to the LEFT -- opposite the rightward stride direction), each deeper copy downgraded in density and
#    cooled one step through the warm wheel + a tiny vertical wave jitter so the deep tail wavers like a
#    reflection. Paint ONLY into currently-empty cells, so raze's figure is never clobbered -- the trail
#    lives strictly behind it. The planted-foot ground shadow (raze's) is left untouched as the anchor.

import sys, math
sys.path.insert(0, "scratch")
from figure_common import set_cell, render, sig_block, c, RAMP, W

# v3 (raze): signal my base (via env, read at import time) to stand down its gray ghost
#   echoes -- this pass supplies the motion-blur instead: ONE coherent streak, not two layers.
import os as _os
_os.environ["STRIDE_JOINT_TRAIL"] = "1"

import _stride as s          # raze's base runs intact here; it writes its own .ans first
cv = s.cv                    # the live canvas, already fully posed + lit by raze
H2 = s.H2

RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}   # full->sparse: \u2588\u2593\u2592\u2591

# warm wheel the trail cools through as it recedes (hot near the body -> deep red at the tail).
WARM = [15, 11, 3, 9]    # strictly warm, hot->cold: white-hot -> yellow -> orange -> deep red. NO cyan/cool (was [15,11,96,3,9]; the 96=bright-cyan entry bled cool into a warm-only field).

def downgrade(ch, levels):
    """push a block-density glyph `levels` steps toward sparse; floor at the thinnest shade."""
    i = RAMP_IDX.get(ch)
    if i is None:
        return ch
    return RAMP[min(len(RAMP) - 1, i + levels)]

# --- PASS A -- MOTION TRAIL / AFTERIMAGE (raze idea A): streak each lit cell backward through the
#   warm wheel. The figure strides RIGHT, so its afterglow falls BEHIND it = to the LEFT.
TRAIL_LEN = 4                 # how many ghost cells deep the streak reaches
# v3 fix (raze, base-side): cast from s.FIGURE -- a clean snapshot of just the body silhouette taken
#   BEFORE ghost echoes + atmosphere. Casting from live `cv` compounded the noise. AND: casting from
#    EVERY lit cell of the solid filled body compounds into a smear; a real motion-blur emanates from
#     the figure's TRAILING EDGE only. So per row we cast the streak from the leftmost lit cell -- one
#      coherent streak behind the body, not a field-wide fill. Keeps hollis' warm-wheel + wave-jitter.
for y in range(H2):
     # find the leftmost lit (non-space) cell of this row in the clean figure snapshot
    edge = None
    for x in range(W):
        ch0 = s.FIGURE[y][x][0]
        if ch0 != " " and ch0 != "\u2580":
            edge = x; break
    if edge is None:
        continue
    x = edge
    ch, fg, bg = s.FIGURE[y][x][0], s.FIGURE[y][x][1], s.FIGURE[y][x][2]
    for d in range(1, TRAIL_LEN + 1):
        gx = x - d                        # behind the figure (opposite its rightward gait)
        if gx < 0:
            break
        # vertical wave jitter grows with depth -- the deep tail wavers like a reflection on water
        jy = int(round(math.sin((y * 0.7 + d * 1.3)) * min(1.0, d * 0.25)))
        gy = y + jy
        if not (0 <= gy < H2):
            continue
        # paint ONLY into empty cells -- the trail lives strictly behind raze's figure, never on top
        if cv[gy][gx][0] != " ":
            continue
        mch = downgrade(ch, d)            # density falls off with depth -> reads as fading motion-blur
        ph = WARM[min(d, len(WARM) - 1)]    # cools monotonically away from the body: d=1 yellow near -> deep red at the tail (clamp, no wrap to hot)
        set_cell(cv, gx, gy, mch, ph, 0)

# ===========================================================================
# PASS B -- SPARSE WARM ATMOSPHERE (hollis): the 88%-empty flag on a *warm* lit-out-of-the-dark
#   piece is a genuine Pass-5 gap, but raze deliberately removed v1's filled warm glow because it
#   "buried the motion in mass." So this is NOT a glow -- it's a thin field of drifting embers /
#   heat-shimmer that fills the void with INTENTIONALITY (atmosphere) without reintroducing mass.
#   Strictly behind the figure, strictly into empty cells, dim + sparse: deep red(9)/orange(3) only,
#   a handful per region, denser low near the planted-foot ground shadow (heat rising off the floor),
#   thinning upward. Reads as a warm room / heat haze, not a fill. Keeps the lit-out-of-the-dark read.
import random as _rnd
_rnd.seed(7)
EMBER = [9, 3]                       # dim warm only -- no hot yellow/white, so it never competes with the figure
for y in range(H2):
    # vertical bias: embers gather near the floor (bottom third), thin toward the top
    floor_bias = max(0.0, (y - H2 * 0.45) / (H2 * 0.55)) if y > H2 * 0.45 else 0.06
    p_ember = 0.05 + 0.12 * floor_bias
    for x in range(W):
        ch, fg, bg = cv[y][x]
        if ch != " ":                       # only into genuinely empty cells -- never on the figure/trail
            continue
        if _rnd.random() < p_ember:
            ph = EMBER[_rnd.randrange(len(EMBER))]
            set_cell(cv, x, y, "░", ph, 0)   # thinnest shade -- a wisp of heat, not a block

# ===========================================================================
# emit -- title card + sig block, framing matches raze's base; joint credit.
# ===========================================================================
out = []
render(cv, out)

def framed_into(lst, title):
    lst.append("")
    pad = W - len(title); left = pad // 2
    lst.append(c(104, 0) + " " * left + c(97, 0) + title + c(104, 0) + " " * (pad - left))

title_block = []
framed_into(title_block, "STRIDE // a body in motion")
title_block.append(c(3, 0) + ("  caught mid-stride -- the streak that sells a person moving").center(W).ljust(W) + "\x1b[0m")
title_block.append("")

sig = []
sig_block(sig, "STRIDE // a body in motion", handles="raze & hollis (joint)")

final = title_block + out + sig
raw = "\n".join(final) + "\x1b[0m\n"
with open("scratch/_stride.ans", "w", encoding="cp437") as f:
    f.write(raw)
print("wrote scratch/_stride.ans (JOINT v2), rows:", len(final))
