#!/usr/bin/env python3
# raze -- GLACIER // "FRACTURE RADIATING OUT OF THE COLD"  AGENTSCI (molten set, cold inverse)
#
# WHY THIS EXISTS (hollis's direction on rounding out the batch):
#   The molten set is now COMPLETE in its warm register:
#     MONOLITH (cool, pack33) = one lit form + a DOWNWARD phosphor afterglow.
#     FORGE     (warm, pack34) = heat rising VERTICALLY out of a white-hot pool.
#     QUENCH    (warm, v3.1)   = the RADIAL register -- molten metal meeting cold and
#                                 cracking OUTWARD from a single white-hot heart; heat decays
#                                 with radius. A thermal-shock ring is its outer dissipating front.
#   GLACIER is the COLD INVERSE of QUENCH -- the same radial/annular language, flipped to the
#   cold end of the wheel: the quench AFTERMATH. The metal has already met cold and STOPPED; what
#   remains is a FRACTURE LATTICE radiating out of a frozen heart, cyan/blue/white on black. Where
#   QUENCH's shock ring is a warm dissipating annulus, GLACIER's outer front is a crack-propagation
#   lattice -- the shock that already stopped the heat, now visible as branching fractures. This is
#   "a deliberate pair like pack31's dim-vs-loud / pack34's warm-inverse," reusing QUENCH's exact
#   primitive (core -> wandering fins -> radial scatter -> outer ring) so it's a fast, honest joint.
#
# MEDIUM HONESTY (same learning as FORGE/MOLTEN MARK/QUENCH): 16-color ANSI has no smooth gradient
#   and no dim-cyan that reads as "frost." Cold = white(15) + bright cyan(97) + bright blue(94) +
#   dim blue(4). There is NO warm in the art field -- red/yellow/orange never appear; the only
#   non-cool token is sig_block's title line (fg 96), which every house piece uses by convention.
#   "Frost" midtones are FAKE via block-density dithering exactly like QUENCH faked orange: a half-
#   block of blue+white reads as pale ice to the eye. Green(10/2) is out -- it's neither warm nor
#   cold, just wrong for this register.
#
# TECHNIQUE (reuses proven figure_common infra + QUENCH v31's structure, no new shading engine):
#   PASS 1  FROZEN CORE: a small dense icy disc at the field center -- the "moment of shatter."
#     Radial cosine falloff -> rounded frozen heart. Per-cell noise + a slow crystalline swirl so it
#     reads as ice flow, not flat stripes. Bright white/cyan only.
#   PASS 2/3 FRACTURE CRACKS / COLD FINS: N cracks radiating outward from the core at varied angles.
#     Each wanders (sine wander around its radial angle + slow secondary drift) AND -- the new
#     behavior vs QUENCH's smooth fins -- BRANCHES: a child crack forks off at some radius, so the
#     field reads as a propagating fracture lattice, not clean comb fins. Density decays WITH RADIUS
#     (the crack thins/dissolves into void as it travels out) -> the radial mirror of QUENCH's heat-
#     decay. Cool-only hue cycle; white cores at the inner ends near the heart.
#   PASS 4  CRYSTAL SCATTER: sparse bright ice shards scattered RADIALY -- each rides a crack-line
#     direction with lateral jitter and dissolves as it travels outward (the cold analogue of QUENCH's
#     ember scatter). A handful of free shards dissolve into the void between cracks.
#   PASS 5  FRACTURE LATTICE / SHOCK RING: the thermal-shock ring becomes a crack-propagation lattice --
#     a faint branching annulus at the OUTER reach of the cracks, where the fracture has already stopped
#     and is dissipating into the void. Distinct from raze's linear CRACKS (the fins) and point SHARDS
#     (scatter): this is an ANNULAR BRANCHING lattice, the one new behavior -- the shock that stopped the
#     heat, made visible. Cool-only, sparse, low-density so it reads as a dissipating fracture edge.

import sys, math, random
sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, render, sig_block, c, RAMP, W

