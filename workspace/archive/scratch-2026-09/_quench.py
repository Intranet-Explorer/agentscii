#!/usr/bin/env python3
# raze -- QUENCH // "CONFLAGRATION RADIATING OUT OF THE DARK"  AGENTSCI (molten set v3)
#
# WHY THIS IS A GENUINE v3, NOT A RE-SHIP (curator's direction on the rejected molten pieces):
#   The molten set so far is two registers:
#     MONOLITH (cool, pack33) = one lit form + a DOWNWARD phosphor afterglow decaying into dark.
#     FORGE    (warm, pack34) = heat rising VERTICALLY out of a white-hot pool at the bottom;
#                               7 magma channels climb, embers cascade UP along their centerlines.
#   Both are 1-D in their heat flow: vertical up or vertical down. QUENCH is the missing THIRD
#   register -- RADIAL. It's the thermodynamic INVERSE of FORGE: where FORGE is a pool feeding
#   heat upward, QUENCH is molten metal meeting COLD and cracking OUTWARD in every direction from
#   a single white-hot center -- a conflagration / quench-crack bloom. Heat decays with RADIUS
#   (cools as it travels outward), the radial mirror of FORGE's height-decay. This is "a third
#   register, a different ember behavior, and an extended field" exactly as asked -- not a prior
#   revision re-shipped.
#
# MEDIUM HONESTY (same learning as FORGE/MOLTEN MARK): 16-color ANSI has no orange and no
#   dim-warm. Warm = white(15) + yellow(3/11) + red(9/1). "Orange" midtones are FAKE via
#   block-density dithering (a half-block of red+yellow reads as orange to the eye). Green(10)/
#   cyan(14) are COOL and must never appear in the art field; the only cyan is sig_block's title
#   line, which uses fg 96 by house convention -- every piece does.
#
# TECHNIQUE (reuses proven figure_common infra, no new shading engine):
#   PASS 1  WHITE-HOT CORE: a small dense hot disc at the field center -- the "moment of impact."
#     Radial cosine falloff so it reads as a rounded molten heart, not a square block. Per-cell
#     noise + a slow swirl term break it up so it reads as molten flow, not flat stripes.
#   PASS 2/3 CRACK-LINES / MOLTEN FINS: N fins radiating outward from the core at varied angles.
#     Each fin wanders (sine wander around its radial angle + a slow secondary drift). Heat decays
#     WITH RADIUS (cools as it travels out) -> the radial inverse of FORGE's height-decay. Per-cell
#     density ramp (dense/hot inner end, sparse/cool outer tip => rounded molten bodies) + a warm-
#     only hue cycle so it shimmers; white-hot cores (fg 15) at the inner ends near the heart.
#   PASS 4  EMBER SCATTER: sparse bright embers scattered RADIALY -- each rides a crack-line
#     direction with lateral jitter and cools as it travels outward (the "different ember behavior":
#     radial scatter with cooling trails, not FORGE's vertical drift). A handful of free embers
#     dissolve into the void between fins for the "breaking apart" feel.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, render, sig_block, c, RAMP, W

OUT = "scratch/_quench.ans"
H2 = 64
CX = W / 2.0
CY = H2 * 0.46                       # field center -- a touch above middle so the bloom has room to fall into the sig
RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}

# warm-only wheel: white-hot core -> bright yellow -> bright red -> red -> dark-red. NO green/cyan.
WARM = [15, 11, 9, 3, 1]

def heat_to_density(h):
    """heat 0..1 -> block-density glyph. Hot inner end = full block, cooling tip = sparse."""
    i = int((1.0 - max(0.0, min(1.0, h))) * (len(RAMP) - 1))
    return RAMP[min(len(RAMP) - 1, i)]

def warm_fg(h, phase):
    """heat 0..1 + cycle phase -> a WARM fg index that shimmers within the warm set only.
    Hotter = earlier in the wheel (white-hot core); cooler embers drift toward deep red.
    The phase cycles WITHIN the warm wheel so it never wraps into green/cyan."""
    pos = int((1.0 - max(0.0, min(1.0, h))) * len(WARM)) + int(phase)
    return WARM[pos % len(WARM)]

# cheap deterministic value noise (no numpy dependency needed for this)
random.seed(11)
_NOISE = [[random.random() for _ in range(W)] for _ in range(H2)]
def noise(x, y):
    return _NOISE[y][x]

cv = new_canvas(H2, W)

# clean black void everywhere first -- ACiD "out of the dark" family
for y in range(H2):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# ===========================================================================
# PASS 1 -- WHITE-HOT CORE: a small dense hot disc at the field center. The moment
#   of impact. Radial cosine falloff -> rounded molten heart. Per-cell noise + a slow
#   swirl term break it up so it reads as molten flow, not flat stripes.
# ===========================================================================
CORE_R = 7.0
for y in range(H2):
    for x in range(W):
        d = math.hypot(x - CX, y - CY)
        if d > CORE_R + 1.5:
            continue
        h = max(0.0, 1.0 - (d / CORE_R) ** 2)               # cosine-ish radial falloff
        swirl = 0.16 * math.sin(d * 0.7 - (x - CX) * 0.3 + y * 0.4) + 0.12 * (noise(x, y) - 0.5)
        h = max(0.0, min(1.0, h + swirl))
        if h < 0.16:
            continue
        fg = warm_fg(h, d * 0.30 + x * 0.05)
        if h > 0.92 and noise(x, y) > 0.5:                  # white-hot heart only at the true center
            fg = 15
        set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 2+3 -- CRACK-LINES / MOLTEN FINS radiating outward from the core. N fins at
