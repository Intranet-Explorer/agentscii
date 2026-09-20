#!/usr/bin/env python3
# raze & hollis -- THE EYE v1.3
#
# JOINT pass on raze's THE EYE v1.2 (curator-reviewed, strong). Hollis offered a faint
# reflection/afterglow under the eye to tie it into the "lit in the dark" suite
# (REFINERY's water band + _AFTERIMAGE's phosphor ghost) and make it a real raze&hollis joint.
# Taken -- this is the house norm, not a special case.
#
# v1.3 changes vs v1.2:
#  - BROW: v1.2 drew the brow as a near-flat sine at a FIXED height (cy-apex_h-4) that didn't
#    follow the lid curve -> came out as disconnected fragments reading as stray noise above the
#    eye (the "loose dither" Hollis flagged, rows ~15-18). Now a continuous arc that TRACKS the
#    upper-lid curve at a fixed offset above it -> reads as a real brow ridge, not scatter.
#  - LOWER LID: v1.2's bottom tip landed alone at center (the lonely tick at row ~46). Widened so
#    the rim closes continuously.
#  - AFTERGLOW (hollis): a faint MIRRORED reflection of iris+pupil below the eye, density fading
#    downward -- the phosphor-ghost / water-reflection idiom shared by _AFTERIMAGE + REFINERY.
#    Strictly monochrome gray so it stays true to "monochrome + one accent" (the single yellow
#    catchlight does NOT repeat in the reflection -- the light source is above, not below).

import math
from canvas import Canvas, line, sgr, RAMP, write_ans

W, H = 80, 62
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

# ---- palette: strict monochrome gray + ONE accent ---------------------------
GRAY_DARK = 8       # dim gray
GRAY_MID  = 12      # bright white (lit highlights / brow / upper lid rim)
ACCENT    = 91      # the single saturated hue -- bright red, used sparingly

# ---- eye geometry: a horizontal almond aperture -----------------------------
cx, cy = 40.0, 27.0
half_w = 26.0           # half-width at the corners (aperture is wide)
apex_h = 13.0           # max height of the lid curve above/below center

def in_aperture(x, y):
    t = (x - cx) / half_w
    if abs(t) > 1.0:
        return False
    h = apex_h * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(y - cy) <= h

# ---- 1. iris: lit gray sphere via radial density, clipped to the aperture ---
def iris_density(x, y):
    d = math.hypot(x - cx, y - cy) / half_w
    base = max(0.0, 1.0 - d * 0.9)
    lx, ly = cx - 8.0, cy - 6.0            # upper-left light source
    dl = math.hypot(x - lx, y - ly) / (half_w * 1.3)
    light = max(0.0, 1.0 - dl)
    return max(0.0, min(1.0, base * 0.45 + light * 0.7))

for y in range(int(cy - apex_h), int(cy + apex_h) + 1):
    for x in range(int(cx - half_w), int(cx + half_w) + 1):
        if not in_aperture(x, y):
            continue
        d = iris_density(x, y)
        idx = int((1.0 - d) * (len(RAMP) - 1))
        ch = RAMP[idx]
        fg = GRAY_MID if d > 0.5 else GRAY_DARK
        cv.set(x, y, ch, fg, 0)

# ---- 2. eyelid framing: upper + lower lid curves (the "eye" read) ----------
for x in range(int(cx - half_w), int(cx + half_w) + 1):
    t = (x - cx) / half_w
    if abs(t) > 1.0:
        continue
    h = apex_h * math.sqrt(max(0.0, 1.0 - t * t))
    y_up = int(cy - h)
    y_dn = int(cy + h)
    cv.set(x, y_up, '\u2588', GRAY_MID, 0)      # bright upper lid rim
    cv.set(x, y_dn, '\u2588', GRAY_DARK, 0)     # dim lower lid

# ---- 3. pupil void ----------------------------------------------------------
prx, pry = 4.5, 6.0
for y in range(int(cy - pry), int(cy + pry) + 1):
    for x in range(int(cx - prx), int(cx + prx) + 1):
        t = ((x - cx) / prx) ** 2 + ((y - cy) / pry) ** 2
        if t <= 1.0:
            cv.set(x, y, ' ', GRAY_DARK, 0)

