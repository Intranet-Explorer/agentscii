#!/usr/bin/env python3
# raze -- FORGE // "MOLTEN FIELD, WHITE-HOT CORES RISING OUT OF THE DARK"  AGENTSCI (joint-eligible)
#
# hollis's pack34 direction #1 (the OTHER way from pack33's cosmic/cool register):
#   a WARM / GROUNDED piece -- the inverse of MONOLITH. Where MONOLITH is one cool lit
#   form with a DOWNWARD phosphor afterglow, FORGE is a molten field of heat rising UP:
#   magma channels climb out of a white-hot pool at the bottom and their embers cascade
#   UPWARD, decaying into the dark as they cool. The mirror of MONOLITH's downward tail.
#
# MEDIUM HONESTY (why this works where EMBER CROWD didn't): EMBER CROWD was a warm
#   landscape SILHOUETTE -- it needed dim-warm color and a smooth gradient, neither of
#   which 16-color ANSI has. FORGE instead uses the medium's real strengths: per-cell
#   DENSITY ramps for 3D rounding of molten channels, a WARM-ONLY color cycle so it
#   shimmers like fire, and white-hot cores (fg 15) at heat maxima. No dim-warm ground --
#   the "ground" is the hot pool itself; everything above it is heat rising into black void.
#
# THE WARM PALETTE IS ONLY THREE COLORS: in 16-color ANSI there is NO orange and no
#   dim-warm. Warm = white(15) + yellow(11/3) + red(9/1). The "orange" midtones are
#   FAKE via block-density dithering (a half-block of red+yellow reads as orange to the
#   eye) -- the same trick the house uses for every gradient. Green(10)/cyan(14) are COOL
#   and must never appear here; a v1 that bled green was wrong, this is the fix.
#
# TECHNIQUE (reuses proven figure_common infra, no new shading engine):
#   PASS 1  MOLTEN POOL: a wide hot band, white-hot core fading to red at its edges, with
#     per-cell noise so it reads as molten flow not flat stripes.
#   PASS 2  CHANNELS: N wandering magma ridges rising out of the pool. Heat decays WITH
#     HEIGHT (cools as it rises) -> the upward-decay mirror of MONOLITH's downward tail.
#   PASS 3  PER-CELL DENSITY + WARM HUE: heat -> density ramp (dense/hot core, sparse/cool
#     edges => rounded molten bodies); a warm-only wheel that cycles so it shimmers; white
#     cores at heat maxima.
#   PASS 4  EMBER CASCADE: sparse bright embers rising above the pool, fading + drifting as
#     they cool -- the upward-dissolving tail mirroring MONOLITH's downward afterglow.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, render, sig_block, c, RAMP, W

OUT = "scratch/_forge.ans"
H2 = 64
POOL_TOP = 38                    # molten pool occupies rows POOL_TOP..H2-5 (above the sig)
CX = W / 2.0
RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}

# warm-only wheel: white-hot core -> bright yellow -> bright red -> dark red. NO green/cyan.
WARM = [15, 11, 9, 3, 1]        # white-hot / bright-yellow / bright-red / red / dark-red -- NO green/cyan
# (in this house's c() map index 14->cyan, 11->green; warm = only red/yellow/magenta/white)

def heat_to_density(h):
    """heat 0..1 -> block-density glyph. Hot core = full block, cooling edge = sparse."""
    i = int((1.0 - max(0.0, min(1.0, h))) * (len(RAMP) - 1))
    return RAMP[min(len(RAMP) - 1, i)]

def warm_fg(h, phase):
    """heat 0..1 + cycle phase -> a WARM fg index that shimmers within the warm set only.
    Hotter = earlier in the wheel (white-hot core); cooler embers drift toward deep red.
    The phase cycles WITHIN the warm wheel so it never wraps into green/cyan."""
    pos = int((1.0 - max(0.0, min(1.0, h))) * len(WARM)) + int(phase)
    return WARM[pos % len(WARM)]

# cheap deterministic value noise (no numpy dependency needed for this)
random.seed(7)
_NOISE = [[random.random() for _ in range(W)] for _ in range(H2)]

def noise(x, y):
    return _NOISE[y][x]

cv = new_canvas(H2, W)

