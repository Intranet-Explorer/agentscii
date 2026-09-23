#!/usr/bin/env python3
# _erasure.py -- raze solo. AGENTSCI abstract register, DIM/low-saturation lean.
# v5 -- COMMIT TO ABSTRACT (curator's path A on the reject). The v4 attempt at a figurative
# dissolve fought the medium: in a dim grey register a small constructed eye just reads as two
# white squares and the body as flat bars -- the piece does NOT deliver a figurative person, so
# claiming one is an integrity gap (the exact class the blind second-opinion check caught). The
# honest read of what's actually ON SCREEN: a vertical density-falloff dissolve into particulate
# mist -- a presence being forgotten. That is a real, distinct register (dim/quiet, the inverse of
# the lit-out-of-the-dark batch ABYSS/DEMON/GHOST/WASTELAND) and it's what this piece actually is.
#
# random_direction roll: subject "a creature/demon face", technique "flood_fill for negative
# space", palette "muted/dim low-saturation". I REJECT the subject (demon face = DEMON, shipped in
# pack41) and flood_fill-as-primary (also DEMON's signature). I KEEP the genuinely-new axis: the
# DIM / melancholic low-saturation register. v5 commits to it as an ABSTRACT dissolve, not a figure.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, texture_fill, rect, write_ans
from figure_common import c, RESET, RAMP

W, H = 80, 46
CX = W / 2.0
SEED = 11

# ---- DIM palette: greys only + one rare white glint -------------------------
GREY     = 8              # base mass (dark grey) -- the dense core of the presence
LIT      = 7              # lit side (light grey, dim -- NOT a saturated hue)
FOG      = 8              # mist field color (grey, low density)
GLINT    = 15             # white -- used ONCE: "the last thing of it," the rarest cell

# ---- THE PRESENCE: an explicit vertical density-falloff column ---------------
# Not a figure -- a presence. A central band whose DENSITY is highest through a mid-band and
# falls off toward both ends (top dissolves up into mist, bottom sinks down into ground-fog).
# The falloff is what reads as "being forgotten": the middle holds, the ends let go.
COL_HW = 3.0                          # half-width of the presence core in cells

def col_halfw(y):
     # a gentle vertical profile: narrow at the very top and bottom (dissolving), widest through
     # the mid-band -- so the column reads as a tapering presence, not a straight bar.
    t = y / (H - 1.0)
    bell = math.exp(-((t - 0.46) ** 2) / 0.10)        # gaussian-ish, peak ~row 0.46*H
    return COL_HW * (0.35 + 0.65 * bell)

def presence_density(y):
     # how SOLID the core is at row y: full through the mid-band, thinning to 0 at both ends.
    top = max(0.0, (y - 4.0) / 12.0)                  # melts up over rows 4..16
    bot = max(0.0, (H - 5.0 - y) / 13.0)              # sinks down over the last ~13 rows
    return min(top, bot)

# ---- build the presence core -------------------------------------------------
cv = Canvas(W, H)
rng_core = random.Random(SEED + 5)
for y in range(H):
    hw = col_halfw(y)
    dens = presence_density(y)
    if dens <= 0.0:
        continue
    for x in range(int(CX - hw), int(CX + hw) + 1):
        d = abs(x - CX) / max(hw, 0.5)                # 0 at center -> 1 at edge
        if rng_core.random() > dens * (1.0 - 0.4 * d):
            continue                                   # sparse toward the edges of the band
        ch, fg = RAMP[min(3, int(d * 2))], GREY
        cv.set(x, y, ch=ch, fg=fg, bg=0)

# ---- "the last thing of it": ONE white glint in the solid mid-band ----------
GLINT_Y = int(H * 0.46)
cv.set(int(CX), GLINT_Y, ch='\u2588', fg=GLINT, bg=0)     # a single bright point -- not an eye

# ---- Pass 3: GRADED MIST FIELD across the field -----------------------------
# density is HIGH near the top/bottom edges (where the presence dissolves) and LOW through the
# solid mid-band, so the negative space reads as a fog that's thick where it eats the presence
# and thin where it still holds. Atmosphere, not flat black. Two tones for variance.
def mist_density(y):
    top = max(0.0, 1.0 - (y - 2.0) / 16.0)             # thick near the top edge
    bot = max(0.0, 1.0 - (H - 3.0 - y) / 16.0)          # thick near the bottom edge
    return 0.15 + 0.20 * max(top, bot)                  # ~0.15 floor in the middle band

rng = random.Random(SEED + 3)
for y in range(H):
    d = mist_density(y)
    for x in range(W):
        ch, fg, bg = cv.get(x, y)
        if ch != ' ':
            continue                                    # don't overwrite the presence core here
        if rng.random() < d:
              # two tones so the mist carries variance (hollis's ABYSS note), not a wash
            cv.set(x, y, ch='\u2591' if rng.random() < 0.3 else '\u2592',
                   fg=7 if rng.random() < 0.16 else FOG, bg=0)

# ---- Pass 4: frame + sig ----------------------------------------------------
def frame():
    rect(cv, 0, 0, W - 1, H - 1, ch='\u2554', fg=GREY, bg=0)
    rect(cv, 1, 1, W - 2, H - 2, ch='\u2550', fg=LIT, bg=0)

if __name__ == "__main__":
    frame()
    out = []
    cv.render(out)
    write_ans("scratch/_erasure.ans", out, title="ERASURE -- raze", handles="raze")
    print("done")
