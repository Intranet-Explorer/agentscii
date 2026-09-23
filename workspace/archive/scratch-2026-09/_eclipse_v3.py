#!/usr/bin/env python3
# ECLIPSE v3 -- "object + object". raze, solo. AGENTSCII.
# Extends SOLSTICE's "sun as a constructed object" idiom into the unexplored
# axis hollis named after pack46: OCCULTATION -- two objects, not one. A dark
# lunar disc occulting a shaded sun-sphere; the corona spills around its limb
# and a diamond-ring of white-hot light escapes at the edge. Warm palette only;
# ZERO green/cyan/blue (coherent with SOLSTICE).
#
# v3 REBUILD -- answers hollis's v1 rejection critique AND Tyler's flat-band gap:
#   The v2 corona interior still read as stacked HORIZONTAL bars (coral row, grey
#   row, white row) -- the same flat-band central read that got TOTEM/ECLIPSE
#   rejected. v3 fixes it with the NEW house tools instead of hand-rolled math:
#    (1) photoreal_gradient() -> a MULTI-HUE radial spectrum across the corona
#        annulus (white-hot core -> yellow -> amber -> red -> magenta fringe),
#        not single-hue density. This is the "painterly photo" read, not flat
#        color-with-shading.
#    (2) streak_field() -> dense VERTICAL flame-streak texture over the corona,
#        breaking any residual horizontal banding the way TOTEM v10's grain did,
#        but with genuine per-column raggedness instead of a smooth gradient.
#    (3) bevel_text() -> chrome 3D "ECLIPSE" wordmark (lit top / amber body / red
#        underside), replacing the hand-rolled GLYPHS dict (one of the 9 Tyler
#        flagged as duplicated).
#   Kept from v2 (it was right): the MOON as a coherent CLOSED near-black
#   silhouette that fully occults the sun (contrast = the "two objects" read),
#   and the DIAMOND-RING as a thin fg15 arc hugging only the LIT limb.
import math, random
import figure_common as fc
import canvas as cv_mod

W, H = 80, 64
RAMP = "\u2588\u2593\u2592\u2591"

CANVAS = cv_mod.Canvas(W, H)
cv = CANVAS.cells     # figure_common wants a bare list; canvas.py fns want the Canvas. Same [[ch,fg,bg]] cells.

# warm hue ramp by heat t in [0,1]: 0=cool magenta fringe, 1=white-hot core
def heat_fg(t):
    if t >= 0.93: return 15        # white hot
    if t >= 0.80: return 11        # bright yellow
    if t >= 0.62: return 3         # yellow
    if t >= 0.44: return 9         # bright red / amber
    if t >= 0.26: return 1         # red
    return 5                       # magenta fringe

LX, LY = -0.55, -0.75              # light direction (upper-left), same as SOLSTICE
Ln = math.hypot(LX, LY); LX/=Ln; LY/=Ln

# geometry: the MOON is concentric with the SUN and slightly larger, so it FULLY
# occults the sun's disc -- a total eclipse. The corona is an annular glow that
# peaks at the moon's limb; the centre (the moon) stays dark.
SUN_CX, SUN_CY = 40, 36
MOON_CX, MOON_CY = 40, 36
MOON_R = 18

def in_moon(x, y):
    return math.hypot(x-MOON_CX, y-MOON_CY) <= MOON_R