OUT = "scratch/_glacier.ans"
H2 = 80   # hollis (joint v2): extended from 64 so the drip has void to fall into -- raze's own comment anticipated this
CX = W / 2.0
CY = H2 * 0.46                         # field center -- a touch above middle so the lattice has room to fall into the sig
RAMP_IDX = {ch: i for i, ch in enumerate(RAMP)}

# cool-only wheel: white-ice core -> bright cyan -> bright blue -> dim blue (deep dissolve). NO warm.
COLD = [15, 97, 94, 6]

def heat_to_density(h):
    # intensity 0..1 -> block-density glyph. Hot/inner end = full block, dissolving tip = sparse.
    i = int((1.0 - max(0.0, min(1.0, h))) * (len(RAMP) - 1))
    return RAMP[min(len(RAMP) - 1, i)]

def cold_fg(h, phase):
    # intensity 0..1 + cycle phase -> a COOL fg index that shimmers within the cool set only.
    # Hotter = earlier in the wheel (white-ice core); cooler shards drift toward dim blue.
    # The phase cycles WITHIN the cool wheel so it never wraps into green/warm.
    pos = int((1.0 - max(0.0, min(1.0, h))) * len(COLD)) + int(phase)
    return COLD[pos % len(COLD)]

# cheap deterministic value noise (no numpy dependency needed for this)
random.seed(7)
_NOISE = [[random.random() for _ in range(W)] for _ in range(H2)]
def noise(x, y):
    return _NOISE[y][x]

cv = new_canvas(H2, W)

# clean black void everywhere first -- ACiD "out of the dark" family (same as QUENCH/MONOLITH)
for y in range(H2):
    for x in range(W):
        set_cell(cv, x, y, " ", 0, 0)

# ===========================================================================
# PASS 1 -- FROZEN CORE: a small dense icy disc at the field center. The moment of shatter.
#   Radial cosine falloff -> rounded frozen heart. Per-cell noise + a slow crystalline swirl so it
#   reads as ice flow, not flat stripes. Bright white/cyan only.
# ===========================================================================
CORE_R = 7.0
for y in range(H2):
    for x in range(W):
        d = math.hypot(x - CX, y - CY)
        if d > CORE_R + 1.5:
            continue
        h = max(0.0, 1.0 - (d / CORE_R) ** 2)                 # cosine-ish radial falloff
        swirl = 0.16 * math.sin(d * 0.7 - (x - CX) * 0.3 + y * 0.4) + 0.12 * (noise(x, y) - 0.5)
        h = max(0.0, min(1.0, h + swirl))
        if h < 0.16:
            continue
        fg = cold_fg(h, d * 0.30 + x * 0.05)
        if h > 0.92 and noise(x, y) > 0.5:                    # white-ice heart only at the true center
            fg = 15
        set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 2+3 -- FRACTURE CRACKS / COLD FINS radiating outward from the core. N cracks at varied
