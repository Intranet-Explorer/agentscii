#!/usr/bin/env python3
# DEEPZOOM v1.0 -- AGENTSCII (raze).
#
# A DEEP-ZOOM INTERIOR of a JULIA set -- the "tunnel" view we've NEVER rendered.
# FRACTAL = full-plane Mandelbrot silhouette; JULIA = full-plane dendrite orbit.
# Both were MAXIT-limited wide views where the black core is just "the inside."
# DEEPZOOM pushes the opposite direction: a tight window INSIDE an interesting
# Julia c, at very high MAXIT (512), so the escape-time bands resolve into fine
# concentric filaments -- the classic ACiD fractal-tunnel idiom. The interior is no
# longer a void; it's a dense rainbow of nested bands with a black core at center.
#
# Same ACiD idiom (math set quantized to 16 colors + block-dithered), same house
# conventions byte-for-byte as FRACTAL/JULIA/PLASMA: 80 cols, cp437 on disk, raw
# SGR, bright fg (91-107), double-line frame + title bar, sig block "raze / AGENTSCII"
# + version line, standalone \x1b[0m reset tail. Self-check hygiene gate mirrors them.
#
# Technique: Julia z->z^2+c over a TIGHT window centered on the seed's interesting
# interior region. Smooth escape time (log-log) so bands don't band; hue driven by
# RAW smooth-iteration count cycled fast across the house HUE wheel so every nested
# ring gets a different color -> the rainbow-tunnel look, not flat far-field. Density
# from a high-frequency term for block-dithered shading at the band boundaries.

import math

W = 80
H = 46                         # full single-screen field (matches FRACTAL/JULIA/PLASMA)
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house saturated bright fg set, ACiD-intro order (from FRACTAL/JULIA/PLASMA/capstone)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]       # mag red yel grn cya blu wht amb
RAMP = "\u2588\u2593\u2592\u2591"               # light->dark density ramp

out = []
def emit(line=""): out.append(line)

# ---------------------------------------------------------------------------
# DEEP-ZOOM JULIA INTERIOR.
# c = -0.7269 + 0.1889 i -- the same dendrite seed as JULIA, but we zoom TIGHT
# into its interior so the fine nested escape bands resolve at high MAXIT. The
# window is small enough that most cells take many iterations before escaping ->
# dense rainbow filaments instead of a flat far-field sea.
# ---------------------------------------------------------------------------
def deepzoom_field():
    emit(sgr(0, 100))                           # black bg baseline
    CR, CI = -0.7269, 0.1889                    # the fixed seed (dendrite interior)
    CX, CY = -0.50, 0.30                         # tight window center (boundary-band region)
    RADIUS = 0.09                                # half-window -> deep zoom
    RE_MIN, RE_MAX = CX - RADIUS, CX + RADIUS
    IM_MIN, IM_MAX = CY - RADIUS, CY + RADIUS
    MAXIT = 512                                 # high cap -> fine nested bands resolve
    SMOOTH_MAX = 480.0                          # normalize smooth-iter into [0,1]

    for r in range(H):
        zi0 = IM_MIN + (IM_MAX - IM_MIN) * (r + 0.5) / H
        cells = []
        for c in range(W):
            zr0 = RE_MIN + (RE_MAX - RE_MIN) * (c + 0.5) / W
            zr, zi = zr0, zi0
            it = 0
            while zr * zr + zi * zi <= 4.0 and it < MAXIT:
                zr2, zi2 = zr * zr, zi * zi
                zr = zr2 - zi2 + CR
                zi = 2.0 * zr * zi + CI
                it += 1
            if it >= MAXIT:
                # still inside the set after MAXIT -> black core (the tunnel center)
                cells.append((' ', 0))
                continue
            # smooth escape time
            mag = math.sqrt(zr * zr + zi * zi)
            mu = it + 1.0 - math.log(math.log(mag) / math.log(2.0)) / math.log(2.0)
            t = mu / SMOOTH_MAX
            if t < 0.0: t = 0.0
            if t > 1.0: t = 1.0
            # HUE driven by RAW smooth-iteration count (mu), cycled fast, so every
            # nested ring gets a different wheel color -> rainbow-tunnel look across
            # the whole field. High-MAXIT cells land on real hues, not flat far-field.
            phase = mu * 0.62 + math.sin(t * 9.0) * 0.4
            fg = HUE[int(phase) % len(HUE)]
            # density from a high-frequency term -> dithered shading at band edges,
            # the ACiD block-dither look rather than flat color bands.
            dp = math.sin(mu * 1.3 + t * 7.0) * 0.5 + 0.5
            ch = RAMP[min(3, int(dp * 4))]
            cells.append((ch, fg))

        # compress runs of identical (char,fg) into one SGR emit
        row = ""; cur = None
        for ch, fg in cells:
            code = str(fg)
            if code != cur:
                row += sgr(int(code)); cur = code
            row += ch
        emit(row)

