import sys; sys.path.insert(0, "scratch")
from halfblock import HalfBlockCanvas

# Proof of concept: an orb with a lit gradient + a constructed eye inside it.
W = 40; H = 20
cv = HalfBlockCanvas(W, H, bg=0)
cx, cy = W//2, H*2//2   # pixel-space center (square units)

# lit sphere: fill circle with a light gradient from upper-left
import math
r = min(W, H*2)//2 - 2
for py in range(cv.ph):
    for px in range(cv.w):
        d = math.hypot(px-cx, py-cy)
        if d <= r:
            # light from upper-left
            L = max(0.0, 1.0 - (px- (cx-r*0.4))/r) * 0.5 + max(0.0,1.0-(py-(cy-r*0.4))/r)*0.5
            L = min(1.0, L)
            # amber->white hot on lit side, deep red shadow
            if L > 0.85: col=15
            elif L>0.6: col=11
            elif L>0.35: col=9
            else: col=8
            cv.set_pixel(px,py,col)

# a constructed eye in the upper area using half-block resolution
eyex, eyey = cx-4, cy-6
cv.fill_circle(eyex, eyey, 5, 15)        # sclera white
cv.fill_circle(eyex+1, eyey+1, 3, 9)     # iris amber
cv.fill_circle(eyex+1, eyey+1, 1.4, 4)   # pupil blue
cv.set_pixel(eyex-0, eyey-2, 15)         # glint

rows = cv.render()
out = "\n".join(rows) + "\x1b[0m\n"
open("scratch/_hb_test.ans","w").write(out)
print("wrote _hb_test.ans", len(rows), "rows")
