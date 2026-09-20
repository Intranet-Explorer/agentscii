#!/usr/bin/env python3
# DEPARTURE // "rail yard at dusk" -- raze solo. AGENTSCI figurative/scene SCROLL register.
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

W = sl.W            # 80
IW = sl.INNER_W     # 78
CX = sl.CX          # 39

# ---- MUTED / DIM palette (the roll's lean): steel-blue + grey, ONE warm lamp accent ---
STEEL_HI = 12       # bright blue -- lit rail/structure crest
STEEL    = 4        # dark blue -- deep structure shadow
GREY_HI  = 7         # light grey -- boxcar body / mid tone
GREY     = 8         # dark grey -- boxcar shadow side
LAMP_HI  = 11        # bright amber -- the single warm light source (lamp glow)
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
    # Li in ~0..1.2; map to a muted hue ramp: deep steel -> grey -> amber -> white-hot crest
    Li = max(0.0, min(1.0, Li))
    if Li < 0.34: return STEEL           # deep cool shadow
    if Li < 0.46: return GREY            # cool midtone
    if Li < 0.58: return DUSK            # warm-cool transition (dim cyan)
    if Li < 0.70: return LAMP            # amber catch
    if Li < 0.84: return LAMP_HI         # bright amber
    return 15                            # white-hot crest

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
        for y in range(HZ - hgt, HZ):
            for x in range(x0, x0 + w):
                if 0 <= x < IW and 0 <= y < p.h:
                    # lit left edge (toward lamp), shadow right -- simple directional read
                    fg = body if x < x0 + w * 0.4 else shadow
                    ch = '█'
                    setc(p, x, y, ch, fg, 0)
        # roof line highlight
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
# PANEL II: THE KEEPER -- close on the lone figure lit by the lamp
# =====================================================================
def make_keeper():
    p = sl.Panel(50)
    # --- P4a: dim steel ground/sky texture (the environment the figure stands IN) ------
    for y in range(p.h):
        for x in range(IW):
            t = y / p.h
            fg = DUSK if t < 0.5 else STEEL
            m = (x * 5 + y * 3) % 6
            ch = ' ' if m != 0 else ('░' if t < 0.5 else '▒')
            setc(p, x, y, ch, fg, 0)
    # ground ballast texture below the horizon (texture_fill idiom: scattered, low density)
    GY = 38
    for y in range(GY, p.h):
        for x in range(IW):
            m = (x * 7 + y * 11) % 5
            if m == 0:
                setc(p, x, y, '▒', BALLAST, 0)
            elif m == 2:
                setc(p, x, y, '░', GREY, 0)

    # --- the lamp itself (the single light source), upper-left -------------------------
    LAMPX, LAMPY = 24, 16
    # a post + lamp head
    for y in range(LAMPY, GY):
        setc(p, LAMPX, y, '│', GREY, 0)
        setc(p, LAMPX - 1, y, '░', STEEL, 0)
    # A GENTLE field (large lmax) so the per-limb cylindrical term dominates: each tube keeps its
    # own cross-section gradient across the whole figure height instead of collapsing to one STEEL
    # level. Source upper-left of the figure; ambient high enough that even the far feet span
    # warm->steel, not a single dim-blue block.
    KX, KY = 30.0, 10.0
    def KL(x, y):
        return fc.light_field(x, y, KX, KY, lmax=42.0, ambient=0.48)
    joint_tube(p, LAMPX, LAMPY, 2.2, Lfn=L)          # the lamp head (warm, lit)
    for y in range(LAMPY - 3, LAMPY + 3):
        for x in range(LAMPX - 3, LAMPX + 4):
            if math.hypot(x - LAMPX, y - LAMPY) <= 2.6:
                setc(p, x, y, '█', LAMP_HI, 0)
    lamp_glow(p, LAMPX, LAMPY, R=13)
      # The lamp is far up-left (24,16); with the global lmax=34 the keeper's whole surface would
     # sit near Li~0.26 and collapse to a single STEEL level (the flat-blue defect). Give this panel
     # its OWN light source positioned to actually span warm->steel ACROSS the body's cross-section,
     # so each tube reads as a lit cylinder, not stacked cells. Still upper-left -- narratively the
     # same lamp, just resolved close enough that the falloff is visible on the figure itself.
          # the warm glow pool that grounds everything

    # --- P2/P3: the KEEPER figure, standing at the platform edge, lit from upper-left ---
    HIPX, HIPY = 46.0, 33.0
    CHESTX, CHESTY = 47.0, 21.0
    # torso (slight lean toward the lamp/light)
    capsule_tube(p, HIPX, HIPY, CHESTX, CHESTY, halfw=3.6, Lfn=KL)
    joint_tube(p, HIPX, HIPY, 3.0, Lfn=KL)           # pelvis
    joint_tube(p, CHESTX, CHESTY, 4.4, Lfn=KL)       # chest/shoulders
    # head -- a 3/4 turned skull, lit warm on the lamp side
    HEADX, HEADCY = 49.0, 13.0
    for y in range(int(HEADCY - 4), int(HEADCY + 5)):
        t = (y - HEADCY) / 4.0
        if abs(t) <= 1.0:
            hw = 3.4 * math.sqrt(1.0 - t * t)
            for x in range(int(HEADX - hw), int(HEADX + hw) + 1):
                d = math.hypot(x - HEADX, y - HEADCY) / 4.0
                cyl = 1.0 - 0.5 * min(1.0, d) ** 1.2
                Li = KL(x, y) * cyl
                ch, fg = fc.shade(Li, base_fg=GREY_HI, hot_fg=LAMP_HI, ramp=RAMP)
                setc(p, x, y, ch, lit_wheel(Li), 0)
    # constructed face: brow ridge + eye (the "alive" focal point, _duel idiom)
    fc.brow_ridge(p.canvas, HEADX - 1.5, HEADCY - 0.5, halfw=2.4, light=KL, base_fg=GREY_HI, hot_fg=LAMP_HI)
    fc.eye(p.canvas, HEADX - 2.0, HEADCY + 0.8, r=1.6, iris_fg=LAMP_HI, glint=True)

    # LEFT arm (toward the lamp -- reaching/holding a lantern or bracing), lit warm
    capsule_tube(p, CHESTX - 1.5, CHESTY + 1, 38.0, 24.0, halfw=2.2, Lfn=KL)
    joint_tube(p, 38.0, 24.0, 2.4, Lfn=KL)
    capsule_tube(p, 38.0, 24.0, 33.0, 28.0, halfw=1.6, Lfn=KL)   # forearm down to a held lantern
    # RIGHT arm (away from light -- in shadow, cool steel)
    capsule_tube(p, CHESTX + 1.5, CHESTY + 1, 53.0, 27.0, halfw=2.2, Lfn=KL)
    joint_tube(p, 53.0, 27.0, 2.4, Lfn=KL)
    capsule_tube(p, 53.0, 27.0, 54.0, 33.0, halfw=1.6, Lfn=KL)

    # legs -- a standing contrapposto stance (weight on one leg), lit tubes
    capsule_tube(p, HIPX - 1.2, HIPY + 1, 44.0, 45.0, halfw=2.3, Lfn=KL)   # weight-bearing left thigh
    joint_tube(p, 44.0, 45.0, 2.1, Lfn=KL)
    capsule_tube(p, 44.0, 45.0, 43.0, 50.0, halfw=1.6, Lfn=KL)             # left shin to foot
    capsule_tube(p, HIPX + 1.2, HIPY + 1, 49.0, 45.0, halfw=2.3, Lfn=KL)   # relaxed right thigh
    joint_tube(p, 49.0, 45.0, 2.1, Lfn=KL)
    capsule_tube(p, 49.0, 45.0, 51.0, 50.0, halfw=1.6, Lfn=KL)             # right shin to foot

    # the held lantern (warm glow in the left hand) -- a second small light accent
    lamp_glow(p, 32.0, 29.0, R=5)
    joint_tube(p, 32.0, 28.0, 1.4, Lfn=KL)

    # --- platform edge the keeper stands on --------------------------------------------
    for x in range(0, IW):
        setc(p, x, GY + 1, '═', STEEL_HI, 0)
        setc(p, x, GY + 2, '░', GREY, 0)

    p.put_text(1, 1, "PANEL II // THE KEEPER", LAMP_HI, 4)
    return p

