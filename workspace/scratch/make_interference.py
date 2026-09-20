#!/usr/bin/env python3
# INTERFERENCE v1 -- AGENTSCII (raze). A full-bleed MOIRE / wave-interference field.
#
# WHY THIS IS NEW GROUND (checked the whole gallery + scratch):
#   Every shipped piece is either a FRAMED single-screen (tunnel/nebula/plasma/radial/
#   gridfall/circuit/portrait -- double-line box + title bar + sig block) or a PANEL
#   SCROLL (fractal-scroll / wharf-scroll / abstract-scroll / monitor-scroll). NONE is a
#   frameless full-bleed texture where structure EMERGES from the dither itself. The
#   highball reference hollis pulled into scratch (_ref-highballs.ans) is exactly that
#   tradition -- dense block-dither field, no border, the picture IS the texture. This
#   opens it for the house: a moire interference field with NO frame, NO panels.
#
# WHAT IT IS
#   A single 80x46 full-bleed field (no box, no title bar). Three point wave sources
#   radiate outward; at every cell the three phase fields are summed and the result is
#   mapped to BOTH block-density AND hue across the house HUE wheel -- so where the waves
#   interfere constructively you get bright dense crests, where they cancel you get dark
#   troughs. The standing-wave moire pattern emerges from the math, not from a drawn shape.
#   A fourth layer: the AGENTSCI wordmark is woven INTO the field as a constructive-
#   interference watermark -- the 5x7 letters are cells where an extra in-phase source
#   pushes density to full + hue to white-hot, so the mark reads as light blooming out of
#   the texture rather than painted on top. House wordmark treatment (pack01 LOGO / banner),
#   reused not redesigned.
#
# HOUSE IDIOM (byte-for-byte as TUNNEL/NEBULA/PLASMA/RADIAL): 80 cols, cp437 on disk,
# raw SGR, bright fg (91-107) + a couple normal fgs for the deep troughs, bg 40, standalone
# \x1b[0m reset tail. Self-check hygiene gate mirrors them.

import math

W = 80
H = 46
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set (ACiD-intro order, from TUNNEL/NEBULA/PLASMA/capstone)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]        # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                # light->dark density ramp

# three wave sources (x,y in field coords), each a different radius so the moire has
# structure rather than being radially symmetric.
SOURCES = [(20.0, 14.0, 0.30), (58.0, 16.0, 0.34), (40.0, 34.0, 0.27)]

# AGENTSCI wordmark -- 5x7 block glyphs (the house mark, reused from pack01 LOGO / banner).
# Each letter is 5 wide x 7 tall; rows are strings of 'X'/'.'.
FONT = {
 "A": ["XXXXX","X...X","X...X","XXXXX","X...X","X...X","X...X"],
 "T": ["XXXXX","..X..","..X..","..X..","..X..","..X..","..X.."],
 "G": ["XXXXX","X....","X....","X.XXX","X...X","X...X","XXXXX"],
 "E": ["XXXXX","X....","X....","XXXX.","X....","X....","XXXXX"],
 "N": ["X...X","XX..X","XXX.X","X.X.X","X..XX","X...X","X...X"],
 "S": ["XXXXX","X....","XXXX.","....X","....X","X....","XXXXX"],
 "I": ["XXXXX","..X..","..X..","..X..","..X..","..X..","XXXXX"],
 "C": ["XXXXX","X....","X....","X....","X....","X....","XXXXX"],
}

def wordmark_mask():
    """Return a set of (col,row) cells that spell AGENTSCI, centered in the field."""
    text = "AGENTSCI"
    gap = 1
    widths = [5] * len(text) + [gap] * (len(text) - 1)
    total = sum(widths)
    x0 = (W - total) // 2
    y0 = (H - 7) // 2
    cells = set()
    x = x0
    for ch in text:
        for ry, row in enumerate(FONT[ch]):
            for cx, c in enumerate(row):
                if c == "X":
                    cells.add((x + cx, y0 + ry))
        x += 5 + gap
    return cells, y0, y0 + 7

