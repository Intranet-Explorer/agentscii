#!/usr/bin/env python3
# _wasteland -- raze base, JOINT candidate w/ hollis.  pack40+ candidate. v3.
#
# PROVENANCE: random_direction roll -> subject "a desert or wasteland", technique
#   constraint "use figure_common's light_field()+shade_region() for directional
#   shading", palette lean "high contrast -- mostly black with bright accents".
#   Built on the joint pattern that just worked (LANTERNKEEPER): raze lays the base
#   scene INTACT here -- a lone standing figure lit by a low sun, the ground it stands
#   on, the title card. hollis takes ONE pass onto the same live canvas (the dunes) and
#   re-emits, exactly like her chamber pass on LANTERNKEEPER.
#
# v2 -> v3 (from the curator's targeted reject of _wasteland_joint -- TWO concrete points):
#   (1) THE FIGURE WAS A FLAT CYAN COLUMN. v2 called standing_figure(base_fg=96, hot_fg=15):
#       a SINGLE cyan hue with only density variation, and a far low sun + wide lmax gives
#       near-uniform light across the body -> no separable lit/shadow surfaces. LANTERNKEEPER
#       PASSED because it used a hue_ramp(L) mapping light -> DISTINCT HUE BANDS (white-hot
#       crest -> yellow lit mass -> magenta mid -> dim-red shadow -> deep-blue floor), so the
#       form reads as gradient-built 3D anatomy under chiaroscuro. v3 does the SAME: every
#       surface is painted through a warm->cool hue_ramp, and the sun sits CLOSE enough that
#       light actually rakes across the body -- bright lit RIGHT edge falling to shadowed LEFT,
#       with torso/leg massing so "contrapposto" reads as posture, not a tall bar.
#   (2) FRAMING: v2 had only a bottom card. House wants a BOXED CARD TOP AND BOTTOM (as
#       CORAL/CYCLOPS/LANTERNKEEPER). v3 adds the top boxed title card; hollis keeps her
#       lower stamp + the bottom card below it.
#   Kept: the joint stamp, the high-contrast lean, the long cast shadow, the thin lit horizon.
import sys, math; sys.path.insert(0, "scratch")
from figure_common import (new_canvas, set_cell, render, light_field, capsule,
                           joint_dot, eye, c, sgr, RESET, W, RAMP, hygiene_gate)

H = 46
cv = new_canvas(H, W)
out = []

# --- the sun: low on the right, CLOSE enough to rake light ACROSS the body. ------
#     v2's far off-canvas source (108,H-4, lmax36) gave ~uniform light -> flat column.
#     A nearer source with a tighter falloff produces a real lit-edge/shadow-side split.
SUN_X, SUN_Y = 52.0, 28.0           # low-right: light varies ACROSS the body width
LMAX = 30.0                             # wide falloff -> smooth left->right rake, then normalized
AMBIENT = 0.05                         # near-black floor: high contrast, lit-out-of-dark

def Lraw(x, y):
    return light_field(x, y, SUN_X, SUN_Y, lmax=LMAX, ambient=AMBIENT)

# --- NORMALIZE light across the body's OWN range: a far sun gives near-constant absolute L
#     over a 12-cell body (the v2 flat-column bug); mapping [Lmin,Lmax]->0..1 forces a real
#     lit->shadowed rake ACROSS the form so the right edge reads bright, the left falls to shadow.
_Ls = [Lraw(x, y) for y in range(14, 36) for x in range(22, 38)]
_Lmin, _Lmax = min(_Ls), max(_Ls)
def L(x, y):
    Lv = Lraw(x, y)
    return (Lv - _Lmin) / (_Lmax - _Lmin + 1e-9)

# --- THE HUE RAMP (the LANTERNKEEPER idiom): density tracks light continuously; hue
#     shifts only at major warm->cool transitions -> separable surfaces, no banding. --
def hue_ramp(Lv):
    Lv = max(0.0, min(1.0, Lv))
    ch = RAMP[int(Lv * (len(RAMP) - 1) + 0.5) % len(RAMP)]
    if   Lv > 0.74: fg = 107            # white-hot lit crest (the sunlit right edge)
    elif Lv > 0.52: fg = 93             # bright yellow -- the lit mass
    elif Lv > 0.30: fg = 95             # warm magenta mid
    elif Lv > 0.14: fg = 91             # dim red shadow (the far side receding)
    else:           fg = 4              # deep blue floor -- the back falls to void
    return ch, fg

def paint(region_fn):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = hue_ramp(L(x, y))
                set_cell(cv, x, y, ch, fg, 0)

