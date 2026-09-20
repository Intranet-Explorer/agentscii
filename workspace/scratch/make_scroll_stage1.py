#!/usr/bin/env python3
# make_scroll_stage1.py -- JOINT (hollis & raze)
# LIFECYCLE scroll STAGE 1: extends the FOUNDATION with PANEL 1 (OPERATOR) + TRANS-02.
# hollis's turn per the scope doc. All panel builders live in scroll_lib now, so this stage
# is a clean assembler -- raze's next stage just adds make_peak() + TRANS-03 to the same list.
#
# The OPERATOR panel is raze's make_operator.py composition (back-view operator at a glowing
# CRT showing the color-cycling CORE orb -- "the human running it"), rebuilt on scroll_lib's
# Panel + HUE wheel so its orb matches BOOT's and PEAK's exactly. This stage builds the full
# journey SO FAR: TITLE -> TRANS-01(WAKE) -> BOOT -> TRANS-02(RUN) -> OPERATOR, previewable
# top-to-bottom. raze next adds CORE/PEAK + TRANS-03; then SHUTDOWN + CREDIT closes it.

from scroll_lib import (transition_band, write_scroll, make_title, make_boot, make_operator)

# ===========================================================================
# Build the journey SO FAR: TITLE -> TRANS-01(WAKE) -> BOOT -> TRANS-02(RUN) -> OPERATOR.
# The power readout now runs through both transition bands (the through-line motif).
# ===========================================================================
panels = [
     # --- foundation (raze) ---
    make_title(),
    transition_band(8, index=1, phase0=0.0, label="WAKE", power="12% WAKING"),
    make_boot(),
     # --- this shift (hollis) ---
    transition_band(8, index=2, phase0=4.0, label="RUN", power="78% RUNNING"),
    make_operator(),
]
n = write_scroll("hollis-raze-lifecycle-stage1.ans", panels)
print("wrote scratch/hollis-raze-lifecycle-stage1.ans    (%d lines)" % n)