# ---- PASS 1: frame + corner flourishes (kept from v2 -- it was right) ----
def pass1():
    for x in range(W):
        fc.set_cell(cv, x, 0, "\u2554", 3); fc.set_cell(cv, x, H-1, "\u2557", 3)
        fc.set_cell(cv, x, 1, "\u2550", 3); fc.set_cell(cv, x, H-2, "\u2550", 3)
    for y in range(H):
        fc.set_cell(cv, 0, y, "\u2551", 3); fc.set_cell(cv, W-1, y, "\u2551", 3)
    for (ox, oy, sx, sy) in [(3,3,1,1),(W-4,3,-1,1),(3,H-4,1,-1),(W-4,H-4,-1,-1)]:
        for (px,py) in [(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(1,3),(0,3)]:
            fc.set_cell(cv, ox+sx*px, oy+sy*py, "\u2588", 9)

# ---- PASS 2: the CORONA as a MULTI-HUE SPECTRUM (NEW: photoreal_gradient).
# Brightest white-hot at the moon's limb, walking through yellow->amber->red to a
# magenta fringe. This replaces v2's stepped single-hue density ramp -- the gap
# Tyler named. Region = the annulus just outside the moon out to the fringe; the
# centre is left for the moon (pass 4) so it pops by contrast.
def pass2():
    ring_r = MOON_R + 1
    outer  = MOON_R + 16
    def corona(x, y):
        if y < 13: return False          # keep the top title band dark void
        d = math.hypot(x-SUN_CX, y-SUN_CY)
        return (d > ring_r - 0.5) and (d < outer)
    # hue_stops walk CENTER->EDGE: white-hot core -> yellow -> amber -> red -> magenta
    fc.photoreal_gradient(cv, corona, SUN_CX, SUN_CY, [15, 11, 3, 9, 1, 5],
                          max_dist=outer)

# ---- PASS 2b: VERTICAL FLAME STREAKS over the corona (NEW: streak_field).
# Per-column ragged vertical runs -- this is what breaks any residual horizontal
# banding. Hot at the base, cooling to magenta at the tip. Kept inside the annulus
# so it doesn't bleed into the moon's dark centre or the void.
def pass2b():
    ring_r = MOON_R + 1
    outer  = MOON_R + 16
    def corona(x, y):
        if y < 13: return False          # keep the top title band dark void
        d = math.hypot(x-SUN_CX, y-SUN_CY)
        return (d > ring_r - 0.5) and (d < outer)
    cv_mod.streak_field(CANVAS, corona, fg_ramp=[11, 3, 9, 1, 5], ch="\u2588",
                        density=0.45, min_len=3, max_len=12, seed=7)

# ---- PASS 3: radiating CORONA RAYS -- long light streaks occluded by the moon.
def pass3():
    n_rays = 56
    for i in range(n_rays):
        ang = (i / n_rays) * 2*math.pi + 0.02
        dx, dy = math.cos(ang), math.sin(ang)
        primary = (i % 3 == 0)
        length = MOON_R + (16 if primary else 8)
        for s in range(MOON_R+1, length):
            x = int(round(SUN_CX + dx*s)); y = int(round(SUN_CY + dy*s))
            if in_moon(x, y): continue             # the moon occults the corona behind it
            f = 1.0 - (s-MOON_R)/length
            if f <= 0: continue
            fg = heat_fg(f*0.85 + 0.12)
            ch = "\u2588" if s < MOON_R+4 else RAMP[1]
            fc.set_cell(cv, x, y, ch, fg)

# ---- PASS 4: the MOON -- a coherent CLOSED near-black silhouette IN FRONT of the
# corona. Fully occults the sun (moon_r > sun_r, concentric). Faint earthshine on
# its lit upper-left limb keeps it reading as a modeled body, not a flat hole.
def pass4():
    for y in range(MOON_CY-MOON_R-1, MOON_CY+MOON_R+2):
        for x in range(MOON_CX-MOON_R-1, MOON_CX+MOON_R+2):
            dx = (x-MOON_CX)/MOON_R; dy = (y-MOON_CY)/MOON_R
            d = math.hypot(dx, dy)
            if d <= 1.0:
                nx, ny = dx, dy
                nz = math.sqrt(max(0.0, 1.0 - dx*dx - dy*dy))
                dot = nx*LX + ny*LY + nz*0.40
                dot = max(-1.0, min(1.0, dot))
                t = (dot + 1.0)/2.0 * 0.30              # dim: the moon is in shadow
                if d > 0.96:        ch = RAMP[3]        # faint outer limb
                elif d > 0.85:      ch = RAMP[2]
                else:               ch = "\u2588"
                s = math.sin(x*1.7 + 0.3) * math.cos(y*1.3 - 0.5)
                fg = 7 if s > 0.55 else 0               # near-black body, faint grain
                fc.set_cell(cv, x, y, ch, fg)

# ---- PASS 5: the DIAMOND-RING -- a THIN white-hot arc hugging the LIT limb only.
def pass5():
    for y in range(MOON_CY-MOON_R-2, MOON_CY+MOON_R+3):
        for x in range(MOON_CX-MOON_R-2, MOON_CX+MOON_R+3):
            dx = (x-MOON_CX)/MOON_R; dy = (y-MOON_CY)/MOON_R
            d = math.hypot(dx, dy)
            if 1.0 <= d <= 1.12:                   # thin arc just outside the limb
                nx, ny = dx, dy
                nz = math.sqrt(max(0.0, 1.0 - min(dx*dx+dy*dy,1.0)))
                dot = nx*LX + ny*LY + nz*0.40      # bright only where light reaches
                if dot > 0.35:                    # lit crescent only -> a ring, not a swath
                    fc.set_cell(cv, x, y, "\u2588", 15)

# ---- PASS 6: negative-space texture -- sparse warm embers in the void (kept clear
# of both halos so the two objects stay legible). ----
def pass6():
    rng = random.Random(11)
    for _ in range(130):
        x = rng.randint(2, W-3); y = rng.randint(16, H-3)
        if cv[y][x][0] != " ": continue
        ds = math.hypot(x-SUN_CX, y-SUN_CY)
        dm = math.hypot(x-MOON_CX, y-MOON_CY)
        if ds < 30 or dm < 21: continue             # keep the corona field clean
        fg = heat_fg(rng.random()*0.5 + 0.1)
        fc.set_cell(cv, x, y, rng.choice(["\u2588","\u2593","\u2592"]), fg)

# ---- PASS 7: chrome wordmark (NEW: bevel_text) + tagline + credit band.
# Replaces the hand-rolled GLYPHS dict with the shared 44-glyph title font,
# beveled lit-top / amber-body / red-underside like real ACiD chrome lettering.
def pass7():
    word = "ECLIPSE"
    w = cv_mod.text_width(word, scale=1)
    x0 = (W - w)//2; y0 = 5
     # dark outline behind the letters so the chrome bevel reads over the bright corona:
     # paint a 1-cell black halo where each glyph cell would land, then bevel on top.
    def _outline():
        for li, ch in enumerate(word):
            g = cv_mod.GLYPHS_5x7.get(ch.upper(), cv_mod.GLYPHS_5x7[' '])
            gx = x0 + li*(5*2+1)
            for ri, row in enumerate(g):
                for ci, cell in enumerate(row):
                    if cell != '#': continue
                    for sy in range(2):
                        for sx in range(2):
                            px, py = gx+ci*2+sx, y0+ri*2+sy
                            for dxo in (-1,0,1):
                                for dyo in (-1,0,1):
                                    if dxo==0 and dyo==0: continue
                                    fc.set_cell(cv, px+dxo, py+dyo, "█", 0)
    _outline()
    # per-row bevel: top rows lit white/yellow, body amber, underside red
    def bevel_color(ri, ci):
        if ri == 0: return 15          # lit top edge
        if ri >= 6: return 1           # shadowed underside
        return 3                       # amber body
    cv_mod.bevel_text(CANVAS, word, x0, y0, top_fg=15, mid_fg=3, bottom_fg=1,
                      ch="█", scale=1)
    cred = "raze / AGENTSCII / ECLIPSE v3.0"
    cxp = (W - len(cred))//2
    for i, c in enumerate(cred):
        fc.set_cell(cv, cxp+i, H-4, c, 9 if i%3==0 else 3)
    for x in range(6, W-6):
        fc.set_cell(cv, x, H-5, "\u2500", 1)

for fn in (pass1, pass2, pass2b, pass3, pass4, pass5, pass6, pass7):
    fn()

# ---- RENDER -> ANSI, cp437 on disk ----
out = []
CANVAS.render(out)
data = "\n".join(out) + "\x1b[0m\n"
with open("scratch/_eclipse_v3.ans", "wb") as f:
    f.write(data.encode("cp437"))
print("wrote scratch/_eclipse_v3.ans")
