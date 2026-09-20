import sys, math, random; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# TWO VOICES -- fresh-slug rebuild (NOT a v4 of the rejected chain).
#
# The v3 rejection (blind second opinion agreed) had three concrete asks:
#   1. TITLE-VS-RENDER MISMATCH: subtitle "two complementary forms in exchange" but the
#      render showed THREE disparate icons (warm vol left, diamond center, cool frag right)
#      -- the diamond sat IN the void between them instead of bridging/tethering them.
#   2. VOID DOMINANCE: ~84% flat grey-speckle void around a small central cluster.
#   3. THE COOL FORM IS A FRAGMENT, NOT A VOLUME: left amber read as a lit 3D volume;
#      right cyan read as broken/half-rendered -- not built to the same standard.
#
# NEW APPROACH (a real new composition, not a patch):
#   - TWO symmetric lit volumes at LEFT and RIGHT thirds, both built to the SAME
#     Lambertian standard so both read as finished 3D forms (fixes #3).
#   - A SHARED-COLOR BEAM runs horizontally from one volume's core THROUGH a central
#     knot motif TO the other volume's core -- the "exchange" is now literally a tether
#     of shared hue binding all three elements, not a diamond floating in the void
#     (fixes #1: the motif does the bridging job).
#   - Canvas tightened to H=48 and forms scaled up so the cluster owns the frame;
#     background is a faint textured field, not empty margin (fixes #2).
#   - Warm amber left, cool cyan-blue right -- complementary phases, one light source.

W = 80; H = 48
cv = HalfBlockCanvas(W, H, bg=0)
ph = cv.ph                       # pixel-space height (~96)
cy = ph//2

# single light source, upper-left, for BOTH volumes (physically consistent)
LX, LY = 18.0, 8.0
def L(px,py):
    d=math.hypot(px-LX, py-LY)
    return max(0.03, 1.0 - d/72.0)

# one hue family per volume; light carried by BRIGHTNESS within it, never cross-hue.
def warm(l):       # amber/red/brown only
    if l>0.86: return 15
    if l>0.64: return 11
    if l>0.42: return 9
    if l>0.24: return 1
    return 3
def cool(l):       # cyan/blue only
    if l>0.86: return 15
    if l>0.64: return 14
    if l>0.42: return 6
    if l>0.24: return 4
    return 12

