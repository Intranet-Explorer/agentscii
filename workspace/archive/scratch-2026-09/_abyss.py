#!/usr/bin/env python3
# ABYSS // "an eye that was not made to see" -- raze solo, AGENTSCI scroll register.
# random_direction roll (taken straight): subject "an eye embedded in something inhuman",
# technique = build it as a scroll_lib.py panel sequence (multiple linked panels, not one
# static screen), palette lean = cool tones (blues/cyans/greens) dominant.
#
# Through-line motif (the connective tissue STYLE.md asks for, analog of LIFECYCLE's PWR arc):
# a DEPTH readout -- the scroll descends, depth increases panel to panel, and the eye is found
# at the bottom of it. Cool palette throughout: cyan/blue/green/teal dominant; magenta reserved
# as a single rare accent (the eye's glint), never in the field washes.
#
# Built in passes (METHODOLOGY): P1 flat silhouettes -> verify by eye -> P2 shade from ONE
# upper-left source -> P3 directional detail + constructed eye anatomy -> P4 texture the
# negative space -> P5 frame (automatic via assemble) -> verify page-by-page.
import math, sys
sys.path.insert(0, "scratch")
from scroll_lib import Panel, c, hue, stamp_wordmark, write_scroll, INNER_W, CX

# ---- cool-dominant wheel: cyan/blue/green/teal ONLY. No magenta/red/yellow in the body
# washes -- that's what makes it read "cool" not "full ACiD rainbow". Magenta = rare accent. ----
COOL = [6, 4, 2, 10, 9]                  # cyan, blue, green, bright-cyan, bright-green
def cool(phase):
    return COOL[int(phase) % len(COOL)]

# house palette handles (normal 0-7 / bright 8-15; c() maps them)
CY = 6; BL = 4; GR = 2; TE = 9; WH = 15; MG = 5; AM = 3; DK = 0

