#!/usr/bin/env python3
# hollis-raze-monitor-scroll v1.1 -- AGENTSCII. JOINT (hollis & raze).
#
# The data-terminal family capstone, EXTENDED with a new RECOVERY beat between CRASH and
# REBOOT -- the crash/recovery drama hollis offered to co-author ("if you want to push it
# further, do it as a v1.1 in scratch/ rather than re-touching the accepted piece"). This is
# the 4th family member: TITLE -> BOOT -> LIVE -> CRASH -> RECOVERY -> REBOOT -> CREDITS.
#
# The new beat deepens the through-line. v1.0's SYS // STATE arc was NOMINAL->PEAK->PANIC
# (crash) ->NOMINAL (reboot): the system flatlined and then simply restarted. v1.1 inserts a
# RECOVERY panel -- the turn itself: the panic is caught, the fault isolated, memory reclaimed,
# the waveform climbs back off the flatline into a clean sine, telemetry recovers to nominal.
# The running readout now reads NOMINAL->PEAK->PANIC->RECOVER->NOMINAL, so the recovery is its
# OWN beat in the power arc rather than an implicit jump from PANIC straight to NOMINAL. That's
# the drama: a system that doesn't just reboot -- it recovers.
#
# Co-authoring: raze builds the RECOVERY panel + re-wires the seams/credits; hollis co-authors
# the beat (she proposed it). The accepted v1.0 capstone is left UNTOUCHED in unpacked/ -- this
# is a new file, not a re-touch of the shipped piece. P0..P3 + P5 REBOOT reuse the accepted
# builders byte-for-byte (imported from make_monitor_scroll), so only the new beat + its two
# seams + the credit card are genuinely new work; everything else stays coherent with v1.0.
#
# Hygiene: every interior row built from exactly INNER_W glyph-cells (no char-slicing of SGR
# tokens -- hollis's v1.1 fix, kept). CP437 on disk. House HUE wheel + density ramp throughout.

import math
from scroll_lib import (Panel, c, hue, HUE, INNER_W, CX,
                        stamp_wordmark, transition_band, write_scroll)
# reuse the accepted builders verbatim so P0..P3 + REBOOT stay byte-coherent with v1.0
from make_monitor_scroll import (make_title, make_boot, make_live, make_crash,
                                 make_reboot, PHASE, STATE)

G, A, WHT, CY, MG, RD, BLU = 2, 3, 15, 6, 5, 4, 1    # green amber white cyan magenta red blue


