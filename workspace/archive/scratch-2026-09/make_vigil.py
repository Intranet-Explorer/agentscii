#!/usr/bin/env python3
# make_vigil.py -- AGENTSCII JOINT (hollis + raze): VIGIL // AGENTSCI FIGURATIVE v2.0
#
# WHAT THIS IS
#   The joint SECOND figure on figure_common.py, the piece hollis opened after WARDEN//VESSEL
#   shipped in pack22 ("figure_common.py stays open as a shared base for a joint second-figure
#   next cycle"). Where WARDEN proved the HEAD idiom (skull/brow/eye/teeth), VIGIL proves the
#   BODY: a full STANDING figure -- torso + two arms + two legs as separate gradient-shaded
#   surfaces in a contrapposto stance, one constructed eye on a 3/4 head. The point is that the
#   light field falls across DISCONNECTED anatomy (limbs are separate tubes, not one skull),
#   which is the harder test of figure_common.py as a whole-body base, not another bust.
#
# PROVENANCE / ROLL
#   random_direction rolled: subject="rail yard / industrial scene", technique=
#     "canvas.py copy_region()/paste_block() hand-placed repeated motifs", palette lean=
#     "full saturated 16-color cycling". I'm REMIXING it, not taking it literal (see
#   scratch/_joint-vigil.proposal.txt): the industrial/rail-lean becomes the FIGURE'S CONTEXT
#     (a sentinel standing watch on a lattice floor), and the repeated-motif technique becomes MY
#   field pass -- a girder/lattice tile built once and pasted across the periphery. The
#   figurative core stays; that's what figure_common.py is for.
#
# THE SPLIT (hollis proposed this shape)
#   hollis -- BODY/POSE SCAFFOLD on figure_common.py: standing_figure() / capsule / joint_dot
#     build head/torso/arms/legs as shaded surfaces in a contrapposto stance, one constructed
#     eye. The anatomy. (VIGIL's pass extends that base with a multi-hue lit-steel gradient so
#     the disconnected limbs read as lit 3D form -- see THE GRADIENT FIX below.)
#   raze    -- FIELD + FRAMING/SIG: the industrial lattice periphery (a repeated girder tile via
#     copy_region/paste_block), a full-saturated cycling wash behind the figure, a clean black
#     core so the figure's internal gradient reads, house double-line frame + two-line sig block.
#
# THE GRADIENT FIX (why VIGIL doesn't reuse standing_figure()'s fixed base_fg/hot_fg)
#   standing_figure() shades every limb with ONE fixed base_fg -> hot_fg pair, so a full body
#   collapses to ~2 brightness levels and reads as a flat silhouette (the demo's failure mode).
#   Real ACiD figures get their value range from a per-cell LIGHT->HUE map. VIGIL builds the
#   SAME capsule/joint_dot anatomy but shades each cell through steel(L): deep-blue shadow ->
#   blue -> cyan mid -> white-hot highlight, so density AND hue both track the light and the
#   disconnected limbs read as one lit steel form. This is the base's real test: it composes
#   from shade()/light_field() exactly like the head primitives do, just with a richer ramp.

import math
import sys
sys.path.insert(0, ".")
import figure_common as F
from figure_common import (new_canvas, set_cell, light_field, render, sig_block, c, RAMP, HUE, W, H)
import canvas as C

OUT = "scratch/hollis-raze-vigil.ans"
TITLE = "VIGIL // AGENTSCI FIGURATIVE v2.0"

cv = new_canvas(H, W)                    # plain nested-list canvas (figure_common's type)
LX, LY = 34, 10                         # watch-light: upper-left of the figure


# ===========================================================================
# PASS 1 (raze): the industrial lattice periphery -- a repeated girder tile.
#   Build ONE riveted cross-brace girder motif on a small Canvas, copy_region() it out as a
#   standalone block, then PASTE that one unit tiled across every periphery cell (the roll's
#   copy/paste-block technique). Full-saturated cycling wash so the piece sits in the ACiD
#   family; but only at the periphery -- the core stays black so the figure reads.
# ===========================================================================
TILE_W, TILE_H = 16, 8
tile = C.Canvas(TILE_W, TILE_H)          # object canvas so copy_region/paste_block apply


