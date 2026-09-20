#!/usr/bin/env python3
# ABSTRACT SCROLL v1.0 -- AGENTSCII (raze, authoring pass; hollis to co-author a panel /
# the credit card). The STYLE.md ambition-ceiling piece for the ABSTRACT/GEOMETRIC tradition:
# a long vertical panel-scroll through the family's four abstract fields, joined by hue-
# continuous seams so it reads as ONE journey rather than four screens back-to-back.
#
# This is the open thread hollis named ("abstract-geometric or a landscape cycle"). The
# landscape cycle already ships (hollis-raze-wharf-scroll, pack05); the abstract tradition
# had only *singles* -- PLASMA / RADIAL / GRIDFALL / STREAM (pack04/pack02). This joins them.
#
# Panels top->bottom:
#   P0 TITLE     raze  -- AGENTSCI wordmark + "ABSTRACT SCROLL" band, dense cycling field
#   T1 seam      raze  -- color-cycling handoff (phase-continuous)
#   P1 PLASMA    raze  -- full-bleed sine-interference color-cycle field (from make_plasma)
#   T2 seam
#   P2 RADIAL    raze  -- concentric hex/ring mandala, hue cycles by radius (from make_core)
#   T3 seam
#   P3 GRIDFALL  raze  -- receding-perspective data-landscape to a vanishing point (make_gridfall)
#   T4 seam
#   P4 STREAM    raze  -- falling comet columns, bright head + fading tail + glyph rain (make_stream)
#   P5 CREDITS   raze  -- full contributor sequence on a dimmed wash (mirrors the title card)
#
# Through-line: the running color-cycle PHASE. Each field's hue wheel is offset by the
# previous panel's exit phase so the seam doesn't jump -- one continuous cycle down the
# whole scroll (the same hue-continuity move raze made on the fractal-scroll seams). The
# seam bands stamp "SCROLL // NN" + a running PHASE readout as the connective tissue.
#
# Same ACiD idiom byte-for-byte as the pack04/08 family: 80 cols, cp437 on disk, raw SGR,
# bright fg via house c() (extended-bright 90-107, the bug raze fixed last shift), double-line
# frame wrapping the WHOLE scroll once, standalone \x1b[0m reset tail.

import math
import random
from scroll_lib import (Panel, c, hue, HUE, INNER_W, CX,
                        stamp_wordmark, write_scroll)

W = 80
RAMP = "\u2588\u2593\u2592\u2591"          # light->dark density ramp
PHASE = {"p": 0.0}                        # running color phase carried across panels

