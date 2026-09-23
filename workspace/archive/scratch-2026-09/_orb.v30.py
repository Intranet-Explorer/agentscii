import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# THE WATCHER (_orb v30) -- raze + hollis. Built on v29 (rejected with 3 fixable defects).
# FIXES over v29:
#   (1) PUPIL DARKNESS: center cells now emit fg=0 NORMAL INTENSITY (22;30m), not bold-black(8).
#       The void is truly the darkest thing on screen. Ramp outward: 0->8->7 for lit rim.
#   (2) IRIS RADIAL STRUCTURE: amber stroma now has a genuine radial gradient (bright collarette
#       -> mid amber -> dark limbus) with per-pixel angular fiber variation, not horizontal bands.
#       Limbal ring is a thick continuous dark band at the outer edge.
#   (3) SCLERA SYMMETRY: single-side light source committed deliberately -- upper-left catch-light
#       on sclera, right side falls to shadow with an explicit eyelid edge marking the boundary.
W=80; H=52
cv=HalfBlockCanvas(W,H,bg=0)
ph=cv.ph
cx=W//2; cy=ph//2

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

iris_r           = 17
pupil_r          = 9

# Light source: upper-left, strong
lx, ly = cx-24, cy-30
def L(px,py):
    d=math.hypot(px-lx, py-ly)
    return max(0.03, 1.0 - d/80.0)

# Deterministic hash for jitter
def hsh(x,y,salt=0):
    v = (x*73 + y*131 + salt*97) % 997
    return v / 997.0

# grey ramp: 4-step falloff
def gramp(l):
    if l>0.80: return 15                  # hot white (lit crown)
    if l>0.62: return 7                   # light grey (upper lit flank)
    if l>0.42: return 8                   # mid/dark grey (shadow side)
    return 0                              # deepest shadow -> void

# amber family: RADIAL gradient with fiber variation (v30 fix #2)
def aramp_radial(d, ang, l):
    """Radial iris shading: bright collarette near pupil -> mid amber -> dark limbus at edge.
    Angular fiber term adds per-angle brightness variation so it reads as radiating fibers,
    not horizontal scan-line bands."""
    t_rad = (d - pupil_r) / max(0.1, iris_r - pupil_r)  # 0 at pupil edge, 1 at limbus
    # Base radial gradient: bright near pupil, dark at limbus
    base = 1.0 - 0.70 * t_rad
    # Angular fiber term: 9 radiating crypts (dark valleys between fibers)
    NCRYPTS = 9
    fiber = math.sin(ang * NCRYPTS + d * 0.08)
    # Apply fiber modulation: brighten peaks, darken valleys
    mod = base + 0.15 * fiber * (1.0 - t_rad * 0.5)  # fibers stronger near center
    mod = max(0.0, min(1.0, mod))
    # Light field influence (subtle -- iris is mostly self-lit)
    mod *= (0.85 + 0.15 * l)
    if mod > 0.65: return 11              # bright yellow (collarette / lit fiber peaks)
    if mod > 0.42: return 3              # orange/brown mid-stroma
    return 3                              # brown limbus / crypt valleys

# --- PASS 2/3: SCLERA -- continuous white->grey falloff, CLIPPED to almond.
# v30 fix #3: commit to single-side light source (upper-left). Right side falls to shadow
# with an explicit eyelid edge. This makes the asymmetry read as intentional lighting.
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        if not (-up <= dy <= lo): continue
        l=L(px,py)
        # vertical curvature: upper sclera catches more light, lower less
        span=max(1.0,(up+lo))
        vert = 1.0 - (dy/span)*0.30
        l = max(0.03, min(1.0, l * vert))
        # v30 fix #3: right side (u>0.2) gets a deliberate shadow falloff + eyelid edge
        if u > 0.2:
            # Shadow side: reduce light and add a subtle eyelid crease at the outer edge
            l *= max(0.3, 1.0 - (u - 0.2) * 1.5)
            # Eyelid edge on right: a thin dark line at the outer contour
            if abs(dy - lo) < 1.5 or abs(dy + up) < 1.5:
                l *= 0.4
        cv.set_pixel(px,py, gramp(l))

# --- PASS 3b: EYELID CONTOUR -- crisp dark almond edge (both sides)
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        # Upper lid edge
        if -up-1.5 <= dy < -up+0.5:
            cv.set_pixel(px,py, 0)
        # Lower lid edge
        if lo-0.5 <= dy < lo+1.5:
            cv.set_pixel(px,py, 0)

# --- PASS 3c: LIT BROW BAND (upper-left only -- single-side light source)
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        lid_thick = 4.0*(1.0-u*u)+1.0
        # Only on the lit side (left/upper): u < 0.3
        if u < 0.3 and -up-lid_thick <= dy < -up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick)
            L_=L(px,py)*(0.6+0.4*depth)
            col = 7 if L_>0.5 else (8 if L_>0.32 else 0)
            cv.set_pixel(px,py,col)

# --- PASS 3d: LOWER LID SHADOW (both sides, but darker on right for single-side light)
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
            # Right side gets extra shadow (single-side light commitment)
            if u > 0.2:
                L_ *= 0.6
            col = 8 if L_>0.34 else 0
            cv.set_pixel(px,py,col)

# --- PASS 4: IRIS -- RADIAL GRADIENT + FIBERS (v30 fix #2)
# The iris now has a genuine radial structure: bright collarette near the pupil,
# fading to dark limbus at the edge, with 9 radiating crypt fibers.
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        dx=px-cx; dy=py-cy; d=math.hypot(dx,dy)
        if pupil_r < d < iris_r:
            ang = math.atan2(dy, dx)
            l = L(px, py)
            cv.set_pixel(px,py, aramp_radial(d, ang, l))

