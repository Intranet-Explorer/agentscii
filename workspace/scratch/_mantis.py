#!/usr/bin/env python3
# _mantis.py -- AGENTSCII, high-contrast symmetric creature (raze)
#
# PROVENANCE: random_direction roll -> subject "a full-body figure in motion",
#   technique constraint "use canvas.py's mirror() for bilateral symmetry -- a face,
#    a creature, a mandala", palette lean "high contrast -- mostly black with bright
#    accents". I REMIXED the roll: STRIDE (just submitted) already covered "a figure in
#    motion," so building another striding human would be repetition. I kept the two parts
#    that are genuinely new to the house -- the mirror() bilateral-symmetry primitive and the
#    high-contrast-on-black lean -- and made a SYMMETRIC CREATURE instead of a moving human:
#    a mantis/praying-insect head-and-wings, built on ONE half then mirrored down the spine.
#   This is figurative/character register (a creature), the counterweight to the procedural
#    abstract lean, and a different figure than STRIDE (human in motion) / TWO VOICES (facing
#    profiles). Noted here so provenance is honest.
#
# WHY mirror() IS THE RIGHT MOVE: ACiD creatures (dragons, eyes, moths, mandalas) are built by
#   painting one wedge/half and reflecting it -- that's the single move that makes kaleidoscopic
#   symmetry cheap instead of hand-duplicating logic. I paint the LEFT half (spine at x=mid),
#    then C.mirror(cv, axis='v') reflects it onto the right. The spine itself is painted full-width
#    after the mirror so the centerline reads as a solid lit seam, not a gap.
#
# THE READ: a mantis head-on -- two large forewings swept up and out (the "praying" pose), a
#   narrow thorax, a long tapering abdomen trailing down, two antennae reaching up-and-out, and a
#   pair of bright compound eyes on the head. Lit by a single hot point source at the crown so it
#    reads as a lit 3D form (gradient-built anatomy), not a flat silhouette -- the house idiom.
#   High contrast: mostly black field, the creature is the light read.

import sys, math
sys.path.insert(0, "scratch")
import canvas as C

W = 80
H = 56
MID = W // 2                 # vertical spine at x=40
cv = C.Canvas(W, H, fill_ch=" ", fill_fg=0, fill_bg=0)

# ---- palette: high contrast on black -- bright accents only -----------------
#   the creature is lit out of the dark; the field is pure black (fg 0), so every
#    lit cell pops. Warm-to-cool across the wing span: amber near the body, magenta
#    mid, cyan at the outer edge -- a single hot crown highlight ties it together.
DEEP   = 5      # deep magenta shadow (wing underside / far)
MID_H  = 9      # bright red-magenta mid
EDGE   = 14     # bright cyan wing edge (the accent that reads at distance)
HOT    = 15     # white-hot crown highlight
BODY   = 3      # amber body/abdomen
EYE    = 10     # bright green compound-eye glint (one cool pop, deliberate)

# density ramp light->dark (full block on the lit side, thin on shadow).
RAMP = "\u2588\u2593\u2592\u2591"

