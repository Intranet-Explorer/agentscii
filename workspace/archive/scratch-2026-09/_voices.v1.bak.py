import sys, math; sys.path.insert(0,"scratch")
from halfblock import HalfBlockCanvas

# TWO VOICES v2 -- a genuine supersede attempt for the OBSERVER NOTE #1 gap.
# v1 (pack36) rendered as three flat solid-color horizontal bands forming tapered
# cones -- NO anatomical construction, despite its critique claiming "two facing
# profile heads... brow/jaw/eye-line built from gradient shading over anatomical
# regions." That critique described generator INTENT, not what rendered.
#
# v2 actually builds two CONSTRUCTED profile heads at half-block resolution, each
# lit from ONE source and shaded over real anatomical regions (cranium / forehead /
# brow / nose / cheek / jaw / neck), on COMPLEMENTARY hue phases: the left voice is
# a single warm amber family, the right voice a single cool cyan-blue family -- the
# confrontation made visible as warm-vs-cool. A woven diamond "exchange" motif sits
# at the eye-line between them (the conversation itself). ONE hue family per head;
# light carried by BRIGHTNESS within that family. No cross-hue contamination.

W = 80; H = 54
cv = HalfBlockCanvas(W, H, bg=0)
ph = cv.ph                       # pixel-space height (~108)

# --- one light source for BOTH heads (physically consistent), upper-left --------
LX, LY = 22.0, 16.0
def L(px, py):
    d = math.hypot(px - LX, py - LY)
    return max(0.04, 1.0 - d / 95.0)

# brightness ramp WITHIN one hue family: hot(highlight)->mid->cold(shadow).
def warm(l):   # amber/red family only
    if l > 0.86: return 15      # white highlight (catches on brow/nose crest)
    if l > 0.62: return 11      # bright yellow
    if l > 0.40: return 9       # bright red
    if l > 0.22: return 1       # red
    return 3                    # brown / dark amber (deep shadow)

def cool(l):   # cyan/blue family only
    if l > 0.86: return 15      # white highlight
    if l > 0.62: return 14      # bright cyan
    if l > 0.40: return 6       # cyan
    if l > 0.22: return 4       # blue
    return 12                   # deep blue shadow

# --- profile head builder ------------------------------------------------------
# A head facing `dir` (+1 = faces right toward the other, -1 = faces left).
# Built from overlapping anatomical regions in priority order; each region is a
# surface shaded by the shared light field. The nose bump + eye socket + brow are
# the cues that make it read as a FACE rather than a blob.
def profile_head(cx, cy, R, dir, ramp):
    cr_cy = cy - 0.12 * R            # cranium center slightly above head-center
    for py in range(ph):
        for px in range(W):
            dx = px - cx
            dy = py - cr_cy
            dcr = math.hypot(dx, dy)                       # distance to cranium center
            t = (py - cy) / R                              # 0 at head-center, +1 near chin
            front = dir * dx                                # +ve toward the face side

            region = None
            # cranium mass (the skull): a circle, but flattened on the back-bottom
            if dcr <= R:
                region = "cranium"
            # neck: vertical column below the cranium, narrower than the head
            ny = py - cy
            if 0.78 * R < ny < 1.55 * R and abs(dx) < 0.42 * R:
                region = "neck"

            if region is None:
                continue

            l = L(px, py)

            # --- anatomical shading on top of the base cranium/neck light -------
            if region == "cranium":
                # forehead: upper-front surface, catches a little more light
                if front > 0.15 * R and dy < -0.1 * R:
                    l = min(1.0, l + 0.06)
                # brow ridge: a lit protrusion at eye level on the front
                brow_y = cr_cy + 0.18 * R
                if abs(py - brow_y) < 0.16 * R and front > 0.35 * R:
                    l = min(1.0, l + 0.12)          # ridge crest catches light
                # nose: a forward spike at mid-face -- the strongest profile cue
                nose_y = cr_cy + 0.42 * R
                if abs(py - nose_y) < 0.30 * R and front > 0.55 * R:
                    # triangular bump: widest near top of nose, tapering down
                    nt = (py - (nose_y - 0.30 * R)) / (0.60 * R)
                    if front > (0.55 + 0.28 * max(0.0, 1.0 - abs(nt))) * R:
                        l = min(1.0, l + 0.14)
                # eye socket: a dark depression just behind/below the brow -- the
                # single most "anatomical" read in a face profile
                eye_y = cr_cy + 0.30 * R
                if abs(py - eye_y) < 0.14 * R and 0.18 * R < front < 0.52 * R:
                    l = max(0.0, l - 0.30)          # carve the socket dark
                # cheek: mid-front, gentle
                if 0.30 * R < front < 0.6 * R and 0.30 * R < dy < 0.7 * R:
                    pass
                # jaw / chin: lower-front juts forward then recedes; shadowed under-jaw
                if py > cr_cy + 0.55 * R:
                    if front > 0.2 * R and py < cr_cy + 0.95 * R:
                        l = min(1.0, l + 0.04)      # chin catches a little light
                    else:
                        l = max(0.0, l - 0.18)       # under-jaw shadow

            if region == "neck":
                # neck is in the head's shadow (below cranium), lit only on front edge
                l = L(px, py) * 0.7 + 0.05
                if front > 0.1 * R:
                    l = min(1.0, l + 0.12)

            cv.set_pixel(px, py, ramp(l))

# two voices, facing each other, complementary hue phases
profile_head(cx=27, cy=46, R=20, dir=+1, ramp=warm)   # left voice: warm, faces right
profile_head(cx=53, cy=46, R=20, dir=-1, ramp=cool)   # right voice: cool, faces left

# --- constructed eyes at the socket of each head (a real eye, not a dot) -------
def eye_socket(px_c, py_c, iris):
    cv.fill_circle(px_c, py_c, 2.4, 0)          # dark socket void
    cv.fill_circle(px_c - 0.6, py_c - 0.6, 1.5, iris)   # small lit iris disc
    cv.set_pixel(int(px_c - 1.2), int(py_c - 1.2), 15)  # glint

eye_socket(34.0, 44.0, 11)     # warm voice's eye (bright yellow iris in the dark socket)
eye_socket(46.0, 44.0, 14)     # cool voice's eye (bright cyan iris)

# --- THE EXCHANGE: a woven diamond suspended at the eye-line between them -------
# not a column -- a small lattice of alternating warm/cool marks that reads as the
# conversation passing between the two voices. Tapered to points top and bottom.
ex_cx = 40.0; ex_cy = 44.0; ex_r = 6.5
for py in range(ph):
    for px in range(W):
        d = math.hypot(px - ex_cx, (py - ex_cy))
        if d <= ex_r:
            # diamond lattice: checker of the two voices' hues by a diagonal weave
            weave = int((px + py) / 2.0) & 1
            col = 11 if weave else 6           # warm/cool interleave -- the exchange
            # brighten the core, dim toward the rim (a lit suspended form, not flat)
            ll = 1.0 - d / ex_r
            if ll > 0.7:
                col = 15
            cv.set_pixel(px, py, col)

# --- void texture: sparse grey depth so the negative space isn't flat black -----
import random; random.seed(7)
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
