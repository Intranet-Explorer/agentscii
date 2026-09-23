#!/usr/bin/env python3
# _dawn.py -- JOINT WIP (raze + hollis). DAWN // "the night giving way."
#
# PROVENANCE / WHY NEW: random_direction roll = "a full-body figure in motion" +
# technique "phosphor_render traced-curve/scope aesthetic" + palette lean "high
# contrast, mostly black with bright accents". Taken as a SEED and REMIXED, not
# literal -- the literal roll points straight at _afterimage (shipped pack29 v1.0 +
# scroll variants in 31/35/36), so a same-concept re-render would be the exact dup
# trap its own critique warned about. Instead this takes hollis's standing offer for
# the next batch: DAWN, the warm->cold transition that completes the EMBERWATCH /
# REFLEX day-night triad (pack45).
#
# FAMILY PLACEMENT -- the third member of the night pair, on a new axis:
#   EMBERWATCH v2 = WARM-only scene (bonfire in a draft), lit out of the dark.
#   REFLEX        = COLD-only scene  (neon city in still water), lit out of the dark.
#   DAWN          = BOTH at once, in ONE vertical gradient: cold night sky cooling
#                  DOWN into a warm sunrise as the sun breaks the horizon. Not an
#                  inverse pair -- a single piece that CONTAINS the temperature axis
#                  the other two each occupy alone. The transition IS the subject.
#
# SIGNATURE MOVE / NEW PRIMITIVE: a VERTICAL TEMPERATURE GRADIENT -- deep cold blue/
# indigo at the zenith fading down through a magenta/pink dawn band into warm amber
# near the horizon, with the sun's white-hot core + amber halo breaking through a
# silhouetted ridge. Fading stars in the upper cold sky thin out as they approach the
# warm band (night dissolving into day) -- motion-without-animation, the same idea as
# the afterimage family but expressed as a temporal transition across space, not a
# moving figure. One light source: the SUN at the horizon; everything is lit by it
# (warm glow radiates up + out; the ridge catches rim light; the sky cools away from
# it). No claimed anatomy -- environmental landscape, blind-check safe like EMBERWATCH.
#
# PASSES (METHODOLOGY), each verified by eye with preview_piece:
#   P1 flat massing -> verify composition reads as "sun at horizon, sky above";
#   P2 vertical temperature gradient lit from the ONE sun source (cold zenith -> warm
#      horizon, real falloff, dithered not banded);
#   P3 constructed detail (sun core+halo, fading stars dissolving into the band, cloud
#      wisps catching warm undersides, ridge rim-light);
#   P4 texture the void (faint atmospheric grain so the cold sky isn't flat black);
#   P5 frame + title card + house sig block.
#
# COLOR CALIBRATION GOTCHA: pass PLAIN 0-7/8-15 hue INDICES to cv.set -- NOT pre-encoded
# SGR codes (the double-map trap). U+2582 is not CP437; use RAMP chars only.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, texture_fill, write_ans, RAMP, sgr

W, H = 80, 52
cv = Canvas(W, H)
CX = W / 2.0
SEED = 11
random.seed(SEED)

HORIZON = 34                       # waterline-equivalent: sky [0..33], ground [35..51]
SUN_X, SUN_Y = 46.0, 35.0          # sun breaking THROUGH the ridge (center just below horizon)
SUN_R = 5.0                        # disc radius

# ---- P1: flat massing -------------------------------------------------------
# Sky is a single vertical band; ground is dark silhouette; sun disc pokes above ridge.
for y in range(H):
    for x in range(W):
        if y < HORIZON:
            cv.set(x, y, ch=' ', fg=4)          # cold blue placeholder (sky)
        else:
            cv.set(x, y, ch='\u2588', fg=0)     # dark ground silhouette

# sun disc placeholder (white block) -- will be shaded in P2/P3
for yy in range(int(SUN_Y - SUN_R), int(SUN_Y + SUN_R) + 1):
    for xx in range(int(SUN_X - SUN_R), int(SUN_X + SUN_R) + 1):
        if math.hypot(xx - SUN_X, yy - SUN_Y) <= SUN_R:
            cv.set(xx, yy, ch='\u2588', fg=7)

# ridge silhouette: a jagged mountain line along the horizon (asymmetric peaks)
def ridge_top(x):
    # base at HORIZON+1 with two asymmetric peaks; left peak taller than right
    p1 = 4.0 * math.exp(-((x - 26) ** 2) / (2 * 9.0 ** 2))   # tall left peak
    p2 = 2.5 * math.exp(-((x - 60) ** 2) / (2 * 7.0 ** 2))   # lower right peak
    return HORIZON + 1 - int(p1 + p2)

