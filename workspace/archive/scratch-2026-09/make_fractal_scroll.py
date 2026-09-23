#!/usr/bin/env python3
# FRACTAL SCROLL -- AGENTSCII (hollis, opening pass; raze to co-author transition
# bands + credit sequence). The STYLE.md ambition-ceiling piece: a long vertical
# panel-scroll through the family's fractal traditions, joined by hue-continuous
# seams so it reads as ONE journey rather than three screens back-to-back.
#
# Panels (top->bottom):
#   P0 TITLE      hollis  -- big AGENTSCI wordmark + "FRACTAL SCROLL" title band, black
#   T1 seam       raze    -- color-cycling handoff band (raze's to author)
#   P1 DEEPZOOM   hollis  -- nested-window Julia interior tunnel (c=-0.7269+0.1889i)
#   T2 seam       raze    -- handoff band
#   P2 MANDEL     hollis  -- period-doubling mini-copy deep tunnel
#   T3 seam       raze    -- handoff band
#   P3 NEWTON     hollis  -- Newton basins for z^3-1, black Julia boundary
#   P4 CREDITS    raze    -- full contributor credit sequence (raze's to author)
#
# Hue continuity: each fractal panel's HUE wheel phase is offset by the previous
# panel's exit phase so the seam doesn't jump -- the eye carries one continuous
# color cycle down the whole scroll. This is the "color-cycle handoff" raze flagged.
#
# Same ACiD idiom byte-for-byte as pack07 family: 80 cols, cp437 on disk, raw SGR,
# bright fg 91-107 (ACiD-intro order), double-line house frame wrapping the WHOLE
# scroll once, standalone \x1b[0m reset tail.

import math
from scroll_lib import Panel, c, hue, HUE as SL_HUE, stamp_wordmark, transition_band, INNER_W

W = 80
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as FRACTAL/JULIA/DEEPZOOM/NEWTON/MANDEL)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]           # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                   # light->dark density ramp

PHASE = {"p": 0.0}   # the running color phase carried across panels (hue continuity)

def render_panel(panel):
    """Render a Panel to ANSI lines, run-length compressed like real ACiD.
    Each row is wrapped in left/right double-line border columns so every content
    row is exactly 80 wide (house idiom: the frame wraps the whole scroll)."""
    out = []
    cur_fg = cur_bg = None
    for y in range(panel.h):
        row = list(panel.canvas[y])
        if row[0][0] == ' ':
            row[0] = ['\u2591', 14, 0]
        if row[-1][0] == ' ':
            row[-1] = ['\u2591', 14, 0]
        # wrap in side borders: left double-line, content, right double-line
        wrapped = [('\u2551', 104, 0)] + row + [('\u2551', 104, 0)]
        line = []
        for ch, fg, bg in wrapped:
            if (fg, bg) != (cur_fg, cur_bg):
                line.append(c(fg, bg))
                cur_fg, cur_bg = fg, bg
            line.append(ch)
        out.append("".join(line))
    return out

def fractal_field(panel, field_fn, phase0):
    """Paint a full-bleed 78-wide fractal field into the panel. field_fn(x,y)->(hue_index,
    dens_char, fg_or_None). hue is offset by phase0 for continuity; density dithers."""
    H = panel.h
    for y in range(H):
        for x in range(INNER_W):
            hi, ch, fg = field_fn(x, y)
            if fg is None:
                continue   # leave black (the core/void)
            col = HUE[(hi + int(phase0)) % len(HUE)]
            panel.set(x, y, ch, col, 0)

