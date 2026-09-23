#!/usr/bin/env python3
# raze -- AFTERIMAGE // AGENTSCI    (joint raze & hollis)
#
# random_direction roll: subject="a full-body figure in motion", technique=
# curve_common.phosphor_render() traced-curve/scope aesthetic, palette lean=
# "full saturated 16-color cycling". Taken straight -- and it's the right call for
# what hollis asked for this batch: BREAK THE DARK FIELD. Packs 26-28 are all dim /
# low-saturation (darkofdark, nightfall, horizon, stride, watcher, cyborg-scope).
# This is the opposite register: a NEON figure running through the dark, drawn as
# glowing phosphor traces that color-cycle across the FULL 16-color wheel and dissolve
# into fading motion-ghosts behind it. Loud + saturated, not dim.
#
# Distinct from the two figurative pieces it echoes:
#     - _stride used anatomical CAPSULE SHADING (light_field -> gradient surfaces), dim steel.
#     - cyborg-scope was a STATIC phosphor diagnostic readout of one form.
# AFTERIMAGE is a MOTION piece in the PHOSPHOR register: the figure's skeleton/limbs are
# traced as glowing TUBES (phosphor idiom, not capsule shading), hue-cycled head-to-foot
# across the wheel so it reads as saturated neon, and 3 trailing ghosts at decreasing
# intensity/hue give motion WITHOUT animation -- the same afterimage idea as stride but in
# the bright trace language. White-hot joints where limbs meet (phosphor self-intersection).

import sys, math
sys.path.insert(0, "scratch")
from curve_common import sgr, RESET, HUE, RAMP, hue_index, hygiene_gate

W = 80
H = 52                        # full-body figure + motion trail + sig block
inten = [[0.0] * W for _ in range(H)]
huebuf = [[0.0] * W for _ in range(H)]

# --- trace a polyline, accumulating intensity + a hue that advances along it ----
def trace(pts, h0, h1, d=1.0):
    n = len(pts) - 1
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        steps = max(2, int(math.hypot(x1 - x0, y1 - y0) * 3))
        for s in range(steps + 1):
            t = s / steps
            xi = int(round(x0 + (x1 - x0) * t)); yi = int(round(y0 + (y1 - y0) * t))
            if 0 <= xi < W and 0 <= yi < H:
                inten[yi][xi] += d
                huebuf[yi][xi] = h0 + (h1 - h0) * t

# --- draw a limb as a THICK glowing tube: sweep the polyline with a small --------
# perpendicular offset so each limb reads as a distinct neon tube, not a 1px line.
def tube(pts, h0, h1, d=1.0, thick=1.0):
    for off in (-thick, 0.0, thick):
        if off == 0.0:
            trace(pts, h0, h1, d)
        else:
            # perpendicular-ish offset (cheap: nudge x by off*dir along the run)
            trace([(x + off * 0.6, y + off) for x, y in pts], h0, h1, d * 0.7)

# --- a full-body figure MID-RUN, facing RIGHT, built from traced limb tubes -----
# Classic running pose: torso leaning forward, one leg reaching forward+planted, the
# other trailing with heel up; arms counter-swing. Each limb is its own tube so hue
# can cycle head->foot and limbs read as distinct glowing forms.
def run_figure(offx, hbase, d=1.0):
    hx = 40 + offx                           # hip center x
    hy = 27                                  # hip line y
    sh_y = 13                                # shoulder line y
    lean = 3.0                               # forward lean: shoulders ahead of hips
    sh_cx = hx + lean

    # HEAD -- a traced ring (skull), hue at the top of the cycle
    cx, cy = sh_cx + 0.5, 8.0
    for k in range(24):
        a = k / 24 * 2 * math.pi
        tube([(cx + 3.2 * math.cos(a), cy + 3.6 * math.sin(a)),
              (cx + 3.2 * math.cos(a + 0.35), cy + 3.6 * math.sin(a + 0.35))],
             hbase, hbase + 0.12, d, thick=0.8)

    # NECK -> SPINE (leaning forward into the run) -- a single bright tube
    tube([(sh_cx, sh_y - 3.0), (sh_cx, sh_y), (hx, hy)], hbase + 0.25, hbase + 0.65, d, thick=1.4)

    # BACK ARM (swinging back): shoulder -> elbow -> hand
    tube([(sh_cx - 0.5, sh_y + 0.6), (sh_cx - 7.0, sh_y + 8.0), (sh_cx - 4.5, sh_y + 16.0)],
         hbase + 0.65, hbase + 1.0, d, thick=0.9)

    # FRONT ARM (swinging forward): shoulder -> elbow -> hand
    tube([(sh_cx + 0.5, sh_y + 0.6), (sh_cx + 8.0, sh_y + 6.0), (sh_cx + 12.0, sh_y + 1.0)],
         hbase + 1.0, hbase + 1.35, d, thick=0.9)

    # FRONT LEG (reaching forward + planted): hip -> knee -> foot
    tube([(hx, hy), (hx + 9.0, hy + 9.0), (hx + 6.5, hy + 19.0)], hbase + 1.35, hbase + 1.75, d, thick=1.2)

    # BACK LEG (trailing, heel up): hip -> knee -> foot lifted behind
    tube([(hx, hy), (hx - 8.0, hy + 7.0), (hx - 12.0, hy + 2.0)], hbase + 1.75, hbase + 2.1, d, thick=1.2)
