#!/usr/bin/env python3
# canvas.py -- AGENTSCII house drawing-primitives toolkit.
#
# WHY THIS EXISTS: every piece so far (procedural fields, portraits, scrolls)
# hand-derives its own per-cell math from scratch in a fresh script -- ellipse
# formulas, light falloff, dithering, mirroring -- every single time. Real
# ACiD/BBS-era artists had TheDraw/ACiDDraw: line, fill, mirror, block-copy,
# gradient as INSTANT primitives, not math you re-derive per piece. This module
# is that toolkit for AGENTSCII. It doesn't replace figure_common.py or
# curve_common.py (those stay as their families' specialized machinery) --
# it's the general-purpose layer underneath any of them, and underneath
# whatever NEW piece idea comes next that doesn't fit an existing family.
#
# DESIGN: a Canvas is a 2D grid of [char, fg, bg] cells (fg/bg are 0-15 ANSI
# indices, bright = 8+base exactly like the rest of the house SGR convention).
# Every primitive below mutates a Canvas in place. When you're done, call
# canvas.render(out) to get real SGR-coded lines, then write_ans(path, out,
# title, handles) to produce a finished, hygiene-clean .ans file in one call.
#
# QUICK START:
#   import canvas as C
#   cv = C.Canvas(80, 40)
#   C.rect(cv, 2, 2, 77, 37, ch='\u2591', fg=4)                  # dim blue border field
#   C.ellipse(cv, 40, 20, 12, 8, ch='\u2588', fg=14, fill=True)  # bright yellow disc
#   C.gradient_fill(cv, lambda x,y: (x-40)**2+(y-20)**2 < 12*12, cx=40, cy=20,
#                    fg_near=15, fg_far=4)                       # radial shading
#   C.mirror(cv, axis='v')                                       # mirror left half -> right half
#   out = []
#   cv.render(out)
#   C.write_ans('scratch/my_piece.ans', out, title='MY PIECE v1.0', handles='raze')
#
# Every primitive is intentionally simple and composable -- the goal is to
# make "try an idea" cheap, not to make every possible picture in one call.
# Compose primitives the way a real editor's tools get combined by hand.

import math
import re

RAMP = "\u2588\u2593\u2592\u2591"   # full -> empty block-density ramp (bright to dim)

# ---- fixed palette reference + hue-family ramps ------------------------------
# Added 2026-09-16 directly in response to a real, repeated failure: both the
# artist agent and the assistant building this toolkit independently guessed
# wrong about what a color INDEX (0-15) actually renders as, more than once
# the same session -- assuming index 6 was "dark red" (it's cyan, #00aaaa),
# assuming HOUSE_HUE's raw SGR codes (95, 91, 93...) were interchangeable with
# 0-15 indices (they aren't -- passing 95 as an index computes a WRONG color
# via the (90+(fg&7)) formula, since 95 was never meant to go through that
# math a second time). Re-deriving "what does this number mean" from memory
# every shift is exactly the kind of thing a fixed reference exists to avoid.
#
# PALETTE below is the ACTUAL hex value for every index 0-15, taken directly
# from harness.py's _ANSI_PALETTE (the single source of truth for what
# actually renders) -- not re-derived, not guessed.
PALETTE = {
    0: ("black",         "#000000"),
    1: ("red",           "#aa0000"),
    2: ("green",         "#00aa00"),
    3: ("brown/orange",  "#aa5500"),
    4: ("blue",          "#0000aa"),
    5: ("magenta",       "#aa00aa"),
    6: ("cyan",          "#00aaaa"),
    7: ("light gray",    "#aaaaaa"),
    8: ("dark gray",     "#555555"),
    9: ("bright red",    "#ff5555"),
    10: ("bright green", "#55ff55"),
    11: ("bright yellow","#ffff55"),
    12: ("bright blue",  "#5555ff"),
    13: ("bright magenta","#ff55ff"),
    14: ("bright cyan",  "#55ffff"),
    15: ("white",        "#ffffff"),
}

# Hue-family ramps: [hot, mid, cold] -- three indices that are GENUINELY the
# same hue at different brightness, verified against PALETTE above, not
# assumed from index proximity (9,10,11 look adjacent but are red/green/
# yellow -- three different hues, the exact rainbow-flooding bug this fixes).
# Use these instead of hand-picking 3 numbers and hoping they're related.
_HUE_RAMPS = {
    "amber":   [11, 9, 1],    # bright yellow -> bright red -> red (warm lamp/fire)
    "red":     [9, 1, 1],     # bright red -> red -> red (no dim-red index exists; repeats)
    "blue":    [12, 4, 4],    # bright blue -> blue -> blue
    "cyan":    [14, 6, 6],    # bright cyan -> cyan -> cyan
    "green":   [10, 2, 2],    # bright green -> green -> green
    "magenta": [13, 5, 5],    # bright magenta -> magenta -> magenta
    "gray":    [15, 7, 8],    # white -> light gray -> dark gray (the usual "neutral" ramp)
    "white":   [15, 7, 8],    # alias for gray -- what most callers mean by "white ramp"
}


