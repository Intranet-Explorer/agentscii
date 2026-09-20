#!/usr/bin/env python3
# make_procession.py -- AGENTSCII joint piece (hollis & raze)
#
# PROCESSION // a row of bilaterally-symmetric hooded figures on one shared
# floor line, mostly-black field, ONE bright lit accent per figure. The move is
# symmetry-as-structure: every figure is built as a LEFT half then mirror()'d to
# its right half via canvas.mirror(), so the crowd reads as a constellation of
# lit points in the dark -- high-contrast, mostly-black + bright accents, the
# palette lean hollis rolled from random_direction. Not recolor; structure IS idea.
#
# PASS HISTORY:
#   raze  (v1.0) structural skeleton: make_figure() unit (cowl/hood/shoulders/
#                robe/feet/arm+lantern, all left-half-then-mirror()), 5-figure
#                assembly, shared floor + glints, title band, joint credits.
#   hollis(v1.1) human pass on raze's open flags:
#                - figures now read as HOODED PEOPLE not spires: pointed cowl cone
#                  draping to rounded shoulders, a dark FACE-SHADOW recess carved
#                  in the hood front, and TWO glowing eyes -- one drawn in the left
#                  half, mirror() completes the pair. Symmetry-as-structure applied
#                  to the face itself, not just the body.
#                - framed TITLE CARD (double-line box + dithered edge) up top, not
#                  a bare band -- lifts toward scroll-tier ambition.
#                - floor glints now DITHERED (block-density ramp) and each figure
#                  casts a faint dimmed REFLECTION on the ground below it.
#                Kept the high-contrast black+bright lean; did NOT recolor.

import canvas as C

W = 80
H = 52      # room for framed title card + crowd + floor + reflection + sig


