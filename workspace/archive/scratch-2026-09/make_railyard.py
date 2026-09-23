#!/usr/bin/env python3
# RAILYARD v1 -- AGENTSCII (raze). A night rail yard in ONE-POINT PERSPECTIVE.
#
# Fresh territory for the house: everything landscape-ish we've shipped is horizon-based
# (DUSK sun-over-water, WHARF lamp-on-pier, CITY skyline) or abstract/fractal/dashboard.
# No one-point perspective yet -- converging tracks receding to a vanishing point is a
# distinct ACiD composition and plays the block-dither idiom well: density + brightness
# falloff carry DEPTH (far = dim/dense toward the VP, near = bright), not flat fills.
#
# Composition (single screen, 46 rows):
#     - night sky top band: deep-blue gradient to black, sparse stars, faint cyan horizon glow
#     - a field of parallel tracks converging to ONE vanishing point high-center; ties
#       (sleepers) get shorter + closer toward the VP (perspective), rails bright-cyan lit
#     - a single SIGNAL LIGHT mast standing on a track lane as the focal source: amber head
#       + glow halo, illuminating its own nearest rail (physically coherent light, not a fake
#       reflection stripe) -- the one warm accent in an otherwise cool blue/cyan field
#     - rising STEAM wisps (dithered) drifting up from the yard, breaking the geometry
#     - house double-line frame + title bar + bottom-right sig block, standalone \x1b[0m tail
#
# House idiom byte-for-byte as TUNNEL/DEEPZOOM/FRACTAL: 80 cols, cp437 on disk, raw SGR,
# bright fg (91-107), no flat fills. Self-check hygiene gate at the end.

import math, re

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, same as TUNNEL/FRACTAL/JULIA/PLASMA)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]     # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"             # light->dark density ramp

# vanishing point (col,row) high-center; tracks fan out from here to the wide bottom
VPX, VPY = 40.0, 7.0
SKY_ROWS = 11                                 # top band is sky; below it is the yard floor
SIG_ROW = H - 3                               # sig block starts here

grid = [[(None, None, None)] * W for _ in range(H)]
def put(r, c, ch, fg=None, bg=None):
    if 0 <= r < H and 0 <= c < W:
        grid[r][c] = (ch, fg, bg)

# ---------------------------------------------------------------------------
# SKY: vertical gradient deep-blue -> black over the top band, sparse stars,
# a faint cyan horizon glow just above where the yard floor begins.
# ---------------------------------------------------------------------------
def sky():
    for r in range(SKY_ROWS):
        t = r / max(1, SKY_ROWS - 1)                 # 0 top -> 1 at horizon
        bg = 44 if t < 0.5 else 0                    # deep blue high, fading to black
        for c in range(W):
            put(r, c, " ", None, bg)
    hr = SKY_ROWS - 1                                # horizon glow line: sky meets floor
    for c in range(W):
        d = abs(c - VPX) / (W * 0.5)                # strongest near center (under the VP)
        fg = 94 if d < 0.35 else (96 if d < 0.7 else None)     # cya core, blu falloff
        put(hr, c, " ", fg, 0)
      # sparse stars -- deterministic scatter in the upper sky, a few bright glints
    rng = 12345
    for _ in range(46):
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        c = rng % W
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        r = rng % max(1, SKY_ROWS - 2)
        if grid[r][c][0] == " ":
            bright = (rng % 7 == 0)
            put(r, c, "*", 107 if bright else 96, None)

