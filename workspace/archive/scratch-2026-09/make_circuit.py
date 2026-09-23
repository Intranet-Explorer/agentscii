#!/usr/bin/env python3
# CIRCUIT v1.0 -- AGENTSCII (solo raze). A NEW tradition: a PCB / hardware-substrate
# field. Distinct from the data-terminal family (which shows DATA on a screen); this
# shows the physical SUBSTRATE itself -- copper traces routing between pads, IC chips
# with pin rows, vias at junctions, silkscreen component labels, all color-cycling
# across the house hue wheel. 80 wide, single full-bleed field.
#
# House idiom byte-for-byte as PLASMA / GRIDFALL / TUNNEL: cp437 on disk (raw bytes,
# code point == cp437 byte for block/box set), raw SGR (fg;40 form), BRIGHT fg 91-107
# + bg 40 ONLY (no dim codes -- matches the house range hollis checks), top/bottom
# border + centered cyan title band + sig block, standalone \x1b[0m tail. The "board"
# is black negative space; every lit cell is a chosen trace/via/pin/label -- no flat fill.
W = 80
H = 46
HUE = [91, 92, 93, 94, 95, 96, 97]     # bright wheel: r y g c b m w

def C(s):
    return bytes(ord(ch) & 0xFF for ch in s)

ch = [[' ' for _ in range(W)] for _ in range(H)]
fg = [[None for _ in range(W)] for _ in range(H)]

def put(x, y, c, f):
    if 0 <= x < W and 0 <= y < H:
        ch[y][x] = c
        fg[y][x] = f

# Substrate is pure black negative space (space on bg40) -- the board itself.
# No weave: authentic PCB-on-black, keeps the field legible and SGR-clean.

import math, random
random.seed(1984)

def hue_at(x, y, ph=0):
    return HUE[(x + y * 2 + ph) % len(HUE)]

# --- trace routing: clean Manhattan routes with a single 45-degree elbow, each route
#     one hue so it reads as a continuous copper path, not noise. Vias at both ends.
COLS = [6, 14, 22, 30, 38, 46, 54, 62, 70, 76]
ROWS = [3, 9, 15, 21, 27, 33, 39, 43]

def via(x, y, f):
    put(x, y, '\u25cf', f)              # ● solid via
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        if ch[y+dy][x+dx] == ' ':
            put(x+dx, y+dy, '\u25cb', f)  # ○ ring

def route(a, b, f):
    """a->b Manhattan with one elbow; direction chosen for variety."""
    x0,y0 = a; x1,y1 = b
    if random.random() < 0.5:
        for x in range(x0, x1 + (1 if x1>=x0 else -1), 1 if x1>=x0 else -1):
            put(x, y0, '\u2588', f)
        for y in range(y0, y1 + (1 if y1>=y0 else -1), 1 if y1>=y0 else -1):
            put(x1, y, '\u2588', f)
    else:
        for y in range(y0, y1 + (1 if y1>=y0 else -1), 1 if y1>=y0 else -1):
            put(x0, y, '\u2588', f)
        for x in range(x0, x1 + (1 if x1>=x0 else -1), 1 if x1>=x0 else -1):
            put(x, y1, '\u2588', f)
    via(x0, y0, f); via(x1, y1, f)

