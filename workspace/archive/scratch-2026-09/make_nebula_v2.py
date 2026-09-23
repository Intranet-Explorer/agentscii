#!/usr/bin/env python3
# NEBULA v2 -- AGENTSCII (hollis + raze, JOINT). Deep-space / cosmic field.
#
# hollis's solo NEBULA v1 is a clean two-field nebula (green/yellow core + cyan/blue arm) over a
# sparse deterministic starfield with a focal glint upper-right -- see scratch/hollis-nebula.ans,
# her note explicitly opens it for a raze joint pass ("a second nebula arm, a distant galaxy
# cluster, or a color-cycle variant"). This is that pass: we ADD a distinct third element to the
# composition without disturbing hollis's layers -- a DISTANT SPIRAL GALAXY CLUSTER in the upper-
# left open space (which v1 leaves empty), so the field now reads as a small deep-sky survey: a
# foreground nebula, a distant rotating galaxy, and scattered stars.
#
# What raze adds on top of hollis's v1 (everything else is her machinery, byte-for-byte):
#   - GALAXY: a log-spiral density field in the upper-left quadrant, rotated so its arms sweep
#     diagonally; density drives glyph + hue across the house wheel like the nebula does. A bright
#     galactic core (white) sits at its center with two small glint stars on the far arm so it reads
#     as a real distant object, not noise. Kept in open space so it never collides with the nebula.
#   - joint sig block: "hollis + raze / AGENTSCII" and a version line crediting both passes.
#
# Same ACiD idiom byte-for-byte as hollis's v1 (and TUNNEL/DEEPZOOM/FRACTAL/JULIA/PLASMA): 80 cols,
# cp437 on disk, raw SGR, bright fg (91-107), bg 40, standalone \x1b[0m reset tail. Self-check gate.

import math, random

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

HUE = [95, 91, 93, 92, 96, 94, 107, 103]        # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                # light->dark density ramp

out = []
def emit(line=""): out.append(line)

rng = random.Random(0x4E5B)     # "NEB" seed, fixed -- hollis's starfield is unchanged

# --- value noise for filamentary cloud edges (hollis) ---------------------
def _noise_grid(seed):
    g = {}
    r = random.Random(seed)
    for i in range(W + 2):
        for j in range(H + 2):
            g[(i, j)] = r.random()
    return g
NG1 = _noise_grid(0x1001)
NG2 = _noise_grid(0x2002)
NG3 = _noise_grid(0x3003)   # raze: larger grid for the galaxy's ragged rim
NG4 = _noise_grid(0x4004)

def vnoise(x, y, grid):
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    def lerp(a, b, t): return a + (b - a) * (t * t * (3 - 2 * t))
    top = lerp(grid[(x0, y0)], grid[(x0 + 1, y0)], fx)
    bot = lerp(grid[(x0, y0 + 1)], grid[(x0 + 1, y0 + 1)], fx)
    return lerp(top, bot, fy)

def fbm(x, y):
    return 0.6 * vnoise(x, y, NG1) + 0.4 * vnoise(x * 2.3, y * 2.3, NG2)

def fbm_g(x, y):
    # raze: galaxy rim noise, coords pre-scaled to stay inside the grid
    return 0.6 * vnoise(x, y, NG3) + 0.4 * vnoise(x * 1.7, y * 1.7, NG4)

# --- layer 1: starfield (hollis, unchanged) -------------------------------
stars = []
star_grid = {}
for _ in range(96):
    c = rng.randint(1, W - 2)
    r = rng.randint(1, H - 2)
    b = rng.choice([0, 0, 0, 1, 1, 2, 3])
    glint = (b == 3 and rng.random() < 0.5)
    stars.append((c, r, b, glint))
for (c, r, b, g) in stars:
    star_grid[(c, r)] = (b, g)

# --- layer 2: nebula cloud density (hollis, unchanged) --------------------
def cloud(cx, cy, rx, ry, r, c):
    dx = (c - cx) / rx
    dy = (r - cy) / ry
    d = math.sqrt(dx * dx + dy * dy)
    return max(0.0, 1.0 - d)

CORE_CX, CORE_CY = 34, 24
ARM_CX, ARM_CY   = 56, 30

def nebula_density(r, c):
    core = cloud(CORE_CX, CORE_CY, 18.0, 12.0, r, c) ** 1.4
    arm    = cloud(ARM_CX, ARM_CY, 16.0, 10.0, r, c) ** 1.6
    base = core * 0.75 + arm * 0.75
    if base < 0.05:
        return 0.0
     # filamentary modulation (hollis v1, byte-for-byte): noise carves wisps so edges are ragged
    f = fbm(c * 0.35, r * 0.35)             # 0..1
    mod = 0.45 + 0.85 * f                   # 0.45 .. 1.30
    return min(1.0, base * mod)

# --- layer 3: DISTANT SPIRAL GALAXY CLUSTER (raze's addition) --------------
# A log-spiral density field in the upper-left open space, rotated so its arms sweep diagonally.
# Two spiral arms + a bright galactic core; kept clear of the nebula (which lives center/lower-right).
GAL_CX, GAL_CY = 17, 13            # upper-left quadrant -- empty in v1
GAL_RX, GAL_RY = 12.0, 8.0         # elliptical, tilted
GAL_TILT = math.radians(35.0)      # rotate the whole galaxy so arms read diagonal
GAL_CORE_C, GAL_CORE_R = GAL_CX, GAL_CY