# ---------------------------------------------------------------------------
# YARD FLOOR: parallel tracks converging to the VP. Each track is a pair of rails;
# ties (sleepers) are short horizontal segments between them that get shorter + closer
# toward the VP (perspective). Brightness/hue falloff with depth carries the recession.
# ---------------------------------------------------------------------------
def yard():
    bottom_xs = [4, 18, 32, 46, 60, 74]            # 6 lanes of track centerlines at bottom
    rail_half = 2.0                                 # half-width of a track at the near edge
    floor_top = SKY_ROWS                            # yard starts right under the horizon

    for r in range(floor_top, SIG_ROW):
        t = (r - floor_top) / max(1, (SIG_ROW - 1) - floor_top)     # 0 far -> 1 near
        depth = (r - VPY) / max(1, (H - 1) - VPY)                   # perspective pinch
        if depth < 0: depth = 0.0
        scale = depth * depth                       # quadratic pinch -> strong convergence

        for lx in bottom_xs:
            cx = VPX + (lx - VPX) * scale           # rail centerline at this row
            half = rail_half * scale                # track width pinches to ~0 at VP
            left_r = int(round(cx - half))
            right_r = int(round(cx + half))

              # ties: horizontal sleeper between the rails. Spacing tightens with depth
              # (more ties visible far away) via a row-parity gate that flips with scale.
            tie_gate = ((r * 3 + int(lx)) % max(1, int(2 + (1 - scale) * 6))) == 0
            if tie_gate and right_r >= left_r:
                for c in range(left_r, right_r + 1):
                      # sleepers: one muted blue-grey structure, brightness by depth only
                      # (far ties dim/dense receding into the yard, near ties brighter) --
                      # NOT per-row hue cycling, which read as scattered colored dots.
                    fg = 94 if t > 0.7 else (96 if t > 0.4 else 92)
                    dens = RAMP[1 if t < 0.45 else (0 if t > 0.8 else 2)]
                    put(r, c, dens, fg, 0)

              # the two rails: bright cyan catching light, brightest near the camera
            for rc in (left_r, right_r):
                if 0 <= rc < W:
                    fg = 94 if t > 0.3 else 96      # cya when lit, dimmer blu far away
                    put(r, rc, "|", fg, 0)

# ---------------------------------------------------------------------------
# SIGNAL LIGHT: a mast standing IN the yard on a real track lane (x=60 at bottom).
# Its base is near (bottom of the floor), its head rises up toward the horizon. The lamp
# illuminates its OWN nearest rail with amber -- physically coherent light, not a fake
# reflection stripe. Glow halo around the head; amber spill onto the lit end of the track.
# ---------------------------------------------------------------------------
def signal():
    mx = 58                                          # mast column, off-center right third
    base = SIG_ROW - 1                                # base sits on the near floor
    head_r = SKY_ROWS + 3                            # amber head at mid-yard height (visible)
       # mast: a vertical pole standing in the yard -- bright near its base, dimming up
       # toward the head. A real signal-light post, not a perspective-collapsed stripe.
    for r in range(head_r, base):
        t = (r - head_r) / max(1, base - head_r)      # 0 at head -> 1 at base (near)
        put(r, mx, "\u2502", 96 if t > 0.4 else 94, 0)       # blu->cya as it nears camera
       # head: amber lamp with a dithered glow halo (3x3 ring + bright core) -- the one
       # warm accent in an otherwise cool blue/cyan field; this is the focal source.
    put(head_r, mx, "\u2588", 93, 0)                # bright amber core
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0: continue
            put(head_r + dr, mx + dc, "\u2593", 93, 0)       # amber glow ring
       # amber spill onto the nearest track lane (x=60) just below the head -- the lit end
       # of that track, physically coherent light from the lamp.
    for r in range(head_r + 1, min(base, head_r + 7)):
        t = (r - head_r) / max(1, base - head_r)
        depth = (r - VPY) / max(1, (H - 1) - VPY)
        scale = depth * depth if depth > 0 else 0.0
        cx = int(round(VPX + (60.0 - VPX) * scale))     # lane-60 perspective at this row
        put(r, cx, "|", 93, 0)                       # amber-lit rail near the lamp


# ---------------------------------------------------------------------------
# STEAM: dithered wisps rising from the yard floor, breaking the track geometry.
# A few drifting columns that fade as they rise.
# ---------------------------------------------------------------------------
def steam():
    cols = [12, 27, 43, 66]
    for base in cols:
        for i, r in enumerate(range(SIG_ROW - 4, SKY_ROWS + 2, 1)):
            c = base + int(2 * math.sin(i * 0.6))     # wisp drifts sideways as it rises
            fade = (r - SKY_ROWS) / max(1, SIG_ROW - SKY_ROWS)    # 0 high -> 1 low
            if fade < 0.35: continue                  # wisp dissipates up top
            dens = RAMP[0 if fade > 0.7 else (1 if fade > 0.45 else 2)]
            put(r, c, dens, 96, 0)                   # faint blue-white steam

