#!/usr/bin/env python3
# COSMIC SCROLL v2 -- AGENTSCII (raze). Ambition-ceiling scroll, COSMIC / DEEP-SPACE.
#
# v1 was REJECTED on two concrete, fixable points (see raze-cosmic-scroll.ans.critique.txt):
#   1) P1 "THE FIELD" inverted its own brief -- it rendered as a dense saturated yellow/red
#      mass instead of the sparse COOL void establishing shot it claims to be. A far view is
#      mostly empty space; that's what makes P2/P3 read as descent INTO something.
#   2) P3 "IGNITION" (the climax) read as a fragmented ragged pile with a disconnected floating
#      bar, not an ignition event -- 7 protostars scattered by RNG over a broken fbm body don't
#      cohere into one hot core.
#
# v2 FIXES (both in cosmic_field, both thermal/density-math, concept untouched):
#   P1: threshold raised to ~0.58, dens dropped to ~0.40 so most of the panel stays black;
#       only faint cool wisps + a sparse starfield survive. Reads as void.
#   P3: ONE coherent dense core (tighter env falloff, higher dens so the body is solid) with
#       3 protostar ignition cores EMBEDDED inside that mass (white-hot center -> amber shell ->
#       red glow), placed on a tight ring around the core center, not scattered in a box. The
#       disconnected-bar signature is killed: glint bounds + arm-envelope overlap are checked so
#       nothing falls outside the core envelope. P3 is now the brightest, most coherent moment.
#   P2 APPROACH (the strongest v1 panel) is kept as-is -- it's the target P1/P3 each approach.
#
# Journey (top->bottom): a continuous DESCENT into one star-forming region.
#   P0 TITLE / T1 seam / P1 THE FIELD / T2 seam / P2 APPROACH / T3 seam / P3 IGNITION /
#   T4 seam / P4 CREDITS.  Carries hollis's cool->warm DEPTH read into new ground: distant
#   panels sit COOL, P3's protostars are explicitly HOT -- the warm climax, not a recolor.

import math, random, sys
sys.path.insert(0, "scratch")
from scroll_lib import Panel, c, hue, HUE as SL_HUE, stamp_wordmark, transition_band, INNER_W

W = 80
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

RAMP = "\u2588\u2593\u2592\u2591"                  # light->dark density ramp

PHASE = {"p": 0.0}      # the running color phase carried across panels (hue continuity)

# temperature ramp: cool end (distant/faint) -> hot end (ignition).
TEMP = [94, 96, 92, 95, 91, 103, 107]             # blu cya grn mag red amb wht

# ---------------------------------------------------------------------------
# value noise (cheap 2D fbm) for filamentary cloud structure.
# ---------------------------------------------------------------------------
def _noise_grid(seed):
    g = {}
    r = random.Random(seed)
    for i in range(400):
        for j in range(400):
            g[(i, j)] = r.random()
    return g
NG1 = _noise_grid(0xC05C)
NG2 = _noise_grid(0x5B1A)

def vnoise(x, y, grid):
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    def lerp(a, b, t): return a + (b - a) * (t * t * (3 - 2 * t))     # smoothstep
    top = lerp(grid[(x0, y0)], grid[(x0 + 1, y0)], fx)
    bot = lerp(grid[(x0, y0 + 1)], grid[(x0 + 1, y0 + 1)], fx)
    return lerp(top, bot, fy)

def fbm(x, y):
    return 0.6 * vnoise(x, y, NG1) + 0.4 * vnoise(x * 2.3, y * 2.3, NG2)

# ---------------------------------------------------------------------------
# deterministic starfield -- sparse intentional constellation placement, NOT noise.
# glint cross is bounded so it can never fall outside the panel (kills the "disconnected bar").
# ---------------------------------------------------------------------------
def make_stars(seed, count, glint_prob=0.18):
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        cx = rng.randint(2, INNER_W - 3)
        cy = rng.randint(1, 999)              # row is panel-relative; clamp at use time
        b = rng.choice([0, 0, 0, 1, 1, 2, 3])
        glint = (b == 3 and rng.random() < glint_prob)
        out.append((cx, cy, b, glint))
    return out

# ---------------------------------------------------------------------------
# a cosmic FIELD panel: full-bleed nebula cloud at a given zoom + temperature, with a
# sparse starfield on top. THRESHOLD keeps the field sparse/wispy; TEMP places the panel
# at its thermal point in the descent. core_rx/core_ry control how tight the body is --
# P1 wants a wide faint wisp, P3 wants one TIGHT coherent core.
# ---------------------------------------------------------------------------
def env(dx, dy, rx, ry):
    d = math.hypot(dx / rx, dy / ry)          # quadratic radial falloff -> falls to void
    if d >= 1.0:
        return 0.0
    return (1.0 - d * d)

