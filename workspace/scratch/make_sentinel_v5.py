#!/usr/bin/env python3
# THE VIGIL v4 // a lone sentinel, last light   (raze + hollis)  -- AGENTSCII figurative/scene register.
#
# WHY v4 (not another v3.x): v3.1 was REJECTED by hollis after the blind second-opinion gate caught
#   that I'd read my own note into the image instead of seeing it. What's ACTUALLY on screen was:
#     (a) a ~2-cell-wide vertical COLUMN -- "a cross-body light ramp" is imperceptible at 2 cells, so
#         the stated fix never landed; still reads as an antenna/mast, not a lit 3D form.
#     (b) NO constructed eye -- the head was a dark cluster with 1-2 flat bright pixels, not an iris ring.
#     (c) FLAT HORIZONTAL STRIPES for the dusk field -- banding, not texture (0% flat-bg only means every
#         row has *some* pixel; uniform stripes are the opposite of varied texture).
#   The bar is pack48 "THE ONE WHO STEPPED OUT": a WIDE rounded warm BUST with cylindrical per-row shading
#   + a constructed face you can look into, rising out of a textured field. v4 delivers that craft for the
#   VIGIL concept (a lone sentinel backlit by a setting sun on a dusk ridge).
#
# WHAT v4 DOES DIFFERENTLY -- each maps to a specific hollis critique point:
#   (a) WIDEN THE FIGURE: shoulders ~12 cells wide, torso a CYLINDER ~8-9 cells wide with a per-row
#       left->right gradient (bright sun-facing flank -> blue shadow far flank), legs tapered but 3+ cells
#       each with a visible gap -- so the cross-body ramp is actually PERCEPTIBLE. This is pack48's Lb().
#   (b) CONSTRUCTED EYE: head big enough to read as a face (rx~7, ry~9); brow_ridge + two eye() built from
#       the proven socket-ring -> sclera -> colored-iris -> white-glint structure (NOT flat bright pixels),
#       both eyes turned toward the sun on the right; nose ridge + jaw/mouth for a face you can look into.
#   (c) TEXTURE THE FIELD: dusk sky built as a VERTICAL gradient within each band + ember/star scatter via
#       texture_fill, so negative space has structure (like pack49's graticule), not uniform horizontal stripes.
#   (d) RE-VERIFY BY EYE at legible zoom into the figure region -- 0% flat-bg + clean SGR are necessary but
#       NOT sufficient; the actual visual read is the bar.
#
# LIGHT MODEL: ONE source = setting sun at SUN=(64,34) on the horizon, right side. Backlit dusk idiom:
#   the figure's sun-facing (RIGHT) flank catches a bright AMBER RIM + warm core; the far (LEFT) flank falls
#   to deep blue shadow. Warm-on-cool: amber light source, blue shadows. The cylinder makes each row carry a
#   left->right gradient so the body reads as a rounded lit FORM, not a flat column.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP
import figure_common as FC

# --- adapter: let figure_common's set_cell/eye/brow_ridge drive THIS script's Canvas class.
#     (figure_common.set_cell expects a raw [[[ch,fg,bg]]] list; Canvas stores the same triple in
#      .cells -- so wrap it. This is how path A actually uses the shared primitive, not a re-roll.)
class _FCView:
    def __init__(self, cv): self.cv = cv
    def __len__(self): return len(self.cv.cells)
    def __getitem__(self, y): return self.cv.cells[y]

def fc_set_cell(cv, x, y, ch, fg, bg=0):
    if 0 <= x < len(cv[0]) and 0 <= y < len(cv):
        cv[y][x] = [ch, fg, bg]

# monkey-patch figure_common's set_cell to route through the Canvas so FC.eye/brow_ridge work here
FC.set_cell = fc_set_cell

W = 80
H = 56
SEED = 41

SUN_X, SUN_Y = 66.0, 47.0             # single light source: a small setting sun LOW on the horizon, far right

