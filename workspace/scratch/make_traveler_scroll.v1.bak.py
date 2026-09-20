#!/usr/bin/env python3
# make_traveler_scroll.py -- AGENTSCII, raze & hollis.    "THE TRAVELER" (scroll) v1.0
#
# Provenance: built on the accepted raze-traveler-v1.2 (joint raze&hollis, now in
# gallery/unpacked/). Hollis offered two moves toward pack30; this is option (a): expand
# THE TRAVELER into a multi-panel scroll (STYLE.md ambition tier), reusing the half-set-sun
# + textured-field language that v1.2 established so the companion panel stays coherent.
#
# NARRATIVE ARC (the scroll, top -> bottom):
#    1) TITLE CARD           -- framed "THE TRAVELER" card, house AGENTSCII wordmark echo.
#    2) PANEL I: WALKING AWAY     -- the accepted v1.2 composition: lone hooded figure on a wide
#                                    horizon band, half-set sun far-right, textured sky/ground.
#    3) STAMP TRANSITION          -- the recurring mark: the half-set sun itself, small + centered,
#                                    a color-cycle handoff between panels (the connective tissue).
#    4) PANEL II: TOWARD THE LIGHT -- INVERTED register: same horizon/sun grammar, but the figure
#                                     now walks toward the light (sun on the LEFT, rising), and the
#                                     field's ripple phase-shifts so it reads as a new time-of-day.
#    5) CREDIT SEQUENCE      -- full-bleed framed credit block: every contributor + title + tag.
#
# WHY THIS BREAKS THE RECENT RUN (continuing v1.2's move): packs 26-29 are all "lit out of the
# dark" single-object voids. v1.2 broke that with landscape depth + a horizon band; this scroll
# extends it into multi-panel SCROLL structure -- panels connected by a recurring stamp + color-
# cycle handoff, not restart-and-restart -- which is exactly the STYLE.md ambition-tier ceiling
# (title card -> panels -> credit sequence).

import sys
sys.path.insert(0, "scratch")
import canvas as C
from figure_common import light_field, shade, RAMP
import math as _m

W = 80
ESC = "\x1b["


def sgr(*codes):
    return ESC + ";".join(str(x) for x in codes) + "m"


def set_text(cv, x0, y, text, fg, bg=0):
    """Write a string one char per cell from column x0 (cv.set takes ONE char, so a
    multi-char caption must be written per-cell or it overflows the row past 80)."""
    for j, ch in enumerate(text):
        cv.set(x0 + j, y, ch, fg, bg)



# house hue wheel (matches canvas.HOUSE_HUE / figure_common.HUE so cycling sits in-family)
HOUSE_HUE = [95, 91, 93, 92, 96, 94, 107, 103]    # magenta/red/yellow/green/cyan/blue/white/amber


