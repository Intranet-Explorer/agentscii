#!/usr/bin/env python3
# EMBER MANDALA // "a molten sigil" -- raze solo. AGENTSCI ornamental register.
#
# WHY NEW: the house catalog has leaned FIGURATIVE/SCENE for a while (afterimage, duel,
#  leap, crowd, departure). random_direction rolled "rail yard + mirror() symmetry + warm
#  tones". I take the TECHNIQUE (4-way kaleidoscope symmetry, the canvas.mirror_quad idea)
#  and the PALETTE lean (warm reds/yellows/magentas dominant), but REJECT the rail-yard
#  subject -- DEPARTURE already owns that register and is pending review; duplicating it adds
#  nothing. Instead: a 4-WAY ORNAMENTAL MANDALA, a register no house piece has done (studied
#  from references/study/blocktronics-mx_mess.ANS -- dense curled white ornament + warm
#  accents over a textured void). The signature move is authoring ONE upper-left quadrant of
#  molten flame-tendrils + rings + corner flourish, then mirroring it into all four.
#
# THE LIGHT TRICK: every quadrant cell is shaded by a light_field centered on the CANVAS CENTER.
#  Because both mirror axes pass through that center, the mirror preserves the radial lighting
#  EXACTLY -- the baked shading of a copied cell is identical to what a true central light would
#  give it at the mirrored position. So one authored quadrant becomes a perfectly radially-lit
#  molten sigil: white-hot core -> yellow -> red -> magenta cooling embers toward the rim.
#
# THE FOCAL POINT: after the mirror, a single constructed burning EYE (figure_common.eye +
#  brow_ridge) is painted on top at dead center -- real anatomy, not flat blocks (the OBSERVER
#  NOTES #1 discipline). It's the heart of the fire.
import sys, os, math, random
sys.path.insert(0, os.getcwd())
import figure_common as fc

W, H = 80, 52
CX, CY = W // 2, H // 2             # 40, 26 -- the molten core / light source
SEED = 71
RAMP = fc.RAMP                      # full -> empty block density ramp

# --- warm molten hue wheel: white-hot core -> yellow -> red -> magenta cooling ember shadow ---
WHITE = 97; YELLOW = 93; RED = 91; MAGENTA = 95; PURPLE = 35
def warm(li):
    li = max(0.0, min(1.0, li))
    if li > 0.86: return WHITE
    if li > 0.62: return YELLOW
    if li > 0.40: return RED
    if li > 0.20: return MAGENTA
    return PURPLE

# --- ONE light source, radial from the core (glows from within) -------------------------------
def L(x, y):
    return fc.light_field(x, y, float(CX), float(CY), lmax=30.0, ambient=0.18)

def setc(cv, x, y, ch, fg, bg=0):
    if 0 <= x < W and 0 <= y < H:
        cv[y][x] = [ch, fg, bg]

def paint_disc(cv, cx, cy, r, taper=True):
    """A shaded disc: density AND color both track the radial light -> reads as a lit 3D core."""
    rr = int(round(r))
    for y in range(int(cy - rr), int(cy + rr) + 1):
        for x in range(int(cx - rr), int(cx + rr) + 1):
            d = math.hypot(x - cx, y - cy)
            if d > r:
                continue
            Li = L(x, y) * (1.0 - 0.35 * (d / r)) if taper else L(x, y)
            ch, fg = fc.shade(Li, base_fg=warm(Li), hot_fg=warm(min(1.0, Li + 0.18)), ramp=RAMP)
            setc(cv, x, y, "\u2588", warm(Li))

def paint_tendril(cv, ang0, sweep, r0, rmax, w0, w1, curl=0.0):
    """A molten flame-tongue / thorn: a tapering tube sweeping from r0 out to rmax, curving by `curl`.
    Authored in the upper-left quadrant (angles measured CCW from +x; 60..150 deg = up-left wedge)."""
    n = int((rmax - r0) * 3.0) + 6
    for i in range(n):
        t = i / max(1, n - 1)
        ang = math.radians(ang0 + sweep * t + curl * t * t * 40.0)
        r = r0 + (rmax - r0) * t
        x = CX - r * math.cos(ang)
        y = CY - r * math.sin(ang)
        w = w0 + (w1 - w0) * t             # taper: thick at core, thin at tip
        rr = max(0.6, w)
        for yy in range(int(y - rr), int(y + rr) + 1):
            for xx in range(int(x - rr), int(x + rr) + 1):
                if math.hypot(xx - x, yy - y) > rr:
                    continue
                 # cylindrical cross-section so the tube reads rounded, not flat (the OBSERVER #2 fix)
                cyl = 1.0 - 0.7 * (math.hypot(xx - x, yy - y) / max(0.6, rr)) ** 1.2
                Li = L(xx, yy) * cyl
                setc(cv, xx, yy, "\u2588", warm(Li))

