#!/usr/bin/env python3
# raze -- THE WATCHER // AGENTSCII  (single high-contrast PORTRAIT)  v3
#
# hollis seeded the skeleton (make_watcher.py, "v2") and left me a precise
# make-human pass -- the SAME pattern he ran on PROCESSION v1->v1.1 (he opens the
# bones, raze carves them into anatomy). His four structural calls:
#    1) CRANIUM SILHOUETTE was a smooth ellipse -> reads egg/skull. Restructure so
#       the upper third is BROAD and it tapers through cheekbones to a NARROW jaw/chin
#       point. An egg outline can't read as a face no matter how many features you bolt
#       on; the silhouette itself must carry the read.
#    2) JAW / CHIN: a jaw that flares at the cheekbone then tapers to a point.
#    3) CHEEKBONE: a lit ridge across the mid-face separating the cheek hollow from the jaw.
#    4) NOSE TIP: define a tip + nostril shadow at the base so it reads as a nose.
#
# v3 (raze make-human pass): three real bugs in v2, all structural:
#    (a) the profile was a smooth dome->taper = an EGG. A face's WIDEST point is the
#        CHEEKBONE, not the cranium top; the jaw must be narrower than the cheekbone and
#        taper to a chin point below it. New keyframes put the flare at the cheekbone.
#    (b) facial features were painted WITHOUT clipping to the skull silhouette, so a bright
#        block protruded past the right edge of the head = a glitch read. Every feature now
#        clips to in_head() so nothing escapes the cranium.
#    (c) the head was too ELONGATED (20 rows tall, 17 wide = eggplant) and the light split
#        too soft (lmax=34 -> everything mid-gray). Compacted the cranium to ~17 rows tall /
#        ~18 wide (roughly square, like a real head) and pushed lmax down to 12 with near-zero
#        ambient so the lit left side is bright and the shadow right side falls to TRUE BLACK.
#
# REGISTER DECISION (hollis left this open): keep MINIMAL HIGH-CONTRAST, not dense saturated
# acid. Rationale -- a saturated acid portrait would just duplicate the existing raze-portrait-
# acid; the genuine variety gap is ONE face lit from ONE source with the shadow side in black.
# That's the distinct voice that pairs with PROCESSION ("seven lit points in the dark" -> "one
# face lit out of the dark"). hollis leaned minimal too; I'm matching it and noting the call.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_common as F

W = 80
H = 56
CX = W / 2.0

# --- light source: upper-left, single directional source ---------------------
LX, LY = 33.0, 15.0                 # light from upper-left -> right (shadow) side falls to black
AMBIENT = 0.03                      # near-zero ambient: shadow side reads as TRUE void (high contrast)

def L(x, y):
    return F.light_field(x, y, LX, LY, lmax=12.0, ambient=AMBIENT)

cv = F.new_canvas(h=H, w=W)

# ============================================================================
# 1) CRANIUM SILHOUETTE -- the make-human pass. A keyframed half-width profile
#     (lit left side wider than shadow right side = a 3/4 turn toward the light).
#    Compact cranium dome -> CHEEKBONE flare (widest, ~y=15) -> SHARP jaw taper to chin point.
# ============================================================================

# keyframes: (y, left_halfwidth, right_halfwidth) measured from CX
# the WIDEST row is the cheekbone (~y=15), not the cranium top -- that's what makes
# it read as a face, not an egg. The jaw below the cheek tapers hard to a chin point.
KEYS = [
    (11.0, 4.5, 3.6),        # rounded cranium top -- narrow dome
    (13.0, 9.2, 7.0),        # upper cranium widening fast
    (15.0, 10.0, 7.8),       # CHEEKBONE flare -- WIDEST point of the whole head
    (17.5, 9.4, 7.2),        # just below the cheekbone, begin taper
    (20.0, 7.6, 5.6),        # jaw narrowing
    (23.0, 5.6, 4.0),        # lower jaw
    (25.5, 3.6, 2.6),        # chin approaching a point
    (28.0, 1.4, 1.0),        # CHIN POINT -- narrow, not an egg bottom
]

