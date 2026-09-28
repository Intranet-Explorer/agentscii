#!/usr/bin/env python3
"""Half-block canvas primitives behind the harness's canvas_* tools.

Lets the agents draw with tool calls instead of writing generator scripts.
Each canvas is one JSON file at workspace/canvases/<slug>.json, so state
persists across calls and restarts. Data model matches
workspace/scratch/halfblock.py's HalfBlockCanvas:
  - "pixels": width x (height*2) grid of color indices 0-15 in PIXEL space.
    Each cell is two pixels tall, so circles come out round with no aspect
    correction.
  - "glyph_override": sparse {"row,col": [char, fg, bg]} in CELL space.
    Wins over the pixel pair for that cell. Used for dither glyphs, text
    and stamped patch cells.

Does not import workspace/scratch/*.py. Those files are agent-writable and
tool dispatch must not depend on them. The duplicated logic (sgr, shade_ramp,
half-block packing) is kept identical to its scratch/ counterpart.
"""
import base64
import json
import math
import re
from pathlib import Path

CANVAS_DIR_NAME = "canvases"
_SLUG_RE = re.compile(r"^[a-z0-9_-]{1,64}$")

MAX_W = 200
MAX_H = 500

# Same full->empty block-density ramp as workspace/scratch/canvas.py's RAMP.
_RAMP = "\u2588\u2593\u2592\u2591"

_DIRECTIONS = {
    "top":          lambda fx, fy: fy,
    "bottom":       lambda fx, fy: 1 - fy,
    "left":         lambda fx, fy: fx,
    "right":        lambda fx, fy: 1 - fx,
    "top-left":     lambda fx, fy: (fx + fy) / 2,
    "top-right":    lambda fx, fy: ((1 - fx) + fy) / 2,
    "bottom-left":  lambda fx, fy: (fx + (1 - fy)) / 2,
    "bottom-right": lambda fx, fy: ((1 - fx) + (1 - fy)) / 2,
}


class CanvasError(ValueError):
    pass


def _validate_slug(slug):
    if not slug or not _SLUG_RE.match(slug):
        raise CanvasError(
            f"invalid canvas slug {slug!r} -- lowercase letters, digits, "
            "-, _ only, max 64 chars"
        )


def _canvas_dir(workspace):
    d = Path(workspace) / CANVAS_DIR_NAME
    d.mkdir(exist_ok=True)
    return d


def _canvas_path(workspace, slug):
    _validate_slug(slug)
    return _canvas_dir(workspace) / f"{slug}.json"


def canvas_exists(workspace, slug):
    return _canvas_path(workspace, slug).exists()


def list_canvases(workspace):
    d = _canvas_dir(workspace)
    return sorted(p.stem for p in d.glob("*.json"))


def load_canvas(workspace, slug):
    path = _canvas_path(workspace, slug)
    if not path.exists():
        raise CanvasError(
            f"no canvas named '{slug}' (call canvas_new first). "
            f"Open canvases: {list_canvases(workspace)}"
        )
    return json.loads(path.read_text())


def save_canvas(workspace, slug, data):
    _canvas_path(workspace, slug).write_text(json.dumps(data))


def new_canvas(workspace, slug, width, height, bg=0):
    if canvas_exists(workspace, slug):
        raise CanvasError(
            f"canvas '{slug}' already exists -- pick a new slug, or "
            "canvas_save it and start a new slug for the next piece"
        )
    width, height, bg = int(width), int(height), int(bg)
    if not (1 <= width <= MAX_W):
        raise CanvasError(f"width must be 1-{MAX_W} cells, got {width}")
    if not (1 <= height <= MAX_H):
        raise CanvasError(f"height must be 1-{MAX_H} cells, got {height}")
    if not (0 <= bg <= 15):
        raise CanvasError(f"bg must be a color index 0-15, got {bg}")
    ph = height * 2
    data = {
        "w": width, "h_cells": height, "ph": ph, "bg": bg,
        "pixels": [[bg] * width for _ in range(ph)],
        "glyph_override": {},
    }
    save_canvas(workspace, slug, data)
    return data


def _check_color(color):
    color = int(color)
    if not (0 <= color <= 15):
        raise CanvasError(f"color must be a palette index 0-15, got {color}")
    return color


def _drop_overrides(data, cells):
    """Remove glyph overrides on cells a pixel write just painted.

    Overrides render in place of a cell's pixels, so without this a later
    pixel fill over a shaded area would change nothing visible.
    """
    go = data["glyph_override"]
    for (r, c) in cells:
        go.pop(f"{r},{c}", None)


def fill_px(workspace, slug, x, y, w, h, color):
    """Fill a rectangle in PIXEL space (x: 0..width-1, y: 0..height*2-1)."""
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    W, PH = data["w"], data["ph"]
    x0, y0 = int(x), int(y)
    x1, y1 = x0 + int(w), y0 + int(h)
    x0c, x1c = max(0, min(x0, x1)), min(W, max(x0, x1))
    y0c, y1c = max(0, min(y0, y1)), min(PH, max(y0, y1))
    pixels = data["pixels"]
    _hit = set()
    for py in range(y0c, y1c):
        row = pixels[py]
        for px in range(x0c, x1c):
            row[px] = color
            _hit.add((py >> 1, px))
    # last_shape is the default target for canvas_shade.
    _drop_overrides(data, _hit)
    data["last_shape"] = {"type": "rect", "x0": x0c, "y0": y0c, "x1": x1c, "y1": y1c}
    save_canvas(workspace, slug, data)
    return data


