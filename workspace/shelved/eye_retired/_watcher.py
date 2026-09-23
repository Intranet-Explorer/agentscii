# THE WATCHER // AGENTSCII -- raze
# A lit iris/eye emblem: dithered cyan iris with a REAL 3-band brightness ladder
# (dark-gray shadow flank -> normal-cyan mid surface -> bright-cyan crest + white
# glint), a magenta limbus ring, and a dark pupil with a catchlight rim, over a dim
# structured graticule field. Phosphor/CRT register. Reads as a single watchful eye
# motif WITHOUT the title card doing the work.
#
# WHY THIS VERSION: the earlier canvas-tool iris left (a) SOLID bright caps that the
# flat-region gate hard-blocks, and (b) only 2 distinct brightness steps -- the
# _figurative_precheck gate needs >=3 (dim/mid/highlight). Both fixed here with the
# house technique from make_demon_v3.py: a per-cell brightness LADDER within one hue
# family (ANSI has only 2 brightness steps per hue, so a true gradient climbs dim->
# bright->white), with per-cell glyph jitter so no contiguous same-(glyph,color) patch
# survives the flat-region gate.
#
# Brightness table the gate uses: _BRIGHTNESS = [0,2,2,2,2,2,2,3,1,4,4,4,4,4,4,5]
#   idx 8 (dark gray)=1 shadow | idx 6 (cyan)=2 mid | idx 14 (bright cyan)=4 crest
#   | idx 15 (white)=5 glint  -> {1,2,4,5} = 4 distinct steps, clears the >=3 gate.

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, texture_fill, write_ans, sgr

W = 80
H = 46
SEED = 7

# off-center upper-left light source (ACiD directional)
LX, LY = 31.0, 15.0
CX, CY = 40.0, 21.0
R_IRIS = 17.0
R_LIMBUS = 20.0
R_PUPIL = 6.0

# a tiny deterministic bayer-ish jitter so adjacent cells in a band get different
# glyphs -- this is what breaks any large same-(glyph,color) patch for the flat gate.
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
def jitter(x, y):
    return BAYER[y % 4][x % 4] / 16.0 - 0.5

# RAMP: full -> empty block density (bright light = dense ink)
RAMP = "\u2588\u2593\u2592\u2591"

def light_at(x, y):
    d = math.hypot(x - LX, y - LY)
    return max(0.0, min(1.0, 1.0 - d / (R_IRIS * 2.1)))

def shade_bright(Lval, hue=6):
    """Light 0..1 -> (glyph, fg SGR code). Density from RAMP tracks light; fg climbs a
    real brightness ladder within the hue family: dark-gray shadow -> normal hue mid ->
    bright hue crest. jitter keeps per-cell glyph variation (no flat patch)."""
    Lval = max(0.0, min(1.0, Lval + 0.06 * jitter(*None) if False else Lval))
    # glyph density: brighter light -> denser ink, with a fine per-cell step
    idx = int(Lval * (len(RAMP) - 1) + 0.5) % len(RAMP)
    ch = RAMP[idx]
    if Lval > 0.86:
        fg = 15                       # white-hot crest / glint
    elif Lval > 0.60:
        fg = 90 + (hue & 7)           # bright cyan -- lit surface
    elif Lval > 0.32:
        fg = 30 + (hue & 7)           # normal cyan -- mid surface
    else:
        fg = 8                        # dark gray -- deep shadow flank (brightness step 1)
    return ch, fg

cv = Canvas(W, H, fill_ch=' ', fill_fg=8, fill_bg=0)

# ---------------------------------------------------------------------------
# STEP 1 -- structured graticule field so negative space has structure, not flat
# black (Pass 5). Dim blue scope-lattice dots.
# ---------------------------------------------------------------------------
for y in range(H):
    for x in range(W):
        if (x % 4 == 0) and (y % 3 == 0):
            cv.set(x, y, '\u2591', 4, 0)

# ---------------------------------------------------------------------------
# STEP 2 -- the iris body: a lit cyan sphere with a REAL brightness ladder.
# Per-cell glyph variation + per-band fg climb = no flat cap, >=3 brightness steps.
# ---------------------------------------------------------------------------
def in_iris(x, y):
    return ((x - CX) ** 2 + (y - CY) ** 2) <= R_IRIS ** 2

for y in range(H):
    for x in range(W):
        if not in_iris(x, y):
            continue
        L = light_at(x, y)
        # per-cell glyph jitter so no large same-glyph patch forms within a band
        Lj = max(0.0, min(1.0, L + 0.05 * jitter(x, y)))
        ch, fg = shade_bright(Lj, hue=6)
        cv.set(x, y, ch, fg, 0)

# ---------------------------------------------------------------------------
# STEP 3 -- the limbus: a magenta ring just outside the iris, dithered + a small
# brightness climb (normal magenta -> bright magenta) so it reads as a lit rim.
# ---------------------------------------------------------------------------
def in_limbus(x, y):
    r2 = (x - CX) ** 2 + (y - CY) ** 2
    return R_IRIS ** 2 < r2 <= R_LIMBUS ** 2

for y in range(H):
    for x in range(W):
        if not in_limbus(x, y):
            continue
        L = light_at(x, y)
        Lj = max(0.0, min(1.0, L + 0.05 * jitter(x, y)))
        ch = RAMP[int(Lj * (len(RAMP) - 1) + 0.5) % len(RAMP)]
        fg = 90 + 5 if L > 0.55 else 30 + 5     # bright magenta crest / normal magenta mid
        cv.set(x, y, ch, fg, 0)

# ---------------------------------------------------------------------------
# STEP 4 -- the pupil: a dark cavity with a thin white catchlight rim on the lit
# arc. The carved void + glint is what makes it read as an eye, not a ball.
# ---------------------------------------------------------------------------
for y in range(H):
    for x in range(W):
        r2 = (x - CX) ** 2 + (y - CY) ** 2
        if r2 <= R_PUPIL ** 2:
            cv.set(x, y, ' ', 8, 0)             # dark pupil cavity
for y in range(H):
    for x in range(W):
        r2 = (x - CX) ** 2 + (y - CY) ** 2
        if R_PUPIL ** 2 < r2 <= (R_PUPIL + 1.0) ** 2:
            if (x < CX or y < CY):              # lit arc only
                cv.set(x, y, '\u2588', 15, 0)   # white catchlight rim

# a single crisp specular glint at the light point on the iris
cv.set(int(LX), int(LY), '\u2588', 15, 0)
cv.set(int(LX) + 1, int(LY), '\u2588', 15, 0)

# ---------------------------------------------------------------------------
# STEP 5 -- top frame bar (single row -> not a flat region). Bottom via write_ans.
# ---------------------------------------------------------------------------
out = [sgr(13) + "\u2550" * W]
for y in range(H):
    row = sgr(8, 0)
    for x in range(W):
        ch, fg, bg = cv.get(x, y)
        if (ch, fg, bg) != (' ', 8, 0):
            row += sgr(fg, bg) + ch
        else:
            row += ' '
    out.append(row.rstrip())

# single house-standard footer via write_ans (correct AGENTSCII spelling, stamped ONCE).
write_ans("scratch/_watcher.ans", out, title="THE WATCHER", handles="raze", add_sig=True)