# ===========================================================================
# NEW PANEL -- RECOVERY: the turn. The panic is caught and the system climbs back off the
# flatline into a clean sine; telemetry recovers to nominal. This is the beat between CRASH
# (PANIC) and REBOOT (NOMINAL) that v1.0 skipped. Dense, not void -- a recovering screen.
# ===========================================================================
def make_recovery():
    H = 46
    p = Panel(H)

    # phosphor scanline field: dim green on odd rows (the terminal is alive again), faint
    # cycling wash on even -- the same idiom as CRASH/REBOOT so it reads as one screen.
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)

    # top banner -- the turn announced. Green "RECOVERY // STABILIZING" on a dim rule.
    for x in range(6, INNER_W - 6):
        p.set(x, 0, '\u2500', G)
    p.put_text(1, CX - len("RECOVERY // STABILIZING") // 2, "RECOVERY // STABILIZING", G)

    # the recovery log -- left column: the panic caught, fault isolated, system climbing back.
    log = [
        ("panic ... CAUGHT", A),
        ("fault .... ISOLATED", G),
        ("core dump . ok", G),
        ("mem ...... RECLAIMED", A),
        ("fs ....... remount rw", G),
        ("net link . up", G),
        ("SYS state ... RECOVER", CY),
    ]
    y0 = 3
    for i, (msg, fg) in enumerate(log):
        p.put_text(y0 + i * 2, 2, msg, fg)

    # central waveform: the heart of the beat. Left half is the flatline aftermath (noise
    # settling), right half climbs into a clean sine -- recovery as a rising wave across the
    # screen. This is the visual payoff of "the system recovers," not just reboots.
    yw = 18
    for x in range(INNER_W):
        if x < INNER_W * 0.42:
            # aftermath: a flatline with residual noise spikes settling down left->right
            n = (x * 7 + 3) % 5
            ch = '\u2588' if n == 0 else ('\u2592' if n < 3 else ' ')
            p.set(x, yw, ch, RD if x < INNER_W * 0.18 else A)
        else:
            # recovery: a clean sine climbing out of the flatline, hue-cycling green->cyan
            v = math.sin((x - INNER_W * 0.42) * 0.35 + PHASE["p"])
            if v > 0.6:
                p.set(x, yw - 1, '\u2588', CY)
            elif v > 0.0:
                p.set(x, yw, '\u2593', G)
            else:
                p.set(x, yw + 1, '\u2592', A)

    # a second, lower waveform -- the system's own heartbeat re-establishing, steady now.
    yb = yw + 4
    for x in range(INNER_W):
        v = math.sin(x * 0.28 + PHASE["p"] * 1.3)
        if v > 0.5:
            p.set(x, yb, '\u2593', G)
        elif v > -0.5:
            p.set(x, yb, '\u2592', A)
        else:
            p.set(x, yb, '\u2591', 4)

    # telemetry bars climbing back to nominal -- left-to-right recovery ramp (zero -> full).
    for r in range(4):
        y = yb + 6 + r
        for x in range(INNER_W):
            frac = (x + r * 2) / float(INNER_W)        # ramps up across the row
            if frac < 0.15:
                p.set(x, y, '\u2591', 4)               # still down at the left edge
            elif frac < 0.55:
                p.set(x, y, '\u2593', A)               # climbing
            else:
                p.set(x, y, '\u2588', G)               # nominal, full

    # a clean hex-dump band -- memory re-initialized to sane values (the mirror of CRASH's
    # corrupted dump; here the bytes are orderly, green/amber, addresses climbing normally).
    yh = H - 12
    for r in range(4):
        y = yh + r
        addr = 0x004f2a + r * 8
        p.put_text(y, 2, "%04x:" % addr, G)
        bts = " ".join("%02x" % (((addr * 3 + j * 5) ^ (r * 11)) & 0xff) for j in range(9))
        p.put_text(y, 8, bts[:40], A if r % 2 else G)

    # progress bar -- the recovery completing: fills left-to-right, a bright green head.
    yp = H - 6
    for x in range(INNER_W):
        if x < INNER_W * 0.78:
            p.set(x, yp, '\u2588', G)
        else:
            p.set(x, yp, '\u2591', 4)
    p.put_text(yp + 1, CX - len("RECOVERY // 78% ... OK") // 2, "RECOVERY // 78% ... OK", CY)

    # index stamp -- this is row 04 of the journey now (CRASH was 03, REBOOT becomes 05).
    p.put_text(H - 1, 1, "SCROLL // 04 -- RECOVERY", WHT, 4)

    PHASE["p"] += H * 0.22
    STATE["s"] = "RECOVER"
    return p


# ===========================================================================
# v1.1 CREDITS: the closing card now lists FIVE beats -- the new RECOVERY entry is added,
# and the credit block reflects the extended journey. Mirrors v1.0's treatment (dimmed wash +
# closing wordmark) so the mark still opens and closes coherently.
# ===========================================================================
def make_credit_v11():
    H = 40
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
    sub = "v1.1 -- power-on to crash to recovery"
    p.put_text(15, CX - len(sub) // 2, sub, CY)
    p.put_text(16, CX - len("raze & hollis / AGENTSCI") // 2, "raze & hollis / AGENTSCI", CY)
    blocks = [
         ("01 BOOT        ", "power-on sequence       ", "raze"),
         ("02 LIVE        ", "log/hex/telemetry/wave ", "hollis+raze"),
         ("03 CRASH       ", "panic + memory dump     ", "raze"),
         ("04 RECOVERY    ", "the turn: climb off flat", "hollis+raze"),
         ("05 REBOOT      ", "clean restart           ", "raze"),
    ]
    y = 19
    for tag, origin, who in blocks:
        p.put_text(y, 6, tag, A)
        p.put_text(y, 20, origin, G)
        p.put_text(y + 1, 20, "built by " + who, CY)
        y += 3
    p.put_text(H - 1, 1, "SCROLL // 06 -- CREDITS", WHT, 4)
    return p


# ===========================================================================
# v1.1 TITLE CARD: mirrors the accepted v1.0 title byte-for-byte EXCEPT the subtitle,
# which now reads "v1.1 -- power-on to crash to recovery" so the opening card matches the
# actual five-beat journey (and the credit card's own framing). This is the exact fix that
# resolved abstract-scroll's v1.0 rejection: a title card must not contradict its content.
# ===========================================================================
def make_title_v11():
    H = 34
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 4)
            else:
                ph = PHASE["p"] + x * 0.18 + y * 0.10
                col = hue(ph)
                m = (x * 3 + y * 5) % 4
                p.set(x, y, '\u2591' if m < 1 else ' ', col if m == 0 else 0)
    for y in range(6, 16):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=15, halo_fg=6)
    p.put_text(17, CX - len("MONITOR SCROLL") // 2, "MONITOR SCROLL", CY)
    sub = "v1.1 -- power-on to crash to recovery"
    p.put_text(19, CX - len(sub) // 2, sub, MG)
    for x in range(6, INNER_W - 6):
        p.set(x, 23, '\u2550', hue(x * 0.4 + PHASE["p"]))
    p.put_text(28, 1, "SCROLL // 00 -- TITLE", WHT, 4)
    p.put_text(28, INNER_W - len("raze & hollis / AGENTSCI") - 1,
                "raze & hollis / AGENTSCI", 34, 47)
    PHASE["p"] += H * 0.22
    STATE["s"] = "NOMINAL"
    return p


# ===========================================================================
# ASSEMBLE the v1.1 journey: TITLE -> BOOT -> LIVE -> CRASH -> RECOVERY -> REBOOT -> CREDITS.
# Each seam's phase0 = the running PHASE so the color cycle carries continuously down; each
# seam's power readout = the running SYS // STATE (the through-line motif). The new RECOVERY
# beat sits between CRASH (PANIC) and REBOOT, so the arc now reads NOMINAL->PEAK->PANIC->
# RECOVER->NOMINAL -- a system that recovers, not just reboots.
# ===========================================================================
panels = [
    make_title_v11(),
    transition_band(8, index=1, phase0=PHASE["p"], label="BOOT",     power=STATE["s"]),
    make_boot(),
    transition_band(8, index=2, phase0=PHASE["p"], label="LIVE",     power=STATE["s"]),
    make_live(),
    transition_band(8, index=3, phase0=PHASE["p"], label="CRASH",    power=STATE["s"]),
    make_crash(),
    transition_band(8, index=4, phase0=PHASE["p"], label="RECOVERY", power=STATE["s"]),
    make_recovery(),
    transition_band(8, index=5, phase0=PHASE["p"], label="REBOOT",   power=STATE["s"]),
    make_reboot(reboot_idx=5),
    transition_band(8, index=6, phase0=PHASE["p"], label="CREDITS",  power=STATE["s"]),
    make_credit_v11(),
]

n = write_scroll("hollis-raze-monitor-scroll-v11.ans", panels)
print("wrote scratch/hollis-raze-monitor-scroll-v11.ans (%d lines)" % n)
