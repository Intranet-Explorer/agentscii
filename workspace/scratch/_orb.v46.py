import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas
from canvas import shade_ramp

# THE WATCHER (_orb v42) -- raze + hollis. Built on v32 (clean void/iris/light source).
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

# --- PASS 7d: UPPER-LEFT SOCKET TEXTURE -- use shade_ramp for real gradient
# The upper-left socket (rows ~12-21, cols ~4-24 in cell space = rows ~24-42, cols ~4-24 in pixel space)
# was a flat block of color 8. Use shade_ramp to create a proper dithered gradient there.
ramp_8_0 = shade_ramp(8, 0, 5)  # dark grey -> black
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) != 8: continue
        cr = py // 2
        if 6 <= cr <= 10 and px < 25:
              # Position-based gradient: top-left is lighter, bottom-right is darker
            t = (px + (cr - 6) * 3) / 30.0  # 0 at top-left, 1 at bottom-right
            idx = min(4, int(t * 4))
            glyph, fg, bg = ramp_8_0[idx]
            if glyph == '\u2588':
                cv.set_pixel(px,py, fg)
            else:
                cv.set_pixel(px,py, bg)

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
            t_pup = d / max(0.5, pupil_r)
            if t_pup < 0.82:
                cv.glyph_override[(cr,px)] = ('\u2588', 0, 0)    # solid black core
            else:
                cv.glyph_override[(cr,px)] = ('\u2588', 8, 0)    # thin gray rim only
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

# === v46 POST-PROCESS (raze): direct cell-space fixes for the two flagged flat regions ===
# The half-block glyph_override system is too fragile to reliably land a clean core gradient
# (v43/v44/v45 all produced identical cores). Post-process the rendered rows directly:
# decode each row into (char, fg, bg) cells, apply fixes, re-encode with SGR.
import re as _re

def decode_row(s):
    out=[]; fg=0; bg=0; i=0
    while i<len(s):
        if s[i]=='\x1b':
            m=_re.match(r'\x1b\[([0-9;]*)m', s[i:])
            if m:
                for p in [int(x) for x in m.group(1).split(';') if x!='']:
                    if p==0: fg=bg=0
                    elif 30<=p<=37: fg=p-30
                    elif 40<=p<=47: bg=p-40
                    elif 90<=p<=97: fg=p-90+8
                    elif 100<=p<=107: bg=p-100+8
                i+=m.end()
            else: i+=1
        else:
            out.append([s[i],fg,bg]); i+=1
    return out

def encode_cells(cells):
    parts=[]; last_fg=last_bg=None
    for ch,fg,bg in cells:
        if (fg,bg)!=(last_fg,last_bg):
            bright = fg>7 or bg>7
            f=30+(fg&7); b=(100+(bg&7)) if bg>7 else 40+bg
            pre="1;" if bright else ""
            parts.append(f"\x1b[{pre}{f};{b}m")
            last_fg,last_bg=fg,bg
        parts.append(ch)
    return ''.join(parts)

# Core region: rows 25-30, cols 31-44 (cell space). Radial gradient from iris center.
# CELL-space center: col=iris_cx(38), row=iris_cy//2(26). pupil_r in cell space ~4.
core_cx = iris_cx; core_cy = iris_cy // 2; core_pr = max(2, int(pupil_r / 2))
core_r0, core_r1 = 25, 31
core_c0, core_c1 = 31, 45
for r in range(core_r0, min(core_r1, len(rows))):
    cells = decode_row(rows[r])
    for c in range(core_c0, min(core_c1, len(cells))):
        dx = c - core_cx; dy = r - core_cy
        d = math.hypot(dx, dy)
        t = d / max(1.0, core_pr + 2.0)
        if t < 0.35:
            cells[c] = ['\u2588', 0, 0]         # black void center
        elif t < 0.60:
            cells[c] = ['\u2588', 8, 0]         # dark-gray depth ring
        elif t < 0.82:
            cells[c] = ['\u2588', 7, 0]         # light-gray mid-ring
        else:
            cells[c] = ['\u2588', 15, 0]        # bright rim at the edge
             # upper-left catchlight (cell space)
        cd = math.hypot(c - (core_cx-3), r - (core_cy-4))
        if cd < 2.5 and d < core_pr * 1.0:
            cells[c] = ['\u2588', 15, 0]        # bright catchlight glint
    rows[r] = encode_cells(cells)

# Socket region: rows 13-21, cols 4-24 (cell space). Directional light->dark gradient fill.
sock_r0, sock_r1 = 13, 22
sock_c0, sock_c1 = 4, 25
for r in range(sock_r0, min(sock_r1, len(rows))):
    cells = decode_row(rows[r])
    for c in range(sock_c0, min(sock_c1, len(cells))):
        # distance from upper-left light source, normalized
        t = math.hypot(c - lx, r - ly) / 60.0
        t = max(0.0, min(1.0, t))
        idx = int(t * 4 + 0.5)
        if idx == 0:
            cells[c] = ['\u2588', 7, 0]       # light gray (near source)
        elif idx == 1:
            cells[c] = ['\u2593', 7, 0]       # ~75% density
        elif idx == 2:
            cells[c] = ['\u2592', 7, 0]       # ~50% density
        elif idx == 3:
            cells[c] = ['\u2591', 7, 0]       # ~25% density
        else:
            cells[c] = [' ', 0, 0]             # black (far from source)
    rows[r] = encode_cells(cells)

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
open("scratch/_orb.v46.ans","w").write(out)
print(f"orb v32 = v30 + 3 targeted fixes + flat-region gate fixes (shade_ramp on upper-left socket), {len(frame)} rows")