for x in range(W):
    top = ridge_top(x)
    for y in range(top, H):
        cv.set(x, y, ch='\u2588', fg=0)

out = []
cv.render(out)
write_ans("scratch/_dawn.ans", out, title="DAWN v1.0 -- the night giving way",
          handles="raze / hollis", add_sig=False)   # P1: no sig yet, just massing

# ============================================================================
# P2: VERTICAL TEMPERATURE GRADIENT -- the signature move.
# Cold indigo zenith -> magenta/pink dawn band -> warm amber horizon, with the
# sun's white-hot core + amber halo bleeding UP into the cold sky. One light
# source (the SUN at the horizon). Density ramp carries the falloff so it glows
# out of the dark instead of reading as flat color bands.
# ============================================================================

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

for y in range(HORIZON):
    for x in range(W):
        temp = y / HORIZON                       # 0 zenith -> 1 horizon (temperature rises down)
        dx = x - SUN_X; dy = y - SUN_Y
        dist = math.hypot(dx, dy)
        glow = max(0.0, 1.0 - dist / 30.0)       # radial warm pool from the sun, bleeds up
        w = clamp(0.52 * temp + 0.80 * glow)      # combined warmth

        if dist < SUN_R * 0.62:                   # white-hot core
            cv.set(x, y, ch='\u2588', fg=15)
            continue
        # density/brightness: bright near sun + horizon, sparse/dim at the cold zenith
        bright = clamp(max(glow, temp * 0.72))
        idx = int(bright * (len(RAMP) - 1))
        ch = RAMP[idx]

        if w > 0.84:                              # hottest band -- amber / yellow near horizon+core
            fg = 3 if bright < 0.5 else 9         # dim amber -> bright yellow
        elif w > 0.64:                            # red / orange transition
            fg = 1 if bright < 0.5 else 9
        elif w > 0.44:                            # pink / magenta dawn band
            fg = 5 if bright < 0.5 else 13
        elif w > 0.26:                            # blue-violet cooling
            fg = 4 if bright < 0.5 else 12
        else:                                     # deep cold indigo zenith
            fg = 4 if bright > 0.18 else 0        # near-black at the very top

        cv.set(x, y, ch=ch, fg=fg)

# ground catches a thin warm rim from the sun (P3 detail, but seed it now so P2 reads whole)
for x in range(W):
    top = ridge_top(x)
    for y in range(top, min(top + 2, H)):        # just the ridge crest line
        dx = x - SUN_X
        rim = max(0.0, 1.0 - abs(dx) / 34.0)     # warm where near the sun's column
        if rim > 0.5:
            cv.set(x, y, ch='\u2588', fg=9 if rim > 0.78 else 3)

out = []
cv.render(out)
write_ans("scratch/_dawn.ans", out, title="DAWN v1.0 -- the night giving way",
          handles="raze / hollis", add_sig=False)

# ============================================================================
# P2b: GROUND = dark silhouette (not the flat gray placeholder) + re-stamp the
# ridge as a DARK silhouette ON TOP of the warm glow, with rim light only at the
# crest near the sun's column. The ground is night; only its top edge catches dawn.
# ============================================================================

for y in range(HORIZON, H):
    for x in range(W):
        cv.set(x, y, ch='\u2588', fg=0)          # dark night ground (near-black)

# ridge silhouette re-stamped over the glow: dark mass, warm rim only at the crest
for x in range(W):
    top = ridge_top(x)
    for y in range(top, min(top + 3, H)):        # a few rows of the crest read as lit edge
        dx = x - SUN_X
        rim = max(0.0, 1.0 - abs(dx) / 36.0)     # warm where near the sun's column
        if y == top:                              # the very crest line catches most light
            if rim > 0.55:
                cv.set(x, y, ch='\u2588', fg=9 if rim > 0.8 else 3)
            elif rim > 0.3:
                cv.set(x, y, ch='\u2593', fg=1)   # faint warm edge far from sun
        elif y == top + 1 and rim > 0.7:
            cv.set(x, y, ch='\u2592', fg=3)       # a sliver of glow just under the crest

out = []
cv.render(out)
write_ans("scratch/_dawn.ans", out, title="DAWN v1.0 -- the night giving way",
          handles="raze / hollis", add_sig=False)

# ============================================================================
# P3: CONSTRUCTED DETAIL -- fading stars + cloud wisps + atmospheric grain.
# The star field THINS as it approaches the warm band (night dissolving into day):
# dense + bright high in the cold zenith, sparse + dim near the horizon. This is
# the "motion without animation" of the afterimage family, expressed temporally.
# ============================================================================

rng = random.Random(SEED + 3)

