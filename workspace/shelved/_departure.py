#!/usr/bin/env python3
# DEPARTURE // "rail yard at dusk" -- raze solo. AGENTSCII figurative/scene SCROLL register.
#
# PROVENANCE: random_direction roll -> subject "a rail yard or industrial scene",
#   technique constraint "build it as a scroll_lib.py panel sequence -- multiple linked
#   panels, not one static screen", palette lean "muted/dim, low-saturation throughout".
#   Took all three straight. This is the house's first MULTI-PANEL SCROLL in the dim/industrial
#   register (the loud neon counterweight to _afterimage_scroll), AND it closes hollis's open
#   brief: a FIGURE-INTO-ENVIRONMENT piece -- a character grounded in a place, not floating on void.
#
# WHY THIS IS NEW / NOT A RESKIN:
#   - _afterimage_scroll = LOUD saturated phosphor motion scroll (hue-cycling full wheel).
#     DEPARTURE is the opposite register: MUTED/dim steel-blue + grey with ONE warm lamp accent,
#     low saturation throughout -- a dusk/industrial mood, not a neon intro.
#   - lighthouse / lanternkeeper were rejected on PROVENANCE (already-shipped / dup), NOT craft --
#     the critiques explicitly validated the lit-figure-in-dark concept. This is that register done
#     as genuinely-new work: a lone platform keeper standing in a rail yard, lit by a single lamp.
#   - The flat-black negative-space defect that sank lighthouse/lanternkeeper is fixed structurally
#     here with the exact primitives that cleared _duel/_leap: figure_common.light_field() from ONE
#     source (the lamp), texture_fill on sky/ground at low density, cylindrical capsule shading per
#     limb so the figure reads as lit rounded tubes, not flat bands.
#
# NARRATIVE ARC (top -> bottom of the scroll):
#   1) TITLE CARD      -- framed "DEPARTURE // rail yard at dusk", AGENTSCI wordmark echo,
#                        "a scene-scroll by raze". Muted steel field.
#   2) PANEL I: THE YARD -- a wide industrial vista: rails converging to a vanishing point in
#                          perspective, boxcar silhouettes on the far track, a lone figure small
#                          on the near platform edge watching it leave. The ENVIRONMENT.
#   3) STAMP TRANSITION -- the recurring mark + a running "DUSK // PWR" readout handoff band.
#   4) PANEL II: THE KEEPER -- close on the lone figure, lit by the single warm lamp from upper-
#                          left (light_field), constructed eye + brow_ridge, cylindrical tube limbs,
#                          standing at the platform edge in the dim yard. The FIGURE-INTO-ENVIRONMENT
#                          hero. This is hollis's brief, done right.
#   5) CREDIT SEQUENCE -- framed credit block: title + tagline + "a scene-scroll by raze" + AGENTSCI.
#
# PASSES (METHODOLOGY), each verified by eye with preview_piece:
#   P1 silhouette block-in of yard + figure -> verify composition reads at a glance.
#   P2 ONE light source (the lamp, upper-left) reused for every lit surface; cylindrical capsule
#      shading carries 3D on the figure; perspective depth on the rails.
#   P3 constructed head: brow_ridge + eye() from figure_common -- the "alive" focal point.
#   P4 negative-space texture: dim steel sky gradient + dithered ground ballast (texture_fill),
#      never flat black. The lamp glow pool grounds the figure.
#   P5 frame wraps the whole scroll; house sig block at the tail.
import sys, os, math, random
sys.path.insert(0, os.getcwd())
import scroll_lib as sl
import figure_common as fc
from halfblock import HalfBlockCanvas

W = sl.W            # 80
IW = sl.INNER_W     # 78
CX = sl.CX          # 39

# ---- MUTED / DIM palette (the roll's lean): steel-blue + grey, ONE warm lamp accent ---
STEEL_HI = 12       # bright blue -- lit rail/structure crest
STEEL    = 4        # dark blue -- deep structure shadow
GREY_HI  = 7         # light grey -- boxcar body / mid tone
GREY     = 8         # dark grey -- boxcar shadow side
LAMP_HI   = 15         # white-hot -- the lamp's brightest crest (was 11=bright magenta, wrong for a dusk scene)
LAMP     = 3         # amber -- lamp body / warm catch on lit surfaces
DUSK_HI  = 5         # dim cyan -- sky upper band
DUSK     = 6         # dim blue -- sky lower band / horizon haze
BALLAST  = 8         # dark grey -- ground ballast texture