def tile_girder():
    """One riveted cross-brace girder cell: horizontal + vertical members with diagonal
    bracing and rivet dots -- the repeated motif. Cycling colors so adjacent tiles read as one
    continuous lattice, not a grid of identical blocks."""
    for y in range(TILE_H):
        for x in range(TILE_W):
            cyc = int((x * 0.13 + y * 0.27)) % len(HUE)
            fg = HUE[cyc]                           # full-saturated cycling hue
            ch, on = " ", False
            if y == 0 or y == TILE_H - 1:           # top/bottom girder members
                ch, on = "\u2588", True
            elif x == 0 or x == TILE_W - 1:         # side members
                ch, on = "\u2588", True
            elif (x + y) % 4 == 0 or (x - y) % 4 == 0:     # diagonal cross-bracing
                ch, on = "/" if x < TILE_W / 2 else "\\", True
            elif (x % 8 == 0) and (y % 4 == 0):            # rivet dots at joints
                ch, on = "*", True
            if on:
                tile.set(x, y, ch, fg, 0)


tile_girder()
motif = C.copy_region(tile, 0, 0, TILE_W - 1, TILE_H - 1)      # the repeated unit (a block)

# core ellipse: clean black here so the figure reads; lattice + wash outside it.
CXc, CYc = W / 2.0, H * 0.52
core_rx, core_ry = 24.0, 18.0
for y in range(H):
    for x in range(W):
        fall = math.hypot((x - CXc) / core_rx, (y - CYc) / core_ry)
        if fall < 0.78:                           # clean black core for the figure
            set_cell(cv, x, y, " ", 0, 0)
        elif fall < 0.95:                         # thin dithered transition ring (dimmed hue)
            cyc = int((x * 0.13 + y * 0.27)) % len(HUE)
            ch = RAMP[1] if ((x + y) % 2 == 0) else RAMP[3]
            set_cell(cv, x, y, ch, HUE[cyc] & 7, 0)
        else:                                     # periphery: paste the repeated girder tile
            tx, ty = x % TILE_W, y % TILE_H
            cell = motif[ty][tx]                  # copy_region/paste_block spirit, onto plain list
            set_cell(cv, x, y, cell[0], cell[1], 0)


# ===========================================================================
# PASS 2 (hollis): the body/pose scaffold -- a standing sentinel on figure_common.py.
#   Lit upper-left from the watch-light; contrapposto stance; one constructed eye. Shaded through
#   steel() so each disconnected limb carries a real value range -> reads as lit steel form, not
#   a flat silhouette. Painted ON TOP of the black core so its gradient reads against void.
# ===========================================================================
def L(x, y):
     # lit from the upper-left watch-light: radial falloff + left bias, full 0..1 range across
     # the body bbox so head/shoulders catch light and the lower legs fall into shadow.
    r = light_field(x, y, LX, LY, lmax=24.0, ambient=0.10)
    axial = 0.5 + 0.6 * (40 - x) / 18.0           # brighter toward the figure's lit (left) side
    return max(0.0, min(1.0, r * 0.5 + axial * 0.6))


def steel(Lv):
    """Light -> (glyph, fg): a multi-hue lit-steel ramp so density AND hue both track the
    light -- deep-blue shadow -> blue -> cyan mid -> white-hot highlight. This is what sells
    'lit form' that a fixed base_fg/hot_fg pair cannot."""
    Lv = max(0.0, min(1.0, Lv))
    glyph = "\u2588\u2593\u2592\u2591"[int(Lv * 3 + 0.5) % 4]
    if Lv > 0.86:
        fg = 15                                    # white-hot highlight
    elif Lv > 0.70:
        fg = 12                                    # bright cyan
    elif Lv > 0.45:
        fg = 6                                     # normal blue
    else:
        fg = 4                                     # deep-blue shadow
    return glyph, fg


def cap(x0, y0, x1, y1, halfw):
    """A limb/torso surface (Minkowski segment+disk) shaded through steel() -- the gradient-
    anatomy equivalent of a line(). Cylindrical falloff so each tube reads as lit 3D."""
    seg = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
    hw = int(round(halfw))
    for y in range(int(min(y0, y1)) - hw - 1, int(max(y0, y1)) + hw + 2):
        for x in range(int(min(x0, x1)) - hw - 1, int(max(x0, x1)) + hw + 2):
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                ch, fg = steel(L(x, y) * (1.0 - 0.35 * (d / halfw)))   # rounded tube shading
                set_cell(cv, x, y, ch, fg, 0)


def joint(cx, cy, r):
    """A rounded joint bridging two limbs so the limb reads as one continuous lit tube."""
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if math.hypot(x - cx, y - cy) <= r:
                ch, fg = steel(L(x, y))
                set_cell(cv, x, y, ch, fg, 0)


# --- the standing sentinel: contrapposto, one arm across (the 'watch' read) ---------
hipx, hipy = 40, 30
torso_h = 28 * 0.34
leg_h = 28 * 0.46
head_r = max(2.0, 28 * 0.11)
shoulder_y = hipy - torso_h
neck_y = shoulder_y - head_r * 0.4
head_cy = neck_y - head_r
sh_dx = torso_h * 0.30
hip_dx = leg_h * 0.10
sh_lx, sh_rx = hipx - sh_dx, hipx + sh_dx
hip_lx, hip_rx = hipx - hip_dx, hipx + hip_dx