def ramp(hue_name):
    """Return [hot, mid, cold] -- three palette indices (0-15) that are the
    SAME hue family at descending brightness, verified against the real
    palette. Use this instead of hand-computing a 3-color ramp: 'amber',
    'red', 'blue', 'cyan', 'green', 'magenta', 'gray'/'white' are defined.
    Raises KeyError with the valid options listed if the name isn't known --
    deliberately loud instead of silently returning something wrong."""
    if hue_name not in _HUE_RAMPS:
        raise KeyError(
            f"ramp({hue_name!r}) not defined. Valid hue families: "
            f"{sorted(_HUE_RAMPS.keys())}"
        )
    return list(_HUE_RAMPS[hue_name])


def shade_ramp(from_color, to_color, steps=None):
    """Build a REAL brightness transition between two palette indices,
    using genuine ░▒▓ density dithering -- not a hand-picked flat fill.

    Added 2026-09-18 in direct response to a measured, load-bearing gap:
    every version of _orb (v5-v8) and _phosphor.v3 used 0.0% RAMP density
    characters -- zero dithering anywhere in the piece. That's not a
    style choice, it's the literal absence of a shading mechanism, and
    it's the exact, repeated reason the Opus curator gate rejected all of
    them ("flat unshaded region", "hard vertical seam", "no gradient
    within each color zone"). A checker can only keep catching this; it
    can't fix it. This function is the fix: a real way to go from a lit
    color to a shadow color across a surface instead of two flat blocks
    meeting at a hard edge.

    Technique (the actual real-ACiD dithering trick, not invented):
    ANSI has only 16 real colors, so intermediate brightness is FAKED by
    varying how much of the "hot" color's ink shows through against the
    "cold" color's background, using the block-density glyphs
    █(100% ink) ▓(~75%) ▒(~50%) ░(~25%) space(0% ink, pure bg). fg is
    ALWAYS from_color, bg is ALWAYS to_color, across every step -- only
    the GLYPH changes, which is what fakes the extra brightness levels a
    16-color palette doesn't actually have.

    Returns a list of `steps` (char, fg_idx, bg_idx) tuples, ordered from
    from_color (index 0, solid) to to_color (index -1, solid). Default
    steps=5 (one solid + the 3 RAMP density levels + one solid) is the
    real ceiling of distinct-looking dither levels obtainable from one
    glyph's density pattern between two colors -- passing a larger
    `steps` repeats levels near the ends rather than inventing more real
    ones, which is honest (you cannot fake more gradations than the
    glyph set provides).

    Usage: index into the returned list by local position along the
    transition -- `shade_ramp(hot, cold, 5)[int(t * 4)]` for t in [0,1]
    -- instead of picking one flat (fg, bg) pair for a whole shaded
    region. Combine with ramp(hue_name) for real same-hue endpoints:
    hot, mid, cold = ramp('amber'); stops = shade_ramp(hot, cold, 7).
    """
    if steps is None:
        steps = len(RAMP) + 1  # 5: solid-hot, ▓, ▒, ░, solid-cold
    if steps < 2:
        raise ValueError("shade_ramp needs steps >= 2 (at least the two endpoints)")

    stops = []
    for i in range(steps):
        t = i / (steps - 1)
        if i == 0:
            # solid from_color: full-block glyph, fg=from, bg=to (bg is
            # irrelevant here since the glyph is 100% ink, but keep it
            # consistent so a renderer relying on bg for anything else
            # -- e.g. a later texture pass -- sees the right value)
            stops.append((RAMP[0], from_color, to_color))
        elif i == steps - 1:
            # solid to_color: space char, 0% ink, pure bg
            stops.append((" ", from_color, to_color))
        else:
            # map the interior fraction onto RAMP's density levels
            # (RAMP[0]=█ full ink already used for i==0, so interior
            # steps draw from RAMP[1:] -- the ▓▒░ partial-density glyphs)
            interior_t = (i - 1) / (steps - 2) if steps > 2 else 0.0
            ramp_idx = 1 + min(len(RAMP) - 2, int(interior_t * (len(RAMP) - 1)))
            stops.append((RAMP[ramp_idx], from_color, to_color))
    return stops


HOUSE_HUE = [13, 9, 11, 10, 14, 12, 15, 3]  # bright magenta/red/yellow/green/
# cyan/blue/white/amber wheel -- FIXED 2026-09-16: this used to store raw SGR
# codes (95, 91, 93, 92, 96, 94, 107, 103), which is a DIFFERENT number space
# than the 0-15 palette index that cv.set()/render() actually expect. Passing
# 95 through render()'s sgr() formula ((90+(fg&7)) if fg>7 else 30+fg)
# computes an unrelated color (verified: cycle_hue(0) rendered as bright
# WHITE, not the intended bright magenta). Real pieces built on the old
# HOUSE_HUE (_afterimage_scroll.py, _patch_traveler_v4.py, make_dialogue.py,
# make_traveler_scroll.py) likely have miscolored hue-cycling as a result --
# flagged in OBSERVER_NOTES.txt for the agents to review, not silently
# rewritten here.


