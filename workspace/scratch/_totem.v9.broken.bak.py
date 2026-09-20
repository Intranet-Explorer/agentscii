#!/usr/bin/env python3
# TOTEM // "the mask that watches back" -- raze solo. AGENTSCI figurative register.
#
# PROVENANCE: random_direction roll -> subject "a robot/cyborg head", technique
#    "canvas.mirror() for bilateral symmetry", palette "monochrome + one accent". Took the
#   TECHNIQUE (mirror) + PALETTE LEAN (mono grey + single amber) straight; REJECTED the literal
#   cyborg-head subject -- COGHEAD / CYBORGS-SCOPE / CYCLOPS already shipped it. The move that's
#   genuinely new is a CONSTRUCTED ceremonial mask built as a true left-half then mirror(axis='v').
#
# v8 REJECTED by curator (hollis) + blind visual check: read as a symmetric FLAT-BAR silhouette --
#   horizontal white rectangles stacked into an inverted teardrop, NOT modeled 3D stone. Root cause
#   diagnosed here: the old light was RADIAL DISTANCE from a point source, so across a wide form every
#   cell at similar distance got the SAME glyph -> concentric rings = horizontal bands = flat bars.
#
# v9 FIX (path A -- commit to the lit-3D-stone ambition): two changes.
#   (1) Switch from radial-distance light to N.L shading -- each surface's density tracks its OUTWARD
#       NORMAL dotted with a fixed light DIRECTION (upper-left), not its distance from a point. That
#       makes the dome read as rounded, the brow as a ridge catching light on top / falling into the
#       socket below, the cheekbones as raised planes, the jaw as a tapering recessed plane -- real
#       surfaces, not stacked bars.
#   (2) Build geometry symmetrically (left-half then mirror), but apply the N.L light AFTER mirroring,
#       across the WHOLE form. A directional upper-left light copied by mirror() would make the right
#       side a lit duplicate of the left and the half-lit split couldn't read -- so symmetry is
#       structural (geometry defined once) while lighting stays directional: left faces the light and
#       peaks white, right turns away and falls to grey. A genuine light-vs-shadow fall across the axis.

import sys, math
sys.path.insert(0, "scratch")
from canvas import Canvas, RAMP, mirror, texture_fill, write_ans, hygiene_gate, sig_block

W = 80
H = 46
MID = W // 2                             # 40 -- vertical axis of symmetry
ACCENT = 11                              # bright amber -- the ONE accent color (eyes only)

# ---- single light DIRECTION (upper-left), not a point source ----------------
LX, LY = -0.86, -0.5                    # unit vector pointing up-and-to-the-left
_n = math.hypot(LX, LY); LX /= _n; LY /= _n

cv = Canvas(w=W, h=H, fill_ch=' ', fill_fg=0, fill_bg=0)


def shade(L, base_fg=8, hot_fg=15, ramp=RAMP, white_at=0.97):
     """Map a light value 0..1 -> (glyph, fg). Density AND brightness both track the light so a lit
    surface is bright+full and a shadowed one dim+thin -- this is what turns flat block shapes into
    gradient-built form."""
    L = max(0.0, min(1.0, L))
    idx = int(L * (len(ramp) - 1) + 0.5) % len(ramp)
    fg = hot_fg if L > white_at else base_fg
    return ramp[idx], fg


def nl(cx, cy, rx, ry, x, y, amb=0.10):
     """N.L diffuse light on a convex surface centered (cx,cy), radii (rx,ry). The outward normal at
    a cell is the normalized position vector from the surface center; dot it with the fixed light
    DIRECTION. Density tracks SURFACE ORIENTATION, not distance -- the fix for flat bars."""
    nx = (x - cx) / rx
    ny = (y - cy) / ry
    r = math.hypot(nx, ny)
    if r < 1e-6:
        n = (0.0, 0.0)
    else:
        n = (nx / r, ny / r)
    d = n[0] * LX + n[1] * LY            # -1..1
    L = 0.5 * (d + 1.0)                 # remap to 0..1
    return max(amb, min(1.0, L))


# ---- Pass 3a: build the mask GEOMETRY symmetrically (left half -> mirror) ---
def cranium_hw(y):
     """Upper skull: a rounded dome, centered high so it reads as a cranium, not a bar."""
    cy, ry = 16.0, 12.0
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return None
    return 24.0 * math.sqrt(1.0 - t * t)


def jaw_hw(y):
     """Lower face tapering to the chin -- a narrowing plane, not a flat bar."""
    top, tip = 26.0, 43.0
    if y < top or y > tip:
        return None
    frac = (y - top) / (tip - top)
    return 15.0 * (1.0 - frac) ** 1.1


def in_mask(x, y):
    hw = cranium_hw(y)
    if hw is not None and abs(x - MID) <= hw:
        return True
    hw2 = jaw_hw(y)
    if hw2 is not None and abs(x - MID) <= hw2:
        return True
    return False