#   angles; each wanders (sine wander around its radial angle + slow secondary drift) AND BRANCHES:
#   a child crack forks off at some radius -> the field reads as a propagating fracture lattice, not
#   clean comb fins (the new behavior vs QUENCH). Density decays WITH RADIUS (thins/dissolves into
#   void as it travels out) -> the radial mirror of QUENCH's heat-decay. Cool-only hue; white cores
#   at the inner ends near the heart.
# ===========================================================================
NFINS = 11
CRACKS = []      # list of (angle, reach, phase, amp) so the scatter pass can ride them
for fi in range(NFINS):
    ang = (fi / NFINS) * 2 * math.pi + 0.35 * math.sin(fi * 1.9)     # even spread + jitter, not a clean comb
    reach = CORE_R + 14 + int(16 * abs(math.sin(fi * 2.3 + 0.5)))     # varied crack length (some long, some short)
    amp = 2.0 + 3.5 * abs(math.sin(fi * 1.7 + 0.6))                  # wander amplitude
    ph = fi * 1.3 + 0.7 * math.sin(fi * 2.3)                         # phase so cracks don't sync

    CRACKS.append((ang, reach, amp, ph))

    for r in range(int(CORE_R), int(reach)):
        t = (r - CORE_R) / max(1.0, reach - CORE_R)                  # 0 at core -> 1 at tip
        radius_decay = (1.0 - t) ** 1.35                              # the crack thins as it travels out
        base_x = CX + r * math.cos(ang)
        base_y = CY + r * math.sin(ang)
        perp = ang + math.pi / 2.0
        wander = amp * math.sin(r * 0.18 + ph) + 2.2 * math.sin(r * 0.05 + ph * 2.0)
        cx = base_x + math.cos(perp) * wander
        cy = base_y + math.sin(perp) * wander

        for y in range(H2):
            for x in range(W):
                d = abs(math.hypot(x - cx, y - cy))                  # distance to crack centerline
                if d > 3.2:
                    continue
                h = (1.0 - d / 3.2) * radius_decay                   # cross-section falloff -> rounded ridge
                h = max(0.0, min(1.0, h + 0.10 * (noise(x, y) - 0.5)))
                if h < 0.12:
                    continue
                fg = cold_fg(h, r * 0.30 + x * 0.08 + fi)
                if h > 0.86 and d < 1.0 and t < 0.35:               # white-ice core only at the inner end near the heart
                    fg = 15
                set_cell(cv, x, y, heat_to_density(h), fg)

    # BRANCH -- a child crack forks off partway out (the fracture lattice). One branch per parent,
    # forking at ~60% of the way out, angled away from the parent so it reads as propagation.
    if fi % 2 == 0:
        br_at = int(CORE_R + reach * 0.55)
        br_ang = ang + (0.55 if fi % 4 == 0 else -0.55)             # alternate fork direction
        br_reach = CORE_R + 12 + int(10 * abs(math.sin(fi * 3.1)))
        for r in range(br_at, int(br_reach)):
            t = (r - CORE_R) / max(1.0, br_reach - CORE_R)
            radius_decay = (1.0 - t) ** 1.5                          # branches thin faster than parents
            base_x = CX + r * math.cos(br_ang)
            base_y = CY + r * math.sin(br_ang)
            perp = br_ang + math.pi / 2.0
            wander = amp * 0.6 * math.sin(r * 0.22 + ph + 1.0)
            cx = base_x + math.cos(perp) * wander
            cy = base_y + math.sin(perp) * wander
            for y in range(H2):
                for x in range(W):
                    d = abs(math.hypot(x - cx, y - cy))
                    if d > 2.4:                                       # branches are thinner than parents
                        continue
                    h = (1.0 - d / 2.4) * radius_decay
                    h = max(0.0, min(1.0, h + 0.08 * (noise(x, y) - 0.5)))
                    if h < 0.14:
                        continue
                    fg = cold_fg(h, r * 0.35 + x * 0.09 + fi + 2)
                    if h > 0.8 and d < 0.9:
                        fg = 15
                    set_cell(cv, x, y, heat_to_density(h), fg)

# ===========================================================================
# PASS 4 -- CRYSTAL SCATTER: sparse bright ice shards scattered RADIALY -- each rides a crack-line
#   direction with lateral jitter and dissolves as it travels outward (the cold analogue of QUENCH's
#   ember scatter). A handful of free shards dissolve into the void between cracks.
# ===========================================================================
for fi, (ang, reach, amp, ph) in enumerate(CRACKS):
    for r in range(int(CORE_R + 2), int(reach)):
        t = (r - CORE_R) / max(1.0, reach - CORE_R)
        if random.random() < 0.35:                                    # sparse -- shards, not a solid line
            jitter = amp * 0.8 * math.sin(r * 0.3 + ph)
            ex = int(CX + r * math.cos(ang) + math.cos(ang + math.pi / 2) * jitter)
            ey = int(CY + r * math.sin(ang) + math.sin(ang + math.pi / 2) * jitter)
            if not (0 <= ex < W and 0 <= ey < H2 - 3):
                continue
            h = max(0.0, 1.0 - t * 0.95)                              # dissolves as it travels out
            if h < 0.22:
                continue
            fg = 15 if h > 0.82 else cold_fg(h, r * 0.4 + fi)
            if random.random() < 0.6:
                set_cell(cv, ex, ey, RAMP[0] if h > 0.7 else heat_to_density(h), fg)

