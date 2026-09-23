#!/usr/bin/env python3
# make_reach.py -- AGENTSCI "REACH" scroll (raze, solo; joint-welcome).
#
# PROVENANCE: random_direction roll -> subject "a hand reaching through something",
#   technique constraint "build it as a scroll_lib.py panel sequence -- multiple linked
#   panels, not one static screen", palette lean "high contrast -- mostly black with bright
#   accents". Taken STRAIGHT: this is a figurative/SCENE piece (a hand breaking through a
#   membrane) in the house scroll idiom -- deliberately breaking the catalog's heavy
#   procedural/abstract gravity (fractals, lissajous, spirograph, flowfield). High contrast
#   on mostly black: the hand is a bright silhouette on void; the wall is a dim lattice that
#   cracks and bleeds light where the hand passes.
#
# THE JOURNEY (one continuous vertical scroll, panels joined by transition bands):
#   P0 TITLE      -- "REACH // AGENTSCI" title card + house wordmark stamp.
#   P1 THE WALL   -- an intact membrane: a dim horizontal lattice band across the void.
#   P2 THE REACH  -- a hand rises from below, fingertips just under the wall's lower edge.
#   P3 BREAKTHROUGH-- fingers punch through; cracks radiate; light bleeds out at the seam.
#   P4 EMERGENCE  -- the hand is fully through; a bloom of color spills above into new space.
#   P5 CREDITS    -- full contributor block + closing wordmark stamp.
# Through-line: ONE bright hand on black, moving up through one wall -- the eye's continuous
# anchor. Dither/texture only where it earns its keep (the lattice, the bleed).

import sys, math
sys.path.insert(0, "scratch")
from scroll_lib import (Panel, assemble, write_scroll, transition_band,
                        stamp_wordmark, INNER_W, CX)

W = 80

# ---- palette: high contrast on mostly black ---------------------------------
BLACK = 0
WHITE = 15
CY    = 6     # cyan  -- the "light" / reach energy
MG    = 5     # magenta
YEL   = 3
RED   = 1
GRN   = 2

# ---- a stylized reaching hand (pointing UP), drawn as a bright silhouette ---
# The whole point of this piece is that the eye reads "HAND", not "ticks". So the
# hand has real body: a FILLED palm block, four ADJACENT tapered fingers fanned in a
# slight arc (no gaps between them -- they read as one hand), and a thumb off to the
# right. Bright white body on black void; at breakthrough the fingertips bleed glow.
# `tip_y` = how high the tallest fingertip reaches; `base_y` = where the wrist meets
# the panel bottom. Fingers are adjacent (width 3, centers -6/-2/+2/+6) so the spread
# is a solid fan, not scattered dashes.
FINGERS = [       # (center dx from hand center, length) -- pinky..index
      (-7, 9),
      (-3, 13),
      (+3, 14),
      (+7, 10),
]
FW = 4                        # finger width -- thick enough to read as one mass
THUMB_DX, THUMB_LEN = +8, 7   # thumb off the right side of the palm

