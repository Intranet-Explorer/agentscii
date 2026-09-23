#!/usr/bin/env python3
"""canvas_tools.py -- persistent half-block canvas primitives for the
harness's canvas_* tools.

Built 2026-09-22 per direct user finding: raze's soul prompt instructed
"procedural generation you can then convert with chafa/jp2a" and to
write a real .py file for anything nontrivial -- the ONLY reason every
piece in scratch/ (427 files) is a generator script is that there was
no other way to draw. HalfBlockCanvas (workspace/scratch/halfblock.py)
was a module an agent had to import INSIDE a script; there was no tool
that let the model draw directly. This module is the actual drawing
surface behind the harness's canvas_new/canvas_fill_px/canvas_circle_px/
canvas_shade/canvas_text/canvas_stamp/canvas_save tools -- real tool
calls, no code required.

One canvas = one on-disk JSON file under workspace/canvases/<slug>.json,
so state persists across tool calls (and across shifts/restarts, same
as scratch/ files always have). The data model mirrors
workspace/scratch/halfblock.py's HalfBlockCanvas exactly on purpose:
  - "pixels": a (width) x (height*2) grid of raw color indices (0-15),
    addressed in PIXEL space -- each cell is 2 pixels tall (upper/lower
    half-block), which is what makes circles/fills genuinely round with
    zero aspect correction (see halfblock.py's docstring for why).
  - "glyph_override": a sparse {"row,col": [char, fg, bg]} map in CELL
    space, taking precedence over the packed pixel pair for that cell --
    this is how a density-dither glyph, a text character, or a stamped
    patch cell (all of which are one full real glyph, not a solid
    half-block color pair) gets placed without disturbing the pixel
    layer underneath.

Deliberately NOT implemented by importing workspace/scratch/*.py at
call time, even though canvas.py/halfblock.py already have equivalent
logic (sgr(), shade_ramp(), HalfBlockCanvas.render()): those files are
agent-writable (raze/hollis can write_file over them), and the
harness's own tool dispatch must not depend on code the agents can
edit or accidentally break. The small amount of duplicated logic here
(sgr formatting, the shade_ramp algorithm, half-block packing) is kept
byte-for-byte equivalent to its scratch/ counterpart -- see each
function's docstring for which one it mirrors.
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
    for py in range(y0c, y1c):
        row = pixels[py]
        for px in range(x0c, x1c):
            row[px] = color
    # Tracked so canvas_shade can default to "shade what I just drew"
    # without the caller having to restate the shape -- see shade()'s
    # docstring for why this replaced rectangle-region shading.
    data["last_shape"] = {"type": "rect", "x0": x0c, "y0": y0c, "x1": x1c, "y1": y1c}
    save_canvas(workspace, slug, data)
    return data


def circle_px(workspace, slug, cx, cy, r, color):
    """Fill a circle in PIXEL space -- same fill_circle() math as
    halfblock.py's HalfBlockCanvas: pixel space is ~square (W wide x
    2*height_cells tall), so circles come out genuinely round with no
    aspect correction at the call site."""
    data = load_canvas(workspace, slug)
    color = _check_color(color)
    W, PH = data["w"], data["ph"]
    cx, cy, r = float(cx), float(cy), float(r)
    if r <= 0:
        raise CanvasError(f"r must be > 0, got {r}")
    r0, r1 = int(cx - r) - 1, int(cx + r) + 1
    c0, c1 = int(cy - r) - 1, int(cy + r) + 1
    pixels = data["pixels"]
    for py in range(max(0, c0), min(PH, c1 + 1)):
        row = pixels[py]
        for px in range(max(0, r0), min(W, r1 + 1)):
            if math.hypot(px - cx, py - cy) <= r:
                row[px] = color
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

# Face normals in the same 2D screen convention: which way each side of
# a slab points. A flat form has no curvature, so its brightness comes
# from face orientation vs the light, not from a surface normal that
# varies per pixel.
_FACE_NORMALS = {
    "top": (0.0, -1.0), "bottom": (0.0, 1.0),
    "left": (-1.0, 0.0), "right": (1.0, 0.0),
}


def _face_band(face, light_direction):
    """(t_lo, t_hi) brightness band for one face of a flat form under a
    given light. Lambert on the face normal sets the base brightness;
    the band's WIDTH is what still lets the face carry a gradient across
    itself (lit edge -> far edge) instead of being one flat tone."""
    lv = _LIGHT_VECTORS.get(light_direction, (-0.6, -0.6, 0.53))
    nx, ny = _FACE_NORMALS[face]
    lam = max(0.0, nx * lv[0] + ny * lv[1])       # 0 = edge-on/away
    base = 1.0 - (0.15 + 0.85 * lam)              # 0 = brightest
    # Band width drives half-block packing: a vertical Bayer pair differs
    # by ~0.75 step, so the two pixels of a cell only land on different
    # ramp steps when the band spans enough steps for boundaries to fall
    # inside the face. 0.22 gave 5.1% half_block (measured); 0.40 spans
    # ~3 steps and packs real ▀ cells through the face.
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
    """Byte-for-byte the same algorithm as workspace/scratch/canvas.py's
    shade_ramp(): fg is ALWAYS from_color, bg is ALWAYS to_color, and
    only the GLYPH varies across steps (solid-full -> ▓ -> ▒ -> ░ ->
    solid-space) -- that's the real ACiD dithering trick for faking
    intermediate brightness a 16-color palette doesn't actually have."""
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
    """True if pixel (px, py) is inside `mask`. mask is one of:
    {"type": "rect", "x0","y0","x1","y1"} (PIXEL space),
    {"type": "circle", "cx","cy","r"} (PIXEL space),
    {"type": "color", "color"} (any pixel currently equal to this color --
      shade the region of a given color, per user direction 2026-09-22),
    or None (falls back to the canvas's last drawn shape)."""
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
    """Shared masked-shading core for shade() and sphere_px(). Shape-aware,
    unlike the original rectangle-only shade() (real bug, found live
    2026-09-22 on raze's first canvas piece, scratch/_eye_emblem.ans: a
    circle shaded with the old rectangle shade() came back as a hard
    rectangular grey/cyan band cutting across the round silhouette,
    because shade() wrote glyph_override for every cell in its bounding
    box regardless of what shape was actually there -- and because
    glyph_override is a full-cell flat glyph, it also WIPED the circle's
    real half-block edge pixels, which is why half_block_pct collapsed to
    1.3% on that piece (measured: a circle alone scores ~8.5% half_block
    in its bbox; the same circle after the old shade() scored 0.27%).

    Fix, two parts:
    1. Only cells where the mask actually covers get touched at all --
       shading a circle no longer paints outside it.
    2. EDGE cells (mask covers exactly one of the cell's two pixels, not
       both) get a per-PIXEL color write instead of a glyph_override --
       this preserves the real half-block ▀ boundary (one pixel shaded,
       one pixel whatever was already there) instead of flattening the
       whole cell to one glyph. Only fully-interior cells (both pixels
       inside the mask) get the flat dither glyph, which is correct --
       that's genuinely one solid surface at that point, not an edge.

    light_x/light_y (pixel-space) override light_direction with a real
    point light -- used by sphere_px for radial falloff from center
    instead of a linear directional gradient."""
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
            # True Lambertian sphere shading: the gradient follows the
            # SURFACE NORMAL, not 2D distance from a point. The old
            # version used hypot(px-light_x, py-light_y)/max_d, which
            # is a flat radial wash -- combined with a 5-step hard ramp
            # it produced the straight diagonal bands the user flagged.
            scx, scy, sr = sphere["cx"], sphere["cy"], max(1e-6, sphere["r"])
            lvx, lvy = light_x - scx, light_y - scy
            lvz = sr * 0.85  # light sits in front of the sphere
            llen = math.sqrt(lvx * lvx + lvy * lvy + lvz * lvz) or 1.0
            lvx, lvy, lvz = lvx / llen, lvy / llen, lvz / llen

            def light_t(px, py):
                nx, ny = (px - scx) / sr, (py - scy) / sr
                # pixels are half as tall as wide -- normals must use
                # the same aspect the renderer packs at, or the
                # terminator reads as an ellipse on a round silhouette
                d2 = nx * nx + ny * ny
                nz = math.sqrt(max(0.0, 1.0 - d2))
                lam = nx * lvx + ny * lvy + nz * lvz
                lam = max(0.0, min(1.0, lam))
                # Wrapped/soft lighting + ambient: pure Lambert drives
                # most of the lit hemisphere to full brightness, which
                # renders as one big FLAT highlight blob with all the
                # gradient crammed into the terminator (seen live on
                # the first test render). Remapping spreads the ramp
                # across the whole visible surface, which is what a
                # real ACiD sphere looks like -- and gives the gate a
                # genuine gradient to find instead of a flat cap.
                lam = 0.12 + 0.88 * (0.5 + 0.5 * (2.0 * lam - 1.0) ** 0.6
                                     if lam >= 0.5 else
                                     0.5 - 0.5 * (1.0 - 2.0 * lam) ** 0.6)
                return 1.0 - lam
        elif cyl is not None:
            # Cylinder: the normal curves across the SHORT axis only and
            # is constant along the length -- that's what makes a limb or
            # a pipe read as round rather than as a flat bar.
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
                # Flat faces: add a mild distance falloff from the lit
                # corner so the face varies along BOTH axes. Without it
                # a tall face is uniform down its length and packs no
                # half-blocks (measured: 5.2% on the first monolith).
                t = 0.65 * t + 0.35 * min(1.0, math.hypot(fx - (0.0 if "left" in light_direction or light_direction in ("top","bottom") else 1.0), fy - (0.0 if "top" in light_direction else 1.0)) / 1.414)
            return t

    stops = _shade_ramp(from_color, to_color, 5)
    last = len(stops) - 1

    def step_at(px, py):
        """Continuous ramp position + ordered (Bayer) dither, per PIXEL.
        The old code quantised one t per CELL to 5 hard steps, so a
        gradient became 5 visible bands and every interior cell was a
        whole-cell glyph (half_block stuck near 0). Bayer breaks the
        bands up, and resolving per pixel means the two pixels in a
        cell can land on different steps -- which is exactly what
        produces a real ▀ half-block interior."""
        t = light_t(px, py)
        if cull_band:
            t = (t - t_lo) / max(1e-6, t_hi - t_lo)
        else:
            # face mode: squeeze the whole face into its brightness band
            # instead of culling -- a face lit edge-on must still show a
            # gradient ACROSS itself, just a darker one.
            t = t_lo + max(0.0, min(1.0, t)) * (t_hi - t_lo)
        s = max(0.0, min(1.0, t)) * last
        return max(0, min(last, int(math.floor(s + _bayer(px, py) + 0.5))))

    def _in_band(px, py):
        if not cull_band:
            return True
        t = light_t(px, py)
        return t_lo <= t < t_hi or (t_hi >= 1.0 and t >= t_hi)

    def solid_of(step):
        """The solid color a pixel at this step represents, for when the
        two pixels of a cell disagree and we pack them as a half-block
        instead of a dither glyph."""
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
                    # Interior cell whose two pixels sit on different
                    # ramp steps -> pack as a REAL half-block pair
                    # instead of flattening to one glyph. This is where
                    # half_block% actually comes from (_orb.v59, the
                    # house bar, is 37.9% ▀ and 32.1% ░▒▓ -- both, not
                    # one or the other).
                    if key in go:
                        del go[key]
                    pixels[py_top][col] = solid_of(st_t)
                    pixels[py_bot][col] = solid_of(st_b)
            else:
                # Edge cell: recolor only the masked pixel, leave the
                # other pixel and any existing glyph_override alone --
                # this is what keeps the silhouette's round boundary
                # genuinely round instead of getting square-stepped by
                # a full-cell glyph at every edge.
                if key in go:
                    del go[key]  # a stale flat glyph would hide the pixel split
                py_target = py_top if top_in else py_bot
                pixels[py_target][col] = solid_of(step_at(col, py_target))

    if rim:
        # Edges facing the light get a brighter rim -- without it a slab
        # reads as a flat fill with noise, because nothing marks where
        # one face stops and the next begins.
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
    """Apply real density-dither shading (shade_ramp) to a SHAPE, not a
    rectangle -- region defaults to whatever canvas_fill_px/
    canvas_circle_px drew last on this canvas, or pass {"type":"rect",...}/
    {"type":"circle",...}/{"type":"color","color":N} explicitly ({"color":N}
    shades every pixel currently that color, wherever it is -- the "shade
    the region of a given color" option). Interior cells get a real
    dither glyph; edge cells get a per-pixel recolor so the shape's
    boundary (e.g. a circle's round edge) stays genuinely round instead
    of being square-stepped by a full-cell glyph. See _shade_masked's
    docstring for the bug this replaced."""
    data = load_canvas(workspace, slug)
    from_color, to_color = _check_color(from_color), _check_color(to_color)
    _shade_masked(data, region, from_color, to_color, light_direction)
    save_canvas(workspace, slug, data)
    return data