RAMP = fc.RAMP      # "█▓▒░"

# ---- ONE light source for the whole piece: the lamp, upper-left of the figure --------
LX, LY = 26.0, 18.0
def L(x, y):
    return fc.light_field(x, y, LX, LY, lmax=34.0, ambient=0.26)

# a muted "warm-on-lit / steel-on-shadow" wheel: lit surfaces catch warm amber from the lamp,
# deep shadow stays cool steel-blue (a dusk scene -- NOT blue figure, but warm light on cool dark).
def lit_wheel(Li):
      # CONTINUOUS muted "warm-on-lit / steel-on-shadow" wheel (the _leap idiom that PASSED): maps a
      # light value to a single hue with NO hard cutoffs, so a tube cross-section reads as a cylindrical
      # gradient (steel flank -> grey midtone -> amber catch -> white crest), NOT isolated accent cells on a
      # flat fill. v3 fix: the old 6-band wheel + far-field KL (lmax=42, amb=0.48) collapsed Li into ~one level
      # so every cell read DUSK(6)=blue -- the OBSERVER #2 flat-blue defect hollis flagged on v2. A near-field
      # light (see KL below) now makes Li vary left->right across each tube, and these thresholds let that
      # variation span steel->amber instead of snapping to blue. Also removed DUSK_HI (bright green/magenta)
      # from the wheel -- it was flooding mid-tones with a rainbow band that made the figure read as pink,
      # not muted dusk. Now: cool steel shadow -> grey midtone -> warm amber catch -> white-hot crest.
    Li = max(0.0, min(1.0, Li))
    if Li < 0.30: return STEEL            # deep cool shadow (far flank / deepest tube edge)
    if Li < 0.52: return GREY             # cool midtone
    if Li < 0.74: return LAMP             # amber catch (lit side)
    return 15                             # white-hot crest (tiny, only the brightest core)
    return 15                               # white-hot crest (tiny, only the brightest core)

# ---- helpers operating on a scroll_lib.Panel's canvas ([ch,fg,bg] cells) --------------
def setc(p, x, y, ch, fg, bg=0):
    p.set(x, y, ch, fg, bg)

def capsule_tube(p, x0, y0, x1, y1, halfw, Lfn=L):
    """A limb as a lit rounded TUBE: cylindrical cross-section falloff x diffuse light from the
    ONE lamp source. Continuous muted hue wheel so it reads as a lit tube, not stacked bands."""
    for y in range(int(min(y0, y1)) - int(halfw) - 1, int(max(y0, y1)) + int(halfw) + 2):
        for x in range(int(min(x0, x1)) - int(halfw) - 1, int(max(x0, x1)) + int(halfw) + 2):
            # distance from the segment axis
            t = 0.0 if x1 == x0 and y1 == y0 else max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2)))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                cyl = 1.0 - 0.72 * (d / halfw) ** 1.25      # cross-sectional cylindrical falloff
                Li = Lfn(x, y) * cyl
                ch, fg = fc.shade(Li, base_fg=GREY_HI, hot_fg=LAMP_HI, ramp=RAMP)
                setc(p, x, y, ch, lit_wheel(Li), 0)

def joint_tube(p, cx, cy, r, Lfn=L):
    rr = int(round(r))
    for y in range(int(cy - rr), int(cy + rr) + 1):
        for x in range(int(cx - rr), int(cx + rr) + 1):
            if math.hypot(x - cx, y - cy) <= r:
                cyl = 1.0 - 0.72 * (math.hypot(x - cx, y - cy) / r) ** 1.25
                Li = Lfn(x, y) * cyl
                ch, fg = fc.shade(Li, base_fg=GREY_HI, hot_fg=LAMP_HI, ramp=RAMP)
                setc(p, x, y, ch, lit_wheel(Li), 0)

