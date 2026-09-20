#!/usr/bin/env python3
"""STRIDE -- full-body figure in motion, from a random_direction roll:
subject "a full-body figure in motion", technique "canvas.mirror() for bilateral
symmetry", palette "muted/dim, low-saturation throughout".

REMX: kept the subject + mirror() move + muted palette; REJECTED the implicit
high-contrast lean (house has done lit-out-of-the-dark enough). The tension of
the piece: build the body's *silhouette* via mirror(axis='v') so it's perfectly
bilateral, then let the MOTION break that symmetry -- one leg/limb strides
forward while a trailing ghost of the figure dissolves behind. Muted dim register
throughout (deep blue shadow -> gray -> a single restrained highlight), NOT bright
saturated accents and NOT high-contrast lit-out-of-the-dark.

v1->v2 fixes (from my own preview by eye): v1 used figure_common.shade() which
emits BRIGHT ansi codes (96/97/91/95) so it was never actually "muted/dim", and a
160-strand pass shredded the silhouette into noise so the signature move didn't read.
v2: genuinely dim palette, NO destructive strand pass -- the clean lit silhouette +
the legible dissolving ghost trail ARE the texture, not competing strokes.

PASS PLAN (METHODOLOGY):
 1. void background (dim, textured)
 2. build LEFT half of body silhouette via capsule/joint_dot -> mirror() to right
      => bilateral symmetric base figure
 3. BREAK symmetry: stride the lead leg + arm forward; trail a dissolving ghost
    of the prior pose behind (motion, not static mannequin)
 4. texture_fill the negative space (atmosphere, dim)
 5. frame + title card
"""
import sys, math
sys.path.insert(0, 'scratch')
import canvas as C
from figure_common import (new_canvas, set_cell, light_field, capsule, joint_dot,
                           shade_region, brow_ridge, RAMP)

W, H = 80, 46
cv = new_canvas(h=H, w=W)

# single dim light source, upper-left. Muted register: we remap the light value
# into a DIM gray->light-gray ramp with a deep-blue shadow floor, so nothing goes
# bright saturated and the whole figure stays low-key -- "muted/dim".
LX, LY = 26.0, 14.0

def L(x, y):
    return light_field(x, y, LX, LY, lmax=34.0, ambient=0.22)

# Muted dim palette: deep blue shadow floor -> gray body -> a single restrained
# highlight (light gray, not full white). Low saturation throughout.
SHADOW = 17           # deep blue -- the shadowed side of every surface
MID    = 8            # gray body base
HILITE = 245          # light gray -- only the very top of the light ramp touches this
GHOST = [240, 236, 231]   # ghost-trail grays, dimmer still (afterimage dissolving)

import figure_common as FC

def shade_dim(Lval, base_fg=8, hot_fg=15, ramp=RAMP):
    """MUTED override of figure_common.shade: same signature, but maps light into a
    dim gray->light-gray ramp with a deep-blue shadow floor instead of bright ansi
    codes. That's what makes the whole figure 'muted/dim' rather than lit-out-dark."""
    Lval = max(0.0, min(1.0, Lval))
    idx = int(Lval * (len(ramp) - 1) + 0.5) % len(ramp)
    if Lval < 0.30:
        fg = SHADOW            # shadowed side reads deep blue
    elif Lval > 0.86:
        fg = HILITE           # only the peak catches light gray
    else:
        fg = MID              # body mass is plain gray
    return ramp[idx], fg

FC.shade = shade_dim   # capsule/joint_dot/shade_region now use our dim shading

# ---------------------------------------------------------------- pass 1: void
for y in range(H):
    for x in range(W):
        set_cell(cv, x, y, ' ', 0, 0)

# ---------------------------------------------------------------- pass 2: build
# the LEFT half of a striding figure's silhouette, then mirror to the right.
MIDX = W // 2
HIPX, HIPY = MIDX - 1.0, 19.0
TORSO_H = 8.5
LEG_H   = 13.0
HEAD_R  = 2.6
shoulder_y = HIPY - TORSO_H
neck_y      = shoulder_y - HEAD_R * 0.4
head_cy     = neck_y - HEAD_R

# --- torso: S-curved spine (waist bend) so it's not a straight tube
spine_pts = [
    (HIPX, HIPY),
    (HIPX + 0.5, HIPY - TORSO_H * 0.33),
    (HIPX - 0.2, HIPY - TORSO_H * 0.66),
    (HIPX + 0.4, shoulder_y),
]
for i in range(len(spine_pts) - 1):
    capsule(cv, spine_pts[i][0], spine_pts[i][1], spine_pts[i+1][0], spine_pts[i+1][1],
            halfw=2.3 - i * 0.3, Lfn=L)

# --- shoulders (front shoulder drops a touch for the stride)
sh_dx = 2.5
joint_dot(cv, HIPX - sh_dx, shoulder_y + 0.5, 1.6, L)     # back shoulder
joint_dot(cv, HIPX + sh_dx, shoulder_y - 0.3, 1.6, L)     # front shoulder

# --- hips
hip_dx = 1.9
joint_dot(cv, HIPX - hip_dx, HIPY, 1.5, L)
joint_dot(cv, HIPX + hip_dx, HIPY, 1.5, L)

# --- head: 3/4 turned skull, lit upper-left
def head_region(x, y):
    return math.hypot(x - (HIPX + 0.4), y - head_cy) <= HEAD_R
