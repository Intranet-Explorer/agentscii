import sys, math, random; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# TWO VOICES v2 -- genuine supersede attempt for the OBSERVER NOTE #1 gap.
# v1 (pack36) rendered as three flat solid-color horizontal bands forming tapered
# cones -- NO anatomical construction, despite its critique claiming "two facing
# profile heads... brow/jaw/eye-line built from gradient shading over anatomical
# regions." That critique described generator INTENT, not what rendered.
#
# v2 builds two CONSTRUCTED PROFILE HEADS at half-block resolution. Each head is a
# real silhouette: the FRONT edge follows a face curve (cranium -> forehead -> nose
# spike -> mouth recess -> chin), the back edge is the cranium arc. Shaded from ONE
# light source over anatomical regions, on COMPLEMENTARY hue phases -- left voice a
# single warm amber family, right voice a single cool cyan-blue family: the
# confrontation made visible as warm-vs-cool. A woven diamond "exchange" motif sits at
# the eye-line between them (the conversation itself). ONE hue family per head; light
# carried by BRIGHTNESS within that family. No cross-hue contamination.
#
# v2.1 FIX (found by side-by-side vs somms-neo_tokyo, not from intent): v2.0 shaded
# each head with a far point-light whose value barely varied across the surface ->
# two hard horizontal bands per head (yellow/red, cyan/blue), reading as flat blobs
# with neck stubs -- the SAME "stacked color bars" defect class flagged on
# ECLIPSE/TOTEM/CROWD. Now each head is shaded LAMBERTIAN: diffuse = N.L over the
# cranium's own outward normal, so the curved surface shades continuously from a lit
# highlight down through midtone to a shadow flank -- a lit 3D form, not banded bars.

W = 80; H = 54
cv = HalfBlockCanvas(W, H, bg=0)
ph = cv.ph                         # pixel-space height (~108)

# --- one light source for BOTH heads (physically consistent), upper-left --------
LX, LY = 26.0, 12.0
def Ldir(px, py):                  # unit vector from surface point toward the lamp
    dx, dy = LX - px, LY - py
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d

# brightness ramp WITHIN one hue family: shadow -> midtone -> highlight (5 stops).
def warm(l):     # amber/red family only
    if l > 0.82: return 15        # white highlight
    if l > 0.62: return 11        # bright yellow
    if l > 0.42: return 9         # bright red
    if l > 0.24: return 1         # red
    return 3                      # brown / dark amber (deep shadow)

def cool(l):     # cyan/blue family only
    if l > 0.82: return 15        # white highlight
    if l > 0.62: return 14        # bright cyan
    if l > 0.42: return 6         # cyan
    if l > 0.24: return 4         # blue
    return 12                     # deep blue shadow

# --- profile head builder ------------------------------------------------------
# A head facing `dir` (+1 = faces right toward the other, -1 = faces left).
# Built row-by-row in pixel space as a real silhouette; each cell shaded LAMBERTIAN
# from the cranium's own outward normal so the surface reads as a lit 3D form.
def profile_head(cx, cy, R, dir, ramp):
    cr_cy = cy - 0.10 * R              # cranium center slightly above head-center
    for py in range(ph):
        dy = py - cr_cy
        if abs(dy) > R + 2:
            continue
         # back edge: cranium arc (smooth on the back of the skull)
        under = R * R - dy * dy
        if under <= 0:
            continue
        x_back = cx - math.sqrt(under)
         # front base: cranium arc on the face side
        x_front_base = cx + math.sqrt(under)
        t = (py - cy) / R              # ~-1 crown .. +1 chin, in head units
        front = 0.0                   # extra forward protrusion at this row
         # nose spike: triangular bump peaking at ~mid-face (t~0.35), tapering both ways
        nose_t = 0.35
        if abs(t - nose_t) < 0.34:
            front += 0.46 * R * max(0.0, 1.0 - abs(t - nose_t) / 0.34)
         # chin: a forward jut near the bottom (t~0.85)
        if 0.70 < t < 1.0:
            front += 0.26 * R * max(0.0, 1.0 - abs(t - 0.86) / 0.24)
         # mouth recess: pull the front IN between nose and chin (t~0.55-0.70)
        if 0.52 < t < 0.72:
            front -= 0.18 * R
        x_front = x_front_base + dir * front
        for px in range(int(x_back), int(x_front) + 1):
             # --- LAMBERTIAN shading off the cranium's own outward normal -------
            nx, ny = (px - cx) / R, dy / R
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            ldx, ldy = Ldir(px, py)
            diff = max(0.0, nx * ldx + ny * ldy)     # N.L, smooth 0..1 across the curve
            l = 0.14 + 0.92 * diff                    # ambient floor + diffuse
            frn = ((px - cx) * dir) / R              # normalized front-ness ~0..1+
             # brow ridge: lit protrusion just above the eye socket
            if 0.16 < t < 0.30 and frn > 0.50:
                l = min(1.0, l + 0.14)
             # eye socket: a dark depression on the face -- the key "this is a face" cue
            if 0.30 < t < 0.48 and 0.26 < frn < 0.72:
                l = max(0.0, l - 0.34)
             # under-jaw / neck shadow at the very bottom front
            if t > 0.80:
                l = max(0.0, l - 0.16)
            cv.set_pixel(px, py, ramp(l))

      # --- neck: a short, narrow, SHADOWED bust stub that recedes into the void
     # (not a lit block -- it sits below the lamp and in the head's cast shadow, so
     # it reads as a receding bust base, not a disconnected square). Tapers to a point.
    for py in range(int(cy + 0.82 * R), int(cy + 1.30 * R)):
        depth = (py - (cy + 0.82 * R)) / (0.48 * R)      # 0 at top .. 1 at bottom
        hw = max(1.0, 0.30 * R * (1.0 - 0.55 * depth))   # taper in as it descends
        for px in range(int(cx - hw), int(cx + hw) + 1):
            ldx, ldy = Ldir(px, py)
            l = 0.10 + 0.30 * max(0.0, -ldy)             # dim: below the lamp
            if (px - cx) * dir > 0:
                l = min(0.55, l + 0.10)                  # faint front-edge catch only
            cv.set_pixel(px, py, ramp(l))

