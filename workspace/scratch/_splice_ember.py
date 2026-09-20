import io
src = open("_emberwatch_v2.py", encoding="utf-8").read()

# --- my two new passes, left-half only (inserted before MIRROR) --------------
new_passes = r'''
# ---- P3c: SECOND SPARK TIER -- the "escapees" carried up by the draft --------
# A second rising scatter that starts higher (already partway up the column), climbs
# further into the void, and is sparser + dimmer than tier 1. This deepens the rising-
# spark-lattice primitive from ONE wave to TWO: heat doesn't just rise once, it keeps
# escaping upward in a second, thinner draft -- the warm counter to CRYO's single outward
# frost fracture. Left half only -> mirror keeps it symmetric.
random.seed(SEED + 11)
def spark_tier2():
    n = 16
    for i in range(n):
        x0 = CX + random.uniform(-4.5, 4.5)       # spawn a bit wider than tier 1 (already scattered)
        y0 = TIP - random.uniform(2.0, 7.0)       # start HIGHER up the column, not at the tip
        reach = random.uniform(10.0, 18.0)        # climbs further into the void
        drift = random.uniform(-3.5, 3.5)         # more wander -- these are loose embers
        phase = random.uniform(0.0, 6.28)
        freq = random.uniform(0.5, 1.2)
        for s in range(int(reach * 2)):
            t = s / (reach * 2.0)                 # 0 at spawn -> 1 at top of climb
            yy = y0 - reach * t                   # rising = decreasing y
            xx = x0 + drift * math.sin(t * 6.28 * freq + phase) * (0.5 + t)
            ix, iy = int(round(xx)), int(round(yy))
            if not (0 <= ix < W and 0 <= iy < H):
                continue
            Lv = 1.0 - t                          # cools as it climbs: white -> amber -> dim red
            ch, fg = warm_shade(Lv * 0.8 + 0.05)  # slightly dimmer overall than tier 1 (farther up)
            if random.random() < (0.6 - t * 0.45):# sparser than tier 1 -- a thin escape, not a column
                cv.set(ix, iy, ch, fg, 0)

spark_tier2()

# ---- P4e: EMBER-GLOW BLOOM ON THE GROUND -- the fire lights the earth --------
# A radial warm pool of light radiating OUTWARD from the fire base across the scorched
# ground -- the downward counterpart to P4c's upward ambient halo. So the fire reads as
# illuminating MORE of the scene (the ground it sits on), not just a colored shape on black.
# Density AND hue both track distance from the fire core: hot white/amber near the base,
# cooling to dim red at the pool's edge. Left half only -> mirror keeps it symmetric.
random.seed(SEED + 13)
for y in range(37, H):
    for x in range(MID):
        d = math.hypot(x - CX, y - (BASE - 1))     # distance from the fire base
        if d <= 20.0:
            fall = 1.0 - d / 20.0                  # 1 at base -> 0 at pool edge
            dens = 0.30 * fall                     # dense near the fire, thinning outward
            if random.random() < dens:
                Lv = max(0.05, fall)              # warm light value tracks the falloff
                ch, fg = warm_shade(Lv)
                cv.set(x, y, ch, fg, 0)

'''

marker = "# ---- MIRROR: copy the left half to the right for a symmetric bonfire --------"
assert src.count(marker) == 1, "mirror marker not unique"
src = src.replace(marker, new_passes + marker)

# joint v2 title + handles
src = src.replace('write_ans("scratch/_emberwatch.ans", out, title="EMBERWATCH v1.0", handles="raze")',
                  'write_ans("scratch/_emberwatch_v2.ans", out, title="EMBERWATCH v2.0", handles="raze / hollis")')

# update the header comment to note this is the joint extension
src = src.replace("# _emberwatch.py -- raze solo. EMBERWATCH // \"the fire that keeps the dark at bay.\"",
                  "# _emberwatch_v2.py -- JOINT (raze + hollis). EMBERWATCH v2.0 // \"the fire that keeps the dark at bay.\"\n# EXTENSION OF SHIPPED pack44 v1.0: raze adds a 2nd rising spark tier (P3c) + an ember-glow bloom on the\n# ground (P4e); hollis's pass = wind-lean to the flame column so the whole set reads as one night.")

open("_emberwatch_v2.py", "w", encoding="utf-8").write(src)
print("spliced OK")
