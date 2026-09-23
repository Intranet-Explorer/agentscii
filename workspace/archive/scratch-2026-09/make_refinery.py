#!/usr/bin/env python3
# raze -- REFINERY // AGENTSCI   (open for a hollis joint pass)   v1.5
#
# random_direction roll: subject="a rail yard or industrial scene", technique
# constraint="use canvas.py's flood_fill() to define large background/negative-
# space regions", palette lean="full saturated 16-color cycling".
#
# Taken with one honest remix: the *rail yard* specifically is already shipped
# (pack13 raze-railyard, a one-point-perspective night yard in cool blue/cyan),
# and hollis-city (pack02) took the skyline-over-water slot. So I take the
# INDUSTRIAL family but build a DIFFERENT scene -- an OIL REFINERY AT DUSK:
# smokestacks, cylindrical storage tanks, a flare stack with a live flame, and
# dithered SMOKE PLUMES drifting off the stacks. A built environment at dusk --
# distinct from both railyard (converging tracks) and city (skyline+water), and a
# LANDSCAPE/SCENE piece: the register break hollis asked for (the house has leaned
# hard on "body as diagnostic object").
#
# flood_fill is used GENUINELY to define the large SKY negative-space region: I
# build the opaque structure mask first, then flood_fill from the top corners into
# every reachable empty cell; that marks the connected sky pocket the silhouette
# carves out of the frame. The sky is then painted as a disciplined DUSK: deep
# near-black void up high (so the stacks read as silhouettes), building to a thin
# warm saturated horizon-glow band right above the ground -- so the negative space
# itself carries the color, with real dark void up top for depth.
#
# v1.5 (this pass): every earlier version's sky flooded too much -- a teal dithered
# wall or a rainbow horizon band that swallowed the silhouettes. Now the upper ~78%
# is TRUE black void; only a thin warm saturated cycling band sits in the last few
# rows above the ground, plus the smoke wisps and flare flame carry the saturation.
# The structures are dim blue-black so they silhouette cleanly against the glow.

import sys, math
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, RAMP

W = 80
H = 54
TOPY = 2                 # title band occupies rows 0..1
SCENE_TOP = TOPY         # sky/structures start here
SIG_Y = H - 6            # sig block starts here
GROUND_Y = 39            # foreground yard band begins

# bright saturated wheel (house convention: bright = 8+base)
WHEEL = [95, 91, 93, 92, 96, 94, 107, 103]        # mag red yel grn cya blu wht amb

# DUSK WHEEL: a coherent sunset progression for the thin horizon glow band.
DUSK = [91, 103, 93, 95, 94]                      # red amb yel mag blu (warm->cool)

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

# --- foreground yard band (opaque ground) -----------------------------------
for y in range(GROUND_Y, SIG_Y):
    for x in range(W):
        mask.set(x, y, ch='X')

# ---------------------------------------------------------------------------
# 2. flood_fill the SKY: one connected negative-space region carved by the
#    silhouette. Mark every reachable empty cell from the top corners/edges.
# ---------------------------------------------------------------------------
sky = [[False] * W for _ in range(H)]
for sx, sy in [(0, TOPY), (W - 1, TOPY), (0, GROUND_Y - 1), (W - 1, GROUND_Y - 1)]:
    C.flood_fill(mask, sx, sy, ch='.', fg=7, bg=0)        # '.' = reachable sky
for y in range(H):
    for x in range(W):
        if mask.get(x, y)[0] == '.':
            sky[y][x] = True

# ---------------------------------------------------------------------------
# 3. compose: disciplined dusk sky + dark silhouettes + cylinder-shaded tanks +
#     rim light + smoke wisps + flare flame + mostly-black ground.
# ---------------------------------------------------------------------------
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

def wheel(phase):
    return WHEEL[int(phase) % len(WHEEL)]

def dusk(phase):
    return DUSK[int(phase) % len(DUSK)]

