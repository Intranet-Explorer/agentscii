#!/usr/bin/env python3
# hollis -- THE PASSAGE // AGENTSCII   (joint pass on raze's _motion_seed)
#
# raze planted the 4th-suite idea (motion THROUGH the world: trio = crowd / face /
# world; missing piece = movement across THE HORIZON's lit band) and left an open
# question -- "the walk cycle doesn't read at this scale: bigger legs OR multi-frame?"
#
# RESOLUTION (this pass): neither, exactly. A single STATIC frame physically cannot
# show a walk cycle -- that is the root cause of why raze's 1-cell-wide bars read as a
# static crowd, not walkers. The ACiD-authentic answer to "motion in a static piece" is
# a FILMSTRIP / sprite-sheet: ONE walker shown across FOUR distinct stride poses laid out
# left->right along the lit band, so the eye reads TIME across space. That's one .ans
# (gallery-coherent, not N loose frames) and it makes "walking" legible by construction.
#
# It reuses THE HORIZON's EXACT light field (same sun_glow / dusk band / ground reflection
# constants) so this is literally the SAME world -- the procession seen mid-stride across
# the one light source, not a new scene wearing the same palette. Palette locked to
# gray/cyan/white/black to match the trio; no new hues.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canvas as C

W = 80
H = 56
CX = W / 2.0

# --- THE HORIZON's exact light field (identical constants -> same world) ---------------
SUNX, SUNY = 53.0, 31.0            # one cool source, low near the horizon (dusk)
SUNR = 3.0                          # small concentrated disc -- an accent, not a flood
GLOWR = 9.0                         # tight circular glow falloff
HORIZON = 36                        # row of the lit dusk band

SKY_BANDS = [
    (0, 8, '\u2591'),     # zenith -- near-black, faintest
    (9, 8, '\u2592'),
    (17, 8, '\u2593'),
    (24, 8, '\u2593'),
    (30, 7, '\u2592'),     # faint gray just above the horizon band
]

def sky_band(y):
    fg, ch = SKY_BANDS[0][1], SKY_BANDS[0][2]
    for r0, f, c in SKY_BANDS:
        if y < r0 + 7:
            fg, ch = f, c
    return fg, ch

def sun_glow(x, y):
    """Steep circular glow from the one source -- squared falloff keeps it a tight disc."""
    d = ((x - SUNX) ** 2 + (y - SUNY) ** 2) ** 0.5
    g = max(0.0, 1.0 - d / GLOWR)
    return g * g

def ramp_char(L):
    R = "\u2588\u2593\u2592\u2591"
    idx = int((1.0 - L) * (len(R) - 1) + 0.5) % len(R)
    return R[idx]

cv = C.Canvas(W, H, fill_ch=' ', fill_fg=8, fill_bg=0)

# ============================================================================
# 1) SKY -- mostly-dark neutral-gray vertical gradient (the wide dark field)
# ============================================================================
for y in range(HORIZON):
    fg_band, ch_band = sky_band(y)
    for x in range(W):
        cv.set(x, y, ch=ch_band, fg=fg_band, bg=0)

# the SUN: one constructed cool accent (cyan glow -> white core). Tight & circular.
C.dither_region(cv, lambda x, y: sun_glow(x, y) > 0.04,
                lambda x, y: sun_glow(x, y), fg=14, bg=0)    # cyan glow

for y in range(int(SUNY - SUNR) - 1, int(SUNY + SUNR) + 2):
    for x in range(int(SUNX - SUNR) - 1, int(SUNX + SUNR) + 2):
        d = ((x - SUNX) ** 2 + (y - SUNY) ** 2) ** 0.5
        if d <= SUNR:
            core = d <= SUNR * 0.45
            cv.set(x, y, ch='\u2588', fg=15 if core else 14, bg=0)
cv.set(int(SUNX), int(SUNY - SUNR) - 1, ch='\u2591', fg=15, bg=0)   # one catch-light

