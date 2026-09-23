#!/usr/bin/env python3
# Pass 2 on duo_v2 (regex variant): per-cell cross-section falloff on cap()/joint()
# so tubes round off (bright core, dark edges) instead of banding into stripes.
import re

p = "scratch/_duo_v2.py"
src = open(p, encoding="utf-8").read()

new_cap = '''def cap(Lfn, ramp, x0, y0, x1, y1, halfw):
    """Minkowski-segment shaded surface -- the limb/torso tube. Each cell's light is the
    global field Lfn MODULATED by a cosine cross-section across the tube width: the core
    (|t|~0) catches most light, edges fall into shadow, so a vertical limb rounds off as a
    3D body instead of banding into horizontal stripes."""
    dx, dy = x1 - x0, y1 - y0
    L2 = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L2, dy / L2
    nx, ny = -uy, ux
    for s in range(0, int(L2 * 4), 1):
        px, py = x0 + ux * (s / 4.0), y0 + uy * (s / 4.0)
        for t in range(-int(halfw * 4), int(halfw * 4) + 1):
            ex, ey = px + nx * (t / 4.0), py + ny * (t / 4.0)
            if 0 <= ex < W and 0 <= ey < H:
                u = t / (halfw * 4.0)
                cross = 0.55 + 0.45 * math.cos(u * math.pi / 2.0)
                ch, fg = ramp(Lfn(int(ex), int(ey)) * cross)
                set_cell(cv, int(ex), int(ey), ch, fg, 0)'''

new_joint = '''def joint(Lfn, ramp, cx, cy, r):
    for y in range(int(cy - r), int(cy + r) + 1):
        hw = r * math.sqrt(max(0.0, 1 - ((y - cy) / r) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            u = (x - cx) / (hw or 1.0)
            cross = 0.55 + 0.45 * math.cos(u * math.pi / 2.0)
            ch, fg = ramp(Lfn(int(x), int(y)) * cross)
            set_cell(cv, int(x), int(y), ch, fg, 0)'''

# Replace cap() body: from 'def cap' up to (not incl) 'def joint'
src, n1 = re.subn(r"def cap\(Lfn, ramp, x0, y0, x1, y1, halfw\):.*?(?=\ndef joint)",
                  new_cap + "\n\n", src, count=1, flags=re.S)
# Replace joint() body: from 'def joint' up to (not incl) 'def sentinel'
src, n2 = re.subn(r"def joint\(Lfn, ramp, cx, cy, r\):.*?(?=\ndef sentinel)",
                  new_joint + "\n\n", src, count=1, flags=re.S)

assert n1 == 1 and n2 == 1, f"expected 1+1 replacements, got {n1}+{n2}"
open(p, "w", encoding="utf-8").write(src)
print("patched cap()/joint() with cross-section falloff")