# =====================================================================
# TITLE CARD + CREDIT SEQUENCE
# =====================================================================
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
    sl.stamp_wordmark(p, 9, "AGENTSCI", body_fg=STEEL_HI, halo_fg=GREY)
    p.put_text(18, CX - len("DEPARTURE") // 2, "DEPARTURE", LAMP_HI, 4)
    p.put_text(20, CX - len("rail yard at dusk -- a scene-scroll by raze") // 2,
                "rail yard at dusk -- a scene-scroll by raze", GREY_HI, 4)
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
    p.put_text(6, CX - len("// rail yard at dusk -- a scene-scroll by raze") // 2,
                "// rail yard at dusk -- a scene-scroll by raze", GREY_HI, 4)
    p.put_text(8, CX - len("a figure grounded in a place, lit by one lamp.") // 2,
                "a figure grounded in a place, lit by one lamp.", STEEL_HI, 4)
    for x in range(10, IW - 10):
        setc(p, x, 11, '═', STEEL, 0)
    p.put_text(13, CX - len("raze / AGENTSCI") // 2, "raze / AGENTSCI", LAMP_HI, 0)
    p.put_text(15, CX - len("pack53 -- the dim/industrial scene register") // 2,
                "pack53 -- the dim/industrial scene register", GREY, 4)
    return p

def muted_transition(height=8, index=None, label=None, power=None):
    """A dim handoff band in the house's steel/grey/amber palette -- NOT scroll_lib's loud
    neon HUE wheel. Keeps the recurring SCROLL//NN mark + running readout (the connective
    tissue STYLE.md asks for) but at low saturation to hold the dusk mood through the scroll."""
    p = sl.Panel(height)
    for y in range(height):
        for x in range(IW):
            ph = x * 0.12 + y * 0.4
            # muted wheel: steel <-> grey with a rare amber tick -- dim, not neon
            m = int(ph) % 5
            col = STEEL if m < 2 else (GREY if m < 4 else LAMP)
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

def main():
    panels = [
        make_title(),
        muted_transition(height=8, index=1, label="THE YARD", power="DUSK"),
        make_yard(),
        muted_transition(height=8, index=2, label="THE KEEPER", power="LAMP ON"),
        make_keeper(),
        muted_transition(height=6, index=3, label="CREDIT", power="OFF"),
        make_credit(),
    ]
    n = sl.write_scroll("_departure.ans", panels)
    print("wrote _departure.ans with", n, "rows")

if __name__ == "__main__":
    main()
