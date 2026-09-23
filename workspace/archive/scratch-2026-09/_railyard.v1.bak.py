#!/usr/bin/env python3
# raze -- RAIL YARD // AGENTSCI  (solo, dim/muted register)
#
# PROVENANCE: built from a random_direction roll ->
#   subject "a rail yard or industrial scene", technique constraint
#   "use canvas.py's flood_fill() to define large background/negative-space
#   regions", palette lean "muted/dim, low-saturation throughout".
#
# WHY THIS PIECE: the recent house streak has been LOUD -- saturated phosphor
# (AFTERIMAGE), molten warm fields (FORGE / MOLTEN MARK). This is the deliberate
# counterweight: a single-screen industrial landscape in the DIM register, one
# point of warm life against an otherwise low-saturation field. Distinct from
# REFINERY (an oil refinery over water) -- this is a freight yard at dusk: boxcars
# + a tank car on a gravel track bed under catenary wires, receding to the left.
#
# TECHNIQUE: flood_fill() defines the two large negative-space regions -- SKY and
# GROUND -- by seeding each and letting the 4-connected fill stop at real
# boundaries (the horizon line, the car silhouettes). The cars are placed as solid
# placeholders first so the sky fill carves cleanly around them; then each region
# gets a vertical gradient dithered on top of its flat flood base. This is the
# "define large regions by flood" technique the roll asked for, not a hand-painted
# per-cell field.

import sys
sys.path.insert(0, "scratch")
from canvas import Canvas, sgr, RAMP, write_ans, flood_fill, line

W = 80
H = 42
ESC = "\x1b["

# ---- dim / muted palette (low saturation throughout) -----------------------
SKY_TOP      = 4       # dim blue upper sky
SKY_MID      = 4       # dim blue mid-sky (held flat, very low contrast)
SKY_LOW      = 7       # medium gray horizon haze -- the only warm-ish break
GROUND       = 0       # near-black earth base (dimmest)
GRAVEL       = 7       # medium-gray ballast band along the rail (reads as gravel)
STEEL        = 4       # boxcar body -- dim blue-steel, NOT bright white
STEEL_DK     = 0       # shadow side / underbelly / bogies (black)
ROOF         = 7       # roof cap highlight -- medium gray, one row only
WIRE         = 4       # catenary, dim steel-blue
SIGNAL       = 11      # the single warm accent -- BRIGHT amber signal light (only life)

cv = Canvas(W, H, fill_ch=' ', fill_fg=7, fill_bg=0)


# ---------------------------------------------------------------------------
# STEP 1 -- place the cars as solid placeholders so flood_fill carves around them.
# Each car is a small self-contained block: body + roof cap + bogies (wheels).
# They sit on the track bed; the horizon runs just below their base.
# ---------------------------------------------------------------------------
HORIZON = 27            # sky above, ground below
TRACK_Y = HORIZON - 1   # rail line / car base

def place_boxcar(x0, w, body_h, fg=STEEL):
    """A freight boxcar: solid body, a slightly lighter roof cap, two bogies."""
    top = TRACK_Y - body_h
    for y in range(top, TRACK_Y):
        for x in range(x0, x0 + w):
            cv.set(x, y, '\u2588', fg, 0)
    # roof cap (one row lighter, overhangs by 1 on each side)
    for x in range(x0 - 1, x0 + w + 1):
        cv.set(x, top, '\u2588', ROOF, 0)
    # a vertical seam / door line mid-body
    mid = x0 + w // 2
    for y in range(top + 1, TRACK_Y - 1):
        cv.set(mid, y, '\u2593', STEEL_DK, 0)
    # bogies (wheels) under the body -- two dark clusters
    for bx in (x0 + 1, x0 + w - 2):
        cv.set(bx, TRACK_Y, '\u2588', STEEL_DK, 0)
        cv.set(bx + 1, TRACK_Y, '\u2588', STEEL_DK, 0)
    return (x0, top, w, body_h)

def place_tankcar(x0, w, body_h):
    """A tank car: rounded profile -- flat middle band with tapered ends."""
    top = TRACK_Y - body_h
    for y in range(top + 1, TRACK_Y):
        # taper the first/last two columns to read as a cylinder end
        inset = 0
        if y == top + 1 or y == TRACK_Y - 1:
            inset = 2
        elif y == top + 2 or y == TRACK_Y - 2:
            inset = 1
        for x in range(x0 + inset, x0 + w - inset):
            cv.set(x, y, '\u2588', STEEL, 0)
    # rounded top/bottom caps
    for x in range(x0 + 2, x0 + w - 2):
        cv.set(x, top, '\u2588', ROOF, 0)
        cv.set(x, TRACK_Y, '\u2588', STEEL_DK, 0)
    # a faint horizontal band line (tank seam)
    mid = top + body_h // 2
    for x in range(x0 + 1, x0 + w - 1):
        cv.set(x, mid, '\u2593', STEEL_DK, 0)
    return (x0, top, w, body_h)

# Three boxcars receding to the left (smaller/higher = farther), one tank car.
place_boxcar(48, 16, 7, fg=STEEL)        # nearest, right
place_boxcar(28, 13, 6, fg=STEEL_DK)     # mid, slightly dimmer (farther)
place_boxcar(10, 10, 5, fg=STEEL_DK)     # farthest, smallest + dimmest
place_tankcar(64, 12, 7)                  # tank car, far right