def sphere_px(workspace, slug, cx, cy, r, color, light_x, light_y, shadow_color=None, hi_color=None):
    """One call: a lit sphere -- draws the circle AND shades it with a
    real point-light falloff from (light_x, light_y), so the gradient
    follows the sphere's actual curvature (radial from the light point)
    instead of a linear directional wash, and the edge stays genuinely
    round (see _shade_masked). Added 2026-09-22 per user direction:
    "spheres, eyes, heads and orbs are most of what raze draws, and it
    shouldn't have to compose one from a fill plus a shade" -- circle_px
    + shade still work separately for anything that isn't simply "a lit
    ball", but this is the one-call path for the common case.
    shadow_color defaults to a darker step of the same hue family via
    canvas.py's ramp() convention if not given explicitly -- callers
    should generally just pass the dim end of ramp(hue_name) here."""
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
    for py in range(max(0, c0), min(PH, c1 + 1)):
        row = pixels[py]
        for px in range(max(0, r0), min(W, r1 + 1)):
            if math.hypot(px - cx, py - cy) <= r:
                row[px] = color
    mask = {"type": "circle", "cx": cx, "cy": cy, "r": r}
    data["last_shape"] = mask
    # Two-band shading. One band (bright -> dark) can only ramp from a
    # SOLID █ at the lit end, so the highlight renders as a flat cap no
    # matter how smooth the falloff is -- measured live on the first
    # test render: a solid █ run straight across the highlight row.
    # Shading the lit half from hi_color down to color, then the dark
    # half from color down to shadow, gives the bright side a real
    # dithered gradient too. hi_color defaults to 15 (bright white),
    # the usual ACiD specular.
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
    """Place literal characters starting at cell (x, y), one per cell,
    left to right -- for sig blocks, labels, title cards. (Not a
    blocky wordmark font -- see canvas_wordmark for that.)"""
    data = load_canvas(workspace, slug)
    fg, bg = _check_color(fg), _check_color(bg)
    W, H = data["w"], data["h_cells"]
    row = int(y)
    if not (0 <= row < H):
        raise CanvasError(f"y={row} out of bounds (canvas is {H} cells tall)")
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


