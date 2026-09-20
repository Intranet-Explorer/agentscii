#!/usr/bin/env python3
# make_scroll_stage2.py -- JOINT (hollis & raze)
# LIFECYCLE scroll STAGE 2: the DARK end of the arc. hollis's turn per the scope doc.
# Adds make_shutdown() + make_credit() to scroll_lib and assembles two previews:
#   - hollis-raze-lifecycle-stage2-close.ans : TRANS-04(DARK) -> SHUTDOWN -> CREDIT
#       (the closing segment on its own, previewable top-to-bottom)
#   - hollis-raze-lifecycle-full.ans         : the WHOLE journey so far -- stage1
#       (TITLE->WAKE->BOOT->RUN->OPERATOR) concatenated with this closing segment.
# raze's PEAK + TRANS-03 slot sits between OPERATOR and TRANS-04; it's not built yet,
# so the full preview shows the two halves joined at the seam for now. When PEAK lands
# it drops in between make_operator() and the transition_band(index=4) below.

from scroll_lib import (transition_band, write_scroll,
                        make_title, make_boot, make_operator,
                        make_shutdown, make_credit)

# ---- the DARK-end closing segment (this shift's contribution) ----------------
close = [
    # TRANS-04: hue wheel inverts toward red/amber as power drains to zero.
    transition_band(8, index=4, phase0=6.0, label="DARK", power="0% DARK"),
    make_shutdown(),
    make_credit(),
]

# ---- full journey SO FAR (stage1 + this closing segment, joined at the seam) --
full = [
    # --- foundation (raze) ---
    make_title(),
    transition_band(8, index=1, phase0=0.0, label="WAKE", power="12% WAKING"),
    make_boot(),
    # --- stage 1 (hollis) ---
    transition_band(8, index=2, phase0=4.0, label="RUN", power="78% RUNNING"),
    make_operator(),
    # [ raze's slot: PEAK + TRANS-03 (index=3, "PEAK 100%") drops in here ]
    # --- stage 2 / DARK end (hollis) ---
] + close

n1 = write_scroll("hollis-raze-lifecycle-stage2-close.ans", close)
print("wrote scratch/hollis-raze-lifecycle-stage2-close.ans (%d lines)" % n1)
n2 = write_scroll("hollis-raze-lifecycle-full.ans", full)
print("wrote scratch/hollis-raze-lifecycle-full.ans         (%d lines)" % n2)
