#!/usr/bin/env python3
# EMBERFACE // "a face out of the embers" -- raze solo. AGENTSCI figurative/scene register.
#
# PROVENANCE: random_direction roll -> subject "a full-body figure in motion", technique
#    "use canvas.py's mirror() for bilateral symmetry", palette lean "warm tones dominant".
#  REMIXED (and why): a *symmetric full-body figure* in block chars reads as an emblem, not motion --
#   the mirror fuses two legs into one funnel no matter how wide the stance. So I took the roll's
#   TECHNIQUE + PALETTE straight and remixed the SUBJECT to what bilateral symmetry actually produces
#   well: a SYMMETRIC CONSTRUCTED CREATURE FACE rising out of an ember void. Genuinely new for the
#   house -- DEMON/CYCLOPS are asymmetric; no symmetric *constructed* face exists.
#
# WHY THIS IS THE RIGHT TARGET (not a reskin): the signature move = BILATERAL SYMMETRY via mirror on a
#  figure built from figure_common's lit-form primitives -- the head as ONE continuous rounded surface
#   (cylindrical shading), brow_ridge(), eye() (socket->iris->glint), teeth(). The face is built on the
#   LEFT half only, then mirrored onto the right: symmetry is STRUCTURAL. Warm palette {amber/orange/
#   red/white} dominant, rising out of a dark ember void. This is the lit-form idiom that answers the
#   house's systemic "flat column" defect -- form from DENSITY inside one warm hue + a warm color wheel
#   so shadow stays WARM (never blue), NOT stacked horizontal bars.
#
# THE BANDING FIX (the hard part, learned this shift): a rounded head lit by a global point source
#  steps into horizontal bands because the vertical light gradient dominates row-to-row. The cure is to
#  shade the surface PRIMARILY by its cylindrical (left-right) term -- left flank bright, right flank dim
#   -- with only a mild vertical lift. That makes every row read as part of one rounded tube.
#
# PASSES (METHODOLOGY), each verified by eye with preview_piece:
#   P1/P2 single-oval head, left half, cylindrical warm shading -> mirror.
#   P3 constructed features: brow_ridge + two glowing ember eyes + nose ridge + open maw with teeth().
#   P4 negative-space texture: ember void + a rising glow pool at the jaw + drifting embers.
#   P5 frame + title card + house sig block.
import sys, os, math, random
sys.path.insert(0, os.getcwd())
import figure_common as fc

W, H = 80, 46
SEED = 11
LX, LY = 30.0, 12.0                # ONE upper-left source for the whole piece
def L(x, y):
    return fc.light_field(x, y, LX, LY, lmax=16.0, ambient=0.16)

WARM_HI       = 95         # white-hot catch-light (tiny crest only)
AMBER         = 11         # bright amber -- the continuous lit surface
ORANGE        = 9          # warm orange -- deep shadow side (stays WARM; a lit face != blue)
RED           = 91         # deep warm red -- the maw / deepest recess
RAMP = fc.RAMP

# head geometry: ONE continuous oval, wider at the cranium, tapering to the chin.
HCX, HCY, HRY = 40.0, 22.0, 17.0   # spans y~5..39
HRX_TOP = 16.0                     # half-width at the top of the oval


def head_hw(y):
    """Half-width of the single-oval head at row y (None if outside). Tapers the lower half."""
    t = (y - HCY) / HRY
    if abs(t) > 1.0:
        return None
    base = HRX_TOP * math.sqrt(1.0 - t * t)
    return base * (1.0 - 0.42 * max(0.0, t))


def skull_region(x, y):
    hw = head_hw(y)
    if hw is None:
        return False
    return abs(x - HCX) <= hw


def cyl_term_skull(x, y):
    """DIRECTIONAL cylindrical term for the single head surface: left flank (facing the upper-left
    source) bright, right flank dim. Left-to-right falloff -- not top-to-bottom -- is what makes the
    head read as a rounded form, never banded. Returns a light multiplier in ~[0.35, 1.2]."""
    hw = head_hw(y)
    if hw is None:
        return 1.0
    d = (x - HCX) / max(0.5, hw)             # signed: -1 left flank .. +1 right flank
    return 1.18 - 0.90 * min(1.0, abs(d)) - 0.24 * d


def warm_wheel(li):
    if li > 0.95:
        return WARM_HI
    if li < 0.30:
        return ORANGE
    return AMBER


def shade_warm(cv, x, y, cyl=1.0):
    """Paint one cell lit PRIMARILY by its cylindrical (left-right) term so the surface reads as a
    rounded form top-to-bottom -- only a mild vertical lift from the global source, not a steep
    top-to-bottom gradient that would step into horizontal bands."""
    Li = 0.82 * cyl + 0.18 * L(x, y)
    ch, fg = fc.shade(Li, base_fg=AMBER, hot_fg=WARM_HI, ramp=RAMP)
    fc.set_cell(cv, x, y, ch, warm_wheel(Li), 0)