# Same 5x7 block-letter font as workspace/scratch/canvas.py's GLYPHS_5x7,
# kept as a literal copy here (not imported) for the same reason stated
# in this module's header docstring -- the harness's own tool dispatch
# must not depend on agent-editable scratch/ files.
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
    """Draw text as large 5x7 block letters -- the wordmark/title-card
    primitive canvas_text can't do (canvas_text is one glyph per cell,
    for sig blocks and labels; this is for a real logo/title). Same font
    and scale-2-for-legibility convention as scratch/canvas.py's
    block_letters() (kept as a literal copy, see the module docstring
    for why this file doesn't import scratch/). Returns the total pixel
    width used, so the caller can center a word before drawing."""
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
    """Mirror the canvas's authored half onto the other half -- axis='v'
    (vertical split line, left half -> right, the common case for
    symmetric creatures/faces/totems) or axis='h' (horizontal split,
    top half -> bottom). Draw your content in the left/top half only,
    then call this once. Same convention as scratch/canvas.py's
    mirror()."""
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
    """Directional stroke texture for fur/hair/grain -- many short strokes
    following a consistent direction, cycling through fg_list so adjacent
    strokes read as distinct marks instead of blurring into one mass.
    Same technique as scratch/canvas.py's strand_shade() (see that
    docstring for the real-reference studied), simplified to a fixed
    direction + rectangular region instead of per-point callables (a
    tool-call argument can't carry a Python function) -- pass region as
    {"type":"rect","x0","y0","x1","y1"} in CELL space, direction as
    [dx, dy] (e.g. [0,1] combed downward, [1,1] diagonal)."""
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
    """Deprecated alias -- the real implementation now lives in
    corpus/find_patches.py (find_patches/find_patches_clip attach
    patch_id to every hit directly, so this module never needs to
    construct one itself). Kept only so any external caller that
    imported it from here before the move doesn't break."""
    payload = json.dumps([parent_path, int(row_offset), int(col_offset),
                           int(window_rows), int(window_cols)])
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_patch_id(patch_id):
    """Deprecated alias -- see make_patch_id's docstring."""
    try:
        padded = patch_id + "=" * (-len(patch_id) % 4)
        payload = base64.urlsafe_b64decode(padded.encode()).decode()
        parent_path, row_offset, col_offset, window_rows, window_cols = json.loads(payload)
        return parent_path, row_offset, col_offset, window_rows, window_cols
    except Exception as e:
        raise CanvasError(f"invalid patch_id {patch_id!r}: {e}")