# ---------------------------------------------------------------------------
# STEP 2 -- flood_fill defines the two large negative-space regions.
# Seed the SKY from top-left: it fills down to the horizon AND stops at every
# car silhouette already placed (the fill matches the original cell key and won't
# cross into a car body). Then seed GROUND from below the horizon.
# ---------------------------------------------------------------------------
cv.set(0, 0, ' ', SKY_TOP, 0)            # seed marker for sky
flood_fill(cv, 0, 0, ch=' ', fg=SKY_TOP, bg=0)   # whole upper field -> sky base

# ground: fill from just below the horizon across the bottom
cv.set(0, HORIZON + 1, ' ', GROUND, 0)
flood_fill(cv, 0, HORIZON + 1, ch=' ', fg=GROUND, bg=0)

# ---------------------------------------------------------------------------
# STEP 3 -- vertical gradient dither over each flat flood base. The flood gave us
# the REGION; now we shade it so it reads as a real dusk field, not a flat block.
# Sky: dim blue-gray up top -> warm gray haze at the horizon.
# Ground: earth tone with a faint gravel band along the track bed.
# ---------------------------------------------------------------------------
def is_bg(ch):
    return ch in (' ', '\u2591', '\u2592', '\u2593')

# sky: dim blue up top -> warm gray haze at the horizon (vertical density).
# GUARD on glyph, not fg -- STEEL(8) collides with SKY_MID(8), so we must never
# re-shade a placed block glyph or it erases the car silhouettes.
for y in range(0, HORIZON):
    d = y / max(1, HORIZON - 1)            # 0 at top -> 1 at horizon
    fg = SKY_TOP if d < 0.45 else (SKY_MID if d < 0.8 else SKY_LOW)
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        newch = '\u2591' if (y % 3 == 0 and d > 0.6) else ' '
        cv.set(x, y, newch, fg, 0)

# ground: earth with a gravel ballast band hugging the track bed
for y in range(HORIZON + 1, H):
    d = (y - HORIZON) / max(1, H - HORIZON - 1)
    for x in range(W):
        ch = cv.get(x, y)[0]
        if not is_bg(ch):
            continue
        newch = ' '
        fg = GROUND
        if abs(y - TRACK_Y) <= 2:            # gravel band around the rail
            newch = '\u2592' if ((x + y) % 2 == 0) else '\u2591'
            fg = GRAVEL
        elif d > 0.6:                        # darker foreground earth
            newch = '\u2591' if (y % 2 == 0) else ' '
        cv.set(x, y, newch, fg, 0)

# ---------------------------------------------------------------------------
# STEP 4 -- catenary wires overhead + the single warm signal light.
# Wires: faint diagonal lines from a mast down to the cars. Signal: one amber
# point of life on a post at the right edge -- the only saturated cell in the field.
# ---------------------------------------------------------------------------
# two catenary masts, wires strung between them and out past the cars
line(cv, 6, 4, 6, TRACK_Y - 8, ch='\u2502', fg=WIRE)     # mast A (far left)
line(cv, 70, 3, 70, TRACK_Y - 9, ch='\u2502', fg=WIRE)   # mast B (right)
line(cv, 6, 5, 70, 4, ch='\u2500', fg=WIRE)              # top wire
line(cv, 6, 8, 70, 7, ch='\u2500', fg=WIRE)              # lower catenary
# droppers (short verticals from wire to rail zone)
for x in range(14, 66, 8):
    line(cv, x, 5, x, 9, ch='\u2502', fg=SKY_MID)

# signal light: a short post at far right with one amber lamp -- the single accent
line(cv, 76, TRACK_Y - 10, 76, TRACK_Y, ch='\u2502', fg=STEEL_DK)
cv.set(76, TRACK_Y - 11, '\u2588', SIGNAL, 0)            # the lamp
# a faint glow halo around it (dim amber, one ring)
for dx in (-1, 1):
    for dy in (-1, 0, 1):
        if cv.in_bounds(76 + dx, TRACK_Y - 11 + dy):
            c = cv.get(76 + dx, TRACK_Y - 11 + dy)
            if c[1] != SIGNAL:
                cv.set(76 + dx, TRACK_Y - 11 + dy, '\u2591', 3, 0)

# ---------------------------------------------------------------------------
# STEP 4b -- the track recedes toward us: two faint converging rails + ballast in
# the foreground, so the lower void reads as depth (a yard stretching toward the
# viewer) not dead space. Dim throughout -- this is still the muted register.
# ---------------------------------------------------------------------------
VP_X = W // 2                       # vanishing point on the horizon, center
for y in range(TRACK_Y + 1, H):
    t = (y - TRACK_Y) / max(1, H - TRACK_Y - 1)   # 0 at track bed -> 1 at bottom
    spread = int(t * 34)            # rails fan out toward the viewer
    for rx in (VP_X - spread, VP_X + spread):
        if cv.in_bounds(rx, y):
            ch = '\u2593' if t < 0.5 else '\u2588'   # dimmer far, fuller near
            cv.set(rx, y, ch, GRAVEL if t > 0.4 else STEEL_DK, 0)
    # faint ballast speckle between the rails, denser toward the viewer
    for x in range(VP_X - spread, VP_X + spread):
        if (x + y) % 3 == 0 and t > 0.35:
            cv.set(x, y, '\u2591', STEEL_DK, 0)

# ---------------------------------------------------------------------------
# STEP 5 -- render to SGR rows.
# ---------------------------------------------------------------------------
out = []
for y in range(H):
    row = []
    cur_fg = None
    for x in range(W):
        ch, fg, bg = cv.get(x, y)
        if fg != cur_fg:
            row.append(sgr(fg, bg))
            cur_fg = fg
        row.append(ch)
    out.append(''.join(row))

write_ans("scratch/_railyard.ans", out, title="RAIL YARD // dusk freight", handles="raze / AGENTSCI")
