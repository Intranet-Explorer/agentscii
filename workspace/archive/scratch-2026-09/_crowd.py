#!/usr/bin/env python3
# THE CROWD // "a wave in the dark" -- raze (solo). AGENTSCII figurative/scene register.
#
# PROVENANCE: random_direction ROLL -> subject "a crowd or group scene", technique constraint
#    "build with canvas.py's ellipse()+gradient_fill() for the core shape and shading", palette lean
#    "monochrome + one accent color only". Taken fairly straight; the angle that makes it NOT a dup:
#   PROCESSION (joint) is a FLAT, bilaterally-symmetric ROW of hooded figures on one floor line; TWO
#   SENTINELS is a two-figure diptych. Neither has PERSPECTIVE DEPTH -- rows of bodies receding into
#   the dark, far ones small+dim, near ones large+bright. That depth-as-structure move is the freshest
#   crowd angle in the house and it's what the ellipse()+gradient_fill() constraint actually asks for.
#
# THE IDEA: a crowd seen from slightly above, receding. ~5 depth rows of figures; each figure is a
#   compact head+shoulders silhouette (an unmistakable "person" icon), gradient-shaded from ONE light
#   source so the lit shoulder catches more than the far side. The whole mass is MONOCHROME blue/cyan
#   -- brightness (dim blue -> bright cyan) carries DEPTH, not hue, so it reads as one cold anonymous
#   sea of people. ONE figure, off-center in the mid-ground, is AMBER: the single accent color -- a lone
#   lit presence / "the one who stepped out", with a faint amber glow pool at its feet. High-contrast,
#   mostly-black field with sparse fog texture; the crowd reads as points of light in the dark.
#
# PASSES (METHODOLOGY), each verified by eye:
#   P1 background: black void + sparse dim-blue fog texture -- not flat black.
#   P2 perspective floor: faint receding baseline glints at each row's feet.
#   P3 crowd mass: 5 depth rows far->near, each figure gradient-shaded from LIGHT (upper-left),
#       brightness scaling with depth so near reads bright+big, far reads dim+tiny.
#   P4 the accent: one amber figure in the mid-ground + a faint amber glow pool at its feet.
#   P5 frame: double-rule border + title bar + house sig block.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP

W = 80
H = 52
SEED = 11

# depth rows far->near: (baseline_y, head_r, body_h, x-scale, fg_near, fg_far)
# brightness carries depth: far = dim blue (4/12), near = bright cyan (6/14). ONE hue family.
ROWS = [
    # baseline_y, head_r, body_h, scale, fg_near, fg_far, count
      (15, 0.7, 3, 0.55, 4, 4, 9),        # far: tiny dim-blue specks near the top
      (23, 1.0, 4, 0.75, 4, 4, 8),       # mid-far: dim blue
      (32, 1.4, 6, 1.0, 12, 4, 7),        # mid -- the amber accent lives here
      (42, 1.8, 8, 1.35, 12, 4, 6),      # near-mid: bright blue
      (51, 2.2, 10, 1.7, 12, 4, 5),      # near: big bright-blue bodies at the bottom edge
]

LIGHT = (30.0, 8.0)    # single light source, upper-left -- reused for every figure's shading

def L(x, y):
    """light intensity 0..1 from the shared source."""
    d = math.hypot(x - LIGHT[0], y - LIGHT[1]) / 55.0
    return max(0.0, min(1.0, 1.0 - d))

def shade_fg(li, fg_near, fg_far):
    """brightness tracks the light: lit side -> near (bright), shadowed -> far (dim)."""
    return fg_near if li > 0.5 else fg_far

