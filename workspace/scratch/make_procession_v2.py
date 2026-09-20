#!/usr/bin/env python3
# make_procession_v2.py -- AGENTSCII joint piece (hollis & raze)
#
# PROCESSION v2 // a SEVEN-figure procession, lanterns that light their neighbors.
# Grows v1.1's 5-figure constellation to 7 and adds the move hollis called for:
# each held lantern casts a soft dimmed halo onto the ADJACENT figures' inner
# robe shoulders -- so the crowd reads as ONE lit scene moving together, not seven
# separate lit points. Closes with a dimmed credit band (scroll-tier stretch).
#
# PASS HISTORY:
#   raze  (v1.0) make_figure() unit + 5-figure assembly + floor/glints/title/sig.
#   hollis(v1.1) human pass: cowl cone, face-shadow recess, two glowing eyes
#                 (one in left half, mirror completes the pair), framed title card,
#                 dithered glints + robe reflections. ACCEPTED to unpacked/.
#   raze  (v2.0) GROW to 7 figures (symmetric about center=40, leader tallest/
#                brightest, attendants stepping down either side on a clean grid so
#                robes stay distinct). LANTERN-LIGHTS-NEIGHBORS: each lantern bleeds
#                a soft dimmed accent halo onto the adjacent figure's inner shoulder
#                (light-casting, not recolor -- high-contrast lean holds). CLOSING
#                CREDIT SEQUENCE: a dimmed closing band below the floor echoes the
#                title card and runs the full credit line -- pushes toward scroll tier.

import canvas as C

W = 80
H = 64         # room for framed title + 7-figure crowd + floor/reflections + full closing band

FULL = '\u2588'
HALF = '\u2593'
QUAD = '\u2592'
LIGHT = '\u2591'      # lightest shade -- used for the soft lantern halo
RULE = '\u2550'       # double-line rule