# ---------------------------------------------------------------------------
# FRAME + TITLE BAR + SIG BLOCK (house bar from logo/RADIAL/TUNNEL).
# ---------------------------------------------------------------------------
def frame():
    for c in range(W):                               # double-line border all around
        put(0, c, "\u2554", 93, 0); put(1, c, "\u2550", 96, 0)
        put(H - 1, c, "\u2557", 93, 0); put(H - 2, c, "\u2550", 96, 0)
    for r in range(1, H - 1):
        put(r, 0, "\u2551", 96, 0); put(r, W - 1, "\u2551", 96, 0)
      # title bar: a centered wordmark band just under the top border
    title = " RAILYARD "
    tc = (W - len(title)) // 2
    for c in range(tc, tc + len(title)):
        put(3, c, title[c - tc], 107, 4)            # bright white on blue band
    sub = " one-point perspective / night yard "
    sc = (W - len(sub)) // 2
    for c in range(sc, sc + len(sub)):
        put(4, c, sub[c - sc], 94, None)

def sig():
      # bottom-right signature block per STYLE.md: handle / tag / title+version / date
    lines = [
          "raze / AGENTSCII",
          "RAILYARD v1.0 -- night yard, one-point perspective",
          "1996  joint-ready (open for hollis pass)",
     ]
    for i, ln in enumerate(lines):
        r = SIG_ROW + i
        c = W - len(ln) - 2
        for j, ch in enumerate(ln):
            fg = 107 if i == 0 else (93 if i == 1 else 96)
            put(r, c + j, ch, None)

# ---------------------------------------------------------------------------
# COMPOSE
# ---------------------------------------------------------------------------
sky()
yard()
signal()
steam()
frame()
sig()

# render grid -> ANSI. A cell with no char is black bg space; we emit SGR only when
# the (fg,bg) pair changes from the previous emitted cell, to keep it tight.
def cell_sgr(fg, bg):
    fg = 0 if fg is None else fg                    # house: explicit black, never default
    bg = 0 if bg is None else bg
    fcode = str(90 + (fg & 7)) if fg >= 8 else str(30 + (fg & 7))
    bcode = str(100 + (bg & 7)) if bg >= 8 else str(40 + (bg & 7))
    return ESC + fcode + ";" + bcode + "m"

lines = []
for r in range(H):
    cells = []
    cur = None
    for c in range(W):
        ch, fg, bg = grid[r][c]
        if ch is None:
            ch, fg, bg = " ", 0, 0
        key = (fg, bg)
        if key != cur:
            cells.append(cell_sgr(fg, bg))
            cur = key
        cells.append(ch)
    lines.append("".join(cells))

body = "\n".join(lines)
data = body + "\n" + RESET + "\n"                   # standalone reset tail, house convention

with open("scratch/raze-railyard.ans", "w", encoding="cp437") as f:
    f.write(data)

# ---------------------------------------------------------------------------
# HYGIENE GATE (mirror TUNNEL/FRACTAL self-checks)
# ---------------------------------------------------------------------------
raw = data.encode("cp437")
assert raw.count(0xe2) == 0, "UTF-8 lead byte leaked -- not cp437"
ctrl = set(b for b in raw if b < 32 or b == 127)
assert ctrl <= {0x1b, 0x0a}, f"unexpected control bytes: {ctrl}"
def width(line):
    s = re.sub(r"\x1b\[[0-9;]*m", "", line)
    return len(s)
for i, ln in enumerate(lines):
    w = width(ln)
    assert w == W, f"row {i} width {w} != {W}"
bad = []
for m in re.finditer(rb"\x1b\[([0-9;]+)m", raw):
    for tok in m.group(1).decode().split(";"):
        v = int(tok)
        if v == 0: continue
        if not (30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
            bad.append(v)
assert not bad, f"out-of-range SGR tokens: {set(bad)}"
assert raw.rstrip().endswith(ESC.encode() + b"0m"), "no standalone reset tail"
print("OK raze-railyard.ans", len(raw), "bytes,", H, "rows x", W, "cols, hygiene clean")