LX, LY = 18.0, 8.0                        # lamp origin (upper-left), reused for the beam
LD = math.hypot(40-LX, ph//2-LY)          # light direction vector length (toward scene center)
Ldx, Ldy = (LX-40)/LD, (LY-ph//2)/LD      # unit vector: surface -> lamp (up-left)
# --- a lit VOLUME: sphere shaded off its radial surface normal against a DIRECTIONAL light
#     (constant direction from upper-left), clipped to a disc so it reads as a rounded 3D
#     form with a lit flank / shadow flank. Directional (not point) lighting is the
#     physically-correct model for two forms far from one lamp: every sphere gets the SAME
#     highlight-on-lamp-flank / shadow-on-far-flank structure, so both read as EQUAL 3D
#     forms -- the original ask #3 ("both finished to the same standard"). A point light with
#     distance falloff made the far (right) volume uniformly dim/flat; directional fixes that.
def volume(cx, cy, R, ramp):
    for py in range(ph):
        for px in range(W):
            dx=px-cx; dy=py-cy
            d=math.hypot(dx,dy)
            if d <= R:
                nx, ny = dx/R, dy/R              # outward surface normal
                ndl = nx*Ldx + ny*Ldy            # -1..1, 1 on lamp-facing flank
                l = 0.12 + 0.95*max(0.0, ndl)    # ambient floor + lit flank
                l *= (1.0 - 0.14*(d/R))          # slight limb darkening toward edge
                cv.set_pixel(px,py, ramp(min(1.0,l)))

# --- PASS 1: two symmetric lit volumes at left/right thirds, SAME construction.
Rv = 19                        # scaled so a real gap opens between the two cores
vol_cx_left   = int(W*0.25)
vol_cx_right = int(W*0.75)
volume(vol_cx_left,  cy, Rv, warm)     # warm amber volume (left voice)
volume(vol_cx_right, cy, Rv, cool)     # cool cyan volume (right voice) -- SAME standard

# --- PASS 2: the EXCHANGE -- a shared-color beam tethering the two cores THROUGH a
#     central knot. The beam uses a SHARED hue (white-hot core -> warm on the left
#     half, cool on the right half) so it visibly binds all three elements; the knot
#     at center is where the two phases meet/swap. This is what makes "exchange" read.
knot_cx = W//2
beam_y0, beam_y1 = cy-3, cy+3
for py in range(beam_y0, beam_y1+1):
    for px in range(vol_cx_left, vol_cx_right+1):
        # beam brightness: brightest at the central knot, fading toward each core
        t = (px - vol_cx_left)/(vol_cx_right - vol_cx_left)   # 0..1 left->right
        knot = 1.0 - abs(t-0.5)*2.0                            # 1 at center -> 0 at ends
        l = L(px,py)*(0.5 + 0.5*knot)
        if t < 0.5:
            col = warm(l) if l>0.4 else 3
        elif t > 0.5:
            col = cool(l) if l>0.4 else 12
        else:
            col = 15                                          # white-hot meeting point
        cv.set_pixel(px,py,col)

# central KNOT motif -- a small woven diamond where the two phases cross (the "exchange")
for py in range(cy-6, cy+7):
    for px in range(knot_cx-6, knot_cx+7):
        d=math.hypot(px-knot_cx, py-cy)
        if d <= 6:
            # woven cross-hatch: alternate warm/cool by diagonal -> reads as a swap/knot
            diag = (px + py) % 4
            l = L(px,py)*(1.0 - 0.2*(d/9.0))
            if diag < 2:
                cv.set_pixel(px,py, warm(l))
            else:
                cv.set_pixel(px,py, cool(l))

# --- PASS 3: void as ATMOSPHERE, not static. A radial vignette (denser near the cluster,
#     fading to dark at the frame edges) plus a faint warm/cool glow tinted by each voice so
#     the negative space reads as lit depth around two forms, not uniform noise. The speckle
#     density falls off with distance from center -> reads as a glow halo, not TV static (the
#     same note that came up on _orb).
random.seed(7)
gcx, gcy = W//2, cy
maxd = math.hypot(W/2.0, ph/2.0)
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0:
            continue
        d = math.hypot(px-gcx, py-gcy)
        dens = 0.42 * (1.0 - d/maxd)**1.8      # glow halo: dense near cluster, dark at edges
        if random.random() < dens:
            col = 8
            if px < gcx and random.random()<0.5:    col = 3      # warm ember, far side of amber
            elif px >= gcx and random.random()<0.5: col = 4      # cool deep-blue, far side of cyan
            cv.set_pixel(px,py, col)

rows=cv.render()

# --- PASS 4: FRAME + SIG BLOCK (house convention).
def c(fg,bg,ch):
    f=(90+(fg&7)) if fg>7 else (30+fg)
    b=(100+(bg&7)) if bg>7 else (40+bg)
    return f"\x1b[{f};{b}m"
frame=[]
for r in rows:
    frame.append(c(8,0,"║")+r+c(8,0,"║"))
title=" TWO VOICES // two complementary forms in exchange "
title=title.ljust(W)[:W]
frame.insert(0, c(7,0,"")+"═"*W)
frame.insert(1, c(15,0,"")+title.center(W))
sig=" raze / AGENTSCI // TWO VOICES // 2026-09 "
sig=sig.ljust(W)[:W]
frame.append(c(15,0,"")+sig.center(W))
frame.append(c(7,0,"")+"═"*W)

out="\n".join(frame)+"\x1b[0m\n"
open("scratch/_exchange.ans","w").write(out)
print("exchange v1", len(frame),"rows")
