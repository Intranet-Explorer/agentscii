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
HOUSE_HUE = [95, 91, 93, 92, 96, 94, 107, 103]  # bright magenta/red/yellow/green/cyan/blue/white/amber wheel


def sgr(fg, bg=0):
    """Return the raw ESC[...m code for a given fg/bg pair (0-15 each)."""
    f = (90 + (fg & 7)) if fg > 7 else (30 + fg)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return "\x1b[%d;%dm" % (f, b)


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
