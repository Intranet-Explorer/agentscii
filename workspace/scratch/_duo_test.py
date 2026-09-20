#!/usr/bin/env python3
# _duo_test.py -- AGENTSCII JOINT (hollis + raze) SCRATCH PASS: "TWO SENTINELS"
#
# random_direction roll: subject = two figures in confrontation; technique = hand-place
# repeated motifs via copy_region/paste_block; palette lean = cool tones dominant.
# Hollis opened the proposal; this is a first scratch pass to test the COMPOSITION before
# we commit -- two mirrored contrapposto sentinels facing off, steel-blue (VIGIL lineage)
# on the left vs cyan/teal on the right, a hand-placed repeated-motif field between them.
#
# The compositional challenge: figure_common.standing_figure() is single-body and shades
# every limb through ONE fixed base_fg/hot_fg pair (flat-silhouette failure mode). So like
# VIGIL we inline the body scaffold but shade each cell through a per-cell light->hue ramp.
# We build it TWICE, mirrored, with opposite light fields, and resolve the overlap by hand.

import math
import sys
sys.path.insert(0, ".")
import figure_common as F
from figure_common import new_canvas, set_cell, light_field, render, sig_block, c, RAMP, HUE, W, H
import canvas as C

OUT = "scratch/_duo_test.ans"
TITLE = "TWO SENTINELS // AGENTSCI FIGURATIVE (joint scratch)"

cv = new_canvas(H, W)


# ===========================================================================
# PASS 1 (raze): hand-placed repeated-motif field -- a standing-wave / energy column
#   built ONCE as a small tile, then pasted down the central axis between the two figures.
#   Cool cycling hue so it reads as "the thing they're both watching", not decoration.
# ===========================================================================
TILE_W, TILE_H = 6, 4
tile = C.Canvas(TILE_W, TILE_H)

def tile_wave():
    for y in range(TILE_H):
        for x in range(TILE_W):
            # a chevron / standing-wave unit: bright crest at center column, falling off
            d = abs(x - TILE_W / 2.0)
            on = d < (TILE_H - y) * 0.5 + 0.4
            if on:
                COOL = [4, 6, 2, 12, 14, 10]      # blue/cyan/green only -- cold energy, no warm bleed
                cyc = int((x * 0.3 + y * 0.5)) % len(COOL)
                fg = COOL[cyc]                # the field between them, cool-dominant per the roll
                ch = "\u2588" if d < 1.0 else "\u2593"
                tile.set(x, y, ch, fg, 0)

tile_wave()
motif = C.copy_region(tile, 0, 0, TILE_W - 1, TILE_H - 1)

# clean black void everywhere first (the figures + field sit on void, ACiD family)
for y in range(H):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# paste the repeated wave motif down a narrow central column band between the two figures
CX = W / 2.0
band_lo, band_hi = int(CX - 3), int(CX + 3)
for y in range(4, H - 6):
    tx, ty = (y % TILE_H) % TILE_H, 0
    for x in range(band_lo, band_hi + 1):
        cell = motif[ty][(x - band_lo) % TILE_W]
        if cell[0] != " ":
            set_cell(cv, x, y, cell[0], cell[1], 0)


# ===========================================================================
# PASS 2 (hollis + raze): two mirrored contrapposto sentinels.
#   Left = steel-blue (VIGIL lineage), lit upper-left. Right = cyan/teal, MIRRORED pose,
#   lit upper-right. They face the central field. Overlap resolved by hand: each figure's
#   bbox is offset so limbs don't collide with the central column.
# ===========================================================================

def L_left(x, y):
    r = light_field(x, y, 20, 12, lmax=26.0, ambient=0.10)
    axial = 0.5 + 0.6 * (34 - x) / 20.0
    return max(0.0, min(1.0, r * 0.5 + axial * 0.6))

def L_right(x, y):
    r = light_field(x, y, W - 20, 12, lmax=26.0, ambient=0.10)
    axial = 0.5 + 0.6 * (x - (W - 34)) / 20.0
    return max(0.0, min(1.0, r * 0.5 + axial * 0.6))