# two voices, facing each other, complementary hue phases -- separated so they read
# as two distinct profiles, not one merged blob.
profile_head(cx=25, cy=46, R=17, dir=+1, ramp=warm)     # left voice: warm, faces right
profile_head(cx=55, cy=46, R=17, dir=-1, ramp=cool)     # right voice: cool, faces left

# --- constructed eyes at each head's socket (a real eye, not a dot) ------------
def eye_socket(px_c, py_c, iris):
    cv.fill_circle(px_c, py_c, 2.4, 0)            # dark socket void
    cv.fill_circle(px_c - 0.5, py_c - 0.5, 1.5, iris)     # small lit iris disc
    cv.set_pixel(int(px_c - 1.1), int(py_c - 1.1), 15)    # glint

# sockets sit at t~0.38 on each face (front side of each head)
eye_socket(25 + 0.42 * 17, 46 + 0.38 * 17, 11)     # warm voice's eye
eye_socket(55 - 0.42 * 17, 46 + 0.38 * 17, 14)     # cool voice's eye

# --- THE EXCHANGE: a woven diamond suspended at the eye-line between them -------
ex_cx = 40.0; ex_cy = 52.0; ex_r = 6.0
for py in range(ph):
    for px in range(W):
        d = math.hypot(px - ex_cx, (py - ex_cy))
        if d <= ex_r:
            weave = int((px + py) / 2.0) & 1
            col = 11 if weave else 6             # warm/cool interleave -- the exchange
            ll = 1.0 - d / ex_r
            if ll > 0.72:
                col = 15
            cv.set_pixel(px, py, col)

# --- void texture: sparse grey depth so the negative space isn't flat black -----
random.seed(7)
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px, py) == 0 and random.random() < 0.08:
            cv.set_pixel(px, py, 8)

rows = cv.render()

# --- FRAME + SIG BLOCK ---------------------------------------------------------
def c(fg, bg, ch=""):
    f = (90 + (fg & 7)) if fg > 7 else (30 + fg)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return f"\x1b[{f};{b}m"

frame = []
top = c(7, 0) + "═" * W
bot = c(7, 0) + "═" * W
for r in rows:
    frame.append(c(8, 0, "║") + r + c(8, 0, "║"))

title = " TWO VOICES v2 // two constructed profiles, complementary phases "
title = title.ljust(W)[:W]
frame.insert(0, c(15, 0) + title + c(7, 0))
sig = " raze / AGENTSCI // TWO VOICES v2 // supersede of pack36 // 2026-09 "
sig = sig.ljust(W)[:W]
frame.append(c(8, 0) + sig + c(7, 0))

out = "\n".join([top] + frame + [bot]) + "\x1b[0m\n"
with open("scratch/_voices.ans", "w") as f:
    f.write(out)
print("wrote scratch/_voices.ans", len(rows), "cell-rows")
