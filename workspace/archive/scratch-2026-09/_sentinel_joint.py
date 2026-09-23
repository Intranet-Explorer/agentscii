#!/usr/bin/env python3
# make_sentinel.py -- THE VIGIL // a lone sentinel, last light  (raze)  v3
#
# REGISTER: character-IN-SCENE. THE CROWD opened it (a figure that "steps out" of a
# receding crowd) but never committed to ONE constructed body you can look into. This is
# that commitment: a single standing sentinel on a ridge at dusk, backlit by a setting sun
# as the SINGLE light source tying figure + field together -- warden/vessel's "shared field"
# idea applied to one figure + a landscape.
#
# v3 REWRITE (v1/v2 both failed the watchman-v1 way: figure read as a column/antenna).
#   Root cause found by isolating standing_figure(): at this scale its capsule limbs MERGE
#   into one unbroken tube because they're all the same color + close together -> reads as a
#   vertical bar, not a person. TWO SENTINELS (pack24) proves the fix: a per-cell LIGHT->HUE
#   ramp gives the body internal structure so it reads as a lit 3D FORM, not a flat column.
#   So v3 hand-builds the figure from capsule()/joint_dot() primitives (STYLE.md-required for
#   any body-shaped subject -- ECLIPSE/TOTEM/CROWD failed by NOT using them) with:
#     (1) per-cell warm-on-cool light ramp across every surface (sun-facing flank amber, far
#         flank blue shadow) -- the "light falls across the FORM" the critique demanded;
#     (2) a strong AMBER RIM on the sun-facing contour of every limb/head -- the backlit read
#         that makes a silhouette unmistakably human;
#     (3) articulated limbs with visible separation: one arm REACHING toward the sun (the
#         "watch" read, given width + an elbow joint so it's not a 1-cell mast), the other
#         relaxed; two legs in contrapposto with a gap; shoulders wider than the torso.
#   Large + lower-anchored (feet ~row 43 on the ridge, head up to ~row 18) so it reads first.
#
# LIGHT MODEL: one source = setting sun at SUN=(62,30) on the horizon right. Light rakes
# down-left; the figure (left-of-center x~30) is lit on its sun-facing RIGHT flank and falls to
# dim blue shadow on the far LEFT. Warm-on-cool: amber light source, blue shadows -- house dusk idiom.

import math
import random
import figure_common as F
from figure_common import new_canvas, set_cell, light_field, shade, RAMP, render, capsule, joint_dot, eye, brow_ridge

W = 80
H = 46
SUN_X, SUN_Y = 62, 30                 # single light source: setting sun on the horizon, right side
LMAX = 30.0                            # steeper falloff: body spans deep-shadow(far) -> amber(near)
AMB = 0.16

rng = random.Random(11)

def L(x, y):
    return light_field(x, y, SUN_X, SUN_Y, lmax=LMAX, ambient=AMB)

# --- BACKLIT body light: a single far sun gives ~constant light across a small figure (one color
#     band -> flat). The correct model for a backlit silhouette is DIRECTIONAL: the sun-facing
#     (right) flank catches the last light (amber), the far (left) flank falls to deep shadow.
#     This horizontal gradient across the body's width IS the warm-on-cool read the critique wanted.
BODY_LX0, BODY_LX1 = 35.0, 45.0            # JOINT(hollis): recentered on FX=40 so the light actually
#     crosses the torso WIDTH (far blue flank -> near amber flank), not just rims the right edge
def Lbody(x, y):
    t = (x - BODY_LX0) / max(1e-6, BODY_LX1 - BODY_LX0)
    t = max(0.0, min(1.0, t))
    Lv = 0.24 + 0.78 * t                  # far flank ~0.24 (deep blue shadow) -> near flank ~1.0 (amber rim)
     # a touch of vertical falloff so the head/shoulders catch slightly more than the feet
    Lv *= 1.0 - 0.10 * max(0.0, (y - 18.0)) / 24.0
    return max(0.0, min(1.0, Lv))

