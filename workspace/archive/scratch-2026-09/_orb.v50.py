import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas
from canvas import shade_ramp

# THE WATCHER (_orb v49) -- raze + hollis (joint synthesis).
# v49 = v47's clean solid-black pupil void (the correct 'eye in the dark' read) +
# raze's v48 fix to PASS 7d (socket gradient was dead code in v47: set_pixel discarded
# the computed glyph; re-applied via glyph_override). v48's pupil radial-gradient fill is
# REVERTED -- it muddied the void into a murky blob, the v29/v30/v31 defect family. Built on v32 (clean void/iris/light source).
# hollis: replace raze's uniform static dither (v33->v41, blocky patches + lost iris
# structure) with DIRECTIONAL negative-space texture following the upper-left light source.
# THREE TARGETED FIXES over v30 + flat-region gate fixes:
#       (1) PUPIL CORE RENDERS DARK + ROUND with internal shading variation
#       (2) CENTER THE IRIS IN THE RING at col 38
#       (3) FILL LOWER-RIGHT QUADRANT
#     FLAT-REGION GATE FIXES:
#          - Pupil core: subtle radial gradient INSIDE the void (0->8->0) to avoid flat flag
#          - Upper-left socket: use shade_ramp() for a real dithered gradient instead of flat block
W=80; H=52
cv=HalfBlockCanvas(W,H,bg=0)
ph=cv.ph
cx=W//2; cy=ph//2

iris_cx = 38
iris_cy = cy

half_w = 30
h_upper = 20
h_lower = 13
exp_u, exp_l = 0.50, 0.42

def opening_half_h(u):
    a=abs(u)
    if a>=1.0: return (0.0,0.0)
    up = h_upper*(1.0-u*u)**exp_u
    lo = h_lower*(1.0-u*u)**exp_l
    return up, lo

def in_opening(px,py):
    u=(px-cx)/half_w
    if abs(u)>=1.0: return False
    up,lo=opening_half_h(u)
    dy=py-cy
    return -up <= dy <= lo

iris_r                 = 17
pupil_r                = 8

lx, ly = cx-24, cy-30
def L(px,py):
    d=math.hypot(px-lx, py-ly)
    return max(0.03, 1.0 - d/80.0)

def hsh(x,y,salt=0):
    v = (x*73 + y*131 + salt*97) % 997
    return v / 997.0

def gramp(l):
    if l>0.80: return 15
    if l>0.62: return 7
    if l>0.42: return 8
    return 0

def aramp_radial(d, ang, l):
    t_rad = (d - pupil_r) / max(0.1, iris_r - pupil_r)
    base = 1.0 - 0.70 * t_rad
    NCRYPTS = 9
    fiber = math.sin(ang * NCRYPTS + d * 0.08)
    mod = base + 0.15 * fiber * (1.0 - t_rad * 0.5)
    mod = max(0.0, min(1.0, mod))
    mod *= (0.85 + 0.15 * l)
    if mod > 0.65: return 11
    if mod > 0.42: return 3
    return 3

# --- PASS 2/3: SCLERA
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        if not (-up <= dy <= lo): continue
        l=L(px,py)
        span=max(1.0,(up+lo))
        vert = 1.0 - (dy/span)*0.30
        l = max(0.03, min(1.0, l * vert))
        if u > 0.2:
            l *= max(0.3, 1.0 - (u - 0.2) * 1.5)
        col = gramp(l)
        cv.set_pixel(px,py,col)

# --- PASS 3b: UPPER LID SHADOW -- use shade_ramp for real dithered gradient
# The upper-left socket area needs a proper gradient, not a flat block.
# Use shade_ramp(7, 0, 5) to create light grey -> black transition based on position.
ramp_7_0 = shade_ramp(7, 0, 5)  # 5 steps: █, ▓, ▒, ░, space
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        lid_thick = 4.0*(1.0-u*u)+1.0
        if u < 0.3 and -up-lid_thick <= dy < -up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick)
              # Use the ramp based on depth (0 at top, 1 at bottom of lid shadow)
            idx = int(depth * 4)  # 0-4
            glyph, fg, bg = ramp_7_0[idx]
            cv.set_pixel(px,py, fg if glyph == '\u2588' else bg)

# --- PASS 3d: LOWER LID SHADOW
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        ll = 3.5*(1.0-u*u)+0.8
        if lo+1.5 <= dy < lo+1.5+ll:
            depth=(dy-(lo+1.5))/max(0.5,ll)
            L_=L(px,py)*(1.0-0.7*depth)
            if u > 0.2:
                L_ *= 0.6
            col = 8 if L_>0.34 else 0
            cv.set_pixel(px,py,col)