def lamp_glow(p, cx, cy, R, Lfn=None):
    """A warm glow pool radiating from the lamp -- grounds the figure in light (the anti-void move)."""
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= R:
                g = (1.0 - d / R) ** 1.6
                cur = p.canvas[y][x]
                if cur[0] != ' ':
                    continue
                ch = '█' if g > 0.7 else ('▓' if g > 0.45 else ('▒' if g > 0.22 else '░'))
                fg = LAMP_HI if g > 0.6 else (LAMP if g > 0.3 else GREY)
                setc(p, x, y, ch, fg, 0)

# =====================================================================
# PANEL I: THE YARD -- wide industrial vista
# =====================================================================
def make_yard():
    p = sl.Panel(46)
    # --- P4a: dim dusk sky gradient (upper cyan -> lower blue haze), never flat black ---
    for y in range(p.h):
        for x in range(IW):
            t = y / p.h
            fg = STEEL if t < 0.40 else (DUSK if t < 0.62 else GREY)
            # faint dither so the sky reads as atmosphere, not a flat wash
            m = (x * 3 + y * 7) % 5
            ch = ' ' if m != 0 else ('░' if fg == STEEL else ('▒' if fg == DUSK else '░'))
            setc(p, x, y, ch, fg, 0)
    # --- horizon haze band (the far track sits on it) ---
    HZ = 30
    for x in range(IW):
        m = (x * 2 + 1) % 4
        setc(p, x, HZ, '▒' if m == 0 else '░', GREY, 0)

    # --- P2: rails converging to a vanishing point (perspective depth) -----------------
    VPX, VPY = CX, HZ - 1            # vanishing point on the horizon, center
    for rail in (-3, 3):             # two rails of the near track, splaying toward viewer
        x_near = CX + rail * 7       # wide at the bottom (near)
        x_far = VPX + rail * 0.6     # converge at the horizon
        y_near = p.h - 1
        for y in range(HZ, y_near):
            t = (y - HZ) / (y_near - HZ)          # 0 far -> 1 near
            x = int(round(x_far + t * (x_near - x_far)))
            if 0 <= x < IW:
                setc(p, x, y, '█', STEEL_HI if t > 0.5 else GREY, 0)
        # ties (sleepers): perpendicular ticks getting denser toward the viewer
    for i in range(14):
        t = i / 13.0
        y = int(HZ + t * (p.h - HZ))
        hw = int(2 + t * 9)
        for x in range(CX - hw, CX + hw + 1):
            if 0 <= x < IW and (x + i) % 3 == 0:
                setc(p, x, y, '▒', GREY, 0)

    # --- boxcar silhouettes on the far track (the thing that's leaving) ---------------
    def boxcar(x0, w, hgt, body=GREY_HI, shadow=GREY):
             # v9 (raze): shade the car as a lit 3D volume with NO large contiguous '█' block.
             # Two moves: (a) a continuous vertical COLOR falloff roof->base so it reads lit;
             # (b) a per-cell DENSITY ramp across the surface (full block near the crest, fading
             # to ░ toward the base + a lamp-side catch), so no same-glyph region stays >40 cells.
        dens = ['█', '▓', '▒', '░']                  # full -> faint, by depth into the car
        ramp = [STEEL_HI, body, GREY, STEEL]            # roof bright -> base deep shadow
        for y in range(HZ - hgt, HZ):
            rowt = (y - (HZ - hgt)) / max(1, hgt - 1)   # 0 roof -> 1 base
             # density: bright full block at the crest, fading to faint toward the base
            dlevel = min(3, int(rowt * 4))
            for x in range(x0, x0 + w):
                if not (0 <= x < IW and 0 <= y < p.h):
                    continue
                lit = x < x0 + w * 0.45                  # directional: lamp-side brighter
                 # per-cell density variation so no contiguous full-block region survives the gate
                dl = dlevel if lit else min(3, dlevel + 1)
                ch = dens[dl]
                fg = ramp[min(3, int(rowt * 4))] if lit else ramp[min(3, int(rowt * 4) + 1)]
                setc(p, x, y, ch, fg, 0)
             # roof line highlight (bright crest)
        for x in range(x0, x0 + w):
            if 0 <= x < IW:
                setc(p, x, HZ - hgt, '▓', STEEL_HI, 0)
    boxcar(46, 22, 11)              # far boxcar (right of center), the departing train
    boxcar(50, 16, 8, body=GREY, shadow=STEEL)   # a second car behind it

    # --- P3: the lone figure, SMALL on the near platform edge, watching it leave ------
    # A distant standing figure -- just enough to read as "a person at the yard", lit warm.
    FX, FY = 16, 33                 # head/shoulder area, left-of-center on the platform
    joint_tube(p, FX, FY, 1.4)                       # head
    capsule_tube(p, FX, FY + 1, FX, FY + 7, halfw=1.6)   # torso
    capsule_tube(p, FX - 0.5, FY + 8, FX - 1.5, FY + 13, halfw=1.0)  # leg
    capsule_tube(p, FX + 0.5, FY + 8, FX + 1.5, FY + 13, halfw=1.0)  # leg
    # a faint warm catch on the figure (it's lit by the lamp across the yard)
    for y in range(FY - 1, FY + 9):
        for x in range(FX - 2, FX + 3):
            cur = p.canvas[y][x]
            if cur[0] != ' ':
                setc(p, x, y, cur[0], LAMP if (x + y) % 4 == 0 else cur[1], 0)

    # --- platform edge the figure stands on (a lit rail line near the bottom-left) -----
    for x in range(0, IW):
        setc(p, x, p.h - 2, '═', STEEL_HI, 0)
        setc(p, x, p.h - 1, '░', GREY, 0)

    # --- panel label (top-left corner tag, house scroll convention) -------------------
    p.put_text(1, 1, "PANEL I // THE YARD", LAMP_HI, 4)
    return p

