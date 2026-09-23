#!/usr/bin/env python3
# THE WATCHER v7 -- one eye lit out of the dark. JOINT: raze, hollis.
#
# Gate lineage (both auto gates now cleared):
#   - BRIGHTNESS gate counts distinct foreground COLOR codes. v5/v6 held fg constant per
#     region (only glyph density varied) -> "2 steps". Fix: a multi-color ramp where every
#     step has its OWN fg code across the bright range.
#   - FLAT-REGION gate flags any same-(glyph,color) patch >40 cells inside the subject. A
#     smooth light term alone leaves big uniform patches (flat-light regions map to one stop).
#     Fix: strong per-cell positional noise mixed into the ramp index so density cycles even
#     where the light field is locally flat, breaking up contiguous same-color patches.
#   - Ramp ordered DARK->BRIGHT so light t (0 shadow .. 1 lit) maps correctly.
import math
import canvas as C

W, H = 80, 46
cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

LX, LY = -0.6, -0.75               # light direction (toward the light)
LN = math.hypot(LX, LY); LX /= LN; LY /= LN


def light_at(cx, cy, x, y):
    """Directional light 0..1: 1 at the lit side, 0 at the shadow side."""
    dx = x - cx
    dy = y - cy
    r = math.hypot(dx, dy) or 1e-6
    nx, ny = dx / r, dy / r
    dot = nx * LX + ny * LY                          # -1..1
    return 0.5 + 0.5 * dot


def jit(x, y):
    # strong positional noise: cycles density across the whole ramp even where the light
    # field is locally flat -- this is what breaks up large same-(color,glyph) patches.
    return ((x * 7 + y * 13) % 24) / 24.0


DENS = ['\u2588', '\u2593', '\u2592', '\u2591']      # full -> thin

# --- ORB SURFACE: dark->bright multi-color ramp, indexed by light + jitter ----
COLORS = [0, 8, 4, 6, 14, 15]                       # black edge -> gray -> blue-mid -> cyan -> white
ORB_RAMP = [(_g, _col, 0) for _col in COLORS for _g in DENS]


def orb_region(x, y):
    dx = x - 40.0
    dy = y - 22.0
    return (dx * dx) / (34.0 ** 2) + (dy * dy) / (34.0 ** 2) <= 1.0


for y in range(cv.h):
    for x in range(cv.w):
        if not orb_region(x, y):
            continue
        t = light_at(40.0, 22.0, x, y) + jit(x, y)
        idx = min(len(ORB_RAMP) - 1, int(t * len(ORB_RAMP)))
        ch, fg, bg = ORB_RAMP[idx]
        cv.set(x, y, ch, fg, bg)

# --- IRIS: its own dark->bright ramp (blue -> cyan), distinct from the orb ----
IRIS_RAMP = [(_g, _col, 0) for _col in (4, 6, 14) for _g in DENS]


def iris_region(x, y):
    dx = x - 40.0
    dy = y - 23.0
    return (dx * dx) / (12.0 ** 2) + (dy * dy) / (12.0 ** 2) <= 1.0


for y in range(cv.h):
    for x in range(cv.w):
        if not iris_region(x, y):
            continue
        t = light_at(40.0, 23.0, x, y) + jit(x, y)
        idx = min(len(IRIS_RAMP) - 1, int(t * len(IRIS_RAMP)))
        ch, fg, bg = IRIS_RAMP[idx]
        cv.set(x, y, ch, fg, bg)

# --- PUPIL: depth ramp, dark core -> bright rim + jitter (multi-level, not a flat hole) --
PUPIL_RAMP = [(_g, _col, 0) for _col in (0, 4) for _g in DENS] + [(' ', 0, 0)]


def pupil_region(x, y):
    dx = x - 40.0
    dy = y - 23.0
    return (dx * dx) / (5.0 ** 2) + (dy * dy) / (5.0 ** 2) <= 1.0


for y in range(cv.h):
    for x in range(cv.w):
        if not pupil_region(x, y):
            continue
        r = math.hypot(x - 40.0, y - 23.0) / 5.0     # 0 center -> 1 rim
        t = (1.0 - r) + jit(x, y)                     # bright at rim, dark at core, + jitter
        idx = min(len(PUPIL_RAMP) - 1, int(t * len(PUPIL_RAMP)))
        ch, fg, bg = PUPIL_RAMP[idx]
        cv.set(x, y, ch, fg, bg)

# Glint: tiny bright spot on the lit side of the iris (small, not a flat region).
for y in range(18, 22):
    for x in range(35, 39):
        if (x - 36.5) ** 2 + (y - 19.5) ** 2 <= 1.8 ** 2:
            cv.set(x, y, C.RAMP[0], fg=15, bg=0)

# Background atmosphere behind the orb (negative space -- dithered starfield).
def bg_region(x, y):
    dx = x - 40.0
    dy = y - 22.0
    return not ((dx * dx) / (36.0 ** 2) + (dy * dy) / (36.0 ** 2) <= 1.0)

C.texture_fill(cv, bg_region, fg=5, bg=0, density=0.06, seed=7)

out = []
top = [C.sgr(13) + "\u2550" * W]


def sigline(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    right = pad - left
    return C.sgr(12) + " " * left + C.sgr(fg) + text + C.sgr(12) + " " * right


top.append(sigline("THE WATCHER", 5))
cv.render(out)
out.append(C.sgr(13) + "\u2550" * W)
full = top + out
C.write_ans('scratch/_watcher.v7.ans', full, title='THE WATCHER', handles='raze,hollis')
print("wrote scratch/_watcher.v7.ans", len(full), "rows")
