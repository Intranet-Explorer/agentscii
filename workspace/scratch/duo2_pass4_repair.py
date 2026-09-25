#!/usr/bin/env python3
"""duo2 pass 4 -- the three defects an outside reviewer named, and only
those. Supersedes duo2_pass2_glass.py and duo2_pass3_frame.py: it runs
pass 1 unchanged for the hand and the bars, then redraws the pane, the
thumb junction and the void, then re-lays the credit block.

The hand's modelling is untouched apart from one fold (defect 2). The
casement is untouched. No element is added or removed.

  1. THE PANE WAS STAMPED FILLER. "The background thirds are
     near-uniform density noise regardless of what's on screen."
     Correct, and it was one line's fault: the old field added a
     per-facet bias of +-0.086 keyed to an angular index, a value step
     with no visible cause, which came out as ░/▒ blotches at constant
     average density. That is a stamp. It is gone, and so is the ordered
     dither over the field. What is left is only what glass has a reason
     to do -- see `field` below -- and where it has no reason to do
     anything the field is now a single even density. Emptier on purpose.

  2. THUMB SEVERED FROM THE PALM. Checked cell by cell first: the
     block-in silhouette is intact through the junction, the thumb and
     the palm are one connected mass. So the break was purely value --
     the thumb's shaded lower flank and the palm's dark left edge met at
     the same tier, and the pane's contact shadow ran black right up
     against them. Fixed on both sides: the thenar web is lifted to the
     value a fold turned toward the source actually has, and the cast
     shadow no longer goes to near-black.

  3. FLAT BLACK LOWER THIRD. Root cause found, not painted over: the
     forearm splits the breach into two void masses of 400 and 387px,
     and D.hole_mask returns only the LARGEST, so every pass so far has
     drawn into one lobe and left the other outside every mask it owned.
     That unreachable lobe is precisely the region the review measured
     as unrendered. Both lobes now carry the one thing really inside a
     hole -- the depth of the opening. Still by a long way the darkest
     region in the piece, so the hole still reads as a hole.
"""
import math
import runpy
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import duo2_common as D  # noqa: E402

BREAK = (40.0, 74.0)
BARS = [(0, 0, 5, 100), (75, 0, 5, 100), (0, 26, 80, 4), (20, 0, 3, 100)]


def in_bar(x, y):
    return any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh in BARS)


# ======================================================================
# pass 1 verbatim -- hand, bars. Then defect 2, on the hand side.
# ======================================================================
g1 = runpy.run_path(str(HERE / "duo2_pass1_shade.py"))
mask, val = g1["mask"], g1["val"]

# The thenar web: the fold of palm the thumb grows out of. It is a raised
# ridge facing the top-left source, so it is genuinely one of the lighter
# things on the front plane -- lifting it is the correct value for it,
# not a patch over a gap. Clipped to the block-in hand mask, so this
# cannot move the silhouette the blind read depends on.
for y in range(D.PH):
    for x in range(D.CW):
        if mask[y][x] != D.HAND:
            continue
        res = D.capsule_light(x, y, 22, 50, 34, 58, 6)
        if not res:
            continue
        v = D.clamp01(0.50 + 0.44 * res[0])
        if val[y][x] is None or v > val[y][x]:
            val[y][x] = v

nh = D.paint(mask, D.HAND, val, (4, 6, 14), dither=0.02)


# ======================================================================
# the breach -- BOTH lobes (see defect 3 in the module docstring)
# ======================================================================
def breach_mask():
    """Every void mass big enough to be part of the break. The next
    largest thing in the void colour is a 53px crack spike, so 150 is a
    clean cut."""
    seen = [[False] * D.CW for _ in range(D.PH)]
    out = [[False] * D.CW for _ in range(D.PH)]
    for sy in range(D.PH):
        for sx in range(D.CW):
            if seen[sy][sx] or mask[sy][sx] != D.VOID:
                continue
            comp, q = [], deque([(sx, sy)])
            seen[sy][sx] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < D.CW and 0 <= ny < D.PH and not seen[ny][nx] \
                            and mask[ny][nx] == D.VOID:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) >= 150:
                for x, y in comp:
                    out[y][x] = True
    return out


hole = breach_mask()

# ======================================================================
# defect 1 -- the pane
# ======================================================================
crack_px = [(x, y) for y in range(D.PH) for x in range(D.CW)
            if mask[y][x] == D.VOID and not hole[y][x]]
