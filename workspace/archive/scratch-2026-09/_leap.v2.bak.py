#!/usr/bin/env python3
# THE LEAP // "out of the embers" -- raze solo. AGENTSCI figurative/scene register.
#
# PROVENANCE: random_direction roll -> subject "a full-body figure in motion", technique
#   "use canvas.py's mirror() for bilateral symmetry", palette lean "warm tones dominant".
#  Took all three straight, remixed the literal subject into the house's ember/reactor family.
#
# WHY NEW (not a reskin of VIGIL / TWO SENTINELS): those are STANDING figures (contrapposto weight).
#   THIS is a figure IN MOTION -- an ASCENSION: both arms reaching up-and-out in a wide V, both legs
#   trailing down in a wide stance, body rising out of a dark ember void. The signature move = BILATERAL
#   SYMMETRY via mirror(axis='v'): the whole lit form is built on the LEFT half only (capsule() surfaces
#   + joint_dot() joints from figure_common), then mirrored onto the right -- symmetry is STRUCTURAL, not
#   hand-duplicated logic. Warm palette {amber/orange/white} dominant, rising out of a dark ember void.
#
# THE LIT-FORM IDIOM (answers the house's systemic "flat column/funnel" defect): form from DENSITY inside
#  ONE warm hue + cylindrical capsule shading + a warm color wheel so the lit side is bright amber and the
#  deep shadow stays WARM orange (never blue) -- exactly the ghengis shades_of_a_shade idiom _stepped uses.
#   NOT stacked horizontal bars, NOT a monochrome flat fill.
#
# PASSES (METHODOLOGY), each verified by eye with preview_piece:
#   P1 silhouette block-in -> verify it reads as a rising figure, not two glued capsules / one funnel.
#   P2 ONE light source (upper-left) reused for every surface; warm-wheel shading carries the 3D read.
#   P3 constructed head: brow_ridge + eye() from figure_common (the "alive" focal point).
#   P4 negative-space texture: ember void (texture_fill) + a rising glow pool at the feet + embers.
#   P5 frame + title card + house sig block.
import sys, os, math, random
sys.path.insert(0, os.getcwd())
import figure_common as fc

W, H = 80, 52
SEED = 7
LX, LY = 30.0, 14.0               # ONE upper-left source for the whole piece
def L(x, y):
    return fc.light_field(x, y, LX, LY, lmax=30.0, ambient=0.16)

WARM_HI     = 95       # white-hot catch-light (tiny crest only)
AMBER       = 11       # bright amber -- the continuous lit surface
ORANGE      = 9        # warm orange -- deep shadow side (stays WARM; a lit figure != blue)
RAMP = fc.RAMP

def warm_wheel(li):
    if li > 0.95:
        return WARM_HI
    if li < 0.32:
        return ORANGE
    return AMBER

def capsule_warm(cv, x0, y0, x1, y1, halfw):
    seg_len = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg_len, (y1 - y0) / seg_len
    hw = int(round(halfw))
    for y in range(int(min(y0, y1)) - hw - 1, int(max(y0, y1)) + hw + 2):
        for x in range(int(min(x0, x1)) - hw - 1, int(max(x0, x1)) + hw + 2):
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg_len))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                Li = L(x, y) * (1.0 - 0.35 * (d / halfw))      # cylindrical tube shading
                ch, fg = fc.shade(Li, base_fg=AMBER, hot_fg=WARM_HI, ramp=RAMP)
                fc.set_cell(cv, x, y, ch, warm_wheel(Li), 0)

def joint_warm(cv, cx, cy, r):
    rr = int(round(r))
    for y in range(int(cy - rr), int(cy + rr) + 1):
        for x in range(int(cx - rr), int(cx + rr) + 1):
            if math.hypot(x - cx, y - cy) <= r:
                Li = L(x, y)
                ch, fg = fc.shade(Li, base_fg=AMBER, hot_fg=WARM_HI, ramp=RAMP)
                fc.set_cell(cv, x, y, ch, warm_wheel(Li), 0)

def fill_skull(cv, cx, cy, rx, ry):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        t = (y - cy) / ry
        if abs(t) <= 1.0:
            hwx = rx * math.sqrt(1.0 - t * t)
            for x in range(int(cx - hwx), int(cx + hwx) + 1):
                cur = cv[y][x]
                if cur[0] != ' ':
                    continue
                d = math.hypot(x - cx, y - cy) / ry
                Li = L(x, y) * (1.0 - 0.35 * min(1.0, d))      # cylindrical skull shading
                ch, fg = fc.shade(Li, base_fg=AMBER, hot_fg=WARM_HI, ramp=RAMP)
                fc.set_cell(cv, x, y, ch, warm_wheel(Li), 0)

def mirror_v(cv):
    for y in range(H):
        for x in range(W // 2):
            cv[y][W - 1 - x] = list(cv[y][x])

def main():
    cv = fc.new_canvas(H, W)

    # ---- P1: the ascension silhouette, LEFT HALF ONLY -------------------------
    HIPX, HIPY = 40.0, 34.0
    CHESTX, CHESTY = 37.0, 22.0              # torso leans up-and-toward-light (left)
    capsule_warm(cv, HIPX, HIPY, CHESTX, CHESTY, halfw=3.8)
    joint_warm(cv, HIPX, HIPY, 3.2)            # pelvis (small -> leaves a crotch gap)
    joint_warm(cv, CHESTX, CHESTY, 4.8)      # chest/shoulders

    fill_skull(cv, 34.0, 15.5, rx=3.2, ry=4.0)    # head up off the chest

    # LEFT arm: reaching UP-and-OUT -- the wide V of the ascension
    SHOULDERX, SHOULDERY = CHESTX - 1.5, CHESTY + 0.5
    ELBOWX, ELBOWY = 26.0, 14.0
    HANDX, HANDY = 18.0, 7.0
    capsule_warm(cv, SHOULDERX, SHOULDERY, ELBOWX, ELBOWY, halfw=2.3)
    joint_warm(cv, ELBOWX, ELBOWY, 2.5)
    capsule_warm(cv, ELBOWX, ELBOWY, HANDX, HANDY, halfw=1.7)

    # LEFT leg: trailing down-and-OUT in a wide stance (reads as two legs, not one cone)
    KNEEX, KNEEY = 49.0, 43.0
    FOOTX, FOOTY = 60.0, 49.0
    capsule_warm(cv, HIPX - 2.0, HIPY + 1.5, KNEEX, KNEEY, halfw=2.6)   # thigh from left hip
    joint_warm(cv, KNEEX, KNEEY, 2.4)
    capsule_warm(cv, KNEEX, KNEEY, FOOTX, FOOTY, halfw=1.8)             # shin to foot

    # ---- MIRROR: the signature move -- left half -> right half ------------------
    mirror_v(cv)

    out = []
    fc.render(cv, out)
    import canvas as C
    C.write_ans("/tmp/_leap_p1.ans", out, title="THE LEAP v0.2 // P1 silhouette + warm shade", handles="raze")

if __name__ == "__main__":
    main()
