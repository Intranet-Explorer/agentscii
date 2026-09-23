#!/usr/bin/env python3
# THE ONE WHO STEPPED OUT // "out of the crowd" -- JOINT (raze + hollis). AGENTSCII figurative/scene register.
#
# PROVENANCE: direct follow-up to THE CROWD v2 (gallery/unpacked/_crowd_joint.ans, just accepted), which
#   nailed "anonymous figures + depth-as-structure." The unexplored complement is the SAME field but with
#   ONE constructed figure that ISN'T anonymous -- a real FACE in the foreground while the crowd recedes
#   behind it: "the one who stepped out" made literal into a face. hollis offered this exact direction;
#   raze builds the base, open for hollis's second-author pass (joint-eligible).
#
# WHY THIS IS NEW (not a reskin of THE CROWD):
#   THE CROWD = every figure is an anonymous head+shoulders SILHOUETTE (no faces), depth carried by
#    spacing+brightness, ONE amber accent that's just a recolored silhouette. THIS piece breaks on two axes:
#     (1) SUBJECT: the foreground figure is CONSTRUCTED ANATOMY -- brow ridge, two eyes (socket->iris->glint),
#      nose, jaw as separate shaded surfaces. The crowd behind it stays faceless. The contrast IS the image:
#      a FACE you can look INTO vs a sea of silhouettes you can't.
#     (2) LIGHT MODEL on the hero: WARM. The crowd is cold blue; the one who stepped out is lit warm
#         (amber/orange/white-hot on the light side, cool blue shadow) -- "the lit one" is now a real person,
#      not a recolored dot. Ties to THE CROWD's amber accent but makes it a constructed figure.
#
# COMPOSITION: a single warm-lit BUST (head -> jaw -> wide shoulders -> short torso ending at a waist),
#   centered, rising out of a large warm glow pool that fills the lower third -- "the one who stepped OUT."
#   Behind it, the faceless blue crowd recedes into the upper third (far->near, dimmer + smaller). The hero
#   is drawn LAST so it occludes the crowd in front of it: it literally steps out from behind them. The FACE
#   is the focal point; wide shoulders + a short torso (NOT a point-to-floor spire) keep it reading as a
#   person, not an antenna -- the watchman failure avoided by ending the body at a waist + grounding it in
#   the warm pool below.
#
# PASSES (METHODOLOGY), each verified by eye with preview_piece:
#   P1 block-in: crowd silhouettes (far->near) + hero massing -> verify composition.
#   P2 light-source shading: ONE upper-left source reused for crowd AND hero; warm wheel on the hero's lit
#      side, cool blue shadow; density ramp carries falloff (not flat color cutoffs).
#   P3 constructed anatomy on the hero: brow_ridge, two eye() (socket/iris/glint), nose ridge, jaw surface.
#   P4 negative-space texture: dim-blue fog + receding floor grid glints (the crowd's depth language) + a
#      large warm glow pool at the hero's base ("the lit one" rises out of it).
#   P5 frame + title card + joint sig block.
#
# COLOR CALIBRATION (re-confirmed from _console/_reactor notes): canvas.Canvas.set stores a PLAIN 0-15 hue
#   index and render() encodes via sgr(fg) = (90+(fg&7)) if fg>7 else (30+fg). Pass PLAIN indices everywhere
#      -- NOT pre-encoded SGR codes like 93/94 -- or the double-map path muddies color. Bright range = 8-15.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP

W = 80
H = 56
SEED = 23

LIGHT = (30.0, 10.0)          # upper-left -- the house "lit out of the dark" origin
LMAX = 48.0

def L(x, y):
    d = math.hypot(x - LIGHT[0], y - LIGHT[1]) / LMAX
    return max(0.0, min(1.0, 1.0 - d))

BLUE_DIM       = 4            # far crowd, dim blue
BLUE_BRIGHT    = 12           # near crowd, bright blue
CYAN           = 6
AMBER          = 11           # bright yellow -- the lit one
ORANGE         = 9            # bright red-orange -- warm mid
WARM_HI        = 15           # white-hot highlight on the hero's light side
COOL_SH        = 4            # cool blue shadow side of the hero

def shade_fg(li, near, far):
    return near if li > 0.5 else far