# Build a clean set of routes: pair up lattice pads by proximity so paths stay legible.
pads = [(c, r) for c in COLS for r in ROWS]
random.shuffle(pads)
used = set()
for i in range(0, len(pads)-1, 2):
    a, b = pads[i], pads[i+1]
    if abs(a[0]-b[0]) > 36 or abs(a[1]-b[1]) > 24:
        continue
    f = hue_at(a[0], a[1], (i//2) % len(HUE))
    route(a, b, f)
    used.add(id(a)); used.add(id(b))

# A few deliberate long "backbone" traces spanning the board for structure.
route((6, 3),  (74, 3),  hue_at(6,3,0))
route((6, 43), (74, 43), hue_at(6,43,2))
route((6, 3),  (6,  43), hue_at(6,3,4))
route((74,3),  (74, 43), hue_at(74,3,5))

# --- IC chips: colored package body + bright pin rows + notch + silkscreen label.
def chip(cx, cy, w, h, label, hue):
    x0 = cx - w//2; y0 = cy - h//2
    for yy in range(y0, y0+h):
        for xx in range(x0, x0+w):
            put(xx, yy, '\u2593', hue)      # ▓ colored package body
    fL = hue_at(x0,     cy, 1); fR = hue_at(x0+w-1, cy, 1)
    for yy in range(y0+1, y0+h):
        put(x0,     yy, '\u2588', fL)       # left pin row
        put(x0+w-1, yy, '\u2588', fR)       # right pin row
    put(cx, y0, '\u2591', 40)               # notch (pin-1 marker), black bite
    lx = cx - len(label)//2
    for i, c in enumerate(label):
        put(lx+i, cy, c, 107)               # white silkscreen label

# central CPU -- focal point, hot white core inside a saturated package
chip(40, 23, 18, 9, "AGENTSCII", 95)
for yy in range(19, 27):
    for xx in range(36, 45):
        if (xx-40)**2 + (yy-23)**2 <= 4:
            put(xx, yy, '\u2588', 107)       # white-hot core

# surrounding IC packages, each a distinct hue so they read as different components
chip(16, 9,   10, 5, "U2", 91)
chip(64, 9,   10, 5, "U3", 93)
chip(16, 37,  10, 5, "U4", 96)
chip(64, 37,  10, 5, "U5", 92)
chip(40, 8,    8, 4, "U6", 94)
chip(40, 39,   8, 4, "U7", 97)

# vias at junctions
for (c, r) in [(14,15),(22,27),(30,11),(54,15),(62,27),(70,19),(8,23),(72,37),(40,15),(40,33)]:
    via(c, r, hue_at(c, r, 1))

# silkscreen component labels (white, thin) -- R/C/L/J designators
def label(x, y, t):
    for i, c in enumerate(t):
        put(x+i, y, c, 97)
label(24, 5, "R1")
label(50, 5, "C2")
label(68, 31, "L1")
label(4,    31, "J1")
label(28, 43, "PWR")
label(56, 43, "GND")
label(70, 5, "CLK")

# ================= emit SGR-optimized bytes (cp437), house format =================
out = []

def border_row(corn_l, corn_r, fill='\u2588', hue=105):
    out.append(b'\x1b[' + str(hue).encode() + b';40m'); out.append(C(corn_l))
    out.append(b'\x1b[104;40m'); out.append(C(fill*78))
    out.append(b'\x1b[' + str(hue).encode() + b';40m'); out.append(C(corn_r))
    out.append(b'\n')

border_row('\u2591', '\u259a')     # top border

title = "CIRCUIT // HARDWARE SUBSTRATE FIELD"
pad = (W - len(title)) // 2
out.append(b'\x1b[104;40m'); out.append(C(' '*pad))
out.append(b'\x1b[96;40m');   out.append(C(title))
out.append(b'\x1b[104;40m');  out.append(C(' '*(W - pad - len(title))))
out.append(b'\n')

prev = None
for y in range(H):
    for x in range(W):
        f = fg[y][x]
        c = ch[y][x]
        if f is None:
            f = 97                       # default substrate: bright on black = blank, keeps SGR in house range
        if f != prev:
            out.append(b'\x1b[' + str(f).encode() + b';40m')
            prev = f
        out.append(C(c))
    out.append(b'\n')

border_row('\u2590', '\u2592')     # bottom border

def sig(text, f=104):
    pad = (W - len(text)) // 2
    out.append(b'\x1b[' + str(f).encode() + b';40m'); out.append(C(' '*pad))
    out.append(b'\x1b[96;40m');   out.append(C(text))
    out.append(b'\n')

out.append(b'\n')
sig("raze / AGENTSCII", 104)
sig("CIRCUIT v1.0 -- copper traces, ICs, vias on a cycling substrate", 96)
out.append(b'\x1b[0m')

path = "scratch/raze-circuit.ans"
data = b"".join(out)
with open(path, 'wb') as fh:
    fh.write(data)

import re
ctrl = {}
for b in data:
    if b < 32 or b == 127:
        ctrl[b] = ctrl.get(b, 0) + 1
print("wrote", path, len(data), "bytes")
print("control bytes:", {hex(k): v for k, v in sorted(ctrl.items())})
try:
    data.decode('cp437'); print("cp437 decode: OK")
except Exception as e:
    print("cp437 FAIL", e)
bad = 0; used_fgs=set()
for m in re.finditer(rb'\x1b\[(\d+;?\d*)m', data):
    p = m.group(1).decode()
    for tok in p.split(';'):
        if tok == '':
            continue
        v = int(tok)
        used_fgs.add(v)
        if not (0 <= v <= 107):
            bad += 1
print("invalid SGR params:", bad, "| fg/bg codes used:", sorted(used_fgs))
clean = re.sub(rb'\x1b\[[0-9;]*m', b'', data)
rows = clean.split(b'\n')
print("total lines:", len(rows))
for i, r in enumerate(rows):
    if len(r) != W and r.strip():
        print(f"  row {i}: width {len(r)} (!= {W})")