def sgr(fg, bg=0):
    """Return the raw ESC[...m code for a given fg/bg pair (0-15 each).

    Uses the classic bold-prefix form (1;3X / 1;4X) for bright colors,
    NOT the aixterm 90-97/100-107 extended range -- confirmed live
    2026-09-18 that ansilove (and, per the DOS/ANSI.SYS convention real
    scene tools followed, most classic ANSI renderers) does not support
    90-97/100-107 at all: ESC[93;40m rendered as pure BLACK, not bright
    yellow, in a direct pixel test. harness.py's own renderer (what
    agents see via preview_piece) DOES parse 90-97 correctly, so this
    bug was invisible in the live agent pipeline -- but any ansilove-
    based tool (external viewers, the corpus validation pipeline) would
    render every bright-color cell from this house library as flat
    black. Classic 1;3X form works everywhere; 90-97 doesn't. Bright
    background (100-107) has no unambiguous classic equivalent (real
    DOS ANSI used the blink-bit + iCE-colors convention for that, which
    is a file-level mode flag, not something a single SGR sequence can
    express) -- emits 100-107 as-is for now since a renderer that
    doesn't support iCE colors wouldn't render bright backgrounds
    correctly under ANY encoding, this only fixes the strictly-worse
    "no bright fg at all" case.
    """
    bright = fg > 7
    f = 30 + (fg & 7)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return ("\x1b[1;%d;%dm" % (f, b)) if bright else ("\x1b[%d;%dm" % (f, b))


class Canvas:
    """A W x H grid of [char, fg, bg] cells. fg/bg are ANSI 0-15 indices."""

    def __init__(self, w=80, h=40, fill_ch=' ', fill_fg=7, fill_bg=0):
        self.w = w
        self.h = h
        self.cells = [[[fill_ch, fill_fg, fill_bg] for _ in range(w)] for _ in range(h)]

    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, ch=None, fg=None, bg=None):
        """Set only the fields given -- set(x,y,fg=4) recolors without erasing the glyph."""
        if not self.in_bounds(x, y):
            return
        cell = self.cells[y][x]
        if ch is not None:
            cell[0] = ch
        if fg is not None:
            cell[1] = fg
        if bg is not None:
            cell[2] = bg

    def get(self, x, y):
        if not self.in_bounds(x, y):
            return None
        return tuple(self.cells[y][x])

    def render(self, out):
        """Append one SGR-coded string per row to out (a list you provide)."""
        for row in self.cells:
            parts = []
            last_fg, last_bg = None, None
            for ch, fg, bg in row:
                if (fg, bg) != (last_fg, last_bg):
                    parts.append(sgr(fg, bg))
                    last_fg, last_bg = fg, bg
                parts.append(ch)
            out.append("".join(parts))


# ---- primitives: shapes -----------------------------------------------------

def line(cv, x0, y0, x1, y1, ch='\u2588', fg=7, bg=0):
    """Bresenham line from (x0,y0) to (x1,y1) inclusive."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        cv.set(x, y, ch, fg, bg)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def rect(cv, x0, y0, x1, y1, ch='\u2588', fg=7, bg=0, fill=False):
    """Axis-aligned rectangle. fill=False draws only the border."""
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    if fill:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                cv.set(x, y, ch, fg, bg)
    else:
        for x in range(x0, x1 + 1):
            cv.set(x, y0, ch, fg, bg)
            cv.set(x, y1, ch, fg, bg)
        for y in range(y0, y1 + 1):
            cv.set(x0, y, ch, fg, bg)
            cv.set(x1, y, ch, fg, bg)


def ellipse(cv, cx, cy, rx, ry, ch='\u2588', fg=7, bg=0, fill=False):
    """Ellipse centered at (cx,cy) with radii rx,ry. fill=False draws only the rim."""
    y_lo, y_hi = int(cy - ry) - 1, int(cy + ry) + 1
    for y in range(y_lo, y_hi + 1):
        t = (y - cy) / ry if ry else 0
        if abs(t) > 1.0:
            continue
        hw = rx * math.sqrt(max(0.0, 1.0 - t * t))
        if fill:
            for x in range(int(cx - hw), int(cx + hw) + 1):
                cv.set(x, y, ch, fg, bg)
        else:
            cv.set(int(cx - hw), y, ch, fg, bg)
            cv.set(int(cx + hw), y, ch, fg, bg)


def flood_fill(cv, x, y, ch, fg, bg=0, match_ch=True, match_fg=True):
    """Classic 4-connected flood fill from (x,y), matching the ORIGINAL cell
    there (not the new fill value) so it stops at real boundaries. Stack-based
    (not recursive) so it's safe on large regions."""
    if not cv.in_bounds(x, y):
        return
    target = cv.get(x, y)
    target_key = (target[0] if match_ch else None, target[1] if match_fg else None)

    def key_of(cell):
        return (cell[0] if match_ch else None, cell[1] if match_fg else None)

    if key_of((ch, fg, bg)) == target_key:
        return  # already the fill value, nothing to do
    stack = [(x, y)]
    seen = set()
    while stack:
        cx_, cy_ = stack.pop()
        if (cx_, cy_) in seen or not cv.in_bounds(cx_, cy_):
            continue
        if key_of(cv.get(cx_, cy_)) != target_key:
            continue
        seen.add((cx_, cy_))
        cv.set(cx_, cy_, ch, fg, bg)
        stack += [(cx_ + 1, cy_), (cx_ - 1, cy_), (cx_, cy_ + 1), (cx_, cy_ - 1)]


# ---- primitives: region-based shading/dithering -----------------------------

