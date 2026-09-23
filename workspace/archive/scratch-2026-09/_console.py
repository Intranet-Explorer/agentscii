#!/usr/bin/env python3
# _console.py -- hollis solo. THE CONSOLE // "the control desk that runs the plant."
#
# PROVENANCE / WHY NEW: raze's THE REACTOR (vertical vessel, radial core light) + THE TURBINE
# (horizontal capsule, axial intake light) are a coherent hot-plasma pair. hollis's #2 brief for
# pack43 is the CONTROL-ROOM / console piece that rounds it into a 3-piece batch: the thing that
# OPERATES the machines. Cool-grey technical UI register -- distinct from BOTH on two axes:
#   (1) SUBJECT/REGISTER: a flat frontal CONTROL PANEL / dashboard (screens + gauges + buttons, an
#       INTERFACE) vs reactor/turbine's 3D machine BODIES and GHOST ENGINE's twin-cylinder engine.
#   (2) LIGHT MODEL: EMISSIVE -- the screens and LEDs glow on their own (multiple self-lit sources),
#       not a single external core light shading a lit mass. A UI lights itself; that's honest.
#   Palette ties to the family via amber+cyan screen glow + rare green/red status, but is
#   predominantly COOL-GREY technical -- distinct from the hot-plasma-dominant pair and from
#   GHOST ENGINE's blue-steel body.
#
# SIGNATURE MOVE: symmetric console FRAME via mirror(axis='v') (a real control desk IS symmetric)
# BUT broken by an ASYMMETRIC main-screen readout -- a live oscilloscope trace that is NOT
# left-right symmetric. "Symmetric frame + asymmetric content" -- a genuinely different move from the
# fully-symmetric machine bodies, and it reads as a LIVE instrument, not a static object.
#
# PASSES (METHODOLOGY), verified by eye with preview_piece at each:
#   P1 flat silhouettes -> verify massing; P2 shade (panel body dim grey / screens emissive glow);
#   P3 constructed details (oscilloscope trace, LED bars, gauge dials + needles, level meters,
#      button bank, status text); MIRROR frame; P4 texture the void around the desk; P5 frame+title.
#
# COLOR CALIBRATION GOTCHA (re-confirmed from _reactor.note.txt): canvas.sgr/figure_common.c both
# map a plain 0-7 hue index via (90+(fg&7)) if fg>7 else (30+fg). Pass PLAIN 0-7 hue indices
# everywhere -- NOT pre-encoded SGR codes like 11/14/15 -- or the double-map path silently muddies
# color. Verified against a swatch render.

import sys, math, random
sys.path.insert(0, "scratch")
from canvas import Canvas, mirror, texture_fill, RAMP, write_ans
from figure_common import light_field, shade, c, RESET

PASS = int(sys.argv[1]) if len(sys.argv) > 1 else 5   # which pass to render up to (for verify-by-eye)

W, H = 80, 52
cv = Canvas(W, H)
CX = W / 2.0
MID = W // 2
SEED = 13
random.seed(SEED)

# ---- console geometry (LEFT-HALF region fns; mirror() handles the right) -------
# A frontal control desk: big central monitor + two flanking side panels, a row of gauges below,
# a button bank at the base. Everything defined for x < MID where it's symmetric.

def body(x, y):
    # the console shell: a wide rounded-rect panel with a slightly splayed (trapezoid) lower jaw
    if 8 <= y <= 39 and 6 <= x <= 73:
        # round the top corners
        if y < 11 and abs(x - CX) > 30.0:
            return False
        return True
    return False

def main_screen(x, y):
    # the central CRT -- the hero element, shows a live oscilloscope trace
    return 12 <= y <= 26 and 25 <= x <= 54

def side_panel(x, y):
    # flanking vertical status panels (LED stacks + level meters)
    if not (11 <= y <= 37):
        return False
    return (9 <= x <= 21) or (58 <= x <= 70)

def gauge_row(x, y):
    # a row of circular dials across the lower console
    return 30 <= y <= 38 and 8 <= x <= 71

def button_bank(x, y):
    # the key/button bank at the base of the desk
    return 40 <= y <= 42 and 10 <= x <= 69

# ---- P1: flat silhouettes (massing check) -------------------------------------
def paint_flat(region_fn, fg):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                cv.set(x, y, "\u2588", fg, 0)