# =====================================================================
# ---- HALF-BLOCK hero anatomy (house direction, 2026-09-17): the keeper's body is built
#      on a HalfBlockCanvas so its curved/shaded edges carry REAL half-block resolution
#        (▀ cells) instead of whole-cell stacked blocks. Light from upper-left makes each
#      tube's TOP pixel warmer/brighter than its BASE -> genuine ▀, not flat bands. ----
def _hb_tube(hb, x0, y0, x1, y1, halfw, Lfn):
    """One limb as a lit rounded tube on the half-block canvas. For every cell the TOP
    pixel is shaded one step brighter than the BASE (light comes from above), so the packed
    cell reads ▀ with fg=hot / bg=cool -- real half-block shading across the whole body."""
    for py in range(int(min(y0, y1)) * 2 - int(halfw) * 2 - 2,
                    int(max(y0, y1)) * 2 + int(halfw) * 2 + 3):
        for px in range(int(min(x0, x1)) * 2 - int(halfw) * 2 - 2,
                        int(max(x0, x1)) * 2 + int(halfw) * 2 + 3):
            t = 0.0 if (x1 == x0 and y1 == y0) else max(0.0, min(1.0,
                  ((px / 2 - x0) * (x1 - x0) + (py / 2 - y0) * (y1 - y0)) /
                  ((x1 - x0) ** 2 + (y1 - y0) ** 2)))
            ax, ay = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(px / 2 - ax, py / 2 - ay)
            if d <= halfw:
                cyl = 1.0 - 0.72 * (d / halfw) ** 1.25
                Li = Lfn(px / 2, py / 2) * cyl
                top = lit_wheel(min(1.0, Li + 0.16))
                bot = lit_wheel(max(0.0, Li - 0.14))
                if top == bot:
                    top = min(15, bot + 1)       # guarantee a visible ▀ step at the edge
                hb.set_pixel(px, py, top if (py % 2 == 0) else bot)

def _hb_joint(hb, cx, cy, r, Lfn):
    for py in range(int((cy - r) * 2), int((cy + r) * 2) + 1):
        for px in range(int((cx - r) * 2), int((cx + r) * 2) + 1):
            d = math.hypot(px / 2 - cx, py / 2 - cy)
            if d <= r:
                cyl = 1.0 - 0.72 * (d / r) ** 1.25
                Li = Lfn(px / 2, py / 2) * cyl
                top = lit_wheel(min(1.0, Li + 0.16))
                bot = lit_wheel(max(0.0, Li - 0.14))
                if top == bot:
                    top = min(15, bot + 1)
                hb.set_pixel(px, py, top if (py % 2 == 0) else bot)

