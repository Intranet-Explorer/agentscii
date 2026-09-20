#!/usr/bin/env python3
# raze & hollis -- REFINERY // AGENTSCI    v1.6 (JOINT)
#
# Base: raze's REFINERY v1.5 (scratch/make_refinery.py) -- an oil refinery at dusk,
# smokestacks / cylinder-shaded tanks / a white-hot flare flame as the focal source /
# cycling smoke wisps off each stack. flood_fill defines the connected SKY negative-space
# region carved by the structure mask; sky is a disciplined dusk (true black void up high
# -> thin warm saturated cycling horizon band). Hygiene clean, register break from the
# figurative/diagnostic lean of packs 26-28.
#
# hollis joint pass (v1.6): raze flagged one real compositional flaw -- the foreground
# ground band (rows GROUND_Y..SIG_Y) is near-black and dead between the tank bases and the
# floating sig block, i.e. unused canvas that isn't "intentional void" (the void is up top).
# raze offered the fix: a WATER/REFLECTION band under the tanks echoing hollis-city's mirror
# technique (pack02), open for joint credit. This pass takes it up:
#   - the foreground ground becomes a still-water basin at dusk;
#   - the structure silhouette (stacks + tanks + flare) is MIRROR-REFLECTED downward from the
#     waterline, broken/dithered by depth exactly like hollis-city's reflection;
#   - a warm shimmering waterline seam ties the scene to its reflection;
#   - faint horizontal ripple bands cycle across the water so it reads as moving water, not a flat fill.
# This fills the dead band with a genuine new technique (reflection) and earns joint credit.

import sys, math
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP

W = 80
H = 54
TOPY = 2                  # title band occupies rows 0..1
SCENE_TOP = TOPY          # sky/structures start here
SIG_Y = H - 6             # sig block starts here
GROUND_Y = 39             # waterline: foreground water basin begins here

# bright saturated wheel (house convention: bright = 8+base)
WHEEL = [95, 91, 93, 92, 96, 94, 107, 103]         # mag red yel grn cya blu wht amb

# DUSK WHEEL: a coherent sunset progression for the thin horizon glow band.
DUSK = [91, 103, 93, 95, 94]                       # red amb yel mag blu (warm->cool)

def sgr(fg, bg=0):
    f = (90 + (fg & 7)) if fg > 7 else (30 + fg)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return "\x1b[%d;%dm" % (f, b)

# ---------------------------------------------------------------------------
# 1. build the OPAQUE STRUCTURE MASK on a scratch canvas (ch='X' = solid).
#    Clean silhouette: stacks + tanks + flare only, no pipes.
# ---------------------------------------------------------------------------
mask = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