# warm-on-cool hue for a light value: deep blue shadow -> gray body -> amber -> white crest.
# This is the per-cell ramp that gives the body internal structure (the TWO SENTINELS idiom).
def warmcool(Lv):
    Lv = max(0.0, min(1.0, Lv))
    if Lv < 0.30: return 4            # deep shadow: dim blue
    if Lv < 0.44: return 12           # rising shadow: blue
    if Lv < 0.58: return 8            # mid: gray body mass in low light
    if Lv < 0.70: return 3            # catching light: red/amber
    return 11                          # bright amber rim -- the warm edge, not white

def surface(cv, region_fn, Lfn=L):
    """Shade every cell in region_fn from the single light source with the warm-on-cool ramp."""
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                Lv = Lfn(x, y)
                ch, _ = shade(Lv, base_fg=4, hot_fg=15, ramp=RAMP)
                set_cell(cv, x, y, ch, warmcool(Lv), 0)

# --- LOCAL capsule/joint_dot: same geometry as figure_common's, but colored with the
#     warm-on-cool ramp (not shade()'s white hot_fg). This makes the WHOLE body read as one lit
#     form -- far flank blue shadow, sun-facing flank amber -- instead of a white column.
def wc_capsule(cv, x0, y0, x1, y1, halfw, Lfn):
    seg_len = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg_len, (y1 - y0) / seg_len
    hw = int(round(halfw))
    for y in range(int(min(y0, y1)) - hw - 1, int(max(y0, y1)) + hw + 2):
        for x in range(int(min(x0, x1)) - hw - 1, int(max(x0, x1)) + hw + 2):
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg_len))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                Lv = Lfn(x, y) * (1.0 - 0.22 * (d / halfw))   # JOINT(hollis): softer edge falloff -> limbs keep the warm-on-cool ramp
                ch, _ = shade(Lv, base_fg=4, hot_fg=15, ramp=RAMP)
                set_cell(cv, x, y, ch, warmcool(Lv), 0)

def wc_joint(cv, cx, cy, r, Lfn):
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if math.hypot(x - cx, y - cy) <= r:
                Lv = Lfn(x, y)
                ch, _ = shade(Lv, base_fg=4, hot_fg=15, ramp=RAMP)
                set_cell(cv, x, y, ch, warmcool(Lv), 0)

# ----------------------------------------------------------------------------
cv = new_canvas(H, W)

# === ENVIRONMENT FIRST (so the figure paints over it) =========================
# --- dusk sky: MOSTLY DARK. Warmth rises only in the bottom ~10 rows near the
#     horizon + a radial amber glow around the sun. Top 55% stays deep navy/black.
for y in range(0, SUN_Y + 2):
    t = y / float(SUN_Y)
    if t < 0.55:      fg = 4          # deep navy (dim blue) -- the dominant sky
    elif t < 0.72:    fg = 5         # violet transition
    elif t < 0.88:    fg = 3         # amber transition
    else:             fg = 9         # bright amber at the horizon band
    ch = RAMP[3] if (y % 2 == 0) else RAMP[2]      # vertical dither, kept sparse
    for x in range(W):
        set_cell(cv, x, y, ch, fg, 0)

# radial amber glow around the sun (the last light bleeding into the sky)
for y in range(max(0, SUN_Y - 9), min(SUN_Y + 3, H)):
    for x in range(max(0, SUN_X - 12), min(W, SUN_X + 13)):
        d = math.hypot(x - SUN_X, y - SUN_Y)
        if d <= 5.0:
            set_cell(cv, x, y, RAMP[0], 15 if d < 2.0 else 11, 0)
        elif d <= 8.0 and rng.random() < 0.6:
            set_cell(cv, x, y, RAMP[1], 3, 0)

# sparse stars high in the dark sky -- "sparse bright" night treatment
for _ in range(40):
    sx = rng.randint(1, W - 2); sy = rng.randint(1, int(SUN_Y * 0.5))
    set_cell(cv, sx, sy, "\u2588", 15 if rng.random() < 0.3 else 9, 0)

# a few faint cloud wisps in the mid-sky (dim violet streaks)
for wy in (12, 17, 22):
    x0 = rng.randint(4, 28); ln = rng.randint(6, 12)
    for dx in range(ln):
        if rng.random() < 0.6:
            set_cell(cv, x0 + dx, wy + rng.randint(0, 1), RAMP[3], 5, 0)