# ---------------------------------------------------------------------------
# DOUBLE-LINE FRAME + title bar + signature block (house format).
# ---------------------------------------------------------------------------
def frame_top():
    emit(sgr(105, 40) + "\u2554" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u2557")

def frame_bottom():
    emit(sgr(105, 40) + "\u255a" + sgr(104, 40) + "\u2550" * (W - 2) + sgr(105, 40) + "\u255d")

def title_bar(text, fg):
    pad = (W - len(text)) // 2
    emit(sgr(104, 40) + " " * pad + sgr(fg, 40) + text + sgr(104, 40) + " " * (W - pad - len(text)))

# ---------------------------------------------------------------------------
# ASSEMBLE: title bar -> deep-zoom field -> signature block.
# ---------------------------------------------------------------------------
frame_top()
title_bar("DEEPZOOM // JULIA INTERIOR TUNNEL", 96)      # bright cyan title
emit()
deepzoom_field()
emit()
frame_bottom()

sig = "raze / AGENTSCII"
pad = (W - len(sig)) // 2
emit(sgr(104, 40) + " " * pad + sgr(97, 40) + sig + sgr(104, 40) + " " * (W - pad - len(sig)))
title = "DEEPZOOM v1.0 -- julia interior, MAXIT 512, 16-color quantized"
pad2 = (W - len(title)) // 2
emit(sgr(104, 40) + " " * pad2 + sgr(96, 40) + title + sgr(104, 40) + " " * (W - pad2 - len(title)))

text = "\n".join(out) + "\n" + RESET
with open("scratch/raze-deepzoom.ans", "w", encoding="cp437") as f:
    f.write(text)

# ---- self-checks (mirror FRACTAL/JULIA hygiene gate) ----
import re
data = text.encode("utf-8")
ctrl = sorted({b for b in data if b < 32 or b == 127})
print("control bytes:", [hex(b) for b in ctrl], "(expect 0x1b,0x0a only)")
try:
    ok = text.encode("cp437").decode("cp437") == text
except Exception as e:
    ok = False
print("cp437 round-trip:", "OK" if ok else "FAIL")
sgr_groups = re.findall(r"\x1b\[([0-9;]*)m", text)
fgs, bgs, invalid = set(), set(), []
for grp in sgr_groups:
    if grp == "":
        continue
    for p in grp.split(";"):
        n = int(p)
        if 30 <= n <= 37 or 90 <= n <= 107: fgs.add(n)
        elif 40 <= n <= 47 or 100 <= n <= 107: bgs.add(n)
        else: invalid.append(n)
print("distinct SGR groups:", len(sgr_groups), "invalid params:", sorted(set(invalid)))
print("bright fg present (98-105):", sorted(f for f in fgs if 98 <= f <= 105))
lines = text.split("\n")
non80 = [(i, len(re.sub(r"\x1b\[[0-9;]*m", "", l))) for i, l in enumerate(lines[:-1])
         if len(re.sub(r"\x1b\[[0-9;]*m", "", l)) != 80]
print("rows:", len(lines), "non-80 content rows (excl last):", len(non80), non80[:6])
print("ends on standalone reset:", text.endswith("\x1b[0m"))
