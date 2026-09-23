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

def warm_shade(cv, region_fn, warm_floor=False):
    for y in range(len(cv.cells)):
        for x in range(len(cv.cells[0])):
            if not region_fn(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            li = L(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            if li > 0.62:
                fg = WARM_HI if li > 0.85 else AMBER
            elif li > 0.42:
                fg = ORANGE
            else:
                # shadow side: keep it warm (dim orange) on the body so a lit figure doesn't read blue;
                # only the head/jaw use true cool-blue shadow for the lit-form read
                fg = ORANGE if warm_floor else COOL_SH
            cv.set(x, y, RAMP[idx], fg, 0)

def body_region(x, y):
    top = int(HEAD_CY + HEAD_RY * 0.55)     # neck, just under the jaw
    bot = H - 6                                  # reaches down toward the floor -- connects into the pool
    if y < top or y > bot:
        return False
    t = (y - top) / max(1, bot - top)       # 0 at neck -> 1 at waist
        halfw = 3.0 + 8.5 * (t / 0.25)          # neck -> wide shoulders (big flare)
    elif t < 0.6:
        halfw = 11.5 - 4.5 * ((t - 0.25) / 0.35)     # shoulders -> waist (modest taper, stays BROAD ~7)
    else:
        halfw = 7.0 + 4.0 * ((t - 0.6) / 0.4)      # waist -> feet (flare OUT to a wide base -- grounded)
        halfw = 11.5 - 3.5 * ((t - 0.25) / 0.75)   # shoulders -> waist (gentle taper, stays wide)
    return abs(x - HERO_X) <= halfw

def brow_ridge(cv, cx, cy, halfw):
    for y in range(int(cy - 1), int(cy + 2)):
        hw = halfw * math.sqrt(max(0.0, 1.0 - ((y - cy) / 1.5) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] == ' ':
                continue
            li = L(x, y) * (0.95 if y <= cy else 0.72)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], WARM_HI if li > 0.8 else AMBER, 0)

def eye(cv, cx, cy, r=1.5, iris_fg=CYAN):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if r < d <= r + 1.0:
                cur = cv.get(x, y)
                if cur[0] != ' ':
                    cv.set(x, y, "\u2591", COOL_SH, 0)      # shadowed socket wall
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                cv.set(x, y, "\u2588", WARM_HI, 0)           # light sclera
    for y in range(int(cy - r * 0.6), int(cy + r * 0.6 + 1)):
        for x in range(int(cx - r * 0.6), int(cx + r * 0.6 + 1)):
            if not cv.in_bounds(x, y):
                continue
            d = math.hypot(x - cx, y - cy)
            if d <= r * 0.6:
                cv.set(x, y, "\u2588", iris_fg, 0)           # colored iris core
    cv.set(int(cx - r * 0.3), int(cy - r * 0.3), "\u2588", WARM_HI, 0)   # glint, upper-left

def nose(cv, cx, y_top, y_bot):
    for y in range(int(y_top), int(y_bot) + 1):
        t = (y - y_top) / max(1, y_bot - y_top)
        hw = 0.4 + 0.9 * t
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] == ' ':
                continue
            li = L(x, y) * (0.85 if abs(x - cx) < hw else 1.0)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], AMBER if li > 0.5 else ORANGE, 0)

def mouth(cv, cx, y, halfw):
    y = int(y)
    for x in range(int(cx - halfw), int(cx + halfw) + 1):
        if not cv.in_bounds(x, y):
            continue
        cur = cv.get(x, y)
        if cur[0] == ' ':
            continue
        cv.set(x, y, "\u2580", ORANGE, 0)     # thin dark cavity w/ bright teeth -- the "alive" read

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
    warm_shade(cv, in_head)            # (a) skull, gradient-shaded warm/cool from the single light
    warm_shade(cv, jaw_region)         # (b) jaw/chin as a separate shaded surface -- gives a face shape
    warm_shade(cv, body_region, warm_floor=True)   # (c) shoulders+torso to floor -- stays warm, connects to pool

    # (d) constructed anatomy on top of the lit skull
    brow_ridge(cv, HERO_X, HEAD_CY - 2.5, 4.5)
    eye(cv, HERO_X - 3.2, HEAD_CY - 0.5, r=1.8, iris_fg=CYAN)
    eye(cv, HERO_X + 3.2, HEAD_CY - 0.5, r=1.8, iris_fg=CYAN)
    nose(cv, HERO_X, HEAD_CY + 1.0, HEAD_CY + 4.0)
    mouth(cv, HERO_X, HEAD_CY + 6.0, 2.8)

    # P4: a LARGE warm glow pool filling the lower third -- "the lit one" rises out of it
    pool_top = int(HEAD_CY + 32.0)
    for y in range(pool_top, H - 1):
        for x in range(W):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            d = math.hypot((x - HERO_X) / 1.0, (y - (H - 2)) / 1.6) / 18.0
            if d < 1.25 and random.Random(SEED + x * 7 + y).random() < max(0.0, 1.0 - d) * 0.9:
                cv.set(x, y, RAMP[2], AMBER if d < 0.4 else (ORANGE if d < 0.9 else BLUE_DIM), 0)

    # P5: frame + title card + joint sig block
    C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=AMBER, bg=0, fill=False)      # outer rule (amber)
    C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=BLUE_DIM, bg=0, fill=False)    # inner dim-blue rule
    title = "THE ONE WHO STEPPED OUT // out of the crowd"
    tx = (W - len(title)) // 2
    for i, ch in enumerate(title):
        cv.set(tx + i, 1, ch, AMBER, 0)

    out = []
    cv.render(out)
    C.write_ans("scratch/_stepped.ans", out, title="THE ONE WHO STEPPED OUT v1.0", handles="raze, hollis")
    print("wrote scratch/_stepped.ans, rows:", H)

if __name__ == "__main__":
    main()