def cosmic_field(panel, phase0, zoom, dens, temp, threshold, protostars=False,
                 core_rx=0.34, core_ry=0.42, arm_scale=0.85):
    H = panel.h

    CORE_CX, CORE_CY = INNER_W * 0.42, H * 0.50
    ARM_CX, ARM_CY   = INNER_W * 0.68, H * 0.64

    # starfield (panel-relative rows). For P1 we want FEW stars; for P3 a denser field.
    stars = make_stars(int(phase0 * 131 + 7), int(28 + dens * 30), glint_prob=0.22)
    for (sx, sy, sb, sg) in stars:
        if not (0 <= sy < H):
            continue
        if sb == 0:
            continue
        col = [96, 94, 107, 103][min(3, sb)]       # cya->blu->wht->amb by brightness
        panel.set(sx, sy, "\u2588", col, 0)
        if sg:
            for dx in (-1, 1):                       # cross glint -- BOUNDED to the panel
                if 0 <= sx + dx < INNER_W:
                    panel.set(sx + dx, sy, "\u2593", 96, 0)
            for dy in (-1, 1):
                if 0 <= sy + dy < H:
                    panel.set(sx, sy + dy, "\u2593", 96, 0)

    for y in range(H):
        for x in range(INNER_W):
            dc = env(x - CORE_CX, y - CORE_CY, INNER_W * core_rx, H * core_ry)
            da = env(x - ARM_CX, y - ARM_CY, INNER_W * 0.26 * arm_scale, H * 0.34 * arm_scale)
            cloud = max(dc, 0.85 * da)
            if cloud <= 0.0:
                continue

            f = fbm(x * zoom + 11.0, y * zoom + 7.0)
            d = cloud * (0.35 + 0.95 * f) * dens

            if d < threshold:
                continue              # deep-space void -- leave black (intentional, not a bug)

            di = int(d * 3.99)
            ch = RAMP[min(3, di)]

            t = temp + (f - 0.5) * 0.25
            ti = int(max(0.0, min(1.0, t)) * len(TEMP)) % len(TEMP)
            fg = TEMP[ti]
            panel.set(x, y, ch, fg, 0)

    # --- protostars: the ignition climax (P3 only). EMBEDDED in a tight ring around the
    #     core center so they cohere into ONE hot mass, not scattered over a broken field. ---
    if protostars:
        rng = random.Random(0xF1E4)
        n = 3                          # v2: 3 coherent ignition cores, not 7 scattered
        for k in range(n):
            ang = (k / n) * 2 * math.pi + 0.6
            rr = 0.18                  # tight ring radius around core center -> one mass
            px = int(CORE_CX + INNER_W * rr * math.cos(ang))
            py = int(CORE_CY + H * rr * math.sin(ang))
            R = rng.choice([4, 5])     # glow radius
            for gy in range(-R, R + 1):
                for gx in range(-R, R + 1):
                    dd = math.hypot(gx, gy)
                    if dd > R:
                        continue
                    xx, yy = px + gx, py + gy
                    if not (0 <= xx < INNER_W and 0 <= yy < H):
                        continue
                    t2 = 1.0 - dd / R              # 1 at core -> 0 at edge
                    if dd < 1.0:
                        panel.set(xx, yy, "\u2588", 107, 0)        # white-hot ignition core
                    elif t2 > 0.6:
                        panel.set(xx, yy, "\u2588", 103, 0)        # amber shell
                    elif t2 > 0.3:
                        panel.set(xx, yy, "\u2593", 91, 0)         # red outer glow
                    else:
                        panel.set(xx, yy, "\u2592", 95, 0)         # magenta wisps

# ---------------------------------------------------------------------------
# render a Panel to ANSI lines (run-length compressed like real ACiD), wrapped in
# left/right double-line border columns so every content row is exactly 80 wide.
# ---------------------------------------------------------------------------
def render_panel(panel):
    out = []
    cur_fg = cur_bg = None
    for y in range(panel.h):
        row = list(panel.canvas[y])
        if row[0][0] == ' ':
            row[0] = ['\u2591', 14, 0]
        if row[-1][0] == ' ':
            row[-1] = ['\u2591', 14, 0]
        wrapped = [('\u2551', 104, 0)] + row + [('\u2551', 104, 0)]
        line = []
        for ch, fg, bg in wrapped:
            if (fg, bg) != (cur_fg, cur_bg):
                line.append(c(fg, bg))
                cur_fg, cur_bg = fg, bg
            line.append(ch)
        out.append("".join(line))
    return out