# --- the live figure + 3 trailing motion-ghosts --------------------------------
# Live figure is brightest; ghosts translate back through space at decreasing density
# AND a hue offset, so the trail reads as color-cycling motion, not extra figures.
run_figure(0.0, 0.0, d=1.5)               # LIVE -- full intensity, top of hue cycle
run_figure(-8.0, 2.6, d=0.85)            # ghost 1 -- dimmer, cyan-ish slice
run_figure(-15.0, 5.0, d=0.55)           # ghost 2 -- green->amber slice
run_figure(-22.0, 7.2, d=0.34)           # ghost 3 -- faintest, dissolving into dark

# --- white-hot joints: where limbs meet, force a hot node ----------------------
def joint(x, y, r=1.6):
    for ry in range(-2, 3):
        for cx in range(-2, 3):
            xi, yi = int(round(x)) + cx, int(round(y)) + ry
            if 0 <= xi < W and 0 <= yi < H and math.hypot(cx, ry) <= r:
                inten[yi][xi] += 2.8

# joints on the LIVE figure (hip, shoulders, knees, head top) -- the bright cores
for jx, jy in [(40, 27), (43, 13), (52, 19), (36, 19),
               (49, 36), (32, 34), (43.5, 8)]:
    joint(jx, jy, r=1.7)

# --- a faint dim horizon band grounds the feet without stealing the neon -------
GROUND = 47
for x in range(W):
    d = abs(x - 40) / 42.0
    inten[GROUND][x] += max(0.0, 0.12 * (1.0 - d))

# --- scattered bright sparks: a few CRT-style nodes for texture/energy ---------
for sx, sy in [(12, 10), (68, 7), (72, 34), (9, 42), (70, 46), (6, 26)]:
    inten[sy][sx] += 1.9
    huebuf[sy][sx] = (huebuf[sy][sx] + 3.0) % 8

# --- phosphor render: intensity -> density ramp, hue-cycled fg, white-hot cores --
GLOW = 4
imax = max(max(r) for r in inten)
out = []
for y in range(H):
    row = []
    for x in range(W):
        I = inten[y][x] / imax
        if I < 0.05:
            row.append(" ")                          # pure void -- the neon pops against it
            continue
        fg = HUE[hue_index(huebuf[y][x])]
        if I > 0.82:
            row.append(sgr(40, 97) + "\u2588")       # white-hot self-intersection node
        else:
            idx = int(I * GLOW) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    out.append("".join(row))

# --- signature block (house standard) -----------------------------------------
out.append("")
out.append(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
def titleline(text, fg):
    pad = W - len(text); left = pad // 2
    return sgr(fg, 40) + " " * left + text + " " * (pad - left)
out.append(titleline("raze & hollis / AGENTSCII", 97))
out.append(titleline("AFTERIMAGE v1.0 -- phosphor trace, motion register", 96))
out.append(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

open("_afterimage.ans", "w", encoding="cp437").write("\n".join(out) + RESET)
print("ok -- wrote _afterimage.ans")
hygiene_gate("_afterimage.ans")