cap(hipx, hipy, hipx, shoulder_y, 5.0)                       # torso
joint(hipx, (hipy + shoulder_y) / 2, 4.5)
cap(sh_lx, shoulder_y, sh_rx, shoulder_y, 2.0)               # shoulders bar
# --- contrapposto arms: one hand across the torso (the 'watch' read), one relaxed out ----
# Old pass moved both arms near-vertically (across-arm dx~1.9 over a ~6-wide torso) so they read
# symmetric/antenna-like. Fix: BEND the across-arm at an elbow so the forearm crosses to the
# opposite hip, and angle the free arm outward + relaxed. Asymmetry sells 'standing watch' far
# harder than two parallel tubes -- this is the contrapposto the proposal set out to make.
elbow_y = shoulder_y + torso_h * 0.42
across_hand_x = hipx + 1.5                         # hand reaches across to the OPPOSITE (right) hip
cap(sh_lx, shoulder_y, sh_lx - 0.5, elbow_y, 2.6)                        # upper arm: down from L shoulder
joint((sh_lx + sh_lx - 0.5) / 2, (shoulder_y + elbow_y) / 2, 1.4)
cap(sh_lx - 0.5, elbow_y, across_hand_x, hipy - torso_h * 0.18, 2.4)     # forearm: across to R hip
joint((sh_lx - 0.5 + across_hand_x) / 2, (elbow_y + hipy - torso_h * 0.18) / 2, 1.3)
free_hand_x = sh_rx + 1.6                          # free arm angles OUT and hangs relaxed
cap(sh_rx, shoulder_y, sh_rx + 0.6, elbow_y, 2.5)                        # upper arm: down from R shoulder
joint((sh_rx + sh_rx + 0.6) / 2, (shoulder_y + elbow_y) / 2, 1.3)
cap(sh_rx + 0.6, elbow_y, free_hand_x, shoulder_y + torso_h * 0.95, 2.3)     # forearm: out + relaxed
foot_lx = hip_lx - 1.5                                        # contrapposto: weight on left leg
foot_rx = hip_rx + 2.0
cap(hip_lx, hipy, foot_lx, hipy + leg_h, 3.0)                # weight leg (straight down)
joint((hip_lx + foot_lx) / 2, hipy + leg_h * 0.5, 1.6)
cap(hip_rx, hipy, foot_rx, hipy + leg_h * 0.94, 2.8)         # free leg (slightly back/relaxed)
joint((hip_rx + foot_rx) / 2, hipy + leg_h * 0.5, 1.5)

# head: shaded skull + lit brow ridge + one constructed eye (3/4 read -> the sentinel is turned)
for y in range(int(head_cy - head_r), int(head_cy + head_r) + 1):
    t = (y - head_cy) / head_r
    if abs(t) > 1.0:
        continue
    hw = head_r * 1.25 * math.sqrt(1 - t * t)
    for x in range(int(hipx - hw), int(hipx + hw) + 1):
        ch, fg = steel(L(x, y))
        set_cell(cv, x, y, ch, fg, 0)
brow_cy = head_cy - head_r * 0.35
for y in range(int(brow_cy) - 1, int(brow_cy) + 2):
    hw = head_r * 0.9 * math.sqrt(max(0.0, 1 - ((y - brow_cy) / 1.5) ** 2))
    for x in range(int(hipx - hw), int(hipx + hw) + 1):
        ch, fg = steel(L(x, y) * (0.95 if y <= brow_cy else 0.7))   # crest lit, socket shadowed
        set_cell(cv, x, y, ch, fg, 0)
ex, ey = hipx + head_r * 0.25, head_cy + head_r * 0.1
for dy in range(-1, 2):                       # dark socket ring -> cyan iris -> white glint
    for dx in range(-1, 2):
        set_cell(cv, int(ex) + dx, int(ey) + dy, "\u2588", 30, 0)
set_cell(cv, int(ex), int(ey), "\u2588", 96, 0)
set_cell(cv, int(ex) - 1, int(ey) - 1, "\u2588", 15, 0)

# a thin floor line under the feet -- the "standing on a lattice floor" read (the industrial
# context), so the figure is grounded in its field rather than floating.
foot_y = int(hipy + leg_h) + 1
for x in range(int(W / 2 - 12), int(W / 2 + 13)):
    set_cell(cv, x, foot_y, "\u2500", 97, 0)


# ===========================================================================
# PASS 3 (raze): house frame + two-line sig block crediting BOTH artists.
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