#   varied angles; each wanders (sine wander around its radial angle + slow secondary drift).
#   Heat decays WITH RADIUS (cools as it travels out) -> the radial inverse of FORGE's height-
#   decay. Per-cell density + warm hue carry the 3D rounding; white-hot cores at inner ends.
# ===========================================================================
NFINS = 11
FINS = []    # list of (angle, reach, phase, amp) so the ember pass can scatter along them
for fi in range(NFINS):
    ang = (fi / NFINS) * 2 * math.pi + 0.35 * math.sin(fi * 1.9)   # even spread + jitter, not a clean comb
    reach = CORE_R + 14 + int(16 * abs(math.sin(fi * 2.3 + 0.5)))   # varied fin length (some long, some short)
    amp = 2.0 + 3.5 * abs(math.sin(fi * 1.7 + 0.6))                # wander amplitude
    ph = fi * 1.3 + 0.7 * math.sin(fi * 2.3)                       # phase so fins don't sync

    FINS.append((ang, reach, amp, ph))

    for r in range(int(CORE_R), int(reach)):
        t = (r - CORE_R) / max(1.0, reach - CORE_R)                # 0 at core -> 1 at tip
        radius_decay = (1.0 - t) ** 1.35                            # heat cools as it travels outward
        # wandering centerline: radial direction + perpendicular sine wander + slow secondary drift
        base_x = CX + r * math.cos(ang)
        base_y = CY + r * math.sin(ang)
        perp = ang + math.pi / 2.0
        wander = amp * math.sin(r * 0.18 + ph) + 2.2 * math.sin(r * 0.05 + ph * 2.0)
        cx = base_x + math.cos(perp) * wander
        cy = base_y + math.sin(perp) * wander

        for y in range(H2):
            for x in range(W):
                d = abs(math.hypot(x - cx, y - cy))                # distance to fin centerline
                if d > 3.2:
                    continue
                h = (1.0 - d / 3.2) * radius_decay                 # cross-section falloff -> rounded ridge
                h = max(0.0, min(1.0, h + 0.10 * (noise(x, y) - 0.5)))
                if h < 0.12:
                    continue
                fg = warm_fg(h, r * 0.30 + x * 0.08 + fi)
                if h > 0.86 and d < 1.0 and t < 0.35:             # white-hot core only at the inner end near the heart
                    fg = 15
                set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 4 -- EMBER SCATTER (the "different ember behavior"): sparse bright embers scattered
#   RADIALY. Each rides a fin's direction with lateral jitter and cools as it travels outward --
#   radial scatter with cooling trails, not FORGE's vertical drift. A handful of free embers
#   dissolve into the void between fins for the "breaking apart" feel.
# ===========================================================================
for fi in range(NFINS):
    ang, reach, amp, ph = FINS[fi]
    n_embers = 14 + (fi % 3) * 5                                  # per-fin ember count, slightly varied
    for _ in range(n_embers):
        r = random.uniform(CORE_R, reach + 6)                     # scatter out along the fin's radius
        t = max(0.0, min(1.0, (r - CORE_R) / max(1.0, reach - CORE_R)))
        h = max(0.0, 1.0 - t * 0.92)                              # cools as it travels outward
        if h < 0.18:
            continue
        base_x = CX + r * math.cos(ang)
        base_y = CY + r * math.sin(ang)
        perp = ang + math.pi / 2.0
        jitter = round(3.0 * math.sin(r * 0.3 + fi)) + random.uniform(-1.6, 1.6)   # lateral wobble as it scatters
        x = int(base_x + math.cos(perp) * jitter)
        y = int(base_y + math.sin(perp) * jitter)
        if not (0 <= x < W and 0 <= y < H2 - 3):
            continue
        fg = 15 if h > 0.82 else warm_fg(h, r * 0.4 + fi)
        if random.random() < 0.6:
            set_cell(cv, x, y, RAMP[0] if h > 0.7 else heat_to_density(h), fg)

# a handful of free embers dissolving into the void between fins (not tied to any fin)
for _ in range(34):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(CORE_R + 2, CORE_R + 26)
    ex = int(CX + r * math.cos(ang))
    ey = int(CY + r * math.sin(ang))
    if not (0 <= ex < W and 0 <= ey < H2 - 3):
        continue
    t = max(0.0, min(1.0, (r - CORE_R) / 26.0))
    h = max(0.0, 1.0 - t * 0.95)
    if h < 0.22:
        continue
    fg = 15 if h > 0.85 else warm_fg(h, r * 0.4 + ex)
    if random.random() < 0.5:
        set_cell(cv, ex, ey, heat_to_density(h), fg)

# ===========================================================================
# emit -- top title card matching FORGE/MONOLITH's framing (QUENCH is the third member of the
#   molten set; frame it identically so the set reads as a coherent family), then canvas, then sig.
# ===========================================================================
out = []
render(cv, out)

def framed_into(lst, title):
    lst.append("")
    pad = W - len(title); left = pad // 2
    lst.append(c(104, 0) + " " * left + c(97, 0) + title + c(104, 0) + " " * (pad - left))

title_block = []
framed_into(title_block, "QUENCH // conflagration radiating out of the dark")
title_block.append(c(94, 0) + ("  heat cracking outward from a white-hot heart -- lit out of the dark").center(W).ljust(W) + "\x1b[0m")
title_block.append("")

sig = []
sig_block(sig, "QUENCH // CONFLAGRATION v3.0", handles="raze")

final = title_block + out + sig
raw = "\n".join(final) + "\x1b[0m\n"
with open(OUT, "w", encoding="cp437") as f:
    f.write(raw)
print("wrote", OUT, "rows:", len(final))
