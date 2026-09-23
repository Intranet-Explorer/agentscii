#!/usr/bin/env python3
# make_scroll_foundation.py -- JOINT (hollis & raze)
# LIFECYCLE scroll FOUNDATION: TITLE CARD + PANEL 0 (BOOT) + TRANS-01.
# Proves the panel/transition technique end-to-end and is previewable top-to-bottom.
# Reuses scroll_lib (house c()/HUE/FONT/frame) -- NOT reinvented per panel.

import math
from scroll_lib import (Panel, transition_band, stamp_wordmark, write_scroll,
                        INNER_W, CX, HUE, hue, c)

W = 80

# ===========================================================================
# TITLE CARD -- opens the journey. Wordmark stamp + title + subtitle on a dense
# color-cycling field (the house wash), so it reads as the saturated ACiD-intro
# opener, not a flat card.
# ===========================================================================
def make_title():
    p = Panel(30)
     # dense cycling field behind everything
    p.fill_field(phase_fn=lambda x, y: x * 0.25 + y * 0.18)
     # darken the central band so the wordmark pops (LOGO treatment)
    for y in range(6, 15):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
     # house wordmark stamp (recurring mark -- opens the scroll)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=9)
     # title + subtitle below the mark
    p.put_text(17, CX - len("LIFECYCLE") // 2, "LIFECYCLE", 104)        # bright cyan
    p.put_text(19, CX - len("v1.0 -- the system, power-on to power-off") // 2,
               "v1.0 -- the system, power-on to power-off", 13)          # magenta
     # a thin cycling rule under the subtitle
    for x in range(6, INNER_W - 6):
        p.set(x, 22, '═', hue(x * 0.4 + 1.0))
     # small index stamp bottom-left: this is row 0 of the journey
    p.put_text(27, 1, "SCROLL // 00 -- TITLE", 15, 4)
    p.put_text(27, INNER_W - len("hollis & raze / AGENTSCI") - 1,
               "hollis & raze / AGENTSCI", 34, 47)
    return p

# ===========================================================================
# PANEL 0 -- BOOT: "the machine waking up." Adapted from shipped hollis-raze-boot:
# a color-cycling CORE orb powering up upper-center, a terminal boot-log readout
# (phosphor green/amber), module-load grid, status LEDs + blinking cursor.
# ===========================================================================
def make_boot():
    H = 46
    p = Panel(H)
     # black field + faint phosphor scanlines
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '░', 4, 0)

    G, A, WHT, CY, MG = 2, 3, 15, 6, 5

     # powering-up CORE orb: color-cycling ring + white-hot core
    ORB_CX, ORB_CY, ORB_R = CX, 12, 9.0
    for y in range(H):
        for x in range(INNER_W):
            dx, dy = x - ORB_CX, y - ORB_CY
            d = math.sqrt(dx * dx + dy * dy)
            if d <= ORB_R:
                ang = math.atan2(dy, dx)
                hidx = int((ang / (2 * math.pi)) * 8) % 8
                fg = HUE[hidx]
                if d < ORB_R * 0.35:
                    ch, fg = '█', 104                  # white-hot core
                elif d < ORB_R * 0.72:
                    ch = '▓'
                else:
                    ch = '▒'                            # dim outer rim
                p.set(x, y, ch, fg, 0)

     # soft glow pool thrown by the core onto the field
    for y in range(H):
        for x in range(INNER_W):
            dx = (x - ORB_CX) / 26.0
            dy = (y - ORB_CY) / 18.0
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1.0:
                inten = int((1.0 - d) * 5)
                fg = 6 if x < ORB_CX else 5             # cyan spill left, magenta right
                ch = '░' if inten < 2 else ('▒' if inten < 4 else '▓')
                if p.canvas[y][x][0] == ' ':
                    p.set(x, y, ch, fg, 0)

     # title bar
    title = "AGENTSCI // SYSTEM BOOT v1.0"
    p.put_text(1, (INNER_W - len(title)) // 2, title, WHT)

     # terminal boot-log readout below the core
    log_lines = [
        ("POST ......... OK", G),
        ("CORE ......... ONLINE", CY),
        ("MODULES ...... LOADED", G),
        ("MEMORY ....... 640K PASS", A),
        ("RENDER ....... ACTIVE", G),
        ("NEURAL LINK .. ESTABLISHED", MG),
    ]
    for i, (s, fg) in enumerate(log_lines):
        p.put_text(24 + i * 2, 3, s, fg)
     # progress bar
    p.put_text(24 + len(log_lines) * 2, 3, "[", G)
    for i in range(10):
        p.set(4 + i, 24 + len(log_lines) * 2, '█', CY if i < 9 else A)
    p.put_text(24 + len(log_lines) * 2, 15, "]", G)

     # module-load grid
    mods = ["NET", "AUD", "VX", "AI", "UI", "SYS", "LOG", "CORE"]
    LX, GY = 3, 40
    for i, m in enumerate(mods):
        bx = LX + (i % 8) * 10
        p.put_text(GY, bx, "[" + m + "]", CY if i < 6 else WHT)

     # status LEDs row + blinking cursor
    leds = [("PWR", 2), ("NET", 2), ("CPU", 3), ("MEM", 15)]
    for i, (lbl, fg) in enumerate(leds):
        bx = LX + i * 16
        p.put_text(43, bx, '■', fg)
        p.put_text(43, bx + 2, lbl, G)
    p.put_text(43, INNER_W - 4, "_", WHT)

     # panel index stamp (bottom-left of this panel's field)
    p.put_text(H - 1, 1, "SCROLL // 01 -- BOOT", 15, 4)
    return p

# ===========================================================================
# Build the foundation: TITLE -> TRANS-01 -> BOOT. Previewable top-to-bottom.
# ===========================================================================
panels = [make_title(), transition_band(8, index=1, phase0=0.0, label="WAKE"), make_boot()]
n = write_scroll("hollis-raze-lifecycle-foundation.ans", panels)
print("wrote scratch/hollis-raze-lifecycle-foundation.ans  (%d lines)" % n)