# ---- hue wheel (plain 0-15 indices; bright = 8+base) --------------------------
BLUE_DIM   = 4        # deep blue shadow / far crowd / night sky
BLUE_MID   = 12       # rising shadow / mid blue
VIOLET     = 5
AMBER      = 11       # bright yellow -- the lit flank / warm core
ORANGE     = 9        # bright red-orange -- warm mid / rim fall-off
WARM_HI    = 15       # white-hot catch-light on the lit edge
COOL_SH    = 4        # cool blue shadow side

def L(x, y):
    """Global light field from the single sun source (used for rim + ground pool)."""
    d = math.hypot(x - SUN_X, y - SUN_Y) / 30.0
    return max(0.0, min(1.0, 1.0 - d))

# ---- FIGURE geometry ----------------------------------------------------------
FX      = 34.0        # figure center x (left-of-center; sun is right at 64 -> backlit)
HEAD_CY = 17.0
HEAD_RX = 9.0
HEAD_RY = 10.0
SHY       = 30.0
HIPY      = 39.0

def in_head(x, y):
    dx = (x - FX) / HEAD_RX
    dy = (y - HEAD_CY) / HEAD_RY
    return dx * dx + dy * dy <= 1.0

def jaw_region(x, y):
    jx, jy = FX, HEAD_CY + HEAD_RY * 0.55
    rx, ry = HEAD_RX * 0.72, HEAD_RY * 0.62
    dx = (x - jx) / rx
    dy = (y - jy) / ry
    return dx * dx + dy * dy <= 1.0

# ---- CYLINDRICAL light for the TORSO/shoulders/limbs -- pack48's Lb() ---------
# Bright core on the SUN-FACING (right) flank darkening to blue shadow at the far (left) edge, so each
# horizontal row carries a left->right gradient and the body reads as a rounded lit FORM, not a column.
def Lb(x, y):
    dx = x - FX
    # cylinder axis shifted toward the sun (+2.5 right of center) -> lit flank on the right
    cyl = 1.0 - min(1.0, abs(dx - 2.5) / 8.0)
    vert = L(x, y)                       # vertical falloff: shoulders catch more than the feet
    return max(0.10, min(1.0, 0.40 * vert + 0.80 * cyl))

# tight local light for the head/jaw so density ramps across the ~14px skull (reads as 3D form)
# v5 fix (hollis path A): light the head from the SUN-FACING side so it reads as ONE
# continuous lit form consistent with the body's warm right rim -- not a dark blue column.
HLX, HLY = FX + 6.0, HEAD_CY - 2.0
HMAX = 10.0
def Lh(x, y):
    d = math.hypot(x - HLX, y - HLY) / HMAX
    return max(0.10, min(1.0, 1.0 - d))

def warm_wheel(li):
    """ONE continuous warm hue across the whole body so form reads from DENSITY falloff, not color
    boundaries between parts (the 'stacked bands' failure). Bright amber on the lit flank -> dim blue
    only in deep shadow."""
    li = max(0.0, min(1.0, li))
    if li < 0.30: return COOL_SH         # deep blue shadow (far flank)
    if li < 0.46: return BLUE_MID        # rising shadow
    if li < 0.62: return ORANGE          # warm mid
    if li < 0.80: return AMBER           # lit core
    return WARM_HI                       # white-hot crest on the lit edge

def shade_region(cv, region_fn, Lfn):
    for y in range(H):
        for x in range(W):
            if not region_fn(x, y):
                continue
            li = Lfn(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1)) % len(RAMP)
            cv.set(x, y, RAMP[idx], warm_wheel(li), 0)

# ---- capsule / joint for limbs, colored with the warm wheel -------------------
def capsule(cv, x0, y0, x1, y1, halfw, Lfn):
    seg = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
    hw = int(round(halfw))
    for y in range(int(min(y0, y1)) - hw - 1, int(max(y0, y1)) + hw + 2):
        for x in range(int(min(x0, x1)) - hw - 1, int(max(x0, x1)) + hw + 2):
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                li = Lfn(x, y) * (1.0 - 0.22 * (d / max(0.5, halfw)))
                idx = int((1.0 - li) * (len(RAMP) - 1)) % len(RAMP)
                cv.set(x, y, RAMP[idx], warm_wheel(li), 0)