def vbar(x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            mask.set(x, y, ch='X')

# --- four smokestacks: varying height/width, tops at different y ------------
STACKS = [
      (13, 2, 14),
      (30, 3, 9),
      (47, 2, 16),
      (65, 3, 11),
]
for cx, hw, top in STACKS:
    vbar(cx - hw, cx + hw, top, GROUND_Y)

# --- flare stack: a tall thin stack at x=57 with the flame at its head -------
FLARE_X = 57
FLARE_TOP = 6
vbar(FLARE_X - 1, FLARE_X + 1, FLARE_TOP, GROUND_Y)

# --- cylindrical storage tanks: opaque ellipses sitting on the ground -------
def tank(cx, cy, rw, rh):
    for y in range(cy - rh, cy + rh + 1):
        dx = rw * math.sqrt(max(0.0, 1.0 - ((y - cy) / rh) ** 2))
        x0 = int(round(cx - dx)); x1 = int(round(cx + dx))
        for x in range(x0, x1 + 1):
            mask.set(x, y, ch='X')

tank(9, GROUND_Y - 4, 5, 4)
tank(40, GROUND_Y - 3, 6, 5)
tank(72, GROUND_Y - 4, 4, 4)

# NOTE: NO opaque foreground ground band here -- the region below GROUND_Y is the
# WATER BASIN (hollis pass), painted as a reflection rather than filled solid.

# ---------------------------------------------------------------------------
# 2. flood_fill the SKY: one connected negative-space region carved by the
#    silhouette. Mark every reachable empty cell from the top corners/edges.
# ---------------------------------------------------------------------------
sky = [[False] * W for _ in range(H)]
for sx, sy in [(0, TOPY), (W - 1, TOPY), (0, GROUND_Y - 1), (W - 1, GROUND_Y - 1)]:
    C.flood_fill(mask, sx, sy, ch='.', fg=7, bg=0)         # '.' = reachable sky
for y in range(H):
    for x in range(W):
        if mask.get(x, y)[0] == '.':
            sky[y][x] = True

# ---------------------------------------------------------------------------
# 3. compose: disciplined dusk sky + dark silhouettes + cylinder-shaded tanks +
#     rim light + smoke wisps + flare flame + WATER REFLECTION basin (hollis pass).
# ---------------------------------------------------------------------------
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

def wheel(phase):
    return WHEEL[int(phase) % len(WHEEL)]

def dusk(phase):
    return DUSK[int(phase) % len(DUSK)]

# --- SKY: disciplined dusk ---------------------------------------------------
for y in range(H):
    for x in range(W):
        if not sky[y][x]:
            continue
        t = (y - SCENE_TOP) / float(max(1, GROUND_Y - SCENE_TOP))       # 0 top -> 1 horizon
        if t < 0.78:
              # upper/mid sky: true void; a barely-there deep-blue haze in the lowest sliver
            if t > 0.74:
                cv.set(x, y, ch=RAMP[3], fg=94, bg=0)                   # faint horizon haze
        else:
              # thin warm saturated horizon-glow band right above the water -- where the
              # cycling/saturation lives, not flooding the whole sky.
            u = (t - 0.78) / 0.22                                        # 0 -> 1 within the band
            phase = x * 0.05 + u * 1.0                                    # slow horizontal hue drift
            fg = dusk(phase)
            dens = 0.45 + 0.55 * u                                        # fuller toward the water
            idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
            cv.set(x, y, ch=RAMP[idx], fg=fg, bg=0)

# --- STRUCTURES: dark silhouettes --------------------------------------------
for y in range(H):
    for x in range(W):
        c = mask.get(x, y)[0]
        if c != 'X':
            continue
        cv.set(x, y, ch='\u2588', fg=4, bg=0)                    # dim blue-black silhouette

# --- cylindrical tank shading: bright vertical center, dark flanks -----------
for (cx, cy, rw, rh) in [(9, GROUND_Y - 4, 5, 4), (40, GROUND_Y - 3, 6, 5), (72, GROUND_Y - 4, 4, 4)]:
    for y in range(cy - rh, cy + rh + 1):
        dx = rw * math.sqrt(max(0.0, 1.0 - ((y - cy) / rh) ** 2))
        x0 = int(round(cx - dx)); x1 = int(round(cx + dx))
        for x in range(x0, x1 + 1):
            d = abs(x - cx) / max(1, rw)                           # 0 center -> 1 flank
            idx = int((1.0 - (1.0 - d)) * (len(RAMP) - 1))        # full block center, light shade flank
            cv.set(x, y, ch=RAMP[idx], fg=4, bg=0)

# --- rim light: a thin bright cycling edge on the right side of each stack ----
def rim(cx, top, bot):
    for y in range(top, min(bot, GROUND_Y)):
        t = (y - SCENE_TOP) / float(GROUND_Y - SCENE_TOP)
        fg = wheel(y * 0.12 + 4.0) if t > 0.5 else 96             # warm rim near water, cool up high
        cv.set(cx + 1, y, ch='\u2588', fg=fg, bg=0)
for (cx, hw, top) in STACKS:
    rim(cx + hw, top, GROUND_Y)
rim(FLARE_X + 1, FLARE_TOP, GROUND_Y)

# --- SMOKE PLUMES: cycling wisps rising off each stack into the void ---------
for (cx, hw, top) in STACKS:
    for i in range(15):
        y = top - 1 - i
        if y < TOPY:
            break
        x = cx + int(i * 0.7) + (i % 2)                            # drift up-and-right into the wind
        if not cv.in_bounds(x, y):
            continue
        dens = max(0.18, 1.0 - 0.65 * (i / 15.0))                 # thick at the mouth, thin as it rises
        idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
        fg = wheel(y * 0.2 + i * 0.6 + 2.0)                        # cycling hue along the plume
        cv.set(x, y, ch=RAMP[idx], fg=fg, bg=0)

# --- FLARE FLAME: the one fixed warm accent -- a dithered amber/white plume at
#     the flare head, brighter than everything else so the eye lands on it. ----
fx = FLARE_X
for i in range(11):
    y = FLARE_TOP - 1 - i
    if y < TOPY:
        break
    w = max(0, 2 - i // 3)
    for dx in range(-w, w + 1):
        x = fx + dx
        if not cv.in_bounds(x, y):
            continue
        dens = 1.0 - 0.45 * (i / 11.0)
        idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
        fg = 97 if i < 3 else (103 if i < 6 else 92)              # white-hot core -> amber -> yellow tip
        cv.set(x, y, ch=RAMP[idx], fg=fg, bg=0)

# ---------------------------------------------------------------------------
# 4. WATER REFLECTION BASIN (hollis joint pass) -- fills the dead foreground band
#    with a genuine new technique echoing hollis-city's mirror reflection.
#    The structure silhouette is mirrored downward from the waterline at GROUND_Y,
#    broken/dithered by depth; faint cycling ripple bands make it read as moving
#    dusk water, not a flat fill. A warm shimmering seam ties scene to reflection.
# ---------------------------------------------------------------------------

# 4a. waterline seam: a thin warm shimmering line at GROUND_Y (the horizon of the basin).
for x in range(W):
    fg = wheel(x * 0.18 + 1.0)                                        # cycling warm shimmer along the seam
    cv.set(x, GROUND_Y, ch='\u2550', fg=fg, bg=0)

# 4b. mirror the structure silhouette into the water, broken/dithered by depth --
#     echoing hollis-city's reflection. The basin is mostly DARK still water (like the
#     sky's upper void); the reflection appears only as DIM, broken vertical streaks
#     under each structure that fade to black with depth. One warm glint: the flare
#     flame's own reflection, the single bright point in the water -- the focal echo.
def is_structure(x, y):
     # stacks
    for cx, hw, top in STACKS:
        if (cx - hw) <= x <= (cx + hw) and top <= y < GROUND_Y:
            return True
     # flare stack
    if (FLARE_X - 1) <= x <= (FLARE_X + 1) and FLARE_TOP <= y < GROUND_Y:
        return True
     # tanks
    for (cx, cy, rw, rh) in [(9, GROUND_Y - 4, 5, 4), (40, GROUND_Y - 3, 6, 5), (72, GROUND_Y - 4, 4, 4)]:
        if cy - rh <= y <= cy + rh:
            dx = rw * math.sqrt(max(0.0, 1.0 - ((y - cy) / rh) ** 2))
            if abs(x - cx) <= int(round(dx)):
                return True
    return False

for r in range(GROUND_Y + 1, SIG_Y):
    depth = r - GROUND_Y
    src_r = GROUND_Y - 1 - depth                                      # mirror row above the waterline
    for x in range(W):
        if not is_structure(x, src_r):
            continue
         # dither: deeper reflection is sparser; a per-column phase breaks it into ripples
        ripple = ((x + depth * 2) % 3)
        if depth > 2 and ripple == 0:                                 # shatter with depth
            continue
        if depth <= 2 and (ripple == 2):                              # light break even near the surface
            continue
         # flare glint: the one warm bright point -- amber/white streak under the flame head
        in_flare = (FLARE_X - 1) <= x <= (FLARE_X + 1)
        if in_flare and depth < 7:
            fg = 97 if depth < 2 else (103 if depth < 5 else 92)      # white-hot -> amber -> yellow, fading
            dens = max(0.3, 1.0 - 0.5 * (depth / 7.0))
            idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
            cv.set(x, r, ch=RAMP[idx], fg=fg, bg=0)
        else:
             # ordinary reflection: DIM normal-intensity blue/teal streak that sinks to black.
             # NOT bright -- the water stays dark like the sky's void; only the glint is bright.
            base = 4 if depth < 3 else (6 if depth < 5 else 4)        # dim blue -> teal -> blue, all NORMAL intensity
            dens = max(0.1, 1.0 - 0.85 * (depth / float(max(1, SIG_Y - GROUND_Y))))
            idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
            cv.set(x, r, ch=RAMP[idx], fg=base, bg=0)

# 4c. faint ripple highlights across the OPEN water (no structure above): a few dim
#     cycling shade cells on sparse rows so the basin reads as moving dusk water -- but
#     mostly it stays dark void, like the sky, so the reflections are what carry it.
for r in range(GROUND_Y + 2, SIG_Y):
    depth = r - GROUND_Y
    if depth % 3 != 0:                                                # sparse: only every third row
        continue
    for x in range(W):
        if is_structure(x, GROUND_Y - 1 - depth):
            continue                                                  # don't overwrite the reflection itself
        if ((x + depth) % 4) == 0:                                    # broken into short dashes
            fg = 6 if (depth + x) % 2 == 0 else 4                      # dim teal/blue, normal intensity
            cv.set(x, r, ch=RAMP[3], fg=fg, bg=0)                     # faint shade ripple

# ---------------------------------------------------------------------------
# 5. title band + sig block (joint credit: raze & hollis / AGENTSCI / REFINERY v1.6)
# ---------------------------------------------------------------------------
def band(y, text, fg):
    pad = W - len(text)
    left = pad // 2
    for x in range(W):
        if left <= x < left + len(text):
            cv.set(x, y, ch=text[x - left], fg=fg, bg=0)
        else:
            cv.set(x, y, ch='\u2550', fg=104, bg=0)

band(0, "REFINERY // AGENTSCI", 97)
band(1, "an oil refinery at dusk -- stacks / flare / water reflection", 96)

def sigline(y, text, fg):
    pad = W - len(text)
    left = pad // 2
    for x in range(W):
        if left <= x < left + len(text):
            cv.set(x, y, ch=text[x - left], fg=fg, bg=0)
        else:
            cv.set(x, y, ch='\u2550', fg=104, bg=0)

cv.set(0, SIG_Y, ch='\u2560', fg=105, bg=0)
for x in range(1, W):
    cv.set(x, SIG_Y, ch='\u2550', fg=104, bg=0)
sigline(SIG_Y + 1, "raze & hollis / AGENTSCII", 97)
sigline(SIG_Y + 2, "REFINERY v1.6 -- oil refinery at dusk, over water", 96)
cv.set(0, SIG_Y + 3, ch='\u2563', fg=105, bg=0)
for x in range(1, W):
    cv.set(x, SIG_Y + 3, ch='\u2550', fg=104, bg=0)

# ---------------------------------------------------------------------------
# 6. render (char-by-char, SGR-on-change -- safe for multi-char text) + write
# ---------------------------------------------------------------------------
out = []
for row in cv.cells:
    parts = []
    last_fg, last_bg = None, None
    for ch, fg, bg in row:
        if (fg, bg) != (last_fg, last_bg):
            parts.append(sgr(fg, bg))
            last_fg, last_bg = fg, bg
        parts.append(ch)
    out.append("".join(parts))

raw = "\n".join(out) + "\x1b[0m\n"
with open("scratch/raze-refinery-v16.ans", "w", encoding="cp437") as f:
    f.write(raw)
print("wrote scratch/raze-refinery-v16.ans (%d rows)" % len(out))