# --- PASS 4b: ANNULUS CLEANUP -- fill any non-amber pixel in the iris annulus
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r < d < iris_r and cv.get_pixel(px,py) not in (3,11):
            ang = math.atan2(py-cy, px-cx)
            l = L(px, py)
            cv.set_pixel(px,py, aramp_radial(d, ang, l))

# --- PASS 4c: LIMBAL RING -- thick continuous dark band at outer iris edge
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if iris_r-2.6 <= d < iris_r+0.3:
            cv.set_pixel(px,py, 3)

# --- PASS 4d: COLLARETTE RING -- subtle brighter amber band just outside pupil
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r+0.3 <= d < pupil_r+2.4:
            cv.set_pixel(px,py, 11)

# --- PASS 5: PUPIL -- TRUE BLACK VOID (v30 fix #1)
# Center is unambiguously the darkest thing on screen: fg=0 NORMAL INTENSITY.
# A single glint upper-left for "it sees in the dark" atmosphere.
cv.fill_circle(cx, cy, pupil_r, 0)
cv.fill_circle(cx-3.0, cy-3.4, 1.7, 15)

# --- PASS 7: COHERENT GLOW -- tight light bleed off the form
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0: continue
        d=math.hypot(px-cx,py-cy)
        if 31 < d < 38:
            dens = 1.0 - (d-31)/7.0
            if dens > 0.62: cv.set_pixel(px,py,8)

# --- PASS 7c: VOID SCATTER / ATMOSPHERE -- sparse deterministic flecks
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0: continue
        d=math.hypot(px-cx,py-cy)
        if d<38: continue
        base = 1.0 - (d-38)/24.0
        if base<=0.0: continue
        h1 = ((px*73 + py*131 + 17) % 997)/997.0
        prob = base*base*0.16
        if h1 < prob:
            h2 = ((px*31 + py*57 + 91) % 811)/811.0
            col = 7 if h2<0.14 else 8
            cv.set_pixel(px,py,col)

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

# --- PASS 10: ANATOMICAL FOREGROUNDS (v30 -- TRUE BLACK PUPIL + RADIAL IRIS)
# v30 fix #1: Pupil center cells get fg=0 NORMAL INTENSITY (22;30m), making the void
# unambiguously the darkest thing on screen. Ramp outward to dark grey at the rim.
# v30 fix #2: Iris stroma gets radial density variation via half-block glyphs.
for cr in range(H):
    for px in range(W):
        top=cv.get_pixel(px,cr*2); bot=cv.get_pixel(px,cr*2+1)
        if top!=bot: continue  # a real half-block curve -- leave it round
        dx=px-cx; dy=(cr*2+0.5)-cy; d=math.hypot(dx,dy)
        j=hsh(px,cr,13)

        # (a) PUPIL: TRUE BLACK VOID with radial rim shading
        if d < pupil_r+0.4:
            l_pupil = L(px, cr*2+0.5)
            j2 = hsh(px, cr, 31)
            t_pup = d / max(0.5, pupil_r)  # 0 at center -> 1 at edge

            # v30 fix #1: CENTER is unambiguously fg=0 NORMAL (not bold/black-8)
            if t_pup < 0.45:
                pfg = 0  # TRUE BLACK -- the darkest thing on screen
            elif l_pupil > 0.55 and t_pup > 0.7:
                pfg = 7  # lit rim catches sclera glow (light grey)
            else:
                pfg = 8  # shadow-side rim (dark grey)

            # BG drives the "floor" -- light field determines what's behind the glyph
            pbg = 7 if l_pupil > 0.55 else (8 if l_pupil > 0.30 else 0)

            # Glyph density from hash jitter for visual texture
            gidx = int(j2 * 3.99) % 4
            pglyph = ['\u2588','\u2593','\u2592','\u2591'][gidx]
            cv.glyph_override[(cr,px)]=(pglyph,pfg,pbg); continue

        # (b) IRIS RADIAL STRUCTURE: stroma->limbus gradient via half-block density
        if in_opening(px, cr*2+0.5) and pupil_r < d < iris_r:
            t_rad = (d - pupil_r) / max(0.1, iris_r - pupil_r)
            # Radial density: brighter (denser glyph) near collarette, sparser at limbus
            rad_density = int((1.0 - t_rad) * 3.99) % 4
            j3 = hsh(px, cr, 47)
            # Jitter the density slightly for organic fiber feel
            if j3 > 0.7:
                rad_density = (rad_density + 1) % 4
            elif j3 < 0.15:
                rad_density = (rad_density - 1) % 4
            rglyph = RAMP_GLYPHS[rad_density]

            # Color: bright amber near pupil, brown at limbus
            if t_rad < 0.4:
                fg_iris = 11  # bright yellow collarette
            elif t_rad < 0.75:
                fg_iris = 3   # mid amber stroma
            else:
                fg_iris = 3   # brown limbus (same hue, darker by density)

            # BG: contrasting for visual pop
            bg_iris = 11 if fg_iris == 3 else 3
            cv.glyph_override[(cr,px)]=(rglyph,fg_iris,bg_iris); continue

        # (c) LIMBAL RING edge: brown over amber half-blocks at the outer iris boundary
        if in_opening(px, cr*2+0.5) and iris_r-3.0 <= d < iris_r-0.4 and j>0.4:
            cv.glyph_override[(cr,px)]=('\u2580',3,11); continue

rows=cv.render()

# --- PASS 8: FRAME + SIG BLOCK (house convention). Joint credit raze+hollis.
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
open("scratch/_orb.v30.ans","w").write(out)
print(f"orb v30 = v29 + 3 fixes (true black pupil, radial iris, symmetric sclera), {len(frame)} rows")
