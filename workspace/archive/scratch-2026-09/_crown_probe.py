import math
MID = 40; PH = 80
def in_cranium(px, py): return math.hypot(px - MID, py - 52) <= 27
def _tri(px, py, ax, ay, by, bx0, bx1):
    if py < ay or py > by: return False
    t = (py - ay) / max(1e-9, (by - ay))
    x0 = ax + (bx0 - ax) * t; x1 = ax + (bx1 - ax) * t
    lo, hi = min(x0, x1), max(x0, x1)
    return lo <= px <= hi

# 5-point crown: tall center, two mid, two short outer. Deep V-notches between them
# so no single row has a long contiguous run. Each spike is narrow at its base.
def in_crown(px, py):
    # central tall spike (narrow base)
    if _tri(px, py, MID, 2, 34, MID - 7, MID + 7): return True
    # two mid spikes
    if _tri(px, py, MID - 16, 8, 34, MID - 23, MID - 9): return True
    if _tri(px, py, MID + 16, 8, 34, MID + 9, MID + 23): return True
    # two short outer spikes
    if _tri(px, py, MID - 30, 16, 34, MID - 35, MID - 25): return True
    if _tri(px, py, MID + 30, 16, 34, MID + 25, MID + 35): return True
    return False

def in_brow(px, py):
    if not (40 <= py <= 47): return False
    a = abs(px - MID)
    if a > 25: return False
    return py >= 40 + (a / 25.0) * 3.0

def in_faceplate(px, py):
    if not (58 <= py <= 90): return False
    hw = 18.0 - (18.0 - 12.0) * (py - 58) / 32.0
    return abs(px - MID) <= hw

def part(px, py):
    if in_crown(px, py): return 7
    if in_brow(px, py): return 6
    if in_faceplate(px, py): return 2
    if math.hypot(px - MID, py - 52) <= 27: return 1
    return 0

from collections import Counter
total = Counter(); interior = Counter()
worst = 0; worstrow = None
for py in range(PH):
    cur = 0
    for px in range(80):
        p = part(px, py)
        if p == 7 and not (part(px, py-1) == 7 or part(px, py+1) == 7):
            pass
        # track crown-only contiguous runs per row
        is_crown_only = (p == 7 and part(px, py+1) != 7)
        if p == 7:
            total[7] += 1
            up = part(px, py-1); dn = part(px, py+1)
            if up == 7 or dn == 7: interior[7] += 1
    # max contiguous crown-only run in this row (bottom edge of crown)
for py in range(PH):
    cur = 0; best = 0
    for px in range(80):
        c = part(px, py) == 7 and part(px, py+1) != 7   # bottom-edge crown cell
        if c: cur += 1; best = max(best, cur)
        else: cur = 0
    if best > worst: worst = best; worstrow = py

print(f"5-point crown: max bottom-edge run={worst} at row {worstrow}")
tot = sum(total.values()); int_ = sum(interior.values())
print(f"TOTAL subject cells={tot} shaded-interior~{int_}  (v5 was 2891/2871)")