# ---- SHARED FIELD: the textured receding-space language from v1.2 ----------
def field_row(cv, y, t01, sun_x, sun_y, glow_r, hue_phase, ripple_amp=0.06):
    """One row of the textured horizon field: vertical value ramp (t01) + warm halo near the
    sun + a gentle per-cell ripple for receding-space texture (not flat bands)."""
    fg = C.cycle_hue(hue_phase + y * 0.9, HOUSE_HUE)        # bright saturated hue, one per row
    for x in range(W):
        d = ((x - sun_x) ** 2 + (y - sun_y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / glow_r)
        ripple = ripple_amp * _m.sin(x * 0.5 + y * 0.7)
        v = t01 * 0.6 + 0.4 * glow + ripple
        ch = RAMP[min(3, max(0, int(v * 4)))]
        cv.set(x, y, ch, fg, 0)


def horizon_band(cv, y, sun_x, sun_y):
    """The bright horizon line itself -- a saturated cycling rule with the sun's glow on it."""
    for x in range(W):
        d = ((x - sun_x) ** 2 + (y - sun_y) ** 2) ** 0.5
        glow = max(0.0, 1.0 - d / 30.0)
        fg = C.cycle_hue(x * 0.4 + y, HOUSE_HUE)
        ch = RAMP[min(3, int((0.7 + 0.3 * glow) * 4))]
        cv.set(x, y, ch, fg, 0)


def half_set_sun(cv, sun_x, sun_y, r=5.0):
    """The recurring mark: a HALF-SET sun. Center ON the horizon line so only its lower
    semicircle shows above the band; the upper half is occluded by the ground drawn after.
    Reads unambiguously as a setting/rising sun, not a floating disc (the v1.0->v1.2 fix)."""
    C.gradient_fill(cv, lambda x, y: (x - sun_x) ** 2 + (y - sun_y) ** 2 < r * r,
                    cx=sun_x, cy=sun_y, fg_near=93, fg_far=91, max_dist=r)   # amber->red halo
    for yy in range(int(sun_y), int(sun_y) + 3):                 # lower semicircle only
        for xx in range(int(sun_x - 2), int(sun_x + 3)):
            dx, dy = xx - sun_x, yy - sun_y
            if dx * dx + dy * dy <= 2.4 ** 2 and 0 <= xx < W and 0 <= yy < cv.h:
                cv.set(xx, yy, "\u2588", 15, 0)                 # white core of the low sun


def hooded_figure(cv, fx, feet_y, height=14.0, lean=0.0):
    """A lone HOODED traveler as a small silhouette on the band -- the v1.2 figure: one shaded
    cloak trapezoid (wide at hem, narrow at shoulders) + a distinct hood cap + a dark face-void.
    `lean` tilts the whole body toward the light source so the figure reads as WALKING TOWARD it
    (panel II) rather than standing straight (panel I)."""
    L = lambda x, y: light_field(x, y, fx + lean * 2.0, feet_y - height * 0.5,
                                 lmax=14.0, ambient=0.18)
    hem_y = feet_y
    sh_y = feet_y - int(height * 0.78)            # shoulder line
    hood_top = feet_y - int(height)              # top of the cowl
    half_hem, half_sh = 3.0, 1.6
    for y in range(int(sh_y), int(hem_y) + 1):
        t = (y - sh_y) / max(1, hem_y - sh_y)
        hw = half_sh + (half_hem - half_sh) * t   # trapezoid: narrow shoulders -> wide hem
        for x in range(int(fx - hw), int(fx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            ch, fg = shade(L(x, y), base_fg=7, hot_fg=15)
            cv.set(x, y, ch, fg, 0)
    for y in range(int(hood_top), int(sh_y) + 1):   # hood cap over the shoulders
        t = (y - hood_top) / max(1, sh_y - hood_top)
        hw = 1.2 + 0.8 * t
        for x in range(int(fx - hw), int(fx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            ch, fg = shade(L(x, y), base_fg=6, hot_fg=14)
            cv.set(x, y, ch, fg, 0)
    for x in range(int(fx - 0.8), int(fx + 0.8) + 1):   # face-void: dark recess in the hood front
        if cv.in_bounds(x, int(sh_y) - 1):
            cv.set(x, int(sh_y) - 1, "\u2591", 0, 0)


def framed_card(cv, y0, lines, border_fg=13, inner_bg=4):
    """A framed title/credit card in the house AGENTSCII wordmark idiom: double-rule box + a thin
    dithered inner edge band, with centered text on a clear inner field. `lines` is a list of
    (text, fg). Layout top->bottom: frame / band / [text] / band / frame -- bands never overlap text."""
    n = len(lines)
    h = n + 4                                       # frame + band + text(n) + band + frame
    y_top, y_bot = y0, y0 + h - 1
    for y in range(y_top, y_bot + 1):               # 1) fill inner field solid (gaps aren't black)
        for x in range(W):
            cv.set(x, y, " ", 7, inner_bg)
    for x in range(1, W - 1):                       # 2) outer double-rule frame
        cv.set(x, y_top, "\u2550", border_fg, inner_bg)
        cv.set(x, y_bot, "\u2550", border_fg, inner_bg)
    for y in range(y_top + 1, y_bot):
        cv.set(0, y, "\u2551", border_fg, inner_bg)
        cv.set(W - 1, y, "\u2551", border_fg, inner_bg)
    for x in range(1, W - 1):                       # 3) thin dithered edge bands
        cv.set(x, y_top + 1, "\u2592" if x % 2 else "\u2591", border_fg, inner_bg)
        cv.set(x, y_bot - 1, "\u2592" if x % 2 else "\u2591", border_fg, inner_bg)
    for i, (text, tfg) in enumerate(lines):         # 4) centered text on the clear field
        y = y_top + 2 + i
        left = (W - len(text)) // 2
        for j, ch in enumerate(text):
            if 1 < 1 + left + j < W - 1:
                cv.set(1 + left + j, y, ch, tfg, inner_bg)


# ---------------------------------------------------------------------------
# ASSEMBLE THE SCROLL
# ---------------------------------------------------------------------------
out = []

# ---- PANEL 0: TITLE CARD --------------------------------------------------
H0 = 16
cv = C.Canvas(W, H0, fill_ch=" ", fill_fg=0, fill_bg=0)
framed_card(cv, 3, [
    ("THE TRAVELER", 95),
    ("a wide horizon in two panels", 94),
    ("", 7),
    ("raze & hollis / AGENTSCII", 12),
], inner_bg=4)
cv.render(out)

# ---- PANEL I: WALKING AWAY (the accepted v1.2 composition) ----------------
HORIZON_Y = 12
SUN_X_I = 71.0            # sun far RIGHT -> figure walks away from it to the left
FIG_X_I = 30.0
H1 = 24
cv = C.Canvas(W, H1, fill_ch=" ", fill_fg=0, fill_bg=0)
for y in range(0, HORIZON_Y):                       # sky: value ramp + warm halo + ripple texture
    t = y / max(1, HORIZON_Y - 1)
    field_row(cv, y, t, SUN_X_I, float(HORIZON_Y), 34.0, hue_phase=2.0, ripple_amp=0.06)
horizon_band(cv, HORIZON_Y, SUN_X_I, float(HORIZON_Y))
half_set_sun(cv, SUN_X_I, float(HORIZON_Y), r=5.0)   # drawn before ground -> upper half occluded
for y in range(HORIZON_Y + 1, H1):                   # ground: darker ramp + ripple (receding near-space)
    t = 1.0 - (y - HORIZON_Y) / max(1, H1 - HORIZON_Y - 1)
    field_row(cv, y, t * 0.5, SUN_X_I, float(HORIZON_Y), 34.0, hue_phase=2.0 + 6.0, ripple_amp=0.08)
hooded_figure(cv, FIG_X_I, HORIZON_Y + 1, height=14.0, lean=0.0)   # lone figure, walking away
set_text(cv, 2, H1 - 1, "I | WALKING AWAY", 96, 0)
cv.render(out)

# ---- STAMP TRANSITION: the recurring half-set sun mark + color-cycle handoff
H2 = 8
cv = C.Canvas(W, H2, fill_ch=" ", fill_fg=0, fill_bg=0)
for x in range(W):
    cv.set(x, H2 // 2, "\u2591", C.cycle_hue(x * 0.6 + 3.0, HOUSE_HUE), 0)   # cycling rule
half_set_sun(cv, W / 2.0, float(H2 // 2), r=4.0)                             # the mark, centered
set_text(cv, 2, H2 - 1, "\u2591 the light \u2591", 93, 0)
cv.render(out)

# ---- PANEL II: TOWARD THE LIGHT (inverted register) -----------------------
SUN_X_II = 8.0            # sun on the LEFT (rising) -> figure walks toward it
FIG_X_II = 50.0
H3 = 24
cv = C.Canvas(W, H3, fill_ch=" ", fill_fg=0, fill_bg=0)
for y in range(0, HORIZON_Y):
    t = y / max(1, HORIZON_Y - 1)
    field_row(cv, y, t, SUN_X_II, float(HORIZON_Y), 34.0, hue_phase=2.0 + 4.0, ripple_amp=0.06)
horizon_band(cv, HORIZON_Y, SUN_X_II, float(HORIZON_Y))
half_set_sun(cv, SUN_X_II, float(HORIZON_Y), r=5.0)
for y in range(HORIZON_Y + 1, H3):
    t = 1.0 - (y - HORIZON_Y) / max(1, H3 - HORIZON_Y - 1)
    field_row(cv, y, t * 0.5, SUN_X_II, float(HORIZON_Y), 34.0, hue_phase=2.0 + 10.0, ripple_amp=0.08)
hooded_figure(cv, FIG_X_II, HORIZON_Y + 1, height=14.0, lean=-1.2)   # leans toward the light
set_text(cv, 2, H3 - 1, "II | TOWARD THE LIGHT", 96, 0)
cv.render(out)

# ---- CREDIT SEQUENCE: full-bleed framed block ----------------------------
H4 = 18
cv = C.Canvas(W, H4, fill_ch=" ", fill_fg=0, fill_bg=0)
framed_card(cv, 2, [
    ("THE TRAVELER", 95),
    ("a wide horizon in two panels", 94),
    ("", 7),
    ("art & code   raze & hollis", 12),
    ("the half-set sun + the textured field,", 103),
    ("established in v1.2, carried across both panels.", 103),
    ("", 7),
    ("AGENTSCII | ANSI CREATORS IN DEMAND", 96),
], inner_bg=4)
cv.render(out)

# ---- flush + hygiene ------------------------------------------------------
raw = "\n".join(out) + ESC + "0m\n"
path = "scratch/raze-traveler-scroll.ans"
with open(path, "w", encoding="cp437") as f:
    f.write(raw)
print("wrote", path, "rows:", len(out))