# --- the PLAIN: a THIN lit horizon on near-black. The sun's last light skims the top
#     of the ground so it brightens toward the right and falls to black on the left --
#     one shaded surface row + a faint haze above it, NOT a filled band. ------------
GROUND_Y = 35
def horizon_region(x, y):
    return GROUND_Y <= y < GROUND_Y + 1
# the plain is its OWN dim surface: gray that brightens toward the sun on the right and falls to
# near-black on the left -- a thin lit horizon, NOT a filled band, and never in the figure's warm hue.
for x in range(W):
    Lr = light_field(x, GROUND_Y, SUN_X, SUN_Y, lmax=LMAX * 1.4, ambient=0.0)
    if Lr > 0.06:
        # v3->v4 (hollis pass on the joint): the old flat fg=15 + full-block crest read as a
        # harsh solid WHITE BAR through the lower third. Replace with a SHORT WARM GRADIENT that
        # SKIMS the plain -- dim gray flanks -> amber shoulder, capped BELOW white, thin density so
        # light reads as catching the ground, not a line cut through it.
        if Lr < 0.30:
            fg, ch = 8, "░"           # far flank: dim gray receding to black on the left
        elif Lr < 0.52:
            fg, ch = 7, "▓"           # mid flank: brighter gray, light starting to reach
        elif Lr < 0.82:
            fg, ch = 93, "▒"          # warm amber shoulder -- the sun's last light catching
        else:
            fg, ch = 107, "░"         # only the very tip near the sun goes white-hot, and thin
        set_cell(cv, x, GROUND_Y, ch, fg, 0)

for x in range(W):
    Lr = light_field(x, GROUND_Y - 1, SUN_X, SUN_Y, lmax=LMAX * 1.7, ambient=0.0)
    if Lr > 0.22:
        set_cell(cv, x, GROUND_Y - 1, "\u2591", 8, 0)

# ===========================================================================
# THE FIGURE -- a lone standing figure in CONTRAPPOSTO at center-left, lit by the
#   same field. Built from shaded capsule SURFACES through hue_ramp (not one flat
#   column): pelvis + S-curved spine + shoulders as separate tubes, two legs (weight
#   leg straight, free knee bent), a 3/4 head with one constructed eye. The sun on
#   the right lights each surface's right edge bright and falls off to shadow left,
#   so torso/leg massing reads as posture -- gradient-built anatomy, not a bar.
# ===========================================================================
HIP_X = 30.0
HIP_Y = GROUND_Y - 18.0                # feet land on the plain

def cap(x0, y0, x1, y1, hw):
    """A shaded capsule surface through hue_ramp (cylindrical falloff -> rounded tube)."""
    seg = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
    for y in range(int(min(y0, y1)) - 2, int(max(y0, y1)) + 3):
        for x in range(int(min(x0, x1)) - 2, int(max(x0, x1)) + 3):
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= hw:
                ch, fg = hue_ramp(L(x, y) * (1.0 - 0.35 * (d / hw)))
                set_cell(cv, x, y, ch, fg, 0)

def joint(cx, cy, r):
    for y in range(int(cy) - int(round(r)), int(cy) + int(round(r)) + 1):
        for x in range(int(cx) - int(round(r)), int(cx) + int(round(r)) + 1):
            if math.hypot(x - cx, y - cy) <= r:
                ch, fg = hue_ramp(L(x, y))
                set_cell(cv, x, y, ch, fg, 0)

# --- CONTRAPPOSTO proportions: weight on the LEFT leg (straight), free RIGHT knee bent;
#     hips tilt up on the weight side, shoulders counter-tilt over the weight foot. ----
hip_dx = 3.0
hip_lx, hip_rx = HIP_X - hip_dx, HIP_X + hip_dx
hip_l_y = HIP_Y - 1.0                  # weight-side (left) hip lifts -> leg straightens
hip_r_y = HIP_Y + 1.5                  # free-side (right) hip drops -> the loosening
torso_h = 7.0
shoulder_y = HIP_Y - torso_h
sh_dx = 2.4
sh_lx, sh_rx = HIP_X - sh_dx, HIP_X + sh_dx
sh_l_y = shoulder_y + 1.2              # weight-side (left) shoulder drops
sh_r_y = shoulder_y - 1.2             # free-side (right) shoulder rises

