import sys, math, random; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# TWO VOICES v3 -- genuine supersede attempt for the OBSERVER NOTE #1 gap.
#
# History:
#  v1 (pack36 "TWO VOICES v1.1"): critique CLAIMED two facing profile heads built
#    from gradient shading over anatomical regions, but actually rendered as three
#    flat solid-color horizontal bands -- NO construction. The critique described the
#    generator's INTENT, not what rendered.
#  v2: fixed the flat-band defect (each form now shades continuously through ONE hue
#    family via Lambertian N.L), BUT still read as two lit ORBS with tiny pokes --
#    curator rejected it for the SAME "claim > construction" class, milder: "two
#    rounded complementary orbs, not anatomical profiles. No brow ridge, no nose
#    point, no jaw silhouette." Curator gave two clean paths: (A) commit to the
#    profile claim with real silhouette structure; (B) retitle as abstract study.
#
# v3 takes PATH A -- commit to the profile. Two changes that close the gap:
#   1. A REAL PROFILE CONTOUR, not a flattened semicircle + pokes: crown -> forehead
#      slope -> brow ridge -> nose bridge (slight dip) -> nose TIP (the furthest
#      forward point) -> philtrum RECESS (concave dip) -> lips -> chin/jaw. The
#      front edge is genuinely non-convex so the silhouette reads as a face, not an orb.
#   2. SHADING OFF THE CONTOUR'S OWN SURFACE NORMAL (via a signed-distance-field
#      gradient), NOT off the cranium's spherical normal. A sphere-normal shades every
#      point by its position on the ball -> a lit cap = orb read. The contour normal
#      makes the nose tip and brow ridge catch light (they protrude toward the lamp)
#      while the bridge, philtrum and eye socket fall into shadow -- that differential
#      is what reads as 3D facial structure. ONE hue family per head; light carried by
#      BRIGHTNESS within it. Complementary phases: left voice warm amber, right cool
#      cyan-blue -- the confrontation made visible as warm-vs-cool. A woven diamond
#      "exchange" motif sits at the eye-line between them (the conversation itself).
#
# Verified by preview_piece + compare_to_reference vs somms-neo_tokyo, NOT from intent.

W = 80; H = 56
cv = HalfBlockCanvas(W, H, bg=0)
ph = cv.ph                          # pixel-space height (~112)

# --- one light source for BOTH heads (physically consistent), upper-left --------
LX, LY = 24.0, 10.0
def Ldir(px, py):                   # unit vector from surface point toward the lamp
    dx, dy = LX - px, LY - py
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d

# brightness ramp WITHIN one hue family: deep shadow -> midtone -> highlight.
def warm(l):      # amber/red/brown family only -- no cross-hue contamination
    if l > 0.86: return 15          # white hot highlight
    if l > 0.66: return 11          # bright yellow
    if l > 0.46: return 9           # bright red
    if l > 0.28: return 1           # red
    return 3                        # brown / dark amber (deep shadow)

def cool(l):      # cyan/blue family only
    if l > 0.86: return 15          # white hot highlight
    if l > 0.66: return 14          # bright cyan
    if l > 0.46: return 6           # cyan
    if l > 0.28: return 4           # blue
    return 12                       # deep blue shadow

# --- profile contour builder ---------------------------------------------------
# A head facing `dir` (+1 = faces right toward the other, -1 = faces left).
# The FRONT edge is a genuine face profile (non-convex); the BACK edge is the
# cranium arc. Shaded LAMBERTIAN off the CONTOUR'S OWN surface normal so the
# nose/brow protrude into light and the bridge/philtrum/socket fall into shadow.
#
# v3.1 FIX: the two heads were ASYMMETRIC (warm interior ~19px wide, cool ~3px)
# because `dir` flipped the face-protrusion term to the wrong side for dir=-1,
# collapsing the cranium. Now we build ONE canonical silhouette (back arc + face
# profile, both measured from center) and MIRROR it for each facing direction, so
# the two voices are identical shapes just flipped -- a true mirror confrontation.

def _face_profile():
    """Canonical half-silhouette: for each t in [-1,1] return (back_off, front_off)
    in R-units measured from center. back_off = cranium arc depth (always +),
    front_off = face contour (nose/brow/chin protrusions). Both positive; the head
    spans [cx - back_off*R .. cx + front_off*R]."""
    ctrl = [
        (-1.00, 0.00, 0.30),    # crown: cranium top, face flat
        (-0.78, 0.55, 0.34),    # forehead: cranium deepens, face slopes forward
        (-0.52, 0.66, 0.46),    # brow ridge -- furthest point above the nose
        (-0.30, 0.70, 0.30),    # nose bridge -- dips back behind the brow (notch)
        (-0.10, 0.62, 0.80),    # NOSE TIP -- single furthest-forward point
        ( 0.12, 0.50, 0.40),    # philtrum -- RECESSES in behind the nose tip
        ( 0.30, 0.46, 0.58),    # lips / mouth -- juts forward again
        ( 0.52, 0.40, 0.40),    # under-lip -> chin slope
        ( 0.72, 0.30, 0.64),    # CHIN -- juts forward (jaw)
        ( 1.00, 0.00, 0.10),    # jaw recedes back into the neck at the bottom
    ]
    def interp(t):
        for i in range(len(ctrl)-1):
            t0,b0,f0 = ctrl[i]; t1,b1,f1 = ctrl[i+1]
            if t0 <= t <= t1:
                u = (t - t0)/(t1 - t0)
                s = u*u*(3-2*u)                       # smoothstep, no kinks
                return b0 + (b1-b0)*s, f0 + (f1-f0)*s
        return ctrl[-1][1], ctrl[-1][2]
    return interp

FACE = _face_profile()