def gradient_fill(cv, region_fn, cx, cy, fg_near, fg_far, max_dist=None, ramp=RAMP):
    """Paint every cell where region_fn(x,y) is True with a radial gradient
    from fg_near (at the center) to fg_far (at the edge), block-density
    dithered rather than a flat color swap -- this is what makes shading
    read as a real gradient instead of two solid-color rings."""
    if max_dist is None:
        max_dist = max(cv.w, cv.h) / 2.0
    for y in range(cv.h):
        for x in range(cv.w):
            if not region_fn(x, y):
                continue
            d = math.hypot(x - cx, y - cy) / max_dist
            d = max(0.0, min(1.0, d))
            fg = fg_near if d < 0.5 else fg_far
            idx = int(d * (len(ramp) - 1) * 2) % len(ramp)
            cv.set(x, y, ramp[idx], fg, cv.get(x, y)[2])


def dither_region(cv, region_fn, density_fn, fg, bg=0, ramp=RAMP):
    """Paint region_fn(x,y) cells using density_fn(x,y) -> 0.0-1.0 to pick a
    ramp character (1.0 = full block, 0.0 = lightest shade). Use this for any
    custom shading curve that gradient_fill's simple radial model doesn't fit
    (directional light, noise fields, hand-authored falloffs, etc)."""
    for y in range(cv.h):
        for x in range(cv.w):
            if not region_fn(x, y):
                continue
            d = max(0.0, min(1.0, density_fn(x, y)))
            idx = int((1.0 - d) * (len(ramp) - 1))
            cv.set(x, y, ramp[idx], fg, bg)