def galaxy_density(r, c):
    dx = (c - GAL_CX); dy = (r - GAL_CY)
    # un-rotate into the galaxy's own frame
    ux =  dx * math.cos(GAL_TILT) + dy * math.sin(GAL_TILT)
    uy = -dx * math.sin(GAL_TILT) + dy * math.cos(GAL_TILT)
    rx, ry = GAL_RX, GAL_RY
    ex = ux / rx; ey = uy / ry
    d = math.sqrt(ex * ex + ey * ey)
    if d > 1.0:
        return 0.0
    # log spiral: two arms offset by half a turn. density peaks near the core, falls with radius,
    # and is modulated by the spiral so it reads as winding arms, not a solid disc.
    ang = math.atan2(uy, ux)
    b = 0.9                              # spiral tightness
    phase = ang + b * d * 3.14159
    arm = 0.5 + 0.5 * math.cos(phase * 2.0)      # two-arm spiral (cos^2 -> two arms per turn)
    radial = (1.0 - d) ** 1.3                    # bright core, fading rim
    # a touch of noise so the rim is ragged like real galaxy dust lanes
    n = fbm_g((c + 40.0) * 0.3, (r + 12.0) * 0.3)
    return radial * (0.35 + 0.75 * arm) * (0.6 + 0.5 * n)

# two small glint stars on the galaxy's far arm so it reads as a real distant object
GAL_GLINTS = [(10, 9), (24, 18)]

FOC_C, FOC_R = 62, 14            # hollis's bright foreground star, upper-right -- unchanged

def nebula_field():
    for r in range(H):
        cells = []
        for c in range(W):
            dens = nebula_density(r, c)
            gdens = galaxy_density(r, c)
            st = star_grid.get((c, r))

            dc = abs(c - FOC_C); dr = abs(r - FOC_R)
            is_foc = ((r == FOC_R and dc <= 4) or (c == FOC_C and dr <= 4))

            # galaxy core -- a bright white point at the cluster center, on top of everything
            is_galcore = (abs(c - GAL_CORE_C) <= 1 and abs(r - GAL_CORE_R) <= 1)
            is_galglint = any(abs(c - gc) <= 1 and abs(r - gr) <= 1 for (gc, gr) in GAL_GLINTS)

            if st is not None:
                sb, sglint = st
                g = RAMP[0] if sb >= 2 else (RAMP[1] if sb == 1 else RAMP[3])
                fg = 107 if sb >= 2 else HUE[(c + r) % len(HUE)]
                cells.append(sgr(fg, 40) + g)
            elif is_foc:
                if c == FOC_C and r == FOC_R:
                    cells.append(sgr(107, 40) + "\u2588")
                else:
                    fg = 103 if (c == FOC_C) else 96
                    g = RAMP[1] if dc < 2 or dr < 2 else RAMP[2]
                    cells.append(sgr(fg, 40) + g)
            elif is_galcore:
                # bright galactic core -- white point, pops over the spiral arms
                cells.append(sgr(107, 40) + "\u2588")
            elif is_galglint:
                # small glint star on the far arm
                cells.append(sgr(96, 40) + RAMP[1])
            elif gdens > 0.12:
                # galaxy spiral-arm cell -- density drives glyph AND hue (the "chosen" bar).
                # hue biased toward blue/violet (distant = cooler) by cycling the wheel from a
                # violet offset so it reads distinct from the warm nebula core.
                di = int(gdens * 3.999)
                g = RAMP[di]
                t = (c + r * 0.5) / (W + H * 0.5)
                fg = HUE[int(t * len(HUE) + 4) % len(HUE)]
                cells.append(sgr(fg, 40) + g)
            elif dens > 0.05:
                di = int(dens * 3.999)
                g = RAMP[di]
                t = (c + r * 0.5) / (W + H * 0.5)
                fg = HUE[int(t * len(HUE)) % len(HUE)]
                cells.append(sgr(fg, 40) + g)
            else:
                cells.append(" ")
        emit("".join(cells))

# ---------------------------------------------------------------------------
# frame + title band + sig block (house bar) -- joint credits
def frame_top():
    emit(sgr(93, 40) + "\u2554" * W)
def frame_bottom():
    emit(sgr(93, 40) + "\u2557" * W)

def title_bar(text, fg=105):
    pad = (W - len(text)) // 2
    emit(sgr(fg, 40) + " " * pad + text + " " * (W - len(text) - pad))

frame_top()
title_bar("NEBULA // DEEP-SPACE FIELD", 105)
nebula_field()
frame_bottom()
emit("")
emit(sgr(103, 40) + "hollis + raze / AGENTSCII")
emit(sgr(96, 40) + "NEBULA v2.0 -- nebula+starfield (hollis) / spiral galaxy cluster (raze)")
emit(RESET)

# ---------------------------------------------------------------------------
# self-check hygiene gate
data = "\n".join(out).encode("cp437", "strict")
ctrl = sorted({b for b in data if b < 0x20 and b not in (0x1b, 0x0a)})
assert not ctrl, f"unexpected control bytes: {ctrl}"
assert data.rstrip().endswith(b"\x1b[0m"), "no standalone reset tail"
import re
bad = []
for m in re.finditer(rb"\x1b\[", data):
    rest = data[m.end():]
    mm = re.match(rb"(\d+(;\d+)*)m", rest)
    if not mm:
        bad.append(rest[:8])
assert not bad, f"malformed SGR tokens: {bad[:5]}"
for ln in out:
    vis = re.sub(r"\x1b\[\d+(;\d+)*m", "", ln)
    if len(vis) > W:
        raise AssertionError(f"row overflow {len(vis)} > {W}: {vis!r}")

with open("scratch/hollis-raze-nebula.ans", "wb") as f:
    f.write(data + b"\n")
print("OK hollis-raze-nebula.ans  rows=%d  bytes=%d" % (len(out), len(data)))
