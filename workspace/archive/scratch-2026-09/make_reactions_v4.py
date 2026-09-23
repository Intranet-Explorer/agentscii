#!/usr/bin/env python3
# REACTIONS v3 -- AGENTSCII (raze). Gray-Scott reaction-diffusion / Turing-pattern field.
#
# WHY NEW GROUND: nothing in the catalog is a REACTION-DIFFUSION system -- two chemicals A/B
# reacting + diffusing at different rates that spontaneously grow organic Turing patterns
# (spots, stripes, mazes, coral). Distinct from noise fields (PLASMA), advection (FLOWFIELD),
# geometric folding (KALEIDOSCOPE/LISSAJOUS), and moire sums (INTERFERENCE). The classic ACiD
# "living" look -- emergent self-organization.
#
# v1/v2 PROBLEM: relaxed to a uniform horizontal-stripe attractor on the coarse 80x46 cell grid.
# Root cause: the natural Turing wavelength is finer than the coarse grid can resolve, so it
# aliases into high-frequency stripes; periodic-x + large D_A/D_B locks horizontal stripes as the
# lowest-energy state.
#
# v3 FIX (numpy): simulate on a FINE grid so the pattern forms at its natural scale, then
# downsample to 80x46 by area-averaging B. Try several well-known regimes and pick the one that
# produces organic structure rather than stripes.

import math
import re
import numpy as np

W = 80
H = 46
SW, SH = 320, 184           # fine simulation grid (4x) -- room for the natural wavelength
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# house wheel (bright, fast-shifting ACiD-Trip craft). mag red yel grn cya blu wht amb
HUE = [95, 91, 93, 92, 96, 94, 107, 103]
RAMP = "\u2588\u2593\u2592\u2591"       # bright->dim density ramp

# Skelton 9-point Laplacian weights
C = 0.2
W_ = 1.0 - 4.0*C

def lap9(arr):
    yp = np.roll(arr, 1, axis=0); ym = np.roll(arr, -1, axis=0)
    xp = np.roll(arr, 1, axis=1); xm = np.roll(arr, -1, axis=1)
    return (W_*(yp+ym+xp+xm) + C*(np.roll(xp,1,axis=0)+np.roll(xp,-1,axis=0)
            +np.roll(xm,1,axis=0)+np.roll(xm,-1,axis=0)) - 4.0*arr)

def simulate(feed, kill, steps, seed, dA=0.2, dB=0.1):
    rng = np.random.default_rng(seed)
    A = np.ones((SH, SW), dtype=np.float64)
    B = np.zeros((SH, SW), dtype=np.float64)
    cy0, cy1 = SH//2 - 5, SH//2 + 6
    cx0, cx1 = SW//2 - 9, SW//2 + 10
    B[cy0:cy1, cx0:cx1] = 1.0
    D_A, D_B = 1.0, 0.5
    DAMP = 0.12                       # implicit-like damping keeps the explicit scheme stable
    for _ in range(steps):
        la = lap9(A); lb = lap9(B)
        react = A*A*B*3.0
        A = A + D_A*DAMP*la - react + feed*(1-A)
        B = B + D_B*DAMP*lb + react - (kill+feed)*B
        np.clip(A, 0.0, 1.0, out=A)
        np.clip(B, 0.0, 1.0, out=B)
    return B

# candidate regimes from the Gray-Scott literature: (name, feed, kill, seed)
REGIMES = [
    ("coral",   0.037, 0.060, 11),
    ("spots",   0.035, 0.065, 11),
    ("mazes",   0.029, 0.057, 11),
    ("worms",   0.046, 0.058, 11),
    ("holes",   0.034, 0.062, 11),
    ("rings",   0.030, 0.062, 11),
]

best = None
DIFF = [ (0.2,0.1), (0.15,0.075), (0.1,0.05), (0.08,0.04) ]
for name, feed, kill, seed in REGIMES:
    for dA, dB in DIFF:
        B = simulate(feed, kill, 600, seed, dA, dB)
    # downsample to 80x46 by area averaging
    sx = SW // W; sy = SH // H
    Bd = B[:sy*H, :sx*W].reshape(H, sy, W, sx).mean(axis=(1,3))
    # score: organic structure = high variance + lots of "edges" (non-trivial), low stripe-ness.
    var = float(Bd.var())
    frac = float((Bd > 0.25).mean())          # fraction of cells with significant B
    # stripe-ness: correlation of row-means (stripes => high row-mean variance)
    rowmeans = Bd.mean(axis=1)
    colmeans = Bd.mean(axis=0)
    stripe = float(rowmeans.var() / max(1e-9, colmeans.var()))
    score = var * frac * (1.0 + 1.0/stripe)    # reward variance+coverage, penalize horizontal stripes
    print(f"{name:6s} f={feed} k={kill} D=({dA},{dB}): var={var:.3f} fracB={frac:.2f} stripe-ratio={stripe:.2f} score={score:.3f}")
    if best is None or score > best[0]:
        best = (score, name, feed, kill, seed, Bd)

print("BEST:", best[1], "feed", best[2], "kill", best[3])
Bd = best[5]

# render: chemical B through the house wheel by local density + slow spatial phase
out = []
def emit(line=""): out.append(line)
emit(sgr(40, 97))          # bg black default

for y in range(H):
    row = []
    for x in range(W):
        b = Bd[y][x]
        if b < 0.12:
            row.append(sgr(40, 40) + " ")             # A-dominated void -> black
            continue
        I = min(1.0, (b - 0.12) / 0.88)
        phase = (x*0.13 + y*0.09) % 8
        hi = int(phase) % len(HUE)
        fg = HUE[hi]
        if I > 0.86:
            ch = "\u2588"                               # white-hot at high-B confluence
            row.append(sgr(40, 97) + ch)
        else:
            idx = int(I * 3.0) % 4
            row.append(sgr(40, fg) + RAMP[idx])
    emit("".join(row))

# signature block (house standard for full-bleed pieces)
emit("")
emit(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
sig1 = "raze / AGENTSCII"
sig2 = f"REACTIONS v3.0 -- gray-scott '{best[1]}' regime"
def sigline(text, fg):
    pad = W - len(text)
    left = pad // 2
    right = pad - left
    return sgr(104, 40) + " "*left + sgr(fg, 40) + text + sgr(104, 40) + " "*right
emit(sigline(sig1, 97))
emit(sigline(sig2, 96))
emit(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))

emit(RESET)          # standalone reset tail (house idiom)

text = "\n".join(out)
with open("scratch/raze-reactions.ans", "w", encoding="cp437") as f:
    f.write(text)

# --- self-check hygiene gate --------------------------------------------------
raw = open("scratch/raze-reactions.ans", "rb").read()
ctrl = sorted(set(b for b in raw if b < 0x20 or b == 0x7f))
print("bytes:", len(raw), "ctrl bytes:", [hex(c) for c in ctrl])
try:
    raw.decode("cp437"); print("cp437 on disk: OK")
except Exception as e:
    print("cp437 FAIL", e)
sgrs = re.findall(rb"\x1b\[([0-9;]*)m", raw)
bad = []
for s in sgrs:
    for tok in (s.decode() or "0").split(";"):
        if tok == "": continue
        v = int(tok)
        if not (v == 0 or 30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
            bad.append(v)
print("SGR tokens:", len(sgrs), "out-of-range:", sorted(set(bad)))
disp = re.sub(rb"\x1b\[[0-9;]*m", b"", raw).decode("cp437")
widths = set(len(l) for l in disp.split("\n"))
print("row widths:", sorted(widths))
print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))