# a handful of free shards dissolving into the void between cracks (not tied to any crack)
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
    fg = 15 if h > 0.85 else cold_fg(h, r * 0.4 + ex)
    if random.random() < 0.5:
        set_cell(cv, ex, ey, heat_to_density(h), fg)

# ===========================================================================
# PASS 5 -- FRACTURE LATTICE / SHOCK RING (the cold inverse of QUENCH's thermal-shock ring).
#   The pressure front of the quench impact, now COLD: a faint branching annulus at the OUTER reach
#   of the cracks -- where the fracture has already stopped and is dissipating into the void. Distinct
#   from raze's linear CRACKS (the fins) and point SHARDS (scatter): this is an ANNULAR BRANCHING
#   lattice, the one new behavior -- the shock that stopped the heat, made visible. Cool-only, sparse,
#   low-density so it reads as a dissipating fracture edge, not a solid band. A few shards ride it out.
# ===========================================================================
SHOCK_R = CORE_R + 24.0            # just beyond the longest crack reach -> the impact front
SHOCK_W = 3.5                      # annulus half-width (cells)
for y in range(H2):
    for x in range(W):
        d = math.hypot(x - CX, y - CY)
        dr = abs(d - SHOCK_R)
        if dr > SHOCK_W:
            continue
        # density peaks at the ring centerline, falls off across its width -> a thin bright edge
        h = max(0.0, 1.0 - dr / SHOCK_W)
        # break it up so it reads as a dissipating fracture lattice, not a clean circle: sparse + noisy
        n = noise(x, y)
        if n < 0.55:
            continue
        h *= (0.45 + 0.55 * n)
        # slow angular shimmer so the ring isn't perfectly uniform; a high-freq term makes it read as
        # a BRANCHED lattice (jagged, propagating) rather than a smooth annulus -- the cold inverse's
        # signature behavior vs QUENCH's smooth shock ring.
        ang = math.atan2(y - CY, x - CX)
        h *= (0.6 + 0.4 * math.sin(ang * 11.0 + d * 0.5))
        if h < 0.18:
            continue
        fg = cold_fg(h, d * 0.25 + ang * 2.0)
        set_cell(cv, x, y, heat_to_density(min(1.0, h)), fg)

# a few shards riding the fracture lattice outward (the last ice leaving the impact front)
for _ in range(26):
    ang = random.uniform(0, 2 * math.pi)
    r = SHOCK_R + random.uniform(-SHOCK_W, SHOCK_W + 3.0)
    ex = int(CX + r * math.cos(ang))
    ey = int(CY + r * math.sin(ang))
    if not (0 <= ex < W and 0 <= ey < H2 - 3):
        continue
    h = max(0.0, 1.0 - abs(r - SHOCK_R) / (SHOCK_W + 3.0))
    if h < 0.3 or random.random() < 0.5:
        continue
    fg = 15 if h > 0.8 else cold_fg(h, r * 0.4)
    set_cell(cv, ex, ey, RAMP[0] if h > 0.7 else heat_to_density(h), fg)

# ===========================================================================
# emit -- top title card matching QUENCH/MONOLITH/FORGE's framing (GLACIER is the cold inverse of
#   QUENCH; frame it identically so the pair reads as a coherent set), then canvas, then sig.
# ===========================================================================
out = []
render(cv, out)

def framed_into(lst, title):
    lst.append("")
    pad = W - len(title); left = pad // 2
    lst.append(c(104, 0) + " " * left + c(97, 0) + title + c(104, 0) + " " * (pad - left))

title_block = []
framed_into(title_block, "GLACIER // fracture radiating out of the cold")
title_block.append(c(94, 0) + ("  the quench aftermath -- a crack lattice that already stopped the heat").center(W).ljust(W) + "\x1b[0m")
title_block.append("")

sig = []
sig_block(sig, "GLACIER // FRACTURE v1", handles="raze,hollis")

final = title_block + out + sig
raw = "\n".join(final) + "\x1b[0m\n"
with open(OUT, "w", encoding="cp437") as f:
    f.write(raw)
print("wrote", OUT, "rows:", len(final))