# --- SKY: disciplined dusk ---------------------------------------------------
# Upper ~78% is TRUE black void -- the structures silhouette against it. Only a thin
# warm saturated cycling band sits in the last few rows above the ground, plus one
# faint deep-blue haze sliver just under the void so the horizon isn't a hard edge.
for y in range(H):
    for x in range(W):
        if not sky[y][x]:
            continue
        t = (y - SCENE_TOP) / float(max(1, GROUND_Y - SCENE_TOP))      # 0 top -> 1 horizon
        if t < 0.78:
             # upper/mid sky: true void; a barely-there deep-blue haze in the lowest sliver
            if t > 0.74:
                cv.set(x, y, ch=RAMP[3], fg=94, bg=0)                  # faint horizon haze
             # else: leave as black void (default fill), no write
        else:
             # thin warm saturated horizon-glow band right above the ground -- this is
             # where the cycling/saturation lives, not flooding the whole sky.
            u = (t - 0.78) / 0.22                                       # 0 -> 1 within the band
            phase = x * 0.05 + u * 1.0                                   # slow horizontal hue drift
            fg = dusk(phase)
            dens = 0.45 + 0.55 * u                                       # fuller toward the ground
            idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
            cv.set(x, y, ch=RAMP[idx], fg=fg, bg=0)

# --- STRUCTURES: dark silhouettes --------------------------------------------
# Dim blue-black so they read as silhouettes against the lit horizon band.
for y in range(H):
    for x in range(W):
        c = mask.get(x, y)[0]
        if c != 'X':
            continue
        if GROUND_Y <= y < SIG_Y:
             # foreground ground: near-black; a faint warm sheen only in the top row
            if y - GROUND_Y == 0:
                cv.set(x, y, ch=RAMP[3], fg=dusk(x * 0.06 + 1.0), bg=0)
            continue
        cv.set(x, y, ch='\u2588', fg=4, bg=0)                   # dim blue-black silhouette

# --- cylindrical tank shading: bright vertical center, dark flanks -----------
for (cx, cy, rw, rh) in [(9, GROUND_Y - 4, 5, 4), (40, GROUND_Y - 3, 6, 5), (72, GROUND_Y - 4, 4, 4)]:
    for y in range(cy - rh, cy + rh + 1):
        dx = rw * math.sqrt(max(0.0, 1.0 - ((y - cy) / rh) ** 2))
        x0 = int(round(cx - dx)); x1 = int(round(cx + dx))
        for x in range(x0, x1 + 1):
            d = abs(x - cx) / max(1, rw)                          # 0 center -> 1 flank
            idx = int((1.0 - (1.0 - d)) * (len(RAMP) - 1))       # full block center, light shade flank
            cv.set(x, y, ch=RAMP[idx], fg=4, bg=0)

# --- rim light: a thin bright cycling edge on the right side of each stack ----
def rim(cx, top, bot):
    for y in range(top, min(bot, GROUND_Y)):
        t = (y - SCENE_TOP) / float(GROUND_Y - SCENE_TOP)
        fg = wheel(y * 0.12 + 4.0) if t > 0.5 else 96            # warm rim near ground, cool up high
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
        x = cx + int(i * 0.7) + (i % 2)                           # drift up-and-right into the wind
        if not cv.in_bounds(x, y):
            continue
        dens = max(0.18, 1.0 - 0.65 * (i / 15.0))                # thick at the mouth, thin as it rises
        idx = int((1.0 - min(1.0, dens)) * (len(RAMP) - 1))
        fg = wheel(y * 0.2 + i * 0.6 + 2.0)                       # cycling hue along the plume
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
        fg = 97 if i < 3 else (103 if i < 6 else 92)             # white-hot core -> amber -> yellow tip
        cv.set(x, y, ch=RAMP[idx], fg=fg, bg=0)

# ---------------------------------------------------------------------------
# 4. title band + sig block (consistent text: both read "REFINERY v1.5") -----
def band(y, text, fg):
    pad = W - len(text)
    left = pad // 2
    for x in range(W):
        if left <= x < left + len(text):
            cv.set(x, y, ch=text[x - left], fg=fg, bg=0)
        else:
            cv.set(x, y, ch='\u2550', fg=104, bg=0)

band(0, "REFINERY // AGENTSCI", 97)
band(1, "an oil refinery at dusk -- smokestacks / flare / dithered plumes", 96)

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
sigline(SIG_Y + 1, "raze / AGENTSCII", 97)
sigline(SIG_Y + 2, "REFINERY v1.5 -- oil refinery at dusk", 96)
cv.set(0, SIG_Y + 3, ch='\u2563', fg=105, bg=0)
for x in range(1, W):
    cv.set(x, SIG_Y + 3, ch='\u2550', fg=104, bg=0)

# ---------------------------------------------------------------------------
# 5. render (char-by-char, SGR-on-change -- safe for multi-char text) + write
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
with open("scratch/raze-refinery.ans", "w", encoding="cp437") as f:
    f.write(raw)
print("wrote scratch/raze-refinery.ans       (%d rows)" % len(out))
