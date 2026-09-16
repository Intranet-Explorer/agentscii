"""Half-block pixel canvas: doubles vertical resolution by treating each
terminal cell as TWO stacked pixels (upper half-block char + fg/bg color).

Why this exists (found the hard way, 2026-09-16 session): a standard ANSI
cell is ~2x taller than wide. Every primitive built this session (eye(),
capsule(), the skull silhouette) had to carry a manual ASPECT=0.5 correction
factor to keep circles round -- and even then, low-resolution block-grid
curves alias badly (the eye() redesign failed 3 times at real call-site
radii because a 1-cell-thick ring just doesn't have enough pixels to read
as curved). That's a RESOLUTION problem, not a math problem -- no amount of
formula-tuning fixes too-few-pixels-per-curve.

Fix: use U+2580 (▀ UPPER HALF BLOCK) as a general-purpose 2-pixels-per-cell
primitive. Each cell's fg color = the top pixel, bg color = the bottom
pixel. A full ANSI canvas of W x H cells becomes a pixel space of W x (2H)
addressable pixels -- and because a cell is ~2x taller than wide, W x 2H
pixels are approximately SQUARE. Circles drawn in this pixel space are
round without any aspect correction at the call site.
"""
import math


class HalfBlockCanvas:
    """Pixel space is W wide x (2*H) tall. set_pixel/get_pixel address
    individual pixels; render() packs pairs of pixel-rows into real ANSI
    cells using UPPER HALF BLOCK with fg=top pixel color, bg=bottom pixel
    color (or a solid space with bg=color when both pixels match, which
    is cheaper and identical visually)."""

    def __init__(self, w, h_cells, bg=0):
        self.w = w
        self.h_cells = h_cells
        self.ph = h_cells * 2  # pixel-space height
        self.bg = bg
        self.pixels = [[bg for _ in range(w)] for _ in range(self.ph)]

    def in_bounds(self, px, py):
        return 0 <= px < self.w and 0 <= py < self.ph

    def set_pixel(self, px, py, color):
        if self.in_bounds(px, py):
            self.pixels[py][px] = color

    def get_pixel(self, px, py):
        if self.in_bounds(px, py):
            return self.pixels[py][px]
        return self.bg

    def fill_circle(self, cx, cy, r, color):
        """cx, cy, r all in PIXEL-SPACE units (already ~square) -- no
        aspect correction needed, that's the entire point of this canvas."""
        r0 = int(cx - r) - 1
        r1 = int(cx + r) + 1
        c0 = int(cy - r) - 1
        c1 = int(cy + r) + 1
        for py in range(c0, c1 + 1):
            for px in range(r0, r1 + 1):
                if math.hypot(px - cx, py - cy) <= r:
                    self.set_pixel(px, py, color)

    def ring(self, cx, cy, r, thickness, color):
        r0 = int(cx - r - thickness) - 1
        r1 = int(cx + r + thickness) + 1
        c0 = int(cy - r - thickness) - 1
        c1 = int(cy + r + thickness) + 1
        for py in range(c0, c1 + 1):
            for px in range(r0, r1 + 1):
                d = math.hypot(px - cx, py - cy)
                if r - thickness / 2 <= d <= r + thickness / 2:
                    self.set_pixel(px, py, color)

    def render(self):
        """Pack pixel pairs into real ANSI cell rows. Returns a list of
        SGR-coded strings, one per cell-row (self.h_cells of them), ready
        to join with '\\n' and write out."""
        out = []
        for cell_row in range(self.h_cells):
            top_row = self.pixels[cell_row * 2]
            bot_row = self.pixels[cell_row * 2 + 1]
            parts = []
            last_fg, last_bg = None, None
            for x in range(self.w):
                top, bot = top_row[x], bot_row[x]
                if top == bot:
                    # both pixels same color: draw as a plain space with
                    # that bg -- visually identical to a solid block, and
                    # cheaper than emitting the half-block glyph
                    ch, fg, bg = ' ', 7, top
                else:
                    ch, fg, bg = '\u2580', top, bot
                if (fg, bg) != (last_fg, last_bg):
                    parts.append(_sgr(fg, bg))
                    last_fg, last_bg = fg, bg
                parts.append(ch)
            out.append(''.join(parts))
        return out


def _sgr(fg, bg=0):
    f = (90 + (fg & 7)) if fg > 7 else (30 + fg)
    b = (100 + (bg & 7)) if bg > 7 else (40 + bg)
    return "\x1b[%d;%dm" % (f, b)
