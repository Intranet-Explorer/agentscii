#!/usr/bin/env python3
# _lanternkeeper -- a 3/4-turned figure peering into a lantern it holds UP beside its face,
# lit in the dark. FIGURE is the subject: gradient-built anatomy (figure_common primitives)
# under strong chiaroscuro so brow/jaw/cheek read as separate surfaces. ONE continuous global
# light field drives every surface; per-surface shading is carried by DENSITY (the RAMP), not
# by separate hue multipliers -- so the form reads smooth with a single coherent warm->cool
# transition, no per-surface color seams. "Lit in the dark" register, figure-as-subject.
# Solo raze build; hollis to add the border pass -> joint pack40 candidate.
import sys, math; sys.path.insert(0, "scratch")
from figure_common import new_canvas, set_cell, light_field, eye, c, sgr, RESET, W, RAMP

H = 56
cv = new_canvas(h=H, w=W)

# --- ONE global warm->cool ramp: density tracks light continuously (smooth form);
#     hue shifts only at major warm->cool transitions -> no per-surface banding.
def hue_ramp(L):
    L = max(0.0, min(1.0, L))
    ch = RAMP[int(L * (len(RAMP)-1) + 0.5) % len(RAMP)]
    if   L > 0.74: fg = 93            # white-hot crest
    elif L > 0.52: fg = 92            # bright yellow (lit mass)
    elif L > 0.36: fg = 107           # warm magenta mid
    elif L > 0.22: fg = 31            # dim warm shadow (normal red, receding)
    else:          fg = 4             # deep blue floor -- far side recedes to void
    return ch, fg

def paint(region_fn):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = hue_ramp(L(x, y))
                set_cell(cv, x, y, ch, fg, 0)

# --- LIGHT: lantern held UP beside the head; light falls left across the form ----
LX, LY, LMAX = 52.0, 21.0, 26.0
def L(x, y): return light_field(x, y, LX, LY, lmax=LMAX, ambient=0.08)

# --- HEAD: large 3/4-turned skull, center-left of frame ------------------------
HCX, HCY, HR = 35.0, 21.0, 13.0
def in_skull(x, y):
    t = (y - HCY) / HR
    if abs(t) > 1.0: return False
    hw = HR * math.sqrt(1.0 - t*t)
    return abs(x - HCX) <= hw
paint(in_skull)

# --- BROW ridge: a thin band across the upper face (crest reads via density) -----
def brow_band(x, y):
    by = HCY - HR*0.30
    return abs(y - by) <= 1.2 and abs(x - HCX) <= HR*0.80*math.sqrt(max(0.0,1-((y-by)/1.4)**2))
paint(brow_band)

# --- EYE: one constructed eye in the lit 3/4 view ------------------------------
eye(cv, HCX + HR*0.26, HCY + HR*0.18, r=HR*0.30, iris_fg=92, glint=True)

# --- NOSE: a shaded wedge down center ------------------------------------------
def nose(x, y):
    ny0 = HCY + HR*0.10
    t = (y - ny0)/(HR*0.55)
    if t < 0 or t > 1: return False
    w = 0.6 + 2.4*t
    return abs(x - HCX) <= w and y >= ny0
paint(nose)

# --- CHEEKBONE: a surface below the eye on the near side -----------------------
def cheek(x, y):
    cy = HCY + HR*0.46
    return abs(y - cy) <= 1.3 and HCX-3 < x < HCX+HR*0.72
paint(cheek)

# --- JAW / chin: taper the lower skull to a jawline ----------------------------
def jaw(x, y):
    jy = HCY + HR*0.84
    return jy <= y <= jy+3 and abs(x - HCX) <= 4.5*(1-(y-jy)/3.0)+1.5
paint(jaw)

# --- NECK: two capsules down from the jaw --------------------------------------
def capsule(x0,y0,x1,y1,hw):
    seg = math.hypot(x1-x0,y1-y0) or 1.0
    ux,uy=(x1-x0)/seg,(y1-y0)/seg
    for y in range(int(min(y0,y1))-2,int(max(y0,y1))+3):
        for x in range(int(min(x0,x1))-2,int(max(x0,x1))+3):
            t=max(0.0,min(1.0,((x-x0)*ux+(y-y0)*uy)/seg))
            px,py=x0+t*(x1-x0),y0+t*(y1-y0)
            d=math.hypot(x-px,y-py)
            if d<=hw:
                ch,fg=hue_ramp(L(x,y)*(1.0-0.35*(d/hw)))   # cylindrical falloff = rounded tube
                set_cell(cv,x,y,ch,fg,0)

neck_y = HCY + HR*1.02
capsule(HCX-2, neck_y, HCX-3, neck_y+7, 2.6)
capsule(HCX+3, neck_y, HCX+4, neck_y+7, 2.4)

# --- SHOULDERS: a broad shaded bar ---------------------------------------------
def shoulders(x, y):
    sy = neck_y + 6
    t = (y - sy)/5.0
    if t < 0 or t > 1: return False
    w = 4 + 20*t
    return abs(x - HCX) <= w
paint(shoulders)

# --- ARM reaching UP to hold the lantern beside the head -----------------------
sh_y = neck_y + 7
capsule(HCX+13, sh_y, HCX+16, sh_y-6, 2.6)               # upper arm up-out
capsule(HCX+16, sh_y-6, LX-1, LY, 2.4)                   # forearm up to the lantern

# --- THE LANTERN: warm glow object held beside the head (the light source) -----
lx, ly = int(LX), int(LY)
for y in range(ly-1, ly+3):
    for x in range(lx-2, lx+3):
        set_cell(cv, x, y, "\u2588", 93, 0)
set_cell(cv, lx, ly-2, "\u2588", 15, 0)                    # top cap
for y in range(ly-4, ly+5):                                 # soft glow halo
    for x in range(lx-6, lx+7):
        d = math.hypot(x-lx, y-ly)
        if 3.0 < d <= 6.0:
            set_cell(cv, x, y, "\u2591", 92, 0)

# --- GROUND GLOW: a faint warm pool where the lantern's light meets the floor ----
gy = int(neck_y) + 16
for y in range(gy, gy+3):
    for x in range(int(HCX)-18, int(HCX)+18):
        d = math.hypot(x - (HCX+2), y - gy) / 18.0
        Lg = max(0.0, 1.0 - d) * 0.5
        if Lg > 0.10:
            ch, fg = hue_ramp(Lg)
            set_cell(cv, x, y, ch, fg, 0)

# --- render the figure ---------------------------------------------------------
from figure_common import render
out = []
render(cv, out)

# --- boxed title card + house sig block ----------------------------------------
out.append("")
out.append(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
def centerline(text, fg):
    pad = W - len(text); left = pad // 2
    return sgr(104, 40) + " " * left + sgr(fg, 40) + text + sgr(104, 40) + " " * (pad - left)
out.append(centerline("LANTERNKEEPER", 93))
out.append(centerline("a figure lit in the dark", 96))
out.append(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

open("scratch/_lanternkeeper.ans", "w").write("\n".join(out) + "\n" + RESET)
print("rows:", len(out))
