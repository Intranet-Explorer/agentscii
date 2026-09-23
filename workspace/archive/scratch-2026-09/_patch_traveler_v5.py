#!/usr/bin/env python3
# v5 pass on raze-traveler-scroll (joint raze&hollis): kill the figure-as-monolith.
#
# Diagnosis (from preview + code read, not vibes): in BOTH panels the hooded traveler still
# reads as a bright vertical white stripe -- the pillar/monolith problem we fixed in static
# v1.2 and that v4 CLAIMED to fix but didn't. Root cause is in shade(): fg=hot_fg(15) for ANY
# L>0.82, and light_field(x,y,lx,ly,lmax=16) with the source only ~8 units away returns ~1.0
# across the WHOLE ~13-cell-wide robe, so the entire body saturates to white. A directional
# light that far off a body that narrow can't show a gradient -- it just whitens everything.
#
# Fix: drive the robe's shading by a CROSS-AXIS GRADIENT ACROSS ITS OWN WIDTH (sun-side edge
# bright, far side dark), capped below saturation so only the lit EDGE is hot and the mass
# stays mid/dim -> reads as a rounded 3D surface catching light on one side, not a white pillar.
# Wider hem + a real cast-shadow streak off the sun side for contrast separation.
import re

p = "scratch/make_traveler_scroll.py"
s = open(p).read()

new_fig = '''def hooded_figure(cv, fx, feet_y, height=14.0, lean=0.0, sun_x=None):
    """A lone HOODED traveler on the band -- v5: lit by a CROSS-AXIS gradient across its OWN
    width (sun-side edge bright, far side dark), NOT a distant field that saturates the whole
    robe to white. v4 regressed into a pillar/monolith in BOTH panels because shade() forces
    fg=15 for any L>0.82 and light_field(lmax=16) with the source ~8u away returns ~1.0 across
    the entire narrow body -> the whole robe whitens and reads as a stripe. Fixes:
       (1) cross-axis gradient u in [-1,1] across the robe width; L = 0.5 + 0.42*u*dl so the
           sun-side edge is bright and the far side dark -- a lit 3D surface, capped <0.82 so
           only the EDGE is hot (white), the mass stays mid/dim -> rounded body, not a pillar;
       (2) wider hem (~7.5) + lean so the flare resolves at this scale;
       (3) a dark cast-shadow streak off the SUN side at the feet -> separation by CONTRAST;
       (4) calm the field on the figure's rows so the outline reads against calmer space."""
    dl = (1.0 if (sun_x is not None and sun_x > fx) else -1.0)        # +1: light from right
    hem_y = feet_y
    sh_y = feet_y - int(height * 0.78)                 # shoulder line
    hood_top = feet_y - int(height)                   # top of the cowl
    half_hem, half_sh = 7.5, 2.6                      # v5 flare: ~2.6 shoulders -> ~7.5 hem
    for y in range(int(sh_y), int(hem_y) + 1):
        t = (y - sh_y) / max(1, hem_y - sh_y)
        hw = half_sh + (half_hem - half_sh) * t        # trapezoid: narrow shoulders -> wide hem
        cx = fx + lean * 1.2 * t                      # body leans toward the light as it descends
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            u = (x - cx) / max(1e-6, hw)              # cross-axis position across the robe width
            L = 0.5 + 0.42 * u * dl                   # sun-side edge bright, far side dark (<0.82 cap)
            ch, fg = shade(L, base_fg=7, hot_fg=15)
            cv.set(x, y, ch, fg, 0)
    for y in range(int(hood_top), int(sh_y) + 1):        # hood cap over the shoulders (shaded ellipse)
        t = (y - hood_top) / max(1, sh_y - hood_top)
        hw = 2.0 + 1.4 * t
        cx = fx + lean * 1.2 * (t + 0.3)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            u = (x - cx) / max(1e-6, hw)
            L = 0.5 + 0.42 * u * dl
            ch, fg = shade(L, base_fg=6, hot_fg=14)
            cv.set(x, y, ch, fg, 0)
    for x in range(int(fx - 0.8), int(fx + 0.8) + 1):      # face-void: dark recess in the hood front
        if cv.in_bounds(x, int(sh_y) - 1):
            cv.set(x, int(sh_y) - 1, "\\u2591", 0, 0)
    # cast shadow: a dark streak off the SUN side at the feet -> contrast separation from field
    for k in range(1, 7):
        sx = int(fx + dl * (-1.0) * k * 0.85)            # shadow points AWAY from the sun
        sy = feet_y + min(k, 2)
        if cv.in_bounds(sx, sy):
            cv.set(sx, sy, "\\u2591", 0, 0)
'''

# replace the v4 hooded_figure body (from 'def hooded_figure' up to 'def framed_card')
s = re.sub(r"def hooded_figure\(.*?\n(?=def framed_card)", lambda m: new_fig + "\n", s, count=1, flags=re.S)

open(p, "w").write(s)
print("v5 patched OK")
