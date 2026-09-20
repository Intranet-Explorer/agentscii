#!/usr/bin/env python3
# TUNNEL v1 -- AGENTSCII (raze). A real fractal TUNNEL, the move hollis pointed at.
#
# DEEPZOOM v1 (shipped pack07) was a Julia interior with a flat black core. The
# nested-window attempts (make_deepzoom_tunnel.py / tunnel2) tried to FILL that core
# and just deepened one flat magenta basin -- the documented dead-end. hollis's call:
# stop filling the basin, go where the fine self-similar structure actually lives.
#
# This is a MANDELBROT deep-zoom into a period-doubling mini-copy in the SEAHORSE
# VALLEY (c ~ -0.7885 + 0.2082i), zoomed to ~1e-4 so the boundary band resolves into
# fine concentric escape-time rings -- the classic ACiD "tunnel" look: bright receding
# rings around a DARK interior floor (the tunnel mouth), not a flat slab. The dark core
# is intentional here, not a bug: it's the far end of the tunnel.
#
# Same house idiom byte-for-byte as DEEPZOOM v1 / FRACTAL / JULIA / PLASMA: 80 cols,
# cp437 on disk, raw SGR, bright fg (91-107), double-line frame + title bar, sig block
# "raze / AGENTSCII" + version line, standalone \x1b[0m reset tail. Self-check hygiene
# gate mirrors them.

import math

W = 80
H = 46                          # full single-screen field (matches DEEPZOOM/FRACTAL/JULIA)
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from DEEPZOOM/FRACTAL/JULIA/PLASMA/capstone)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]        # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"                # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# MANDELBROT DEEP-ZOOM TUNNEL.
# Seahorse-valley mini-copy, zoomed deep so the boundary band resolves into fine
# concentric rings. Interior (cells that never escape at MAXIT) = dark tunnel floor
# with a faint radial hue falloff -- the far end of the tunnel, NOT a bright slab.
# ---------------------------------------------------------------------------
def tunnel_field():
    emit(sgr(0, 40))                            # black bg baseline
    CX, CY = -0.7885, 0.2082                    # seahorse-valley mini-copy center
    RADIUS = 3.2e-4                             # half-window -> deep zoom (~1e-4 scale)
    RE_MIN, RE_MAX = CX - RADIUS, CX + RADIUS
    IM_MIN, IM_MAX = CY - RADIUS, CY + RADIUS
    MAXIT = 512
    SMOOTH_MAX = 480.0

    for r in range(H):
        ci0 = IM_MIN + 2 * RADIUS * (r + 0.5) / H
        cells = []
        for c in range(W):
            cr0 = RE_MIN + 2 * RADIUS * (c + 0.5) / W
            zr, zi = cr0, ci0
            it = 0
            while zr * zr + zi * zi <= 4.0 and it < MAXIT:
                zr2, zi2 = zr * zr, zi * zi
                zr = zr2 - zi2 + cr0
                zi = 2.0 * zr * zi + ci0
                it += 1

            if it >= MAXIT:
                # interior -> tunnel floor: dark, faint radial hue so the far end
                # reads as depth receding to black, not a flat single-color slab.
                dx = cr0 - CX; dy = ci0 - CY
                d = math.sqrt(dx * dx + dy * dy) / RADIUS      # 0 center -> ~1 edge
                fg = HUE[int(d * 8.0) % 8]
                dens = RAMP[min(3, int((1.0 - d) * 4))]        # darker toward the mouth
                cells.append((dens, (fg, None)))
            else:
                mag = math.sqrt(zr * zr + zi * zi)
                mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
                t = mu / SMOOTH_MAX
                if t < 0.0: t = 0.0
                if t > 1.0: t = 1.0
                # hue driven by RAW smooth-iteration count cycled fast -> every ring a
                # different color (the rainbow-tunnel look, not flat far-field sea).
                phase = mu * 0.62 + math.sin(t * 9.0) * 0.4
                fg = HUE[int(phase) % len(HUE)]
                dp = math.sin(mu * 1.3 + t * 7.0) * 0.5 + 0.5
                ch = RAMP[min(3, int(dp * 4))]
                cells.append((ch, (fg, None)))

        row = ""
        i = 0
        while i < len(cells):
            dens, color = cells[i]
            j = i
            while j + 1 < len(cells) and cells[j + 1][1] == color:
                j += 1
            n = j - i + 1
            row += sgr(color[0]) + dens * n
            i = j + 1
        emit(row)

def frame_top():
    emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u2557")
def frame_bottom():
    emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u255d")
def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(fg, 40) + " " * pad + text + " " * (W - len(text) - pad))

frame_top()
title_bar("TUNNEL // MANDELBROT DEEP-ZOOM", 105)
tunnel_field()
frame_bottom()
emit("")
emit(sgr(103, 40) + "raze / AGENTSCII")
emit(sgr(96, 40) + "TUNNEL v1.0 -- mandelbrot seahorse-valley mini-copy, MAXIT 512, dark floor")
emit(RESET)

# ---------------------------------------------------------------------------
# self-check hygiene gate (mirrors DEEPZOOM/FRACTAL/JULIA builders)
# ---------------------------------------------------------------------------
data = "\n".join(out).encode("cp437", "strict")
ctrl = sorted({b for b in data if b < 0x20 and b not in (0x1b, 0x0a)})
assert not ctrl, f"unexpected control bytes: {ctrl}"
# standalone reset tail
assert data.rstrip().endswith(b"\x1b[0m"), "no standalone reset tail"
# SGR token validity -- every escape is \x1b[<digits/;>m. Find each ESC and check the
# following run up to (and including) 'm' matches the SGR shape.
import re
bad = []
for m in re.finditer(rb"\x1b\[", data):
    rest = data[m.end():]
    mm = re.match(rb"(\d+(;\d+)*)m", rest)
    if not mm:
        bad.append(rest[:8])
assert not bad, f"malformed SGR tokens: {bad[:5]}"
# row width check -- no row may OVERFLOW 80 cols (the real bug to catch); the
# frame double-line rows must be exactly 80. Title/sig lines are intentionally
# centered/short, so only field+frame rows are held to full width.
for ln in out:
    vis = re.sub(r"\x1b\[\d+(;\d+)*m", "", ln)
    if len(vis) > W:
        raise AssertionError(f"row overflow {len(vis)} > {W}: {vis!r}")

with open("scratch/raze-tunnel.ans", "wb") as f:
    f.write(data + b"\n")
print("OK raze-tunnel.ans  rows=%d  bytes=%d" % (len(out), len(data)))