# ---- cool-only transition band (house transition_band cycles the FULL HUE wheel; we override
# so the connective tissue stays in-palette for this piece). DEPTH readout on the bottom edge.
def cool_transition(height=8, index=None, label=None, power=None):
    p = Panel(height)
    for y in range(height):
        for x in range(INNER_W):
            ph = x * 0.16 + y * 0.5
            col = cool(ph)
            m = (x * 2 + y * 3) % 4
            ch = '█' if m < 2 else ('▓' if m == 2 else '▒')
            p.set(x, y, ch, col, 0)
    if index is not None:
        tag = "SCROLL // %02d" % index
        for i, ch in enumerate(tag):
            p.set(1 + i, height // 2, ch, WH, 4)
    if label:
        lx = INNER_W - len(label) - 1
        for i, ch in enumerate(label):
            p.set(lx + i, height // 2, ch, WH, 4)
    if power is not None:
        pw = "DEPTH // %s" % power
        px = (INNER_W - len(pw)) // 2
        for i, ch in enumerate(pw):
            p.set(px + i, height - 1, ch, WH, 4)
    return p

# ===========================================================================
# PANEL 0 -- TITLE: wordmark + subtitle over a deep abyssal gradient field.
# Cool, darker toward the bottom (the descent begins here). Textured, not flat black.
# ===========================================================================
def make_title():
    H = 30
    p = Panel(H)
    for y in range(H):
        depth = y / float(H)                       # 0 at top -> 1 at bottom
        for x in range(INNER_W):
            ph = x * 0.20 + y * 0.14
            col = cool(ph)
            m = (x * 3 + y * 5) % 4
            ch = '█' if m < 2 else ('▓' if m == 2 else '▒')
             # dim the lower third so it reads as "going down into the dark"
            fg = col if depth < 0.6 else (BL if depth < 0.85 else DK)
            p.set(x, y, ch, fg, 0)
     # black interior band for the wordmark (LOGO treatment)
    for y in range(6, 15):
        for x in range(CX - 34, CX + 34):
            p.set(x, y, ' ', 0, 0)
    stamp_wordmark(p, 8, "AGENTSCI", body_fg=WH, halo_fg=TE)
    p.put_text(17, CX - len("A B Y S S") // 2, "A B Y S S", CY)
    p.put_text(19, CX - len("// an eye that was not made to see //") // 2,
               "// an eye that was not made to see //", TE)
    for x in range(6, INNER_W - 6):
        p.set(x, 22, '═', cool(x * 0.4 + 1.0))
    p.put_text(27, 1, "SCROLL // 00 -- SURFACE", WH, 4)
    p.put_text(27, INNER_W - len("raze / AGENTSCI") - 1, "raze / AGENTSCI", TE, 4)
    return p

# ===========================================================================
# PANEL 1 -- DESCENT: a dark cool sea; faint ripples; the eye far below as a glint.
# ===========================================================================
def make_descent():
    H = 40
    p = Panel(H)
     # abyssal water field, cool gradient deepening downward + sparse particulate texture
    for y in range(H):
        depth = y / float(H)
        base = CY if depth < 0.35 else (BL if depth < 0.7 else DK)
        for x in range(INNER_W):
            m = (x * 7 + y * 3) % 9
            ch = ' ' if m < 6 else ('░' if m == 6 else '▒')
            p.set(x, y, ch, base, 0)
     # faint horizontal ripple lines (cool), spaced -- the "surface" feel near the top
    for ry in range(3, H - 4, 5):
        for x in range(INNER_W):
            wob = int(round(math.sin((x + ry * 2) * 0.18)))
            yy = ry + wob
            if 0 <= yy < H:
                p.set(x, yy, '─', TE if (x + ry) % 3 else CY, 0)
     # the eye far below: a single small glint near the bottom center -- "something is down there"
    ex, ey = CX, H - 6
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            d = math.sqrt(dx * dx + (dy * 1.6) ** 2)
            if d < 1.0:
                p.set(ex, ey, '█', WH, 0)
            elif d < 2.2:
                p.set(ex + dx, ey + dy, '▒', CY, 0)
    p.put_text(1, CX - len("D E S C E N T") // 2, "D E S C E N T", TE)
    p.put_text(H - 1, 1, "SCROLL // 01 -- DESCENT", WH, 4)
    p.put_text(H - 1, INNER_W - len("DEPTH 040m") - 1, "DEPTH 040m", TE, 4)
    return p

# ===========================================================================
# PANEL 2 -- THE EYE: the focal panel. A large constructed eye embedded in an INHUMAN
# crystalline/gill mask (asymmetric radiating plates), lit upper-left, cool-toned.
# P1 flat silhouette -> P2 shade from ONE upper-left source -> P3 anatomy + detail ->
# P4 texture the void around it.
# ===========================================================================
def make_eye():
    H = 46
    p = Panel(H)
    EX, EY = CX, 21                         # eye center (focal point of the whole scroll)
    LX, LY = EX - 18, EY - 14              # single light source, upper-left

      # ---- P1: flat inhuman mask silhouette (irregular crystalline mass, asymmetric) ----
    def in_mask(x, y):
        dx = x - EX; dy = y - EY
        r = math.sqrt(dx * dx + dy * dy)
        ang = math.atan2(dy, dx)
           # irregular radius: 3-fold crystalline asymmetry -- not a human face
        # deliberate crystalline facets: quantize the angle into 8 sectors so the
        # silhouette reads as intentional faceted plates, not random radius jitter;
        # one gentle low-order wobble keeps it asymmetric/inhuman but structured.
        sector = int((ang % (math.pi * 2)) / (math.pi * 2) * 8.0)
        facet = 14.5 + 2.6 * math.cos(sector * (math.pi / 4.0))
        rad = facet + 1.6 * math.sin(ang * 2 + 0.3)
        return r < rad

       # ---- P2: shade the mask from ONE upper-left source (density ramp, cool hue by light) ----
    for y in range(H):
        for x in range(INNER_W):
            if not in_mask(x, y):
                continue
            ldx = x - LX; ldy = y - LY
            ld = math.sqrt(ldx * ldx + ldy * ldy) / 34.0
            lit = max(0.0, min(1.0, 1.0 - ld))
               # cool hue shifts by light: teal on the lit side, deep blue in shadow
            col = TE if lit > 0.55 else (CY if lit > 0.3 else BL)
            ch = '█' if lit > 0.7 else ('▓' if lit > 0.4 else ('▒' if lit > 0.18 else '░'))
            p.set(x, y, ch, col, 0)

       # ---- P3a: gill/plate ridges -- directional strokes radiating from the eye (strand feel).
       # STOP at the eye's almond so they frame it instead of clobbering it. ----
    EYE_RX, EYE_RY = 12.0, 4.6              # horizontal almond -- wide enough to read as THE eye
    def in_almond(x, y):
        dx = x - EX; dy = y - EY
        return (dx / EYE_RX) ** 2 + (dy / EYE_RY) ** 2
    for k in range(16):
        ang = k * (math.pi * 2 / 16.0) + 0.15
        for t in range(7, 13):
            x = int(round(EX + math.cos(ang) * t))
            y = int(round(EY + math.sin(ang) * t * 0.92))
            if 0 <= x < INNER_W and 0 <= y < H and in_mask(x, y) and in_almond(x, y) >= 1.3:
                # dim the ridges so they frame the eye without competing for focus:
                # cool near the socket, falling off to deep blue + lighter block outward.
                col = BL if t > 10 else (CY if t > 8 else TE)
                p.set(x, y, '▓' if t > 10 else '█', col, 0)

       # ---- P4: texture the void AROUND the mask (cool particulate, not flat black) ----
    for y in range(H):
        for x in range(INNER_W):
            if p.canvas[y][x][0] != ' ':
                continue
            m = (x * 5 + y * 7) % 11
            if m == 0:
                p.set(x, y, '░', DK, 0)
            elif m == 3:
                p.set(x, y, '·', BL, 0)

       # ---- P3b: the eye itself -- drawn LAST so it sits on top of everything (the focal point).
       # socket well -> white sclera -> cyan iris ring -> carved pupil -> glint. Lit upper-left.
       # The single rare magenta accent in the whole piece lives on the glint. ----
       # socket well: a dark carved rim just outside the almond (reads as "set into" the mask)
    for y in range(H):
        for x in range(INNER_W):
            v = in_almond(x, y)
            if 1.0 <= v < 1.45:
                p.set(x, y, '░', DK, 0)
       # sclera (white), iris ring (cyan), pupil (carved void), lit upper-left
    for y in range(H):
        for x in range(INNER_W):
            v = in_almond(x, y)
            if v >= 1.0:
                continue
            dx = x - EX; dy = y - EY
            r = math.sqrt(dx * dx + dy * dy)
            ldx = x - LX; ldy = y - LY
            lit = max(0.0, min(1.0, 1.0 - math.sqrt(ldx * ldx + ldy * ldy) / 34.0))
            if r < 2.6:
                p.set(x, y, ' ', 0, 0)                   # pupil void (carved out of the sclera)
            elif r < 5.6:
                col = WH if lit > 0.6 else CY            # iris ring: bright cyan, white on lit side
                p.set(x, y, '█', col, 0)
            else:
                p.set(x, y, '▓', TE if lit > 0.4 else BL)     # sclera body, shaded by light
       # glint: white highlight upper-left of the iris + the single rare magenta accent lower-right
    p.set(EX - 3, EY - 1, '█', WH, 0)
    p.set(EX + 3, EY + 1, '█', MG, 0)

    p.put_text(1, CX - len("T H E   E Y E") // 2, "T H E   E Y E", CY)
    p.put_text(H - 1, 1, "SCROLL // 02 -- THE EYE", WH, 4)
    p.put_text(H - 1, INNER_W - len("DEPTH 700m") - 1, "DEPTH 700m", TE, 4)
    return p

# ===========================================================================
# PANEL 3 -- CREDIT / the eye closes: a dimming cool field + closing card.
# ===========================================================================
def make_credit():
    H = 26
    p = Panel(H)
    for y in range(H):
        depth = y / float(H)
        for x in range(INNER_W):
            ph = x * 0.2 + y * 0.15
            m = (x * 3 + y * 5) % 4
            ch = '▒' if m < 2 else ('░' if m == 2 else ' ')
            col = cool(ph) if depth < 0.7 else DK
            p.set(x, y, ch, col, 0)
     # closing card band
    for y in range(8, 16):
        for x in range(CX - 30, CX + 30):
            p.set(x, y, ' ', 0, 0)
    p.put_text(9, CX - len("ABYSS // END OF DESCENT") // 2, "ABYSS // END OF DESCENT", CY)
    p.put_text(11, CX - len("the eye was not made to see. it sees anyway.") // 2,
               "the eye was not made to see. it sees anyway.", TE)
    p.put_text(13, CX - len("raze / AGENTSCI") // 2, "raze / AGENTSCI", WH)
    p.put_text(H - 1, 1, "SCROLL // 03 -- ABYSS", WH, 4)
    p.put_text(H - 1, INNER_W - len("DEPTH 999m") - 1, "DEPTH 999m", TE, 4)
    return p

# ---- assemble the journey: panels joined by cool transition bands w/ DEPTH motif ----
panels = [make_title()]
panels.append(cool_transition(8, index=0, label="ABYSS", power="010m"))
panels.append(make_descent())
panels.append(cool_transition(8, index=1, label="DESCENT", power="250m"))
panels.append(make_eye())
panels.append(cool_transition(8, index=2, label="THE EYE", power="700m"))
panels.append(make_credit())

n = write_scroll("scratch/_abyss.ans", panels)
print("wrote scratch/_abyss.ans -- %d lines" % n)
