#!/usr/bin/env python3
# _aperture.py -- AGENTSCII abstract geometric field, "APERTURE".
#
# PROVENANCE: started from a random_direction roll (subject = abstract/geometric
# field; technique = canvas.py ellipse()+gradient_fill(); palette lean = muted/dim).
# REMIXED: the roll's flat radial gradient is too close to the existing curve-trace
# family (lissajous/rose/spirograph all cycle a hue wheel along a traced parameter).
# Instead this builds a COMPOSED nested-ellipse field -- concentric rings, each shaded
# as a lit 3D curved surface by a single off-center light source (the same "lit surface"
# language the traveler robe fix landed on), so it reads as depth/aperture, not a trace.
# This is the third piece of the traveler thread's pack: it BREAKS the figurative/landscape
# motif entirely to give the batch genuine variety (hollis's request).
#
# Technique layer: canvas.py primitives (ellipse / gradient_fill / dither_region /
# mirror) composed by hand, plus a directional density function for the ring shading.

import math
import sys
sys.path.insert(0, "scratch")
import canvas as C

W, H = 80, 46
CX, CY = W / 2.0, H / 2.0

# house hue wheel (magenta red yel grn cya blu wht amb) -- same order as curve_common
HUE = [95, 91, 93, 92, 96, 94, 107, 103]
RAMP = "\u2588\u2593\u2592\u2591"   # full -> light

# --- light source: off-center upper-left so every ring reads as a tilted bowl ----
LX, LY = CX - 14.0, CY - 12.0      # sun up-and-to-the-left of the aperture center
LMAX = 34.0


def light(x, y):
    """Directional light falloff from (LX,LY) -> 0..1, capped below saturation so a
    lit surface shows a gradient across its width instead of whitening to a stripe
    (the exact fix that made the traveler robe read as 3D)."""
    d = math.hypot(x - LX, y - LY) / LMAX
    return max(0.0, min(1.0, 1.0 - d))


def ring_band(x, y, r_in, r_out):
    """True if (x,y) falls in the annulus between two ellipse radii (squished vertically)."""
    dx = x - CX
    dy = (y - CY) * 1.7            # vertical squash -> lens/aperture aspect
    rr = math.hypot(dx, dy)
    return r_in <= rr < r_out


def main():
    cv = C.Canvas(W, H, fill_ch=' ', fill_fg=0, fill_bg=0)

    # --- backdrop: faint square graticule so empty space has structure, not flat black
    STEP = 8
    for y in range(H):
        for x in range(W):
            if x % STEP == 0 or y % STEP == 0:
                cv.set(x, y, '\u2591', 40, 40)   # dim cyan tick on near-black

    # --- nested elliptical rings, outer -> inner so inner rings overdraw cleanly ----
    # each ring is a lit curved surface: density from directional light across its band,
    # hue cycling slowly outward (ACiD craft) but the CORE stays controlled/dim.
    N = 7
    r_out_total = 30.0
    for i in range(N):
        r_out = r_out_total * (1.0 - i / N)
        r_in = r_out_total * (1.0 - (i + 1) / N)

        # hue cycles outward but is pulled toward dim/low-sat in the inner rings so the
        # core reads controlled, not a saturated blob -- the "clean core / cycling periphery"
        # idiom the critiques keep praising.
        phase = i * 1.35 + 0.4
        hue = HUE[int(phase) % len(HUE)]
        dimmed = (i < N - 2)          # inner two rings: pull brightness down

        def density(x, y, _i=i):
            # directional light across the band; add a faint radial term so the ring's
            # own curvature reads even where the global light is weak.
            L = light(x, y)
            rr = math.hypot(x - CX, (y - CY) * 1.7)
            rad = 1.0 - abs(rr - (r_in + r_out) / 2.0) / max(0.5, (r_out - r_in))
            d = 0.35 * L + 0.65 * max(0.0, rad)
            if dimmed:
                d *= 0.55
            return max(0.0, min(1.0, d))

        C.dither_region(cv, lambda x, y, _i=i: ring_band(x, y, r_in, r_out),
                        density, hue, bg=0)

    # --- rim highlight on the outermost ring's lit edge (a single bright catch-light) --
    for y in range(H):
        for x in range(W):
            if ring_band(x, y, r_out_total - 1.4, r_out_total + 0.2):
                L = light(x, y)
                if L > 0.78:
                    cv.set(x, y, '\u2588', 97, 0)        # white-hot catch on the lit rim

    # --- aperture core: a small dark pupil so the nested rings read as a lens opening ----
    C.ellipse(cv, CX, CY, 3.2, 1.9, ch='\u2588', fg=40, bg=0, fill=True)
    cv.set(int(CX), int(CY), '\u2588', 97, 0)            # single glint at the very center

    # --- render + house sig block ----------------------------------------------------
    out = []
    cv.render(out)
    C.write_ans("scratch/raze-aperture.ans", out,
                title="APERTURE v1.0", handles="raze")


if __name__ == "__main__":
    main()