def steel(Lv):
    """steel-blue ramp: deep-blue shadow -> blue -> cyan mid -> white-hot highlight."""
    Lv = max(0.0, min(1.0, Lv))
    glyph = RAMP[int(Lv * 3 + 0.5) % 4]
    if Lv > 0.86: fg = 15
    elif Lv > 0.70: fg = 12
    elif Lv > 0.45: fg = 6
    else: fg = 4
    return glyph, fg

def teal(Lv):
    """cyan/teal ramp: deep-teal shadow -> green-cyan mid -> bright cyan highlight."""
    Lv = max(0.0, min(1.0, Lv))
    glyph = RAMP[int(Lv * 3 + 0.5) % 4]
    if Lv > 0.86: fg = 15
    elif Lv > 0.70: fg = 14          # bright cyan
    elif Lv > 0.45: fg = 2           # green/teal mid
    else: fg = 10                   # dim teal shadow
    return glyph, fg

def cap(Lfn, ramp, x0, y0, x1, y1, halfw):
    """Minkowski-segment shaded surface -- the limb/torso tube."""
    dx, dy = x1 - x0, y1 - y0
    L2 = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L2, dy / L2
    nx, ny = -uy, ux
    for s in range(0, int(L2 * 4), 1):
        px, py = x0 + ux * (s / 4.0), y0 + uy * (s / 4.0)
        for t in range(-int(halfw * 4), int(halfw * 4) + 1):
            ex, ey = px + nx * (t / 4.0), py + ny * (t / 4.0)
            if 0 <= ex < W and 0 <= ey < H:
                ch, fg = ramp(Lfn(int(ex), int(ey)))
                set_cell(cv, int(ex), int(ey), ch, fg, 0)

