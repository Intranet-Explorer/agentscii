#!/usr/bin/env python3
# curve_common -- shared machinery for the AGENTSCII "parametric curve" mini-family.
#
# The family opens a single new idiom (a 1D PARAMETRIC CURVE traced through the 2D field,
# not a per-cell scalar field or rotational fold) and renders it three ways:
#   LISSAJOUS  -- Cartesian looping figures x=A sin(at+d), y=B sin(bt), over a square graticule.
#   ROSE       -- polar petal bloom r=cos(k*theta), over a faint concentric-ring polar graticule.
#   SPIROGRAPH -- interlaced hypotrochoid + epitrochoid gear-lace, pure black void.
# All three share the same phosphor-decay trace, the same 16-color house hue wheel cycled along
# the curve parameter, white-hot self-intersection nodes, and the same framed sig block -- so they
# read as one coherent family of "scopes" rather than three unrelated pieces. Each differs in its
# curve family AND its backdrop structure, so none is a copy of another.
#
# Treatment (matches raze-lissajous v1.0 exactly):
#   - 80x46 full-bleed field, no box/title bar (house idiom for full-bleed pieces).
#   - phosphor accumulation: every cell a curve passes through accumulates intensity; overlapping
#     nodes bloom bright, trails fade via the density ramp.
#   - hue cycles the FULL 16-color house wheel along the parameter t (dense fast-shifting = ACiD craft).
#   - white-hot node at high-intensity self-intersection (I>0.78 -> full block on white fg).
#   - faint backdrop gives empty space structure instead of flat black.
#   - framed sig block below: bright-blue corners, bright-cyan rule body, two centered lines.
#   - standalone \x1b[0m reset tail. cp437 on disk. Self-checking hygiene gate.

import math
import re

W = 80
H = 46
CX = W / 2.0
CY = H / 2.0
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house hue wheel: mag red yel grn cya blu wht amb (matches lissajous exactly)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]
RAMP = "\u2588\u2593\u2592\u2591"          # bright->dim density ramp (full block first)

def hue_index(phase):
    return int(phase) % len(HUE)

# --- backdrops: give empty space structure instead of flat black ---------------
GRID_STEP = 8
def backdrop_graticule(x, y):
    """Square scope grid -- dim cyan ticks on a Cartesian lattice (lissajous look)."""
    if (x % GRID_STEP == 0) or (y % GRID_STEP == 0):
        return sgr(40, 94) + "\u2591"
    return sgr(40, 40) + " "

def backdrop_rings(x, y):
    """Concentric polar rings -- faint cyan circles at fixed radii (polar-scope look)."""
    dx = x - CX; dy = y - CY
    r = math.hypot(dx, dy)
    ring = round(r / 5.0) * 5.0            # nearest ring radius
    if abs(r - ring) < 0.45:               # on a ring line
        return sgr(40, 94) + "\u2591"
    return sgr(40, 40) + " "

def backdrop_void(x, y):
    """Pure black void -- the curve's lace IS the structure (spirograph look)."""
    return sgr(40, 40) + " "

# --- phosphor render ----------------------------------------------------------
def phosphor_render(inten, huebuf, imax, GLOW, backdrop, out):
    """Map accumulated intensity -> phosphor cells over a backdrop. Returns nothing; appends to out."""
    for y in range(H):
        row = []
        for x in range(W):
            I = inten[y][x] / imax
            if I < 0.06:
                row.append(backdrop(x, y))
                continue
            fg = HUE[hue_index(huebuf[y][x])]
            if I > 0.78:
                row.append(sgr(40, 97) + "\u2588")          # white-hot self-intersection node
            else:
                idx = int((I * GLOW)) % 4
                row.append(sgr(40, fg) + RAMP[idx])
        out.append("".join(row))

# --- signature block (house standard for full-bleed pieces) -------------------
def sig_block(out, title):
    out.append("")
    out.append(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
    def sigline(text, fg):
        pad = W - len(text)
        left = pad // 2
        right = pad - left
        return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
    out.append(sigline("raze / AGENTSCII", 97))
    out.append(sigline(title, 96))
    out.append(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

# --- hygiene gate -------------------------------------------------------------
def hygiene_gate(path):
    raw = open(path, "rb").read()
    ctrl = sorted(set(b for b in raw if b < 0x20 or b == 0x7f))
    print("bytes:", len(raw), "ctrl bytes:", [hex(c) for c in ctrl])
    try:
        raw.decode("cp437"); print("cp437 on disk: OK")
    except Exception as e:
        print("cp437 FAIL", e)
    sgrs = re.findall(rb"\x1b\[([0-9;]*)m", raw)
    bad = []
    for s in sgrs:
        for tok in (s.decode() or "0").split(";"):
            if tok == "": continue
            v = int(tok)
            if not (v == 0 or 30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
                bad.append(v)
    print("SGR tokens:", len(sgrs), "out-of-range:", sorted(set(bad)))
    disp = re.sub(rb"\x1b\[[0-9;]*m", b"", raw).decode("cp437")
    widths = set(len(l) for l in disp.split("\n"))
    print("row widths:", sorted(widths))
    # dead-region check: 3+ fully-blank consecutive rows (a real render bug signature)
    blank_runs = []
    run = 0
    for l in disp.split("\n"):
        if l.strip() == "":
            run += 1
        else:
            if run >= 3: blank_runs.append(run)
            run = 0
    if run >= 3: blank_runs.append(run)
    print("blank runs >=3:", blank_runs)
    print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))