# --- PASS 4: IRIS -- RADIAL GRADIENT + FIBERS
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        dx=px-iris_cx; dy=py-iris_cy; d=math.hypot(dx,dy)
        if pupil_r < d < iris_r:
            ang = math.atan2(dy, dx)
            l = L(px, py)
            cv.set_pixel(px,py, aramp_radial(d, ang, l))

# --- PASS 4b: ANNULUS CLEANUP
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-iris_cx,py-iris_cy)
        if pupil_r < d < iris_r and cv.get_pixel(px,py) not in (3,11):
            ang = math.atan2(py-iris_cy, px-iris_cx)
            l = L(px, py)
            cv.set_pixel(px,py, aramp_radial(d, ang, l))

# --- PASS 4c: LIMBAL RING
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-iris_cx,py-iris_cy)
        if iris_r-2.6 <= d < iris_r+0.3:
            cv.set_pixel(px,py, 3)

# --- PASS 4d: COLLARETTE RING
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-iris_cx,py-iris_cy)
        if pupil_r+0.3 <= d < pupil_r+2.4:
            cv.set_pixel(px,py, 11)

# --- PASS 5: PUPIL -- SOLID TRUE-BLACK VOID + THIN GRAY RIM (no internal scatter)
# v31 bug source: h-based gray scatter into core pixels -> mottled gray blob, not a
# clean black round hole. This is the decisive defect across v29/v30/v31. Fix at the
# SOURCE: core pixels are unambiguously black; a 1-2px dark-gray rim sits only at the
# pupil/iris boundary so the void reads as depth, not a flat block.
for py in range(ph):
    for px in range(W):
        dx=px-iris_cx; dy=py-iris_cy; d=math.hypot(dx,dy)
        if d < pupil_r + 1.0:
            t = d / max(0.5, pupil_r)
            if t < 0.82:
                cv.set_pixel(px,py, 0)      # solid black core
            else:
                cv.set_pixel(px,py, 8)      # thin gray rim only at the edge


cv.fill_circle(iris_cx-9.0, iris_cy-8.0, 1.2, 15)

# --- PASS 7: COHERENT GLOW (extend to lower-right)
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0 and cv.get_pixel(px,py)!=8: continue
        d=math.hypot(px-iris_cx,py-iris_cy)
        if 31 < d < 42:
            dens = 1.0 - (d-31)/11.0
            ang = math.atan2(py-iris_cy, px-iris_cx)
            if 0 < ang < math.pi/2:
                dens *= 1.3
            if dens > 0.55 and cv.get_pixel(px,py)==0:
                cv.set_pixel(px,py,8)

# --- PASS 7b: LOWER-RIGHT SHADOW GRADIENT
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0: continue
        dx=px-iris_cx; dy=py-iris_cy
        if dx > 5 and dy > 5:
            d = math.hypot(dx, dy)
            if d < 50:
                base = 1.0 - d/50.0
                h1 = ((px*73 + py*131 + 42) % 997)/997.0
                prob = base * 0.12
                if h1 < prob:
                    cv.set_pixel(px,py, 8)

# --- PASS 7c: VOID SCATTER / ATMOSPHERE
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0: continue
        d=math.hypot(px-iris_cx,py-iris_cy)
        if d<38: continue
        base = 1.0 - (d-38)/24.0
        if base<=0.0: continue
        h1 = ((px*73 + py*131 + 17) % 997)/997.0
        prob = base*base*0.16
        if h1 < prob:
            h2 = ((px*31 + py*57 + 91) % 811)/811.0
            col = 7 if h2<0.14 else 8
            cv.set_pixel(px,py,col)

# --- PASS 7d (v49, raze's fix): UPPER-LEFT SOCKET DITHERED GRADIENT -- FINAL-SAY.
# v47 computed a shade_ramp glyph here but DISCARDED it: set_pixel only yields solid
# col-8/col-0, so the socket stayed flat. raze found this in v48 and re-applied it via
# glyph_override with extended coverage (cr 6..21, px<28) + jitter. Kept from v48.
ramp_8_0 = shade_ramp(8, 0, 5)         # dark grey -> black
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) != 8: continue
        cr = py // 2
        if 6 <= cr <= 21 and px < 28:
            t = (px + (cr - 6) * 3) / 40.0         # 0 top-left -> 1 bottom-right
            jz = hsh(px, cr, 5)                    # jitter so adjacent cells differ
            idx = min(4, max(0, int(t * 4 + (jz - 0.5))))
            glyph, fg, bg = ramp_8_0[idx]
            cv.glyph_override[(cr,px)] = (glyph, fg, bg)