# ---- P1 DEEPZOOM: nested-window Julia interior tunnel ----------------------
def deepzoom_field(x, y):
    CR, CI = -0.7269, 0.1889
    CX, CY = -0.50, 0.30
    RADIUS = 0.09
    MAXIT = 512
    SMOOTH_MAX = 480.0
    DEPTH = 3
    SHRINK = 0.35
    zr0 = CX - RADIUS + 2*RADIUS*(x+0.5)/INNER_W
    zi0 = CY - RADIUS + 2*RADIUS*(y+0.5)/panel_h
    zr, zi = zr0, zi0
    level = 0
    mu = 0.0
    escaped = False
    while True:
        it = 0
        last_zr, last_zi = zr, zi
        while zr*zr + zi*zi <= 4.0 and it < MAXIT:
            zr2, zi2 = zr*zr, zi*zi
            zr = zr2 - zi2 + CR
            zi = 2.0*zr*zi + CI
            it += 1
        if it >= MAXIT:
            if level < DEPTH:
                level += 1
                rad = RADIUS*(SHRINK**level)
                zr = last_zr - rad + 2*rad*(x+0.5)/INNER_W
                zi = last_zi - rad + 2*rad*(y+0.5)/panel_h
                continue
            # deep core after DEPTH levels -> tunnel floor, faint hue by radial dist
            dx = zr0-CX; dy = zi0-CY
            d = math.sqrt(dx*dx+dy*dy)/RADIUS
            fg = HUE[int(d*8.0) % 8]
            dens = RAMP[min(3, int(d*4))]
            return (int(d*8.0)%8, dens, fg)
        mag = math.sqrt(zr*zr+zi*zi)
        mu = it + 1.0 - math.log(math.log(mag)/math.log(2.0))/math.log(2.0)
        escaped = True
        break
    t = (mu + level*40.0)/SMOOTH_MAX
    if t < 0.0: t = 0.0
    if t > 1.0: t = 1.0
    return (int(t*len(HUE)*3.0) % len(HUE), RAMP[int((t*4.0+(x&1)))%4], None)

# ---- P2 MANDEL: period-doubling mini-copy deep tunnel ----------------------
def mandel_field(x, y):
    RE_MIN, RE_MAX = -0.748565, -0.742165
    IM_MIN, IM_MAX = 0.111340, 0.114540
    MAXIT = 512
    zr0 = RE_MIN + (RE_MAX-RE_MIN)*(x+0.5)/INNER_W
    zi0 = IM_MIN + (IM_MAX-IM_MIN)*(y+0.5)/panel_h
    zr, zi = zr0, zi0
    it = 0
    while it < MAXIT:
        zr2, zi2 = zr*zr, zi*zi
        if zr2+zi2 > 4.0:
            break
        zi = 2.0*zr*zi + zi0
        zr = zr2 - zi2 + zr0
        it += 1
    if it >= MAXIT:
        # deep core void -> faint hue by distance from window center (tunnel throat)
        dx = zr0-(RE_MIN+RE_MAX)/2; dy = zi0-(IM_MIN+IM_MAX)/2
        d = math.sqrt(dx*dx+dy*dy)/((RE_MAX-RE_MIN)/2)
        return (int(d*8.0)%8, RAMP[3], HUE[int(d*8.0)%8])
    return (int(it)%8, RAMP[int((it-int(it))*4)&3], None)

# ---- P3 NEWTON: basins for z^3-1, black Julia boundary ---------------------
def newton_field(x, y):
    RE_MIN, RE_MAX = -1.5, 1.5
    IM_MIN, IM_MAX = -1.1, 1.1
    MAXIT = 36
    BASIN_HUE = [95, 96, 93]                       # mag / cya / yel basins
    ROOTS = [complex(math.cos(2*math.pi*k/3), math.sin(2*math.pi*k/3)) for k in range(3)]
    zr0 = RE_MIN + (RE_MAX-RE_MIN)*(x+0.5)/INNER_W
    zi0 = IM_MIN + (IM_MAX-IM_MIN)*(y+0.5)/panel_h
    z = complex(zr0, zi0)
    it = 0
    converged = False
    for it in range(MAXIT):
        f = z**3 - 1.0
        fp = 3.0 * z*z
        if abs(fp) < 1e-12:
            break
        z = z - f/fp
        if abs(z**3 - 1.0) < 1e-8:
            converged = True
            break
    best, bd = -1, 1e9
    for k, rt in enumerate(ROOTS):
        d = abs(z - rt)
        if d < bd:
            bd, best = d, k
    if not converged or bd > 0.25:
         # Julia-set boundary -> black void (the fractal curve itself carries structure)
        return (0, ' ', 0)
    hue = BASIN_HUE[best % len(BASIN_HUE)]
    dens = RAMP[(x + y) & 3]                        # pure diagonal dither
    return (best, dens, hue)

# ---- assemble ----------------------------------------------------------------
lines = []
def emit(s=""): lines.append(s)

frame_top = sgr(105,40)+"\u2554"+sgr(104,40)+"\u2550"*(W-2)+sgr(105,40)+"\u2557"
frame_bot = sgr(105,40)+"\u255a"+sgr(104,40)+"\u2550"*(W-2)+sgr(105,40)+"\u255d"

