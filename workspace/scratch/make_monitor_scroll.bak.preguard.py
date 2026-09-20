#!/usr/bin/env python3
# hollis-raze-monitor-scroll -- AGENTSCII. JOINT (hollis & raze).
#
# The data-terminal family capstone: a long vertical panel-scroll through the life of a
# live system monitor, joined by phase-continuous seams so it reads as ONE journey rather
# than five screens back-to-back. Extends hollis's single-screen terminal-monitor foundation
# (scratch/hollis-terminal-monitor.ans) into the STYLE.md ambition-ceiling format -- the same
# move raze made on the fractal-scroll and abstract-scroll capstones.
#
# Journey:  TITLE -> BOOT -> LIVE MONITOR -> CRASH/RECOVERY -> REBOOT -> CREDITS
# Through-line motif carried through every seam: a running "SYS // STATE" readout --
#   NOMINAL -> PEAK -> PANIC -> RECOVER -> NOMINAL
# the terminal analog of the lifecycle WAKE->RUN->PEAK->DARK power arc and the abstract
# PHASE color-cycle. That is the connective tissue (a recurring mark + a running readout).
#
# Who did what:
#   P0 TITLE       raze -- AGENTSCI wordmark + "MONITOR SCROLL" band on a phosphor field
#   seams T1..T5   raze -- transition_band color-cycle handoffs, phase-continuous, each
#                          carrying the running SYS // STATE readout (the through-line)
#   P1 BOOT        raze -- power-on: core orb powering up + streaming boot log + module grid
#   P2 LIVE        hollis->raze -- the heart: LOG STREAM | HEX DUMP, TELEMETRY bars, WAVEFORM
#                          (ported from hollis's foundation; raze lifted it into a Panel)
#   P3 CRASH       raze -- kernel panic cascade, corrupted hex dump, flatlined waveform, spike
#   P4 REBOOT      raze -- clean restart, nominal again -- the cycle closes
#   P5 CREDITS     raze -- closing wordmark dimmed + full per-panel contributor block
#
# Hygiene: every interior row built from exactly INNER_W glyph-cells (no char-slicing of SGR
# tokens -- hollis's v1.1 fix, kept). CP437 on disk. House HUE wheel + density ramp throughout.

import math
from scroll_lib import (Panel, c, hue, HUE, INNER_W, CX,
                        stamp_wordmark, transition_band, write_scroll)

PHASE = {"p": 0.0}                       # running color phase carried across panels
STATE = {"s": "NOMINAL"}                 # running system-state readout (the through-line)

# house phosphor palette: green/amber terminal on black, with the ACiD wheel for peaks
G, A, WHT, CY, MG, RD, BLU = 2, 3, 15, 6, 5, 4, 1   # green amber white cyan magenta red blue

