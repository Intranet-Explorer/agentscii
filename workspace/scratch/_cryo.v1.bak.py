#!/usr/bin/env python3
# _cryo.py -- raze solo. THE CRYO // "the vessel that stopped."
#
# PROVENANCE / WHY NEW: pack43's hot-plasma family is REACTOR (vertical vessel, radial HOT
# core) + TURBINE (horizontal capsule, axial intake) + CONSOLE (flat dashboard, emissive).
# hollis flagged the open move as a 4th piece that BREAKS the family on a THIRD axis -- not a
# reskin. The third axis is TEMPERATURE: reactor/turbine are hot, console is neutral; THE CRYO
# is the COLD odd-one-out. It is THE REACTOR's deliberate cold inverse -- SAME vertical vessel
# silhouette + SAME radial core light + SAME bilateral-mirror signature move (honest reuse of
# raze's own infra, like GLACIER reused QUENCH's), but the palette flips to frozen blue-white
# and it adds a primitive reactor lacks: a radiating FROST LATTICE off the core.
#
# FAMILY PLACEMENT: this is the machine-body twin of GLACIER (pack37, the molten set's cold
# inverse -- an abstract fracture lattice). GLACIER = the shatter as pure field; THE CRYO = the
# shatter INSIDE a containment vessel. Together they read as "the quench aftermath" in two
# registers (abstract + machine), so the cold thread runs through both families.
#
# BREAKS ON TWO AXES vs REACTOR (so it's not a reskin):
#   (1) TEMPERATURE / PALETTE: frozen blue-white {4,6,7,8}+{12,14,15}, ZERO warm fg in the art
#       field -- vs reactor's amber/red hot plasma. The whole point.
#   (2) LIGHT BEHAVIOR: the core doesn't radiate HEAT outward; it FRACTURES -- a jagged frost
#       lattice of spokes shoots off the frozen heart and dissolves into the void (GLACIER idiom),
#       vs reactor's smooth radial heat-shimmer bloom. Cold stops; hot spreads.
#
# SIGNATURE MOVE: paint x < MID only, mirror(axis='v') copies it right -> perfect bilateral
# symmetry for free. Light is RADIAL from the frozen core (CX,CORE_Y) so the vessel glows out of
# black and the falloff reads as a lit mass. Then a NEW pass: frost spokes radiate off the core
# in jagged, wandering directions -- the cold inverse of reactor's smooth heat bloom.
#
# PASSES (METHODOLOGY), verified by eye with preview_piece at each:
#   P1 flat silhouettes -> verify massing; P2 radial shade every surface from the ONE core source;
#   P3 constructed accents (frozen plasma column, frost lattice spokes, valve ports, glass sheen);
#   MIRROR(axis='v'); P4 texture the void around the vessel; P5 frame + title card.
#
# COLOR CALIBRATION GOTCHA (METHODOLOGY Pass 1): pass PLAIN 0-7 hue indices to cv.set / shade --
# NOT pre-encoded SGR codes. U+2582 is not CP437; use U+2580/U+2591 for thin frost lines.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, RAMP, write_ans
from figure_common import light_field, shade, c, RESET

W, H = 80, 52
cv = Canvas(W, H)
CX = W / 2.0
MID = W // 2
SEED = 11
random.seed(SEED)

# frozen core: the light source + center of mass (slightly above mid so the vessel reads tall)
CORE_X, CORE_Y = CX, 25.0
LX, LY = CORE_X, CORE_Y            # ONE radial source for the whole piece

def L(x, y):
    return light_field(x, y, LX, LY, lmax=34.0, ambient=0.10)

# ---- P1: silhouette region functions (the ANATOMY as massing), LEFT HALF ONLY --
# Same vessel anatomy as reactor; the cold register lives in the palette + the frost pass.

def vessel(x, y):
    cy = CORE_Y
    ry = 17.0           # half-height of the rounded end
    rx = 8.5            # half-width of the body
    top_cap = cy - ry
    bot_cap = cy + ry
    if y < top_cap or y > bot_cap:
        return False
    if top_cap <= y <= bot_cap:
        return abs(x - CX) <= rx
    t = (y - cy) / ry
    hw = rx * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(x - CX) <= hw

def plasma(x, y):
    cy = CORE_Y
    ry = 15.0
    if (y - cy) / ry < -1.0 or (y - cy) / ry > 1.0:
        return False
    t = (y - cy) / ry
    hw = 2.4 * math.sqrt(max(0.0, 1.0 - t * t)) + 0.8
    return abs(x - CX) <= hw

def fins(x, y):
    cy = CORE_Y
    ry = 15.0
    if (y - cy) / ry < -1.0 or (y - cy) / ry > 1.0:
        return False
    fin_ys = [CORE_Y + k * 4.5 for k in range(-3, 4)]    # 7 fins stacked vertically
    for k, fy in enumerate(fin_ys):
        if abs(y - fy) <= 0.8:
            inner = 6.0
            outer = 17.0 - (k % 2) * 3.5
            if inner <= abs(x - CX) <= outer:
                return True
    return False

