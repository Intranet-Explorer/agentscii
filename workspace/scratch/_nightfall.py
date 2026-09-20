#!/usr/bin/env python3
# _nightfall.py -- AGENTSCII pack27 companion to _darkofdark.ans   (joint raze & hollis)
#
# random_direction roll: subject "a night skyline / cityscape", technique
# "build the core shape + shading with canvas.ellipse() + gradient_fill()",
# palette lean "muted/dim, low-saturation throughout".
#
# DELIBERATELY DISTINCT from hollis-city (pack02): that one is BRIGHT NEON over
# water -- saturated blue->magenta sky, white moon, an AGENTSCI sign column.
# This is the OPPOSITE register: a DIM, low-saturation nocturnal skyline. A
# mostly-BLACK sky with only a thin dim-blue band at the very top; one small
# pale moon (ellipse + radial halo); near-black building silhouettes built as a
# DITHERED mass (not solid fills -- 16-color has no "dim red", so a solid fill
# reads loud, like an equalizer); a FEW sparse amber windows; and a broken,
# wavy water reflection. No neon, no wordmark sign -- the city at its quietest
# hour. Pairs thematically with _darkofdark ("the constellation goes out") as
# "the world after the light". Different FORM on purpose: darkofdark is a tall
# vertical scroll (time across space); this is ONE static panel (a held moment).
#
# Core shape/shading built on canvas.ellipse() (moon disc + halo) and
# canvas.gradient_fill()/dither_region() (sky top-band fade, moon radial halo,
# building-mass dither).

import sys
import random
sys.path.insert(0, "scratch")
import canvas as C

W = 80
H = 52
cv = C.Canvas(W, H, fill_ch=" ", fill_fg=0, fill_bg=0)

# ---- palette: muted / dim throughout ---------------------------------------
SKY_TOP   = 4          # dim blue -- only the very top band
BLACK     = 0
MOON      = 8          # bright white -- the ONE accent, kept small/pale
MOON_HALO = 7          # gray halo / reflected moonlight
B_BACK    = 8          # back building mass -- faint gray silhouette (far)
B_FRONT   = 7          # front building mass -- slightly brighter gray (near)
WIN       = 3          # dim amber window -- sparse warm accent
WATER     = 1          # near-black red water base
REFL      = 7          # reflected light, broken by waves

SKY_BOTTOM = 30        # row where skyline base / waterline sits
WATER_TOP  = SKY_BOTTOM + 1

# ---- 1. SKY: mostly black; only a thin dim-blue band at the very top --------
def sky_band(x, y):
    return y < 6                                            # just the top ~6 rows
C.dither_region(cv, sky_band, lambda x, y: max(0.0, 1.0 - y / 6.0), fg=SKY_TOP)

# ---- 2. MOON: small pale ellipse disc + subtle radial gradient halo ---------
MOONX, MOONY = 58, 9
C.ellipse(cv, MOONX, MOONY, 3, 3, ch='\u2588', fg=MOON, fill=True)           # pale disc

def halo_region(x, y):
    d = ((x - MOONX) ** 2 + (y - MOONY) ** 2) ** 0.5
    return 3.4 < d < 6.0
C.gradient_fill(cv, halo_region, cx=MOONX, cy=MOONY, fg_near=MOON_HALO,
                fg_far=BLACK, max_dist=6.5)

# ---- 3. STARS: sparse dim points in the upper sky --------------------------
random.seed(1984)
for _ in range(20):
    sx = random.randint(1, W - 2)
    sy = random.randint(1, SKY_BOTTOM - 16)
    if ((sx - MOONX) ** 2 + (sy - MOONY) ** 2) ** 0.5 < 7:
        continue
    cv.set(sx, sy, '*', fg=random.choice([8, 7, 6]))

