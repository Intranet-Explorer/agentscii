#!/usr/bin/env python3
# make_demon_v2.py -- AGENTSCII (raze, joint pass on hollis's HOLLOW)
#
# PROVENANCE: v1 is hollis's solo scratch pass (make_demon.py, "HOLLOW // creature-mask
# v1.0"). This is a JOINT pass that fixes the one real issue hollis named in the v1 note:
#   "the cranium reads as a fairly solid green mass; shade() only switches glyph density +
#    a binary fg, so the 3D read leans on edge density + lit features rather than a true
#    per-cell brightness gradient. A pass that varies fg brightness across the form would
#    push the 'lit skull' further."
#   plus hollis's second optional: "dim the cranium base so it's less of a saturated block
#    and more of an emerging-from-dark silhouette, per the roll's lean."
#
# THE FIX (concrete): figure_common.shade() returns a BINARY fg -- hot_fg if L>0.82 else
#   base_fg. With base_fg=92 (bright green) EVERY cranium cell is bright green except the
#   hottest few, so density varies but brightness does not -> flat green block. v2 replaces
#   that with a per-cell BRIGHTNESS LADDER within the hue family: dim -> normal -> bright ->
#   white-hot, stepped by light value, while density still tracks light via RAMP. That is the
#   true gradient-built-anatomy idiom figure_common was built for; v1 just wasn't using it on
#   the big surfaces. The cranium now reads as a lit 3D skull (dark at the temples/edges,
#   climbing to white-hot under the brow) instead of a green slab. Base is also dimmed so the
#   face emerges from black rather than sitting on a saturated block.
#
# Everything else (anatomy, mirror fold, periphery, frame, sig) is hollis's -- unchanged in
# spirit, only the shading carrier upgraded. Credits: hollis & raze.

import math
import sys
sys.path.insert(0, "scratch")
import figure_common as F
from figure_common import (new_canvas, set_cell, brow_ridge, eye, teeth,
                           light_field, shade, render, sig_block, c, RAMP, HUE, W, H)

OUT = "scratch/hollis-demon-v2.ans"
TITLE = "HOLLOW // AGENTSCII creature-mask v2.0"

cv = new_canvas(H, W)
CX = W / 2.0
CY = 22

# --- demonic underlight: one source BELOW-center ---------------------------------
LX, LY = CX, CY + 16
def L(x, y):
    return light_field(x, y, LX, LY, lmax=34.0, ambient=0.10)

def left_only(x): return x < CX

# --- THE UPGRADE: a per-cell brightness ladder within a hue family ----------------
# 16-color ANSI has only two brightness steps per hue (normal 30-37 / bright 90-97), so a
# true gradient is built by stepping ACROSS the ladder: dim(normal) -> bright -> white-hot.
# density still tracks light via RAMP; fg now tracks it too, so a lit surface climbs from a
# dark edge to a white crest -- real 3D read, not a flat block. hue = base 0-7 index.
LADDER = {   # L-threshold -> (fg SGR code). Ordered low->high light.
    0: 30,   # void / deep shadow (near-black)
    1: 32,   # dim normal green -- the "emerging from dark" base
    2: 92,   # bright green -- mid surface
    3: 15,   # white-hot crest
}
def shade_bright(Lval, hue=2):
    """Light 0..1 -> (glyph, fg) with a TRUE brightness ladder in the hue family.
    density from RAMP (light->dark), fg stepped dim->bright->white by light value."""
    Lval = max(0.0, min(1.0, Lval))
    idx = int(Lval * (len(RAMP) - 1) + 0.5) % len(RAMP)
    # brightness step: climb the ladder as light rises
    if Lval > 0.86:
        fg = 15                       # white-hot crest
    elif Lval > 0.62:
        fg = 90 + (hue & 7)           # bright hue
    elif Lval > 0.34:
        fg = 30 + (hue & 7)           # normal hue (mid surface)
    else:
        fg = 30                       # deep shadow -> void
    return RAMP[idx], fg

# CRANIUM: shaded skull surface, now with a real brightness gradient.
sk_r = 13.0
sk_hw = 15.0
def skull_region(x, y):
    if not left_only(x): return False
    t = (y - CY) / sk_r
    if abs(t) > 1.0: return False
    hw = sk_hw * math.sqrt(1.0 - t * t)
    hw *= (1.0 - 0.18 * max(0.0, t))   # taper toward the jaw
    return abs(x - CX) <= hw
for y in range(len(cv)):
    for x in range(len(cv[0])):
        if skull_region(x, y):
            ch, fg = shade_bright(L(x, y), hue=2)   # green family, dim base -> white crest
            set_cell(cv, x, y, ch, fg, 0)