paint_flat(body, fg=8)
paint_flat(gauge_row, fg=9)
paint_flat(side_panel, fg=10)
paint_flat(main_screen, fg=14)
paint_flat(button_bank, fg=12)

if PASS == 1:
    out = []
    cv.render(out)
    write_ans("scratch/_console.ans", out, title="THE CONSOLE v1.0", handles="hollis")
    print("P1 silhouettes written")
    sys.exit(0)

# ---- P2: shade -- panel body dim grey (flat UI mass), screens emissive glow ---
def shade_region(region_fn, base_fg, hot_fg):
    for y in range(H):
        for x in range(MID):
            if region_fn(x, y):
                ch, fg = shade(L(x, y), base_fg, hot_fg)
                cv.set(x, y, ch, fg, 0)

# panel body: dim grey shell, slightly brighter toward the top (catches ambient room light)
for y in range(H):
    for x in range(MID):
        if body(x, y):
            t = (y - 8.0) / 31.0
            ch, fg = shade(1.0 - 0.5 * t, base_fg=8, hot_fg=15)
            cv.set(x, y, ch, fg, 0)

# side panels: cool grey-blue, emissive-tinted toward their LED stacks
for y in range(H):
    for x in range(MID):
        if side_panel(x, y):
            t = (y - 11.0) / 26.0
            ch, fg = shade(1.0 - 0.4 * t, base_fg=8, hot_fg=15)
            cv.set(x, y, "\u2593" if x % 2 else "\u2591", fg, 0)

# main screen: emissive -- a self-lit CRT, bright cyan glow with a dimmer bezel edge
for y in range(H):
    for x in range(MID):
        if main_screen(x, y):
            # emissive field: brightest at the trace centerline, dimming to the glass edges
            dy = abs(y - 19.0) / 7.5
            Lc = max(0.0, 1.0 - 0.6 * dy)
            ch, fg = shade(Lc, base_fg=4, hot_fg=6)     # blue glass (4) -> cyan glow (6)
            cv.set(x, y, "\u2591", fg, 0)

# gauge row: dim grey dial faces
for y in range(H):
    for x in range(MID):
        if gauge_row(x, y):
            t = (y - 30.0) / 8.0
            ch, fg = shade(1.0 - 0.5 * t, base_fg=8, hot_fg=15)
            cv.set(x, y, "\u2591", fg, 0)

# button bank: dim grey keybed
for y in range(H):
    for x in range(MID):
        if button_bank(x, y):
            cv.set(x, y, "\u2588", 8, 0)

if PASS == 2:
    out = []
    cv.render(out)
    write_ans("scratch/_console.ans", out, title="THE CONSOLE v1.0", handles="hollis")
    print("P2 shade written")
    sys.exit(0)

# ---- P3: constructed details --------------------------------------------------
# P3a: the live oscilloscope trace on the main screen -- ASYMMETRIC (the signature break).
# A damped sine with a spike, sampled across the screen width. Not left-right symmetric.
trace_y = {}
for i in range(0, 30):           # x from 25..54
    px = 25 + i
    t = i / 29.0
    # damped oscillation + a transient spike near the left third -- reads as a live signal
    sig = 6.0 * math.sin(t * 18.0) * math.exp(-1.4 * t) + (3.5 if 8 < i < 11 else 0.0)
    ty = int(round(19.0 - sig))
    trace_y[px] = ty
for px, ty in trace_y.items():
    for yy in range(max(12, ty - 1), min(27, ty + 2)):
        cv.set(px, yy, "\u2588", 3 if abs(yy - ty) == 0 else 6, 0)   # amber trace (3), cyan glow trail
# screen gridlines (dim) so it reads as an instrument display, not a blank panel
for y in range(12, 27, 3):
    for x in range(25, 55):
        if cv.get(x, y)[0] == "\u2591":
            cv.set(x, y, "\u2500", 4, 0)

# P3b: LED indicator stacks on the side panels -- vertical status bars (green/amber/red)
def led_stack(x0, x1, y0, y1):
    cols = [10, 11, 9]           # green / amber / red status columns
    for ci, cx in enumerate(range(x0, x1 + 1)):
        col = cols[ci % len(cols)]
        for yy in range(y0, y1):
            on = ((yy + ci * 3) % 5) < 3     # a live-looking on/off pattern per column
            cv.set(cx, yy, "\u2588", col if on else (col - 8), 0)

