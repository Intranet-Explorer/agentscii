import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas
from canvas import shade_ramp

# THE WATCHER (_orb v33) -- raze + hollis. Built on v32 (blocked by flat-region gate).
# TWO TARGETED FIXES over v32:
#        (1) PUPIL CORE: subtle radial gradient with dithered density glyphs, not flat black
#        (2) UPPER-LEFT SOCKET: proper directional gradient using shade_ramp() + glyph_override
#     The mottling defect from v29/v30/v31 is NOT reintroduced -- these are coherent gradients,
#     not random hash noise.
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

iris_r                  = 17
pupil_r                 = 8

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
ramp_7_0 = shade_ramp(7, 0, 5)   # 5 steps: █, ▓, ▒, ░, space
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
        lid_thick = 4.0*(1.0-u*u)+1.0
        if u < 0.3 and -up-lid_thick <= dy < -up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick)
            idx = int(depth * 4)   # 0-4
            glyph, fg, bg = ramp_7_0[idx]
            cr = py // 2
            cv.set_pixel(px, cr*2, fg)
            cv.set_pixel(px, cr*2+1, bg)
            if glyph != '█' and glyph != ' ':
                cv.glyph_override[(cr, px)] = glyph

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
        if iris_r <= d < iris_r+1.5:
            cv.set_pixel(px,py, 0)

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

# --- PASS 5: PUPIL -- SUBTLE RADIAL GRADIENT WITH DITHERED DENSITY GLYPHS
# v32 had a flat black core (62 cells of solid █, color 0). The gate wants internal shading
# variation. This is NOT the mottling defect -- it's a coherent radial gradient from black
# (center) to dark gray (rim), using dithered density glyphs via glyph_override.
ramp_0_8 = shade_ramp(0, 8, 5)   # 5 steps: █, ▓, ▒, ░, space
for py in range(ph):
    for px in range(W):
        dx=px-iris_cx; dy=py-iris_cy; d=math.hypot(dx,dy)
        if d < pupil_r + 1.0:
            t = d / max(0.5, pupil_r)
            cr = py // 2
            if t < 0.50:
                # Very center: solid black (keep the void reading as dark)
                cv.set_pixel(px,py, 0)
            elif t < 0.70:
                # Inner ring: subtle dithered transition (▓ = ~75% black, ~25% gray)
                glyph, fg, bg = ramp_0_8[1]   # ▓
                cv.set_pixel(px, cr*2, fg)
                cv.set_pixel(px, cr*2+1, bg)
                cv.glyph_override[(cr, px)] = glyph
            elif t < 0.85:
                # Mid ring: more dithering (▒ = ~50% black, ~50% gray)
                glyph, fg, bg = ramp_0_8[2]   # ▒
                cv.set_pixel(px, cr*2, fg)
                cv.set_pixel(px, cr*2+1, bg)
                cv.glyph_override[(cr, px)] = glyph
            else:
                # Outer rim: light gray (solid)
                cv.set_pixel(px,py, 8)

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

# --- PASS 7d: UPPER-LEFT SOCKET TEXTURE -- proper directional gradient using shade_ramp
# v32 had a flat dark-gray block (53 cells of color 8). The gate wants a real directional
# gradient. Use shade_ramp(7, 0, 5) to create light gray -> black transition based on position.
ramp_7_0_socket = shade_ramp(7, 0, 5)   # 5 steps: █, ▓, ▒, ░, space
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) != 8: continue
        cr = py // 2
        # Upper-left socket area (rows ~13-21 pixel = cell rows 6-10, cols 4-24)
        if 6 <= cr <= 10 and px < 25:
            # Position-based gradient: top-left is lighter, bottom-right is darker
            t = (px + (cr - 6) * 3) / 30.0   # 0 at top-left, 1 at bottom-right
            idx = min(4, int(t * 4))
            glyph, fg, bg = ramp_7_0_socket[idx]
            cv.set_pixel(px, cr*2, fg)
            cv.set_pixel(px, cr*2+1, bg)
            if glyph != '█' and glyph != ' ':
                cv.glyph_override[(cr, px)] = glyph

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
        idx=base_idx if j>0.28 else (base_idx+1)%4
        glyph=RAMP_GLYPHS[idx]
        if glyph=='\u2588': continue
        cv.glyph_override[(cr,px)]=glyph

# --- PASS 10: FRAME + TITLE CARD + SIGNATURE
lines = cv.render()
out=[]
out.append("\x1b[1;37m" + "═"*80 + "\x1b[0m")
out.append("\x1b[1;37mTHE WATCHER // IT SEES IN THE DARK\x1b[0m")
for l in lines:
    out.append(l)
out.append("\x1b[0m" + " "*80)
out.append("\x1b[22;37mraze + hollis / AGENTSCI // THE WATCHER // 2026-09\x1b[0m")
out.append("\x1b[1;37m" + "═"*80 + "\x1b[0m")

data = "\n".join(out) + "\x1b[0m\n"
with open("_orb.v33.ans","w",encoding="utf-8") as f:
    f.write(data)
print("wrote _orb.v33.ans:", len(data), "bytes")