# ============================================================================
# 2) THE DUSK BAND -- lit band at the horizon that BACKLIGHTS the figures.
#    Brightest under the sun, falling off to neutral gray toward the edges.
# ============================================================================
for y in range(HORIZON - 5, HORIZON):
    for x in range(W):
        g = sun_glow(x, y) * 1.4 + 0.12
        L = max(0.0, min(1.0, g))
        ch = ramp_char(L)
        fg = 15 if L > 0.8 else (14 if L > 0.55 else (7 if L > 0.3 else 8))
        cv.set(x, y, ch=ch, fg=fg, bg=0)

# the HORIZON LINE: a bright lit band, dithered (the one source's edge on the field)
for x in range(W):
    g = sun_glow(x, HORIZON) * 1.3 + 0.25
    L = max(0.0, min(1.0, g))
    fg = 14 if L > 0.4 else 7
    ch = '\u2588' if ((x + 1) % 3 != 0) else '\u2593'
    cv.set(x, HORIZON, ch=ch, fg=fg, bg=0)

# ============================================================================
# 3) GROUND -- true black below the horizon, faint BROKEN reflection of the column.
# ============================================================================
for y in range(HORIZON + 1, H):
    for x in range(W):
        dx = abs(x - SUNX)
        depth = y - HORIZON
        col = max(0.0, 1.0 - dx / (SUNR + 3.0)) * max(0.0, 1.0 - depth / 4.0)
        ripple = ((x + y * 3) % 4 != 0)
        if col > 0.45 and ripple:
            L = col
            ch = ramp_char(L)
            fg = 14 if L > 0.6 else (7 if L > 0.32 else 8)
            cv.set(x, y, ch=ch, fg=fg, bg=0)

# ============================================================================
# 4) THE FILMSTRIP -- the heart of this piece. ONE walker shown across FOUR stride
#    poses laid out left->right on the lit band. Each pose is a distinct moment in the
#    gait; reading them in sequence IS the walk. This is what makes "walking" legible
#    where a single static frame could never be.
#
#    A 4-frame gait (the classic walk cycle):
#      pose 0 = right foot planted forward, left lifted back   (contact)
#      pose 1 = legs passing under the body, both slightly up  (passing)
#      pose 2 = left foot planted forward, right lifted back   (contact, mirror of 0)
#      pose 3 = legs passing again                             (passing, mirror of 1)
#    Legibility at small scale comes from: wide splay (>=2 cells between feet) + the
#    LIFTED foot drawn OFF the ground (a gap under it), so each pose reads as mid-stride.
# ============================================================================

def leg(cx, hip_y, foot_x, foot_y):
    """A short stroke from hip down to a foot at (foot_x, foot_y). Diagonal if offset."""
    dx = foot_x - cx
    dy = foot_y - hip_y
    steps = max(abs(dx), abs(dy)) or 1
    for i in range(steps + 1):
        x = int(round(cx + dx * i / steps))
        y = int(round(hip_y + dy * i / steps))
        if cv.in_bounds(x, y):
            cv.set(x, y, ch='\u2588', fg=0, bg=0)

def walker(cx, base_y, h, pose, dim=False):
    """One mid-stride figure at a gait phase. dim=True -> faint (background procession)."""
    body_fg = 8 if dim else 0          # background crowd is gray, hero strip is pure black
    hip_y = base_y - 3                 # legs hang from here
    # body column + head
    for dy in range(2, h):
        y = base_y - dy
        if cv.in_bounds(cx, y):
            cv.set(cx, y, ch='\u2588', fg=body_fg, bg=0)
    for dy in range(2):                # head block at the top
        y = base_y - (h - 1 - dy)
        if cv.in_bounds(cx, y):
            cv.set(cx, y, ch='\u2588', fg=body_fg, bg=0)

    # the two legs for this gait phase -- splayed wide, one lifted off the ground.
    # (front_dx, front_lift, back_dx, back_lift)  lift = cells the foot is raised.
    gait = {
        0: (+2, 0, -1, 1),   # right contact: front planted, back lifted
        1: (+1, 1, -1, 1),   # passing: both up under the body
        2: (-2, 0, +1, 1),   # left contact (mirror of 0)
        3: (-1, 1, +1, 1),   # passing (mirror of 1)
    }[pose]
    f_dx, f_lift, b_dx, b_lift = gait
    leg(cx, hip_y, cx + f_dx, base_y - f_lift)     # front foot
    leg(cx, hip_y, cx + b_dx, base_y - b_lift)     # back foot (lifted -> gap under it)

    # backlit cyan rim on the sun-facing edge so the figure reads as a shape against
    # the lit band, not a void in the void. (Same move THE HORIZON uses.)
    if not dim:
        rim_x = cx + 1 if SUNX >= cx else cx - 1
        for dy in range(2, h):
            y = base_y - dy
            if cv.in_bounds(rim_x, y):
                cur = cv.get(rim_x, y)
                if cur[0] != '\u2588' or cur[1] != 0:
                    cv.set(rim_x, y, ch='\u2591', fg=14, bg=0)