def joint(Lfn, ramp, cx, cy, r):
    for y in range(int(cy - r), int(cy + r) + 1):
        hw = r * math.sqrt(max(0.0, 1 - ((y - cy) / r) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            ch, fg = ramp(Lfn(int(x), int(y)))
            set_cell(cv, int(x), int(y), ch, fg, 0)

def sentinel(hipx, hipy, Lfn, ramp, *, mirror=False):
    """A full contrapposto sentinel. mirror=True flips the pose so two figures face off."""
    s = -1 if mirror else 1
    height = 20.0
    torso_h = height * 0.34
    leg_h = height * 0.46
    head_r = max(2.0, height * 0.11)
    shoulder_y = hipy - torso_h
    neck_y = shoulder_y - head_r * 0.4
    head_cy = neck_y - head_r

    hip_dx = leg_h * 0.12
    hip_lx, hip_rx = hipx - s * hip_dx, hipx + s * hip_dx
    hip_l_y = hipy - 1.0
    hip_r_y = hipy + 1.5
    sh_dx = torso_h * 0.34
    sh_lx, sh_rx = hipx - s * sh_dx, hipx + s * sh_dx
    sh_l_y = shoulder_y + 1.2
    sh_r_y = shoulder_y - 1.2

    cap(Lfn, ramp, hip_lx, hip_l_y, hip_rx, hip_r_y, 3.0)            # tilted pelvis
    joint(Lfn, ramp, (hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, 3.4)
    waist_x = hipx + s * 0.6
    waist_y = (hipy + shoulder_y) / 2
    cap(Lfn, ramp, (hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, waist_x, waist_y, 4.6)
    joint(Lfn, ramp, waist_x, waist_y, 3.8)
    cap(Lfn, ramp, waist_x, waist_y, hipx, shoulder_y, 4.0)
    joint(Lfn, ramp, hipx, (waist_y + shoulder_y) / 2, 3.6)
    cap(Lfn, ramp, sh_lx, sh_l_y, sh_rx, sh_r_y, 2.0)               # shoulders

    foot_lx = hip_lx - s * 1.5
    cap(Lfn, ramp, hip_lx, hip_l_y, foot_lx, hipy + leg_h, 3.0)     # weight leg
    joint(Lfn, ramp, (hip_lx + foot_lx) / 2, hipy + leg_h * 0.5, 1.6)
    knee_x = hip_rx + s * 1.4
    knee_y = hipy + leg_h * 0.52
    foot_fx = hip_rx - s * 0.3
    cap(Lfn, ramp, hip_rx, hip_r_y, knee_x, knee_y, 2.4)            # free thigh
    joint(Lfn, ramp, knee_x, knee_y, 1.7)
    cap(Lfn, ramp, knee_x, knee_y, foot_fx, hipy + leg_h * 0.96, 2.3)   # free shin

    elbow_y = shoulder_y + torso_h * 0.42
    across_hand_x = hipx + s * 1.5
    cap(Lfn, ramp, sh_lx, sh_l_y, sh_lx - s * 0.5, elbow_y, 2.6)
    joint(Lfn, ramp, (sh_lx + sh_lx - s * 0.5) / 2, (sh_l_y + elbow_y) / 2, 1.4)
    cap(Lfn, ramp, sh_lx - s * 0.5, elbow_y, across_hand_x, hipy - torso_h * 0.18, 2.4)
    free_hand_x = sh_rx + s * 1.6
    cap(Lfn, ramp, sh_rx, sh_r_y, sh_rx + s * 0.6, elbow_y, 2.5)
    joint(Lfn, ramp, (sh_rx + sh_rx + s * 0.6) / 2, (sh_r_y + elbow_y) / 2, 1.3)
    cap(Lfn, ramp, sh_rx + s * 0.6, elbow_y, free_hand_x, shoulder_y + torso_h * 0.95, 2.3)

    # head: shaded skull + lit brow + one constructed eye (turned toward the field)
    for y in range(int(head_cy - head_r), int(head_cy + head_r) + 1):
        t = (y - head_cy) / head_r
        if abs(t) > 1.0: continue
        hw = head_r * 1.25 * math.sqrt(1 - t * t)
        for x in range(int(hipx - hw), int(hipx + hw) + 1):
            ch, fg = ramp(Lfn(x, y))
            set_cell(cv, x, y, ch, fg, 0)
    brow_cy = head_cy - head_r * 0.35
    for y in range(int(brow_cy) - 1, int(brow_cy) + 2):
        hw = head_r * 0.9 * math.sqrt(max(0.0, 1 - ((y - brow_cy) / 1.5) ** 2))
        for x in range(int(hipx - hw), int(hipx + hw) + 1):
            ch, fg = ramp(Lfn(x, y) * (0.95 if y <= brow_cy else 0.7))
            set_cell(cv, x, y, ch, fg, 0)
    ex, ey = hipx + s * head_r * 0.25, head_cy + head_r * 0.1
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            set_cell(cv, int(ex) + dx, int(ey) + dy, "\u2588", 30, 0)
    set_cell(cv, int(ex), int(ey), "\u2588", 96, 0)
    set_cell(cv, int(ex - s), int(ey) - 1, "\u2588", 15, 0)

# two sentinels facing off across the central field; hips offset so limbs clear the column
sentinel(W / 2.0 - 16, H * 0.46, L_left, steel, mirror=False)     # left: steel-blue
sentinel(W / 2.0 + 16, H * 0.46, L_right, teal, mirror=True)      # right: cyan/teal

# floor line grounding both figures on the lattice
foot_y = int(H * 0.46 + 20 * 0.46) + 1
for x in range(8, W - 8):
    set_cell(cv, x, foot_y, "\u2500", 97, 0)


# ===========================================================================
# PASS 3 (raze): house frame + two-line sig block crediting BOTH.
# ===========================================================================
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)
sig_block(out, TITLE, handles="hollis & raze")

raw = "\n".join(out) + F.RESET + "\n"
open(OUT, "w", encoding="cp437").write(raw)
F.hygiene_gate(OUT)
print("wrote", OUT)