def base(x, y):
    cy = CORE_Y + 18.5
    t = (y - cy) / 4.5
    if abs(t) > 1.0:
        return False
    hw = 24.0 * math.sqrt(1.0 - t * t)
    return abs(x - CX) <= hw

def dome(x, y):
    cy = CORE_Y - 17.0
    d = math.hypot(x - CX, y - cy)
    return d <= 4.2

def ports(x, y):
    d = math.hypot(x - CX, y - CORE_Y)
    if 9.0 <= d <= 10.5:
        ang = math.atan2(y - CORE_Y, x - CX)
        return abs(math.sin(ang * 8.0)) < 0.30
    return False

# ---- P1: paint flat silhouettes (dim gray, unlit) to verify massing ----------
def paint_flat(region_fn, fg=8):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                cv.set(x, y, "\u2588", fg, 0)

paint_flat(vessel, fg=4)
paint_flat(fins, fg=8)
paint_flat(dome, fg=6)
paint_flat(base, fg=7)
paint_flat(ports, fg=14)
paint_flat(plasma, fg=15)

# ---- P2: radial shade every lit surface from the ONE core source -------------
def shade_region(region_fn, base_fg, hot_fg):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                ch, fg = shade(L(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

shade_region(vessel, base_fg=4, hot_fg=7)             # chamber: cold BLUE steel (4), white at the core seam (7)
shade_region(fins,   base_fg=8, hot_fg=6)             # fins: dim blue plates (8), cyan sheen near core (6) -- frost-plate read
shade_region(dome,   base_fg=4, hot_fg=7)             # cap: cold blue housing (4), white at the top seam (7)
shade_region(base,   base_fg=8, hot_fg=8)              # pedestal: dim gray floor, recedes into void

# ---- P3: constructed bright accents ------------------------------------------
# frozen plasma column: white-hot heart with cyan falloff -- the core, drawn on top.
for y in range(H):
    for x in range(MID):
        if plasma(x, y):
            d = math.hypot(x - CX, y - CORE_Y)
            Lc = light_field(x, y, LX, LY, lmax=10.0, ambient=0.2)
            ch, fg = shade(Lc, base_fg=6, hot_fg=7)     # cyan body (6) -> white at the very center (7)
            cv.set(x, y, ch, fg, 0)
            if abs((y - CORE_Y)/15.0) > 0.80:           # shatter tips where the column freezes solid
                cv.set(x, y, ch, 15, 0)

# valve ports: cyan glass sheen (the frost-rimmed valves against the blue vessel)
for y in range(H):
    for x in range(MID):
        if ports(x, y):
            cv.set(x, y, "\u2593", 6, 0)

# P3b: specular sheen down each fin's light-facing (inner/core-facing) edge so fins read as
# PLATES catching the core light, not flat bars. Light is at the core, so the lit side faces in.
for fy in [CORE_Y + k * 4.5 for k in range(-3, 4)]:
    for t in [i / 10.0 for i in range(11)]:
        px = CX + (22.0 - t * 16.0)       # inner->outer along the fin
        py = fy
        cv.set(int(px), int(py), "\u2588", 6, 0)        # cyan sheen stripe on the core-facing edge

# core bloom: a faint ring of light around the plasma heart so it glows, not just dots
for y in range(H):
    for x in range(MID):
        d = math.hypot(x - CX, y - CORE_Y)
        if 2.6 < d <= 4.4:
            cv.set(x, y, "\u2592", 6, 0)

# ---- P3c: FROST LATTICE -- the NEW primitive (cold inverse of reactor's heat bloom) ----
# Jagged spokes radiate off the frozen core in wandering directions and dissolve into the void.
# This is GLACIER's fracture idiom, here as a machine's shatter: cold STOPS and cracks outward,
# it doesn't spread as smooth heat. Each spoke wanders (sine drift) and thins with radius; every
# other spoke branches a child crack at ~50% reach. Cool wheel only {6,14,7} -> white tips.
def frost_spokes():
     """The signature NEW primitive: a FROST LATTICE -- the cold inverse of reactor's smooth heat
    bloom. The shatter ESCAPES the containment: dominant white cracks start just past the fin
    reach (r ~ 19) and radiate out into the open void ring as near-continuous lines, so each reads
    as a clean fracture line, not noise. All spokes point LEFTWARD (cos<0); mirror(axis='v') then
    copies them to the right -- so the lattice is perfectly bilateral by construction. Three tiers:
      DOMINANT    -- few, long, near-continuous WHITE lines from the surface outward (the main shatter).
      SECONDARY   -- more, cyan, slightly broken, shorter (the branching network between the mains).
      HAIR        -- fine dim-blue, sparse, far out only (the dissolving fringe at the reach).
    Each crack wanders gently and thins with radius; dominant + secondary branch a child crack near
    their outer end. Cool wheel only {6,14,7} -> white tips. Drawn LAST so it sits on top of the
    shimmer/bloom field and reads as a distinct radiating shatter over the ambient void."""
    def crack(ang, r0, reach, wander, phase, ch_near, fg_near, ch_far, fg_far, skip):
        for r in range(r0, int(reach)):
            t = (r - r0) / max(1.0, reach - r0)
            if random.random() < skip * t:                  # thins/dissolves as it travels out
                continue
            wx = math.cos(ang) * r + math.sin(r * 0.35 + phase) * wander * (1.0 - t)
            wy = math.sin(ang) * r + math.cos(r * 0.4 + phase) * wander * (1.0 - t)
            px = int(round(CX + wx))
            py = int(round(CORE_Y + wy))
            if not (0 <= px < MID and 0 <= py < H):
                continue
            if in_mass(px, py) or (px, py) in _occ:         # frost lives in the void, on top of nothing
                continue
            ch = ch_far if t > 0.7 else ch_near
            fg = fg_far if t > 0.6 else fg_near
            cv.set(px, py, ch, fg, 0)
                # branch a child crack off near the outer end, angled away, thinning fast
            if abs(r - int(reach * 0.72)) <= 1:
                bang = ang + random.uniform(0.35, 0.7) * (1 if k % 2 else -1)
                for rr in range(1, int((reach - r) * 0.6)):
                    bx = math.cos(bang) * rr
                    by = math.sin(bang) * rr
                    bpx = int(round(CX + wx + bx))
                    bpy = int(round(CORE_Y + wy + by))
                    if not (0 <= bpx < MID and 0 <= bpy < H):
                        continue
                    if in_mass(bpx, bpy) or (bpx, bpy) in _occ:
                        continue
                    cv.set(bpx, bpy, ch_far, fg_far, 0)

    n = 14
    for k in range(n):
        # all spokes point LEFTWARD: ang in (pi/2, pi), evenly spread, jittered -- mirror handles right
        ang = math.pi / 2.0 + (k + 0.5) * (math.pi / n) + random.uniform(-0.06, 0.06)
        phase = random.uniform(0.0, math.pi * 2)
        reach = 34.0 + random.uniform(-2.0, 5.0)
        wander = random.uniform(0.4, 0.9)
        if k % 3 == 0:                                               # DOMINANT white lines from just past the fins outward
            crack(ang, 19, reach, wander, phase, "\u2580", 15, "\u2580", 14, skip=0.05)
        elif k % 3 == 1:                                             # SECONDARY cyan network between the mains
            crack(ang, 21, reach * 0.8, wander, phase, "\u2591", 14, "\u2591", 6, skip=0.14)
        else:                                                        # HAIR -- fine dim-blue fringe far out only
            crack(ang + 0.13, 23, reach * 0.7, wander * 1.3, phase, "\u2580", 6, "\u2591", 6, skip=0.28)


# ---- MIRROR: the signature move -- copy left half onto right -----------------
mirror(cv, axis='v')

# ---- P4: texture the void around the mass (not flat black) -------------------
def in_mass(x, y):
    return (vessel(x, y) or fins(x, y) or dome(x, y)
            or base(x, y) or ports(x, y) or plasma(x, y))

# Occupied-set guard: every cell painted so far. The FROST LATTICE is drawn LAST, on top of
# the shimmer/bloom, and skips occupied cells -- so it reads as a distinct radiating shatter
# OVER the ambient field instead of blurring into it (the v1 bug: frost was painted before the
# texture pass and got buried). cv.set is wrapped to record occupancy.
_occ = set()
_real_set = cv.set
def _set(x, y, ch, fg, bg):
    _real_set(x, y, ch, fg, bg)
    _occ.add((x, y))
cv.set = _set

# P4a: gray cold-shimmer dust far out (the chamber's frozen atmosphere), not flat black.
texture_fill(cv, lambda x, y: not in_mass(x, y), fg=8, density=0.26, seed=SEED + 1)
for y in range(H):
    for x in range(MID):
        if in_mass(x, y):
            continue
        d = math.hypot(x - CX, y - CORE_Y)
         # P4b: radial cold bloom -- cool cyan near the core thinning to gray at the edges.
        if 4.4 < d <= 30.0:
            Lb = light_field(x, y, LX, LY, lmax=30.0, ambient=0.06)
            p = Lb * 0.55 if d < 12 else Lb * 0.30
            if random.random() < p:
                ch = "\u2591" if d < 14 else ("\u2592" if random.random() < 0.4 else "\u2591")
                cv.set(x, y, ch, 6 if d < 8 else (7 if d < 14 else 8), 0)

# ---- P3c LATE: FROST LATTICE -- the signature NEW primitive, drawn on top of everything ----
frost_spokes()

# ---- P5: frame + title card --------------------------------------------------
out = []
out.append(c(13) + "\u2554" * W)            # top rule (magenta chrome, house convention)
cv.render(out)                                # body rows appended in place
out.append(c(13) + "\u2557" * W)             # bottom rule

write_ans("_cryo.ans", out, title="THE CRYO v1.0", handles="raze", add_sig=True)
print("wrote scratch/_cryo.ans")