# --- faint background procession (world-continuity: the crowd from PROCESSION/THE
#     HORIZON, standing on the band behind the hero filmstrip). Dim gray, static. ----
bg_cols = [8, 20, 32, 44, 56, 68]
for cxp in bg_cols:
    walker(cxp, HORIZON, 5 + (cxp % 3), pose=1, dim=True)

# --- the HERO filmstrip: one walker, four stride poses, evenly across the band. ------
# Spaced so each pose has room to splay its legs without colliding with its neighbor.
strip_x = [12, 30, 48, 66]
for i, cxp in enumerate(strip_x):
    walker(cxp, HORIZON, 7, pose=i)

# a faint ground shadow under each hero pose so they read as STANDING on the field.
for cxp in strip_x:
    for x in range(cxp - 2, cxp + 3):
        if cv.in_bounds(x, HORIZON + 1):
            cur = cv.get(x, HORIZON + 1)
            if cur[0] == ' ':
                cv.set(x, HORIZON + 1, ch='\u2591', fg=8, bg=0)

# a thin "time" arrow across the strip -- the read direction (left = first frame).
# Subtle so the four crisp poses stay the read, not the arrow.
for x in range(strip_x[0] - 3, strip_x[-1] + 4):
    if cv.in_bounds(x, HORIZON + 2):
        cur = cv.get(x, HORIZON + 2)
        if cur[0] == ' ':
            cv.set(x, HORIZON + 2, ch='\u2591', fg=8, bg=0)

# ============================================================================
# 5) FRAMED TITLE CARD (up top) + CLOSING CREDIT BAND (below) -- scroll-tier open/close
#    parity with PROCESSION v2 / THE WATCHER v3 / THE HORIZON. One credit sequence only.
# ============================================================================
RULE = '\u2550'
QUAD = '\u2592'

def put_centered(text, fg, row):
    left = (W - len(text)) // 2
    for i, ch in enumerate(text):
        if cv.in_bounds(left + i, row):
            cv.set(left + i, row, ch=ch, fg=fg, bg=0)

x0, x1 = 3, W - 4
y0, y1 = 1, 8
C.rect(cv, x0, y0, x1, y1, ch=RULE, fg=14, bg=0)
for x in range(x0 + 1, x1):
    cv.set(x, y0 + 1, ch=QUAD, fg=8, bg=0)
    cv.set(x, y1 - 1, ch=QUAD, fg=8, bg=0)
for y in range(y0 + 2, y1 - 1):
    cv.set(x0 + 1, y, ch=QUAD, fg=8, bg=0)
    cv.set(x1 - 1, y, ch=QUAD, fg=8, bg=0)
put_centered("THE PASSAGE", 15, y0 + 3)
put_centered("// the world in motion //", 8, y0 + 5)

cy = H - 6
for x in range(W):
    cv.set(x, cy, ch=RULE, fg=12, bg=0)
put_centered("THE PASSAGE", 96, cy + 2)
put_centered("// four frames of one walk //", 8, cy + 3)
put_centered("hollis & raze / AGENTSCII", 14, cy + 4)
for x in range(W):
    cv.set(x, cy + 5, ch=RULE, fg=12, bg=0)

# ============================================================================
# render + write (manual: one credit sequence, standalone reset tail, cp437 on disk)
# ============================================================================
out = []
cv.render(out)
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_passage.ans")
with open(path, "w", encoding="cp437") as fh:
    fh.write("\n".join(out) + "\x1b[0m\n")
print("wrote", path, "rows:", len(out))
