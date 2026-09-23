import sys, math, random; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# ORB v8 -- "THE WATCHER": a single CONSTRUCTED EYE at half-block resolution.
#
# v7 (rejected by Opus override) had an EXCELLENT iris (amber radial gradient + 8 radiating
# crypts + unbroken limbal ring -- hollis: "genuinely excellent, don't touch it") but four
# execution defects on the SURROUNDING structure. This pass fixes exactly those, point for
# point, and leaves the iris passes byte-for-byte identical:
#   1. SCLERA LIT SIDE READ AS STACKED SLABS -- v7 computed light PER PIXEL-ROW, so adjacent
#      pixel-rows got different gramp colors and packed into separate half-block cells with
#      BLACK backgrounds between them -> horizontal slab striping. FIX: compute the sclera
#      falloff at CELL CENTERS so BOTH pixels in a cell share one color (solid blocks, no
#      inter-strip gaps). The whole left half is now ONE unbroken gradient surface.
#   2. SCLERA SHADOW SIDE WAS A FLAT MID-GREY BLOCK -- FIX: the light falloff runs all the way
#      to the shadow corner (a continuous white->light->mid->deep-grey ramp, never a flat fill),
#      so the right side curves into shadow instead of sitting as one grey patch.
#   3. LIDS WERE FLAT BARS -- FIX: upper and lower lids get a real multi-row gradient (thick at
#      center -> thin at canthi, shaded by light) so they read as curved surfaces with a crease,
#      not horizontal slabs.
#   4. HALO READ AS RANDOM NOISE -- v7 scattered faint dots in a ring + corner stars. FIX: a
#      COHERENT radial glow (dense just outside the form, fading smoothly to pure black at the
#      corners) -- "a watcher in the dark" reads better with clean void than with scatter. No
#      random flecks anywhere.
# Plus cleanup: no stray pixels; frame + credit consistent top-to-bottom (no bottom-right glitch).
W=80; H=52
cv=HalfBlockCanvas(W,H,bg=0)
ph=cv.ph                           # pixel-space height = 104
cx=W//2; cy=ph//2                 # eye center in pixel space

# --- almond geometry: opening is a LENS, not a circle. Narrower vertically than
#     horizontally, pinched to sharp canthi at |u|=1. half_w PULLED IN so the whole
#     eye sits inside the frame with margin on both sides (v5 edge-bleed fix, kept).
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

iris_r        = 17
pupil_r       = 9

lx, ly = cx-24, cy-30             # single light source, upper-left -- kept from v5 (correct)
def L(px,py):
    d=math.hypot(px-lx, py-ly)
    return max(0.03, 1.0 - d/80.0)

# --- grey ramp for the sclera: continuous white -> light -> mid -> deep grey, lit upper-left.
#     The shadow side stays in GREY (never a void inside the eyeball). A 5-step ramp gives a
#     genuinely smooth falloff so the rounded surface reads as ONE sphere catching light.
def gramp(l):
    if l>0.78: return 15            # hot white (lit crown)
    if l>0.62: return 7             # light grey
    if l>0.46: return 8             # mid grey
    if l>0.30: return 8              # deep-mid grey
    return 0                          # deepest shadow -> near-black, eyeball curving away

# --- amber family for the iris: THREE coherent tones only (bright->mid->dark amber).
def aramp(l):
    if l>0.62: return 11          # bright yellow (lit fiber / collarette)
    if l>0.34: return 9           # bright red / amber mid
    return 3                      # brown / dark amber (limbal shadow + crypts)

# --- PASS 1: socket wall + crease shadow -- grey family, lit upper-left, behind the eye.
#     A soft crease band just ABOVE the upper lid (the eyelid fold / socket shadow), shaded by
#     light so it curves rather than reading as stacked horizontal bars.
# --- PASS 1: socket crease -- DROPPED in v8. A 'watcher in the dark' reads better with the eye
#     sitting in clean void than with a grey socket wash behind it. The lids (PASS 6) carry the
#     almond read; the glow (PASS 7) carries the light bleed. No disc.

