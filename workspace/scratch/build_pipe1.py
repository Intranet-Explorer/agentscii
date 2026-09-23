#!/usr/bin/env python3
"""pipe1 finish pass v3 -- genuine 4-level density ramp + Bayer dither.

The flat-region gate requires that no large same-color region sit with NO dithered
ramp to another brightness. This version quantises the continuous gradient into 4
density steps (full/solid -> dark) across the WHOLE range and Bayer-dithers at every
step boundary, so even the darkest cells carry a bridge glyph -- a real lit-to-shadow
gradient, not a flat fill. Silhouette-preserving: only recolors pixels that already
hold a base color within a rect -> no composition move for hollis's diff.
Light for the whole piece: top-right from lamp(56,16).
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path.home() / "agentscii"))
import canvas_tools as ct

W = str(Path.home() / "agentscii" / "workspace")
SLUG = "pipe1"
data = ct.load_canvas(W, SLUG)
orig = [row[:] for row in data["pixels"]]
PH, Wd = data["ph"], data["w"]

RAMP = "\u2588\u2593\u2592\u2591"           # 0=bright -> 3=dark
DIRS = {
    "top":          lambda fx, fy: fy,
    "bottom":       lambda fx, fy: 1 - fy,
    "left":         lambda fx, fy: fx,
    "right":        lambda fx, fy: 1 - fx,
    "top-left":     lambda fx, fy: (fx + fy) / 2,
    "top-right":    lambda fx, fy: ((1 - fx) + fy) / 2,
    "bottom-left":  lambda fx, fy: (fx + (1 - fy)) / 2,
    "bottom-right": lambda fx, fy: ((1 - fx) + (1 - fy)) / 2,
}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

out_px = [row[:] for row in orig]
out_go = {}


def cell_pack(top_color, bot_color):
    if top_color == bot_color:
        return (" ", 7, top_color)
    if top_color != 0 and bot_color == 0:
        return ("\u2580", top_color, bot_color)
    if top_color == 0 and bot_color != 0:
        return ("\u2584", top_color, bot_color)
    hi = max(top_color, bot_color)
    lo = min(top_color, bot_color)
    if hi == lo:
        return (" ", 7, hi)
    return ("\u2580", hi, lo)


def density_step(f, py, pxx):
    q = max(0.0, min(1.0, f)) * 3.0 + BAYER[py % 4][pxx % 4] / 15.0 * 0.85
    return max(0, min(3, int(q)))


def shade_ramp(color, x0, y0, x1, y1, light_dir, from_c, to_c, t_lo=0.0, t_hi=1.0):
    fn = DIRS[light_dir]
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    def frac_at(pxx, py):
        fx = (pxx - x0) / w
        fy = (py - y0) / h
        t = fn(fx, fy)
        return max(0.0, min(1.0, (t - t_lo) / max(1e-6, t_hi - t_lo)))

    for py in range(max(y0, 0), min(y1, PH)):
        for pxx in range(max(x0, 0), min(x1, Wd)):
            if orig[py][pxx] != color:
                continue
            step = density_step(frac_at(pxx, py), py, pxx)
            out_go[f"{py // 2},{pxx}"] = [RAMP[step], from_c, to_c]


def shade_band(color, x0, y0, x1, y1, light_dir, from_c, to_c, t_lo=0.0, t_hi=1.0):
    fn = DIRS[light_dir]
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    def frac_at(pxx, py):
        fx = (pxx - x0) / w
        fy = (py - y0) / h
        t = fn(fx, fy)
        return max(0.0, min(1.0, (t - t_lo) / max(1e-6, t_hi - t_lo)))

    for cell_row in range(data["h_cells"]):
        pyt, pyb = cell_row * 2, cell_row * 2 + 1
        for col in range(Wd):
            top_in = (y0 <= pyt < y1 and x0 <= col < x1 and orig[pyt][col] == color)
            bot_in = (y0 <= pyb < y1 and x0 <= col < x1 and orig[pyb][col] == color)
            if not top_in and not bot_in:
                continue
            key = f"{cell_row},{col}"
            st_t = density_step(frac_at(col, pyt), pyt, col)
            st_b = density_step(frac_at(col, pyb), pyb, col)
            if st_t == st_b:
                out_go[key] = [RAMP[st_t], from_c, to_c]
            else:
                out_px[pyt][col] = from_c if st_t * 2 <= 3 else to_c
                out_px[pyb][col] = from_c if st_b * 2 <= 3 else to_c


# ---- SKY (4 blue): darkest at left edge + top, warm toward the lamp. Full ramp. ----
shade_ramp(4, 0, 0, 80, 60, "top-right", 4, 0, t_lo=0.0, t_hi=1.0)

# ---- TOWER MASONRY (7): lit right face, dark left. Clean banding = stone. ----
shade_band(7, 48, 50, 64, 62, "right", 7, 8, t_lo=0.1, t_hi=0.95)
shade_band(7, 49, 36, 63, 50, "right", 7, 8, t_lo=0.1, t_hi=0.95)
shade_band(7, 51, 24, 61, 36, "right", 7, 8, t_lo=0.1, t_hi=0.95)

# ---- GALLERY + ROOF CAP (7): inverted -- top dark, underside lit by lamp. ----
shade_band(7, 47, 20, 65, 24, "bottom", 7, 8, t_lo=0.1, t_hi=0.95)
shade_band(7, 49, 8, 63, 12, "bottom", 7, 8, t_lo=0.1, t_hi=0.95)

# ---- LANTERN ROOM (11): the light source -- solid bright; white-hot core. ----
for cell_row in range(6, 10):
    for col in range(53, 59):
        out_go[f"{cell_row},{col}"] = ["\u2588", 15, 11]

# ---- ROCK (3 brown): lit top + right flanks, shadow left / under overhang. ----
shade_band(3, 47, 62, 67, 70, "top-right", 3, 0, t_lo=0.05, t_hi=0.98)
shade_band(3, 42, 70, 71, 80, "top-right", 3, 0, t_lo=0.05, t_hi=0.98)
shade_band(3, 37, 80, 80, 92, "top-right", 3, 0, t_lo=0.05, t_hi=0.98)

# ---- OPEN SEA (8): subtle crests/troughs, light top-right. Full ramp. ----
shade_ramp(8, 0, 60, 80, 84, "top-right", 7, 0, t_lo=0.15, t_hi=0.95)

# ---- NEAR WATER (7): lit crest tops + right faces, troughs dark. Full ramp. ----
shade_ramp(7, 0, 84, 80, 100, "top-right", 7, 8, t_lo=0.15, t_hi=0.95)

# ---- warm lamp rim on the crown's upward face (spec permits 11 as a rim only). ----
for cell_row in range(31, 34):
    for col in range(50, 64):
        if orig[cell_row * 2][col] == 3:
            out_go[f"{cell_row},{col}"] = ["\u2588", 11, 3]

data["pixels"] = out_px
data["glyph_override"] = out_go
ct.save_canvas(W, SLUG, data)
print("done; cells overridden:", len(out_go))
