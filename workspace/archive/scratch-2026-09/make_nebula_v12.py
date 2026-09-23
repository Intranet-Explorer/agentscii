#!/usr/bin/env python3
# NEBULA v1.1 -- AGENTSCII (hollis & raze, JOINT).
#
# hollis built the base: a deep-space field with a two-field nebula cloud + sparse
# starfield + focal glint cross. raze adds a distant SPIRAL GALAXY CLUSTER in the
# upper-left quadrant -- balancing the composition (nebula sits center/lower-right,
# focal glint upper-right) and giving the open space a second point of interest.
# Same ACiD idiom byte-for-byte: 80 cols, cp437 on disk, raw SGR, bright fg
# (91-107), bg 40, standalone \x1b[0m reset tail.

import math, random

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from TUNNEL/DEEPZOOM/FRACTAL/JULIA/PLASMA)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]        # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# deterministic starfield + nebula. Seed fixed so the piece is reproducible.
# ---------------------------------------------------------------------------
rng = random.Random(0x4E5B)     # "NEB" seed, fixed

# --- value noise (cheap 2D) for filamentary cloud edges -------------------
def _noise_grid(seed):
    g = {}
    r = random.Random(seed)
    for i in range(W + 2):
        for j in range(H + 2):
            g[(i, j)] = r.random()
    return g
NG1 = _noise_grid(0x1001)
NG2 = _noise_grid(0x2002)

def vnoise(x, y, grid):
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    def lerp(a, b, t): return a + (b - a) * (t * t * (3 - 2 * t))    # smoothstep
    top = lerp(grid[(x0, y0)], grid[(x0 + 1, y0)], fx)
    bot = lerp(grid[(x0, y0 + 1)], grid[(x0 + 1, y0 + 1)], fx)
    return lerp(top, bot, fy)

def fbm(x, y):
     # two octaves of value noise -> wispy filament structure
    return 0.6 * vnoise(x, y, NG1) + 0.4 * vnoise(x * 2.3, y * 2.3, NG2)

# --- layer 1: starfield ---------------------------------------------------
stars = []
star_grid = {}
for _ in range(96):
    c = rng.randint(1, W - 2)
    r = rng.randint(1, H - 2)
    b = rng.choice([0, 0, 0, 1, 1, 2, 3])      # mostly dim, few bright
    glint = (b == 3 and rng.random() < 0.5)
    stars.append((c, r, b, glint))
for (c, r, b, g) in stars:
    star_grid[(c, r)] = (b, g)

# --- layer 2: nebula cloud density ---------------------------------------
def cloud(cx, cy, rx, ry, r, c):
    dx = (c - cx) / rx
    dy = (r - cy) / ry
    d = math.sqrt(dx * dx + dy * dy)
    return max(0.0, 1.0 - d)

CORE_CX, CORE_CY = 34, 24        # core, slightly left of center
ARM_CX, ARM_CY     = 56, 30      # arm, lower-right -> asymmetric, not a blob

def nebula_density(r, c):
    core = cloud(CORE_CX, CORE_CY, 18.0, 12.0, r, c) ** 1.4
    arm    = cloud(ARM_CX, ARM_CY, 16.0, 10.0, r, c) ** 1.6
    base = core * 0.75 + arm * 0.75
    if base < 0.05:
        return 0.0
     # filamentary modulation: noise carves wisps into the cloud so edges are ragged,
     # not smooth ellipse outlines. Keep a floor so the core stays dense.
    f = fbm(c * 0.35, r * 0.35)             # 0..1
    mod = 0.45 + 0.85 * f                   # 0.45 .. 1.30
    return min(1.0, base * mod)

# --- layer 2b: distant spiral galaxy cluster (raze's joint pass) ---------
# A small barred-spiral galaxy in the upper-left quadrant -- a bright dense core
# with two fainter logarithmic spiral arms winding out of it, plus a couple of
# satellite dwarf galaxies. Logarithmic spiral density: r = a * exp(b*theta).
GAL_CX, GAL_CY = 16, 13        # upper-left quadrant, away from the nebula cloud
def galaxy_density(r, c):
    dx = c - GAL_CX
    dy = r - GAL_CY
    d = math.sqrt(dx * dx + dy * dy)
    if d > 13.0:
        return 0.0
     # bright elliptical core (dense, tight)
    core = max(0.0, 1.0 - d / 4.5) ** 2.2
     # two logarithmic spiral arms winding out of the core
    theta = math.atan2(dy, dx)
    b = 0.30                       # spiral tightness
    arm1 = max(0.0, 1.0 - abs(((theta + 0.0) * d / (2 * math.pi * b)) % 1.0 - 0.5) * 3.0)
    arm2 = max(0.0, 1.0 - abs(((theta + math.pi) * d / (2 * math.pi * b)) % 1.0 - 0.5) * 3.0)
    arms = max(arm1, arm2) * max(0.0, 1.0 - d / 9.0) ** 1.8
     # faint satellite dwarf galaxies (two small blobs off to the side)
    sat1 = max(0.0, 1.0 - math.sqrt((c - 30)**2 + (r - 8)**2) / 3.0) ** 2.5 * 0.7
    sat2 = max(0.0, 1.0 - math.sqrt((c - 6)**2 + (r - 24)**2) / 2.5) ** 2.5 * 0.6
    base = core + arms * 0.85 + sat1 + sat2
    if base < 0.05:
        return 0.0
     # light noise modulation so the galaxy edges are ragged, not smooth ellipses
    f = fbm(c * 0.5 + 7.0, r * 0.5 + 3.0)
    mod = 0.6 + 0.6 * f
    return min(1.0, base * mod)