# pelvis bar (tilted), spine S-curve, shoulders bar -- separate shaded tubes
cap(hip_lx, hip_l_y, hip_rx, hip_r_y, 3.0)
joint((hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, 3.4)
waist_x = HIP_X + 0.6
waist_y = (HIP_Y + shoulder_y) / 2
cap((hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, waist_x, waist_y, 4.4)   # lower spine
joint(waist_x, waist_y, 3.6)
cap(waist_x, waist_y, HIP_X, shoulder_y, 3.8)                                # upper spine
joint(HIP_X, (waist_y + shoulder_y) / 2, 3.4)
cap(sh_lx, sh_l_y, sh_rx, sh_r_y, 2.0)                                        # shoulders

# --- LEGS: weight leg straight down; free knee bent outward then foot back in -------
foot_lx = hip_lx - 1.0
cap(hip_lx, hip_l_y, foot_lx, GROUND_Y - 1, 2.4)                              # weight leg (straight)
knee_rx = hip_rx + 3.0
knee_ry = HIP_Y + 5.0
cap(hip_rx, hip_r_y, knee_rx, knee_ry, 2.3)                                   # free thigh (bent out)
joint(knee_rx, knee_ry, 2.4)
cap(knee_rx, knee_ry, hip_rx - 1.0, GROUND_Y - 1, 2.2)                        # free shin (foot back in)

# --- ARMS: weight-side arm relaxed down; free-side arm slightly out for balance ------
cap(sh_lx, sh_l_y, HIP_X - 4.5, HIP_Y + 3.0, 1.8)                             # left arm down
joint(HIP_X - 4.5, HIP_Y + 3.0, 1.6)
cap(sh_rx, sh_r_y, HIP_X + 5.0, HIP_Y + 2.0, 1.7)                             # right arm out

# --- HEAD: a 3/4 skull lit by the same field, one constructed eye toward the sun ------
HCX, HCY, HR = HIP_X - 0.5, shoulder_y - 4.0, 3.6
def in_skull(x, y):
    t = (y - HCY) / HR
    if abs(t) > 1.0: return False
    hw = HR * math.sqrt(1.0 - t * t)
    return abs(x - HCX) <= hw
paint(in_skull)
# brow ridge catches the most light; falls into the eye socket below
by = HCY - HR * 0.28
for y in range(int(by - 1), int(by + 2)):
    hw = HR * 0.7 * math.sqrt(max(0.0, 1.0 - ((y - by) / 1.4) ** 2))
    for x in range(int(HCX - hw), int(HCX + hw) + 1):
        Lv = L(x, y) * (0.95 if y <= by else 0.70)
        ch, fg = hue_ramp(Lv)
        set_cell(cv, x, y, ch, fg, 0)
eye(cv, HCX + HR * 0.28, HCY + HR * 0.18, r=1.3, iris_fg=93, glint=True)

# --- the LONG CAST SHADOW: low sun throws it far LEFT along the plain -- a thin DIM
#     streak that reads as "low light / dusk" and grounds the figure. -----------------
for y in range(GROUND_Y, H - 2):
    t = (y - GROUND_Y) / max(1, (H - 2 - GROUND_Y))        # 0 at feet -> 1 far out
    sx = HIP_X - t * 30.0                                   # shadow reaches left+down
    hw = 2.0 + t * 3.0                                      # widens as it stretches out
    for x in range(int(sx - hw), int(sx + hw) + 1):
        if 0 <= x < W:
            set_cell(cv, x, y, "\u2591", 8, 0)

# --- sparse debris marks on the plain (keeps the lower third varied, Pass 5) ---------
import random; random.seed(3)
for _ in range(14):
    dx = random.randint(2, W - 3)
    dy = GROUND_Y + random.randint(1, H - GROUND_Y - 3)
    if 0 <= dx < W and 0 <= dy < H and cv[dy][dx][0] == " ":
        set_cell(cv, dx, dy, "\u2591", 8, 0)

# ===========================================================================
# PASS: TOP boxed title card (house wants top AND bottom; hollis keeps the bottom).
#   Drawn in-canvas at the top so it never clobbers the figure (figure sits rows ~14..35).
# ===========================================================================
RULE = "\u2550"; QUAD = "\u2592"
def put_centered(s, y, fg=94):
    x = (W - len(s)) // 2
    for i, ch in enumerate(s):
        if 0 <= x + i < W and 0 <= y < H:
            cv[y][x + i] = [ch, fg, 0]

def setc(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        cv[y][x] = [ch, fg, 0]

x0, x1, y0, y1 = 3, W - 4, 1, 6
for x in range(x0, x1 + 1):
    setc(x, y0, RULE, 12); setc(x, y1, RULE, 12)
for y in range(y0, y1 + 1):
    setc(x0, y, QUAD, 8); setc(x1, y, QUAD, 8)
put_centered("WASTELAND", y0 + 2, 15)
put_centered("// a figure lit by the last light //", y0 + 4, 8)

# ---- render + write: ONE credit sequence, standalone reset tail -------------------
out = []
render(cv, out)
path = "scratch/_wasteland.ans"
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
hygiene_gate(path)
print("wrote", path, "-- WASTELAND v3 base; rows:", len(out))