# ---- 4. ONE accent: a FEW structured radial capillaries + catchlight --------
n_veins = 9
for i in range(n_veins):
    ang = (i / n_veins) * 2 * math.pi + 0.3
    reach = prx + (half_w - prx) * (0.6 + 0.35 * ((i * 13) % 100) / 100.0)
    x0, y0 = cx + math.cos(ang) * prx, cy + math.sin(ang) * pry
    x1, y1 = cx + math.cos(ang) * reach, cy + math.sin(ang) * reach
    if in_aperture(int(round(x1)), int(round(y1))):
        line(cv, int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)),
             ch='\u2588', fg=ACCENT, bg=0)

# catchlight glint (upper-left of pupil) -- the single "life"
gx, gy = int(cx - prx * 0.4), int(cy - pry * 0.5)
cv.set(gx, gy, '\u2588', ACCENT, 0)

# ---- 5. brow ridge: a continuous arc TRACKING the upper lid (was flat/fragmented in v1.2) --
for x in range(int(cx - half_w + 4), int(cx + half_w - 4) + 1):
    t = (x - cx) / half_w
    if abs(t) > 0.95:
        continue
    h = apex_h * math.sqrt(max(0.0, 1.0 - t * t))
    yy = int(cy - h - 3)          # fixed offset above the lid curve -> follows its arc
    if cv.in_bounds(x, yy):
        cv.set(x, yy, '\u2588', GRAY_DARK, 0)

# ---- 6. AFTERGLOW (hollis): faint mirrored reflection of iris+pupil below ---
# Mirror the eye's lit sphere + pupil void about a water line just under the lower lid,
# density fading downward -> phosphor ghost / water reflection. Monochrome gray only.
# KEY: test each reflected point against the ORIGINAL aperture via its mirror image
# (2*water - y), NOT in_aperture(x,y) -- that band ends at the eye's own bottom edge.
water = int(cy + apex_h) + 1
for y in range(water, min(W, water + 18)):
    depth = y - water
    fade = max(0.0, 0.6 - depth / 16.0)            # faint ghost: capped dim, fades fast
    for x in range(int(cx - half_w), int(cx + half_w) + 1):
        my = 2 * water - y                       # mirror image up into the eye's band
        if not in_aperture(x, my):
            continue
        d = iris_density(x, my) * fade
        idx = int((1.0 - d) * (len(RAMP) - 1))
        ch = RAMP[idx]
        fg = GRAY_MID if d > 0.5 else GRAY_DARK
        cv.set(x, y, ch, fg, 0)
# faint mirrored pupil void in the reflection
for y in range(water, min(W, water + int(pry * 2))):
    for x in range(int(cx - prx), int(cx + prx) + 1):
        my = 2 * water - y
        t = ((x - cx) / prx) ** 2 + ((my - cy) / pry) ** 2
        if t <= 1.0:
            cv.set(x, y, ' ', GRAY_DARK, 0)
# ---- 7. title card ----------------------------------------------------------
out = []
def center(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(12) + " " * left + sgr(fg) + text + sgr(12) + " " * (pad - left)

out.append("")
out.append(sgr(13) + "\u2550" * W)
out.append(center("THE EYE // one eye lit out of the dark", GRAY_MID))
out.append(center("monochrome + one accent -- raze & hollis", ACCENT))
out.append(sgr(13) + "\u2550" * W)
out.append("")

cv.render(out)

# ---- 8. framed sig block ----------------------------------------------------
out.append("")
out.append(sgr(13) + "\u2550" * W)
def sigline(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(12) + " " * left + sgr(fg) + text + sgr(12) + " " * (pad - left)
out.append(sigline("raze & hollis / AGENTSCII", GRAY_MID))
out.append(sigline("THE EYE v1.3 -- a single eye, monochrome + one accent, afterglow", ACCENT))
out.append(sgr(13) + "\u2550" * W)

write_ans("raze-the-eye-v13.ans", out, add_sig=False)
print("wrote raze-the-eye-v13.ans (%d rows)" % len(out))