# --- layer 3: focal star --------------------------------------------------
FOC_C, FOC_R = 62, 14            # bright foreground star in open space (upper-right),
                                 # away from the cloud so its glint reads cleanly.

def nebula_field():
    emit(sgr(0, 40))              # black bg baseline (deep space)
    for r in range(H):
        cells = []
        for c in range(W):
            dens = nebula_density(r, c)
            gdens = galaxy_density(r, c)
            st = star_grid.get((c, r))

              # focal star glint cross -- drawn on top so it pops over the field.
            dc = abs(c - FOC_C); dr = abs(r - FOC_R)
               # small plus-sign glint centered on the focal star, arms length 4.
            is_foc = ((r == FOC_R and dc <= 4) or (c == FOC_C and dr <= 4))

            if st is not None:
                sb, sglint = st
                   # a star cell. Brightness picks glyph density + hue.
                g = RAMP[0] if sb >= 2 else (RAMP[1] if sb == 1 else RAMP[3])
                fg = 107 if sb >= 2 else HUE[(c + r) % len(HUE)]     # bright white, dim cycle
                cells.append(sgr(fg, 40) + g)
            elif is_foc:
                   # focal star glint -- a thin bright cross, brightest at the center.
                if c == FOC_C and r == FOC_R:
                    cells.append(sgr(107, 40) + "\u2588")
                else:
                    fg = 103 if (c == FOC_C) else 96                # vert arm amber, horiz cyan
                    g = RAMP[1] if dc < 2 or dr < 2 else RAMP[2]
                    cells.append(sgr(fg, 40) + g)
            elif gdens > 0.05:
                   # v1.2: distant spiral galaxy rendered BEFORE the nebula so the cloud can't mask it.
                   # warm core (amber/yellow), cool arms (cyan/blue).
                di = int(gdens * 3.999)
                g = RAMP[di]
                gd = math.sqrt((c - GAL_CX)**2 + (r - GAL_CY)**2)
                if gd < 2.4:
                    fg = 107            # v1.2: hot white core so it pops as a distinct galaxy
                elif gd < 3.6:
                    fg = 93             # yellow
                elif gd < 5.0:
                    fg = 103            # amber mid
                else:
                    fg = HUE[4]         # cyan arms (cool)
                cells.append(sgr(fg, 40) + g)
            elif dens > 0.05:
                   # nebula cloud cell -- density drives glyph AND hue (the "chosen" bar).
                di = int(dens * 3.999)
                g = RAMP[di]
                   # hue: core region magenta/green, arm region cyan/blue, blended by position
                t = (c + r * 0.5) / (W + H * 0.5)
                fg = HUE[int(t * len(HUE)) % len(HUE)]
                cells.append(sgr(fg, 40) + g)
            else:
                   # deep space -- leave the black bg, but keep it a real cell (space char).
                cells.append(" ")
        emit("".join(cells))

# ---------------------------------------------------------------------------
# frame + title band + sig block (house bar, same as TUNNEL/DEEPZOOM/FRACTAL)
# ---------------------------------------------------------------------------
def frame_top():
    emit(sgr(93, 40) + "\u2554" * W)              # double-line top
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
emit(sgr(103, 40) + "hollis & raze / AGENTSCII")
emit(sgr(96, 40) + "NEBULA v1.2 -- nebula + starfield + spiral galaxy (corner), joint pass")
emit(RESET)

# ---------------------------------------------------------------------------
# self-check hygiene gate (mirrors TUNNEL/DEEPZOOM/FRACTAL builders)
# ---------------------------------------------------------------------------
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
    # framed content rows are 80 wide by construction; sig/version lines are
    # intentionally short (centered credits), same as every other piece.
    if len(vis) > W:
        raise AssertionError(f"row overflow {len(vis)} > {W}: {vis!r}")

with open("scratch/hollis-raze-nebula-v12.ans", "wb") as f:
    f.write(data)
print(f"wrote scratch/hollis-raze-nebula.ans  ({len(data)} bytes, {len(out)} lines)")