def circle_px(workspace, slug, cx, cy, r, color):
    """Fill a circle in PIXEL space. Same math as HalfBlockCanvas.fill_circle()."""
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    W, PH = data["w"], data["ph"]
    cx, cy, r = float(cx), float(cy), float(r)
    if r <= 0:
        raise CanvasError(f"r must be > 0, got {r}")
    r0, r1 = int(cx - r) - 1, int(cx + r) + 1
    c0, c1 = int(cy - r) - 1, int(cy + r) + 1
    pixels = data["pixels"]
    _hit = set()
    for py in range(max(0, c0), min(PH, c1 + 1)):
        row = pixels[py]
        for px in range(max(0, r0), min(W, r1 + 1)):
            if math.hypot(px - cx, py - cy) <= r:
                row[px] = color
                _hit.add((py >> 1, px))
    _drop_overrides(data, _hit)
    data["last_shape"] = {"type": "circle", "cx": cx, "cy": cy, "r": r}
    save_canvas(workspace, slug, data)
    return data


_LIGHT_VECTORS = {
    "top":          (0.0, -0.85, 0.53),
    "bottom":       (0.0, 0.85, 0.53),
    "left":         (-0.85, 0.0, 0.53),
    "right":        (0.85, 0.0, 0.53),
    "top-left":     (-0.6, -0.6, 0.53),
    "top-right":    (0.6, -0.6, 0.53),
    "bottom-left":  (-0.6, 0.6, 0.53),
    "bottom-right": (0.6, 0.6, 0.53),
}

# 2D screen-space normal for each side of a slab. Flat faces get their
# brightness from orientation against the light, not a per-pixel normal.
_FACE_NORMALS = {
    "top": (0.0, -1.0), "bottom": (0.0, 1.0),
    "left": (-1.0, 0.0), "right": (1.0, 0.0),
}


def _face_band(face, light_direction):
    """(t_lo, t_hi) brightness band for one face of a flat form.

    Lambert on the face normal sets the base; the band width gives the face
    its own gradient from lit edge to far edge.
    """
    lv = _LIGHT_VECTORS.get(light_direction, (-0.6, -0.6, 0.53))
    nx, ny = _FACE_NORMALS[face]
    lam = max(0.0, nx * lv[0] + ny * lv[1])       # 0 = edge-on/away
    base = 1.0 - (0.15 + 0.85 * lam)              # 0 = brightest
    # The band must span about 3 ramp steps so a cell's two pixels can land
    # on different steps and pack as ▀. Narrower bands produce few half-blocks.
    half = 0.40
    return max(0.0, base - half), min(1.0, base + half)


_BAYER8 = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]


def _bayer(px, py):
    """Ordered-dither threshold in [-0.5, 0.5) for pixel (px, py)."""
    return _BAYER8[py % 8][px % 8] / 64.0 - 0.5


def _shade_ramp(from_color, to_color, steps=5):
    """Density-dither stops, identical to scratch/canvas.py's shade_ramp().

    fg is always from_color and bg always to_color; only the glyph varies
    (█ ▓ ▒ ░ space), faking tones the 16-color palette lacks.
    """
    stops = []
    for i in range(steps):
        if i == 0:
            stops.append((_RAMP[0], from_color, to_color))
        elif i == steps - 1:
            stops.append((" ", from_color, to_color))
        else:
            interior_t = (i - 1) / (steps - 2) if steps > 2 else 0.0
            ramp_idx = 1 + min(len(_RAMP) - 2, int(interior_t * (len(_RAMP) - 1)))
            stops.append((_RAMP[ramp_idx], from_color, to_color))
    return stops


def _pixel_mask_at(data, px, py, mask):
    """True if pixel (px, py) is inside `mask`.

    mask: {"type": "rect", x0, y0, x1, y1}, {"type": "circle", cx, cy, r},
    {"type": "capsule", ax, ay, bx, by, r} (all PIXEL space),
    {"type": "color", color} (every pixel of that color), or None for the
    canvas's last drawn shape.
    """
    if mask is None:
        mask = data.get("last_shape")
        if mask is None:
            raise CanvasError(
                "no region given and no shape has been drawn on this canvas "
                "yet (canvas_fill_px/canvas_circle_px set the default shade "
                "target) -- pass region explicitly"
            )
    mtype = mask.get("type")
    if mtype == "rect":
        return mask["x0"] <= px < mask["x1"] and mask["y0"] <= py < mask["y1"]
    if mtype == "circle":
        return math.hypot(px - mask["cx"], py - mask["cy"]) <= mask["r"]
    if mtype == "capsule":
        # distance from pixel to the axis SEGMENT (rect with round ends)
        ax, ay, bx, by = mask["ax"], mask["ay"], mask["bx"], mask["by"]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
        return math.hypot(px - (ax + t * vx), py - (ay + t * vy)) <= mask["r"]
    if mtype == "color":
        return data["pixels"][py][px] == mask["color"]
    raise CanvasError(f"unknown mask type {mtype!r}")