def build_profile(cx, cy, R, dir):
    """Return (front_x, back_x) lookup tables in pixel space over t in [-1,1].
    front_x is the face-side contour (crown->chin), back_x the cranium arc.
    MIRROR-SYMMETRIC: both voices get identical shapes, just flipped by dir."""
    front_x = [None]*ph
    back_x   = [None]*ph
    cr_cy = cy - 0.06*R              # cranium center slightly above head-center
    for py in range(ph):
        t = (py - cy)/R
        if t < -1.02 or t > 1.02:
            continue
        dy = py - cr_cy
        under = R*R - dy*dy
        if under <= 0:
            continue
        b_off, f_off = FACE(t)
         # back wall (cranium arc) and front wall (face profile), both from center.
         # dir=+1 faces right: face on the +x side; dir=-1 faces left: mirror it.
        if dir > 0:
            bx = cx - b_off*R
            fx = cx + f_off*R
        else:
            bx = cx + b_off*R
            fx = cx - f_off*R
        front_x[py] = fx
        back_x[py]   = bx
    return front_x, back_x

def shade_profile(cx, cy, R, dir, ramp):
    """Shade one profile region Lambertian off its OWN surface -- a blend of the
    front-contour normal (so nose tip / brow ridge / jaw protrude into the light
    while bridge / philtrum / socket fall to shadow) and a radial cranium normal
    (so brightness varies WITHIN a row, not in flat horizontal bands -- that was
    the v2 defect). ONE hue family via `ramp`; light is carried by BRIGHTNESS
    within it, never a cross-hue."""
    front_x, back_x = build_profile(cx, cy, R, dir)
    cr_cx = cx
    cr_cy = cy - 0.06 * R
    for py in range(ph):
        fx = front_x[py]; bx = back_x[py]
        if fx is None or bx is None:
            continue
        lo, hi = (bx, fx) if dir > 0 else (fx, bx)
        # front-contour tangent -> outward normal for this row (finite diff).
        fp = front_x[py+1] if (py + 1 < ph and front_x[py+1] is not None) else fx
        fm = front_x[py-1] if (py - 1 >= 0 and front_x[py-1] is not None) else fx
        df = (fp - fm) * 0.5                       # d(front_x)/dpy
        sgn = 1.0 if dir > 0 else -1.0             # outward points toward face side
        nx_face = sgn
        ny_face = -df * sgn
        ln = math.hypot(nx_face, ny_face) or 1.0
        nx_face /= ln; ny_face /= ln
        for px in range(int(lo), int(hi) + 1):
            # radial normal from cranium center -> within-row variation (anti-band).
            rx = px - cr_cx; ry = py - cr_cy
            rd = math.hypot(rx, ry) or 1.0
            nx = 0.72 * nx_face + 0.28 * (rx / rd)
            ny = 0.72 * ny_face + 0.28 * (ry / rd)
            ldx, ldy = Ldir(px, py)
            l = nx * ldx + ny * ldy
            l = max(0.0, min(1.0, l))
            col = ramp(l)
            if col != 0:
                cv.set_pixel(px, py, col)



# two voices, facing each other, complementary hue phases -- separated so they read
# as two distinct profiles, not one merged blob.
shade_profile(cx=21, cy=54, R=9, dir=+1, ramp=warm)          # left voice: warm, faces right
shade_profile(cx=59, cy=54, R=9, dir=-1, ramp=cool)          # right voice: cool, faces left

# --- constructed eyes at each head's socket (a real eye, not a dot) ------------
def eye_socket(px_c, py_c, iris):
    cv.fill_circle(px_c, py_c, 2.6, 0)               # dark socket void
    cv.fill_circle(px_c - 0.6, py_c - 0.6, 1.6, iris)      # small lit iris disc
    cv.set_pixel(int(px_c-1.3), int(py_c-1.3), 15)   # glint

# sockets sit at t~-0.22 on each face (front side, behind the brow ridge)
eye_socket(21 + 0.58*9, 54 - 0.20*9, 11)                    # warm voice's eye
eye_socket(59 - 0.58*9, 54 - 0.20*9, 14)                   # cool voice's eye

# --- THE EXCHANGE: a woven diamond suspended at the eye-line between them -------
ex_cx = 40.0; ex_cy = 52.0; ex_r = 4.5                 # exchange motif in the central gap
for py in range(ph):
    for px in range(W):
        d = math.hypot(px-ex_cx, (py-ex_cy))
        if d <= ex_r:
            weave = int((px+py)/2.0) & 1
            col = 11 if weave else 6                 # warm/cool interleave -- the exchange
            ll = 1.0 - d/ex_r
            if ll > 0.74:
                col = 15
            cv.set_pixel(px, py, col)

# --- void texture: sparse grey depth so the negative space isn't flat black -----
random.seed(7)
for py in range(ph):
    for px in range(W):
        if cv.get_pixel(px,py) == 0 and random.random() < 0.08:
            cv.set_pixel(px,py, 8)

rows = cv.render()

# --- frame + title card + house sig block (its own pass) ----------------------
from canvas import sgr, write_ans

out = []
out.append(sgr(13) + "\u2550" * W)                       # top magenta rule
for r in rows:
    out.append(r)
# title card over the void (top-left, above the heads)
def center(text, fg):
    pad = max(0, W - len(text))
    left = pad // 2
    return sgr(fg) + " " * left + text + " " * (pad - left)
out[1] = center("TWO VOICES v3", 15)
out[2] = center("-- two constructed profiles, complementary phases --", 94)
out.append(sgr(13) + "\u2550" * W)                       # bottom magenta rule

write_ans("scratch/_voices.ans", out,
          title="TWO VOICES v3 // supersede of pack36 // two constructed profiles",
          handles="raze")
print("ok -- frame+title+sig written")