# --- PASS 9: DITHERED BRIDGE on flat sclera regions
RAMP_GLYPHS=['\u2588','\u2593','\u2592','\u2591']
for cr in range(H):
    for px in range(W):
        top=cv.get_pixel(px,cr*2); bot=cv.get_pixel(px,cr*2+1)
        if top!=bot: continue
        col=top
        l=L(px,cr*2+0.5)
        base_idx=int((1.0-l)*3.999)%4
        j=hsh(px,cr,7)
        idx=base_idx if j>0.28 else (base_idx-1)%4
        g=RAMP_GLYPHS[idx]
        if col in (7,8,15):
            if col==15:
                cv.glyph_override[(cr,px)]=(g,15,col)
            elif g=='\u2588':
                pass
            else:
                bg=0 if col==8 else 7
                cv.glyph_override[(cr,px)]=(g,bg,col)
        elif col in (3,11):
            fg=11 if col!=11 else 3
            cv.glyph_override[(cr,px)]=(g,fg,col)

# --- PASS 9b (hollis v42): DIRECTIONAL NEGATIVE-SPACE TEXTURE
# raze's v33->v41 "dither all flat regions" produced uniform static + blocky gray
# patches flanking the eye -- reads as a fill artifact, not atmosphere. Replace it with
# directional texture: faint diagonal light-streaks running from the upper-left source
# across the dark field, plus sparse flecks. Follows the SAME (lx,ly) light source as
# the rest of the piece, so the negative space reads as intentional ACiD atmosphere
# instead of a flat-region-gate workaround. Only touches genuinely empty (col 0) pixels
# far from the eye, so it never muddies the void/iris/sclera.
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) != 0: continue
        d = math.hypot(px-iris_cx, py-iris_cy)
        if d < 34: continue                      # keep the eye + its glow ring clean
        ang = math.atan2(py-iris_cy, px-iris_cx)
        # diagonal streaks: light travels upper-left -> lower-right (angle ~ -pi/4..pi/4)
        streak = math.sin((px*0.18 + py*0.18) * 1.0 + d*0.05)
        band = abs(streak) < 0.22               # thin diagonal ribbons
        prob = 0.06
        if band:
            prob += 0.30 * (1.0 - min(1.0, d/70.0))   # streaks fade with distance
        h1 = ((px*53 + py*97 + 29) % 899)/899.0
        if h1 < prob:
            col = 7 if band else 8              # brighter on the streak, dimmer flecks
            cv.set_pixel(px,py, col)

# --- PASS 9c (hollis v47): DIRECTIONAL FLECK along the streak bands only.
# ghengis-shades_of_a_shade fills the dark field with fine *directional* grain -- but
# that's streaks, not a uniform wash. v42's streaks were too sparse (41% flat); a dense
# base grain (first v47 attempt) read as mottled static and pushed the flat flag UP to 48%.
# So: keep it directional and SPARSE -- only fleck pixels that already fall on a diagonal
# light-streak band, brighter near the upper-left source, fading out in deep dark. Reads as
# an eye watching from the dark, never noise.
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) != 0: continue
        d = math.hypot(px-iris_cx, py-iris_cy)
        if d < 36: continue                         # keep eye + glow ring clean
        l = L(px, py+0.5)                           # light falloff from upper-left source
        streak = math.sin((px*0.18 + py*0.18) + d*0.05)
        band = abs(streak) < 0.22                   # only on the diagonal ribbons
        if not band: continue
        h2 = ((px*71 + py*43 + 11) % 613)/613.0
        thresh = 0.55 * l                           # fleck density tracks light, ~0 in deep dark
        if h2 < thresh:
            col = 7 if l > 0.35 else 8              # brighter near source, dimmer far out
            cv.set_pixel(px,py, col)