def _shade_masked(data, mask, from_color, to_color, light_direction, light_x=None, light_y=None, sphere=None, t_lo=0.0, t_hi=1.0, cull_band=True, cyl=None, rim=False, face_grad=False):
    """Shade only the pixels inside `mask`. Shared by shade() and the lit shapes.

    Cells outside the mask are untouched. Edge cells (mask covers one of
    the two pixels) get a per-pixel color write so the ▀ silhouette stays
    intact; only fully covered cells can get a dither glyph.

    light_x/light_y (PIXEL space) replace light_direction with a point
    light. sphere/cyl select curved-surface normals.
    """
    W, PH = data["w"], data["ph"]
    pixels = data["pixels"]
    go = data["glyph_override"]

    xs, ys = [], []
    for py in range(PH):
        for px in range(W):
            if _pixel_mask_at(data, px, py, mask):
                xs.append(px)
                ys.append(py)
    if not xs:
        raise CanvasError("shade region/mask matched zero pixels")
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    w_span = max(1, x1 - x0 - 1)
    h_span = max(1, y1 - y0 - 1)

    if light_x is not None and light_y is not None:
        if sphere is not None:
            # Lambert on the sphere's surface normal. Plain 2D distance
            # from the light gives a flat radial wash with visible bands.
            scx, scy, sr = sphere["cx"], sphere["cy"], max(1e-6, sphere["r"])
            lvx, lvy = light_x - scx, light_y - scy
            lvz = sr * 0.85  # light sits in front of the sphere
            llen = math.sqrt(lvx * lvx + lvy * lvy + lvz * lvz) or 1.0
            lvx, lvy, lvz = lvx / llen, lvy / llen, lvz / llen

            def light_t(px, py):
                nx, ny = (px - scx) / sr, (py - scy) / sr
                # Normals must use the renderer's pixel aspect, or the
                # terminator reads as an ellipse on a round silhouette.
                d2 = nx * nx + ny * ny
                nz = math.sqrt(max(0.0, 1.0 - d2))
                lam = nx * lvx + ny * lvy + nz * lvz
                lam = max(0.0, min(1.0, lam))
                # Soft wrap plus ambient. Pure Lambert saturates most of the
                # lit side into a flat highlight; this spreads the ramp
                # across the whole visible surface.
                lam = 0.12 + 0.88 * (0.5 + 0.5 * (2.0 * lam - 1.0) ** 0.6
                                     if lam >= 0.5 else
                                     0.5 - 0.5 * (1.0 - 2.0 * lam) ** 0.6)
                return 1.0 - lam
        elif cyl is not None:
            # Cylinder: normal curves across the short axis only and is
            # constant along the length.
            ax, ay, bx, by = cyl["ax"], cyl["ay"], cyl["bx"], cyl["by"]
            cr = max(1e-6, cyl["r"])
            vx, vy = bx - ax, by - ay
            vlen = math.hypot(vx, vy) or 1.0
            ux, uy = vx / vlen, vy / vlen       # along axis
            nx_a, ny_a = -uy, ux                # perpendicular in-plane
            lv = _LIGHT_VECTORS.get(light_direction, (-0.6, -0.6, 0.53))

            def light_t(px, py):
                t = ((px - ax) * vx + (py - ay) * vy) / (vlen * vlen)
                t = max(0.0, min(1.0, t))
                ox, oy = px - (ax + t * vx), py - (ay + t * vy)
                d = (ox * nx_a + oy * ny_a) / cr
                d = max(-1.0, min(1.0, d))
                nz = math.sqrt(max(0.0, 1.0 - d * d))
                lam = (d * nx_a) * lv[0] + (d * ny_a) * lv[1] + nz * lv[2]
                lam = max(0.0, min(1.0, lam))
                return 1.0 - (0.12 + 0.88 * lam)
        else:
            max_d = math.hypot(x1 - x0, y1 - y0) / 2 or 1.0

            def light_t(px, py):
                return min(1.0, math.hypot(px - light_x, py - light_y) / max_d)
    else:
        if light_direction not in _DIRECTIONS:
            raise CanvasError(
                f"light_direction must be one of {sorted(_DIRECTIONS)}, got {light_direction!r}"
            )
        fn = _DIRECTIONS[light_direction]

        def light_t(px, py):
            fx = (px - x0) / w_span
            fy = (py - y0) / h_span
            t = fn(fx, fy)
            if face_grad:
                # Add falloff from the lit corner so a flat face varies on
                # both axes. Otherwise a tall face is uniform down its length.
                t = 0.65 * t + 0.35 * min(1.0, math.hypot(fx - (0.0 if "left" in light_direction or light_direction in ("top","bottom") else 1.0), fy - (0.0 if "top" in light_direction else 1.0)) / 1.414)
            return t

    stops = _shade_ramp(from_color, to_color, 5)
    last = len(stops) - 1

    def step_at(px, py):
        """Ramp step for one pixel, with Bayer dither.

        Resolving per pixel lets a cell's two pixels land on different
        steps, which is what produces ▀ interiors instead of hard bands.
        """
        t = light_t(px, py)
        if cull_band:
            t = (t - t_lo) / max(1e-6, t_hi - t_lo)
        else:
            # Face mode: compress the whole face into its band instead of
            # culling, so an edge-on face still shows a (darker) gradient.
            t = t_lo + max(0.0, min(1.0, t)) * (t_hi - t_lo)
        s = max(0.0, min(1.0, t)) * last
        return max(0, min(last, int(math.floor(s + _bayer(px, py) + 0.5))))

    def _in_band(px, py):
        if not cull_band:
            return True
        t = light_t(px, py)
        return t_lo <= t < t_hi or (t_hi >= 1.0 and t >= t_hi)

    def solid_of(step):
        """Solid color for a step, used when a cell packs as a half-block."""
        return from_color if step * 2 <= last else to_color

    for cell_row in range(data["h_cells"]):
        py_top, py_bot = cell_row * 2, cell_row * 2 + 1
        for col in range(W):
            top_in = _pixel_mask_at(data, col, py_top, mask)
            bot_in = _pixel_mask_at(data, col, py_bot, mask)
            if not top_in and not bot_in:
                continue
            key = f"{cell_row},{col}"
            if not (_in_band(col, py_top) or _in_band(col, py_bot)):
                continue
            if top_in and bot_in:
                st_t, st_b = step_at(col, py_top), step_at(col, py_bot)
                if st_t == st_b:
                    ch, fg, bg = stops[st_t]
                    go[key] = [ch, fg, bg]
                else:
                    # Pixels on different steps: pack as a half-block pair
                    # rather than flattening to one glyph.
                    if key in go:
                        del go[key]
                    pixels[py_top][col] = solid_of(st_t)
                    pixels[py_bot][col] = solid_of(st_b)
            else:
                # Edge cell: recolor only the masked pixel so the
                # silhouette keeps its half-block boundary.
                if key in go:
                    del go[key]  # an override would hide the pixel split
                py_target = py_top if top_in else py_bot
                pixels[py_target][col] = solid_of(step_at(col, py_target))

    if rim:
        # Brighten light-facing edges so face boundaries read.
        lv = _LIGHT_VECTORS.get(light_direction, (-0.6, -0.6, 0.53))
        for py in range(PH):
            for px in range(W):
                if not _pixel_mask_at(data, px, py, mask):
                    continue
                ox = 1 if lv[0] > 0.2 else (-1 if lv[0] < -0.2 else 0)
                oy = 1 if lv[1] > 0.2 else (-1 if lv[1] < -0.2 else 0)
                out_x, out_y = px + ox, py + oy
                outside = (
                    not (0 <= out_x < W and 0 <= out_y < PH)
                    or not _pixel_mask_at(data, out_x, out_y, mask)
                )
                if outside:
                    cell_row, key = py // 2, f"{py // 2},{px}"
                    if key in go:
                        del go[key]
                    pixels[py][px] = from_color


