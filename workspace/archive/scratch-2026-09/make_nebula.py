#!/usr/bin/env python3
# NEBULA v1 -- AGENTSCII (hollis). A deep-space / cosmic piece: the one tradition
# this house has NOT touched. Everything shipped so far is landscape (dusk/wharf/city/
# railyard), fractal (fractal/julia/deepzoom/tunnel, closed pack11), data-terminal
# (monitor/operator/boot/shutdown/lifecycle, closed pack12), abstract pattern
# (radial/plasma/gridfall) or character portrait. No starscape / nebula exists.
# Cosmic block-dither work is squarely in ACiD/Blocktronics tradition -- this fills it.
#
# Composition: a single 80x46 field, three layers composited cell-by-cell so no cell
# is flat-filled (STYLE.md "every cell chosen"):
#    1. STARFIELD -- deterministic PRNG star scatter, varying brightness/size, a few
#       bright ones with a cross glint. Sparse, not noise: real stars are sparse.
#    2. NEBULA CLOUD -- two overlapping radial density fields (a magenta core + an
#       offset cyan arm) MODULATED by value-noise so the edges go ragged/filamentary
#       instead of reading as two solid ovals, block-dithered across the house HUE wheel.
#    3. A single bright foreground star (the focal point) with a proper glint cross,
#       drawn ON TOP of the cloud so it pops rather than getting buried.
# Double-line house frame + centered title band up top, sig block + version line below.
# Same ACiD idiom byte-for-byte as TUNNEL/DEEPZOOM/FRACTAL/JULIA/PLASMA: 80 cols,
# cp437 on disk, raw SGR, bright fg (91-107), bg 40, standalone \x1b[0m reset tail.

import math, random

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from TUNNEL/DEEPZOOM/FRACTAL/JULIA/PLASMA)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]       # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"               # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# deterministic starfield + nebula. Seed fixed so the piece is reproducible.
# ---------------------------------------------------------------------------
rng = random.Random(0x4E5B)    # "NEB" seed, fixed

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
    def lerp(a, b, t): return a + (b - a) * (t * t * (3 - 2 * t))   # smoothstep
    top = lerp(grid[(x0, y0)], grid[(x0 + 1, y0)], fx)
    bot = lerp(grid[(x0, y0 + 1)], grid[(x0 + 1, y0 + 1)], fx)
    return lerp(top, bot, fy)

def fbm(x, y):
    # two octaves of value noise -> wispy filament structure
    return 0.6 * vnoise(x, y, NG1) + 0.4 * vnoise(x * 2.3, y * 2.3, NG2)

# --- layer 1: starfield ---------------------------------------------------
# (col, row, brightness 0..3, glint bool). Sparse scatter; a few clustered so it
# reads as intentional constellations, not uniform noise.
stars = []
star_grid = {}
for _ in range(96):
    c = rng.randint(1, W - 2)
    r = rng.randint(1, H - 2)
    b = rng.choice([0, 0, 0, 1, 1, 2, 3])     # mostly dim, few bright
    glint = (b == 3 and rng.random() < 0.5)
    stars.append((c, r, b, glint))
for (c, r, b, g) in stars:
    star_grid[(c, r)] = (b, g)

# --- layer 2: nebula cloud density ---------------------------------------
# two overlapping radial fields -> a magenta core + an offset cyan arm.
def cloud(cx, cy, rx, ry, r, c):
    dx = (c - cx) / rx
    dy = (r - cy) / ry
    d = math.sqrt(dx * dx + dy * dy)
    return max(0.0, 1.0 - d)

CORE_CX, CORE_CY = 34, 24       # core, slightly left of center
ARM_CX, ARM_CY    = 56, 30      # arm, lower-right -> asymmetric, not a blob

def nebula_density(r, c):
    core = cloud(CORE_CX, CORE_CY, 18.0, 12.0, r, c) ** 1.4
    arm   = cloud(ARM_CX, ARM_CY, 16.0, 10.0, r, c) ** 1.6
    base = core * 0.75 + arm * 0.75
    if base < 0.05:
        return 0.0
    # filamentary modulation: noise carves wisps into the cloud so edges are ragged,
    # not smooth ellipse outlines. Keep a floor so the core stays dense.
    f = fbm(c * 0.35, r * 0.35)            # 0..1
    mod = 0.45 + 0.85 * f                  # 0.45 .. 1.30
    return min(1.0, base * mod)

# --- layer 3: focal star --------------------------------------------------
FOC_C, FOC_R = 62, 14           # bright foreground star in open space (upper-right),
                                # away from the cloud so its glint reads cleanly.

def nebula_field():
    emit(sgr(0, 40))            # black bg baseline (deep space)
    for r in range(H):
        cells = []
        for c in range(W):
            dens = nebula_density(r, c)
            st = star_grid.get((c, r))

            # focal star glint cross -- drawn on top so it pops over the field.
            dc = abs(c - FOC_C); dr = abs(r - FOC_R)
             # small plus-sign glint centered on the focal star, arms length 4.
            is_foc = ((r == FOC_R and dc <= 4) or (c == FOC_C and dr <= 4))

            if st is not None:
                sb, sglint = st
                 # a star cell. Brightness picks glyph density + hue.
                g = RAMP[0] if sb >= 2 else (RAMP[1] if sb == 1 else RAMP[3])
                fg = 107 if sb >= 2 else HUE[(c + r) % len(HUE)]   # bright white, dim cycle
                cells.append(sgr(fg, 40) + g)
            elif is_foc:
                 # focal star glint -- a thin bright cross, brightest at the center.
                if c == FOC_C and r == FOC_R:
                    cells.append(sgr(107, 40) + "\u2588")
                else:
                    fg = 103 if (c == FOC_C) else 96              # vert arm amber, horiz cyan
                    g = RAMP[1] if dc < 2 or dr < 2 else RAMP[2]
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
    emit(sgr(93, 40) + "\u2554" * W)             # double-line top
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
emit(sgr(103, 40) + "hollis / AGENTSCII")
emit(sgr(96, 40) + "NEBULA v1.0 -- block-dithered nebula + starfield, two-field cloud, focal glint")
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
    if len(vis) > W:
        raise AssertionError(f"row overflow {len(vis)} > {W}: {vis!r}")

with open("scratch/hollis-nebula.ans", "wb") as f:
    f.write(data + b"\n")
print("OK hollis-nebula.ans  rows=%d  bytes=%d" % (len(out), len(data)))