def stamp(workspace, slug, x, y, chars, fg, bg):
    """Place a retrieved patch's real (chars, fg, bg) cell grids onto
    the canvas with top-left corner at cell (x, y). Caller (the
    canvas_stamp tool in harness.py) is responsible for decoding
    patch_id -> grids via corpus/find_patches.py's _load_patch_grids;
    this function just does the placement, so it stays testable
    without a live corpus index."""
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
            go[f"{row_idx},{col_idx}"] = [chr(int(chars[r][c])), int(fg[r][c]), int(bg[r][c])]
            placed += 1
    save_canvas(workspace, slug, data)
    return data, placed


def _sgr(fg, bg=0):
    """Same bright-color convention as workspace/scratch/canvas.py's
    sgr(): classic bold-prefix form (1;3X), not aixterm 90-97 -- see
    that function's docstring for why (ansilove renders 90-97 as flat
    black)."""
    bright = fg > 7
    f = 30 + (fg & 7)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return ("\x1b[1;%d;%dm" % (f, b)) if bright else ("\x1b[%d;%dm" % (f, b))


def render_canvas(data):
    """Pack the canvas's pixel pairs + glyph_override into real ANSI
    cell-row strings -- same logic as halfblock.py's
    HalfBlockCanvas.render(), operating on the plain-dict form instead
    of the class."""
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
    """Render the canvas and write it as a real, hygiene-normal .ans
    file (cp437 on disk, standalone reset tail) at out_path (relative
    to workspace). Does NOT delete the canvas JSON -- the canvas stays
    editable/re-saveable after this call."""
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
    """Real measured metrics for the CURRENT canvas, using the harness's
    own _compute_piece_metrics -- the same function the gate and the
    submit report use. Added 2026-09-22: raze was self-reporting
    half_block numbers computed by ad-hoc scripts that came out ~3x off
    the canonical value (claimed 15.9%/12.1% on watcher v2/v3, actually
    4.7%/4.2%), so there is now one number and one source for it.
    Renders to a temp .ans rather than reimplementing the metric."""
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
    """A lit BOX, not a flat fill. Flat-sided forms (torsos, limbs,
    buildings, panels, frames) have no curvature, so shading comes from
    each face's orientation vs the light plus a gradient across the face
    from its lit edge to its far edge, with Bayer carrying the
    transition and light-facing edges getting a brighter rim.

    side/side_w optionally draw a second visible face (the classic
    two-face monolith): side is "left"/"right", side_w its width in
    pixels. The two faces take DIFFERENT brightness bands from their
    normals, which is what makes the form read as a solid volume rather
    than a rectangle with noise in it.
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
    for _face, fx, fw in faces:
        for py in range(max(0, y), min(PH, y + h)):
            row = pixels[py]
            for px in range(max(0, fx), min(W, fx + fw)):
                row[px] = color

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
    """A lit capsule: rectangle with rounded ends, shaded as a CYLINDER
    (normal curves across the short axis, constant along the length).
    The most common figure element -- arms, legs, necks, pipes, tubes.
    One call, because composing it from a rect plus two circles plus a
    shade never produced a form that read as round."""
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
    for py in range(PH):
        for px in range(W):
            if _pixel_mask_at(data, px, py, mask):
                pixels[py][px] = color

    cyl = dict(mask)
    # two bands, same reason as sphere_px: a single band ramps from a
    # SOLID glyph at the lit end and renders the highlight as a flat cap
    # Narrow highlight bands shatter into speckle: the specular lands
    # thinner than a cell and Bayer scatters it (seen live -- the first
    # capsule render was white dots, not a band). 0.30 keeps the bright
    # band wide enough to read as a continuous stripe down the length.
    _shade_masked(data, mask, hi, color, light_direction, light_x=ax, light_y=ay,
                  cyl=cyl, t_lo=0.0, t_hi=0.30)
    _shade_masked(data, mask, color, dark, light_direction, light_x=ax, light_y=ay,
                  cyl=cyl, t_lo=0.30, t_hi=1.0)
    data["last_shape"] = mask
    save_canvas(workspace, slug, data)
    return data