def shade(workspace, slug, from_color, to_color, light_direction, region=None):
    """Apply density-dither shading to a shape.

    region defaults to the last shape drawn; see _pixel_mask_at for the
    accepted forms.
    """
    data = load_canvas(workspace, slug)
    from_color, to_color = _check_color(from_color), _check_color(to_color)
    _shade_masked(data, region, from_color, to_color, light_direction)
    save_canvas(workspace, slug, data)
    return data


def sphere_px(workspace, slug, cx, cy, r, color, light_x, light_y, shadow_color=None, hi_color=None):
    """Draw a circle and shade it as a sphere lit from (light_x, light_y).

    shadow_color defaults to 0 (black), hi_color to 15 (bright white).
    """
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    dark = _check_color(shadow_color if shadow_color is not None else 0)
    cx, cy, r = float(cx), float(cy), float(r)
    if r <= 0:
        raise CanvasError(f"r must be > 0, got {r}")
    W, PH = data["w"], data["ph"]
    r0, r1 = int(cx - r) - 1, int(cx + r) + 1
    c0, c1 = int(cy - r) - 1, int(cy + r) + 1
    pixels = data["pixels"]
    _hit = set()
    for py in range(max(0, c0), min(PH, c1 + 1)):
        row = pixels[py]
        for px in range(max(0, r0), min(W, r1 + 1)):
            if math.hypot(px - cx, py - cy) <= r:
                row[px] = color
                _hit.add((py >> 1, px))
    mask = {"type": "circle", "cx": cx, "cy": cy, "r": r}
    _drop_overrides(data, _hit)
    data["last_shape"] = mask
    # Two bands: hi -> color, then color -> shadow. A single band starts
    # from a solid █ at the lit end and renders the highlight as a flat cap.
    hi = _check_color(hi_color if hi_color is not None else 15)
    _shade_masked(data, mask, hi, color, "top-left",
                  light_x=float(light_x), light_y=float(light_y),
                  sphere=mask, t_lo=0.0, t_hi=0.55)
    _shade_masked(data, mask, color, dark, "top-left",
                  light_x=float(light_x), light_y=float(light_y),
                  sphere=mask, t_lo=0.55, t_hi=1.0)
    save_canvas(workspace, slug, data)
    return data


def text(workspace, slug, x, y, text_str, fg, bg):
    """Place literal characters from cell (x, y), one per cell. Use wordmark() for big letters."""
    data = load_canvas(workspace, slug)
    fg, bg = _check_color(fg), _check_color(bg)
    W, H = data["w"], data["h_cells"]
    row = int(y)
    if not (0 <= row < H):
        raise CanvasError(f"y={row} out of bounds (canvas is {H} cells tall)")
    bad = sorted({ch for ch in text_str if not _cp437_ok(ch)})
    if bad:
        raise CanvasError(f"not in CP437, would save as '?': {''.join(bad)!r}")
    go = data["glyph_override"]
    col = int(x)
    for ch in text_str:
        if col >= W:
            break
        if col >= 0:
            go[f"{row},{col}"] = [ch, fg, bg]
        col += 1
    save_canvas(workspace, slug, data)
    return data