led_stack(10, 14, 13, 30)        # left panel LED stack
# P3c: a vertical level meter on the outer edge of each side panel
for yy in range(13, 31):
    lvl = (yy - 13) / 17.0
    fg = 10 if lvl < 0.5 else (11 if lvl < 0.8 else 9)   # green->amber->red as it climbs
    cv.set(20, yy, "\u2588", fg, 0)

# P3d: gauge dials -- circular dial faces with a needle + tick marks, across the lower row
def gauge(cx, cy, r, needle_deg):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                cv.set(x, y, "\u2591", 15, 0)          # bright dial face
    # tick marks around the rim
    for a in range(0, 360, 45):
        tx = int(round(cx + (r - 0.5) * math.cos(math.radians(a))))
        ty = int(round(cy + (r - 0.5) * math.sin(math.radians(a))))
        cv.set(tx, ty, "\u2588", 7, 0)
    # the needle -- points at a live reading (asymmetric across gauges)
    ang = math.radians(needle_deg)
    for t in [0.3, 0.6, 0.9]:
        nx = int(round(cx + (r - 1) * t * math.cos(ang)))
        ny = int(round(cy + (r - 1) * t * math.sin(ang)))
        cv.set(nx, ny, "\u2588", 1, 0)                # red needle
    cv.set(int(cx), int(cy), "\u2588", 7, 0)          # hub

gauge(16, 34, 3.5, 210)
gauge(30, 34, 3.5, 150)
gauge(44, 34, 3.5, 90)
gauge(58, 34, 3.5, 60)
gauge(70, 34, 3.5, 30)

# P3e: button bank -- a grid of small colored keys (varied, like a real keybed)
keycols = [10, 11, 9, 12, 14]
for row in range(40, 43):
    for ci in range(0, 60, 2):
        cx = 10 + ci
        cv.set(cx, row, "\u2588", keycols[(row + ci) % len(keycols)], 0)

# P3f: status text strip along the top of the desk (reads as a system banner)
def text_at(x, y, s, fg):
    for i, ch in enumerate(s):
        if x + i < W:
            cv.set(x + i, y, ch, fg, 0)

# ---- MIRROR the symmetric frame; keep the asymmetric trace on top -------------
mirror(cv, axis='v')
# status banner: painted ONCE, centered, after the mirror -> a single clean line (not doubled)
text_at((W - len("SYS // ONLINE")) // 2, 10, "SYS // ONLINE", 10)
# re-assert the asymmetric oscilloscope trace (mirror would have copied it -- we want it live/odd)
for px, ty in trace_y.items():
    for yy in range(max(12, ty - 1), min(27, ty + 2)):
        cv.set(px, yy, "\u2588", 3 if abs(yy - ty) == 0 else 6, 0)

if PASS == 3:
    out = []
    cv.render(out)
    write_ans("scratch/_console.ans", out, title="THE CONSOLE v1.0", handles="hollis")
    print("P3 details written")
    sys.exit(0)

# ---- P4: texture the void around the desk (not flat black) -------------------
def in_mass(x, y):
    return (body(x, y) or main_screen(x, y) or side_panel(x, y)
            or gauge_row(x, y) or button_bank(x, y))

# cool-grey scanline/dust field around the console -- a technical void, not empty space
texture_fill(cv, lambda x, y: not in_mass(x, y), fg=8, density=0.22, seed=SEED + 1)
for y in range(H):
    for x in range(MID):
        if in_mass(x, y):
            continue
        # faint scanline shimmer: dim cyan/gray horizontal glints near the desk's glow
        if y % 3 == 0 and random.random() < 0.10:
            cv.set(x, y, "\u2580", 4 if random.random() < 0.3 else 8, 0)

# ---- P5: frame + title card --------------------------------------------------
out = []
out.append(c(13) + "\u2554" * W)        # top rule (magenta, matches the pair's frame)
cv.render(out)
out.append(c(13) + "\u2557" * W)        # bottom rule

write_ans("scratch/_console.ans", out, title="THE CONSOLE v1.0", handles="hollis")
print("P5 final written")