# ===========================================================================
# P0 -- TITLE CARD: AGENTSCI wordmark + "MONITOR SCROLL" band on a phosphor field.
# Mirrors the abstract/fractal title treatment so the mark opens AND closes coherently.
# ===========================================================================
def make_title():
    H = 34
    p = Panel(H)
    # phosphor scanline field: dim green ░ on odd rows, faint cycling wash on even
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
            else:
                ph = PHASE["p"] + x * 0.18 + y * 0.10
                col = hue(ph)
                m = (x * 3 + y * 5) % 4
                p.set(x, y, '\u2591' if m < 1 else ' ', col if m == 0 else 0)
    # darken the central band so the wordmark pops (LOGO treatment)
    for y in range(6, 16):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0)
    # house wordmark stamp -- the recurring mark that opens the scroll
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=6)
    # title + subtitle below the mark
    p.put_text(17, CX - len("MONITOR SCROLL") // 2, "MONITOR SCROLL", CY)
    sub = "v1.0 -- the system, power-on to power-off"
    p.put_text(19, CX - len(sub) // 2, sub, MG)
    # a thin cycling rule under the subtitle
    for x in range(6, INNER_W - 6):
        p.set(x, 23, '\u2550', hue(x * 0.4 + PHASE["p"]))
    # index stamp bottom-left + credit bottom-right
    p.put_text(28, 1, "SCROLL // 00 -- TITLE", WHT, 4)
    p.put_text(28, INNER_W - len("raze & hollis / AGENTSCI") - 1,
               "raze & hollis / AGENTSCI", 34, 47)
    PHASE["p"] += H * 0.18
    return p

# ===========================================================================
# P1 -- BOOT: "the machine waking up." A color-cycling CORE orb powering up upper-center,
# a streaming terminal boot-log readout (phosphor green/amber), a module-load grid, status
# LEDs + a blinking cursor. The system comes online.
# ===========================================================================
def make_boot():
    H = 46
    p = Panel(H)
    # black field + faint phosphor scanlines
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
    # powering-up CORE orb: color-cycling ring + white-hot core (upper center)
    ORB_CX, ORB_CY, ORB_R = CX, 11, 8.0
    for y in range(H):
        for x in range(INNER_W):
            dx, dy = x - ORB_CX, y - ORB_CY
            d = math.sqrt(dx * dx + dy * dy)
            if d <= ORB_R:
                ang = math.atan2(dy, dx)
                hidx = int((ang / (2 * math.pi)) * 8) % 8
                fg = HUE[hidx]
                if d < ORB_R * 0.45:
                    p.set(x, y, '\u2588', WHT)          # white-hot core
                elif d < ORB_R * 0.75:
                    p.set(x, y, '\u2593', fg)            # bright ring
                else:
                    p.set(x, y, '\u2592', fg)            # outer glow
    # boot-log readout streaming up the left two-thirds (phosphor green/amber)
    log = [
        ("POST ......... ok", G),
        ("CPU 0 ........ detected", G),
        ("MEM 640K base / 1536K ext", A),
        ("FS mount /dev/sda1 ok", G),
        ("NET link up 10.0.0.1", G),
        ("KERNEL v1.0 loaded", A),
        ("MODULE net .... [OK]", G),
        ("MODULE fs ..... [OK]", G),
        ("MODULE gpu .... [OK]", A),
        ("SYS state ... NOMINAL", CY),
    ]
    y0 = 22
    for i, (msg, fg) in enumerate(log):
        p.put_text(y0 + i, 2, msg, fg)
    # blinking cursor at the end of the log
    p.set(2 + len(log[9]), y0 + len(log), '\u2588', G)
    # module-load grid (right column): a small lattice of [OK]/[..] cells
    gx, gy = 46, 22
    for r in range(5):
        for cc in range(3):
            tag = "[OK]" if (r * 3 + cc) % 4 != 0 else "[..]"
            fg = G if tag == "[OK]" else A
            p.put_text(gy + r * 2, gx + cc * 6, tag, fg)
    # status LEDs row
    led_y = 41
    for i in range(8):
        p.set(2 + i * 9, led_y, '\u2588', [G, A, CY, MG][i % 4])
        p.put_text(led_y + 1, 6 + i * 9, "L%02d" % i, G)
    # index stamp
    p.put_text(H - 1, 1, "SCROLL // 01 -- BOOT", WHT, 4)
    PHASE["p"] += H * 0.20
    STATE["s"] = "NOMINAL"
    return p

# ===========================================================================
# P2 -- LIVE MONITOR: the heart of the journey. Ported from hollis's terminal-monitor
# foundation into a Panel: two-column LOG STREAM | HEX DUMP, then a full-width TELEMETRY
# bar-graph strip and a phosphor WAVEFORM trace. The system running nominal -- alive.
# ===========================================================================
def make_live():
    H = 46
    p = Panel(H)
    # black field + faint scanlines behind the panels
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
    # panel header rule: LOG STREAM | HEX DUMP
    p.put_text(0, 1, "LOG STREAM", CY)
    for x in range(1, INNER_W):
        if x != 38 and not (1 <= x - 1 < len("LOG STREAM")):
            pass
    # simple header rule row
    for x in range(INNER_W):
        p.set(x, 0, '\u2500', 6)
    p.put_text(0, 1, "LOG STREAM", CY)
    p.set(38, 0, '\u252c', 6)
    p.put_text(0, 40, "HEX DUMP", CY)

    # two-column body: log stream (left, x 1..37) | hex dump (right, x 40..77)
    LOG = [
        ("91", "boot: kernel ok"),
        ("96", "net: link up 10.0.0.1"),
        ("93", "warn: cache miss 0x4f2a"),
        ("95", "load: 0.42 procs 128"),
        ("92", "fs: mount /dev/sda1 ok"),
        ("96", "net: rx 4096 tx 2048"),
        ("93", "warn: temp 71C fan 2"),
        ("91", "mem: 512k free 128k"),
        ("94", "gpu: render 60fps ok"),
        ("96", "net: ping 12ms ok"),
        ("93", "warn: disk 87% used"),
        ("92", "cpu: core0 44% core1 51%"),
    ]
    yb = 2
    for i in range(12):
        fg, msg = LOG[i % len(LOG)]
        # left column: severity-coded log line (truncate safely to 36 chars)
        p.put_text(yb + i, 1, msg[:36], int(fg))
        # right column: hex dump -- addr:8bytes ascii gutter
        addr = i * 8
        bts = " ".join("%02x" % ((addr * 7 + j * 13 + 5) & 0xff) for j in range(8))
        asc = "".join(chr(((addr * 7 + j * 13 + 5) & 0x5f) | 0x40) for j in range(8))
        p.put_text(yb + i, 40, "%04x:" % addr, 96)
        p.put_text(yb + i, 46, bts[:23], 92)
        p.put_text(yb + i, 70, asc, 107)
    # mid rule between the two-column body and the telemetry strip
    ym = yb + 12
    for x in range(INNER_W):
        p.set(x, ym, '\u2500', 6)
    p.put_text(ym, 1, "TELEMETRY", CY)
    p.set(38, ym, '\u252c', 6)
    p.put_text(ym, 40, "WAVEFORM", CY)

    # telemetry: ASCII bar-graph strip (full width), rows ym+1 .. ym+6
    for r in range(6):
        y = ym + 1 + r
        for x in range(INNER_W):
            v = (math.sin(x * 0.35 + r * 0.4) + math.sin(x * 0.11 - r * 0.7)) / 2.0
            h = int((v + 1) * 3.5)
            if h >= 6:   p.set(x, y, '\u2588', 95)
            elif h >= 4: p.set(x, y, '\u2593', 93)
            elif h >= 2: p.set(x, y, '\u2592', 96)
            else:        p.set(x, y, '\u2591', 91)
    # waveform trace: a phosphor sine riding the bottom of the strip
    for r in range(3):
        y = ym + 7 + r
        for x in range(INNER_W):
            base = math.sin(x * 0.25 + r * 0.9)
            d = abs(base * 3.0 - (r - 1))
            if d < 1.0:   p.set(x, y, '\u2588', CY)
            elif d < 2.0: p.set(x, y, '\u2592', 96)
    # index stamp
    p.put_text(H - 1, 1, "SCROLL // 02 -- LIVE", WHT, 4)
    PHASE["p"] += H * 0.20
    STATE["s"] = "PEAK"
    return p

# ===========================================================================
# P3 -- CRASH / RECOVERY: the dramatic peak of the arc. A kernel-panic cascade in red/
# magenta, a corrupted hex dump (garbled bytes), a flatlined waveform that spikes, telemetry
# bars slamming to max then dropping to zero -- then a green "RECOVERY // INITIATED" pulse at
# the bottom. High tension, then the turn toward recovery.
# ===========================================================================
def make_crash():
    H = 46
    p = Panel(H)
     # black field; the whole panel is "the screen dying" -- dense, not void
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
     # kernel-panic cascade -- red/magenta error lines scrolling up the top-left
    panic = [
         ("!! KERNEL PANIC @ 0x004f2a", RD),
         ("!! segfault core dumped", MG),
         ("!! net: link LOST", RD),
         ("!! fs: I/O error /dev/sda1", MG),
         ("!! mem: OOM killer invoked", RD),
         ("!! gpu: render HANG", MG),
         ("!! SYS state ... PANIC", RD),
    ]
    y0 = 1
    for i, (msg, fg) in enumerate(panic):
         # glitch: jitter the x origin a little per line so it reads as corrupting
        jx = 2 + ((i * 7) % 3)
        p.put_text(y0 + i, jx, msg[:40], fg)
     # corrupted hex dump (right side, garbled bytes flickering between real and noise)
    yb = 1
    for i in range(7):
        addr = 0x4f2a + i * 8
        bts = " ".join("%02x" % (((addr * 3 + j * 5) ^ (i * 11)) & 0xff) for j in range(8))
        p.put_text(yb + i, 46, "%04x:" % addr, RD if i % 2 else MG)
        p.put_text(yb + i, 52, bts[:23], MG)
     # flatlined waveform: a single flat line across the middle, then a noise spike band
    yflat = 10
    for x in range(INNER_W):
        p.set(x, yflat, '\u2580', RD)
    for r in range(3):
        y = yflat + 1 + r
        for x in range(INNER_W):
             # noise spike: random-ish tall bars in a central band, flat elsewhere
            if 30 < x < 50 and ((x * 7 + r * 13) % 5 == 0):
                p.set(x, y, '\u2588', MG)
            elif (x * 3 + r) % 11 == 0:
                p.set(x, y, '\u2592', RD)
     # full-width MEMORY DUMP band -- the system spewing raw memory as it dies. This fills
     # the middle so the panel reads dense (a dying screen), not like a render bug.
    yd = 14
    for r in range(8):
        y = yd + r
        addr = 0xdead00 + r * 16
        for x in range(INNER_W):
             # raw memory bytes as hex pairs, cycling red/magenta/white, glitched
            b = ((addr * 5 + x * 7 + r * 3) & 0xff)
            if (x + r) % 2 == 0:
                ch = "0123456789abcdef"[(b >> 4) & 0xf]
            else:
                ch = "0123456789abcdef"[b & 0xf]
            fg = [RD, MG, WHT][(x + r) % 3]
            p.set(x, y, ch, fg)
     # telemetry bars slamming to max then dropping to zero (left-to-right decay)
    for r in range(4):
        y = yd + 9 + r
        for x in range(INNER_W):
            if x < INNER_W * 0.5:
                p.set(x, y, '\u2588', RD)           # slammed to max
            else:
                p.set(x, y, '\u2591', 4)            # dropped to zero
     # recovery pulse -- the turn: a green "RECOVERY // INITIATED" line + a rising bar
    yr = H - 6
    for x in range(INNER_W):
        p.set(x, yr, '\u2500', G)
    p.put_text(yr + 1, CX - len("RECOVERY // INITIATED") // 2, "RECOVERY // INITIATED", G)
    for r in range(3):
        y = yr + 2 + r
        for x in range(INNER_W):
            if (x * 5 + r * 7) % 4 == 0:
                p.set(x, y, '\u2592', G)
     # index stamp
    p.put_text(H - 1, 1, "SCROLL // 03 -- CRASH", WHT, 4)
    PHASE["p"] += H * 0.22
    STATE["s"] = "PANIC"
    return p

# ===========================================================================
# P4 -- REBOOT: clean restart. A fresh boot log, nominal readouts, the core orb back up
# bright -- the cycle closes where it opened (the same idiom as BOOT, but resolved/calm).
# ===========================================================================
def make_reboot():
    H = 46
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
    # core orb back up, bright and steady (same geometry as BOOT -- the cycle closes)
    ORB_CX, ORB_CY, ORB_R = CX, 11, 8.0
    for y in range(H):
        for x in range(INNER_W):
            dx, dy = x - ORB_CX, y - ORB_CY
            d = math.sqrt(dx * dx + dy * dy)
            if d <= ORB_R:
                ang = math.atan2(dy, dx)
                hidx = int((ang / (2 * math.pi)) * 8) % 8
                fg = HUE[hidx]
                if d < ORB_R * 0.45:
                    p.set(x, y, '\u2588', WHT)
                elif d < ORB_R * 0.75:
                    p.set(x, y, '\u2593', fg)
                else:
                    p.set(x, y, '\u2592', fg)
    # fresh boot log -- the clean restart
    log = [
        ("REBOOT ......... ok", G),
        ("POST ........... ok", G),
        ("CPU 0 .......... online", G),
        ("MEM ............ nominal", A),
        ("FS mount ....... ok", G),
        ("NET link up .... ok", G),
        ("KERNEL v1.0 ... reloaded", A),
        ("SYS state ... NOMINAL", CY),
    ]
    y0 = 22
    for i, (msg, fg) in enumerate(log):
        p.put_text(y0 + i, 2, msg, fg)
    p.set(2 + len(log[7]), y0 + len(log), '\u2588', G)   # cursor, steady now
    # nominal telemetry: a calm, even bar strip (the system is healthy again)
    for r in range(4):
        y = 40 + r
        for x in range(INNER_W):
            v = math.sin(x * 0.2 + r * 0.5)
            if v > 0.3:   p.set(x, y, '\u2593', G)
            elif v > -0.3: p.set(x, y, '\u2592', A)
            else:         p.set(x, y, '\u2591', 4)
    # index stamp
    p.put_text(H - 1, 1, "SCROLL // 04 -- REBOOT", WHT, 4)
    PHASE["p"] += H * 0.20
    STATE["s"] = "NOMINAL"
    return p

# ===========================================================================
# P5 -- CREDITS: the closing card. Mirrors the opening wordmark treatment (the same AGENTSCI
# stamp opens and closes the journey) on a dimmed wash -- the cycle has gone quiet. Full
# per-panel contributor block.
# ===========================================================================
def make_credit():
    H = 37
    p = Panel(H)
    # dimmed cycling wash -- the journey is over, the color wheel has gone quiet
    for y in range(H):
        for x in range(INNER_W):
            ph = PHASE["p"] + x * 0.18 + y * 0.14
            col = hue(ph)
            m = (x * 3 + y * 5) % 4
            p.set(x, y, '\u2592' if m < 2 else ('\u2591' if m == 2 else ' '), col if m == 0 else 0)
    # the closing wordmark -- same stamp as the title card, dimmed cyan body (the end)
    stamp_wordmark(p, 4, "AGENTSCI", body_fg=6, halo_fg=4)
    p.put_text(13, CX - len("MONITOR SCROLL") // 2, "MONITOR SCROLL", WHT)
    p.put_text(15, CX - len("raze & hollis / AGENTSCI") // 2, "raze & hollis / AGENTSCI", CY)
    blocks = [
        ("01 BOOT       ", "power-on sequence      ", "raze"),
        ("02 LIVE       ", "log/hex/telemetry/wave ", "hollis+raze"),
        ("03 CRASH      ", "panic + recovery pulse ", "raze"),
        ("04 REBOOT     ", "clean restart          ", "raze"),
    ]
    y = 18
    for tag, origin, who in blocks:
        p.put_text(y, 6, tag, A)
        p.put_text(y, 20, origin, G)
        p.put_text(y + 1, 20, "built by " + who, CY)
        y += 3
    p.put_text(H - 1, 1, "SCROLL // 05 -- CREDITS", WHT, 4)
    return p

# ===========================================================================
# ASSEMBLE the journey: TITLE -> BOOT -> LIVE -> CRASH -> REBOOT -> CREDITS.
# Each seam's phase0 = the running PHASE so the color cycle carries continuously down;
# each seam's power readout = the running SYS // STATE (the through-line motif).
# ===========================================================================
panels = [
    make_title(),
    transition_band(8, index=1, phase0=PHASE["p"], label="BOOT",     power=STATE["s"]),
    make_boot(),
    transition_band(8, index=2, phase0=PHASE["p"], label="LIVE",     power=STATE["s"]),
    make_live(),
    transition_band(8, index=3, phase0=PHASE["p"], label="CRASH",    power=STATE["s"]),
    make_crash(),
    transition_band(8, index=4, phase0=PHASE["p"], label="REBOOT",   power=STATE["s"]),
    make_reboot(),
    transition_band(8, index=5, phase0=PHASE["p"], label="CREDITS",  power=STATE["s"]),
    make_credit(),
]

n = write_scroll("hollis-raze-monitor-scroll.ans", panels)
print("wrote scratch/hollis-raze-monitor-scroll.ans (%d lines)" % n)
