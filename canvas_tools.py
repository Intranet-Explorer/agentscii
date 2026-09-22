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
    save_canvas(workspace, slug, data)
    return data


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


def shade(workspace, slug, x0, y0, x1, y1, from_color, to_color, light_direction):
    """Apply real density-dither shading (shade_ramp, see above) across
    a rectangular region in CELL space, from_color at the edge nearest
    light_direction fading to to_color at the far edge. Writes
    glyph_override for every cell in the region -- this REPLACES
    whatever pixel color was there, since a dither glyph is a full-cell
    glyph, not a solid half-block color pair."""
    data = load_canvas(workspace, slug)
    from_color, to_color = _check_color(from_color), _check_color(to_color)
    if light_direction not in _DIRECTIONS:
        raise CanvasError(
            f"light_direction must be one of {sorted(_DIRECTIONS)}, got {light_direction!r}"
        )
    fn = _DIRECTIONS[light_direction]
    W, H = data["w"], data["h_cells"]
    cx0, cx1 = sorted((int(x0), int(x1)))
    cy0, cy1 = sorted((int(y0), int(y1)))
    cx0, cx1 = max(0, cx0), min(W, cx1)
    cy0, cy1 = max(0, cy0), min(H, cy1)
    if cx1 <= cx0 or cy1 <= cy0:
        raise CanvasError(f"region ({x0},{y0})-({x1},{y1}) is empty after clamping to canvas bounds")
    w_span = max(1, cx1 - cx0 - 1)
    h_span = max(1, cy1 - cy0 - 1)
    stops = _shade_ramp(from_color, to_color, 5)
    go = data["glyph_override"]
    for row in range(cy0, cy1):
        fy = (row - cy0) / h_span
        for col in range(cx0, cx1):
            fx = (col - cx0) / w_span
            t = fn(fx, fy)
            idx = max(0, min(len(stops) - 1, int(t * (len(stops) - 1))))
            ch, fg, bg = stops[idx]
            go[f"{row},{col}"] = [ch, fg, bg]
    save_canvas(workspace, slug, data)
    return data


def text(workspace, slug, x, y, text_str, fg, bg):
    """Place literal characters starting at cell (x, y), one per cell,
    left to right -- for sig blocks, labels, title cards. (Not a
    blocky wordmark font -- that's still scratch/canvas.py's
    block_letters() inside a script, if a piece wants a large logo.)"""
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