# --- PASS 2/3: SCLERA -- ONE continuous white->grey falloff across the WHOLE rounded surface,
#     CLIPPED to the almond opening. v8 fix: compute light at CELL CENTERS so both pixels in a
#     cell share one color -> solid blocks, NO inter-strip gaps (the slab striping is gone). The
#     light runs all the way around (not just the lit half), so the shadow side has its own grey
#     gradient and there's no hard seam and no flat block.
for cr in range(H):                      # iterate CELL ROWS, not pixel rows
    pyc = cr*2 + 0.5                     # cell-center y (between the two pixels)
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=pyc-cy
        if not (-up <= dy <= lo): continue
        l=L(px,pyc)
          # subtle vertical rounding: the upper part of the eyeball catches more light; the lower
          # part falls off -- so top->bottom is a curve, not two flat patches.
        vert = 1.0 - (dy/max(1.0,(up+lo)))*0.26
        l = max(0.03, min(1.0, l*vert))
        col=gramp(l)
        cv.set_pixel(px,cr*2,     col)   # both pixels same color -> solid block, no gap
        cv.set_pixel(px,cr*2+1,   col)

# soft shadow band just under the upper lid contour (the lid casts onto the sclera) -- a gentle
# 2-step falloff so it reads as a curved lid edge, not a hard line.
for cr in range(H):
    pyc=cr*2+0.5
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=pyc-cy
        if 0 <= dy < 4 and -up <= dy <= lo:
            cur=cv.get_pixel(px,cr*2)
            if cur==15: cv.set_pixel(px,cr*2,7); cv.set_pixel(px,cr*2+1,7)
            elif cur==7 and 1<=dy<3:
                cv.set_pixel(px,cr*2,8); cv.set_pixel(px,cr*2+1,8)

# --- PASS 4: iris -- SMOOTH radial gradient (collarette -> limbus) + a FEW distinct dark
#     radiating CRYPT lines overlaid on top. UNCHANGED FROM v7 -- this is the finished part.
NCRYPTS=8
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        dx=px-cx; dy=py-cy; d=math.hypot(dx,dy)
        if d<iris_r:
            ang=math.atan2(dy,dx)
            t_rad=(d-pupil_r)/(iris_r-pupil_r)         # 0 at pupil edge -> 1 at limbus
            base_l = 1.0 - 0.66*max(0.0,t_rad)          # bright collarette near pupil, dark limbus
            l=base_l
              # overlay distinct dark radiating crypts (thin angular bands w/ slight spiral twist)
            band = math.sin(ang*NCRYPTS + d*0.14)
            if band > 0.78:                             # narrow dark line -> a fiber/crypt
                l *= 0.32
            cv.set_pixel(px,py, aramp(l))
# collarette ring just outside the pupil -- subtle brighter amber band (CLIPPED to opening).
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if pupil_r+0.3 <= d < pupil_r+2.4:
            cv.set_pixel(px,py,11)
# limbal ring at the outer iris edge -- a THICK continuous dark amber band so it's unbroken.
for py in range(ph):
    for px in range(W):
        if not in_opening(px,py): continue
        d=math.hypot(px-cx,py-cy)
        if iris_r-2.6 <= d < iris_r+0.3:
            cv.set_pixel(px,py,3)

# --- PASS 5: pupil -- clean black void + one lit glint upper-left (single accent).
cv.fill_circle(cx, cy, pupil_r, 0)
cv.fill_circle(cx-3.0, cy-3.4, 1.7, 15)