# paint the LEFT half only, then mirror -- true structural symmetry
for y in range(H):
    for x in range(MID):
        if in_mask(x, y):
            cv.set(x, y, '\u2588', 7, 0)
mirror(cv, axis='v')


# ---- Pass 3b: N.L shading across the WHOLE form (light stays directional) ---
def paint(region_fn, cx, cy, rx, ry, base_fg=8, hot_fg=15, amb=0.10, white_at=0.97):
    for y in range(H):
        for x in range(W):
            if region_fn(x, y):
                ch, fg = shade(nl(cx, cy, rx, ry, x, y, amb), base_fg, hot_fg, white_at=white_at)
                cv.set(x, y, ch, fg, 0)


# cranium dome -- the big rounded top; peaks white on its upper-left quadrant
paint(lambda x, y: in_mask(x, y) and cranium_hw(y) is not None,
      MID, 14.0, 26.0, 13.0, base_fg=8, hot_fg=15, amb=0.10, white_at=0.95)

# brow shelf -- a horizontal ridge; top edge catches light, falls into the socket below
def brow(x, y):
    if not (13 <= y <= 15):
        return False
    hw = cranium_hw(y)
    return hw is not None and abs(x - MID) <= hw

paint(brow, MID, 14.0, 24.0, 3.0, base_fg=7, hot_fg=15, amb=0.12, white_at=0.94)

# cheekbone -- a raised plane below the brow; stays in grey mid-tones (only true peaks go white)
def cheek(x, y):
    if not (16 <= y <= 24):
        return False
    cx = MID - 10.0; cy = 20.0
    dL = (x - cx) ** 2 / 9.0 + (y - cy) ** 2 / 16.0
    dR = (x - (W - 1 - cx)) ** 2 / 9.0 + (y - cy) ** 2 / 16.0
    return min(dL, dR) <= 1.0

paint(cheek, MID, 20.0, 3.0, 4.0, base_fg=8, hot_fg=15, amb=0.10, white_at=0.98)

# jaw -- a tapering recessed plane under the cheek; darker, falls off toward the chin
paint(lambda x, y: in_mask(x, y) and cranium_hw(y) is None,
      MID, 32.0, 15.0, 9.0, base_fg=7, hot_fg=14, amb=0.08, white_at=0.99)


# ---- Pass 4: the accent (constructed eyes) + a crown finial -----------------
def eye_socket(x, y):
    ex = MID - 8                        # ~32 on the left; mirror gives ~47 on the right
    ey = 21.0                          # cheek band, BELOW the brow shelf so they read as focal
    dL = (x - ex) ** 2 + (y - ey) ** 2
    dR = (x - (W - 1 - ex)) ** 2 + (y - ey) ** 2
    return min(dL, dR) <= 2.6

for y in range(H):
    for x in range(W):
        if eye_socket(x, y):
            cv.set(x, y, '\u2588', ACCENT, 0)       # amber glow -- the single accent
# a tiny white glint at each eye's light-side edge (the "watches back" catch-light)
for sx in (MID - 8, MID + 8):
    cv.set(int(sx) - 1, 20, '\u2588', 15, 0)

# crown finial: a small spike on top of the skull, lit from the left
for y in range(3, 7):
    for x in range(MID - (7 - y), MID + (7 - y)):
        if abs(x - MID) <= (6 - y):
            ch, fg = shade(nl(MID, 5.0, 6.0, 4.0, x, y, amb=0.12), base_fg=8, hot_fg=15, white_at=0.97)
            cv.set(x, y, ch, fg, 0)


# ---- Pass 5: negative-space texture (rising mist, not flat black) ----------
def void_region(x, y):
    return not in_mask(x, y) and not cheek(x, y)

texture_fill(cv, void_region, fg=8, density=0.16, seed=3)


# ---- Pass 6: frame + title treatment ---------------------------------------
RULE = "\u2550"

def put_centered(text, y, fg):
    for x in range(W):
        cv.set(x, y, ' ', 0, 0)
    pad = W - len(text)
    left = pad // 2
    for i, ch in enumerate(text):
        cv.set(left + i, y, ch, fg, 0)

for x in range(W):
    cv.set(x, 0, RULE, 12, 0); cv.set(x, H - 1, RULE, 12, 0)
for y in range(H):
    cv.set(0, y, RULE, 12, 0); cv.set(W - 1, y, RULE, 12, 0)

put_centered("TOTEM", 1, 15)
put_centered("// the mask that watches back //", 2, 8)

out = []
cv.render(out)
sig_block(out, "TOTEM v9.0 (N.L stone half-lit)", handles="raze")
raw = "\n".join(out) + "\x1b[0m\n"
with open('_totem.ans', 'w', encoding='cp437') as fh:
    fh.write(raw)
hygiene_gate('_totem.ans')
print("PASS 6 written -- N.L stone half-lit")
