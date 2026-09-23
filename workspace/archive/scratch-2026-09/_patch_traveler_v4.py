#!/usr/bin/env python3
# v4 pass on raze-traveler-scroll: fix the figure-as-stripe problem hollis flagged.
#  - light the robe from the SUN side (directional), not its own center -> kills the
#    symmetric white-core stripe that read as a pillar/monolith.
#  - wider hem (~6.5) so the flare resolves into a robe at this scale.
#  - a dark cast-shadow streak off the sun side -> body separates from the field by
#    CONTRAST, not just brightness.
#  - calm the ripple field on the rows the figure occupies so its outline reads.
import re

p = "scratch/make_traveler_scroll.py"
s = open(p).read()

# ---- 1) replace hooded_figure body ---------------------------------------
new_fig = '''def hooded_figure(cv, fx, feet_y, height=14.0, lean=0.0, sun_x=None):
    """A lone HOODED traveler on the band -- v4: lit from the SUN side (directional),
    not its own center. v3 regressed this into a thin bright stripe in BOTH panels:
    light_field(x,y, fx+lean*2, ...) put the source at the body's own midline, so the
    hot_fg=15 core ran straight down the middle and read as a pillar/monolith against
    the busy ripple field. Fixes (hollis's two moves + directional light):
      (1) calm the field on the figure's rows so the outline reads;
      (2) wider hem (~6.5) + a dark cast-shadow streak off the sun side, so the body
          separates from the field by CONTRAST, not just brightness;
      (3) light source offset toward the sun -> bright sun-side edge, dim far-side edge
          across the robe (a lit 3D surface, not a symmetric stripe)."""
    dl = (1.0 if (sun_x is not None and sun_x > fx) else -1.0)      # light from sun side
    lx = fx + dl * 8.0                                              # source near the body, sun-ward
    ly = feet_y - height * 0.12                                     # low light, near the band
    L = lambda x, y: light_field(x, y, lx, ly, lmax=16.0, ambient=0.16)
    hem_y = feet_y
    sh_y = feet_y - int(height * 0.78)               # shoulder line
    hood_top = feet_y - int(height)                 # top of the cowl
    half_hem, half_sh = 6.5, 2.2                    # v4 flare: ~2.2 shoulders -> ~6.5 hem
    for y in range(int(sh_y), int(hem_y) + 1):
        t = (y - sh_y) / max(1, hem_y - sh_y)
        hw = half_sh + (half_hem - half_sh) * t      # trapezoid: narrow shoulders -> wide hem
        cx = fx + lean * 1.2 * t                    # body leans toward the light as it descends
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            cyl = 1.0 - 0.45 * (abs(x - cx) / max(1e-6, hw))    # rounded cross-section -> 3D robe
            ch, fg = shade(L(x, y) * cyl, base_fg=7, hot_fg=15)
            cv.set(x, y, ch, fg, 0)
    for y in range(int(hood_top), int(sh_y) + 1):      # hood cap over the shoulders (shaded ellipse)
        t = (y - hood_top) / max(1, sh_y - hood_top)
        hw = 1.6 + 1.0 * t
        cx = fx + lean * 1.2 * (t + 0.3)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if not cv.in_bounds(x, y):
                continue
            ch, fg = shade(L(x, y), base_fg=6, hot_fg=14)
            cv.set(x, y, ch, fg, 0)
    for x in range(int(fx - 0.8), int(fx + 0.8) + 1):    # face-void: dark recess in the hood front
        if cv.in_bounds(x, int(sh_y) - 1):
            cv.set(x, int(sh_y) - 1, "\\u2591", 0, 0)
    # cast shadow: a dark streak off the SUN side at the feet -> contrast separation from field
    for k in range(1, 6):
        sx = int(fx + dl * (-1.0) * k * 0.9)            # shadow points AWAY from the sun
        sy = feet_y + min(k, 2)
        if cv.in_bounds(sx, sy):
            cv.set(sx, sy, "\\u2591", 0, 0)
'''

# match from 'def hooded_figure' up to (but not including) 'def framed_card'
s = re.sub(r"def hooded_figure\(.*?\n(?=def framed_card)", new_fig + "\n", s, count=1, flags=re.S)

# ---- 2) calm the field on the figure's rows + pass sun_x to each call -----
# Panel I: sky loop ripple in figure band -> smaller; ground loop same.
# We do this by giving field_row a per-row ripple via a small helper closure is overkill;
# instead lower ripple_amp inside the y-loops when y is within the figure's vertical extent.

# Panel I call site
s = s.replace(
    'hooded_figure(cv, FIG_X_I, HORIZON_Y + 1, height=14.0, lean=0.0)    # lone figure, walking away',
    'hooded_figure(cv, FIG_X_I, HORIZON_Y + 1, height=14.0, lean=0.0, sun_x=SUN_X_I)    # lit from the right sun'
)
s = s.replace(
    'hooded_figure(cv, FIG_X_II, HORIZON_Y + 1, height=14.0, lean=-1.2)    # leans toward the light',
    'hooded_figure(cv, FIG_X_II, HORIZON_Y + 1, height=14.0, lean=-1.2, sun_x=SUN_X_II)    # lit from the left sun'
)

# calm channel: add a helper that paints a low-ripple vertical channel behind a figure column,
# called just before each hooded_figure so its outline reads against calmer space.
calm_helper = '''
def calm_channel(cv, fx, y_top, y_bot, half=4):
    """Drop the per-cell ripple to ~0 on the rows a figure occupies (hollis move #1): the
    figure sits in calmer space so its outline reads instead of being swallowed by the busy
    field. A gentle value ramp is kept so it still recedes, just without the texture noise."""
    for y in range(int(y_top), int(y_bot) + 1):
        for x in range(max(0, int(fx - half)), min(W, int(fx + half) + 1)):
            if not cv.in_bounds(x, y):
                continue
            v = 0.35 + 0.25 * (y - y_top) / max(1, y_bot - y_top)    # faint recede, no ripple
            ch = RAMP[min(3, int(v * 4))]
            cv.set(x, y, ch, C.cycle_hue(y * 0.9 + 2.0, HOUSE_HUE), 0)

'''
s = s.replace("# ---------------------------------------------------------------------------\n# ASSEMBLE THE SCROLL",
              calm_helper + "# ---------------------------------------------------------------------------\n# ASSEMBLE THE SCROLL", 1)

# insert calm_channel calls before each figure (figure band: feet_y-14 .. feet_y+2)
s = s.replace(
    "hooded_figure(cv, FIG_X_I, HORIZON_Y + 1, height=14.0, lean=0.0, sun_x=SUN_X_I)    # lit from the right sun",
    "calm_channel(cv, FIG_X_I, HORIZON_Y - 13, HORIZON_Y + 2)\nhooded_figure(cv, FIG_X_I, HORIZON_Y + 1, height=14.0, lean=0.0, sun_x=SUN_X_I)    # lit from the right sun"
)
s = s.replace(
    "hooded_figure(cv, FIG_X_II, HORIZON_Y + 1, height=14.0, lean=-1.2, sun_x=SUN_X_II)    # lit from the left sun",
    "calm_channel(cv, FIG_X_II, HORIZON_Y - 13, HORIZON_Y + 2)\nhooded_figure(cv, FIG_X_II, HORIZON_Y + 1, height=14.0, lean=-1.2, sun_x=SUN_X_II)    # lit from the left sun"
)

open(p, "w").write(s)
print("patched OK")
