#!/usr/bin/env python3
# One-shot patch: replace draw_hand() in make_reach.py with a version whose
# fingers read as DISTINCT digits (rounded tips + 1-cell gaps) instead of fusing
# into one uneven block. Palm stays solid for mass; wrist stays short.
import io, re

SRC = "scratch/make_reach.py"
with open(SRC, encoding="utf-8") as f:
    src = f.read()

# new function body (4-space indent throughout -- clean, no mixed tabs/spaces)
NEW = '''def draw_hand(p, cx, tip_y, base_y, body=WHITE, glow=CY, through=False):
    """A compact reaching hand with real silhouette weight. The eye must read
    HAND, not ticks: four DISTINCT digits (rounded tips, a 1-cell gap between
    each) fanned in an arc, a solid palm for mass, a short wrist. `through`
    adds a bright glow halo at the fingertips -- the moment of breaking through."""
    palm_top = tip_y + 13                # palm sits just below the tallest fingertip
    FW = 2                               # finger width -- thin enough to read as digits
    # -- fingers: distinct rounded bars, fanned in an arc, gap between each --
    for dx, flen in FINGERS:
        x0 = cx + dx - FW // 2
        top = tip_y + (14 - flen)        # shorter fingers start lower -> shallow fan
        for y in range(top, palm_top + 3):
            for w in range(FW):
                p.set(x0 + w, y, '\\u2588', body, BLACK)
        # rounded tip cap: a single wider cell one row above the bar top
        p.set(cx + dx - 1, top - 1, '\\u2593', body, BLACK)
        p.set(cx + dx,     top - 1, '\\u2588', body, BLACK)
        p.set(cx + dx + 1, top - 1, '\\u2593', body, BLACK)
    # -- thumb: angled off the right side of the palm --
    for i in range(THUMB_LEN):
        x = cx + THUMB_DX - i // 3
        y = palm_top - 4 + i
        p.set(x, y, '\\u2588', body, BLACK)
        if i % 2 == 0:
            p.set(x + 1, y, '\\u2588', body, BLACK)
    # -- palm: a filled rounded block (the mass that makes it read as a hand) --
    pw = 16
    for dy in range(0, 11):
        y = palm_top + dy
        half = pw // 2 - abs(dy - 5) // 2          # taper top and bottom into knuckles/wrist
        if half < 4:
            half = 4
        for dx in range(-half, half + 1):
            p.set(cx + dx, y, '\\u2588', body, BLACK)
    # -- wrist: a SHORT taper down to base_y (never a long thin tail) --
    wrist_top = palm_top + 11
    for dy in range(0, max(0, base_y - wrist_top)):
        y = wrist_top + dy
        half = max(3, 5 - dy // 4)
        for dx in range(-half, half + 1):
            p.set(cx + dx, y, '\\u2588', body, BLACK)
    # -- fingertip glow (only at breakthrough): light bleeding out the tips --
    if through:
        for dx, flen in FINGERS:
            top = tip_y + (14 - flen)
            for dy in range(-3, 0):
                p.set(cx + dx,     top + dy, '\\u2588', glow, BLACK)
                if abs(dy) > 1:
                    p.set(cx + dx - 1, top + dy, '\\u2593', glow, BLACK)
                    p.set(cx + dx + 1, top + dy, '\\u2593', glow, BLACK)
            p.set(cx + dx,     top - 4, '\\u2588', WHITE, BLACK)       # white-hot spark
        # a faint bleed halo just above the whole fingertip line
        for dx in range(-7, 8):
            p.set(cx + dx, tip_y - 5, '\\u2591', glow, BLACK)
'''

# also widen FINGERS spread slightly so the fan is more legible (pinky..index)
NEW_FINGERS = '''FINGERS = [       # (center dx from hand center, length) -- pinky..index
      (-7, 9),
      (-3, 13),
      (+3, 14),
      (+7, 10),
]'''

# replace the FINGERS block
src2 = re.sub(r"FINGERS = \[.*?\]", NEW_FINGERS, src, count=1, flags=re.S)
assert src2 != src, "FINGERS block not found/replaced"

# replace draw_hand: from 'def draw_hand(' up to (but not including) the blank line
# before '# ---- the WALL'
start = src2.index("def draw_hand(")
end_marker = "\n# ---- the WALL"
end = src2.index(end_marker, start)
src3 = src2[:start] + NEW + "\n" + src2[end+1:]

with open(SRC, "w", encoding="utf-8") as f:
    f.write(src3)
print("patched draw_hand + FINGERS in", SRC)