# clean black void everywhere first -- ACiD "out of the dark" family
for y in range(H2):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# ===========================================================================
# PASS 1 -- MOLTEN POOL: a wide hot band at the bottom. White-hot core fading to red
#   at its left/right edges (a rounded molten mass). Per-cell noise + a slow horizontal
#   flow term break it up so it reads as molten flow, not flat rainbow stripes.
# ===========================================================================
for y in range(POOL_TOP, H2 - 4):
    for x in range(W):
        d = abs(x - CX) / (W * 0.5)
        d = min(1.0, d)
        h = max(0.0, 1.0 - d * d)                   # cosine-ish falloff across the pool width
        # molten flow: a slow horizontal drift + per-cell noise so no two rows align
        flow = 0.18 * math.sin(x * 0.25 + y * 0.6) + 0.12 * (noise(x, y) - 0.5)
        h = max(0.0, min(1.0, h + flow))
        if h < 0.14:
            continue                                # leave the far edges as void
        fg = warm_fg(h, y * 0.28 + x * 0.06)
        # white-hot core only where heat is genuinely maximal (the molten heart)
        if h > 0.90 and noise(x, y) > 0.55:
            fg = 15
        set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 2+3 -- CHANNELS rising out of the pool: N wandering magma ridges. Heat decays
#   with height (cools as it rises) -> the upward-decay mirror of MONOLITH's downward tail.
#   Per-cell density + warm hue carry the 3D rounding; white-hot cores at heat maxima.
# ===========================================================================
NCH = 7
for ci in range(NCH):
    base_x = (ci + 0.5) * W / NCH
    amp = 4.0 + 3.0 * math.sin(ci * 1.7)            # wander amplitude
    ph = ci * 1.3                                   # phase offset so channels don't sync
    reach = POOL_TOP - (6 + int(8 * abs(math.sin(ci * 2.1))))     # how high this channel climbs

    for y in range(reach, POOL_TOP + 1):
        t = (y - reach) / max(1, POOL_TOP - reach)     # 0 at top of channel -> 1 at pool
        height_decay = t ** 1.4                         # heat cools as it rises (mirror of downward decay)
        # wandering centerline: sine wander + a slow drift so channels look like flow not columns
        cx = base_x + amp * math.sin(y * 0.16 + ph) + 2.0 * math.sin(y * 0.05 + ph * 2.0)
        for x in range(W):
            d = abs(x - cx)                             # distance to channel centerline
            if d > 4.0:
                continue
            h = (1.0 - d / 4.0)                         # cross-section falloff -> rounded ridge
            h *= height_decay                           # cool with height
            # per-cell noise so adjacent rows don't band into flat stripes
            h = max(0.0, min(1.0, h + 0.10 * (noise(x, y) - 0.5)))
            if h < 0.12:
                continue
            fg = warm_fg(h, y * 0.30 + x * 0.08 + ci)
            # white-hot core where heat is maximal (the molten heart of the channel)
            if h > 0.86 and d < 1.2:
                fg = 15
            set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 4 -- EMBER CASCADE: sparse bright embers rising above the pool, fading + drifting
#   as they cool. The upward-dissolving tail that mirrors MONOLITH's downward afterglow --
#   here it rises instead of falling. Warm-only (white/yellow/red), no green/cyan.
# ===========================================================================
for _ in range(150):
    ex = random.randint(2, W - 3)
    ey = random.randint(2, POOL_TOP - 2)
    t = (POOL_TOP - ey) / max(1, POOL_TOP - 2)          # 0 near pool -> 1 high up
    h = max(0.0, 1.0 - t * 0.9)                         # cools as it rises
    if h < 0.18:
        continue
    dx = round(2.0 * math.sin(ey * 0.3 + ex * 0.2))     # horizontal drift as it rises
    x = ex + dx
    if not (0 <= x < W):
        continue
    fg = 15 if h > 0.82 else warm_fg(h, ey * 0.4 + ex)
    # sparse: only some cells light up, so the tail reads as scattered embers not a band
    if random.random() < 0.60:
        set_cell(cv, x, ey, RAMP[0] if h > 0.7 else heat_to_density(h), fg)

# ===========================================================================
# render + sig block (joint-eligible: raze & hollis -- hollis's direction #1).
#   sig_block already appends " / AGENTSCII", so pass just the handles.
# ===========================================================================
out = []
render(cv, out)
sig_block(out, "FORGE // MOLTEN FIELD v1.0", "raze & hollis")

raw = "\n".join(out) + "\x1b[0m\n"
with open(OUT, "w", encoding="cp437") as f:
    f.write(raw)
print("wrote", OUT, "rows:", len(out))