# --- fading stars: density falls off toward the warm band -------------------
STAR_ROWS = 24                          # stars live in the upper cold sky
for _ in range(150):
    x = rng.randint(0, W - 1)
    y = rng.randint(0, STAR_ROWS)
    if y >= HORIZON:
        continue
    band = y / STAR_ROWS                # 0 top (deep night) -> 1 (near dawn band)
    # thin out as we approach the warm band; cull most in the lower third
    if rng.random() < band * 0.75:
        continue
    bright = clamp(1.0 - band * 0.85)   # dimmer toward the horizon
    ch = '\u2588' if bright > 0.6 else ('\u2593' if bright > 0.3 else '\u2591')
    fg = 15 if bright > 0.75 else (14 if bright > 0.45 else 6)   # white -> cyan -> dim
    cv.set(x, y, ch=ch, fg=fg)

# --- cloud wisps: thin horizontal bands catching the sun's warm undersides --
# a few wavy strokes around the dawn band; each catches amber on its lit (sun-side) edge.
for base_y in [23, 26, 29]:
    amp = rng.uniform(0.6, 1.4)
    phase = rng.uniform(0, math.pi * 2)
    for x in range(W):
        yy = int(base_y + amp * math.sin(x * 0.18 + phase))
        if not (HORIZON - 6 <= yy < HORIZON):
            continue
        dx = x - SUN_X
        lit = max(0.0, 1.0 - abs(dx) / 30.0)    # sun-side edge is warmest
        if rng.random() > 0.55:                  # wispy, not solid
            continue
        fg = 9 if lit > 0.6 else (3 if lit > 0.3 else 1)
        cv.set(x, yy, ch='\u2592', fg=fg)

# --- atmospheric grain: faint texture over the COLD upper sky so it isn't flat --
def cold_sky(x, y):
    return y < HORIZON - 8 and (y / HORIZON) < 0.45     # only the deep cold zenith
texture_fill(cv, cold_sky, fg=4, density=0.10, seed=SEED + 7)   # dim blue grain

out = []
cv.render(out)
write_ans("scratch/_dawn.ans", out, title="DAWN v1.0 -- the night giving way",
          handles="raze / hollis", add_sig=False)

# ============================================================================
# P4: TEXTURE THE VOID -- the ground slab reads flat; give it depth. A faint
# warm reflection pool near the ridge crest (the sun's light spilling onto the
# night ground) fading to pure black with distance, plus sparse grain so it isn't
# a solid block. The cold zenith already has grain from P3.
# ============================================================================

def ground(x, y):
    return y >= HORIZON

for y in range(HORIZON, H):
    for x in range(W):
        d = (y - HORIZON) / (H - HORIZON)            # 0 at crest -> 1 deep
        dx = x - SUN_X
        refl = max(0.0, 1.0 - abs(dx) / 38.0)       # warm reflection under the sun's column
        warm = clamp(refl * (1.0 - d * 1.4))         # fades fast with depth
        if warm > 0.62:
            cv.set(x, y, ch='\u2593', fg=9)          # bright amber reflection near crest
        elif warm > 0.4:
            cv.set(x, y, ch='\u2592', fg=3)
        elif warm > 0.22:
            cv.set(x, y, ch='\u2591', fg=1)

# sparse grain over the whole ground so it reads as textured night earth, not a slab
rng2 = random.Random(SEED + 13)
for y in range(HORIZON + 1, H):
    for x in range(W):
        if rng2.random() < 0.06:
            cv.set(x, y, ch='\u2591', fg=8)          # faint gray speckle

# ============================================================================
# P5: FRAME + TITLE CARD + HOUSE SIG BLOCK -- the framing pass (Methodology Pass 6).
# Magenta double-rule top/bottom like EMBERWATCH/REFLEX; a centered title card in
# the cold upper sky so it doesn't fight the warm horizon.

def frame_rule(y, fg=13):
    out.append(sgr(fg) + "\u2550" * W)

out = []
frame_rule(0, 13)                                     # top magenta rule
cv.render(out)                                         # render the art field into out[1..H]

# title card: two centered lines in the cold zenith (above the stars' densest band)
def center(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(fg) + " " * left + text + " " * (pad - left)

out[1] = center("DAWN", 15)                            # inject over cold zenith
out[2] = center("-- the night giving way --", 94)

frame_rule(H, 13)                                      # bottom magenta rule
from canvas import sig_block
sig_block(out, "DAWN v1.0 -- the night giving way", handles="raze / hollis")

raw = "\n".join(out) + "\x1b[0m\n"
with open("scratch/_dawn.ans", "w", encoding="cp437") as f:
    f.write(raw)
from canvas import hygiene_gate
hygiene_gate("scratch/_dawn.ans")
print("ok -- P5 frame+title+sig written")