# Copy of scratch/canvas.py's GLYPHS_5x7. Not imported; see module docstring.
_GLYPHS_5x7 = {
'A': [".#...",".###.","#...#","#####","#...#","#...#","#...#"],
'B': ["####.","#...#","#...#","####.","#...#","#...#","####."],
'C': [".####","#....","#....","#....","#....","#....",".####"],
'D': ["####.","#...#","#...#","#...#","#...#","#...#","####."],
'E': ["#####","#....","#....","####.","#....","#....","#####"],
'F': ["#####","#....","#....","####.","#....","#....","#...."],
'G': [".####","#....","#....","#.##.","#...#","#...#",".####"],
'H': ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
'I': ["#####","..#..","..#..","..#..","..#..","..#..","#####"],
'J': ["....#","....#","....#","....#","#...#","#...#",".###."],
'K': ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
'L': ["#....","#....","#....","#....","#....","#....","#####"],
'M': ["#...#","##.##","#.#.#","#...#","#...#","#...#","#...#"],
'N': ["#...#","##..#","#.#.#","#..##","#...#","#...#","#...#"],
'O': [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
'P': ["####.","#...#","#...#","####.","#....","#....","#...."],
'Q': [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
'R': ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
'S': [".####","#....","#....",".###.","....#","....#","####."],
'T': ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
'U': ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
'V': ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
'W': ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
'X': ["#...#",".#.#.","..#..","..#..","..#..",".#.#.","#...#"],
'Y': ["#...#",".#.#.","..#..","..#..","..#..","..#..","..#.."],
'Z': ["#####","....#","...#.","..#..",".#...","#....","#####"],
'0': [".###.","#...#","#..##","#.#.#","##..#","#...#",".###."],
'1': ["..#..",".##..","..#..","..#..","..#..","..#..","#####"],
'2': [".###.","#...#","....#","...#.","..#..",".#...","#####"],
'3': [".###.","#...#","....#",".###.","....#","#...#",".###."],
'4': ["...#.","..##.",".#.#.","#..#.","#####","...#.","...#."],
'5': ["#####","#....","####.","....#","....#","#...#",".###."],
'6': [".###.","#....","#....","####.","#...#","#...#",".###."],
'7': ["#####","....#","...#.","..#..",".#...","#....","#...."],
'8': [".###.","#...#","#...#",".###.","#...#","#...#",".###."],
'9': [".###.","#...#","#...#",".####","....#","....#",".###."],
' ': [".....",".....",".....",".....",".....",".....","....."],
'-': [".....",".....",".....","#####",".....",".....","....."],
':': [".....","..#..",".....",".....",".....","..#..","....."],
'/': ["....#","...#.","..#..",".#...","#....",".....","....."],
'!': ["..#..","..#..","..#..","..#..","..#..",".....","..#.."],
"'": [".#...",".#...",".....",".....",".....",".....","....."],
'.': [".....",".....",".....",".....",".....",".....","..#.."],
'&': [".##..","#..#.","#.#..",".#...","#.#.#","#..#.",".##.#"],
}


def wordmark(workspace, slug, x, y, text_str, fg, scale=2, gap=1):
    """Draw text as scaled 5x7 block letters in PIXEL space.

    Returns (data, width_px) so the caller can center a word.
    """
    data = load_canvas(workspace, slug)
    fg = _check_color(fg)
    W, PH = data["w"], data["ph"]
    pixels = data["pixels"]
    x0, y0 = int(x), int(y)
    cur_x = x0
    for ch_letter in text_str:
        glyph = _GLYPHS_5x7.get(ch_letter.upper(), _GLYPHS_5x7[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell != "#":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        px = cur_x + col_i * scale + sx
                        py = y0 + row_i * scale + sy
                        if 0 <= px < W and 0 <= py < PH:
                            pixels[py][px] = fg
        cur_x += (5 * scale) + gap
    save_canvas(workspace, slug, data)
    return data, cur_x - x0 - gap


def mirror(workspace, slug, axis="v"):
    """Mirror one half of the canvas onto the other.

    axis='v' copies left to right; axis='h' copies top to bottom.
    """
    data = load_canvas(workspace, slug)
    W, PH = data["w"], data["ph"]
    pixels = data["pixels"]
    go = data["glyph_override"]
    if axis == "v":
        mid = W // 2
        for py in range(PH):
            row = pixels[py]
            for px in range(mid):
                row[W - 1 - px] = row[px]
        new_go = dict(go)
        for key, val in go.items():
            r, c = key.split(",")
            c = int(c)
            if c < mid:
                new_go[f"{r},{W - 1 - c}"] = val
        data["glyph_override"] = new_go
    elif axis == "h":
        h_cells = data["h_cells"]
        mid_cell = h_cells // 2
        for cell_row in range(mid_cell):
            src_top, dst_top = cell_row * 2, (h_cells - 1 - cell_row) * 2
            pixels[dst_top] = list(pixels[src_top])
            pixels[dst_top + 1] = list(pixels[src_top + 1])
        new_go = dict(go)
        for key, val in go.items():
            r, c = key.split(",")
            r = int(r)
            if r < mid_cell:
                new_go[f"{h_cells - 1 - r},{c}"] = val
        data["glyph_override"] = new_go
    else:
        raise CanvasError(f"axis must be 'v' or 'h', got {axis!r}")
    save_canvas(workspace, slug, data)
    return data


def strand_shade(workspace, slug, region, direction, fg_list, n_strands=40, length=6, seed=None):
    """Short directional strokes for fur, hair or grain.

    region: {"type": "rect", x0, y0, x1, y1} in CELL space.
    direction: [dx, dy], e.g. [0, 1] downward. Strokes cycle through fg_list.
    """
    import random
    data = load_canvas(workspace, slug)
    if region.get("type") != "rect":
        raise CanvasError("strand_shade region must be {'type':'rect',...} in cell space")
    x0, y0, x1, y1 = region["x0"], region["y0"], region["x1"], region["y1"]
    W, H = data["w"], data["h_cells"]
    x0, x1 = max(0, x0), min(W, x1)
    y0, y1 = max(0, y0), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        raise CanvasError(f"region ({x0},{y0})-({x1},{y1}) is empty")
    fg_list = [_check_color(c) for c in fg_list]
    dx, dy = direction
    mag = (dx * dx + dy * dy) ** 0.5 or 1.0
    dx, dy = dx / mag, dy / mag
    px_dir, py_dir = -dy, dx  # perpendicular, for jitter
    rng = random.Random(seed)
    go = data["glyph_override"]
    for i in range(n_strands):
        x_start = rng.uniform(x0, x1)
        y_start = rng.uniform(y0, y1)
        off = rng.uniform(-1, 1)
        fg = fg_list[i % len(fg_list)]
        for s in range(length):
            x = int(round(x_start + dx * s + px_dir * off))
            y = int(round(y_start + dy * s + py_dir * off))
            if x0 <= x < x1 and y0 <= y < y1:
                go[f"{y},{x}"] = [_RAMP[0], fg, data["bg"]]
    save_canvas(workspace, slug, data)
    return data


def make_patch_id(parent_path, row_offset, col_offset, window_rows, window_cols):
    """Deprecated. Lives in corpus/find_patches.py; kept for old importers."""
    payload = json.dumps([parent_path, int(row_offset), int(col_offset),
                           int(window_rows), int(window_cols)])
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_patch_id(patch_id):
    """Deprecated. See make_patch_id."""
    try:
        padded = patch_id + "=" * (-len(patch_id) % 4)
        payload = base64.urlsafe_b64decode(padded.encode()).decode()
        parent_path, row_offset, col_offset, window_rows, window_cols = json.loads(payload)
        return parent_path, row_offset, col_offset, window_rows, window_cols
    except Exception as e:
        raise CanvasError(f"invalid patch_id {patch_id!r}: {e}")


def _cp437_ok(ch):
    try:
        return len(ch) == 1 and len(ch.encode("cp437")) == 1
    except UnicodeEncodeError:
        return False


MAX_CELLS_PER_CALL = 400


def cells(workspace, slug, items):
    """Write individual cells.

    items: [[x, y, ch, fg, bg], ...] in CELL space; ch is one CP437 char or
    an int codepoint. Later items win. Returns (placed, errors).
    """
    data = load_canvas(workspace, slug)
    W, H = data["w"], data["h_cells"]
    go = data["glyph_override"]
    items = list(items or [])
    if len(items) > MAX_CELLS_PER_CALL:
        raise CanvasError(f"{len(items)} cells in one call; max is {MAX_CELLS_PER_CALL}")
    placed, errors = 0, []
    for i, it in enumerate(items):
        try:
            x, y, ch, fg, bg = it
            x, y = int(x), int(y)
            if not isinstance(ch, str):
                ch = chr(int(ch))
            if not _cp437_ok(ch):
                raise CanvasError(f"{ch!r} is not a single CP437 character")
            fg, bg = _check_color(fg), _check_color(bg)
            if not (0 <= x < W and 0 <= y < H):
                raise CanvasError(f"({x},{y}) is off the {W}x{H} canvas")
            go[f"{y},{x}"] = [ch, fg, bg]
            placed += 1
        except Exception as e:
            errors.append(f"item {i}: {e}")
    save_canvas(workspace, slug, data)
    return placed, errors


def stamp(workspace, slug, x, y, chars, fg, bg):
    """Place (chars, fg, bg) cell grids with top-left at cell (x, y).

    The caller decodes patch_id into grids, so this needs no corpus index.
    Returns (data, placed).
    """
    data = load_canvas(workspace, slug)
    W, H = data["w"], data["h_cells"]
    go = data["glyph_override"]
    x0, y0 = int(x), int(y)
    rows, cols = len(chars), (len(chars[0]) if len(chars) > 0 else 0)
    placed = 0
    for r in range(rows):
        row_idx = y0 + r
        if not (0 <= row_idx < H):
            continue
        for c in range(cols):
            col_idx = x0 + c
            if not (0 <= col_idx < W):
                continue
            ch = chars[r][c]
            ch = ch if isinstance(ch, str) else chr(int(ch))
            go[f"{row_idx},{col_idx}"] = [ch, int(fg[r][c]), int(bg[r][c])]
            placed += 1
    save_canvas(workspace, slug, data)
    return data, placed


def _sgr(fg, bg=0):
    """SGR for a color pair. Bright fg uses bold (1;3X), not 90-97, which ansilove renders black."""
    bright = fg > 7
    f = 30 + (fg & 7)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    # Lead with 0 (reset) so bold from a bright color doesn't leak into
    # the next dim color.
    return ("\x1b[0;1;%d;%dm" % (f, b)) if bright else ("\x1b[0;%d;%dm" % (f, b))


def render_canvas(data):
    """Render the canvas to one ANSI string per cell row. Mirrors HalfBlockCanvas.render()."""
    w, h_cells = data["w"], data["h_cells"]
    pixels, go = data["pixels"], data["glyph_override"]
    out = []
    for cell_row in range(h_cells):
        top_row = pixels[cell_row * 2]
        bot_row = pixels[cell_row * 2 + 1]
        parts = []
        last_fg, last_bg = None, None
        for x in range(w):
            key = f"{cell_row},{x}"
            if key in go:
                ch, fg, bg = go[key]
            else:
                top, bot = top_row[x], bot_row[x]
                if top == bot:
                    ch, fg, bg = " ", 7, top
                else:
                    ch, fg, bg = "\u2580", top, bot
            if (fg, bg) != (last_fg, last_bg):
                parts.append(_sgr(fg, bg))
                last_fg, last_bg = fg, bg
            parts.append(ch)
        out.append("".join(parts))
    return out


def _sig_block(out, title, handles, width=80):
    """Same layout as workspace/scratch/canvas.py's sig_block()."""
    out.append("")
    out.append(_sgr(13) + "\u2550" * width)

    def sigline(text_, fg):
        pad = max(0, width - len(text_))
        left = pad // 2
        return _sgr(12) + " " * left + _sgr(fg) + text_ + _sgr(12) + " " * (pad - left)

    out.append(sigline(handles + " / AGENTSCII", 15))
    out.append(sigline(title, 14))
    out.append(_sgr(13) + "\u2550" * width)


def save_ans(workspace, slug, out_path, title=None, handles="AGENTSCII", add_sig=True):
    """Write the canvas as a cp437 .ans at out_path (relative to workspace).

    The canvas JSON is kept, so it stays editable.
    """
    data = load_canvas(workspace, slug)
    out = render_canvas(data)
    if add_sig and title:
        _sig_block(out, title, handles, width=data["w"])
    raw = "\n".join(out) + "\x1b[0m\n"
    full_path = Path(workspace) / out_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(raw, encoding="cp437", errors="replace")
    return full_path


def metrics(workspace, slug):
    """Metrics for the current canvas via harness._compute_piece_metrics.

    Same function the gate uses, so there is one source for these numbers.
    Renders to a temp .ans rather than reimplementing the metric.
    """
    import tempfile
    import harness
    data = load_canvas(workspace, slug)
    out = render_canvas(data)
    with tempfile.NamedTemporaryFile("w", suffix=".ans", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\x1b[0m\n")
        tmp = fh.name
    try:
        return harness._compute_piece_metrics(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)


def slab_px(workspace, slug, x, y, w, h, color, light_direction="top-left",
            shadow_color=None, hi_color=None, side=None, side_w=0):
    """Draw a lit box in PIXEL space, shaded per face.

    side ("left"/"right") and side_w (pixels) add a second visible face.
    Each face gets its own brightness band so the form reads as a volume.
    """
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    dark = _check_color(shadow_color if shadow_color is not None else 0)
    hi = _check_color(hi_color if hi_color is not None else color)
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        raise CanvasError(f"w and h must be > 0, got {w}x{h}")

    faces = []
    if side in ("left", "right") and side_w > 0:
        side_w = min(int(side_w), w - 1)
        if side == "left":
            faces.append(("left", x, side_w))
            faces.append(("right", x + side_w, w - side_w))
        else:
            faces.append(("right", x + w - side_w, side_w))
            faces.append(("left", x, w - side_w))
    else:
        faces.append(("right", x, w))

    W, PH = data["w"], data["ph"]
    pixels = data["pixels"]
    _hit = set()
    for _face, fx, fw in faces:
        for py in range(max(0, y), min(PH, y + h)):
            row = pixels[py]
            for px in range(max(0, fx), min(W, fx + fw)):
                row[px] = color
                _hit.add((py >> 1, px))

    _drop_overrides(data, _hit)
    for face, fx, fw in faces:
        mask = {"type": "rect", "x0": fx, "y0": y, "x1": fx + fw, "y1": y + h}
        t_lo, t_hi = _face_band(face, light_direction)
        _shade_masked(data, mask, hi if t_lo < 0.35 else color, dark,
                      light_direction, t_lo=t_lo, t_hi=t_hi,
                      cull_band=False, rim=True, face_grad=True)
    data["last_shape"] = {"type": "rect", "x0": x, "y0": y,
                          "x1": x + w, "y1": y + h}
    save_canvas(workspace, slug, data)
    return data


def capsule_px(workspace, slug, ax, ay, bx, by, r, color,
               light_direction="top-left", shadow_color=None, hi_color=None):
    """Draw a capsule from (ax, ay) to (bx, by), shaded as a cylinder.

    For limbs, necks, pipes and tubes.
    """
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    dark = _check_color(shadow_color if shadow_color is not None else 0)
    hi = _check_color(hi_color if hi_color is not None else 15)
    ax, ay, bx, by, r = float(ax), float(ay), float(bx), float(by), float(r)
    if r <= 0:
        raise CanvasError(f"r must be > 0, got {r}")
    mask = {"type": "capsule", "ax": ax, "ay": ay, "bx": bx, "by": by, "r": r}

    W, PH = data["w"], data["ph"]
    pixels = data["pixels"]
    _hit = set()
    for py in range(PH):
        for px in range(W):
            if _pixel_mask_at(data, px, py, mask):
                pixels[py][px] = color
                _hit.add((py >> 1, px))

    cyl = dict(mask)
    # Two bands, as in sphere_px. The highlight band must be wide (0.30);
    # narrower ones get scattered by Bayer into speckle.
    _drop_overrides(data, _hit)
    _shade_masked(data, mask, hi, color, light_direction, light_x=ax, light_y=ay,
                  cyl=cyl, t_lo=0.0, t_hi=0.30)
    _shade_masked(data, mask, color, dark, light_direction, light_x=ax, light_y=ay,
                  cyl=cyl, t_lo=0.30, t_hi=1.0)
    data["last_shape"] = mask
    save_canvas(workspace, slug, data)
    return data


def crop(workspace, slug, x, y, w, h, scale=6):
    """Magnified render of a w x h CELL region plus its cell data.

    Returns (png_b64, text_dump). scale=6 renders each cell at 54x108, large
    enough to see glyph shape and cell seams, which the normal preview hides.
    """
    data = load_canvas(workspace, slug)
    rows_all = render_canvas_cells(data)
    x, y, w, h = int(x), int(y), int(w), int(h)
    sub = [r[x:x + w] for r in rows_all[y:y + h]]
    if not sub or not sub[0]:
        raise CanvasError(f"crop region ({x},{y},{w},{h}) is empty or off-canvas")

    import harness
    b64, _ = harness._rasterize_rows_to_png_b64(sub)
    if b64:
        import base64, io
        from PIL import Image
        im = Image.open(io.BytesIO(base64.b64decode(b64)))
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        buf = io.BytesIO(); im.save(buf, "PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

    lines = [f"cells ({x},{y}) {w}x{h} — glyph | fg,bg per cell:"]
    for ry, row in enumerate(sub):
        lines.append(f"  row {y+ry:2d}: " + " ".join(
            f"{ch if ch != ' ' else '_'}{fg:X}{bg:X}" for ch, fg, bg in row))
    return b64, "\n".join(lines)


def render_canvas_cells(data):
    """Like render_canvas(), but returns rows of (char, fg, bg) tuples."""
    w, h_cells = data["w"], data["h_cells"]
    pixels, go = data["pixels"], data["glyph_override"]
    out = []
    for cell_row in range(h_cells):
        top_row, bot_row = pixels[cell_row * 2], pixels[cell_row * 2 + 1]
        row = []
        for x in range(w):
            key = f"{cell_row},{x}"
            if key in go:
                ch, fg, bg = go[key]
            else:
                top, bot = top_row[x], bot_row[x]
                ch, fg, bg = (" ", 7, top) if top == bot else ("\u2580", top, bot)
            row.append((ch, fg, bg))
        out.append(row)
    return out


def self_check(workspace, slug):
    """Run the reviewer's glyph-only and colour-only tests on a canvas mid-build.

    Returns (glyphs_only_b64, colour_only_b64, density_report).
      glyphs_only: every cell one fg on black. If it still reads, the glyphs
                   carry the picture.
      colour_only: every glyph a full block. If it still reads, colour alone
                   carries it and the glyph layer is doing nothing.
    The report lists rows with near-uniform ink density.
    """
    import harness
    rows = render_canvas_cells(load_canvas(workspace, slug))
    glyphs_only = [[(ch, 7, 0) for ch, fg, bg in r] for r in rows]
    colour_only = [[("\u2588" if not (ch == " " and bg == 0) else " ",
                     bg if ch == " " else fg, bg) for ch, fg, bg in r]
                   for r in rows]
    g_b64, _ = harness._rasterize_rows_to_png_b64(glyphs_only)
    c_b64, _ = harness._rasterize_rows_to_png_b64(colour_only)

    INK = {"\u2588": 1.0, "\u2593": .75, "\u2592": .5, "\u2591": .25,
           "\u2580": .5, "\u2584": .5, " ": 0.0}
    lines = ["per-row ink density (a flat run of identical numbers is a "
             "'near-uniform row' before anyone calls it one):"]
    flat = 0
    for ry, row in enumerate(rows):
        vals = [INK.get(ch, .6) for ch, fg, bg in row]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        if var < 0.004 and mean > 0.05:
            flat += 1
            lines.append(f"  row {ry:2d}: mean {mean:.2f} var {var:.4f}  <-- FLAT")
    lines.append(f"{flat} of {len(rows)} rows are near-uniform.")

    # --- repeated rows -------------------------------------------------
    # Within-row variance cannot see a row that is a copy of the row above
    # it: _mask scored 0 near-uniform rows while ten of its twenty-one grid
    # rows were the same string. Compare each row to the previous one on ink
    # value per column, so two rows differing only in colour still count as
    # repeated -- the glyph layer is what carries form.
    # 0.90 separates the known-bad from the known-good set: worst run 9 rows
    # on _mask and _mask.v1, <=4 on duo3.s7 and five accepted gallery pieces.
    profs = [[INK.get(ch, .6) for ch, fg, bg in row] for row in rows]
    runs, start = [], None
    for i in range(1, len(rows)):
        a, b = profs[i - 1], profs[i]
        if max(sum(a) / len(a), sum(b) / len(b)) <= 0.03:
            same = False                      # two blank rows are not a defect
        else:
            same = sum(1 for x, y in zip(a, b) if abs(x - y) < 1e-9) / len(a) >= 0.90
        if same and start is None:
            start = i - 1
        elif not same and start is not None:
            runs.append((start, i - 1)); start = None
    if start is not None:
        runs.append((start, len(rows) - 1))
    runs = [(a, b) for a, b in runs if b > a]
    longest = max((b - a + 1 for a, b in runs), default=0)
    if runs:
        lines.append("")
        lines.append(f"REPEATED ROWS: {len(runs)} run(s), longest {longest} rows. "
                     "A row that repeats the row above it is a rule applied down "
                     "the canvas, not drawing.")
        for a, b in runs:
            lines.append(f"  rows {a}-{b} ({b - a + 1} rows) are >=90% identical")
    else:
        lines.append("")
        lines.append("REPEATED ROWS: none (no run of 2+ rows is >=90% identical).")

    # --- colour-only, stated explicitly --------------------------------
    hues = {(fg if ch != " " else bg)
            for row in rows for ch, fg, bg in row if INK.get(ch, .6) > 0}
    lines.append("")
    lines.append(f"COLOUR-ONLY CHECK: {len(hues)} distinct hue(s) over inked cells. "
                 "Look at the second image: if the subject still reads there, "
                 "colour is carrying the picture and the glyphs are decoration.")
    return g_b64, c_b64, "\n".join(lines)