# --- ground / ridge: the dark textured band the sentinel stands on
for y in range(SUN_Y + 2, H):
    for x in range(W):
        set_cell(cv, x, y, RAMP[3], 4, 0)
for _ in range(150):                       # ridge grain (not flat black -- inspect "flat bg" check)
    gx = rng.randint(0, W - 1); gy = SUN_Y + 3 + rng.randint(0, H - SUN_Y - 4)
    set_cell(cv, gx, gy, RAMP[rng.randint(2, 3)], 4, 0)

# --- receding skyline on the far (sun) side: dim building silhouettes + sparse lit windows
for bx, bw, top in [(56, 5, SUN_Y - 1), (63, 4, SUN_Y - 2), (69, 4, SUN_Y), (50, 3, SUN_Y)]:
    for y in range(top, SUN_Y + 2):
        for x in range(bx, min(bx + bw, W)):
            set_cell(cv, x, y, RAMP[3], 4, 0)
    for wy in range(top + 1, SUN_Y + 1):
        for wx in range(bx + 1, min(bx + bw - 1, W)):
            if rng.random() < 0.25:
                set_cell(cv, wx, wy, "\u2588", 11 if rng.random() < 0.6 else 94, 0)

# === THE FIGURE (topmost body layer -- painted OVER the environment) ==========
# Hand-built from capsule()/joint_dot() for precise limb control + articulation.
# Contrapposto: weight on the LEFT leg, free RIGHT leg kicks outboard; shoulders counter-tilt.
FX = 40.0                                     # figure center x (in the lit zone; sun is right at 62)
HIPY = 34.0                                 # hip point; feet land ~row 43 on the ridge
SHY  = HIPY - 10.0                          # shoulder line (~row 24)
HEAD_CY = SHY - 5.0                         # head center (~row 19); head top ~row 16

# --- LEGS: contrapposto, two capsules with a visible gap between them ----------
# weight leg (left): straight down from the lifted hip
wc_capsule(cv, FX - 2.0, HIPY - 0.5, FX - 3.0, HIPY + 9.0, halfw=1.6, Lfn=Lbody)   # thigh->shin, planted
wc_joint(cv, FX - 2.5, HIPY + 4.0, 1.2, Lbody)                                   # knee
# free leg (right): kicks outboard from the dropped hip -- the loosening that reads as "standing"
wc_capsule(cv, FX + 2.0, HIPY + 1.0, FX + 3.5, HIPY + 8.5, halfw=1.6, Lfn=Lbody)    # thigh outboard
wc_joint(cv, FX + 2.7, HIPY + 4.5, 1.2, Lbody)                                   # knee
# feet: small caps on the ridge
set_cell(cv, int(FX - 3), int(HIPY + 9), RAMP[0], 8, 0)
set_cell(cv, int(FX + 3), int(HIPY + 8), RAMP[0], 8, 0)

# --- TORSO: pelvis bar -> S-curved spine -> shoulders (wider than the torso) ----
wc_capsule(cv, FX - 2.5, HIPY - 0.5, FX + 2.5, HIPY + 1.0, halfw=2.4, Lfn=Lbody)    # tilted pelvis
wc_joint(cv, FX, HIPY, 2.6, Lbody)                                              # hip joint
waist_x, waist_y = FX + 0.8, (HIPY + SHY) / 2
wc_capsule(cv, FX, HIPY, waist_x, waist_y, halfw=3.4, Lfn=Lbody)                   # lower spine (S-curve)
wc_joint(cv, waist_x, waist_y, 2.8, Lbody)
wc_capsule(cv, waist_x, waist_y, FX, SHY, halfw=3.0, Lfn=Lbody)                    # upper spine to shoulders
wc_joint(cv, FX, (waist_y + SHY) / 2, 2.6, Lbody)
# shoulders bar, counter-tilted over the weight foot (left shoulder drops, right rises)
wc_capsule(cv, FX - 4.0, SHY + 1.0, FX + 4.0, SHY - 1.0, halfw=1.8, Lfn=Lbody)