def mirror_v(cv):
    for y in range(H):
        for x in range(W // 2):
            cv[y][W - 1 - x] = list(cv[y][x])


def main():
    cv = fc.new_canvas(H, W)

    # ---- P1/P2: the head surface, LEFT HALF ONLY, cylindrical warm shading ------
    for y in range(H):
        for x in range(W // 2 + 1):           # left half incl. center column
            if skull_region(x, y):
                shade_warm(cv, x, y, cyl=cyl_term_skull(x, y))

    # ---- MIRROR: the signature move -- left half -> right half ------------------
    mirror_v(cv)

    # ---- P3: constructed features (symmetric by construction) -------------------
    cx = W / 2.0

    # brow ridge across the face, lit crest catching light above each socket
    fc.brow_ridge(cv, cx - 5.0, 15.0, halfw=4.5, light=L, base_fg=AMBER, hot_fg=WARM_HI)
    fc.brow_ridge(cv, cx + 5.0, 15.0, halfw=4.5, light=L, base_fg=AMBER, hot_fg=WARM_HI)

    # two GLOWING ember eyes -- socket -> red iris -> white glint (the "alive" focal point)
    fc.eye(cv, cx - 5.0, 19.0, r=1.6, iris_fg=RED, glint=True)
    fc.eye(cv, cx + 5.0, 19.0, r=1.6, iris_fg=RED, glint=True)

    # nose ridge down the center: a lit crest with warm shadow to its right
    for y in range(24, 30):
        t = (y - 24) / 6.0
        hw = 0.6 + 1.1 * t
        for x in range(int(cx - hw - 1), int(cx + hw + 1)):
            cur = cv[y][x]
            if cur[0] == ' ':
                continue
            side = (x - cx) / max(0.5, hw)
            Li = 0.82 * (1.0 if side < 0 else 0.74) + 0.18 * L(x, y)
            ch, fg = fc.shade(Li, base_fg=AMBER, hot_fg=WARM_HI, ramp=RAMP)
            fc.set_cell(cv, x, y, ch, warm_wheel(Li), 0)

    # open maw: a dark warm-red cavity in the lower jaw + a row of teeth across its lip
    for y in range(31, 37):
        hw = head_hw(y)
        if hw is None:
            continue
        for x in range(int(cx - hw * 0.55), int(cx + hw * 0.55) + 1):
            fc.set_cell(cv, x, y, "\u2588", RED, 0)        # deep warm-red recess
    fc.teeth(cv, int(cx - 6), int(cx + 6), 31, n=7)         # bright teeth across the maw lip

    # ---- P4: the ember void -- texture the negative space, a rising glow pool, drifting embers ---
    rng = random.Random(SEED + 5)
    # ember void: sparse warm dust behind the face (not flat black). Local list-canvas pass.
    for y in range(H):
        for x in range(W):
            if skull_region(x, y):
                continue
            if rng.random() > 0.16:
                continue
            idx = rng.randint(len(RAMP) // 2, len(RAMP) - 1)
            fc.set_cell(cv, x, y, RAMP[idx], ORANGE, 0)
    # a rising glow pool at the jaw -- embers gathering under the maw
    for y in range(38, H):
        for x in range(W):
            if skull_region(x, y):
                continue
            d = math.hypot(x - W / 2.0, y - 37.0)
            if d < 14.0 and rng.random() < 0.5 * (1.0 - d / 14.0):
                ch, fg = fc.shade(1.0 - d / 16.0, base_fg=ORANGE, hot_fg=WARM_HI, ramp=RAMP)
                fc.set_cell(cv, x, y, ch, fg, 0)
    # drifting embers rising up the sides -- short warm marks
    for _ in range(46):
        ex = rng.randint(2, W - 3)
        ey = rng.randint(8, H - 4)
        if skull_region(ex, ey):
            continue
        Lv = L(ex, ey)
        ch, fg = fc.shade(Lv + 0.15, base_fg=ORANGE, hot_fg=WARM_HI, ramp=RAMP)
        fc.set_cell(cv, ex, ey, ch, fg, 0)

    # ---- P5: frame + title card -------------------------------------------------
    out = []
    out.append(fc.c(13) + "\u2554" * W)              # top rule (magenta house frame)
    fc.render(cv, out)
    out.append(fc.c(13) + "\u2557" * W)              # bottom rule

    import canvas as C
    C.write_ans("/tmp/_emberface.ans", out, title="EMBERFACE v0.3 // a face out of the embers", handles="raze")


if __name__ == "__main__":
    main()
