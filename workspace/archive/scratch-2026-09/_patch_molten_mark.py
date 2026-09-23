#!/usr/bin/env python3
# hollis -- MOLTEN MARK v2 pass on raze's joint base (clean re-run).
import re

src = open("scratch/_molten_mark.py").read()

# --- (a) magma channels rising from pool up to the mark's foot, bridging the gap ---
channel_pass = '''
# ---- MOLTEN CHANNELS (hollis v2): wandering magma ridges rising out of the glow pool
#   up to the mark's foot, so pool + mark read as ONE continuous molten system instead of
#   two disconnected objects. Mirrors FORGE's channel technique; heat cools as it rises. ---
NCH = 5
for ci in range(NCH):
    base_x = (ci + 0.5) * W / NCH
    amp = 3.0 + 2.0 * math.sin(ci * 1.9)              # wander amplitude
    ph = ci * 1.4                                     # phase so channels don't sync
    reach = MARK_TOP + 7                              # climb up to just under the mark's foot
    for y in range(reach, POOL_TOP + 1):
        t = (y - reach) / max(1, POOL_TOP - reach)    # 0 at top -> 1 at pool
        height_decay = t ** 1.3                       # heat cools as it rises
        cx = base_x + amp * math.sin(y * 0.18 + ph) + 1.5 * math.sin(y * 0.06 + ph * 2.0)
        for x in range(W):
            d = abs(x - cx)
            if d > 3.5:
                continue
            h = (1.0 - d / 3.5) * height_decay + 0.10 * (noise(x, y) - 0.5)
            h = max(0.0, min(1.0, h))
            if h < 0.12:
                continue
            fg = warm_fg(h, y * 0.30 + x * 0.08 + ci)
            if h > 0.86 and d < 1.0:
                fg = 15                               # white-hot core at the molten heart
            set_cell(cv, x, y, heat_to_density(h), fg, 0)

'''
anchor = "# ---- EMBER CASCADE"
assert anchor in src, "ember anchor not found"
src = src.replace(anchor, channel_pass + anchor, 1)

# --- (b) replace the random ember scatter with channel-following vertical drifts ---
# match from "random.seed(23)" through the old set_cell line, using a regex on the block
old_block_re = re.compile(
    r"random\.seed\(23\)\n.*?set_cell\(cv, ex, ey, .*?warm_fg\(h, k\*0\.5\), 0\)",
    re.S)
new_ember = '''# EMBER CASCADE (hollis v2): sparse bright embers rising ABOVE the mark along a few
#   vertical drifts / channel centerlines so they read as connected heat rising FROM the
#   mark into void -- not uniform scatter. Mirrors FORGE's channel-following embers.
random.seed(23)
ND = 7
for k in range(120):
    ci = random.randrange(ND)
    base_x = (ci + 0.5) * W / ND
    amp = 3.0 + 2.0 * math.sin(ci * 1.9)
    ph = ci * 1.4
    ey = random.randint(TITLE_Y + 4, MARK_TOP - 1)         # above the crown, into void
    cx = base_x + amp * math.sin(ey * 0.18 + ph) + 1.5 * math.sin(ey * 0.06 + ph * 2.0)
    ex = int(cx + (noise(int(round(cx)), ey) - 0.5) * 3.0)    # jitter along the drift
    if not (0 <= ex < W):
        continue
    h = 0.45 + random.random() * 0.5
    if random.random() < 0.7:                               # sparse, so it reads as embers not a band
        set_cell(cv, ex, ey, "\\u2588" if h > 0.7 else "\\u2593", warm_fg(h, k * 0.5), 0)'''

new_src, n = old_block_re.subn(lambda m: new_ember, src)
assert n == 1, f"expected 1 ember-block match, got {n}"
src = new_src

# bump version string in the sig so v2 is honest about itself (title card text stays "MOLTEN MARK")
src = src.replace('AGENTSCI // MOLTEN MARK v1.0', 'AGENTSCI // MOLTEN MARK v2.0')

open("scratch/_molten_mark.py", "w").write(src)
print("patched _molten_mark.py for v2 OK")