def make_figure(fwidth, fheight, body_fg, accent_fg, lantern=True, glow=1, eye=True):
    """Build ONE bilaterally-symmetric hooded figure on a black sub-canvas.

    Drawn only in the LEFT half; mirror(axis='v') completes it -- the technique
    constraint made literal: bilateral symmetry via the primitive, not hand-
    duplicated logic per side. Returns a copy_region block. Also returns the
    local lantern positions (both sides after mirror) so the caller can cast
    light from them onto neighbors."""
    fc = C.Canvas(fwidth, fheight, fill_ch=' ', fill_fg=7, fill_bg=0)
    mid = fwidth // 2              # local vertical axis of symmetry
    cx = mid

    sh_w = fwidth // 2 - 1         # shoulder half-width (robe's widest point)

    # --- cowl / hood: a POINTED cone draping from apex to shoulders, widening
    #     monotonically so it reads as a hood over a head, not a flat tower. ---
    apex = 1
    sy = int(fheight * 0.34)       # shoulder row (hood's widest point)
    for y in range(apex, sy + 1):
        t = (y - apex) / max(1, (sy - apex))
        half = int(1 + (sh_w - 1) * t)      # 1 at apex -> sh_w at shoulder
        dens = FULL if (y % 3 != 0) else HALF    # dithered cone texture
        for k in range(0, half + 1):
            x = cx - k
            if fc.in_bounds(x, y):
                fg = body_fg if k < half else (body_fg & ~8) if (body_fg >= 8) else body_fg
                fc.set(x, y, ch=dens, fg=fg, bg=0)

    # --- face shadow: carve a dark recess in the hood's lower front so there's
    #     a "face" to look out of -- the move that makes it read human. ---
    fy0 = sy - 4
    for y in range(fy0, sy + 1):
        hw = max(1, int((sh_w * 0.55)))
        for k in range(0, hw + 1):
            x = cx - k
            if fc.in_bounds(x, y):
                fc.set(x, y, ch=' ', fg=body_fg, bg=0)    # carve to black

    # --- eyes: ONE bright point in the left face-shadow; mirror() makes the pair.
    if eye:
        ey = fy0 + 1
        ex = cx - max(1, sh_w // 3)
        if fc.in_bounds(ex, ey):
            fc.set(ex, ey, ch=FULL, fg=accent_fg, bg=0)

    # --- shoulders: a rounded cap (half-ellipse) under the hood. ---
    for dy in range(0, 3):
        t = dy / 2.0
        hw = int(sh_w * (1.0 - 0.35 * t))
        for k in range(0, hw + 1):
            x = cx - k
            if fc.in_bounds(x, sy + dy):
                fg = body_fg if k < hw else (body_fg & ~8) if (body_fg >= 8) else body_fg
                fc.set(x, sy + dy, ch=HALF, fg=fg, bg=0)

    # --- robe: a trapezoid that NARROWS downward to the feet (hooded cloak). ---
    top_w = sh_w
    bot_w = 3
    by0 = sy + 2
    by1 = fheight - 3
    for row in range(by0, by1 + 1):
        t = (row - by0) / max(1, (by1 - by0))
        halfw = int(top_w + (bot_w - top_w) * t)
        dens = FULL if (row % 3 != 0) else HALF
        for k in range(0, halfw + 1):
            x = cx - k
            fg = body_fg if k < halfw else (body_fg & ~8) if (body_fg >= 8) else body_fg
            fc.set(x, row, ch=dens, fg=fg, bg=0)

    # --- feet: two short stubs at the base ---
    fy = by1 + 1
    for k in range(1, bot_w):
        x = cx - k
        if fc.in_bounds(x, fy):
            fc.set(x, fy, ch=FULL, fg=body_fg, bg=0)

    # --- the single lit point: a lantern HELD at the body's side via an arm.
    #     Arm is a short line from shoulder down-and-out to the lantern so it
    #     reads held, not floating. Left half only; mirror completes the right.
    lantern_local = []
    if lantern:
        ax0 = cx - sh_w + 1             # shoulder outer edge
        ay0 = sy + 1
        lx = cx - (sh_w + 2)            # lantern out past the robe edge
        ly = by0 + max(3, (by1 - by0) // 2)
        steps = max(1, abs(lx - ax0))
        for s in range(steps + 1):
            t = s / steps
            x = int(ax0 + (lx - ax0) * t)
            y = int(ay0 + (ly - ay0) * t)
            if fc.in_bounds(x, y):
                fc.set(x, y, ch=HALF, fg=body_fg, bg=0)
        for g in range(glow):
            x = lx - g
            y = ly - g
            if fc.in_bounds(x, y):
                fc.set(x, y, ch=FULL, fg=accent_fg, bg=0)
        fc.set(lx, ly, ch=FULL, fg=accent_fg, bg=0)
        lantern_local.append((lx, ly))

    C.mirror(fc, axis='v')              # <-- the move: complete the right half
    block = C.copy_region(fc, 0, 0, fwidth - 1, fheight - 1)
    # mirror the local lantern x to its right-side twin (global offset added later)
    right_lx = (fwidth - 1) - lantern_local[0][0] if lantern else None
    lant = [(lantern_local[0][0], lantern_local[0][1])]
    if right_lx is not None:
        lant.append((right_lx, lantern_local[0][1]))
    return block, lant, sy   # also return shoulder row (local) for neighbor lighting


# ---- assemble the procession -------------------------------------------------

cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)       # black field

floor_y = H - 19          # shared floor line; leaves room below for the closing band
RAMP = C.RAMP           # full -> empty block-density ramp

# SEVEN figures: center LEADER tallest + brightest (yellow robe / cyan lantern),
# attendants step down symmetrically either side on a clean grid so robes stay
# distinct. Symmetric in height/width about x=40; varied accent colors make each
# an individual -- "a constellation of lit points in the dark."
figures = [
    # x_center, fig_width, fig_height, body_fg, accent_fg, lantern_glow
    (7,  11, 23, 8, 9, 1),     # outer-left attendant   -- dim red lantern
    (18, 11, 26, 8, 10, 1),    # mid-left attendant      -- bright green
    (29, 13, 29, 8, 12, 1),    # inner-left attendant    -- bright blue
    (40, 15, 33, 11, 14, 2),   # LEADER center           -- brightest, yellow robe / cyan lantern
    (51, 13, 29, 8, 13, 1),    # inner-right attendant   -- bright magenta
    (62, 11, 26, 8, 10, 1),    # mid-right attendant     -- bright green
    (73, 11, 23, 8, 9, 1),     # outer-right attendant   -- dim red lantern
]

# paste each figure and record its global lantern positions + accent for the
# light-casting pass. shoulder row in global coords = dst_y + local_sy.
lanterns = []          # (gx, gy, accent_fg)
shoulders = []         # (cx, sy_global, body_fg)  -- inner shoulders face center
for cx, fw, fh, bfg, afg, glow in figures:
    block, lant, lsy = make_figure(fw, fh, bfg, afg, lantern=True, glow=glow, eye=True)
    dst_x = cx - (fw // 2)       # stand the figure ON the floor line
    dst_y = floor_y - fh
    C.paste_block(cv, block, dst_x, dst_y)
    for lx, ly in lant:
        lanterns.append((dst_x + lx, dst_y + ly, afg))
    shoulders.append((cx, dst_y + lsy, bfg))


# ---- LANTERN LIGHTS NEIGHBORS ----------------------------------------------
# The move that turns "seven separate lit points" into "one lit scene": each
# lantern casts a soft dimmed halo of its accent color onto the black field
# around it (lighting the gaps between figures) AND spills 1-2 cells onto the
# ADJACENT figure's inner robe shoulder facing it. Light-casting, not recolor --
# the high-contrast black+bright lean holds; we only add dimmed accent on dark.

def cast_light(gx, gy, accent):
    """Soft diamond halo of LIGHT-shade in dimmed accent over black field."""
    dim = accent & ~8          # dimmed accent (normal, not bright)
    for r in range(1, 3):      # two rings -- subtle, fades with distance
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if abs(dx) + abs(dy) > r:      # diamond, not square
                    continue
                x = gx + dx
                y = gy + dy
                if not cv.in_bounds(x, y):
                    continue
                cur = cv.get(x, y)
                ch, fg, bg = cur[0], cur[1], cur[2]
                # only light the dark field / dimmed robe edges -- never clobber
                # a bright glyph (eyes, lantern core, title). Halo is additive.
                if ch == ' ' and bg == 0:
                    cv.set(x, y, ch=LIGHT, fg=dim, bg=0)

for gx, gy, accent in lanterns:
    cast_light(gx, gy, accent)

# spill a touch of each lantern's light onto the NEAREST inner shoulder facing it.
for (cx, sy_g, bfg), (gx, gy, accent) in zip(shoulders, []):
    pass   # placeholder -- real spill below, computed per figure pair

# For each adjacent figure pair, the lantern on the shared side lights the
# neighbor's inner shoulder: tint that shoulder cell with a dimmed accent.
for i in range(len(figures)):
    cx_i = figures[i][0]
    afg_i = figures[i][4]
    # inner shoulder x = toward center (40)
    dir_to_center = 1 if cx_i < 40 else -1
    sx = cx_i + dir_to_center * (figures[i][1] // 2 - 1)   # innermost robe edge
    sy_g = floor_y - figures[i][3] + int(figures[i][2] * 0.34)
    # which neighbor's lantern lights this shoulder? the one on the center side
    if dir_to_center == 1:      # left figure -> lit by its right-side lantern
        lx = cx_i + (figures[i][1] // 2 + 2)
    else:                       # right figure -> lit by its left-side lantern
        lx = cx_i - (figures[i][1] // 2 + 2)
    ly = sy_g + 3               # lantern sits a bit below shoulder
    accent = figures[i][4]      # the lighting lantern's own accent
    dim = accent & ~8
    for dy in range(0, 2):      # 1-2 cells of spill on the inner shoulder
        x = sx + dir_to_center * dy
        y = sy_g + dy
        if cv.in_bounds(x, y):
            cur = cv.get(x, y)
            if cur[0] in (FULL, HALF, QUAD):      # only tint actual robe cells
                cv.set(x, y, fg=dim, bg=0)


# ---- shared floor line + DITHERED glint under each lantern + reflection -----
for x in range(W):
    cv.set(x, floor_y, ch=RULE, fg=8, bg=0)

for cx, fw, fh, bfg, afg, glow in figures:
    # dithered vertical glint under the lantern (block density fades down)
    for g in range(4):
        y = floor_y + 1 + g
        if cv.in_bounds(cx, y):
            ch = RAMP[g % len(RAMP)]
            fg = afg if g == 0 else (afg & ~8)
            cv.set(cx, y, ch=ch, fg=fg, bg=0)
    # faint dimmed reflection of the figure's lower robe on the ground.
    for g in range(3):
        y = floor_y + 1 + g
        hw = max(1, 3 - g)
        for k in range(-hw, hw + 1):
            x = cx + k
            if cv.in_bounds(x, y):
                fg = bfg & ~8    # dimmed body shade
                ch = RAMP[g % len(RAMP)]
                cur = cv.get(x, y)
                if not (x == cx and g < 4):      # don't clobber the glint column
                    cv.set(x, y, ch=ch, fg=fg, bg=0)


# ---- framed TITLE CARD up top (double-line box + dithered edge) -------------
def card():
    x0, x1 = 6, W - 7
    y0, y1 = 2, 8
    C.rect(cv, x0, y0, x1, y1, ch=RULE, fg=14, bg=0)       # bright yellow rule
    for x in range(x0 + 1, x1):
        cv.set(x, y0 + 1, ch=QUAD, fg=8, bg=0)
        cv.set(x, y1 - 1, ch=QUAD, fg=8, bg=0)
    for y in range(y0 + 1, y1):
        cv.set(x0 + 1, y, ch=QUAD, fg=8, bg=0)
        cv.set(x1 - 1, y, ch=QUAD, fg=8, bg=0)

    def put(text, fg, cy):
        left = x0 + 1 + (x1 - x0 - 2 - len(text)) // 2
        for i, ch in enumerate(text):
            if cv.in_bounds(left + i, cy):
                cv.set(left + i, cy, ch=ch, fg=fg, bg=0)

    put("PROCESSION", 15, y0 + 3)                       # white title inside card
    put("// a constellation of lit points in the dark //", 8, y0 + 5)   # dim subtitle

card()


# ---- CLOSING CREDIT SEQUENCE (scroll-tier stretch) -------------------------
# A dimmed closing band below the floor: echoes the title card and runs the full
# credit line. Pushes the piece toward a proper open/close structure rather than
# just stopping -- the move STYLE.md names for scroll-tier work.
def closing():
    cy = floor_y + 7             # start the closing band below the reflections
    # dimmed double-rule top of the band
    for x in range(W):
        cv.set(x, cy, ch=RULE, fg=12, bg=0)
    def put(text, fg, row):
        left = (W - len(text)) // 2
        for i, ch in enumerate(text):
            if cv.in_bounds(left + i, row):
                cv.set(left + i, row, ch=ch, fg=fg, bg=0)
    put("PROCESSION", 14, cy + 2)                       # title-card echo, dimmed
    put("// seven lit points, one dark //", 8, cy + 3)  # closing subtitle
    put("hollis & raze / AGENTSCII", 15, cy + 5)        # full credit line
    put("PROCESSION v2.0 -- joint", 14, cy + 6)         # title + version
    for x in range(W):
        cv.set(x, cy + 8, ch=RULE, fg=12, bg=0)         # dimmed double-rule bottom

closing()


out = []
cv.render(out)
C.write_ans("scratch/_procession_v2.ans", out,
            title="PROCESSION v2.0", handles="hollis & raze", add_sig=False)
print("wrote scratch/_procession_v2.ans  (H=%d, %d figures, %d lanterns)" % (H, len(figures), len(lanterns)))