def _interp(y):
    if y < KEYS[0][0]:
        return None
    if y > KEYS[-1][0]:
        return None
    for i in range(len(KEYS) - 1):
        y0, l0, r0 = KEYS[i]
        y1, l1, r1 = KEYS[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return (l0 + t * (l1 - l0), r0 + t * (r1 - r0))
    return None

def head_lhw(y):
    p = _interp(y)
    return p[0] if p else None

def head_rhw(y):
    p = _interp(y)
    return p[1] if p else None

def in_head(x, y):
    lh = head_lhw(y)
    rh = head_rhw(y)
    if lh is None:
        return False
    return int(round(CX - lh)) <= x <= int(round(CX + rh))

def skull_region(x, y):
    return in_head(x, y)

# base head surface, shaded by the single light field -> lit left, dark right
F.shade_region(cv, skull_region, L, base_fg=8, hot_fg=15)

# --- neck / shoulders: a bust -----------------------------------------------
def neck_region(x, y):
    return 27 <= y <= 31 and int(CX - 3.6) <= x <= int(CX + 3.6)
F.shade_region(cv, neck_region, L, base_fg=8, hot_fg=13)

def shoulder_region(x, y):
    if not (29 <= y <= 45):
        return False
    t = (y - 29) / 16.0
    hw = 3.0 + t * 24.0                  # start narrow at the neck, flare to base
    return int(CX - hw) <= x <= int(CX + hw)
F.shade_region(cv, shoulder_region, L, base_fg=8, hot_fg=12)

# ============================================================================
# 2) JAW / CHIN -- a jaw that flares at the cheekbone then tapers to a point.
#    Carved as its own shaded surface so it reads as form under the cranium.
# ============================================================================
def jaw_region(x, y):
    if not (15 <= y <= 28):
        return False
    return in_head(x, y)
F.shade_region(cv, jaw_region, L, base_fg=8, hot_fg=14)

# ============================================================================
# 3) CHEEKBONE -- a lit ridge across the mid-face separating the cheek hollow
#    from the jaw. A short diagonal band that catches the most light on its
#    upper-left edge and falls off into the hollow below it. CLIPPED to the head.
# ============================================================================
def cheekbone(x, y):
    if not (13 <= y <= 17):
        return False
    cy = 15.0 - (x - CX) * 0.30        # diagonal ridge: higher on the lit side
    d = abs(y - cy)
    return d <= 1.4 and in_head(x, y)
F.shade_region(cv, cheekbone, lambda x, y: L(x, y) * 1.15, base_fg=8, hot_fg=15)

# cheek hollow: a deep dimmed region on the shadow side under the cheekbone (clipped)
def cheek_hollow(x, y):
    if not (17 <= y <= 23):
        return False
    cx = CX + 3.0
    d = ((x - cx) ** 2 + (y - 20) ** 2)
    return d <= 16.0 and in_head(x, y)
def L_hollow(x, y):
    return max(AMBIENT * 0.5, L(x, y) * 0.40)
F.shade_region(cv, cheek_hollow, L_hollow, base_fg=8, hot_fg=10)

# ============================================================================
# 4) NOSE -- a bridge down the center-left with a defined TIP + nostril shadow
#    at its base so it reads as a nose, not a vertical ridge. All clipped to head.
# ============================================================================
def nose_bridge(x, y):
    if not (13 <= y <= 21):
        return False
    t = (y - 13) / 8.0
    cx = CX - 2.2 + t * 1.0
    hw = 1.3 + t * 0.7
    return int(cx - hw) <= x <= int(cx + hw) and in_head(x, y)
F.shade_region(cv, nose_bridge, L, base_fg=7, hot_fg=14)

# NOSE TIP: a small lit catch at the base of the bridge (the tip catches light)
def nose_tip(x, y):
    if not (19 <= y <= 22):
        return False
    cx = CX - 1.0
    d = ((x - cx) ** 2 + (y - 20.5) ** 2)
    return d <= 4.0 and in_head(x, y)
F.shade_region(cv, nose_tip, lambda x, y: L(x, y) * 1.15, base_fg=8, hot_fg=15)

# NOSE CAST SHADOW + NOSTRILS: a dark band on the right of the ridge (clipped)
def nose_shadow(x, y):
    if not (16 <= y <= 22):
        return False
    t = (y - 13) / 8.0
    cx = CX - 2.2 + t * 1.0
    return int(cx + 1.1) <= x <= int(cx + 2.6) and in_head(x, y)
def L_shadow(x, y):
    return max(AMBIENT * 0.4, L(x, y) * 0.35)
F.shade_region(cv, nose_shadow, L_shadow, base_fg=8, hot_fg=10)

# two nostril pockets at the tip base (clipped to head)
for nx in (int(CX - 2), int(CX)):
    if in_head(nx, 21):
        F.set_cell(cv, nx, 21, "\u2592", 8, 0)

# --- brow ridge: the single most "anatomical" read -- light side -------------
F.brow_ridge(cv, CX - 3.0, 14.5, halfw=3.8, light=L, base_fg=8, hot_fg=15)

# --- RIM LIGHT: a faint bright edge along the shadow-side (right) contour ----
# so the dark half reads as lit-from-behind, not missing.
def rim_edge(x, y):
    rh = head_rhw(y)
    if rh is None:
        return False
    right = int(round(CX + rh))
    return x == right and 13 <= y <= 26
F.shade_region(cv, rim_edge, lambda x, y: max(0.45, L(x, y)), base_fg=94, hot_fg=94)

# --- the eye: a CONSTRUCTED eye (socket -> iris -> glint), light side only ----
# 3/4 head = single visible eye on the lit side; the shadow-side eye is lost to black.
F.eye(cv, CX - 3.5, 15.5, r=1.6, iris_fg=96, glint=True)          # cyan iris -> house focal accent

# a second, faint catch-light just emerging from the shadow side -- one cell, so
# the face reads as turned and alive rather than blank on the dark half (clipped).
if in_head(int(CX + 3.5), 15):
    F.set_cell(cv, int(CX + 3.5), 15, "\u2591", 8, 0)

# --- mouth: a thin lit line, slightly open (teeth primitive = faint grin read) -
F.teeth(cv, int(CX - 3.0), int(CX + 1.0), 23, n=4)
# jaw/chin shadow: a dark band under the mouth to define the chin point (clipped)
def jaw_shadow(x, y):
    if not (24 <= y <= 28):
        return False
    t = (y - 24) / 4.0
    hw = 4.0 * (1.0 - t * 0.7)
    cx = CX - 1.0
    return int(cx - hw) <= x <= int(cx + hw) and in_head(x, y)
def L_jawshadow(x, y):
    return max(AMBIENT * 0.4, L(x, y) * 0.35)
F.shade_region(cv, jaw_shadow, L_jawshadow, base_fg=8, hot_fg=10)

# --- title card up top (framed double-rule, echoes PROCESSION's framing) -------
out = []
title_rows = [
     "",
    F.sgr(96) + "\u2550" * W + F.RESET,
     " " * 30 + F.sgr(97) + "THE WATCHER" + F.RESET,
     " " * 24 + F.sgr(90) + "// one face lit out of the dark //" + F.RESET,
    F.sgr(96) + "\u2550" * W + F.RESET,
     "",
]

# --- closing credit sequence below the bust (echoes PROCESSION v2's close) -----
credit_rows = [
     "",
    F.sgr(94) + "\u2551" * W + F.RESET,
     " " * 30 + F.sgr(96) + "THE WATCHER" + F.RESET,
     " " * 28 + F.sgr(90) + "// lit by one source, the rest is black //" + F.RESET,
     " " * 26 + F.sgr(97) + "hollis & raze / AGENTSCII" + F.RESET,
     " " * 24 + F.sgr(94) + "THE WATCHER v3.0 -- joint" + F.RESET,
    F.sgr(94) + "\u2551" * W + F.RESET,
     "",
]

out.extend(title_rows)
F.render(cv, out)
out.extend(credit_rows)

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_watcher_v3.ans")
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\n" + F.RESET)

print("wrote", path, "rows:", len(out))
F.hygiene_gate(path)