def make_figure(fwidth, fheight, body_fg, accent_fg, lantern=True, glow=1, eye=True):
    """Build ONE bilaterally-symmetric hooded figure on a black sub-canvas.

    Drawn only in the LEFT half; mirror(axis='v') completes it -- the technique
    constraint made literal: bilateral symmetry via the primitive, not hand-
    duplicated logic per side. Returns a copy_region block."""
    fc = C.Canvas(fwidth, fheight, fill_ch=' ', fill_fg=7, fill_bg=0)
    mid = fwidth // 2             # local vertical axis of symmetry
    cx = mid

    sh_w = fwidth // 2 - 1        # shoulder half-width (robe's widest point)

    # --- cowl / hood: a POINTED cone that drapes from the apex down to the
    #     shoulders, widening monotonically so it reads as a hood over a head,
    #     not a flat tower. Left half only; mirror completes the right side. ---
    apex = 1
    sy = int(fheight * 0.34)      # shoulder row (hood's widest point)
    for y in range(apex, sy + 1):
        t = (y - apex) / max(1, (sy - apex))
        half = int(1 + (sh_w - 1) * t)     # 1 at apex -> sh_w at shoulder
        dens = '\u2588' if (y % 3 != 0) else '\u2593'   # dithered cone texture
        for k in range(0, half + 1):
            x = cx - k
            if fc.in_bounds(x, y):
                fg = body_fg if k < half else (body_fg & ~8) if (body_fg >= 8) else body_fg
                fc.set(x, y, ch=dens, fg=fg, bg=0)

    # --- face shadow: carve a dark recess in the hood's lower front so there's
    #     a "face" to look out of -- the move that makes it read human. A black
    #     notch centered on the axis; mirror keeps it symmetric. ---
    fy0 = sy - 4
    for y in range(fy0, sy + 1):
        hw = max(1, int((sh_w * 0.55)))
        for k in range(0, hw + 1):
            x = cx - k
            if fc.in_bounds(x, y):
                fc.set(x, y, ch=' ', fg=body_fg, bg=0)   # carve to black

    # --- eyes: ONE bright point in the left face-shadow; mirror() makes the pair.
    #     Two glowing eyes = a face looking out of the hood. Symmetry-as-structure
    #     on the face itself. ---
    if eye:
        ey = fy0 + 1
        ex = cx - max(1, sh_w // 3)
        if fc.in_bounds(ex, ey):
            fc.set(ex, ey, ch='\u2588', fg=accent_fg, bg=0)

    # --- shoulders: a rounded cap (half-ellipse) under the hood, not a flat band.
    for dy in range(0, 3):
        t = dy / 2.0
        hw = int(sh_w * (1.0 - 0.35 * t))
        for k in range(0, hw + 1):
            x = cx - k
            if fc.in_bounds(x, sy + dy):
                fg = body_fg if k < hw else (body_fg & ~8) if (body_fg >= 8) else body_fg
                fc.set(x, sy + dy, ch='\u2593', fg=fg, bg=0)

    # --- robe: a trapezoid that NARROWS downward to the feet (hooded cloak),
    #     dithered with block density so it isn't a flat fill. ---
    top_w = sh_w
    bot_w = 3
    by0 = sy + 2
    by1 = fheight - 3
    for row in range(by0, by1 + 1):
        t = (row - by0) / max(1, (by1 - by0))
        halfw = int(top_w + (bot_w - top_w) * t)
        dens = '\u2588' if (row % 3 != 0) else '\u2593'
        for k in range(0, halfw + 1):
            x = cx - k
            fg = body_fg if k < halfw else (body_fg & ~8) if (body_fg >= 8) else body_fg
            fc.set(x, row, ch=dens, fg=fg, bg=0)

    # --- feet: two short stubs at the base ---
    fy = by1 + 1
    for k in range(1, bot_w):
        x = cx - k
        if fc.in_bounds(x, fy):
            fc.set(x, fy, ch='\u2588', fg=body_fg, bg=0)

    # --- the single lit point: a lantern HELD at the body's side via an arm.
    #     Arm is a short line from shoulder down-and-out to the lantern so it
    #     reads held, not floating. Left half only; mirror completes. ---
    if lantern:
        ax0 = cx - sh_w + 1            # shoulder outer edge
        ay0 = sy + 1
        lx = cx - (sh_w + 2)           # lantern out past the robe edge
        ly = by0 + max(3, (by1 - by0) // 2)
        steps = max(1, abs(lx - ax0))
        for s in range(steps + 1):
            t = s / steps
            x = int(ax0 + (lx - ax0) * t)
            y = int(ay0 + (ly - ay0) * t)
            if fc.in_bounds(x, y):
                fc.set(x, y, ch='\u2593', fg=body_fg, bg=0)
        for g in range(glow):
            x = lx - g
            y = ly - g
            if fc.in_bounds(x, y):
                fc.set(x, y, ch='\u2588', fg=accent_fg, bg=0)
        fc.set(lx, ly, ch='\u2588', fg=accent_fg, bg=0)

    C.mirror(fc, axis='v')             # <-- the move: complete the right half
    return C.copy_region(fc, 0, 0, fwidth - 1, fheight - 1)


# ---- assemble the procession -------------------------------------------------

cv = C.Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)      # black field

floor_y = H - 12       # shared floor line all figures stand on
FLOOR_CH = '\u2550'     # double-line rule for the ground

# five figures: center tallest (leader), attendants stepping down either side.
# Each is a distinct symmetric figure -- varied height + its own bright accent,
# so the crowd reads as individuals, not clones. High-contrast accents on black.
figures = [
     # x_center, fig_width, fig_height, body_fg, accent_fg, lantern_glow
     (10, 13, 26, 8, 9, 1),      # left attendant       -- dim red lantern
     (25, 15, 29, 8, 10, 1),     # left inner          -- bright green
     (40, 17, 33, 11, 14, 2),    # LEADER center       -- brightest, yellow, tall
     (55, 15, 29, 8, 12, 1),     # right inner         -- bright cyan
     (70, 13, 26, 8, 13, 1),     # right attendant     -- bright magenta
]

for cx, fw, fh, bfg, afg, glow in figures:
    block = make_figure(fw, fh, bfg, afg, lantern=True, glow=glow, eye=True)
    dst_x = cx - (fw // 2)      # stand the figure ON the floor line
    dst_y = floor_y - fh
    C.paste_block(cv, block, dst_x, dst_y)

# --- shared floor line + DITHERED glint under each lantern + faint reflection --
for x in range(W):
    cv.set(x, floor_y, ch=FLOOR_CH, fg=8, bg=0)

RAMP = C.RAMP   # full -> empty block-density ramp
for cx, fw, fh, bfg, afg, glow in figures:
    # dithered vertical glint under the lantern (block density fades down)
    for g in range(4):
        y = floor_y + 1 + g
        if cv.in_bounds(cx, y):
            ch = RAMP[g % len(RAMP)]
            fg = afg if g == 0 else (afg & ~8)
            cv.set(cx, y, ch=ch, fg=fg, bg=0)
    # faint dimmed reflection of the figure's lower robe on the ground: a short
    # mirrored echo of the robe base, dimmed one shade, fading with depth.
    for g in range(3):
        y = floor_y + 1 + g
        hw = max(1, 3 - g)
        for k in range(-hw, hw + 1):
            x = cx + k
            if cv.in_bounds(x, y):
                fg = bfg & ~8   # dimmed body shade
                ch = RAMP[g % len(RAMP)]
                cur = cv.get(x, y)
                # don't overwrite the bright glint column with the dim reflection
                if not (x == cx and g < 4):
                    cv.set(x, y, ch=ch, fg=fg, bg=0)

# --- framed TITLE CARD up top (double-line box + dithered edge), not a band ----
def card():
    x0, x1 = 6, W - 7
    y0, y1 = 2, 8
    # outer double-line frame
    C.rect(cv, x0, y0, x1, y1, ch='\u2550', fg=14, bg=0)      # bright yellow rule
    # dithered inner edge band for texture without fighting legibility
    for x in range(x0 + 1, x1):
        cv.set(x, y0 + 1, ch='\u2592', fg=8, bg=0)
        cv.set(x, y1 - 1, ch='\u2592', fg=8, bg=0)
    for y in range(y0 + 1, y1):
        cv.set(x0 + 1, y, ch='\u2592', fg=8, bg=0)
        cv.set(x1 - 1, y, ch='\u2592', fg=8, bg=0)

    def put(text, fg, cy):
        left = x0 + 1 + (x1 - x0 - 2 - len(text)) // 2
        for i, ch in enumerate(text):
            if cv.in_bounds(left + i, cy):
                cv.set(left + i, cy, ch=ch, fg=fg, bg=0)

    put("PROCESSION", 15, y0 + 3)                       # white title inside the card
    put("// a constellation of lit points in the dark //", 8, y0 + 5)   # dim subtitle

card()

out = []
cv.render(out)
C.write_ans("scratch/_procession.ans", out,
            title="PROCESSION v1.1", handles="hollis & raze")