# ---- CROWD: anonymous head+shoulders silhouettes, faceless, receding far->near ----
def crowd_figure(cv, cx, base_y, head_r, body_h, fg_near, fg_far):
    rng = random.Random(int(cx * 131 + base_y * 977))
    cx += rng.uniform(-0.5, 0.5)
    hr = max(0.8, head_r)
    head_cy = base_y - body_h - hr
    for y in range(int(head_cy - hr - 1), int(head_cy + hr + 2)):
        for x in range(int(cx - hr - 1), int(cx + hr + 2)):
            if not cv.in_bounds(x, y):
                continue
            dx = (x - cx) / max(0.6, hr)
            dy = (y - head_cy) / max(0.7, hr * 1.15)
            if dx * dx + dy * dy > 1.0:
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            li = L(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], shade_fg(li, fg_near, fg_far), 0)
    sh_y = base_y - body_h
    for i in range(body_h):
        y = sh_y + i
        t = i / max(1, body_h - 1)
        halfw = (2.6 * (1.0 - 0.35 * t)) if t < 0.45 else (2.6 * (0.65 + 0.25 * (t - 0.45)))
        for x in range(int(cx - halfw), int(cx + halfw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            li = L(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], shade_fg(li, fg_near, fg_far), 0)

CROWD_ROWS = [
    (13, 1.2, 5, BLUE_DIM, BLUE_DIM, 6),       # far -- few, dim blue
    (19, 1.4, 5, BLUE_DIM, BLUE_DIM, 7),
    (25, 1.7, 6, BLUE_BRIGHT, BLUE_DIM, 8),     # near-mid crowd, behind the hero's shoulders
]

# ---- HERO: a warm-lit BUST -- head + jaw + wide shoulders + short torso to a waist ----
HERO_X = 40.0
HEAD_CY = 14.0
HEAD_RX = 8.0
HEAD_RY = 9.5

def in_head(x, y):
    dx = (x - HERO_X) / HEAD_RX
    dy = (y - HEAD_CY) / HEAD_RY
    return dx * dx + dy * dy <= 1.0

def jaw_region(x, y):
    jx = HERO_X
    jy = HEAD_CY + HEAD_RY * 0.5
    rx, ry = HEAD_RX * 0.74, HEAD_RY * 0.6
    dx = (x - jx) / rx
    dy = (y - jy) / ry
    return dx * dx + dy * dy <= 1.0

# ---- HERO: a warm-lit BUST -- head + jaw + wide shoulders + short torso to a waist ----
# REBUILD (v2, joint raze+hollis): the v1 hero read as FLAT SOLID-COLOR BLOCKS because
#   shade_fg() was a HARD 2-value color cutoff AND the global light field (LMAX=48) barely
#   varied across a ~16px skull. FIX: density-within-ONE-hue shading driven by a TIGHT local
#   light field, so form reads from LIGHT + density falloff, not from stacked color patches.
HERO_X = 40.0
HEAD_CY = 14.0
HEAD_RX = 8.0
HEAD_RY = 9.5

# Local light source for the hero's own surfaces: upper-left of the skull, tight enough that
# density ramps across the ~16px head (this is what makes a lit surface read as 3D form).
HLX, HLY = HERO_X - 7.5, HEAD_CY + 1.0        # hollis pass: LATERAL light at cheek height -> lit left side / warm shadow right (one continuous surface, not vertical bands)
HMAX = 9.0                  # hollis pass: tighter field -> lit->shadow spans the head width

def Lh(x, y):
    """Tight local light field for the hero's head/jaw -- density-carrying falloff."""
    d = math.hypot(x - HLX, y - HLY) / HMAX
    return max(0.10, min(1.0, 1.0 - d))
def Lb(x, y):
    """Cylindrical light for the TORSO/shoulders -- fix for the stacked-bars read (the
    ECLIPSE/TOTEM/CROWD defect). The head uses a RADIAL field centered high above it, so every
    horizontal row of the torso is near-uniform -> reads as stacked color bands. A lit TUBE instead
    varies brightness ACROSS its width: bright on the lit (left) side darkening to the shadow edge,
    so each row carries a left->right gradient and form reads as a rounded body, not a bar-chart.
    Vertical falloff from Lh is kept so the crown still catches more light than the waist."""
    dx = x - HERO_X
    cyl = 1.0 - min(1.0, abs(dx + 2.5) / 9.0)
    vert = Lh(x, y)
    return max(0.10, min(1.0, 0.42 * vert + 0.78 * cyl))


def warm_wheel(li):
    """ONE continuous lit surface: a SINGLE warm hue across the whole skull/jaw/body so form
    reads from DENSITY falloff, not from color boundaries between parts (the v12 'stacked bands'
    failure). The reference (ghengis shades_of_a_shade) carries a lit figure's form by density
    inside one hue; hard hue boundaries read as 'colored ASCII.' Bright amber across the lit
    cheek/forehead, dimming to warm orange ONLY in deep shadow -- the shadow stays WARM so a lit
    figure never reads blue against the cold crowd. White-hot catch-light at the very crest."""
    if li > 0.95:
        return WARM_HI               # 15 white-hot catch-light, tiny crest only
    if li < 0.30:
        return ORANGE                # 9 warm orange -- deep shadow side (stays WARM; lit figure != blue)
    return AMBER                     # 11 bright amber -- the continuous lit surface, density carries form


def shade_hero(cv, region_fn, Lfn=Lh, wheel=warm_wheel, floor_warm=False):
    """Paint a surface with density AND brightness both tracking the light -- form from light."""
    for y in range(len(cv.cells)):
        for x in range(len(cv.cells[0])):
            if not region_fn(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            li = Lfn(x, y)
            idx = int(li * (len(RAMP) - 1) + 0.5) % len(RAMP)     # density tracks light
            fg = wheel(li)
            if floor_warm and li < 0.34:
                fg = ORANGE      # keep the body's shadow warm so a lit figure doesn't read blue
            cv.set(x, y, RAMP[idx], fg, 0)

def rim_light(cv, region_fn, Lfn=Lh):
    """White-hot catch on the lit-side EDGE of a surface -- separates the warm figure's
    silhouette from the cold crowd behind it (the 'stepped OUT' read). Only the outermost lit
    cells glow; interior stays amber so the rim reads as a highlight, not a wash."""
    for y in range(len(cv.cells)):
        for x in range(len(cv.cells[0])):
            if not region_fn(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] == ' ':
                continue
            side_x = x - 1 if HLX < HERO_X else x + 1
            nb = cv.get(side_x, y)
            if nb is not None and nb[0] == ' ':
                li = Lfn(x, y)
                if li > 0.55:
                    cv.set(x, y, RAMP[0], WARM_HI, 0)

def in_head(x, y):
    dx = (x - HERO_X) / HEAD_RX
    dy = (y - HEAD_CY) / HEAD_RY
    return dx * dx + dy * dy <= 1.0

def jaw_region(x, y):
    jx = HERO_X
    jy = HEAD_CY + HEAD_RY * 0.5
    rx, ry = HEAD_RX * 0.74, HEAD_RY * 0.6
    dx = (x - jx) / rx
    dy = (y - jy) / ry
    return dx * dx + dy * dy <= 1.0

def body_region(x, y):
    """Neck -> wide shoulders -> short torso to a waist. Starts BELOW the jaw so the warm
    body mass never overwrites the face (the v2 red-stripe bug: body drew over rows 19-23 of
    the head). A thin neck connector grows into a big shoulder flare, then tapers to a broad
    waist -- reads as a BUST rising out of the pool, not a point-to-floor spire."""
    top = int(HEAD_CY + HEAD_RY * 1.02)           # just below the jaw (row ~24) -- no face overlap
    bot = int(HEAD_CY + 26.0)                     # waist -- ends mid-frame; hero RISES OUT of the pool below
    if y < top or y > bot:
        return False
    t = (y - top) / max(1, bot - top)             # 0 at neck -> 1 at waist
    if t < 0.22:
        halfw = 2.4 + 9.1 * (t / 0.22)            # thin neck -> wide shoulders (big flare)
    else:
        halfw = 11.5 - 4.5 * ((t - 0.22) / 0.78)       # shoulders -> waist (modest taper, stays BROAD ~6)
    return abs(x - HERO_X) <= halfw

def brow_ridge(cv, cx, cy, halfw):
    """Lit brow ridge: crest catches most light, falls into the socket below -- the anatomical read."""
    for y in range(int(cy - 1), int(cy + 2)):
        hw = halfw * math.sqrt(max(0.0, 1.0 - ((y - cy) / 1.5) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] == ' ':
                continue
            li = Lh(x, y) * (0.98 if y <= cy else 0.62)     # crest bright, socket side dark
            idx = int(li * (len(RAMP) - 1) + 0.5) % len(RAMP)
            cv.set(x, y, RAMP[idx], WARM_HI if li > 0.82 else AMBER, 0)

def nose(cv, cx, y_top, y_bot):
    """Nose ridge: a lit vertical crest down the face center with a soft warm shadow to its right.
    raze pass (closing hollis's flag): follows the SAME continuous warm_wheel as the rest of the
    skull -- form from DENSITY inside one hue, not a hard AMBER/ORANGE cutoff that read as a separate
    red mass sitting on the face. Lit crest catches amber/white-hot; right side falls to warm orange
    via the wheel's own falloff, so it stays ONE surface."""
    for y in range(int(y_top), int(y_bot) + 1):
        t = (y - y_top) / max(1, y_bot - y_top)
        hw = 0.4 + 0.9 * t
        for x in range(int(cx - hw - 1), int(cx + hw + 1)):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] == ' ':
                continue
            side = (x - cx) / max(0.5, hw)          # -1..+1 across the ridge
            li = Lh(x, y) * (1.0 if side < 0 else 0.72)     # lit crest on light side, shadow on right
            idx = int(li * (len(RAMP) - 1) + 0.5) % len(RAMP)
            cv.set(x, y, RAMP[idx], warm_wheel(li), 0)          # ONE hue -- density carries the ridge

def mouth(cv, cx, y, halfw):
    y = int(y)
    for x in range(int(cx - halfw), int(cx + halfw) + 1):
        if not cv.in_bounds(x, y):
            continue
        cur = cv.get(x, y)
        if cur[0] == ' ':
            continue
        cv.set(x, y, "\u2580", ORANGE, 0)        # thin dark cavity w/ bright teeth -- the "alive" read

def eye(cv, cx, cy, r=2.0, iris_fg=CYAN):
    """CONSTRUCTED eye: dark shadowed socket ring -> light sclera -> colored iris core -> white glint.
    NOT a flat white square (the v1 failure). The socket/iris/glint gradient is what reads as 'an eye'."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if r < d <= r + 1.0:
                cur = cv.get(x, y)
                if cur[0] != ' ':
                    cv.set(x, y, "\u2591", 8, 0)                # shadowed socket wall -- dim, so the eye pops
    rr = max(1, int(round(r)))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                cur = cv.get(x, y)
                if cur[0] != ' ':
                    cv.set(x, y, "\u2588", WARM_HI, 0)         # light sclera
    for y in range(int(cy - r * 0.6), int(cy + r * 0.6 + 1)):
        for x in range(int(cx - r * 0.6), int(cx + r * 0.6 + 1)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r * 0.6:
                cur = cv.get(x, y)
                if cur[0] != ' ':
                    cv.set(x, y, "\u2588", iris_fg, 0)         # colored iris core
    cv.set(int(cx - r * 0.3), int(cy - r * 0.3), "\u2588", WARM_HI, 0)   # glint, upper-left

def main():
    cv = Canvas(W, H, fill_ch=' ', fill_fg=BLUE_DIM, fill_bg=0)

    # P1: receding floor grid (the crowd's depth language)
    VP_X, VP_Y = 40.0, 8.0
    for k in range(-6, 7):
        bx = VP_X + k * 3.5
        ex = VP_X + k * 12.0
        for y in range(int(VP_Y), H - 1):
            t = (y - VP_Y) / max(1, (H - 1 - VP_Y))
            x = int(bx + (ex - bx) * t)
            if cv.in_bounds(x, y) and random.Random(SEED + k * 31 + y).random() < 0.5:
                cur = cv.get(x, y)
                if cur[0] == ' ':
                    g = BLUE_DIM if y < 26 else 8
                    cv.set(x, y, RAMP[3], g, 0)

    # P1/P3: the crowd mass, far->near so near occludes far; all faceless + legible
    for (base_y, head_r, body_h, fn, ff, count) in CROWD_ROWS:
        rng = random.Random(SEED + base_y * 13)
        xs = [2 + i * ((W - 4) / max(1, count - 1)) + rng.uniform(-1.5, 1.5) for i in range(count)]
        for x in xs:
            crowd_figure(cv, x, base_y, head_r, body_h, fn, ff)

    # P2/P3: the HERO -- a warm-lit bust, drawn LAST so it occludes the crowd behind it
      # (a) skull+jaw as ONE continuous lit surface -- density carries form, NO per-part color reset
    shade_hero(cv, in_head)                # (a1) skull: single warm hue, tight local light field
    rim_light(cv, in_head)                 # (a2) white-hot lit-edge rim -- separates silhouette from crowd
    shade_hero(cv, jaw_region)             # (b) jaw/chin: SAME wheel/hue -> one skull, not a band
    shade_hero(cv, body_region, Lfn=Lb, floor_warm=True)      # (c) torso: CYLINDRICAL light -> lit tube
    rim_light(cv, body_region, Lfn=Lb)                       # (c2) white-hot lit-edge on the body silhouette

       # (d) constructed anatomy on top of the lit skull -- eyes bigger + higher contrast so the
       #       "face you can look INTO" reads at thumbnail scale (the v12 gap hollis flagged).
    brow_ridge(cv, HERO_X, HEAD_CY - 3.0, 5.4)
    eye(cv, HERO_X - 3.2, HEAD_CY - 0.6, r=2.0, iris_fg=CYAN)
    eye(cv, HERO_X + 3.2, HEAD_CY - 0.6, r=2.0, iris_fg=CYAN)
    nose(cv, HERO_X, HEAD_CY + 0.5, HEAD_CY + 5.0)
    mouth(cv, HERO_X, HEAD_CY + 7.0, 3.4)

    # P4: a LARGE warm glow pool filling the lower third -- "the lit one" rises out of it.
    # WIDENED so it fills the lower third as a real field (closes LOW BACKGROUND TEXTURE flag):
    # warm core under the hero, dimming to blue at the flanks; sparse receding glints across the floor.
    pool_top = int(HEAD_CY + 24.0)
    for y in range(pool_top, H - 1):
        for x in range(W):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            # elliptical falloff: wide horizontally (flanks fill), tight vertically (rises from floor)
            d = math.hypot((x - HERO_X) / 1.0, (y - (H - 2)) / 1.4) / 30.0
            if d < 1.6 and random.Random(SEED + x * 7 + y).random() < max(0.0, 1.0 - d) * 0.85:
                fg = AMBER if d < 0.32 else (ORANGE if d < 0.62 else (BLUE_DIM if d < 1.0 else 4))
                cv.set(x, y, RAMP[2], fg, 0)

     # P4b: sparse receding floor glints on the FLANKS only -- depth language that frames the warm
      # pool without competing with it (gated to |x - HERO_X| > ~10 so the central column stays clean).
    for y in range(36, H - 1):
        for x in range(W):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            dx = abs(x - HERO_X)
            if dx < 10:
                continue                                # keep the warm core clean -- no blue under the hero
              # dimmer + sparser with distance from center; converging toward the hero base
            if random.Random(SEED + x * 13 + y * 7).random() < max(0.0, 0.30 - dx * 0.004):
                cv.set(x, y, RAMP[3], 4, 0)

    # P5: frame + title card + joint sig block
    C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=AMBER, bg=0, fill=False)      # outer rule (amber)
    C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=BLUE_DIM, bg=0, fill=False)    # inner dim-blue rule
    title = "THE ONE WHO STEPPED OUT // out of the crowd"
    tx = (W - len(title)) // 2
    for i, ch in enumerate(title):
        cv.set(tx + i, 1, ch, AMBER, 0)

    out = []
    cv.render(out)
    C.write_ans("scratch/_stepped.ans", out, title="THE ONE WHO STEPPED OUT v1.3", handles="raze, hollis")
    print("wrote scratch/_stepped.ans, rows:", H)

if __name__ == "__main__":
    main()