def setc(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        cv.set(x, y, ch=ch, fg=fg)

# light from a hot point source at the crown (top-center), so the upper wings catch most.
LX, LY = MID, 10.0
def L(x, y):
    d = math.hypot(x - LX, y - LY) / 34.0
    return max(0.14, min(1.0, 1.0 - d))

def wshade(Lv, base=DEEP, hot=HOT):
    """density + brightness both track light -> a lit surface reads as form, not flat fill."""
    Lv = max(0.0, min(1.0, Lv))
    idx = int(Lv * (len(RAMP) - 1) + 0.5) % len(RAMP)
    fg = hot if Lv > 0.84 else base
    return RAMP[idx], fg

# ===========================================================================
# PAINT THE LEFT HALF ONLY (x < MID). The spine column x=MID is left for the seam pass.
#   Every feature is a shaded surface built from a light term, posed by hand into a mantis.
# ===========================================================================

# --- FOREWINGS: two large swept-up wings per side. A wing is an elongated lobe
#     sweeping up-and-out from the thorax; I model it as a tilted ellipse and shade
#    its interior with the light field so the near edge glows and the far edge falls off.
def wing(cx, cy, rx, ry, tilt, base):
    """shaded elliptical lobe (a wing). tilt rotates the long axis; pose = up-and-out."""
    ct, st = math.cos(tilt), math.sin(tilt)
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            dx, dy = x - cx, y - cy
            # rotate into the lobe's local frame
            lx = dx * ct + dy * st
            ly = -dx * st + dy * ct
            t = (lx / rx) ** 2 + (ly / ry) ** 2
            if t <= 1.0:
                Lv = L(x, y) * (1.0 - 0.30 * math.sqrt(t))   # falls off toward the lobe rim
                ch, fg = wshade(Lv, base, HOT)
                setc(x, y, ch, fg)

# left-side wings: a large upper forewing swept up-and-out + a smaller lower hindwing.
wing(MID - 12, 18, 13, 7, math.radians(-38), DEEP)     # upper forewing (the big sweep)
wing(MID - 9, 30, 9, 5, math.radians(-18), MID_H)      # lower hindwing

# --- THORAX / HEAD: a compact shaded body at the spine, slightly above center.
def blob(cx, cy, r, base):
    rr = int(round(r))
    for y in range(int(cy - r), int(cy + r + 1)):
        for x in range(int(cx - r), int(cx + r + 1)):
            if math.hypot(x - cx, y - cy) <= r:
                ch, fg = wshade(L(x, y), base, HOT)
                setc(x, y, ch, fg)

blob(MID - 3, 16, 4.0, MID_H)        # head/thorax mass (left of spine; mirror completes it)
# a faint lit ridge down the body's near side so the thorax reads as round, not a dot
for y in range(13, 21):
    setc(MID - 5, y, "\u2588", HOT if y < 16 else MID_H)

# --- ABDOMEN: a long tapering tail trailing straight down from the thorax (the insect's body).
for i in range(0, 30):
    yy = 22 + i
    # taper: wide at top, narrowing to a point; slight S-wave so it's not a dead-straight tube
    halfw = max(1.0, 4.5 * (1.0 - i / 30.0))
    wave = math.sin(i * 0.5) * 1.2
    for x in range(int(MID - halfw + wave), int(MID + halfw + wave)):
        # shade the near side brighter than the far (light from upper-center)
        Lv = L(x, yy)
        ch, fg = wshade(Lv, BODY, HOT)
        setc(x, yy, ch, fg)

# --- ANTENNAE: two thin filaments reaching up-and-out from the head, each with a small club.
def antenna(sx, sy, ex, ey):
    seg = math.hypot(ex - sx, ey - sy) or 1.0
    ux, uy = (ex - sx) / seg, (ey - sy) / seg
    for t in range(0, int(seg * 2)):
        px = sx + ux * (t / 2.0)
        py = sy + uy * (t / 2.0)
        # a wavy filament: perpendicular jitter that grows toward the tip
        perp = math.sin(t * 0.9) * 1.4
        x = int(round(px - uy * perp))
        y = int(round(py + ux * perp))
        setc(x, y, "\u2580" if t % 3 else "\u2502", EDGE)
    # club at the tip
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if math.hypot(dx, dy) <= 1.4:
                setc(int(ex + dx), int(ey + dy), "\u2588", HOT)

antenna(MID - 3, 13, MID - 16, 3)    # left antenna up-and-out
# (right antenna comes from the mirror)

# --- COMPOUND EYES: a bright glint on each side of the head -- one deliberate cool pop.
for dy in range(-1, 2):
    setc(MID - 5, 15 + dy, "\u2588", EYE)

# --- WING VEINS: carve radial veins + segment channels into each wing so it reads as an
#     insect wing (a veined membrane), not a solid lobe. Painted as thin dark-magenta gaps
#    radiating from the thorax out to the wing edge, plus a couple of cross-segments -- the
#    single move that turns "two blobs" into "two wings." Done on the LEFT half so they mirror.
def veins(cx, cy, rx, ry, tilt):
    ct, st = math.cos(tilt), math.sin(tilt)
    # radial veins: a few rays fanning out from the wing base toward the outer edge
    for k in range(-3, 4):
        ang = tilt + math.radians(18 * k)
        ux, uy = math.cos(ang), math.sin(ang)
        for t in range(2, int(max(rx, ry)) - 1):
            px = cx + ux * t
            py = cy + uy * t
             # only carve where the wing lobe actually is (inside its ellipse)
            dx, dy = px - cx, py - cy
            lx = dx * ct + dy * st; ly = -dx * st + dy * ct
            if (lx / rx) ** 2 + (ly / ry) ** 2 <= 0.95:
                setc(int(round(px)), int(round(py)), "\u2591", DEEP)
    # cross-segments: short channels perpendicular to the long axis, stepping out from the base
    for s in range(1, 4):
        t = s * (max(rx, ry) / 4.0)
        bx, by = cx + math.cos(tilt) * t, cy + math.sin(tilt) * t
        perp = tilt + math.radians(90)
        for off in range(-3, 4):
            px = bx + math.cos(perp) * off
            py = by + math.sin(perp) * off
            dx, dy = px - cx, py - cy
            lx = dx * ct + dy * st; ly = -dx * st + dy * ct
            if (lx / rx) ** 2 + (ly / ry) ** 2 <= 0.9:
                setc(int(round(px)), int(round(py)), "\u2591", DEEP)

veins(MID - 12, 18, 13, 7, math.radians(-38))   # upper forewing veins
veins(MID - 9, 30, 9, 5, math.radians(-18))     # lower hindwing veins

# ===========================================================================
# MIRROR: reflect the painted left half onto the right down the spine. THIS is the roll's
#   required primitive -- one wedge of logic, reflected into bilateral symmetry.
# ===========================================================================
C.mirror(cv, axis='v')

# --- SPINE SEAM: paint the centerline full-width so it reads as a solid lit seam, not a gap.
for y in range(13, 52):
    Lv = L(MID, y)
    ch, fg = wshade(Lv, BODY, HOT)
    setc(MID, y, ch, fg)

# ===========================================================================
# emit -- title card + sig block (house standard), standalone reset tail.
# ===========================================================================
out = []

def center(text, fg):
    pad = max(0, W - len(text)); l = pad // 2; r = pad - l
    return C.sgr(12) + " " * l + C.sgr(fg) + text + C.sgr(12) + " " * r

out.append(C.sgr(13) + "\u2550" * W)
out.append(center("MANTIS", 15))
out.append(center("// a creature, mirrored down the spine //", 9))
out.append(C.sgr(13) + "\u2550" * W)
out.append("")

cv.render(out)

out.append("")
C.sig_block(out, "MANTIS // mirrored creature", handles="raze")

C.write_ans("scratch/_mantis.ans", out, add_sig=False)
print("wrote scratch/_mantis.ans rows:", len(out))
