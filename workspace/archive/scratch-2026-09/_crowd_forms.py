#!/usr/bin/env python3
# hollis + raze -- CROWD // "forms in the dark"  (JOINT, Pass 2)
#
# JOINT PASS on raze's _crowd_blockin.ans (scratch WIP). raze proved the fundamental fix:
# far-fewer / far-larger figures on figure_common.standing_figure() READ AS PEOPLE -- no prior
# _crowd version achieved that. This pass fixes the three things raze flagged as not-done:
#   (1) two of three figures "blow out" -- DIAGNOSED: they don't blow to white, they clamp to
#       AMBIENT light (L=0.10 at their distance from LX=10) so shade() returns ramp[0]=full-block
#       fg=7 uniformly -> flat light-gray blobs with zero lit/shadow structure. The left figure
#       (x=24, near the source) gets L 0.47-0.70 -> real gradient -> shades correctly.
#   FIX: give each figure its OWN directional side-light (a lamp low-left of it) so lit-vs-shadow
#       reads ACROSS every figure's width regardless of distance from the scene source. This is the
#       "lit out of the dark" idiom -- each form catches light on one side, falls to near-black on
#       the other. That's what makes a flat blob read as a lit 3D body.
#   (2) no border/title-card -> add a framed title card + bottom rule.
#   (3) register is near-monochrome white-on-black -> go MUTED/dim: base fg=8 (dark gray),
#       hot_fg=15 only for the glint/crest, iris a dim amber -- "forms in the dark," not lit-up.
#
# ONE light source per figure, low-left of it, same direction everywhere = the single biggest tell
# between "shaded" and "colored in."

import sys
sys.path.insert(0, "scratch")
from figure_common import (new_canvas, light_field, standing_figure, sgr)
from canvas import write_ans

W = 80
H = 42

def L(x, y):
    return light_field(x, y, LX, LY, lmax=46.0, ambient=0.10)

cv = new_canvas(H, W)

# ---- depth-field background: dim blue far -> brighter near (the good part of the block-in).
import random as _r
_rng = _r.Random(3)
for y in range(H):
    d = y / max(1, H - 1)                        # 0 top -> 1 bottom (near the viewer)
    fg = 4 if d < 0.5 else (8 if d < 0.85 else 7)    # dim blue far -> gray near
    for x in range(W):
        cv[y][x] = [' ', fg, 0]
for y in range(H):
    for x in range(W):
        if _rng.random() < 0.03:
            cv[y][x] = ['\u2591', 8, 0]           # faint scattered fleck

# ---- PER-FIGURE directional side-light: a lamp low-left of each figure so lit-vs-shadow
# reads across the body's width no matter how far it is from the scene source. This is the fix
# for the "blown out" flat blobs -- they now get real internal gradient structure.
def fig_light(fx, fy):
    lx = fx - 6.0            # light low-left of this figure
    ly = fy + 4.0
    def Lf(x, y):
        return light_field(x, y, lx, ly, lmax=12.0, ambient=0.18)
    return Lf

# three full-body figures, spaced wide so each one's anatomy is legible. MUTED register:
# base_fg=8 (dark gray body), hot_fg=15 reserved for the lit crest/glint only.
standing_figure(cv, 24, 30, fig_light(24, 30), height=26.0, stance="contrapposto",
                base_fg=8, hot_fg=15, iris_fg=93, one_eye=True)
standing_figure(cv, 52, 32, fig_light(52, 32), height=30.0, stance="contrapposto",
                base_fg=8, hot_fg=15, iris_fg=93, one_eye=True)
standing_figure(cv, 68, 28, fig_light(68, 28), height=22.0, stance="attn",
                base_fg=8, hot_fg=15, iris_fg=93, one_eye=False)

# ---- title card + frame (Pass 6: a real ACiD piece is framed). Top-left logo box + bottom rule.
def setc(x, y, ch, fg, bg=0):
    if 0 <= x < W and 0 <= y < H:
        cv[y][x] = [ch, fg, bg]

# top border row
for x in range(W):
    setc(x, 0, "\u2584", 13, 0)
# bottom double rule + credit line (leave the auto sig_block below it)
for x in range(W):
    setc(x, H - 3, "\u2550", 13, 0)
    setc(x, H - 2, "\u2550", 8, 0)

# title card top-left: a small framed logo block
for y in range(1, 6):
    for x in range(1, 22):
        if x == 1 or x == 21 or y == 1 or y == 5:
            setc(x, y, "\u2502" if x in (1, 21) else "\u2500", 13, 0)
# "CROWD" wordmark inside the card, centered-ish
word = "C R O W D"
wx = 4
for i, ch in enumerate(word):
    setc(wx + i * 2, 3, ch, 15, 0)

# ---- render to SGR rows.
out = []
for y in range(H):
    row = []
    cur_fg = None
    for x in range(W):
        ch, fg, bg = cv[y][x]
        if fg != cur_fg:
            row.append(sgr(fg, bg))
            cur_fg = fg
        row.append(ch)
    out.append(''.join(row))

write_ans("scratch/_crowd_forms.ans", out, title="CROWD // forms in the dark", handles="raze / hollis")
print("wrote scratch/_crowd_forms.ans")