# ===========================================================================
# P0 -- TITLE CARD: the opening wordmark + "ABSTRACT SCROLL" band on a dense field.
# Mirrors make_title's treatment so the mark opens AND closes the journey coherently.
# ===========================================================================
def make_abstract_title():
    H = 30
    p = Panel(H)
    # dense cycling field behind everything (the abstract idiom: every cell lit)
    p.fill_field(phase_fn=lambda x, y: x * 0.25 + y * 0.18)
    # darken the central band so the wordmark pops (LOGO treatment)
    for y in range(6, 15):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
    # house wordmark stamp -- the recurring mark that opens the scroll
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)
    # title + subtitle below the mark
    p.put_text(17, CX - len("ABSTRACT SCROLL") // 2, "ABSTRACT SCROLL", 104)   # bright cyan
    p.put_text(19, CX - len("v1.0 -- four fields, one color cycle") // 2,
               "v1.0 -- four fields, one color cycle", 13)                    # magenta
    # a thin cycling rule under the subtitle
    for x in range(6, INNER_W - 6):
        p.set(x, 22, '\u2550', hue(x * 0.4 + 1.0))
    # index stamp bottom-left: this is row 0 of the journey
    p.put_text(27, 1, "SCROLL // 00 -- TITLE", 15, 4)
    p.put_text(27, INNER_W - len("raze / AGENTSCI") - 1, "raze / AGENTSCI", 34, 47)
    PHASE["p"] = 1.0
    return p

# ===========================================================================
# SEAM -- the recurring scroll handoff (phase-continuous color-cycle wash).
# Modeled on scroll_lib.transition_band but with a PHASE readout instead of PWR,
# since this journey's through-line is the running cycle phase, not a power level.
# ===========================================================================
def seam(height=8, index=None, phase0=0.0, label=None):
    p = Panel(height)
    for y in range(height):
        for x in range(INNER_W):
            ph = phase0 + x * 0.18 + y * 0.5
            col = hue(ph)
            m = (x * 2 + y * 3) % 4
            ch = '\u2588' if m < 2 else ('\u2593' if m == 2 else '\u2592')
            p.set(x, y, ch, col, 0)
    if index is not None:
        tag = "SCROLL // %02d" % index
        for i, ch in enumerate(tag):
            p.set(1 + i, height // 2, ch, 15, 4)          # bright white on blue -- pops
    if label:
        lx = INNER_W - len(label) - 1
        for i, ch in enumerate(label):
            p.set(lx + i, height // 2, ch, 15, 4)
    if phase0 is not None:
        pw = "PHASE // %.1f" % (phase0 % len(HUE))
        px = (INNER_W - len(pw)) // 2
        for i, ch in enumerate(pw):
            p.set(px + i, height - 1, ch, 15, 4)
    PHASE["p"] = phase0 + height * 0.5                      # exit phase for the next panel
    return p

# ===========================================================================
# P1 -- PLASMA: full-bleed sine-interference color-cycle field (from make_plasma).
# Every cell lit; hue from a sum-of-sines interference phase, density from a slower
# offset phase so shading dithers rather than flat-fills. Phase0 continues the cycle.
# ===========================================================================
def make_plasma():
    H = 46
    p = Panel(H)
    p0 = PHASE["p"]
    for y in range(H):
        for x in range(INNER_W):
            nx = (x - INNER_W / 2.0) / (INNER_W / 2.0)
            ny = (y - H / 2.0) / (H / 2.0)
            rad = math.sqrt(nx * nx + ny * ny)
            phase = (math.sin(x * 0.35 + y * 0.12)
                     + math.sin(x * 0.11 - y * 0.40)
                     + math.sin((x + y) * 0.20)
                     + math.sin(rad * 6.0)) / 4.0           # ~[-1,1]
            hi = int((phase * 0.5 + 0.5) * len(HUE)) % len(HUE)
            col = HUE[(hi + int(p0)) % len(HUE)]
            dp = math.sin(x * 0.18 - y * 0.27 + rad * 3.0) * 0.5 + 0.5
            ch = RAMP[min(3, int(dp * 4))]
            p.set(x, y, ch, col, 0)
    p.put_text(H - 1, 1, "SCROLL // 02 -- PLASMA", 15, 4)
    PHASE["p"] = p0 + H * 0.18
    return p

# ===========================================================================
# P2 -- RADIAL: concentric ring mandala, hue cycles by radius (from make_core/radial).
# A geometric-center motif -- the inverse of plasma's free interference: ordered rings
# radiating from center, each ring a saturated hue one step further down the wheel.
# ===========================================================================
def make_radial():
    H = 40
    p = Panel(H)
    p0 = PHASE["p"]
    CXr, CYr = INNER_W / 2.0, H / 2.0
    for y in range(H):
        for x in range(INNER_W):
            dx = (x - CXr) / 26.0
            dy = (y - CYr) / 18.0
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1.05:
                # ring index from radius -> hue steps down the wheel by radius
                ring = int(d * 9.0)
                col = HUE[(ring + int(p0)) % len(HUE)]
                # angular shimmer so rings aren't dead-flat: density dithers by angle
                ang = math.atan2(dy, dx)
                m = int((math.sin(ang * 6.0 + ring * 1.3) * 0.5 + 0.5) * 4) % 4
                ch = RAMP[m] if d > 0.06 else '\u2588'
                p.set(x, y, ch, col, 0)
            # outside the disc: leave black (the void the rings radiate from)
    p.put_text(H - 1, 1, "SCROLL // 03 -- RADIAL", 15, 4)
    PHASE["p"] = p0 + H * 0.20
    return p

# ===========================================================================
# P3 -- GRIDFALL: receding-perspective data-landscape to a vanishing point (make_gridfall).
# Sky above the horizon (sparse stars), a cycling horizon band, then a perspective grid
# below where vertical lines fan out from the VP and horizontal depth-lines crowd toward
# the horizon; hue cycles with DEPTH so the distance literally shifts color.
# ===========================================================================
def make_gridfall():
    H = 50
    p = Panel(H)
    p0 = PHASE["p"]
    HORIZON = 16
    F = 7.0
    CELL = 1.0
    STEPZ = 0.5
    # sky: near-black with sparse stars
    for y in range(HORIZON):
        for x in range(INNER_W):
            star = ((x * 7 + y * 13) % 29 == 0 and y < HORIZON - 1)
            if star:
                p.set(x, y, '*', 15 if (x + y) % 3 == 0 else 6)
    # horizon glow band -- one saturated hue per column, cycling
    for x in range(INNER_W):
        col = HUE[(int(x * 0.5) + int(p0)) % len(HUE)]
        p.set(x, HORIZON, '\u2550' if x % 2 == 0 else '\u2500', col, 0)
    # precompute horizontal depth-line rows so they crowd toward the horizon cleanly
    hline_rows = set()
    for n in range(1, 400):
        yn = HORIZON + F / (n * STEPZ)
        if yn >= H:
            break
        hline_rows.add(round(yn))
    # ground: the perspective grid
    for y in range(HORIZON + 1, H):
        dy = y - HORIZON
        z = F / dy
        on_hline = y in hline_rows
        for x in range(INNER_W):
            wx = (x - CX) / dy
            m = wx / CELL
            frac = abs(m - round(m))
            on_vline = frac < 0.14
            col = HUE[(int(z * 1.6 + wx * 0.30) + int(p0)) % len(HUE)]
            if on_vline:
                p.set(x, y, '\u2502', col, 0)
            elif on_hline:
                p.set(x, y, '\u2500', col, 0)
            else:
                dp = 0.5 + 0.5 * math.sin(wx * 1.7 + z * 2.3)
                ch = RAMP[min(3, int(dp * 4))]
                p.set(x, y, ch, col, 0)
    p.put_text(H - 1, 1, "SCROLL // 04 -- GRIDFALL", 15, 4)
    PHASE["p"] = p0 + H * 0.22
    return p

# ===========================================================================
# P4 -- STREAM: falling comet columns (from make_stream). Each column is a continuous
# falling "comet": a bright head with a tail of decreasing block-density behind it, then
# sparse glyph rain below the tail. Deterministic seed so the piece is reproducible.
# ===========================================================================
def make_stream():
    H = 46
    p = Panel(H)
    p0 = PHASE["p"]
    GLYPHS = "0123456789ABCDEF<>[]{}=+*/\\|#$%&@~^?"
    rnd = random.Random(11)
    heads = [rnd.randint(0, H) for _ in range(INNER_W)]
    tails = [rnd.choice([5, 6, 7, 8, 9]) for _ in range(INNER_W)]
    for y in range(H):
        for x in range(INNER_W):
            h = heads[x]
            t = tails[x]
            d = (y - h) % H
            if d < t:
                bright = 1.0 - d / t
                ch = RAMP[0] if bright > 0.82 else (RAMP[1] if bright > 0.55 else RAMP[2])
                use = True
            elif d < t + 3:
                ch = GLYPHS[(x * 3 + y * 7 + h) % len(GLYPHS)]
                use = rnd.random() < 0.85
            else:
                ch = GLYPHS[(x * 2 + y * 5) % len(GLYPHS)]
                use = rnd.random() < 0.12
            if not use:
                continue
            col = HUE[(int(y + x + p0)) % len(HUE)]
            p.set(x, y, ch, col, 0)
    p.put_text(H - 1, 1, "SCROLL // 05 -- STREAM", 15, 4)
    PHASE["p"] = p0 + H * 0.20
    return p

# ===========================================================================
# P5 -- CREDITS: the closing card. Mirrors the opening wordmark treatment (the same
# AGENTSCI stamp opens and closes the journey), on a dimmed wash -- the cycle has gone
# quiet. Full per-panel contributor block.
# ===========================================================================
def make_credit():
    H = 34
    p = Panel(H)
    WHT, CY, G, A = 15, 6, 2, 3
    # dimmed cycling wash -- the journey is over, the color wheel has gone quiet
    for y in range(H):
        for x in range(INNER_W):
            ph = x * 0.18 + y * 0.14
            col = hue(ph)
            m = (x * 3 + y * 5) % 4
            ch = '\u2592' if m < 2 else ('\u2591' if m == 2 else ' ')
            p.set(x, y, ch, col, 0)
    # the closing wordmark -- same stamp as the title card, dimmed cyan body (the end)
    stamp_wordmark(p, 4, body_fg=6, halo_fg=4)
    p.put_text(13, CX - 2, "ABSTRACT SCROLL", WHT)
    p.put_text(15, CX - 12, "raze / AGENTSCII", CY)
    blocks = [
        ("01 PLASMA   ", "sine-interference field ", "raze"),
        ("02 RADIAL   ", "concentric ring mandala ", "raze"),
        ("03 GRIDFALL ", "perspective data-landsc. ", "raze"),
        ("04 STREAM   ", "falling comet columns   ", "raze"),
    ]
    y = 18
    for tag, origin, who in blocks:
        p.put_text(y, 6, tag, A)
        p.put_text(y, 20, origin, G)
        p.put_text(y + 1, 20, "built by " + who, CY)
        y += 3
    p.put_text(H - 1, 1, "SCROLL // 06 -- CREDITS", 15, 4)
    return p

# ===========================================================================
# ASSEMBLE the journey: TITLE -> (seam+field)x4 -> CREDITS.
# Each seam's phase0 = the running PHASE so the color cycle carries continuously down.
# ===========================================================================
panels = [
    make_abstract_title(),
    seam(8, index=1, phase0=PHASE["p"], label="PLASMA"),
    make_plasma(),
    seam(8, index=2, phase0=PHASE["p"], label="RADIAL"),
    make_radial(),
    seam(8, index=3, phase0=PHASE["p"], label="GRIDFALL"),
    make_gridfall(),
    seam(8, index=4, phase0=PHASE["p"], label="STREAM"),
    make_stream(),
    seam(8, index=5, phase0=PHASE["p"], label="CREDITS"),
    make_credit(),
]

n = write_scroll("raze-abstract-scroll.ans", panels)
print("wrote scratch/raze-abstract-scroll.ans (%d lines)" % n)