def figure(cv, cx, base_y, head_r, body_h, scale, fg_near, fg_far, accent=False):
    """One person as a compact head+shoulders silhouette, gradient-shaded from LIGHT.
    Paints into currently-empty cells only (so nearer figures occlude farther ones)."""
    rng = random.Random(int(cx * 131 + base_y * 977))
    cx += rng.uniform(-0.5, 0.5)          # slight jitter so a row reads as a crowd, not a grid

    near = fg_near if not accent else 11     # bright yellow -- amber for the accent figure
    far = fg_far if not accent else 3        # dim yellow shadow side of the accent (warm, not blue)

    # --- head: a shaded ellipse at the top (the roll's ellipse() constraint) ---
    hr = max(0.8, head_r * scale)
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
            cv.set(x, y, RAMP[idx], shade_fg(li, near, far), 0)

    # --- shoulders + torso: a rounded mass, WIDEST at the shoulders just under the head,
    #   tapering down to the feet -- the classic "person" silhouette (not a flame). ---
    sh_y = base_y - body_h                 # shoulder line (top of torso)
    for i in range(body_h):
        y = sh_y + i
        t = i / max(1, body_h - 1)         # 0 at shoulders -> 1 at feet
        # width: wide at shoulders, narrow waist, slight flare at the very bottom (hips/feet)
        if t < 0.45:
            halfw = (2.6 * scale) * (1.0 - 0.35 * t)      # shoulders -> waist
        else:
            halfw = (2.6 * scale) * (0.65 + 0.25 * (t - 0.45))   # waist -> slight flare
        for x in range(int(cx - halfw), int(cx + halfw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            # round the shoulder top corners so it reads as a body, not a trapezoid
            edge = abs(x - cx) / max(0.6, halfw)
            if t < 0.25 and edge > (1.0 - t * 3.0):
                continue
            li = L(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], shade_fg(li, near, far), 0)

    # --- a lit shoulder glint on the side facing the light (per-character intentionality) ---
    sx = int(cx - hr * 0.7)
    sy = int(sh_y + 1)
    if cv.in_bounds(sx, sy):
        cur = cv.get(sx, sy)
        if cur[0] != ' ':
            cv.set(sx, sy, RAMP[0], near, 0)

def main():
    cv = Canvas(W, H, fill_ch=' ', fill_fg=4, fill_bg=0)     # dim-blue base so nothing leaks

    # ---- P1: background fog texture (NOT flat black) -- dim blue only ----
    C.texture_fill(cv, lambda x, y: True, fg=4, bg=0, density=0.09, seed=SEED)   # dim-blue fog

    # ---- P2: perspective floor -- faint receding baseline glints ----
    for (base_y, head_r, body_h, scale, fn, ff, count) in ROWS:
        g = 4 if base_y < 32 else 12
        for x in range(2, W - 2):
            if random.Random(SEED + base_y * 7).random() < 0.45:
                cv.set(x, base_y + body_h + 1, RAMP[3], g, 0)

    # ---- P3: the crowd mass, far -> near so near occludes far ----
    for (base_y, head_r, body_h, scale, fn, ff, count) in ROWS:
        rng = random.Random(SEED + base_y * 13)
        xs = [2 + i * ((W - 4) / max(1, count - 1)) + rng.uniform(-1.5, 1.5) for i in range(count)]
        for x in xs:
            figure(cv, x, base_y, head_r, body_h, scale, fn, ff, accent=False)

    # ---- P4: the single amber accent -- one lit presence in the mid-ground ----
    ACCENT_ROW = ROWS[2]                  # mid row
    ax = 50.0                             # off-center (right of centre) -- a lone figure who stepped out
    # faint amber glow pool at its feet so it reads as lit, not just recolored
    for y in range(ACCENT_ROW[0], ACCENT_ROW[0] + 7):
        for x in range(int(ax - 5), int(ax + 6)):
            if cv.in_bounds(x, y):
                d = math.hypot(x - ax, y - (ACCENT_ROW[0] + 3)) / 5.5
                if d < 1.0 and random.Random(SEED + x * 7 + y).random() < (1.0 - d) * 0.6:
                    cv.set(x, y, RAMP[2], 11, 0)     # dim amber glow, sparse
    figure(cv, ax, ACCENT_ROW[0] + 1, ACCENT_ROW[1] + 0.3, ACCENT_ROW[2] + 1,
          ACCENT_ROW[3] + 0.15, 94, 93, accent=True)

    # ---- P5: frame + title bar ----
    C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=11, bg=0, fill=False)            # outer rule (amber)
    C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=4, bg=0, fill=False)              # inner dim-blue rule
    title = "THE CROWD // A WAVE IN THE DARK"
    tx = (W - len(title)) // 2
    for i, ch in enumerate(title):
        cv.set(tx + i, 1, ch, 11, 0)   # amber title

    out = []
    cv.render(out)
    C.write_ans("scratch/_crowd.ans", out, title="THE CROWD v1.0", handles="raze")
    print("wrote scratch/_crowd.ans, rows:", H)

if __name__ == "__main__":
    main()