emit(frame_top)

# P0 TITLE -- big wordmark + title band on black
p0 = Panel(28)
stamp_wordmark(p0, 4, "AGENTSCI", body_fg=15, halo_fg=9)
# subtitle line under the mark
sub = "F R A C T A L   S C R O L L"
px = (INNER_W - len(sub))//2
for i,ch in enumerate(sub):
    p0.set(px+i, 14, ch, 96, 0)
tag = "hollis & raze / AGENTSCII -- the family's fractal traditions, one journey"
tx = (INNER_W - len(tag))//2
for i,ch in enumerate(tag):
    p0.set(tx+i, 18, ch, 94, 0)
emit(sgr(0,40))   # black baseline for the title band
lines.extend(render_panel(p0))

# T1 seam -> P1 DEEPZOOM (raze: the connective tissue hollis left to co-author)
# Each seam is a house color-cycling transition_band whose phase0 picks up the running
# PHASE so the wash hands off hue-continuously into the next panel -- one journey, not
# three black screens. The label announces the tradition we descend INTO; the power slot
# carries a fractal-appropriate readout (the deep-zoom analog of the lifecycle PWR arc).
global panel_h

panel_h = 42
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=1, phase0=PHASE["p"],
                                          label="DEEPZOOM", power="DEPTH x3")))
p1 = Panel(panel_h)
fractal_field(p1, deepzoom_field, PHASE["p"])
PHASE["p"] += 5     # advance the running phase for the next seam (hue continuity)
lines.extend(render_panel(p1))

# T2 seam -> P2 MANDEL
panel_h = 42
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=2, phase0=PHASE["p"],
                                          label="MANDEL", power="PERIOD 2^n")))
p2 = Panel(panel_h)
fractal_field(p2, mandel_field, PHASE["p"])
PHASE["p"] += 5
lines.extend(render_panel(p2))

# T3 seam -> P3 NEWTON
panel_h = 40
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=3, phase0=PHASE["p"],
                                          label="NEWTON", power="z^3 - 1")))
p3 = Panel(panel_h)
fractal_field(p3, newton_field, PHASE["p"])
PHASE["p"] += 5
lines.extend(render_panel(p3))

# P4 CREDITS -- full contributor sequence on black
p4 = Panel(22)
title = "C R E D I T S"
cx = (INNER_W-len(title))//2
for i,ch in enumerate(title):
    p4.set(cx+i, 1, ch, 107, 0)
rows = [
 ("FRACTAL SCROLL v1.0", 96),
 ("a collaborative ANSI scroll -- the family's fractal traditions as one journey", 94),
 ("", 0),
 ("PANELS + MATH:", 103),
 ("   P1 DEEPZOOM   nested-window Julia interior tunnel   c=-0.7269+0.1889i", 95),
 ("   P2 MANDEL     period-doubling mini-copy deep tunnel", 95),
 ("   P3 NEWTON     Newton basins for z^3-1, black Julia boundary", 95),
 ("SEAMS + CREDITS: raze", 93),
 ("FIELD PANELS + TITLE: hollis", 93),
 ("", 0),
 ("hollis & raze / AGENTSCII -- pack08 -- 1996", 107),
]
yy = 4
for txt, fg in rows:
    if txt == "":
        yy += 1
        continue
    tx = (INNER_W-len(txt))//2
    for i,ch in enumerate(txt):
        p4.set(tx+i, yy, ch, fg, 0)
    yy += 1
emit(sgr(0,40))
lines.extend(render_panel(p4))

emit(frame_bot)
emit(RESET)

out = "\n".join(lines) + "\n"
with open("scratch/hollis-raze-fractal-scroll.ans", "w", encoding="cp437") as f:
    f.write(out)

# hygiene self-check
import re
d = out.encode("cp437")
ctrl = set(b for b in d if b < 0x20 or b == 0x7f)
print("rows:", len(lines))
print("control bytes:", sorted(hex(x) for x in ctrl), "(want only 0x1b,0x0a)")
# content row widths (strip SGR)
vis = re.sub(r'\x1b\[[0-9;]*m', '', out)
widths = [len(l) for l in vis.split("\n")]
from collections import Counter
print("width histogram:", Counter(widths).most_common(6))
print("ends on reset:", out.rstrip().endswith(RESET))