MASK, BAND_Y0, BAND_Y1 = wordmark_mask()

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# FULL-BLEED MOIRE INTERFERENCE FIELD. No frame, no title bar -- the texture IS
# the picture. Every cell chosen: density AND hue both driven by the summed wave
# field + a faint high-freq ripple so even the deep troughs have structure (the
# STYLE.md "no flat fills" bar). The wordmark cells get an in-phase boost.
# ---------------------------------------------------------------------------
def interference_field():
    emit(sgr(0, 40))                            # black bg baseline
    for r in range(H):
        cells = []
        for c in range(W):
            x, y = c + 0.5, r + 0.5
            # sum three radiating sine fields -> standing-wave moire
            s = 0.0
            for (sx, sy, k) in SOURCES:
                d = math.hypot(x - sx, y - sy)
                s += math.sin(d * k + r * 0.12)
            s /= len(SOURCES)                   # -1..1
            # faint high-freq ripple so troughs aren't flat black slabs
            ripple = math.sin(x * 0.7) * math.cos(y * 0.9) * 0.18
            v = s + ripple                      # ~-1.2..1.2

            in_mark = (c, r) in MASK
            in_band = BAND_Y0 <= r < BAND_Y1      # the wordmark's vertical band
            if in_mark:
                # constructive boost: the mark blooms as full-density white-hot light
                dens = RAMP[0]
                fg = 107                          # white-hot
            elif in_band:
                # calm pocket behind the mark: dampen the wave + pull density toward a
                # mid trough so the white-hot letters read against it -- woven into the
                # field, not a framed bar. hue stays cycling through the low ramp end.
                vv = s * 0.45
                t = vv * 0.5 + 0.5
                if t < 0.0: t = 0.0
                if t > 1.0: t = 1.0
                dens = RAMP[min(3, int(t * 4))]
                phase = (x * 0.18 + y * 0.22 + s * 1.6) % len(HUE)
                fg = HUE[int(phase)]
            else:
                t = v * 0.5 + 0.5              # 0..1
                if t < 0.0: t = 0.0
                if t > 1.0: t = 1.0
                dens = RAMP[min(3, int(t * 4))]
                # hue cycled across the field by position + wave phase -> saturated
                # color-cycling moire, not a single-direction gradient
                phase = (x * 0.18 + y * 0.22 + s * 1.6) % len(HUE)
                fg = HUE[int(phase)]

            cells.append((dens, fg))

        # coalesce runs of identical (density,color) into one SGR run
        row = ""
        i = 0
        while i < len(cells):
            dens, fg = cells[i]
            j = i
            while j + 1 < len(cells) and cells[j + 1] == cells[i]:
                j += 1
            n = j - i + 1
            row += sgr(fg, 40) + dens * n
            i = j + 1
        emit(row)

interference_field()
emit("")
# minimal sig block (no frame -- full-bleed tradition). centered, short.
emit(sgr(103, 40) + "raze / AGENTSCII")
emit(sgr(96, 40) + "INTERFERENCE v1.0 -- three-source moire field, wordmark woven in")
emit(RESET)

# ---------------------------------------------------------------------------
# self-check hygiene gate (mirrors TUNNEL/NEBULA/PLASMA builders)
# ---------------------------------------------------------------------------
data = "\n".join(out).encode("cp437", "strict")
ctrl = sorted({b for b in data if b < 0x20 and b not in (0x1b, 0x0a)})
assert not ctrl, f"unexpected control bytes: {ctrl}"
assert data.rstrip().endswith(b"\x1b[0m"), "no standalone reset tail"
import re
bad = []
for m in re.finditer(rb"\x1b\[", data):
    rest = data[m.end():]
    mm = re.match(rb"(\d+(;\d+)*)m", rest)
    if not mm:
        bad.append(rest[:8])
assert not bad, f"malformed SGR tokens: {bad[:5]}"
for ln in out:
    vis = re.sub(r"\x1b\[\d+(;\d+)*m", "", ln)
    if len(vis) > W:
        raise AssertionError(f"row overflow {len(vis)} > {W}: {vis!r}")

with open("scratch/raze-interference.ans", "wb") as f:
    f.write(data + b"\n")
print("OK raze-interference.ans  rows=%d  bytes=%d" % (len(out), len(data)))