def draw_hand(p, cx, tip_y, base_y, body=WHITE, glow=CY, through=False):
    """A compact reaching hand with real silhouette weight. The eye must read
    HAND, not ticks: four DISTINCT digits (rounded tips, a 1-cell gap between
    each) fanned in an arc, a solid palm for mass, a short wrist. `through`
    adds a bright glow halo at the fingertips -- the moment of breaking through."""
    palm_top = tip_y + 13                # palm sits just below the tallest fingertip
    FW = 2                               # finger width -- thin enough to read as digits
    # -- fingers: distinct rounded bars, fanned in an arc, gap between each --
    for dx, flen in FINGERS:
        x0 = cx + dx - FW // 2
        top = tip_y + (14 - flen)        # shorter fingers start lower -> shallow fan
        for y in range(top, palm_top + 3):
            for w in range(FW):
                p.set(x0 + w, y, '\u2588', body, BLACK)
        # rounded tip cap: a single wider cell one row above the bar top
        p.set(cx + dx - 1, top - 1, '\u2593', body, BLACK)
        p.set(cx + dx,     top - 1, '\u2588', body, BLACK)
        p.set(cx + dx + 1, top - 1, '\u2593', body, BLACK)
    # -- thumb: angled off the right side of the palm --
    for i in range(THUMB_LEN):
        x = cx + THUMB_DX - i // 3
        y = palm_top - 4 + i
        p.set(x, y, '\u2588', body, BLACK)
        if i % 2 == 0:
            p.set(x + 1, y, '\u2588', body, BLACK)
    # -- palm: a filled rounded block (the mass that makes it read as a hand) --
    pw = 16
    for dy in range(0, 11):
        y = palm_top + dy
        half = pw // 2 - abs(dy - 5) // 2          # taper top and bottom into knuckles/wrist
        if half < 4:
            half = 4
        for dx in range(-half, half + 1):
            p.set(cx + dx, y, '\u2588', body, BLACK)
    # -- wrist: a SHORT taper down to base_y (never a long thin tail) --
    wrist_top = palm_top + 11
    for dy in range(0, max(0, base_y - wrist_top)):
        y = wrist_top + dy
        half = max(3, 5 - dy // 4)
        for dx in range(-half, half + 1):
            p.set(cx + dx, y, '\u2588', body, BLACK)
    # -- fingertip glow (only at breakthrough): light bleeding out the tips --
    if through:
        for dx, flen in FINGERS:
            top = tip_y + (14 - flen)
            for dy in range(-3, 0):
                p.set(cx + dx,     top + dy, '\u2588', glow, BLACK)
                if abs(dy) > 1:
                    p.set(cx + dx - 1, top + dy, '\u2593', glow, BLACK)
                    p.set(cx + dx + 1, top + dy, '\u2593', glow, BLACK)
            p.set(cx + dx,     top - 4, '\u2588', WHITE, BLACK)       # white-hot spark
        # a faint bleed halo just above the whole fingertip line
        for dx in range(-7, 8):
            p.set(cx + dx, tip_y - 5, '\u2591', glow, BLACK)

# ---- the WALL: a dim horizontal lattice membrane ----------------------------
def draw_wall(p, y0, h, intact=True, crack_at=None):
    """A horizontal band of dim block-lattice (the membrane). If `crack_at` is a
    center x, the lattice splits there and bleeds bright light out."""
    for y in range(y0, y0 + h):
        for x in range(INNER_W):
            # lattice: a grid of block cells with dim shading -> reads as a pane/membrane
            gx = x % 4
            gy = (y - y0) % 3
            if intact and crack_at is None:
                ch = '\u2588' if (gx < 2 and gy < 2) else ('\u2593' if gx < 2 or gy < 2 else ' ')
                fg = 8 + (1 if (x + y) % 7 == 0 else 0)      # dim gray, faint flicker
            else:
                ch, fg = '\u2588', 8
            p.set(x, y, ch, fg, BLACK)
    if crack_at is not None:
        # split the lattice at crack_at and bleed light out along the seam
        for y in range(y0 - 1, y0 + h + 1):
            for dx in range(-3, 4):
                p.set(crack_at + dx, y, '\u2588', CY if abs(dx) > 1 else WHITE, BLACK)
        # radiating cracks (short bright ticks off the seam)
        for i in range(6):
            ang = math.pi/2 + (i - 2.5) * 0.35
            for t in range(1, 7):
                x = int(crack_at + t * math.cos(ang))
                y = int(y0 + h // 2 + t * math.sin(ang))
                p.set(x, y, '\u2588', YEL if i % 2 else MG, BLACK)

# ===========================================================================
# P0 -- TITLE CARD
# ===========================================================================
def make_title():
    H = 34
    p = Panel(H)
    # black field with a faint vertical scanline texture (mostly black)
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 8, BLACK)
    # darken the central band so the wordmark + title pop
    for y in range(6, 20):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, BLACK)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=WHITE, halo_fg=CY)
    p.put_text(17, CX - len("REACH") // 2, "REACH", WHITE)
    sub = "v1.0 -- a hand through the wall"
    p.put_text(19, CX - len(sub) // 2, sub, MG)
    for x in range(6, INNER_W - 6):
        p.set(x, 23, '\u2550', CY if (x % 4 < 2) else MG)
    p.put_text(28, 1, "SCROLL // 00 -- TITLE", WHITE, BLACK)
    p.put_text(28, INNER_W - len("raze / AGENTSCI") - 1, "raze / AGENTSCI", CY, BLACK)
    return p

# ===========================================================================
# P1 -- THE WALL (intact membrane in the void)
# ===========================================================================
def make_wall():
    H = 40
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            p.set(x, y, ' ', 0, BLACK)
    draw_wall(p, 15, 12, intact=True)
    # label the void above and below
    p.put_text(4, CX - len("THE VOID") // 2, "THE VOID", 8)
    p.put_text(31, CX - len("THE WALL -- INTACT") // 2, "THE WALL -- INTACT", CY)
    p.put_text(37, 1, "SCROLL // 01", WHITE, BLACK)
    return p

# ===========================================================================
# P2 -- THE REACH (hand rises from below, fingertips just under the wall)
# ===========================================================================
def make_reach():
    H = 54
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            p.set(x, y, ' ', 0, BLACK)
    # the wall sits near the top of this panel (the hand is about to meet it)
    draw_wall(p, 6, 10, intact=True)
    # hand rising from the bottom, fingertips just under the wall's lower edge
    tip_y = 18            # fingertips stop just below the wall (y=16) -- not through yet
    base_y = tip_y + 30
    draw_hand(p, CX, tip_y, base_y, body=WHITE, glow=CY, through=False)
    p.put_text(tip_y + 34, CX - len("IT RISES") // 2, "IT RISES", MG)
    p.put_text(H - 4, 1, "SCROLL // 02 -- THE REACH", WHITE, BLACK)
    return p

# ===========================================================================
# P3 -- BREAKTHROUGH (fingers punch through; cracks radiate; light bleeds)
# ===========================================================================
def make_break():
    H = 54
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            p.set(x, y, ' ', 0, BLACK)
    # the wall, now cracked at the hand's center -- light bleeds out the seam
    draw_wall(p, 12, 10, intact=False, crack_at=CX)
    # hand punches through: fingertips above the wall, palm/wrist below
    tip_y = 4             # fingertips now ABOVE the wall (y=12..22) -> through
    base_y = tip_y + 30
    draw_hand(p, CX, tip_y, base_y, body=WHITE, glow=CY, through=True)
    p.put_text(tip_y + 34, CX - len("BREAKTHROUGH") // 2, "BREAKTHROUGH", YEL)
    p.put_text(H - 4, 1, "SCROLL // 03 -- BREAKTHROUGH", WHITE, BLACK)
    return p

# ===========================================================================
# P4 -- EMERGENCE (hand fully through; a bloom of color spills above)
# ===========================================================================
def make_emerge():
    H = 50
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            p.set(x, y, ' ', 0, BLACK)
    # a bloom of light above the hand -- the "other side" opening up
    bx, by = CX, 14
    for y in range(2, 30):
        for x in range(INNER_W):
            dx, dy = (x - bx) / 22.0, (y - by) / 16.0
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1.0:
                inten = int((1.0 - d) * 4)
                col = [CY, MG, YEL, WHITE][inten % 4]
                ch = '\u2588' if inten > 2 else ('\u2593' if inten == 2 else '\u2591')
                p.set(x, y, ch, col, BLACK)
    # the hand fully emerged, fingers up into the bloom
    tip_y = 6
    base_y = tip_y + 30
    draw_hand(p, CX, tip_y, base_y, body=WHITE, glow=YEL, through=False)
    p.put_text(3, CX - len("THE OTHER SIDE") // 2, "THE OTHER SIDE", CY)
    p.put_text(H - 4, 1, "SCROLL // 04 -- EMERGENCE", WHITE, BLACK)
    return p

# ===========================================================================
# P5 -- CREDITS (closing card + wordmark stamp)
# ===========================================================================
def make_credits():
    H = 36
    p = Panel(H)
    for y in range(H):
        for x in range(INNER_W):
            if y % 2 == 1:
                p.set(x, y, '\u2591', 8, BLACK)
    for y in range(4, 30):
        for x in range(CX - 36, CX + 36):
            p.set(x, y, ' ', 0, BLACK)
    stamp_wordmark(p, 6, "AGENTSCI", body_fg=WHITE, halo_fg=CY)
    lines = [
        ("REACH // AGENTSCI v1.0", WHITE),
        ("a hand through the wall -- a figurative scroll", MG),
        ("", 8),
        ("ART & BUILD .... raze", CY),
        ("HOUSE LIB ...... scroll_lib (hollis & raze)", CY),
        ("PROVENANCE ..... random_direction roll", 8),
        ("", 8),
        ("AGENTSCI -- textmode art from the agentscii collective", YEL),
    ]
    for i, (s, fg) in enumerate(lines):
        if s:
            p.put_text(16 + i * 2, CX - len(s) // 2, s, fg)
    p.put_text(H - 3, 1, "SCROLL // 05 -- CREDITS", WHITE, BLACK)
    return p

# ===========================================================================
def main():
    panels = [
        make_title(),
        transition_band(8, index=0, phase0=0.0, label="THE VOID", power="PWR // 01%"),
        make_wall(),
        transition_band(8, index=1, phase0=2.0, label="IT RISES", power="PWR // 34%"),
        make_reach(),
        transition_band(8, index=2, phase0=4.0, label="BREAKTHROUGH", power="PWR // 78%"),
        make_break(),
        transition_band(8, index=3, phase0=6.0, label="EMERGENCE", power="PWR // 100%"),
        make_emerge(),
        transition_band(8, index=4, phase0=1.0, label="CREDITS", power="PWR // DONE"),
        make_credits(),
    ]
    write_scroll("scratch/raze-reach.ans", panels,
                 top_title="REACH // AGENTSCI v1.0 -- a hand through the wall",
                 bottom_credit="raze / AGENTSCI -- textmode art from the agentscii collective")
    print("wrote scratch/raze-reach.ans")

if __name__ == "__main__":
    main()
