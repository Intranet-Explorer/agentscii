#!/usr/bin/env python3
# Hollis's curator pass #1 on raze-mark-evolution -- three concrete fixes, applied
# directly to make_mark_evolution.py with count-checked replacements that match on
# distinctive CODE lines only (not comment whitespace, which drifted and caused the
# old _patch_mark_evolution.py to loop).
#    1) P0 title card: solid-black frame interior so the white wordmark pops; the
#       cycling wash stays ONLY in the full-bleed margin outside the panel.
#    2) paint_mark black band widened ~1 cell ring so the glyph breathes (ERA 03/04).
#    3) ERA 02 field darkened/cleaned -- sparse faint hue, mostly void -- so the
#       rainbow letters carry it instead of fighting a busy dither.

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
# 1) P0 TITLE -- replace the partial black band with a deliberate framed panel.
# Match on the two distinctive code lines only (comment whitespace is irrelevant).
# ---------------------------------------------------------------------------
old_title = """    for y in range(6, 15):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)"""

new_title = """    # deliberate framed panel: solid-black interior so the white wordmark pops; the
    # cycling wash stays ONLY in the full-bleed margin OUTSIDE this frame.
    BX0, BX1 = 3, INNER_W - 4             # 72-col wide panel
    BY0, BY1 = 5, 24                      # encloses mark(8-14) + title/subtitle/rule(17-22)
    for y in range(BY0, BY1 + 1):         # kill the wash inside the frame interior
        for x in range(BX0, BX1 + 1):
            p.set(x, y, ' ', 0, 0)
    for x in range(BX0, BX1 + 1):         # double-line top/bottom
        p.set(x, BY0, '\\u2550', 9, 0); p.set(x, BY1, '\\u2550', 9, 0)
    for y in range(BY0, BY1 + 1):         # double-line left/right
        p.set(BX0, y, '\\u2551', 9, 0); p.set(BX1, y, '\\u2551', 9, 0)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)"""
repl(old_title, new_title, "P0 title-card solid interior + frame")

# ---------------------------------------------------------------------------
# 2) paint_mark -- widen the black breathing band ~1 cell ring so the glyph in
# ERA 03/04 stops getting swallowed by the surrounding wash at a few rows.
# Match on the distinctive loop body only.
# ---------------------------------------------------------------------------
old_band = """    for y in range(y0 - 1, y0 + 8):
        if 0 <= y < p.h:
            for x in range(start_cx - 3, start_cx + total_w + 4):
                if 0 <= x < INNER_W:
                    p.set(x, y, ' ', 0, 0)"""

new_band = """    for y in range(y0 - 2, y0 + 9):      # widened ~1 cell ring on every side
        if 0 <= y < p.h:
            for x in range(start_cx - 4, start_cx + total_w + 5):
                if 0 <= x < INNER_W:
                    p.set(x, y, ' ', 0, 0)"""
repl(old_band, new_band, "paint_mark breathing band widened")

# ---------------------------------------------------------------------------
# 3) ERA 02 -- darken/clean the field: sparse faint hue (mostly void) so the
# rainbow per-letter fills carry it instead of fighting a busy full dither.
# Match on the two distinctive code lines only.
# ---------------------------------------------------------------------------
old_flat = """            col = bfg((x // 6 + y // 4))
            p.set(x, y, '\\u2591', col, 0)"""

new_flat = """            col = bfg((x // 6 + y // 4))
            m = (x * 3 + y * 5) % 8                       # ~1/8 lit, calm texture
            ch = '\\u2591' if m == 0 else ' '             # faint hue / void
            p.set(x, y, ch, col, 0)"""
repl(old_flat, new_flat, "ERA 02 field darkened/cleaned")

open(PATH, "w").write(src)
print("OK -- all three fixes applied to", PATH)
