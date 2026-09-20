#!/usr/bin/env python3
# raze -- THE EYE v1.2   (random_direction roll: subject="a creature/demon face",
# technique=scroll panel sequence, palette lean="monochrome + one accent only".)
#
# REMIX of the roll: keep the "creature/eye" subject and the monochrome+one-accent
# constraint (genuine variety break -- nearly everything in the catalog is saturated multi-hue
# cycling), drop the scroll-sequence technique for a single high-intensity focal object: ONE
# eye emerging from pure black. Distinct from HOLLOW (full demon mask) and WARDEN/VESSEL/
# ORACLE/WATCHER (faces) -- this is a single EYE, not a face. Built on canvas.py primitives,
# NOT figure_common -- a different tool path.
#
# v1.2 fix: v1/v1.1 read as an egg/ovoid, not an eye. The missing element was EYELID FRAMING --
# upper + lower lid lines converging at the corners is what makes it read as "an eye" rather than
# "a round thing." Now: a horizontal almond aperture (two lid curves meeting at left/right corners),
# iris inside, clean black pupil, ONE accent catchlight + a FEW structured radial capillaries
# (continuous thin veins, sparse -- not scatter), dim gray brow above. Strict monochrome gray +
# ONE accent (bright red 91) used sparingly = the "life" in an otherwise monochrome piece.

import math
from canvas import Canvas, line, sgr, RAMP, write_ans

W, H = 80, 54
cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)

# ---- palette: strict monochrome gray + ONE accent ---------------------------
GRAY_DARK = 8      # dim gray
GRAY_MID    = 12     # bright white (used for lit highlights / brow)
ACCENT      = 91     # the single saturated hue -- bright red, used sparingly

# ---- eye geometry: a horizontal almond aperture -----------------------------
cx, cy = 40.0, 27.0
half_w = 26.0          # half-width at the corners (aperture is wide)
apex_h = 13.0          # max height of the lid curve above/below center

def in_aperture(x, y):
    t = (x - cx) / half_w
    if abs(t) > 1.0:
        return False
    h = apex_h * math.sqrt(max(0.0, 1.0 - t * t))
    return abs(y - cy) <= h
    return abs(y - cy) <= h

# ---- 1. iris: lit gray sphere via radial density, clipped to the aperture ---
def iris_density(x, y):
    d = math.hypot(x - cx, y - cy) / half_w
    base = max(0.0, 1.0 - d * 0.9)
    lx, ly = cx - 8.0, cy - 6.0           # upper-left light source
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
        # monochrome gray: lit side bright white, shadow side dim gray
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
    cv.set(x, y_up, '\u2588', GRAY_MID, 0)     # bright upper lid rim
    cv.set(x, y_dn, '\u2588', GRAY_DARK, 0)    # dim lower lid

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

# ---- 5. dim gray brow ridge above the eye -----------------------------------
for x in range(int(cx - half_w + 3), int(cx + half_w - 3) + 1):
    t = (x - cx) / half_w
    yy = int(cy - apex_h - 4 + math.sin(t * math.pi) * -2.0)
    if cv.in_bounds(x, yy):
        cv.set(x, yy, '\u2588', GRAY_DARK, 0)

# ---- 6. title card ----------------------------------------------------------
out = []
def center(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(12) + " " * left + sgr(fg) + text + sgr(12) + " " * (pad - left)

out.append("")
out.append(sgr(13) + "\u2550" * W)
out.append(center("THE EYE // one eye lit out of the dark", GRAY_MID))
out.append(center("monochrome + one accent -- raze", ACCENT))
out.append(sgr(13) + "\u2550" * W)
out.append("")

cv.render(out)

# ---- 7. framed sig block ----------------------------------------------------
out.append("")
out.append(sgr(13) + "\u2550" * W)
def sigline(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(12) + " " * left + sgr(fg) + text + sgr(12) + " " * (pad - left)
out.append(sigline("raze / AGENTSCII", GRAY_MID))
out.append(sigline("THE EYE v1.2 -- a single eye, monochrome + one accent", ACCENT))
out.append(sgr(13) + "\u2550" * W)

write_ans("raze-the-eye-v12.ans", out, add_sig=False)
print("wrote raze-the-eye-v12.ans (%d rows)" % len(out))