def texture_fill(cv, region_fn, fg, bg=0, ramp=RAMP, density=0.35, seed=None):
    """Scatter sparse background texture over region_fn(x,y) cells -- for
    negative space, NOT the subject. Real ACiD/Blocktronics work almost
    never leaves flat unshaded black behind a figure/subject (see
    references/study/somms-neo_tokyo.ANS, nokturnal_emissions-
    millenium_edition.ANS); a lot of house figurative work does (compare
    STRIDE/MANTIS's pure-black backgrounds). This is the fast way to close
    that specific gap: call it on whatever's NOT your subject before you
    finish, with a low density (0.15-0.4) so it reads as atmosphere, not
    noise competing with the subject. density is the fraction of cells
    that get ANY mark; among those, ramp index is randomized so the
    texture isn't uniform. Deterministic with a seed if you want reproducible
    output across passes."""
    import random
    rng = random.Random(seed)
    for y in range(cv.h):
        for x in range(cv.w):
            if not region_fn(x, y):
                continue
            if rng.random() > density:
                continue
            idx = rng.randint(len(ramp) // 2, len(ramp) - 1)  # bias toward light/sparse marks
            cv.set(x, y, ramp[idx], fg, bg)


def strand_shade(cv, region_fn, direction_fn, fg_list, n_strands=40, length=6,
                  jitter=1, ch=RAMP[0], seed=None):
    """Directional strand/stroke shading -- for fur, hair, muscle striation,
    grain, or any surface where real ACiD work builds texture from many
    SHORT DIRECTIONAL STROKES following the form, not a uniform gradient
    wash. Studied from references/study/somms-the_powergrid.ANS (fur/mane)
    and ghengis-shades_of_a_shade.ANS (dense stippled fields): individual
    strokes read as distinct marks, angled consistently with the surface
    they're on, in 2-4 alternating hues (not one flat color) so the strokes
    separate from each other visually instead of blurring into a solid mass.

    region_fn(x,y) -> bool: where strokes are allowed to start.
    direction_fn(x,y) -> (dx,dy): the stroke direction AT that origin point
      (e.g. radiating from a center, or a fixed diagonal for combed fur) --
      this is what makes strokes follow the form instead of pointing randomly.
    fg_list: strokes cycle through these colors so adjacent strokes don't
      blend into one flat mass (2-4 related hues works well, e.g.
      [light_highlight, mid_tone, mid_tone, shadow]).
    n_strands: how many strokes to place.
    length: stroke length in cells.
    jitter: +/- random perpendicular offset per stroke so they don't look
      like a mechanical grid (1-2 is usually enough).
    seed: deterministic output across passes if set.

    This is a texture pass -- run it AFTER your base shape/color blocking,
    so strokes lay on top of already-placed color instead of the reverse."""
    import random
    rng = random.Random(seed)
    candidates = [(x, y) for y in range(cv.h) for x in range(cv.w) if region_fn(x, y)]
    if not candidates:
        return
    for i in range(n_strands):
        x0, y0 = rng.choice(candidates)
        dx, dy = direction_fn(x0, y0)
        mag = (dx * dx + dy * dy) ** 0.5 or 1.0
        dx, dy = dx / mag, dy / mag
        # perpendicular jitter so strokes don't sit in a mechanical line
        px, py = -dy, dx
        off = rng.uniform(-jitter, jitter)
        fg = fg_list[i % len(fg_list)]
        for s in range(length):
            x = int(round(x0 + dx * s + px * off))
            y = int(round(y0 + dy * s + py * off))
            if 0 <= x < cv.w and 0 <= y < cv.h:
                cv.set(x, y, ch, fg)


def streak_field(cv, region_fn, fg_ramp, ch=RAMP[0], density=0.5,
                  min_len=3, max_len=None, seed=None):
    """Dense vertical noise-streak texture -- studied from
    references/study/blocktronics-tnt_bl0b.ANS and blocktronics-hx_night.ANS
    (both real ACiD/Blocktronics flame/static-field pieces). NOT the same
    technique as strand_shade() (discrete angled strokes from an origin
    point) -- this is a per-COLUMN randomized-run vertical noise field: for
    each column that region_fn allows, pick a random run length and fill it
    solid from the bottom up, biased toward brighter/hotter colors in
    fg_ramp lower in the run and cooler/dimmer higher up. Repeated across
    many adjacent columns with independent random run lengths, this is what
    produces the ragged, flame-like vertical streak texture in both
    references (very different from a smooth horizontal gradient or a flat
    fill -- the raggedness IS the technique).

    region_fn(x,y) -> bool: where streaks are allowed to exist.
    fg_ramp: a list of colors from HOT (index 0, used near the base of each
      streak) to COOL (last index, used near the streak's tip) -- streak
      color is picked by position within its own run, not randomly, so each
      individual streak reads as a coherent flame/tongue, not noise.
    density: fraction of eligible columns that get a streak at all.
    min_len/max_len: streak length range in cells (max_len defaults to
      region height).
    seed: deterministic output across passes if set.

    Call this AFTER your base composition (title, subject, frame) so
    streaks fill remaining negative space without covering intentional
    content -- same convention as texture_fill()."""
    import random
    rng = random.Random(seed)
    cols = {}
    for x in range(cv.w):
        for y in range(cv.h):
            if region_fn(x, y):
                cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        if rng.random() > density:
            continue
        ys_sorted = sorted(ys)
        base_y = ys_sorted[-1]  # streak grows UPWARD from the lowest eligible cell
        col_max_len = max_len if max_len is not None else len(ys_sorted)
        run_len = rng.randint(min_len, max(min_len, col_max_len))
        eligible_set = set(ys_sorted)
        for i in range(run_len):
            y = base_y - i
            if y not in eligible_set:
                break
            t = i / max(1, run_len - 1)  # 0 at base (hot) -> 1 at tip (cool)
            idx = min(len(fg_ramp) - 1, int(t * len(fg_ramp)))
            cv.set(x, y, ch, fg_ramp[idx], cv.get(x, y)[2])


def drip(cv, x, y0, y1, fg, ch=RAMP[0], bg=None, taper=True, seed=None):
    """A single paint-drip/run mark hanging down from (x, y0) to a random
    depth up to y1 -- studied from references/study/blocktronics-n_silove.ANS
    (drip/paint-run texture on hand-styled lettering). Real drip technique:
    a thin vertical line whose length varies per-column (not a uniform
    fringe) and whose WIDTH narrows as it falls (a droplet tapering to a
    point), which is what reads as "dripping" rather than "a row of icicles
    of the same length." Call once per column along a letter/shape's lower
    edge with a fresh seed or varying x so drips don't line up mechanically.

    x: the column to drip in (typically along a letterform's bottom edge).
    y0: the row the drip starts from (the letter's edge).
    y1: the furthest row a drip could reach (a ceiling on length).
    fg: drip color (usually the same hue as the source letter, optionally
      darker/desaturated to read as "wet").
    taper: if True, the ch glyph density drops (using RAMP) as the drip
      thins toward its tip -- a full block near the source, lighter marks
      at the tip. If False, uses ch uniformly (a harder-edged drip).
    seed: per-drip randomness; vary this per call (e.g. seed=x) or drips
      look identical."""
    import random
    rng = random.Random(seed)
    length = rng.randint(1, max(1, y1 - y0))
    for i in range(length):
        y = y0 + i
        if y > y1:
            break
        if taper:
            t = i / max(1, length - 1)
            idx = min(len(RAMP) - 1, int(t * len(RAMP)))
            cv.set(x, y, RAMP[idx], fg, bg if bg is not None else cv.get(x, y)[2])
        else:
            cv.set(x, y, ch, fg, bg if bg is not None else cv.get(x, y)[2])


def drip_edge(cv, edge_fn, y_max, fg, x_range=None, coverage=0.4, taper=True, seed=None):
    """Convenience wrapper around drip(): call drip() along every column of
    a shape's bottom edge automatically. edge_fn(x) -> y or None: returns
    the row of the lowest painted cell in column x (the drip's start point),
    or None if that column has no shape to drip from. coverage: fraction of
    eligible columns that get a drip at all (real drip work isn't on every
    single column -- that reads as a uniform fringe, not dripping).
    x_range: (x0, x1) to limit which columns are checked; defaults to the
    whole canvas width."""
    import random
    rng = random.Random(seed)
    x0, x1 = x_range if x_range else (0, cv.w)
    for x in range(x0, x1):
        y0 = edge_fn(x)
        if y0 is None:
            continue
        if rng.random() > coverage:
            continue
        drip(cv, x, y0, y_max, fg, taper=taper, seed=rng.randint(0, 1 << 30))


def mirror_quad(cv):
    """4-way (kaleidoscope/mandala) mirror: mirrors the canvas's upper-left
    quadrant into all four quadrants -- studied from
    references/study/blocktronics-mx_mess.ANS (a true 4-way mirrored
    ornamental piece, distinct from canvas.mirror()'s single-axis v/h
    mirror). Build your ornamental motif ONLY in the upper-left quadrant
    (x < w/2, y < h/2), then call this once: it mirrors that quadrant
    rightward (h-axis) AND downward (v-axis) AND diagonally (both), so one
    authored wedge becomes a full symmetric rosette/mandala. This is what
    makes dense curled ornamental patterns (see the reference) cheap --
    author 1/4 of the detail, get a fully symmetric result."""
    w, h = cv.w, cv.h
    mid_x, mid_y = w // 2, h // 2
    for y in range(mid_y):
        for x in range(mid_x):
            src = cv.cells[y][x]
            cv.cells[y][w - 1 - x] = list(src)          # mirror right (h-axis)
            cv.cells[h - 1 - y][x] = list(src)           # mirror down (v-axis)
            cv.cells[h - 1 - y][w - 1 - x] = list(src)   # mirror diagonal (both)


# ---- block-letter text primitives --------------------------------------------
# GLYPHS_5x7: a shared 5-wide x 7-tall block-letter font (full A-Z, 0-9, space,
# and common title punctuation). WHY THIS EXISTS: found directly 2026-09-15 --
# 9 separate scratch files (_eclipse.py, _molten_mark.py, _solstice.py,
# make_banner.py, make_logo.py, and backups) each hand-rolled their OWN GLYPHS
# dict from scratch, the exact "re-derive per piece" duplication canvas.py was
# built to stop. Seeded from make_logo.py's 9 hand-authored house letters
# (A,G,E,N,T,S,C,I -- kept byte-identical), extended to a complete alphabet.
GLYPHS_5x7 = {
'A': ["..#..",".###.","#...#","#####","#...#","#...#","#...#"],
'B': ["####.","#...#","#...#","####.","#...#","#...#","####."],
'C': [".####","#....","#....","#....","#....","#....",".####"],
'D': ["####.","#...#","#...#","#...#","#...#","#...#","####."],
'E': ["#####","#....","#....","####.","#....","#....","#####"],
'F': ["#####","#....","#....","####.","#....","#....","#...."],
'G': [".####","#....","#....","#.##.","#...#","#...#",".####"],
'H': ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
'I': ["#####","..#..","..#..","..#..","..#..","..#..","#####"],
'J': ["....#","....#","....#","....#","#...#","#...#",".###."],
'K': ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
'L': ["#....","#....","#....","#....","#....","#....","#####"],
'M': ["#...#","##.##","#.#.#","#...#","#...#","#...#","#...#"],
'N': ["#...#","##..#","#.#.#","#..##","#...#","#...#","#...#"],
'O': [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
'P': ["####.","#...#","#...#","####.","#....","#....","#...."],
'Q': [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
'R': ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
'S': [".####","#....","#....",".###.","....#","....#","####."],
'T': ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
'U': ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
'V': ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
'W': ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
'X': ["#...#",".#.#.","..#..","..#..","..#..",".#.#.","#...#"],
'Y': ["#...#",".#.#.","..#..","..#..","..#..","..#..","..#.."],
'Z': ["#####","....#","...#.","..#..",".#...","#....","#####"],
'0': [".###.","#...#","#..##","#.#.#","##..#","#...#",".###."],
'1': ["..#..",".##..","..#..","..#..","..#..","..#..","#####"],
'2': [".###.","#...#","....#","...#.","..#..",".#...","#####"],
'3': [".###.","#...#","....#",".###.","....#","#...#",".###."],
'4': ["...#.","..##.",".#.#.","#..#.","#####","...#.","...#."],
'5': ["#####","#....","####.","....#","....#","#...#",".###."],
'6': [".###.","#....","#....","####.","#...#","#...#",".###."],
'7': ["#####","....#","...#.","..#..",".#...","#....","#...."],
'8': [".###.","#...#","#...#",".###.","#...#","#...#",".###."],
'9': [".###.","#...#","#...#",".####","....#","....#",".###."],
' ': [".....",".....",".....",".....",".....",".....","....."],
'-': [".....",".....",".....","#####",".....",".....","....."],
':': [".....","..#..",".....",".....",".....","..#..","....."],
'/': ["....#","...#.","..#..",".#...","#....",".....","....."],
'!': ["..#..","..#..","..#..","..#..","..#..",".....","..#.."],
"'": [".#...",".#...",".....",".....",".....",".....","....."],
'.': [".....",".....",".....",".....",".....",".....","..#.."],
'&': [".##..","#..#.","#.#..",".#...","#.#.#","#..#.",".##.#"],
}


def block_letters(cv, text, x0, y0, fg, ch='\u2588', bg=None, gap=1,
                   glyphs=GLYPHS_5x7, scale=1):
    """Draw text as 5x7 block letters at (x0, y0) -- the shared wordmark/
    title primitive. Replaces hand-rolling a GLYPHS dict per piece (found in
    9 separate scratch files before this existed). Returns the total pixel
    width used, so you can center the result: width = block_letters(...);
    then redraw at x0 = (80 - width) // 2 if you need centering after the
    fact, or precompute with text_width() first.

    IMPORTANT (found directly while building this): use scale=2 or higher
    for anything meant to be read clearly at a glance -- at scale=1 (the
    default, 5 real cells per letter) the preview/PNG rendering pipeline
    doesn't have enough pixel resolution per letter to stay crisp, even
    though the underlying .ans data is completely correct (verified: the
    raw character grid is right, real terminals render scale=1 fine --
    it's specifically the synthetic PNG preview that gets soft at small
    text). scale=2-3 renders clearly in every viewer. ALSO: keep text_width()
    under 80 -- the preview pipeline's terminal-width constant is 80
    columns (the house canvas standard everywhere else too), and text
    wider than that silently wraps/clips in the PNG preview. Use
    text_width() to check before committing to a size/word combination.

    text: uppercase letters/digits/punctuation from GLYPHS_5x7 (unknown
      chars render as a blank 5-wide gap, not an error).
    fg: single color, OR a function(row, col_in_word) -> color for per-cell
      color control (e.g. a gradient across the word, or per-letter hues).
    scale: integer >=1 to draw each glyph cell as an NxN block of output
      cells -- a cheap way to get bigger title text without a bigger font.
    """
    cur_x = x0
    for ch_letter in text:
        glyph = glyphs.get(ch_letter.upper(), glyphs[' '])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell != '#':
                    continue
                color = fg(row_i, cur_x - x0) if callable(fg) else fg
                for sy in range(scale):
                    for sx in range(scale):
                        px = cur_x + col_i * scale + sx
                        py = y0 + row_i * scale + sy
                        cv.set(px, py, ch, color, bg if bg is not None else cv.get(px, py)[2])
        cur_x += (5 * scale) + gap
    return cur_x - x0 - gap


def text_width(text, glyphs=GLYPHS_5x7, gap=1, scale=1):
    """Pixel width block_letters() would use for `text` -- call this FIRST
    to center a wordmark: x0 = (canvas_width - text_width(text)) // 2."""
    n = len(text)
    return n * 5 * scale + max(0, n - 1) * gap


def bevel_text(cv, text, x0, y0, top_fg, mid_fg, bottom_fg, ch='\u2588',
                bg=None, gap=1, glyphs=GLYPHS_5x7, scale=1):
    """Beveled/chrome 3D block-letter text -- studied from
    references/study/asphyx-acid_logo.ANS (real ACiD chrome-lettering
    technique: a lit top edge, a mid-tone body, a dark underside PER
    LETTER, which is what makes text read as beveled metal instead of flat
    color). Same call shape as block_letters() but takes 3 colors instead
    of 1: top_fg for each glyph's TOP row (the lit bevel edge), mid_fg for
    the middle rows (the body), bottom_fg for the BOTTOM row (the shadowed
    underside). This 3-band split is the entire technique -- a flat single
    color reads as a silhouette, three bands reads as a lit 3D surface.
    Returns total pixel width, same as block_letters()."""
    cur_x = x0
    for ch_letter in text:
        glyph = glyphs.get(ch_letter.upper(), glyphs[' '])
        n_rows = len(glyph)
        for row_i, row in enumerate(glyph):
            if row_i == 0:
                color = top_fg
            elif row_i == n_rows - 1:
                color = bottom_fg
            else:
                color = mid_fg
            for col_i, cell in enumerate(row):
                if cell != '#':
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        px = cur_x + col_i * scale + sx
                        py = y0 + row_i * scale + sy
                        cv.set(px, py, ch, color, bg if bg is not None else cv.get(px, py)[2])
        cur_x += (5 * scale) + gap
    return cur_x - x0 - gap


def drop_shadow_text(cv, text, x0, y0, fg, shadow_fg, offset=(1, 1),
                      ch='\u2588', bg=None, gap=1, glyphs=GLYPHS_5x7, scale=1):
    """Block-letter text with a dark offset copy behind it -- studied from
    references/study/avg-theterminator.ans's title treatment (dense
    stippled title text sitting in front of a solid offset shadow copy,
    the classic "raised lettering" read). Draws the shadow copy FIRST at
    (x0+offset[0], y0+offset[1]) in shadow_fg, then the real text on top in
    fg -- so the shadow peeks out from behind the letters on the offset
    side. Returns total pixel width, same as block_letters()."""
    block_letters(cv, text, x0 + offset[0], y0 + offset[1], shadow_fg,
                  ch=ch, bg=bg, gap=gap, glyphs=glyphs, scale=scale)
    return block_letters(cv, text, x0, y0, fg, ch=ch, bg=bg, gap=gap,
                          glyphs=glyphs, scale=scale)


def cycle_hue(phase, wheel=HOUSE_HUE):
    """House color-cycling helper: map a float phase to a wheel index. Use
    this instead of hand-rolling `int(phase) % len(HUE)` in every piece."""
    return wheel[int(phase) % len(wheel)]


# ---- primitives: copy/paste/mirror (the real editor moves) ------------------

def copy_region(cv, x0, y0, x1, y1):
    """Return a standalone list-of-rows block you can paste elsewhere or into
    another canvas -- the block-copy move real ACiD editors give for free."""
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    return [[list(cv.cells[y][x]) for x in range(x0, x1 + 1)] for y in range(y0, y1 + 1)]


def paste_block(cv, block, dst_x, dst_y, transparent_ch=None):
    """Paste a block (from copy_region, or hand-built) at (dst_x, dst_y).
    If transparent_ch is set, cells matching it in the block are skipped
    (so you can paste a non-rectangular shape without clobbering background)."""
    for by, row in enumerate(block):
        for bx, (ch, fg, bg) in enumerate(row):
            if transparent_ch is not None and ch == transparent_ch:
                continue
            cv.set(dst_x + bx, dst_y + by, ch, fg, bg)


def mirror(cv, axis='v', src_half=None):
    """Mirror one half of the canvas onto the other -- 'v' mirrors left-half
    onto right-half (vertical axis of symmetry down the middle), 'h' mirrors
    top-half onto bottom-half. This is the single move that makes kaleidoscope/
    mandala/creature-face symmetry cheap instead of hand-duplicating logic."""
    if axis == 'v':
        mid = cv.w // 2
        for y in range(cv.h):
            for x in range(mid):
                src = cv.cells[y][x]
                cv.cells[y][cv.w - 1 - x] = list(src)
    elif axis == 'h':
        mid = cv.h // 2
        for y in range(mid):
            for x in range(cv.w):
                src = cv.cells[y][x]
                cv.cells[cv.h - 1 - y][x] = list(src)
    else:
        raise ValueError("axis must be 'v' or 'h'")


def rotate90_block(block):
    """Rotate a copy_region() block 90deg clockwise -- useful for kaleidoscope/
    rosette pieces that repeat one wedge around a center point."""
    h = len(block)
    w = len(block[0]) if h else 0
    return [[list(block[h - 1 - x][y]) for x in range(h)] for y in range(w)]


# ---- signature block + file output ------------------------------------------

def sig_block(out, title, handles="AGENTSCII"):
    """House-standard framed signature block, appended to out in place."""
    w = 80
    out.append("")
    out.append(sgr(13) + "\u2550" * w)

    def sigline(text, fg):
        pad = max(0, w - len(text))
        left = pad // 2
        right = pad - left
        return sgr(12) + " " * left + sgr(fg) + text + sgr(12) + " " * right
    out.append(sigline(handles + " / AGENTSCII", 15))
    out.append(sigline(title, 14))
    out.append(sgr(13) + "\u2550" * w)


def write_ans(path, out, title=None, handles="AGENTSCII", add_sig=True):
    """Assemble out (a list of SGR-coded row strings) into a finished, hygiene-
    clean .ans file: optional sig block, standalone reset tail, cp437 on disk.
    Runs hygiene_gate on the result and prints the report so you see problems
    immediately instead of discovering them at inspect_piece time later."""
    if add_sig and title:
        sig_block(out, title, handles)
    raw = "\n".join(out) + "\x1b[0m\n"
    with open(path, "w", encoding="cp437") as f:
        f.write(raw)
    hygiene_gate(path)
    print("wrote", path)


def hygiene_gate(path):
    """Self-checking hygiene report -- same checks inspect_piece runs, so you
    catch problems before submitting, not after. Matches curve_common.py /
    figure_common.py's existing hygiene_gate exactly for consistency."""
    raw = open(path, "rb").read()
    ctrl = sorted(set(b for b in raw if b < 0x20 or b == 0x7f))
    print("bytes:", len(raw), "ctrl bytes:", [hex(c) for c in ctrl])
    try:
        raw.decode("cp437")
        print("cp437 on disk: OK")
    except Exception as e:
        print("cp437 FAIL", e)
    sgrs = re.findall(rb"\x1b\[([0-9;]*)m", raw)
    bad = []
    for s in sgrs:
        for tok in (s.decode() or "0").split(";"):
            if tok == "":
                continue
            v = int(tok)
            if not (v == 0 or 30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
                bad.append(v)
    print("SGR tokens:", len(sgrs), "out-of-range:", sorted(set(bad)))
    disp = re.sub(rb"\x1b\[[0-9;]*m", b"", raw).decode("cp437")
    widths = set(len(l) for l in disp.split("\n") if l)
    print("row widths:", sorted(widths))
    blank_runs = []
    run = 0
    for l in disp.split("\n"):
        if l.strip() == "":
            run += 1
        else:
            if run >= 3:
                blank_runs.append(run)
            run = 0
    if run >= 3:
        blank_runs.append(run)
    print("blank runs >=3:", blank_runs)
    print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))


# ---- self-test: proves every primitive works end to end ---------------------
if __name__ == "__main__":
    cv = Canvas(80, 30)
    rect(cv, 1, 1, 78, 28, ch='\u2591', fg=4, bg=0)
    ellipse(cv, 40, 14, 18, 10, ch='\u2588', fg=14, fill=True)
    gradient_fill(cv, lambda x, y: (x - 20) ** 2 / 100 + (y - 20) ** 2 / 36 < 1,
                  cx=20, cy=20, fg_near=15, fg_far=4)
    line(cv, 5, 5, 74, 24, ch='\u2593', fg=12)
    flood_fill(cv, 3, 3, ch='\u2592', fg=6)
    mirror(cv, axis='v')
    out = []
    cv.render(out)
    write_ans("/tmp/canvas_selftest.ans", out, title="CANVAS SELF-TEST", handles="canvas.py")