angles = sorted({round(math.atan2(y - BREAK[1], x - BREAK[0]), 2)
                 for x, y in crack_px})
seeds, last = [], -9.0
for a in angles:
    if a - last > 0.55:
        seeds.append(a)
        last = a
seeds += [-2.42, -1.98, -1.22]
seeds = sorted(set(round(a, 3) for a in seeds))


def field(x, y):
    """Three causes, no fourth.

    1. LIGHT falling on the glass from the one top-left source: a single
       smooth ramp, no jitter anywhere on it. Away from the break this
       is ALL the field carries, so those regions come out as long even
       runs of one density that step where the light steps. Flat is the
       right answer there -- intact glass has nothing in it to draw, and
       texture put there to make the region look worked is exactly what
       got called filler.
    2. THE BREAK. Fracture faces tilt every which way and catch the
       source, so the glass brightens into a halo round the hole and the
       density climbs with it: ░ in the far corners, ▒ across the middle
       distance, ▓ and solid highlight where the crazing is. Density now
       tracks distance from the break.
    3. REFLECTION. Two steep bands of sky, faded out toward the bottom
       because the sky is up. A pane with no reflection in it is a wall.
    """
    d = math.hypot(x - BREAK[0], y - BREAK[1])
    v = 0.76 - 0.17 * (x / 79.0) - 0.16 * (y / 99.0)
    v += 0.22 * math.exp(-((d - 30) / 13.0) ** 2)
    for c, wdt in ((24, 7.0), (57, 5.5)):
        v += 0.10 * max(0.0, 1.0 - y / 120.0) * \
            math.exp(-(((x - y * 0.55) - c) / wdt) ** 2)
    return v


pval = [[None] * D.CW for _ in range(D.PH)]
for y in range(D.PH):
    for x in range(D.CW):
        if mask[y][x] == D.PANE:
            # the field never ramps to black: that is what stopped the
            # hole reading as a hole on an earlier attempt.
            pval[y][x] = min(0.97, max(0.52, field(x, y)))

# contact shadow / contour. The hand is PRESSED on the glass, so it
# occludes the source and drops a tight shadow down-right onto the pane.
# Floor raised from 0.09 to 0.17 and the reach cut from 4px to 3: at 0.09
# it was a black chasm, and where the hand is concave -- the notch
# between thumb and palm -- two of those chasms met and cut the thumb
# off. It still separates every finger from the field; it no longer
# punches holes in the piece.
for y in range(D.PH):
    for x in range(D.CW):
        if pval[y][x] is None:
            continue
        hit = None
        for dy in range(-3, 2):
            for dx in range(-3, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < D.CW and 0 <= ny < D.PH) \
                        or mask[ny][nx] != D.HAND:
                    continue
                dd = max(abs(dx), abs(dy))
                cast = dx <= 0 and dy <= 0
                if dd <= (3 if cast else 1):
                    v = (0.17 + 0.12 * (dd - 1)) if cast else 0.33
                    hit = v if hit is None else min(hit, v)
        if hit is not None:
            pval[y][x] = min(pval[y][x], hit)

# bevel: pane touching a crack or the hole rim from its up-light side
# takes the bright fracture lip.
for y in range(D.PH):
    for x in range(D.CW):
        if pval[y][x] is None:
            continue
        for ox, oy, amt in ((1, 0, 0.30), (0, 1, 0.26), (1, 1, 0.20),
                            (-1, 0, -0.22), (0, -1, -0.18)):
            nx, ny = x + ox, y + oy
            if 0 <= nx < D.CW and 0 <= ny < D.PH and mask[ny][nx] == D.VOID:
                pval[y][x] = min(0.99, max(0.18, pval[y][x] + amt))


def fracture(xi, yi, k):
    if not (0 <= xi < D.CW and 0 <= yi < D.PH) or pval[yi][xi] is None:
        return
    pval[yi][xi] = 0.02
    lx, ly = xi - 1, yi - 1
    if k % 3 and 0 <= lx < D.CW and 0 <= ly < D.PH and pval[ly][lx] is not None:
        pval[ly][lx] = 0.95


RIM = 22.0
for k, a in enumerate(seeds):
    r = RIM
    while r < 150:
        r += 0.5
        aa = a + 0.10 * math.sin(r / 11.0 + k) + 0.04 * math.sin(r / 3.7)
        xi = int(round(BREAK[0] + math.cos(aa) * r))
        yi = int(round(BREAK[1] + math.sin(aa) * r))
        if not (0 <= xi < D.CW and 0 <= yi < D.PH) or in_bar(xi, yi):
            break
        fracture(xi, yi, int(r * 2))

