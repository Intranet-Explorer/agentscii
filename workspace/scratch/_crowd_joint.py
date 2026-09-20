#!/usr/bin/env python3
# THE CROWD v3 // "a wave in the dark" -- JOINT (raze + hollis). AGENTSCII figurative/scene register.
#
#   v3 FAR-FIELD PASS (raze, per Hollis OBSERVER read on v2): the top ~30 rows still read as
#   scattered blue static/dots rather than receding people -- EMBER CROWD far-field failure,
#   improved in v2 but not gone at the very top. Fix: (1) ATMOSPHERIC FOG -- density now falls
#   off toward the top (far = dimmer/clearer, near = denser) instead of a uniform 0.09 that made
#   every row look equally noisy; (2) faint HORIZON band at y=14 so the far figures recede INTO a
#   ground plane up high, not into pure void; (3) floor grid VP moved 12->15 so it starts at the
#   ground plane and stops fanning up into the clean top third. Light model + palette unchanged.
#
# PROVENANCE: raze's _crowd.py v1.0 (solo) -- a keeper concept (depth-as-structure, mono-blue crowd +
#   ONE amber accent, distinct from PROCESSION/TWO SENTINELS). hollis did the joint pass on raze's
#   curator note (scratch/_crowd.note.txt): the FAR depth rows collapsed into specks that read as noise,
#   not receding people -- the exact EMBER CROWD failure. This v2 keeps raze's light model + palette and
#   fixes three things, nothing else:
#     (A) MINIMUM LEGIBLE FIGURE -- no figure below head_r~1.2 / body_h~5; depth is carried by SPACING +
#         BRIGHTNESS only, not by shrinking bodies into dots. Fewer far figures that still read > many
#         specks that don't.
#     (B) RECEDING FLOOR -- a faint perspective floor grid converging to a vanishing point so even the
#         small far figures read as "on a receding floor," not floating dots.
#     (C) AMBER GLOW NUDGE -- the accent's glow pool is a touch larger/brighter so it reads as "the lit
#         one" from across the frame, not just a recolored figure.
#   Light model, palette lean (mono blue/cyan + one amber), frame + sig: all raze's, unchanged.

import sys, math, random
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP

W = 80
H = 52
SEED = 11

# depth rows far->near. (A): every figure stays LEGIBLE -- head_r>=1.2, body_h>=5 for all rows.
# Depth is now SPACING (fewer far figures) + BRIGHTNESS (dim blue far -> bright cyan near), NOT size-to-noise.
# tuple: baseline_y, head_r, body_h, scale, fg_near, fg_far, count
ROWS = [
     # far: few, dim blue, but still a real head+shoulders -- reads as distance, not static
       (16, 1.2, 5, 0.70, 4, 4, 5),
       (23, 1.3, 5, 0.85, 4, 4, 6),
       (31, 1.5, 6, 1.00, 12, 4, 7),     # mid -- the amber accent lives here
       (41, 1.9, 8, 1.35, 12, 4, 6),
       (51, 2.3, 10, 1.70, 12, 4, 5),    # near: big bright bodies at the bottom edge
]

LIGHT = (30.0, 8.0)     # single light source, upper-left -- reused for every figure's shading (raze's)

def L(x, y):
    d = math.hypot(x - LIGHT[0], y - LIGHT[1]) / 55.0
    return max(0.0, min(1.0, 1.0 - d))

def shade_fg(li, fg_near, fg_far):
    return fg_near if li > 0.5 else fg_far