shade_region(cv, head_region, L)
brow_ridge(cv, HIPX + 0.4, head_cy - HEAD_R * 0.25, HEAD_R * 0.8, L)

# --- BACK arm (left half): swings behind
back_sh = (HIPX - sh_dx, shoulder_y + 0.5)
back_elb = (HIPX - sh_dx - 1.3, shoulder_y + 3.2)
back_hand = (HIPX - sh_dx - 0.7, shoulder_y + 6.2)
capsule(cv, back_sh[0], back_sh[1], back_elb[0], back_elb[1], halfw=1.1, Lfn=L)
joint_dot(cv, back_elb[0], back_elb[1], 1.0, L)
capsule(cv, back_elb[0], back_elb[1], back_hand[0], back_hand[1], halfw=0.9, Lfn=L)

# --- BACK leg (left half): bent knee pushing off behind
back_hip = (HIPX - hip_dx, HIPY)
back_knee = (HIPX - hip_dx - 1.3, HIPY + LEG_H * 0.5)
back_foot = (HIPX - hip_dx - 2.4, HIPY + LEG_H * 0.96)
capsule(cv, back_hip[0], back_hip[1], back_knee[0], back_knee[1], halfw=1.6, Lfn=L)
joint_dot(cv, back_knee[0], back_knee[1], 1.3, L)
capsule(cv, back_knee[0], back_knee[1], back_foot[0], back_foot[1], halfw=1.2, Lfn=L)

# MIRROR the left half -> right half: now the figure is perfectly bilateral
class _Wrap:
    def __init__(self, cells, w, h):
        self.cells = cells; self.w = w; self.h = h
    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h
    def set(self, x, y, ch=None, fg=None, bg=None):
        if not self.in_bounds(x, y):
            return
        cell = self.cells[y][x]
        if ch is not None: cell[0] = ch
        if fg is not None: cell[1] = fg
        if bg is not None: cell[2] = bg
    def get(self, x, y):
        return tuple(self.cells[y][x]) if self.in_bounds(x, y) else None

_W = _Wrap(cv, W, H)
C.mirror(_W, axis='v')

# ---------------------------------------------------------------- pass 3: BREAK
# symmetry with MOTION. The lead (front) leg + arm are drawn AFTER the mirror so
# they're NOT mirrored -- that asymmetry is what reads as "a figure in motion".
front_sh = (HIPX + sh_dx, shoulder_y - 0.3)
fr_elb = (HIPX + sh_dx + 2.4, shoulder_y + 2.6)
fr_hand = (HIPX + sh_dx + 3.8, shoulder_y + 5.0)
capsule(cv, front_sh[0], front_sh[1], fr_elb[0], fr_elb[1], halfw=1.1, Lfn=L)
joint_dot(cv, fr_elb[0], fr_elb[1], 1.0, L)
capsule(cv, fr_elb[0], fr_elb[1], fr_hand[0], fr_hand[1], halfw=0.9, Lfn=L)

fr_hip = (HIPX + hip_dx, HIPY)
fr_knee = (HIPX + hip_dx + 2.8, HIPY + LEG_H * 0.52)
fr_foot = (HIPX + hip_dx + 4.6, HIPY + LEG_H * 0.94)
capsule(cv, fr_hip[0], fr_hip[1], fr_knee[0], fr_knee[1], halfw=1.6, Lfn=L)
joint_dot(cv, fr_knee[0], fr_knee[1], 1.3, L)
capsule(cv, fr_knee[0], fr_knee[1], fr_foot[0], fr_foot[1], halfw=1.2, Lfn=L)

# ---------------------------------------------------------------- pass 3b: the
# TRAILING GHOST -- dissolving echoes of the figure's previous pose, fading left
# (behind the motion). This is what sells "in motion": not one static body but a
# sequence. Each echo is dimmer and further back, stamped only into empty cells so
# it never clobbers the live body.
def ghost_layer(dx, dy, fg):
    snap = [row[:] for row in cv]
    for y in range(H):
        for x in range(W):
            ch, fgc, bgc = snap[y][x]
            if ch == ' ' or (ch == '\u2591' and fgc == 0):
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and cv[ny][nx][0] == ' ':
                set_cell(cv, nx, ny, '\u2591', fg, 0)

ghost_layer(-3, 0, GHOST[0])     # near echo
ghost_layer(-6, 0, GHOST[1])     # mid echo, dimmer
ghost_layer(-9, 1, GHOST[2])     # faintest, dissolving into the void

# ---------------------------------------------------------------- pass 4: atmosphere
def neg_space(x, y):
    return cv[y][x][0] == ' '
C.texture_fill(_W, neg_space, fg=238, density=0.12, seed=11)

def ground(x, y):
    return HIPY + LEG_H * 0.94 <= y <= HIPY + LEG_H * 1.02 and abs(x - (HIPX + hip_dx)) < 15
C.texture_fill(_W, ground, fg=236, density=0.5, seed=3)

# ---------------------------------------------------------------- pass 5: frame + card
out = []
for row in cv:
    parts = []; last_fg, last_bg = None, None
    for ch, fg, bg in row:
        if (fg, bg) != (last_fg, last_bg):
            parts.append(C.sgr(fg, bg)); last_fg, last_bg = fg, bg
        parts.append(ch)
    out.append("".join(parts))
C.sig_block(out, "STRIDE", handles="raze / AGENTSCII")
C.write_ans('scratch/_stride.ans', out, title="STRIDE v2.0 -- raze", add_sig=False)
print("wrote scratch/_stride.ans")