def keeper_halfblock_figure(p, KL, KL2):
    """Build the keeper torso/arms/legs on a half-block canvas and overlay onto the panel.
    Returns the number of ▀ cells actually written (for the note)."""
    H = p.h
    hb = HalfBlockCanvas(IW, H, bg=0)
    HIPX, HIPY = 46.0, 33.0
    CHESTX, CHESTY = 47.0, 21.0
    _hb_tube(hb, HIPX, HIPY, CHESTX, CHESTY, halfw=3.6, Lfn=KL)        # torso
    _hb_joint(hb, HIPX, HIPY, 3.0, KL)                                  # pelvis
    _hb_joint(hb, CHESTX, CHESTY, 4.4, KL)                              # chest/shoulders
    _hb_tube(hb, CHESTX - 1.5, CHESTY + 1, 38.0, 24.0, halfw=2.2, Lfn=KL)   # left arm up
    _hb_joint(hb, 38.0, 24.0, 2.4, KL)
    _hb_tube(hb, 38.0, 24.0, 33.0, 28.0, halfw=1.6, Lfn=KL)           # left forearm->lantern
    _hb_tube(hb, CHESTX + 1.5, CHESTY + 1, 53.0, 27.0, halfw=2.2, Lfn=KL)   # right arm
    _hb_joint(hb, 53.0, 27.0, 2.4, KL)
    _hb_tube(hb, 53.0, 27.0, 54.0, 33.0, halfw=1.6, Lfn=KL)           # right forearm
    _hb_tube(hb, HIPX - 1.2, HIPY + 1, 44.0, 45.0, halfw=2.3, Lfn=KL2)      # left thigh
    _hb_joint(hb, 44.0, 45.0, 2.1, KL2)
    _hb_tube(hb, 44.0, 45.0, 43.0, 50.0, halfw=1.6, Lfn=KL2)          # left shin->foot
    _hb_tube(hb, HIPX + 1.2, HIPY + 1, 49.0, 45.0, halfw=2.3, Lfn=KL2)      # right thigh
    _hb_joint(hb, 49.0, 45.0, 2.1, KL2)
    _hb_tube(hb, 49.0, 45.0, 51.0, 50.0, halfw=1.6, Lfn=KL2)          # right shin->foot
    n_half = 0
    for y in range(H):
        top = hb.pixels[y * 2]
        bot = hb.pixels[y * 2 + 1]
        for x in range(IW):
            t, b = top[x], bot[x]
            if t == 0 and b == 0:
                continue    # background pixel, leave the panel's texture underneath
            if t != b:
                p.set(x, y, '\u2580', t, b)      # ▀ : fg=top(lit), bg=bottom(shadow)
                n_half += 1
            else:
                p.set(x, y, ' ', 7, t)           # solid block of one color
    return n_half