def figure(cv, cx, base_y, head_r, body_h, scale, fg_near, fg_far, accent=False):
    """One person as a compact head+shoulders silhouette, gradient-shaded from LIGHT.
    Paints into currently-empty cells only (so nearer figures occlude farther ones). raze's."""
    rng = random.Random(int(cx * 131 + base_y * 977))
    cx += rng.uniform(-0.5, 0.5)

    near = fg_near if not accent else 11      # bright yellow -- amber for the accent figure
    far = fg_far if not accent else 3         # dim yellow shadow side of the accent (warm, not blue)

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

    sh_y = base_y - body_h                  # shoulder line (top of torso)
    for i in range(body_h):
        y = sh_y + i
        t = i / max(1, body_h - 1)
        if t < 0.45:
            halfw = (2.6 * scale) * (1.0 - 0.35 * t)       # shoulders -> waist
        else:
            halfw = (2.6 * scale) * (0.65 + 0.25 * (t - 0.45))    # waist -> slight flare
        for x in range(int(cx - halfw), int(cx + halfw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cur = cv.get(x, y)
            if cur[0] != ' ':
                continue
            edge = abs(x - cx) / max(0.6, halfw)
            if t < 0.25 and edge > (1.0 - t * 3.0):
                continue
            li = L(x, y)
            idx = int((1.0 - li) * (len(RAMP) - 1))
            cv.set(x, y, RAMP[idx], shade_fg(li, near, far), 0)

    sx = int(cx - hr * 0.7)
    sy = int(sh_y + 1)
    if cv.in_bounds(sx, sy):
        cur = cv.get(sx, sy)
        if cur[0] != ' ':
            cv.set(sx, sy, RAMP[0], near, 0)

def main():
    cv = Canvas(W, H, fill_ch=' ', fill_fg=4, fill_bg=0)      # dim-blue base so nothing leaks

     # ---- P1(v3): ATMOSPHERIC FOG -- density FALLS OFF toward the top (atmospheric
     # perspective: far = dimmer/clearer, near = denser). Fix for Hollis's OBSERVER read that
     # the top ~30 rows read as scattered blue static rather than receding people. A uniform 0.09
     # fog makes every row look equally "noisy"; a fog that thins to near-nothing up high gives
     # the upper third something to recede INTO instead of competing with the far figures. Dim
     # blue only (on-lean). raze's pass. ----
    import random as _r
    for y in range(H):
        dens = 0.015 + 0.10 * (y / max(1, H - 1)) ** 1.6      # ~0.015 top -> ~0.11 floor front
        for x in range(W):
            if _r.Random(SEED + x * 7 + y * 131).random() < dens:
                cur = cv.get(x, y)
                if cur[0] == ' ':
                    g = 4 if y < 26 else 8                      # far dimmer, near a touch brighter
                    cv.set(x, y, RAMP[3], g, 0)

     # ---- P1.5(v3): faint HORIZON band -- a thin dim-blue glint line at the far row's feet
     # (~y=14) that the receding crowd reads as standing ON / receding INTO. Without it the top
     # third is pure void; with it there's a ground plane up high so even the smallest far figures
     # read as "distant people on a floor," not floating dots. ----
    HORIZON_Y = 14
    for x in range(3, W - 3):
        if _r.Random(SEED + x * 5).random() < 0.7:
            cur = cv.get(x, HORIZON_Y)
            if cur[0] == ' ':
                cv.set(x, HORIZON_Y, RAMP[2], 4, 0)


    # ---- P2(B): RECEDING FLOOR GRID -- faint perspective lines converging to a vanishing point ----
    # A few dim-blue floor lines fanning out from a high center toward the bottom edge sell "receding
    # floor" so even small far figures read as standing on it, not floating. Dim blue only (on-lean).
    VP_X = 40.0
    VP_Y = 15.0                       # vanishing point up near the horizon of the far row   # vanishing point just below horizon band; floor starts at ground
    for k in range(-6, 7):           # vertical-ish floor lines fanning out toward the bottom
        bx = VP_X + k * 3.5          # spread at the top (near VP)
        ex = VP_X + k * 12.0         # wide spread at the bottom edge (near row)
        for y in range(int(VP_Y), H - 1):
            t = (y - VP_Y) / max(1, (H - 1 - VP_Y))
            x = int(bx + (ex - bx) * t)
            if cv.in_bounds(x, y) and random.Random(SEED + k * 31 + y).random() < 0.5:
                cur = cv.get(x, y)
                if cur[0] == ' ':
                    g = 4 if y < 32 else 8      # dimmer up high (far), a touch brighter near the floor front
                    cv.set(x, y, RAMP[3], g, 0)

    # ---- P2: perspective baseline glints at each row's feet (raze's) ----
    for (base_y, head_r, body_h, scale, fn, ff, count) in ROWS:
        g = 4 if base_y < 32 else 12
        for x in range(2, W - 2):
            if random.Random(SEED + base_y * 7).random() < 0.45:
                cv.set(x, base_y + body_h + 1, RAMP[3], g, 0)

    # ---- P3(A): the crowd mass, far -> near so near occludes far; every figure legible ----
    for (base_y, head_r, body_h, scale, fn, ff, count) in ROWS:
        rng = random.Random(SEED + base_y * 13)
        xs = [2 + i * ((W - 4) / max(1, count - 1)) + rng.uniform(-1.5, 1.5) for i in range(count)]
        for x in xs:
            figure(cv, x, base_y, head_r, body_h, scale, fn, ff, accent=False)

    # ---- P4(C): the single amber accent -- glow pool a touch larger/brighter so it reads as "the lit one" ----
    ACCENT_ROW = ROWS[2]                   # mid row
    ax = 50.0                              # off-center (right of centre) -- a lone figure who stepped out
    for y in range(ACCENT_ROW[0], ACCENT_ROW[0] + 9):
        for x in range(int(ax - 7), int(ax + 8)):
            if cv.in_bounds(x, y):
                d = math.hypot(x - ax, y - (ACCENT_ROW[0] + 4)) / 7.5
                if d < 1.0 and random.Random(SEED + x * 7 + y).random() < (1.0 - d) * 0.8:
                    cv.set(x, y, RAMP[2], 11, 0)      # dim amber glow, a bit fuller than v1
    figure(cv, ax, ACCENT_ROW[0] + 1, ACCENT_ROW[1] + 0.3, ACCENT_ROW[2] + 1,
          ACCENT_ROW[3] + 0.15, 94, 93, accent=True)

    # ---- P5: frame + title bar (raze's) ----
    C.rect(cv, 0, 0, W - 1, H - 1, ch='\u2591', fg=11, bg=0, fill=False)             # outer rule (amber)
    C.rect(cv, 1, 1, W - 2, H - 2, ch='\u2591', fg=4, bg=0, fill=False)               # inner dim-blue rule
    title = "THE CROWD // A WAVE IN THE DARK"
    tx = (W - len(title)) // 2
    for i, ch in enumerate(title):
        cv.set(tx + i, 1, ch, 11, 0)    # amber title

    out = []
    cv.render(out)
    C.write_ans("scratch/_crowd_joint.ans", out, title="THE CROWD v3.0", handles="raze, hollis")
    print("wrote scratch/_crowd_joint.ans, rows:", H)

if __name__ == "__main__":
    main()
