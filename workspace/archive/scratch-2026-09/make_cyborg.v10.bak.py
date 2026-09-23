#!/usr/bin/env python3
# make_cyborg.py -- AGENTSCII, joint raze & hollis (provenance: random_direction roll)
#
# ROLL: subject "a robot or cyborg head" | technique "curve_common.phosphor_render()
# traced-curve / scope aesthetic" | palette "full saturated 16-color cycling".
#
# CONCEPT -- a CYBORG HEAD rendered as a diagnostic phosphor SCOPE. The head is
# *traced* like an oscilloscope drawing a skull on a CRT, not filled. A single
# closed profile loop (the skull) + a visor band + neural-port wiring accumulate
# into one phosphor field over a dim Cartesian graticule -- the curve_common idiom,
# but figurative. Stylized, not photoreal: strong landmarks read through the glow.
#
#       1) SKULL PROFILE -- one closed loop: round dome crown -> forehead -> pronounced
#          NOSE bump (face side, right) -> chin juts out -> narrow neck stub -> smooth
#          round occiput (back, left). Hue cycles warm red/amber/yel.
#       2) VISOR          -- a cool cyan/blue band across the eye region + white-hot
#          EYE NODE where mind meets machine.
#       3) NEURAL PORT    -- "wiring" runs fanning back from the occiput + an interface
#          loop at the ear, green/cyan.
#       + a faint SCANLINE sweep band so it reads as a live scope, not a static print.
#
# Treatment matches raze-lissajous v1.0: 80x46 full-bleed, no title bar, phosphor
# accumulation with white-hot nodes at I>0.78, full house hue wheel cycled along t,
# framed sig block below, standalone \x1b[0m reset tail, cp437 on disk, hygiene gate.

import math
from curve_common import (W, H, CX, CY, ESC, sgr, RESET, HUE, RAMP,
                          hue_index, phosphor_render, sig_block, hygiene_gate)

# --- canvas buffers -----------------------------------------------------------
inten = [[0.0]*W for _ in range(H)]
huebuf = [[0.0]*W for _ in range(H)]

def trace(pts, hue0, hue1, decay=1.0):
    n = len(pts) - 1
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[i+1]
        d = math.hypot(x1-x0, y1-y0)
        steps = max(2, int(d*3))
        for s in range(steps+1):
            t = s/steps
            x = x0 + (x1-x0)*t; y = y0 + (y1-y0)*t
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < W and 0 <= yi < H:
                inten[yi][xi] += decay
                huebuf[yi][xi] = hue0 + (hue1-hue0)*t

# --- dim graticule ------------------------------------------------------------
GRID_STEP = 6
def backdrop_graticule(x, y):
    if (x % GRID_STEP == 0) or (y % GRID_STEP == 0):
        return sgr(40, 94) + "\u2591"
    return sgr(40, 40) + " "

# --- 1) SKULL PROFILE -- one closed loop, face side RIGHT ---------------------
# crown(top) -> down the FACE (right): forehead, nose bump, chin -> neck stub at
# bottom -> up the BACK (left): occiput, smooth round. Asymmetric = reads as head.
skull = [
       (38, 7),       # crown (top center)
       (46, 9),       # top-right of dome
       (51, 14),      # forehead front
       (52, 19),      # brow ridge
       (57, 23),      # NOSE BUMP -- pronounced, juts far right (the giveaway)
       (50, 26),      # under-nose / philtrum (pulls back in hard)
       (52, 29),      # upper lip
       (48, 31),      # mouth corner in
       (51, 34),      # CHIN -- juts out
       (45, 37),      # under-chin / jaw front
       (40, 39),      # jaw base center
       (36, 40),      # NECK STUB (narrow bottom = head, not shield)
       (32, 38),      # jaw back
       (27, 33),      # back of jaw / neck
       (25, 27),      # occiput low -- smooth round back
       (24, 20),      # occiput mid
       (26, 13),      # occiput up -- smooth round back
       (31, 9),       # back of dome
       (38, 7),       # close to crown
]
trace(skull, 0.0, 2.6, decay=1.0)               # red->amber->yel warm outline

# --- 2) VISOR band across the eye region (cool cyan/blue) --------------------
visor = []
for i in range(15):
    t = i/14.0
    x = 39 + t*12                   # 39 -> 51 across brow/eye
    y = 18 + math.sin(t*math.pi)*1.3       # slight arch
    visor.append((x, y))
trace(visor, 4.2, 6.0, decay=1.4)              # green->cyan->blue cool band

# EYE NODE -- bright self-intersection where mind meets machine (white-hot at I>0.78)
for r in range(-1,2):
    for c in range(-1,2):
        xi, yi = 45+c, 19+r
        if 0<=xi<W and 0<=yi<H:
            inten[yi][xi] += 2.8

# --- 3) NEURAL PORT -- deliberate wiring from the occiput (back of skull) ----
for ang in (-0.5, -0.15, 0.2, 0.55):
    ex = 24 + math.cos(math.pi+ang)*9
    ey = 26 + math.sin(math.pi+ang)*9
    trace([(24,26),(ex,ey)], 5.0, 6.4, decay=0.9)
# one small interface loop at the ear (the "socket")
loop = []
for i in range(41):
    t = i/40 * 2*math.pi
    loop.append((26 + 2.2*math.cos(t), 27 + 2.6*math.sin(t)))
trace(loop, 6.0, 5.0, decay=0.8)

# --- faint SCANLINE sweep band (live-scope feel) -----------------------------
SCAN = 24
for x in range(W):
    inten[SCAN][x] += 0.16
    huebuf[SCAN][x] = 6.5

# --- render -------------------------------------------------------------------
imax = max(max(r) for r in inten)
GLOW = 4
out = []
phosphor_render(inten, huebuf, imax, GLOW, backdrop_graticule, out)

# scanline accent: overlay a dim cyan rule at the sweep row so it reads as live
out[SCAN] = sgr(40, 96) + "\u2500"*W

# --- title card (top) -- scope readout ---------------------------------------
def centered(text, fg):
    pad = W - len(text); l = pad//2; r = pad-l
    return sgr(fg,40) + " "*l + text + sgr(40,40) + " "*r

out.insert(0, centered("CYBORG // MIND-SCAN", 97))
out.insert(1, centered("AGENTSCII PHOSPHOR SCOPE      --  raze & hollis", 96))

# --- joint-credit sig block (curve_common's is single-handle; we need both) ---
out.append("")
out.append(sgr(105,40) + "\u2560" + sgr(104,40) + "\u2550"*(W-1))
def _sl(text, fg):
    pad = W-len(text); l=pad//2; r=pad-l
    return sgr(104,40)+" "*l+sgr(fg,40)+text+sgr(104,40)+" "*r
out.append(_sl("raze & hollis / AGENTSCII", 97))
out.append(_sl("raze-cyborg-scope v1.0", 96))
out.append(sgr(105,40) + "\u2563" + sgr(104,40) + "\u2550"*(W-1))

raw = "\n".join(out) + RESET
path = "raze-cyborg-scope.ans"
open(path, "w", encoding="cp437").write(raw)
print("wrote", path, len(raw), "bytes,", len(out), "rows")
hygiene_gate(path)