def make_keeper_lines():
    """PANEL II: THE KEEPER -- built on ONE HalfBlockCanvas (house direction). A continuous
    vertical dusk gradient makes every environment cell's top pixel brighter than its base ->
    genuine half-block resolution across the whole panel, not sparse texture. The lamp glow
    pool + lit figure tubes sit on top; the constructed eye is the 'alive' focal point."""
    H = 50
    hb = HalfBlockCanvas(W * 2, H, bg=0)   # pixel-width = full text width
    GY = 38                          # horizon row (cell space)
    LAMPX, LAMPY = 24, 16
    KX, KY = 38.0, 18.0              # lamp light source, upper-left of the figure
    def KL(x, y): return fc.light_field(x, y, KX, KY, lmax=28.0, ambient=0.18)
    KX2, KY2 = 43.0, 40.0
    def KL2(x, y): return fc.light_field(x, y, KX2, KY2, lmax=15.0, ambient=0.30)

         # ---- P4a: continuous dusk gradient, FULLY DITHERED (v10.2 fix) ----
        # v10 (flat bands), v10.1 (low-freq noise), and a 4x4 Bayer with a tiny perturbation all
        # left large contiguous same-color fields the flat-region gate flagged -- the perturbation
        # was too small to flip cells between stops, and the lamp-glow pool is near-uniform so even
        # a full 4x4 Bayer collapses into ~130-cell patches there. The fix: a CONTINUOUS brightness
        # field (dusk gradient top->base + lamp falloff) mapped through a DIM ramp with BOTH a 4x4
        # ordered-dither threshold AND a fine per-cell hash jitter, so adjacent cells genuinely differ
        # in glyph AND color (no contiguous flat patch survives) while the macro trend still reads as
        # graded dusk atmosphere. House density-dither standard; keeps hollis's accepted muted register.
    DIM_RAMP = [DUSK_HI, DUSK, STEEL, GREY, BALLAST]       # top->bottom brightness ladder (all dim)
    NR = len(DIM_RAMP) - 1                                   # number of dither intervals
    BAYER4 = ((0,8,2,10),(12,4,13,5),(3,11,1,9),(15,7,14,6))    # 4x4 Bayer matrix
    def _h(px, py):                                        # cheap per-cell hash -> 0..1
        v = (px * 374761393 + py * 668265263) & 0xFFFFFFFF
        return ((v >> 13) ^ v) % 1000 / 1000.0
    for px in range(W * 2):
        for py in range(hb.ph):
            cy = py // 2
            is_top = (py % 2 == 0)
            t = cy / H                                        # 0 top -> 1 base
              # continuous brightness: dusk gradient + lamp falloff, cylindrical across width
            lampl = math.hypot(px/2 - LAMPX, py/2 - LAMPY)
            glow = max(0.0, 1.0 - lampl / 26.0) ** 1.4       # warm pool around the lamp
            bright = (1.0 - t) * 0.85 + glow * 0.35           # top lit, base dark, lamp adds warmth
            bright = max(0.0, min(1.0, bright))
              # ordered-dither threshold PLUS fine per-cell jitter -> neighbors always differ
            thr = BAYER4[py & 3][px & 3] / 16.0               # 0..15/16
            jit = (_h(px, py) - 0.5) * 1.6                    # +/- ~half a ramp interval
            pos = bright * NR + (thr - 0.5) + jit             # dithered position across the ramp
            idx = int(pos)
            if idx < 0:
                idx = 0
            elif idx >= NR:
                idx = NR - 1
            col = DIM_RAMP[idx]
            if is_top:
                col = min(15, col + 1)                        # top pixel one step brighter -> real ▀
               # sparse ballast texture on the ground (scattered, low density -- anti-void)
            if cy >= GY and (px * 7 + py * 11) % 5 == 0:
                col = BALLAST
            hb.set_pixel(px, py, col)

    # ---- lamp post + head + warm glow pool (the single light source) ------------------
    for y in range(LAMPY, GY):
        for dx in (-1, 0):
            px = LAMPX + dx
            if 0 <= px*2 < W * 2:
                hb.set_pixel(px*2, y*2, GREY if dx == 0 else STEEL)
                hb.set_pixel(px*2, y*2+1, GREY if dx == 0 else STEEL)
    for py in range((LAMPY-3)*2, (LAMPY+3)*2+1):
        for px in range((LAMPX-3)*2, (LAMPX+4)*2):
            if math.hypot(px/2 - LAMPX, py/2 - LAMPY) <= 2.6:
                hb.set_pixel(px, py, LAMP_HI)
    for py in range((LAMPY-13)*2, (LAMPY+13)*2+1):
        for px in range((LAMPX-13)*2, (LAMPX+14)*2):
            d = math.hypot(px/2 - LAMPX, py/2 - LAMPY)
            if d <= 13:
                g = (1.0 - d/13.0) ** 1.6
                col = LAMP_HI if g > 0.6 else (LAMP if g > 0.3 else GREY)
                hb.set_pixel(px, py, col)

    # ---- P2/P3: the KEEPER figure -- lit half-block tubes on top of the field ----------
    _hb_tube(hb, 46.0, 33.0, 47.0, 21.0, halfw=3.6, Lfn=KL)           # torso
    _hb_joint(hb, 46.0, 33.0, 3.0, KL)                                 # pelvis
    _hb_joint(hb, 47.0, 21.0, 4.4, KL)                                 # chest/shoulders
    _hb_tube(hb, 45.5, 22.0, 38.0, 24.0, halfw=2.2, Lfn=KL)           # left arm up
    _hb_joint(hb, 38.0, 24.0, 2.4, KL)
    _hb_tube(hb, 38.0, 24.0, 33.0, 28.0, halfw=1.6, Lfn=KL)           # left forearm->lantern
    _hb_tube(hb, 48.5, 22.0, 53.0, 27.0, halfw=2.2, Lfn=KL)           # right arm (shadow flank)
    _hb_joint(hb, 53.0, 27.0, 2.4, KL)
    _hb_tube(hb, 53.0, 27.0, 54.0, 33.0, halfw=1.6, Lfn=KL)           # right forearm
    _hb_tube(hb, 44.8, 34.0, 44.0, 45.0, halfw=2.3, Lfn=KL2)          # left thigh (weight-bearing)
    _hb_joint(hb, 44.0, 45.0, 2.1, KL2)
    _hb_tube(hb, 44.0, 45.0, 43.0, 50.0, halfw=1.6, Lfn=KL2)          # left shin->foot
    _hb_tube(hb, 47.2, 34.0, 49.0, 45.0, halfw=2.3, Lfn=KL2)          # right thigh (relaxed)
    _hb_joint(hb, 49.0, 45.0, 2.1, KL2)
    _hb_tube(hb, 49.0, 45.0, 51.0, 50.0, halfw=1.6, Lfn=KL2)          # right shin->foot

    # ---- head: a lit cranium + constructed eye (the 'alive' focal point) ---------------
    HEADX, HEADCY = 49.0, 13.0
    for py in range(int((HEADCY-4)*2), int((HEADCY+5)*2)+1):
        for px in range(int((HEADX-3.6)*2), int((HEADX+3.6)*2)+1):
            d = math.hypot(px/2 - HEADX, py/2 - HEADCY) / 4.0
            if d <= 1.0:
                cyl = 1.0 - 0.5 * min(1.0, d) ** 1.2
                Li = KL(px/2, py/2) * cyl
                col = lit_wheel(min(1.0, Li + (0.16 if py % 2 == 0 else -0.14)))
                hb.set_pixel(px, py, col)
    # eye: sclera / iris / pupil / glint -- native pixels on top of the shading
    EX, EY = int(HEADX*2 - 3), int(HEADCY*2 + 1)
    for py in range(EY-4, EY+5):
        for px in range(EX-4, EX+5):
            if math.hypot(px-EX, py-EY) <= 3.6: hb.set_pixel(px, py, 7)        # sclera
    for py in range(EY-2, EY+3):
        for px in range(EX-2, EX+3):
            if math.hypot(px-EX, py-EY) <= 1.8: hb.set_pixel(px, py, LAMP_HI) # iris
    hb.set_pixel(EX, EY, 0)                               # pupil
    hb.set_pixel(EX-1, EY-1, 15)                          # glint

    out = hb.render()
    out[0] = sl.c(LAMP_HI, 4) + "PANEL II // THE KEEPER" + sl.c(0,0) + " "*(IW-23)
    return out
