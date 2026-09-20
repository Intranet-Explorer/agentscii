#!/usr/bin/env python3
# burningship_tune.py -- search for a better burning-ship window/trap/c.
# Score: want all 8 hues present, moderate black fraction (core depth but not void),
# and high ridge sharpness (variance in the trap-distance field). Print top candidates.

import math

W = 80
H = 46
HUE = [95, 91, 93, 92, 96, 94, 107, 103]

def score(c_re, c_im, re_min, re_max, im_min, im_max, maxit=96, trap_r=0.35):
    hues = set()
    blacks = 0
    total = W * H
    trd_list = []
    for r in range(H):
        zi0 = im_min + (im_max - im_min) * (r + 0.5) / H
        for c in range(W):
            zr0 = re_min + (re_max - re_min) * (c + 0.5) / W
            zr, zi = zr0, zi0
            it = 0
            trapd = 1e9
            while it < maxit:
                nzr = abs(zr*zr - zi*zi) + c_re
                nzi = 2.0 * zr * zi + c_im
                zr, zi = nzr, nzi
                d = math.hypot(zr, zi) - trap_r
                if d < 0.0: d = 0.0
                if d < trapd: trapd = d
                it += 1
                if zr*zr + zi*zi > 4.0:
                    break
            if it >= maxit:
                blacks += 1
                continue
            t = trapd * 6.0
            hues.add(int(t) % len(HUE))
            trd_list.append(trapd)
    bf = blacks / total
    nhue = len(hues)
    # ridge sharpness: coefficient of variation of trap distances
    if trd_list:
        m = sum(trd_list)/len(trd_list)
        var = sum((x-m)**2 for x in trd_list)/len(trd_list)
        cov = (var**0.5)/m if m > 1e-9 else 0
    else:
        cov = 0
    # want nhue high, bf in a sweet spot (~0.15-0.35), cov high
    s = nhue*10 + cov*4 - abs(bf - 0.28)*30
    return s, nhue, round(bf,3), round(cov,3)

# search c and window aspect (keep re/im ~2:1 for char cell)
best = []
for cr in [0.0, 0.25, 0.5, -0.25, 0.75, 0.1, -0.5]:
    for ci in [0.0, 0.5, -0.5, 1.0, -1.0, 0.3, 0.7]:
        # window centered near the action; try a few centers/scales
        for cx, cy, half in [(0.0,0.0,0.6),(0.0,0.5,0.6),(0.25,0.0,0.5),
                             (0.0,0.0,1.0),(0.3,0.3,0.5),(0.0,0.0,0.45)]:
            re_min, re_max = cx-0.6, cx+0.6
            im_min, im_max = cy-half*2, cy+half*2
            s, nhue, bf, cov = score(cr, ci, re_min, re_max, im_min, im_max)
            best.append((s, cr, ci, re_min, re_max, im_min, im_max, nhue, bf, cov))

best.sort(reverse=True)
print("top 12 (score, c_re, c_im, re_min, re_max, im_min, im_max, #hues, blackfrac, cov):")
for b in best[:12]:
    print(f"  {b[0]:7.2f}  c=({b[1]:+.2f},{b[2]:+.2f})  re[{b[3]:+.2f},{b[4]:+.2f}] im[{b[5]:+.2f},{b[6]:+.2f}]  hues={b[7]} bf={b[8]} cov={b[9]}")
