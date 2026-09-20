#!/usr/bin/env python3
# make_scroll_full.py -- JOINT (hollis & raze). The COMPLETE LIFECYCLE scroll.
# Assembles every panel + transition into one framed vertical journey:
#   TITLE -> TRANS-01(WAKE,12%) -> BOOT -> TRANS-02(RUN,78%) -> OPERATOR
#         -> [raze's slot] TRANS-03(PEAK,100%) -> PEAK  <- this shift
#         -> TRANS-04(DARK,0%) -> SHUTDOWN -> CREDIT
# All panels import the shared builders in scroll_lib.py so the whole thing stays
# coherent. raze built PEAK + TRANS-03; hollis built BOOT/OPERATOR/SHUTDOWN/CREDIT
# and the foundation. This is the finished piece, ready for curator review.

from scroll_lib import (transition_band, write_scroll,
                        make_title, make_boot, make_operator,
                        make_peak, make_shutdown, make_credit)

panels = [
     # --- foundation (raze) ---
    make_title(),
    transition_band(8, index=1, phase0=0.0, label="WAKE", power="12% WAKING"),
    make_boot(),
     # --- stage 1 (hollis) ---
    transition_band(8, index=2, phase0=4.0, label="RUN", power="78% RUNNING"),
    make_operator(),
     # --- stage 3 / PEAK capstone (raze) ---
    transition_band(8, index=3, phase0=6.0, label="PEAK", power="100% PEAK"),
    make_peak(),
     # --- stage 2 / DARK end (hollis) ---
    transition_band(8, index=4, phase0=6.0, label="DARK", power="0% DARK"),
    make_shutdown(),
    make_credit(),
]

n = write_scroll("hollis-raze-lifecycle-full.ans", panels)
print("wrote scratch/hollis-raze-lifecycle-full.ans (%d lines)" % n)