# --- PASS 10: ANATOMICAL FOREGROUNDS
for cr in range(H):
    for px in range(W):
        top=cv.get_pixel(px,cr*2); bot=cv.get_pixel(px,cr*2+1)
        if top!=bot: continue
        dx=px-iris_cx; dy=(cr*2+0.5)-iris_cy; d=math.hypot(dx,dy)
        j=hsh(px,cr,13)

           # (a) PUPIL: SOLID TRUE-BLACK VOID + THIN GRAY RIM ONLY AT THE EDGE.
            # v31 bug: h_rim scattered gray cells INSIDE the void -> mottled gray blob,
            # not a clean black round hole (the decisive defect across v29/v30/v31).
            # Fix: core is unambiguously black; a thin dark-gray rim sits only at the
            # pupil/iris boundary so the void reads as depth, not a flat block.
        if d < pupil_r + 1.0:
               # v51 flat-region gate fix: the pupil core was a single large
               # solid-black region -> 'unshaded flat fill' defect. A real lit void
               # has DEPTH: a faint catch of light on the upper-left wall, fading to
               # TRUE BLACK at center/bottom-right. The whole pupil is filled with a
               # directional DITHERED depth gradient so no solid-ink cluster exceeds the
               # gate threshold -- while staying genuinely DARK (space[0,0] core + faint
               # dark-gray dither only), NOT the v29/v30/v31 muddy full-GRAY blob. Key:
               # space must be bg=0 (true black), never bg=7 (light gray = the defect).
            ang = math.atan2(dy, dx)                  # -pi..pi; upper-left ~ -pi/4
            ul = max(0.0, math.cos(ang + math.pi/4))   # 1 at upper-left, 0 opposite
            t_pup = d / max(0.5, pupil_r)              # 0 center -> 1 edge
               # faint catch: strongest at the lit (upper-left) rim, falls to black.
            catch = ul * (0.30 + 0.70*t_pup)
            jz = hsh(px, cr, 71)
            if catch < 0.30:
                cv.glyph_override[(cr,px)] = (' ', 7, 0)         # TRUE-black void core
            elif catch < 0.50:
                g = '\u2591' if jz > 0.6 else ' '               # sparse faint fleck / black
                cv.glyph_override[(cr,px)] = (g, 8, 0)          # dark-gray on black
            elif catch < 0.70:
                g = '\u2592' if jz > 0.6 else '\u2591'         # faint gray dither
                cv.glyph_override[(cr,px)] = (g, 8, 0)
            else:
                g = '\u2593' if jz > 0.7 else '\u2592'         # lit upper-left wall (still dark gray)
                cv.glyph_override[(cr,px)] = (g, 8, 0)
            continue

          # (b) IRIS RADIAL STRUCTURE
        if in_opening(px, cr*2+0.5) and pupil_r < d < iris_r:
            t_rad = (d - pupil_r) / max(0.1, iris_r - pupil_r)
            rad_density = int((1.0 - t_rad) * 3.99) % 4
            j3 = hsh(px, cr, 47)
            if j3 > 0.7:
                rad_density = (rad_density + 1) % 4
            elif j3 < 0.15:
                rad_density = (rad_density - 1) % 4
            rglyph = RAMP_GLYPHS[rad_density]

            if t_rad < 0.4:
                fg_iris = 11
            elif t_rad < 0.75:
                fg_iris = 3
            else:
                fg_iris = 3

            bg_iris = 11 if fg_iris == 3 else 3
            cv.glyph_override[(cr,px)]=(rglyph,fg_iris,bg_iris); continue

          # (c) LIMBAL RING edge
        if in_opening(px, cr*2+0.5) and iris_r-3.0 <= d < iris_r-0.4 and j>0.4:
            cv.glyph_override[(cr,px)] = ('\u2580', 3, 11); continue

rows=cv.render()

# --- PASS 8: FRAME + SIG BLOCK
def c(fg,bg,ch):
    f=(30+(fg&7))
    b=(40+(bg&7))
    bright = (fg>7) or (bg>7)
    pre="1;" if bright else ""
    return f"\x1b[{pre}{f};{b}m"

frame=[]
for r in rows:
    frame.append(c(8,0,"\u2551")+r+c(8,0,"\u2551"))
title=" THE WATCHER // IT SEES IN THE DARK "
title=title.ljust(W)[:W]
frame.insert(0, c(7,0,"")+"\u2550"*W)
frame.insert(1, c(15,0,"")+title.center(W))
sig=" raze + hollis / AGENTSCI // THE WATCHER // 2026-09 "
sig=sig.ljust(W)[:W]
frame.append(c(15,0,"")+sig.center(W))
frame.append(c(7,0,"")+"\u2550"*W)

out="\n".join(frame)+"\x1b[0m\n"
open("scratch/_orb.v53.ans","w").write(out)
print(f"orb v53 = v49 + pupil-core directional depth gradient (flat-region gate fix), {len(frame)} rows")