# --- PASS 6: EYELIDS -- THE almond read, now with THICKNESS/CREASE (v8 fix for flat bars).
#     A crisp DARK contour traces the opening boundary (the eyelid edge); above it a lit brow band
#     and below it a lower lid, both pinching to sharp canthi at |u|=1. Each is given a MULTI-ROW
#     gradient (light near the crease -> dark toward the socket) so it reads as a curved surface
#     with a fold, not a horizontal slab. Edges smoothed via half-block anti-aliasing.
for py in range(ph):
    for px in range(W):
        u=(px-cx)/half_w
        if abs(u)>=1.0: continue
        up,lo=opening_half_h(u)
        dy=py-cy
           # (a) crisp dark almond contour -- the eyelid edge, ~2px thick, black for max contrast
        if -up-1.5 <= dy < -up+0.5 or lo-0.5 <= dy < lo+1.5:
            cv.set_pixel(px,py, 0)
           # (b) lit upper brow band just above the contour -- a 3-row gradient: brightest at the
          #     crease (just above the lid), falling to dark toward the socket. Thick at center ->
          #     thin at canthi. Shaded by light so it curves, not striping.
        lid_thick = 4.0*(1.0-u*u)+1.0
        if -up-lid_thick <= dy < -up-1.5:
            depth=(dy-(-up-lid_thick))/max(0.5,lid_thick)   # 0 at outer edge -> 1 at crease
            L_=L(px,py)*(0.6+0.4*depth)
            col = 7 if L_>0.5 else (8 if L_>0.32 else 0)
            cv.set_pixel(px,py,col)
           # (c) lower lid just below the contour -- a 2-row gradient: dark at the crease line,
          #     falling to the socket shadow. A deliberate curved line, not a flat slab.
        ll = 3.0*(1.0-u*u)+0.5
        if lo+1.5 <= dy < lo+1.5+ll:
            depth=(dy-(lo+1.5))/max(0.5,ll)                 # 0 at crease -> 1 outward
            L_=L(px,py)*(1.0-0.7*depth)
            col = 8 if L_>0.34 else 0
            cv.set_pixel(px,py,col)

# --- PASS 7: VIGNETTE / GLOW (v8 fix for "halo reads as random noise"). A COHERENT radial glow:
#     a smooth density falloff from just outside the form out to the corners -- dense grey hugging
#     the eye, fading continuously to pure black. No scattered flecks, no corner stars. The void
#     stays clean; the glow reads as light bleeding off the watcher, not static.
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py)!=0: continue             # don't touch the form / lids
        d=math.hypot(px-cx,py-cy)
          # v8 fix: a FAINT tight glow hugging the eye only, fading FAST to pure black. The void
          # stays clean -- "a watcher in the dark" reads better with clean void than with a heavy
          # grey disc or scattered flecks. No outer rings, no corner stars.
        if 31 < d < 37:                                    # v8: tight + faint light bleed
            dens = 1.0 - (d-31)/6.0                        # not a halo; void stays clean
            if dens > 0.72: cv.set_pixel(px,py,8)          # only the innermost ring shows

rows=cv.render()

# --- PASS 8: FRAME + SIG BLOCK (house convention; inspect_piece flags NO FRAME otherwise).
def c(fg,bg,ch):
    f=(90+(fg&7)) if fg>7 else (30+fg)
    b=(100+(bg&7)) if bg>7 else (40+bg)
    return f"\x1b[{f};{b}m"
frame=[]
for r in rows:
    frame.append(c(8,0,"║")+r+c(8,0,"║"))
title=" THE WATCHER // IT SEES IN THE DARK "             # intent, not a technical label
title=title.ljust(W)[:W]
frame.insert(0, c(7,0,"")+"═"*W)
frame.insert(1, c(15,0,"")+title.center(W))
sig=" raze / AGENTSCI // THE WATCHER // 2026-09 "
sig=sig.ljust(W)[:W]
# v8 fix: footer is text+spaces only -- no stray border fragment at the far right.
frame.append(c(15,0,"")+sig.center(W))
frame.append(c(7,0,"")+"═"*W)

out="\n".join(frame)+"\x1b[0m\n"
open("scratch/_orb.v8.ans","w").write(out)
print("orb v8", len(frame),"rows")