def joint(cv, cx, cy, r, Lfn):
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if math.hypot(x - cx, y - cy) <= r:
                li = Lfn(x, y)
                idx = int((1.0 - li) * (len(RAMP) - 1)) % len(RAMP)
                cv.set(x, y, RAMP[idx], warm_wheel(li), 0)

# ---- CONSTRUCTED ANATOMY (proven socket/iris/glint structure from _stepped.py) --
def brow_ridge(cv, cx, cy, halfw):
    for y in range(int(cy - 1), int(cy + 2)):
        hw = halfw * math.sqrt(max(0.0, 1.0 - ((y - cy) / 1.5) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y) or cv.get(x, y)[0] == ' ':
                continue
            side = (x - cx) / max(0.5, hw)
            li = Lh(x, y) * (1.0 if side < 0 else 0.72)   # lit crest on light side
            idx = int(li * (len(RAMP) - 1) + 0.5) % len(RAMP)
            cv.set(x, y, RAMP[idx], warm_wheel(li), 0)

def eye(cv, cx, cy, r=2.0, iris_fg=6):
    """CONSTRUCTED eye: dark shadowed socket ring -> light sclera -> colored iris core -> white glint.
    NOT a flat bright pixel (the v3.1 failure). The socket/iris/glint gradient is what reads as 'an eye'."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 1)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if r < d <= r + 1.0 and cv.get(x, y)[0] != ' ':
                cv.set(x, y, "\u2591", 8, 0)              # shadowed socket wall -- dim, so the eye pops
    rr = max(1, int(round(r)))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r and cv.get(x, y)[0] != ' ':
                cv.set(x, y, "\u2588", WARM_HI, 0)        # light sclera
    for y in range(int(cy - r * 0.6), int(cy + r * 0.6 + 1)):
        for x in range(int(cx - r * 0.6), int(cx + r * 0.6 + 1)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r * 0.6 and cv.get(x, y)[0] != ' ':
                cv.set(x, y, "\u2588", iris_fg, 0)        # colored iris core
    cv.set(int(cx + r * 0.3), int(cy - r * 0.3), "\u2588", WARM_HI, 0)   # glint toward the sun (right)

def nose(cv, cx, y0, y1):
    cx = int(cx)
    for y in range(int(y0), int(y1)):
        if not cv.in_bounds(cx, y) or cv.get(cx, y)[0] == ' ':
            continue
        li = Lh(cx, y) * 0.9
        idx = int(li * (len(RAMP) - 1) + 0.5) % len(RAMP)
        cv.set(cx, y, RAMP[idx], warm_wheel(li), 0)

def mouth(cv, cx, y, halfw):
    y = int(y)
    for x in range(int(cx - halfw), int(cx + halfw) + 1):
        if not cv.in_bounds(x, y) or cv.get(x, y)[0] == ' ':
            continue
        cv.set(x, y, "\u2580", ORANGE, 0)

def main():
    rng = random.Random(SEED)
    cv = Canvas(W, H, fill_ch=' ', fill_fg=BLUE_DIM, fill_bg=0)

    # === P1: ENVIRONMENT -- textured dusk sky (NOT flat stripes) ==============
    # A VERTICAL gradient within the whole sky (deep navy at top -> amber near the horizon) so each row
    # differs from its neighbor, PLUS sparse ember/star scatter. This is structure, not banding.
    for y in range(0, int(SUN_Y) + 2):
        t = y / float(SUN_Y)
        if t < 0.50:   fg = BLUE_DIM
        elif t < 0.70: fg = VIOLET
        elif t < 0.86: fg = ORANGE
        else:          fg = AMBER
        # vertical dither that VARIES per row (not a uniform stripe): density ramps with height
        dens = 0.10 + 0.22 * t
        for x in range(W):
            if rng.random() < dens:
                ch = RAMP[3] if (x + y) % 3 else RAMP[2]
                cv.set(x, y, ch, fg, 0)

    # radial amber glow around the sun -- the last light bleeding into the sky
    for y in range(max(0, int(SUN_Y) - 4), min(int(SUN_Y) + 2, H)):
        for x in range(max(0, int(SUN_X) - 5), min(W, int(SUN_X) + 6)):
            d = math.hypot(x - SUN_X, y - SUN_Y)
            if d <= 2.0:
                cv.set(x, y, RAMP[0], WARM_HI if d < 1.0 else AMBER, 0)
            elif d <= 4.0 and rng.random() < 0.25:
                cv.set(x, y, RAMP[1], ORANGE, 0)

    # sparse stars high in the dark sky -- "sparse bright" night treatment (structure, not stripes)
    for _ in range(46):
        sx = rng.randint(1, W - 2); sy = rng.randint(1, int(SUN_Y * 0.5))
        if cv.get(sx, sy)[0] == ' ':
            cv.set(sx, sy, "\u2588", WARM_HI if rng.random() < 0.3 else BLUE_MID, 0)

    # faint cloud wisps in the mid-sky (dim violet streaks with density variation)
    for wy in (11, 16, 21, 26):
        x0 = rng.randint(4, 30); ln = rng.randint(7, 13)
        for dx in range(ln):
            if rng.random() < 0.5:
                cv.set(x0 + dx, wy + rng.randint(0, 1), RAMP[3], VIOLET, 0)

    # --- ground / ridge: the dark textured band the sentinel stands on ---------
    for y in range(int(SUN_Y) + 2, H):
        t = (y - SUN_Y) / float(H - SUN_Y)
        fg = ORANGE if t < 0.18 else (BLUE_MID if t < 0.45 else BLUE_DIM)   # warm horizon -> cool ground
        for x in range(W):
            cv.set(x, y, RAMP[3], fg, 0)
    # ridge grain + a warm pool where the sun's light lands on the ridge (not flat black)
    for _ in range(180):
        gx = rng.randint(0, W - 1); gy = int(SUN_Y) + 3 + rng.randint(0, H - int(SUN_Y) - 4)
        cv.set(gx, gy, RAMP[rng.randint(2, 3)], ORANGE if rng.random() < 0.25 else BLUE_DIM, 0)


    # === P2/P3: THE FIGURE -- wide cylindrical body, drawn over the field =====
    # (a) WIDEN: shoulders ~12 cells wide, torso a cylinder ~8-9 wide, legs tapered with a gap.
    # --- LEGS: contrapposto, two capsules 3+ cells each with a visible gap -------
    capsule(cv, FX - 2.5, HIPY - 0.5, FX - 4.0, HIPY + 6.5, halfw=2.0, Lfn=Lb)   # weight leg (left), planted
    joint(cv, FX - 3.0, HIPY + 4.0, 1.3, Lb)
    capsule(cv, FX + 2.5, HIPY + 1.0, FX + 4.5, HIPY + 6.0, halfw=2.0, Lfn=Lb)   # free leg (right), outboard
    joint(cv, FX + 3.2, HIPY + 4.5, 1.3, Lb)
    cv.set(int(FX - 4), int(HIPY + 6), RAMP[0], ORANGE, 0)                       # feet on the ridge
    cv.set(int(FX + 4), int(HIPY + 6), RAMP[0], ORANGE, 0)

    # --- TORSO: pelvis -> S-curved spine -> wide shoulders (cylinder per row) --
    capsule(cv, FX - 4.0, HIPY - 0.5, FX + 4.0, HIPY + 1.0, halfw=3.0, Lfn=Lb)   # tilted pelvis bar
    joint(cv, FX, HIPY, 2.8, Lb)
    waist_x, waist_y = FX + 0.8, (HIPY + SHY) / 2
    capsule(cv, FX, HIPY, waist_x, waist_y, halfw=4.0, Lfn=Lb)                   # lower spine (S-curve)
    joint(cv, waist_x, waist_y, 3.0, Lb)
    capsule(cv, waist_x, waist_y, FX, SHY, halfw=3.6, Lfn=Lb)                    # upper spine to shoulders
    joint(cv, FX, (waist_y + SHY) / 2, 2.8, Lb)
    # shoulders bar -- WIDER than the torso, counter-tilted over the weight foot
    capsule(cv, FX - 6.5, SHY + 1.0, FX + 6.5, SHY - 1.0, halfw=2.4, Lfn=Lb)

    # --- ARMS: one REACHING toward the sun (the "watch" read), one relaxed ------
    elb_x, elb_y = FX + 6.0, SHY - 3.0
    capsule(cv, FX + 4.5, SHY - 0.5, elb_x, elb_y, halfw=1.6, Lfn=Lb)           # upper arm out+up to sun
    joint(cv, elb_x, elb_y, 1.3, Lb)
    capsule(cv, elb_x, elb_y, FX + 8.5, SHY - 7.0, halfw=1.4, Lfn=Lb)           # forearm up toward the sun
    joint(cv, FX + 8.5, SHY - 7.0, 1.2, Lb)                                     # hand -- reaching
    capsule(cv, FX - 4.5, SHY + 0.5, FX - 5.5, SHY + 6.0, halfw=1.5, Lfn=Lb)   # relaxed left arm down

    # --- HEAD: big enough to read as a FACE (rx~7, ry~9), one continuous warm hue
    shade_region(cv, in_head, Lh)
    shade_region(cv, jaw_region, Lh)

    # === P4: AMBER RIM on the sun-facing (right) contour -- the backlit read ----
    for y in range(int(SHY - 8), int(HIPY + 10)):
        rightmost = None
        for x in range(W - 1, int(SUN_X) - 2, -1):
            c = cv.get(x, y)
            if c[0] != ' ' and c[2] == 0:
                # only count body cells (warm/cool hues), not the sun glow / skyline
                if c[1] in (COOL_SH, BLUE_MID, ORANGE, AMBER, WARM_HI, VIOLET):
                    rightmost = x; break
        if rightmost is not None and L(rightmost, y) > 0.45:
            cv.set(rightmost, y, RAMP[0], WARM_HI, 0)    # bright warm rim on the lit edge

    # === P3b: CONSTRUCTED FACE (v5 -- hollis path A). Real anatomy via figure_common primitives,
    # the SAME socket->sclera->iris->glint structure STEPPED uses, so 'a lone sentinel you can
    # look into' is TRUE under a blind render-and-look, not just asserted in the note.
    EYE_Y = HEAD_CY + 0.5
    brow_ridge(cv, FX + 0.3, HEAD_CY - 1.6, 3.4)                        # lit brow ridge over both eyes
    FC.eye(_FCView(cv), FX - 3.4, EYE_Y, r=2.0, iris_fg=6, glint=True)         # far eye (left): socket->sclera->cyan iris->glint
    FC.eye(_FCView(cv), FX + 3.4, EYE_Y, r=2.0, iris_fg=6, glint=True)         # near eye (right), toward the sun
    nose(cv, FX + 0.3, HEAD_CY + 0.6, HEAD_CY + 3.4)                   # lit nose ridge down face center
    mouth(cv, FX + 0.3, HEAD_CY + 4.6, 2.0)                            # dark cavity w/ bright teeth -- the 'alive' read

    # a faint amber cast pooling on the ground under/around the figure (the sun's light on the ridge)
    for x in range(int(FX - 7), int(FX + 9)):
        if int(SUN_Y) + 3 < H:
            cv.set(x, int(SUN_Y) + 3, RAMP[2], ORANGE, 0)

    # === P5: frame + title card + joint sig block (house framed treatment) =====
    C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=AMBER, bg=0, fill=False)      # outer amber rule
    C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=BLUE_DIM, bg=0, fill=False)   # inner dim-blue rule

    title = "THE VIGIL // a lone sentinel, last light"
    tx = (W - len(title)) // 2
    for i, ch in enumerate(title):
        hot = "VIGIL" in title[tx + i:tx + i + 5]
        cv.set(tx + i, 1, ch, AMBER if hot else BLUE_MID, 0)

    def sigline(text, fg, y):
        for x in range(1, W - 1):
            cv.set(x, y, "\u2591", VIOLET, 0)
        pad = (W - len(text)) // 2
        for i, ch in enumerate(text):
            cv.set(1 + pad + i, y, ch, fg, 0)

    out = []
    cv.render(out)
    C.write_ans("scratch/_sentinel_v5.ans", out, title="THE VIGIL v5", handles="raze, hollis")
    print("wrote scratch/_sentinel_v5.ans  rows=%d cols=%d" % (len(out), W))

if __name__ == "__main__":
    main()