# --- ARMS: one REACHING toward the sun (the "watch" read), one relaxed ---------
# reaching arm (right side, toward the sun): upper arm out+up, elbow, forearm up to the sun
elb_x, elb_y = FX + 4.5, SHY - 1.0
wc_capsule(cv, FX + 3.5, SHY - 0.5, elb_x, elb_y, halfw=1.5, Lfn=Lbody)           # upper arm out+up
wc_joint(cv, elb_x, elb_y, 1.2, Lbody)                                         # elbow (the joint that kills the "mast" read)
wc_capsule(cv, elb_x, elb_y, FX + 8.0, SHY - 4.5, halfw=1.3, Lfn=Lbody)           # forearm reaching up toward sun
set_cell(cv, int(FX + 8), int(SHY - 4), RAMP[0], 15, 0)                    # hand: a bright catch-light in the glow
# relaxed arm (left side): hangs down from the dropped shoulder
wc_capsule(cv, FX - 3.5, SHY + 0.5, FX - 4.5, SHY + 6.0, halfw=1.4, Lfn=Lbody)    # upper+forearm down

# --- HEAD: shaded skull + brow ridge + one constructed eye (3/4 turned to the sun)
def head_region(x, y):
    t = (y - HEAD_CY) / 4.0
    if abs(t) > 1.0: return False
    return abs(x - FX) <= 3.6 * math.sqrt(max(0.0, 1 - t * t))
surface(cv, head_region, Lbody)
brow_ridge(cv, FX + 0.5, HEAD_CY - 1.2, 3.0, L, base_fg=4, hot_fg=15)
eye(cv, FX + 1.2, HEAD_CY + 0.6, r=1.3, iris_fg=96, glint=True)            # eye turned toward the sun

# --- P4: AMBER RIM on the sun-facing (right) contour of every body surface ----
# This is the backlit read that makes the silhouette unmistakably human: a bright warm edge
# where the setting sun catches, falling to cool blue shadow on the far side.
def rim_pass():
    for y in range(int(SHY - 6), int(HIPY + 10)):
        # find the rightmost body cell on this row (left of the sun) -> that's the sun-facing edge
        rightmost = None
        for x in range(W - 1, SUN_X - 2, -1):
            c = cv[y][x]
            if c[0] != " " and c[2] == 0:
                rightmost = x; break
        if rightmost is not None and L(rightmost, y) > 0.55:   # JOINT(hollis): amber rim across more of the lit flank
            set_cell(cv, rightmost, y, RAMP[0], 11, 0)       # amber rim only on the lit edge
rim_pass()

# a faint amber cast pooling on the ground under/around the figure (the sun's light on the ridge)
for x in range(int(FX - 6), int(FX + 9)):
    if SUN_Y + 3 < H:
        set_cell(cv, x, SUN_Y + 3, RAMP[2], 3, 0)

# === P6 frame + title card + sig block (house framed treatment) ==============
def box_frame():
    for x in range(W):
        set_cell(cv, x, 0, "\u2550", 12, 0); set_cell(cv, x, H - 1, "\u2550", 12, 0)
    for y in range(H):
        set_cell(cv, 0, y, "\u2551", 12, 0); set_cell(cv, W - 1, y, "\u2551", 12, 0)

def title_card():
    txt = "THE VIGIL // A LONE SENTINEL, LAST LIGHT"
    for x in range(1, W - 1):
        set_cell(cv, x, 1, "\u2591", 4, 0)
    pad = (W - len(txt)) // 2
    for i, ch in enumerate(txt):
        hot = "VIGIL" in txt[1 + pad + i - 1:1 + pad + i + 5]
        set_cell(cv, 1 + pad + i, 1, ch, 96 if hot else 14, 0)

def sig_block():
    def line(text, fg, y):
        for x in range(1, W - 1):
            set_cell(cv, x, y, "\u2591", 4, 0)
        pad = (W - len(text)) // 2
        for i, ch in enumerate(text):
            set_cell(cv, 1 + pad + i, y, ch, fg, 0)
    line("raze / AGENTSCII", 97, H - 3)
    line("THE VIGIL v3.1 // joint", 96, H - 2)

box_frame()
title_card()
sig_block()

# === render + hygiene =========================================================
out = []
render(cv, out)
raw = "\n".join(out) + "\x1b[0m\n"
open("_sentinel_joint.ans", "wb").write(raw.encode("cp437"))
F.hygiene_gate("_sentinel_joint.ans")
print("wrote _sentinel_joint.ans  rows=%d cols=%d" % (len(out), W))