for ri, (rad, a0, a1) in enumerate(((31, -3.05, -1.75), (44, -1.30, 0.55),
                                    (38, 1.35, 2.70), (57, -2.85, -2.05))):
    steps = int((a1 - a0) * rad * 2)
    for i in range(steps + 1):
        aa = a0 + (a1 - a0) * i / steps
        rr = rad + 2.2 * math.sin(aa * 3.1 + ri)
        xi = int(round(BREAK[0] + math.cos(aa) * rr))
        yi = int(round(BREAK[1] + math.sin(aa) * rr))
        if not (0 <= xi < D.CW and 0 <= yi < D.PH) or in_bar(xi, yi):
            continue
        fracture(xi, yi, i)

# dither 0.01, not 0.05. The old field leaned on ordered dither to look
# busy; this one is a gradient, and a gradient wants its steps clean. The
# jitter is left just wide enough to keep a tier boundary from landing as
# a single hard scanline.
np_ = D.paint(mask, D.PANE, pval, (0, 4, 12), dither=0.01)

# ======================================================================
# defect 3 -- the void
# ======================================================================
# Not "texture to fill it". The only thing really inside a hole punched
# through a pane is the DEPTH of the opening, and depth has a shape:
#
#   - the reveal. Close to the broken rim you are still seeing the near
#     side of the opening, which catches what the front source spills
#     past the glass; the further in from any rim, the less of that
#     reaches, so value falls off with distance from the rim. This is
#     what fills the two lobes -- each is ~20px across, so the falloff
#     spans them exactly.
#   - the pool. The source is up-LEFT and in front, so the light that
#     gets through lands on the upper-left of what is behind and dies
#     toward the bottom-right. The left lobe is therefore lighter than
#     the right one, and both grade. Asymmetric because the light is.
#
# Top value 0.36 against the pane's 0.52 floor: the void is still the
# darkest region in the piece by a wide margin, every cell of it is dim
# blue on black, and the hole keeps reading as a hole.
rim_d = [[0] * D.CW for _ in range(D.PH)]
for y in range(D.PH):
    for x in range(D.CW):
        if not hole[y][x]:
            continue
        best = 14
        for ny in range(max(0, y - 14), min(D.PH, y + 15)):
            for nx in range(max(0, x - 14), min(D.CW, x + 15)):
                if not hole[ny][nx]:
                    best = min(best, abs(x - nx) + abs(y - ny))
        rim_d[y][x] = best

vval = [[None] * D.CW for _ in range(D.PH)]
for y in range(D.PH):
    for x in range(D.CW):
        if not hole[y][x]:
            continue
        reveal = math.exp(-(rim_d[y][x] / 5.5) ** 2)
        u = (x - 9) * 0.62 + (y - 52) * 0.78          # down-light from the rim
        pool = math.exp(-(u / 34.0) ** 2)
        vval[y][x] = 0.035 + 0.20 * reveal + 0.13 * reveal * pool
nv = D.paint(mask, D.VOID, vval, (0, 4, 8), dither=0.0)

# ======================================================================
# credit block -- pass 3 verbatim
# ======================================================================
data = D.ct.load_canvas(D.W, D.SLUG)
EXTRA = 6
data["pixels"] += [[0] * D.CW for _ in range(EXTRA * 2)]
data["h_cells"] += EXTRA
data["ph"] += EXTRA * 2
D.ct.save_canvas(D.W, D.SLUG, data)

base = D.CH
D.ct.fill_px(D.W, D.SLUG, 0, base * 2 + 2, D.CW, 1, 8)
D.ct.fill_px(D.W, D.SLUG, 0, (base + 5) * 2, D.CW, 1, 8)


def centred(row, s, fg):
    D.ct.text(D.W, D.SLUG, (D.CW - len(s)) // 2, row, s, fg, 0)


centred(base + 2, "opus / AGENTSCII", 15)
centred(base + 3, "CONTACT", 14)
centred(base + 4, "2026-09-24", 7)

D.ct.save_ans(D.W, D.SLUG, "scratch/duo2.ans", title=None, add_sig=False)
print("hand", nh, "pane", np_, "void", nv)
print(D.ct.metrics(D.W, D.SLUG))