def paint_ring(cv, radius, thick=1.0):
    """A dithered concentric ring -- texture, not a solid band (reads as ornament, not a target)."""
    rng = random.Random(SEED + int(radius * 7))
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - CX, y - CY)
            if abs(d - radius) <= thick:
                if rng.random() > 0.55:          # sparse -> reads as a beaded/dithered ring
                    Li = L(x, y)
                    setc(cv, x, y, RAMP[rng.randint(1, 3)], warm(Li))

def paint_diamond(cv, cx, cy, s, fg):
    """A small bright accent diamond (the mx_mess orange-diamond idiom)."""
    for y in range(int(cy - s), int(cy + s) + 1):
        for x in range(int(cx - s), int(cx + s) + 1):
            if abs(x - cx) + abs(y - cy) <= s:
                setc(cv, x, y, "\u2588", fg)

def mirror_quad(cv):
    """4-way kaleidoscope on the raw list-of-lists canvas (the figure_common representation,
    which fc.eye/brow_ridge need). Mirrors the upper-left quadrant into all four quadrants.
    Because both axes pass through (CX,CY), the baked radial shading is preserved exactly."""
    for y in range(CY):
        for x in range(CX):
            src = cv[y][x]
            if src[0] != ' ':
                cv[y][W - 1 - x] = list(src)              # mirror right (h-axis)
                cv[H - 1 - y][x] = list(src)              # mirror down (v-axis)
                cv[H - 1 - y][W - 1 - x] = list(src)      # diagonal

def main():
    cv = fc.new_canvas(H, W)

    # ---- P1: author the UPPER-LEFT QUADRANT motif only (x<CX, y<CY) --------------------------
    # core glow disc at center
    paint_disc(cv, CX, CY, 6.5, taper=True)

    # flame-tendrils / thorns radiating into the quadrant -- 3 arms across the up-left wedge
    for k in range(4):
        base = 64 + k * 32                  # 64,96,128,160 deg -> fills the up..left wedge
        paint_tendril(cv, ang0=base, sweep=-24, r0=5.0, rmax=25.0, w0=2.9, w1=0.8, curl=0.9)

    # concentric dithered rings (beaded ornament)
    paint_ring(cv, 10.0, thick=0.8)
    paint_ring(cv, 15.5, thick=0.8)
    paint_ring(cv, 21.0, thick=0.9)

    # corner flourish: a tight curl in the far upper-left of the quadrant -> 4-way corner ornament
    for i in range(60):
        t = i / 59.0
        ang = math.radians(30 + t * 200.0)
        r = 1.0 + t * 7.0
        x = 8.0 - r * math.cos(ang)
        y = 6.0 - r * math.sin(ang)
        Li = L(x, y)
        if 0 <= x < CX and 0 <= y < CY:
            setc(cv, int(round(x)), int(round(y)), RAMP[1], warm(Li))

    # warm accent diamonds at ring intersections in the quadrant
    for (ax, ay) in [(CX - 14, CY - 14), (CX - 21, CY - 6), (CX - 8, CY - 21)]:
        paint_diamond(cv, ax, ay, 1.5, MAGENTA)

    # ---- MIRROR: one quadrant -> full 4-way mandala ------------------------------------------
    mirror_quad(cv)

    # ---- P2: the burning EYE at dead center (real anatomy on top of the fire) -----------------
    fc.brow_ridge(cv, CX, CY - 3.0, 3.2, L, base_fg=warm(0.6), hot_fg=WHITE)
    fc.eye(cv, CX, CY, r=1.7, iris_fg=YELLOW, glint=True)

    # ---- P3: texture the negative space -- ember dust, sparse + falling off toward the rim -----
    rng = random.Random(SEED + 5)
    for y in range(H):
        for x in range(W):
            if cv[y][x][0] != ' ':
                continue
            d = math.hypot(x - CX, y - CY)
            dens = 0.10 + 0.26 * max(0.0, 1.0 - d / 34.0)   # floor 0.10 everywhere; denser near core
            if rng.random() > dens:
                continue
            Li = L(x, y)
            setc(cv, x, y, RAMP[rng.randint(2, 3)], warm(Li))

    # ---- P4: frame + title card ---------------------------------------------------------------
    out = []
    out.append(fc.c(MAGENTA) + "\u2554" * W)
    fc.render(cv, out)
    out.append(fc.c(MAGENTA) + "\u2557" * W)
    import canvas as C
    C.write_ans("_ember_mandala.ans", out,
                title="EMBER MANDALA v1.0 // a molten sigil", handles="raze")

if __name__ == "__main__":
    main()
