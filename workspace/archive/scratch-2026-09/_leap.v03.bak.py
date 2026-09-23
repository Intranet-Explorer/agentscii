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
RED           = 91        # deep warm red -- the ember-eye iris core
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

def fill_skull_left(cv, cx, cy, rx, ry):
    """Paint ONLY the left half (x <= cx) of a centered head so mirror_v completes it into one
    symmetric skull -- NOT two heads. Cylindrical shading: left flank bright, center dim."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        t = (y - cy) / ry
        if abs(t) <= 1.0:
            hwx = rx * math.sqrt(1.0 - t * t)
            for x in range(int(cx - hwx), int(cx) + 1):            # left half only, incl. center col
                cur = cv[y][x]
                if cur[0] != ' ':
                    continue
                d = math.hypot(x - cx, y - cy) / ry
                Li = L(x, y) * (1.0 - 0.35 * min(1.0, d))         # cylindrical skull shading
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

    fill_skull_left(cv, 40.0, 13.0, rx=3.6, ry=4.2)      # head centered on mirror axis (x=40), left half

    # LEFT arm: reaching UP-and-OUT -- the wide V of the ascension
    SHOULDERX, SHOULDERY = CHESTX - 1.5, CHESTY + 0.5
    ELBOWX, ELBOWY = 26.0, 14.0
    HANDX, HANDY = 18.0, 7.0
    capsule_warm(cv, SHOULDERX, SHOULDERY, ELBOWX, ELBOWY, halfw=2.3)
    joint_warm(cv, ELBOWX, ELBOWY, 2.5)
    capsule_warm(cv, ELBOWX, ELBOWY, HANDX, HANDY, halfw=1.7)

    # LEFT leg: trail down-and-OUT on its OWN side (left of center). Knee/foot stay x<40 so the
    #   mirrored pair DIVERGES into a wide stance -- NOT cross inward and fuse into one funnel
    #   (the mirror-fuses-into-one-form trap; also the systemic flat-column defect).
    KNEEX, KNEEY = 31.0, 45.0        # knee out-and-down on the left
    FOOTX, FOOTY = 23.0, 50.0        # foot trailing further out
    capsule_warm(cv, HIPX - 1.5, HIPY + 1.0, KNEEX, KNEEY, halfw=2.4)   # thigh from left hip, angling OUT
    joint_warm(cv, KNEEX, KNEEY, 2.2)
    capsule_warm(cv, KNEEX, KNEEY, FOOTX, FOOTY, halfw=1.6)             # shin to foot

     # ---- P3: constructed face features, built on the LEFT HALF so they mirror symmetrically ---
    fc.brow_ridge(cv, 37.0, 12.0, halfw=2.6, light=L, base_fg=AMBER, hot_fg=WARM_HI)    # left brow
    fc.eye(cv, 37.0, 14.0, r=1.5, iris_fg=RED, glint=True)                               # glowing ember eye

    # ---- MIRROR: the signature move -- left half -> right half ------------------
    mirror_v(cv)

     # ---- P4: ember void -- texture the negative space, a rising glow pool, drifting embers ---
    import canvas as C
    rng = random.Random(SEED + 3)
    def is_subject(x, y):
        cur = cv[y][x]
        return cur[0] != ' '
     # ember void: sparse warm dust behind the figure (not flat black)
    for y in range(H):
        for x in range(W):
            if is_subject(x, y):
                continue
            if rng.random() > 0.30:
                continue
            idx = rng.randint(len(RAMP) // 2, len(RAMP) - 1)
            fc.set_cell(cv, x, y, RAMP[idx], ORANGE, 0)
     # a rising glow pool at the feet -- embers gathering under the trailing stance
    for y in range(46, H):
        for x in range(W):
            if is_subject(x, y):
                continue
            d = math.hypot(x - W / 2.0, y - 51.0)
            if d < 16.0 and rng.random() < 0.45 * (1.0 - d / 16.0):
                ch, fg = fc.shade(1.0 - d / 18.0, base_fg=ORANGE, hot_fg=WARM_HI, ramp=RAMP)
                fc.set_cell(cv, x, y, ch, fg, 0)
     # drifting embers rising up the sides -- short warm marks
    for _ in range(96):
        ex = rng.randint(2, W - 3)
        ey = rng.randint(4, H - 3)
        if is_subject(ex, ey):
            continue
        Lv = L(ex, ey)
        ch, fg = fc.shade(Lv + 0.15, base_fg=ORANGE, hot_fg=WARM_HI, ramp=RAMP)
        fc.set_cell(cv, ex, ey, ch, fg, 0)

     # ---- P5: frame + title card -------------------------------------------------
    out = []
    out.append(fc.c(13) + "\u2554" * W)                # top rule (magenta house frame)
    fc.render(cv, out)
    out.append(fc.c(13) + "\u2557" * W)                # bottom rule
    C.write_ans("/tmp/_leap_p1.ans", out, title="THE LEAP v0.3 // out of the embers", handles="raze")

if __name__ == "__main__":
    main()