# ---- 4. SKYLINE: two near-black building layers as a DITHERED mass ---------
# In 16-color there is no dim red; a solid fill reads loud. So the city is a
# faint gray silhouette (back = far / fainter, front = near / brighter) with
# per-mass dither so it reads as MASS, not flat blocks.
def building_mass(base_y, top_fn, fg, lo_d, hi_d):
    def region(x, y):
        top = top_fn(x)
        return top is not None and top <= y <= base_y

    def density(x, y):
        rng = random.Random((x * 131 + int(top_fn(x)) * 977) & 0xffff)
        span = max(1, base_y - top_fn(x))
        d = lo_d + (hi_d - lo_d) * ((y - top_fn(x)) / span)
        return max(0.0, min(1.0, d + rng.uniform(-0.12, 0.12)))

    C.dither_region(cv, region, density, fg=fg, bg=BLACK)

def height_series(seed, x0, x1, lo, hi):
    rng = random.Random(seed)
    out = {}
    x = x0
    while x < x1:
        w = rng.randint(2, 5)
        h = rng.randint(lo, hi)
        for xx in range(x, min(x + w, x1)):
            out[xx] = h
        x += w
    return out

back_h  = height_series(7, 0, W, 8, 22)          # back: taller, fainter
front_h = height_series(31, 0, W, 5, 14)         # front: shorter, brighter

building_mass(SKY_BOTTOM, lambda x: SKY_BOTTOM - back_h.get(x, 0), B_BACK, 0.10, 0.30)
building_mass(SKY_BOTTOM, lambda x: SKY_BOTTOM - front_h.get(x, 0), B_FRONT, 0.18, 0.42)

# ---- 5. WINDOWS: a FEW sparse dim-amber dots on the FRONT masses -----------
rng = random.Random(1984)
for bx in range(W):
    fh = front_h.get(bx, 0)
    if fh < 3:
        continue
    top = SKY_BOTTOM - fh
    for wy in range(top + 1, SKY_BOTTOM):
        if rng.random() < 0.14:                          # sparse -> a few lit windows
            cv.set(bx, wy, '\u2588', fg=WIN, bg=BLACK)

# ---- 6. WATERLINE + BROKEN REFLECTION --------------------------------------
C.line(cv, 0, WATER_TOP - 1, W - 1, WATER_TOP - 1, ch='\u2500', fg=WATER)     # thin waterline

# Reflect the lit content (moon, windows, building tops) downward, broken by a
# horizontal wave so it shimmers instead of mirroring cleanly.
sky_block = C.copy_region(cv, 0, SKY_BOTTOM - 18, W - 1, SKY_BOTTOM)          # last 18 rows
flipped = list(reversed(sky_block))
for i, row in enumerate(flipped):
    ry = WATER_TOP + i
    if ry >= H:
        break
    off = int(round(1.6 * ((ry - WATER_TOP) % 4) / 2.0)) * (1 if (i // 3) % 2 == 0 else -1)
    for j, cell in enumerate(row):
        ch, fg, bg = cell
        if ch == ' ':
            continue
        if ((ry + off) // 2) % 3 == 0:                  # wave troughs swallow it -> broken
            continue
        dx = j + off
        if 0 <= dx < W and fg != BLACK:
            cv.set(dx, ry, ch, fg=REFL, bg=BLACK)

# faint reflected moon column, broken the same way
for ry in range(WATER_TOP, min(WATER_TOP + 12, H)):
    if (ry // 2) % 3 == 0:
        continue
    if (ry - WATER_TOP) < 6:
        cv.set(MOONX, ry, '\u2588', fg=MOON_HALO, bg=BLACK)

# ---- 7. TITLE CARD (top) + house signature block (bottom) ------------------
out = []

def center(text, fg):
    pad = max(0, W - len(text)); l = pad // 2; r = pad - l
    return C.sgr(12) + " " * l + C.sgr(fg) + text + C.sgr(12) + " " * r

out.append(C.sgr(13) + "\u2550" * W)
out.append(center("NIGHTFALL", 8))
out.append(center("// the city after the light //", 7))
out.append(C.sgr(13) + "\u2550" * W)
out.append("")

cv.render(out)

out.append("")
# house-standard signature block (handle / tag / title), standalone reset tail
C.sig_block(out, "NIGHTFALL v1.0", handles="raze & hollis")

C.write_ans("scratch/_nightfall.ans", out, add_sig=False)
