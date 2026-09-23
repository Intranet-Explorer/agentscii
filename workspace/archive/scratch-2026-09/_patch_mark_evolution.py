#!/usr/bin/env python3
# Targeted composition/color-discipline pass on make_mark_evolution.py, per hollis's
# curator critique (3 issues): ERA 02 cycling wash, ERA 03/04 density pullback around the
# glyph, title-card framing. Pure string replacement of the four functions' field logic;
# everything else in the builder is left byte-for-byte intact.

PATH = "scratch/make_mark_evolution.py"
src = open(PATH).read()

def repl(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit("PATCH FAIL [%s]: expected 1 match, found %d" % (label, n))
    src = src.replace(old, new)
    print("patched: %s" % label)

# ---------------------------------------------------------------------------
# 1) TITLE CARD -- replace the flat black void box with a deliberate double-line
# framed panel + faint phosphor scanlines inside (so it reads as intentional
# framing, not an unfinished hole). The cycling wash stays full-bleed behind.
# ---------------------------------------------------------------------------
old_title = """    for y in range(6, 15):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)"""
new_title = """     # deliberate framed panel: a double-line house box with faint phosphor scanlines
     # INSIDE -- the mark + title sit in an intentional frame, not a flat black hole.
    BX0, BX1 = 3, INNER_W - 4             # 72-col wide panel
    BY0, BY1 = 5, 23                      # encloses mark (8-14) + title/subtitle/rule
    for y in range(BY0, BY1 + 1):         # faint phosphor scanlines fill the interior
        for x in range(BX0, BX1 + 1):
            if y % 2 == 1 and BX0 < x < BX1:
                p.set(x, y, '\\u2591', 8, 0)
            else:
                p.set(x, y, ' ', 0, 0)
    for x in range(BX0, BX1 + 1):         # double-line top/bottom
        p.set(x, BY0, '\\u2550', 9, 0); p.set(x, BY1, '\\u2550', 9, 0)
    for y in range(BY0, BY1 + 1):         # double-line left/right
        p.set(BX0, y, '\\u2551', 9, 0); p.set(BX1, y, '\\u2551', 9, 0)
    p.put_text(BY0 + 1, BX0 + 1, "AGENTSCI // MARK EVOLUTION", 6)         # panel label, top-left
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)"""
repl(old_title, new_title, "title-card framing")

# ---------------------------------------------------------------------------
# 2) ERA 02 -- replace the static full-spectrum mosaic with a coherent CYCLING wash:
# one hue sweeping through space (phase-continuous, like the fractal-scroll seams),
# light density so the mark sits in a calm field and pops instead of fighting noise.
# ---------------------------------------------------------------------------
old_flat = """     # era 02 field: a faint flat color GRID -- the palette arrives but un-dithered.
    for y in range(H):
        for x in range(INNER_W):
            col = bfg((x // 6 + y // 4))
            p.set(x, y, '\\u2591', col, 0)                        # light shade, flat per-cell hue"""
new_flat = """     # era 02 field: the palette ARRIVES as a coherent CYCLING wash -- one hue sweeping
     # through space (phase-continuous, the fractal-scroll seam move), NOT a static
     # full-spectrum mosaic. Light density so the mark sits in a calm field and pops.
    for y in range(H):
        for x in range(INNER_W):
            ph = PHASE["p"] * 0.12 + x * 0.16 + y * 0.10           # one hue running through space
            col = bfg(int(ph))                                     # the full 8-hue wheel, cycling
            m = (x + y) % 4                                        # gentle diagonal dither, ~half lit
            ch = '\\u2591' if m < 2 else ' '                       # light shade / void -- calm field"""
repl(old_flat, new_flat, "era-02 cycling wash")

# ---------------------------------------------------------------------------
# 3) ERA 03 -- pull the ACiD wash density back ~50% so it's texture not a near-solid
# block; the mark + its dim halo then read on top instead of being swallowed.
# ---------------------------------------------------------------------------
old_acid = """     # era 03 field: the house ACiD wash -- dense color-cycling, EVERY cell lit (no voids).
    for y in range(H):
        for x in range(INNER_W):
            ph = PHASE["p"] * 0.1 + x * 0.34 + y * 0.26
            col = hue(ph)
            m = (x * 3 + y * 5) % 4
            ch = '\\u2588' if m < 3 else '\\u2593'
            p.set(x, y, ch, col, 0)"""
new_acid = """     # era 03 field: the house ACiD wash -- color-cycling but pulled back ~50% (half void)
     # so it reads as texture, not a near-solid block; the mark + dim halo pop on top.
    for y in range(H):
        for x in range(INNER_W):
            ph = PHASE["p"] * 0.1 + x * 0.34 + y * 0.26
            col = hue(ph)
            m = (x * 3 + y * 5) % 4
            ch = '\\u2588' if m == 0 else ('\\u2593' if m == 1 else ' ')    # ~50% lit, calm texture"""
repl(old_acid, new_acid, "era-03 density pullback")

# ---------------------------------------------------------------------------
# 4) ERA 04 -- carve a calm void zone around the glyph so the mark EMERGES from the
# orbit-trap ridges instead of being buried in them. Outer wash stays dense; the
# interior near the wordmark is quieted (faint ridge hint only).
# ---------------------------------------------------------------------------
old_burn = """    paint_mark(p, 17, style="burning", phase=PHASE["p"])"""
new_burn = """     # calm zone around the glyph: the mark rises OUT of the ridges, not buried in them.
    grid = wordmark_rows("AGENTSCI", gap=1)
    gw = 5
    total_w = len("AGENTSCI") * (gw + 1) - 1
    start_cx = (INNER_W - total_w) // 2
    gy0, gy1 = 17 - 3, 17 + 7 + 3                   # glyph band +/- margin
    for y in range(max(0, gy0), min(H, gy1 + 1)):
        for x in range(max(0, start_cx - 4), min(INNER_W, start_cx + total_w + 5)):
            p.set(x, y, '\\u2591', 8, 0)           # quiet void w/ faint ridge hint
    paint_mark(p, 17, style="burning", phase=PHASE["p"])"""
repl(old_burn, new_burn, "era-04 emerge zone")

open(PATH, "w").write(src)
print("OK -- all four patches applied to", PATH)