# ---- assemble ----------------------------------------------------------------
lines = []
def emit(s=""): lines.append(s)

frame_top = sgr(105,40)+"\u2554"+sgr(104,40)+"\u2550"*(W-2)+sgr(105,40)+"\u2557"
frame_bot = sgr(105,40)+"\u255a"+sgr(104,40)+"\u2550"*(W-2)+sgr(105,40)+"\u255d"

emit(frame_top)

# P0 TITLE -- big wordmark + title band on black
p0 = Panel(26)
stamp_wordmark(p0, 4, "AGENTSCI", body_fg=15, halo_fg=9)
sub = "C O S M I C   S C R O L L"
px = (INNER_W - len(sub))//2
for i,ch in enumerate(sub):
    p0.set(px+i, 14, ch, 96, 0)
tag = "a deep-zoom descent into a star-forming region -- one journey"
tx = (INNER_W - len(tag))//2
for i,ch in enumerate(tag):
    p0.set(tx+i, 18, ch, 94, 0)
emit(sgr(0,40))
lines.extend(render_panel(p0))

# T1 seam -> P1 THE FIELD (far view: sparse stars + faint wisps, COOL). v2: mostly VOID.
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=1, phase0=PHASE["p"],
                                          label="THE FIELD", power="DIST 9.2k ly")))
p1 = Panel(44)
cosmic_field(p1, PHASE["p"], zoom=0.05, dens=0.40, temp=0.18, threshold=0.58,
             core_rx=0.30, core_ry=0.40, arm_scale=0.7)    # far: sparse, cool, mostly void
PHASE["p"] += 5
lines.extend(render_panel(p1))

# T2 seam -> P2 APPROACH (cloud resolves into filaments, mid descent, mid-temp). UNCHANGED.
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=2, phase0=PHASE["p"],
                                          label="APPROACH", power="DIST 1.4k ly")))
p2 = Panel(44)
cosmic_field(p2, PHASE["p"], zoom=0.11, dens=1.05, temp=0.50, threshold=0.30)    # mid: filaments resolve
PHASE["p"] += 5
lines.extend(render_panel(p2))

# T3 seam -> P3 IGNITION (deep zoom into ONE dense core; protostars ignite -- climax, HOT).
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=3, phase0=PHASE["p"],
                                          label="IGNITION", power="CORE    //  T-0")))
p3 = Panel(46)
cosmic_field(p3, PHASE["p"], zoom=0.20, dens=1.50, temp=0.85, threshold=0.24,
             protostars=True, core_rx=0.30, core_ry=0.40, arm_scale=0.6)   # tight coherent core
PHASE["p"] += 5
lines.extend(render_panel(p3))

# T4 seam -> P4 CREDITS
emit(sgr(0,40))
lines.extend(render_panel(transition_band(8, index=4, phase0=PHASE["p"],
                                          label="CREDITS", power="END OF DESCENT")))

# P4 CREDITS -- full contributor sequence on black
p4 = Panel(26)
title = "C R E D I T S"
cx = (INNER_W-len(title))//2
for i,ch in enumerate(title):
    p4.set(cx+i, 1, ch, 107, 0)
rows = [
 ("COSMIC SCROLL v2.0", 96),
 ("a collaborative ANSI scroll -- a deep-zoom descent into a star-forming region", 94),
 ("", 0),
 ("PANELS + MATH:", 103),
 ("   P1 THE FIELD   far view: sparse starfield + faint nebula wisps, cool void", 95),
 ("   P2 APPROACH    filamentary fbm cloud body resolves, denser field", 95),
 ("   P3 IGNITION    deep zoom into one coherent core; protostars ignite (hot climax)", 95),
 ("SEAMS + CREDITS: raze", 93),
 ("DEPTH READ (cool->warm): carried from NEBULA v2.0 into new ground", 93),
 ("", 0),
 ("raze / AGENTSCII -- the cosmic tradition, one journey", 107),
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
with open("scratch/raze-cosmic-scroll.ans", "w", encoding="cp437") as f:
    f.write(out)

# hygiene self-check
import re
d = out.encode("cp437")
ctrl = set(b for b in d if b < 0x20 or b == 0x7f)
print("rows:", len(lines))
print("control bytes:", sorted(hex(x) for x in ctrl), "(want only 0x1b,0x0a)")
vis = re.sub(r'\x1b\[[0-9;]*m', '', out)
widths = [len(l) for l in vis.split("\n")]
from collections import Counter
print("width histogram:", Counter(widths).most_common(6))
print("ends on reset:", out.rstrip().endswith(RESET))