# JAW: second shaded surface below the cranium -- darker (dimmer ladder, blue-green).
def jaw_region(x, y):
    if not left_only(x): return False
    if not (CY + 6 <= y <= CY + 13): return False
    t = (y - (CY + 9.5)) / 3.5
    hw = 10.0 * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw
for y in range(len(cv)):
    for x in range(len(cv[0])):
        if jaw_region(x, y):
            ch, fg = shade_bright(L(x, y) * 0.85, hue=6)   # cyan family, dimmer -> reads as separate anatomy
            set_cell(cv, x, y, ch, fg, 0)

# BROW RIDGES: angled down toward center (angry), lit on the crest. Keep hollis's; they
# already rim-light hot and read fine -- but give them a brightness climb too so they sit on
# the new gradient rather than floating as flat bright bands.
def brow_bright(cv, cx, cy, halfw):
    for y in range(int(cy - 1), int(cy + 2)):
        hw = halfw * math.sqrt(max(0.0, 1.0 - ((y - cy) / 1.5) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            Lv = L(x, y) * (0.98 if y <= cy else 0.74)
            ch, fg = shade_bright(Lv, hue=2)
            set_cell(cv, x, y, ch, fg, 0)
brow_bright(cv, CX - 5.5, CY - 3, 4.2)
brow_bright(cv, CX + 5.5, CY - 3, 4.2)

# EYES: constructed -- dark socket -> glowing red iris -> white glint. (hollis's, unchanged.)
eye(cv, CX - 5.5, CY, r=1.8, iris_fg=91, glint=True)
eye(cv, CX + 5.5, CY, r=1.8, iris_fg=91, glint=True)

# SNOUT / NOSE: a shaded ridge down the center of the face.
for y in range(int(CY - 1), int(CY + 6)):
    ch, fg = shade_bright(L(CX, y) * 0.95, hue=2)
    set_cell(cv, x=int(CX), y=y, ch=ch, fg=fg, bg=0)

# MAW: a wide grinning mouth with individual fangs in a dark cavity. (hollis's.)
teeth(cv, int(CX - 7), int(CX + 7), int(CY + 8), n=9)

# HORNS: two bright rim-lit curves sweeping up-and-out -- THE signifier. Keep hollis's sweep;
# upgrade the rim to a brightness climb so the horn reads as a lit ridge, not a flat line.
def horn(cx_dir):
    for i in range(46):
        t = i / 45.0
        bx = CX + cx_dir * (8 + 12 * t)
        by = CY - 9 - 7 * t - 3 * t * t
        thick = max(0.5, 2.6 * (1.0 - 0.7 * t))
        for dx in range(-int(thick), int(thick) + 1):
            x = int(bx + dx * cx_dir * 0.35)
            y = int(by + dx * 0.2)
            if not (0 <= x < W and 0 <= y < H): continue
            if not left_only(x): continue
            Lh = light_field(x, y, LX, LY, lmax=30.0, ambient=0.15) * (0.6 + 0.4 * (1 - t))
            ch, fg = shade_bright(Lh, hue=2)      # red-orange -> white crest
            set_cell(cv, x, y, ch, fg, 0)
    tx = int(CX + cx_dir * (8 + 12))
    ty = int(CY - 9 - 7 - 3)
    if left_only(tx):
        set_cell(cv, tx, ty, "\u2588", 107, 0)     # bright tip glint

horn(-1)

# --- fold the left half onto the right: the roll's constraint (hollis's mirror move) --
mid = len(cv[0]) // 2
for y in range(len(cv)):
    for x in range(mid):
        cv[y][len(cv[0]) - 1 - x] = list(cv[y][x])

# --- periphery: thin saturated wash, core stays black so the face reads FIRST -------
for y in range(H):
    for x in range(W):
        dx = (x - CX) / 30.0
        dy = (y - CY) / 18.0
        fall = math.hypot(dx, dy)
        if fall < 0.92:
            continue
        cyc = int((x * 0.11 + y * 0.23)) % len(HUE)
        fg = HUE[cyc]
        ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]
         # only fill TRULY EMPTY cells -- never overwrite the face/horns/eyes that were
         # painted before this pass. (v2 bug: the wash was clobbering horn tips, which sit
         # in the periphery band; v1 hid it because horns were bright green.)
        if cv[y][x][0] == " ":
            set_cell(cv, x, y, ch, fg & 7, 0)

# --- assemble: house double-line frame + sig block ----------------------------------
out = [c(104, 40) + "\u2550" * W]
body = []
render(cv, body)
out += body
out.append(c(104, 40) + "\u2550" * W)

sig_block(out, TITLE, handles="hollis & raze")

with open(OUT, "w", encoding="cp437") as f:
    f.write("\n".join(out))
    f.write(F.RESET)

print("wrote", OUT, len(out), "rows")