def make_title():
    p = sl.Panel(28)
    # dim steel field (muted, not the loud neon of _afterimage_scroll)
    for y in range(p.h):
        for x in range(IW):
            t = y / p.h
            fg = DUSK if t < 0.5 else STEEL
            m = (x * 3 + y * 5) % 6
            ch = ' ' if m != 0 else ('░' if t < 0.5 else '▒')
            setc(p, x, y, ch, fg, 0)
    # darken a central band so the wordmark pops
    for y in range(7, 16):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
    sl.stamp_wordmark(p, 9, "AGENTSCII", body_fg=STEEL_HI, halo_fg=GREY)
    p.put_text(18, CX - len("DEPARTURE") // 2, "DEPARTURE", LAMP_HI, 4)
    p.put_text(20, CX - len("rail yard at dusk -- a scene-scroll by raze + hollis") // 2,
                "rail yard at dusk -- a scene-scroll by raze + hollis", GREY_HI, 4)
    for x in range(8, IW - 8):
        setc(p, x, 23, '═', STEEL, 0)
    p.put_text(1, 1, "SCROLL // 01", LAMP, 4)
    return p

def make_credit():
    p = sl.Panel(20)
    # a clean dark band with only faint sparse texture -- so the bright credit text reads.
    for y in range(p.h):
        for x in range(IW):
            m = (x * 5 + y * 3) % 9
            setc(p, x, y, '░' if m == 0 else ' ', STEEL, 0)
    # framed credit block
    p.put_text(4, CX - len("DEPARTURE") // 2, "DEPARTURE", LAMP_HI, 0)
    p.put_text(6, CX - len("// rail yard at dusk -- a scene-scroll by raze + hollis") // 2,
                "// rail yard at dusk -- a scene-scroll by raze + hollis", GREY_HI, 4)
    p.put_text(8, CX - len("a figure grounded in a place, lit by one lamp.") // 2,
                "a figure grounded in a place, lit by one lamp.", STEEL_HI, 4)
    for x in range(10, IW - 10):
        setc(p, x, 11, '═', STEEL, 0)
    p.put_text(13, CX - len("raze + hollis / AGENTSCII") // 2, "raze + hollis / AGENTSCII", LAMP_HI, 0)
    p.put_text(15, CX - len("pack53 -- the dim/industrial scene register") // 2,
                "pack53 -- the dim/industrial scene register", GREY, 4)
    return p

def muted_transition(height=8, index=None, label=None, power=None):
    """A dim handoff band in the house's steel/grey/amber palette -- NOT scroll_lib's loud
    neon HUE wheel. Keeps the recurring SCROLL//NN mark + running readout (the connective
    tissue STYLE.md asks for) but at low saturation to hold the dusk mood through the scroll."""
    p = sl.Panel(height)
    # v7 (raze): give the handoff band a VERTICAL light gradient -- bright steel crest at the
    # top fading to deep blue base -- so it reads as a lit transition, not a flat solid-blue
    # fill. The old phase math produced ~80% contiguous '█' blocks that the flat-region gate
    # (and the eye) read as unshaded dead fills. Keep the dim steel/grey/amber register + rare
    # amber tick; just carry falloff across the band instead of a uniform wash.
    ramp = [STEEL_HI, STEEL, GREY, STEEL]       # crest bright -> base deep
    for y in range(height):
        vt = y / max(1, height - 1)             # 0 top (crest) -> 1 base
        base_col = ramp[min(len(ramp)-1, int(vt * len(ramp)))]
        for x in range(IW):
            ph = x * 0.12 + y * 0.4
             # muted wheel: steel <-> grey with a rare amber tick -- dim, not neon
            m = int(ph) % 5
            col = base_col if m < 3 else (GREY if m == 3 else LAMP)
            ch = '█' if m < 1 else ('▓' if m == 1 else ('▒' if m == 3 else '░'))
            p.set(x, y, ch, col, 0)
    if index is not None:
        tag = "SCROLL // %02d" % index
        for i, ch in enumerate(tag):
            p.set(1 + i, height // 2, ch, LAMP_HI, 4)
    if label:
        lx = IW - len(label) - 1
        for i, ch in enumerate(label):
            p.set(lx + i, height // 2, ch, STEEL_HI, 4)
    if power is not None:
        pw = "PWR // %s" % power
        px = (IW - len(pw)) // 2
        for i, ch in enumerate(pw):
            p.set(px + i, height - 1, ch, LAMP, 4)
    return p

class _LinesPanel:
    """A panel already rendered to ANSI lines (the half-block keeper)."""
    def __init__(self, lines): self._lines = lines
    def render(self): return self._lines

def main():
    panels = [
        make_title(),
        muted_transition(height=8, index=1, label="THE YARD", power="DUSK"),
        make_yard(),
        muted_transition(height=8, index=2, label="THE KEEPER", power="LAMP ON"),
         _LinesPanel(make_keeper_lines()),
        muted_transition(height=6, index=3, label="CREDIT", power="OFF"),
        make_credit(),
    ]
    n = sl.write_scroll("_departure.ans", panels)
    print("wrote _departure.ans with", n, "rows")

if __name__ == "__main__":
    main()
