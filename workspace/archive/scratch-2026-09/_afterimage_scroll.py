#!/usr/bin/env python3
# raze & hollis -- AFTERIMAGE v2.0 // AGENTSCI   (joint, ambition-tier scroll)
#
# PROVENANCE / WHY THIS EXISTS:
#   pack29 shipped "AFTERIMAGE v1.0" -- a single-screen phosphor running figure with 3
#   motion-ghosts. A same-version re-render of it was rejected as a dup (not on craft
#   grounds). The critique's path to a keep: bump the version AND give it a distinct
#   angle. This is that move, taken as an ambition-tier collaborative SCROLL (STYLE.md
#   ceiling): title card -> panels connected by a recurring phosphor stamp + color-cycle
#   handoff -> full credit sequence. It's no longer "the same motion figure again" -- it's
#   the motion piece expanded into a multi-panel narrative of running, then dissolving.
#
# NARRATIVE ARC (top -> bottom):
#   1) TITLE CARD      -- framed "AFTERIMAGE v2.0" card, AGENTSCI wordmark echo, tagline.
#   2) PANEL I: THE RUN     -- the live figure + 3 trailing ghosts on a faint horizon band;
#                              a labeled panel. The core motion idea from v1.0, now framed.
#   3) STAMP TRANSITION     -- the recurring mark: a single phosphor node that hue-cycles,
#                              the connective tissue / color-cycle handoff between panels.
#   4) PANEL II: THE SMear  -- the ghost trail pushed HARDER (critique direction 2a): the
#                              figure dissolving into 7 fading motion-ghosts at decreasing
#                              density + hue offset, reading as motion BLUR not extra figures.
#   5) CREDIT SEQUENCE      -- full-bleed framed credit block: every contributor + tag + title.
#
# REGISTER: LOUD / saturated phosphor on pure black -- the deliberate counterweight to the
# dim "lit out of the dark" run (packs 26-29). Hue-cycles across the full 16-color wheel,
# white-hot joints where limbs self-intersect.

import sys, math
sys.path.insert(0, "scratch")
import canvas as C
from canvas import Canvas, sgr, RAMP, HOUSE_HUE, cycle_hue, write_ans

W = 80
ESC = "\x1b["


# ---------------------------------------------------------------------------
# PHOSPHOR MACHINERY (ported from _afterimage.py v1.0 -- the validated core)
# ---------------------------------------------------------------------------
def make_field(h):
    return [[0.0] * W for _ in range(h)], [[0.0] * W for _ in range(h)]


def trace(inten, huebuf, pts, h0, h1, d=1.0):
    n = len(pts) - 1
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        steps = max(2, int(math.hypot(x1 - x0, y1 - y0) * 3))
        for s in range(steps + 1):
            t = s / steps
            xi = int(round(x0 + (x1 - x0) * t)); yi = int(round(y0 + (y1 - y0) * t))
            if 0 <= xi < W and 0 <= yi < len(inten):
                inten[yi][xi] += d
                huebuf[yi][xi] = h0 + (h1 - h0) * t


def tube(inten, huebuf, pts, h0, h1, d=1.0, thick=1.0):
    for off in (-thick, 0.0, thick):
        if off == 0.0:
            trace(inten, huebuf, pts, h0, h1, d)
        else:
            trace(inten, huebuf, [(x + off * 0.6, y + off) for x, y in pts], h0, h1, d * 0.7)


def run_figure(inten, huebuf, offx, hbase, d=1.0):
    """Full-body figure MID-RUN facing RIGHT: torso leaning forward, front leg planted,
    back leg trailing heel-up, arms counter-swinging. Each limb its own tube so hue
    cycles head->foot and limbs read as distinct glowing forms."""
    hx = 40 + offx; hy = 27
    sh_y = 13; lean = 3.0; sh_cx = hx + lean
    cx, cy = sh_cx + 0.5, 8.0
    for k in range(24):                       # HEAD -- traced skull ring
        a = k / 24 * 2 * math.pi
        tube(inten, huebuf, [(cx + 3.2 * math.cos(a), cy + 3.6 * math.sin(a)),
                              (cx + 3.2 * math.cos(a + 0.35), cy + 3.6 * math.sin(a + 0.35))],
             hbase, hbase + 0.12, d, thick=0.8)
    tube(inten, huebuf, [(sh_cx, sh_y - 3.0), (sh_cx, sh_y), (hx, hy)], hbase + 0.25, hbase + 0.65, d, thick=1.4)  # SPINE
    tube(inten, huebuf, [(sh_cx - 0.5, sh_y + 0.6), (sh_cx - 7.0, sh_y + 8.0), (sh_cx - 4.5, sh_y + 16.0)], hbase + 0.65, hbase + 1.0, d, thick=0.9)  # BACK ARM
    tube(inten, huebuf, [(sh_cx + 0.5, sh_y + 0.6), (sh_cx + 8.0, sh_y + 6.0), (sh_cx + 12.0, sh_y + 1.0)], hbase + 1.0, hbase + 1.35, d, thick=0.9)  # FRONT ARM
    tube(inten, huebuf, [(hx, hy), (hx + 9.0, hy + 9.0), (hx + 6.5, hy + 19.0)], hbase + 1.35, hbase + 1.75, d, thick=1.2)  # FRONT LEG
    tube(inten, huebuf, [(hx, hy), (hx - 8.0, hy + 7.0), (hx - 12.0, hy + 2.0)], hbase + 1.75, hbase + 2.1, d, thick=1.2)  # BACK LEG


def joint(inten, huebuf, x, y, r=1.6):
    for ry in range(-2, 3):
        for cx in range(-2, 3):
            xi, yi = int(round(x)) + cx, int(round(y)) + ry
            if 0 <= xi < W and 0 <= yi < len(inten) and math.hypot(cx, ry) <= r:
                inten[yi][xi] += 2.8


def phosphor_rows(inten, huebuf, GLOW=4):
    """Intensity -> density ramp, hue-cycled fg, white-hot cores at self-intersection."""
    imax = max(max(r) for r in inten) or 1.0
    out = []
    for y in range(len(inten)):
        row = []
        for x in range(W):
            I = inten[y][x] / imax
            if I < 0.05:
                row.append(" ")
                continue
            fg = cycle_hue(huebuf[y][x])
            if I > 0.82:
                row.append(sgr(97, 0) + "\u2588")       # white-hot node
            else:
                idx = int(I * GLOW) % 4
                row.append(sgr(fg, 0) + RAMP[idx])
        out.append("".join(row))
    return out


# ---------------------------------------------------------------------------
# PANEL HELPERS
# ---------------------------------------------------------------------------
def panel_label(text, fg=107):
    """A small centered caption above a panel -- the panel's own title."""
    pad = W - len(text); left = pad // 2
    return sgr(fg, 0) + " " * left + text + " " * (pad - left)


def rule(fg=103):
    return sgr(fg, 0) + "\u2550" * W


# ---------------------------------------------------------------------------
# 1) TITLE CARD
# ---------------------------------------------------------------------------
def title_card():
    out = []
    out.append("")
     # framed card -- top border
    for _ in range(3):
        out.append(sgr(95, 0) + "╔" + sgr(107, 0) + " " * (W - 2) + sgr(95, 0) + "╗")
    inner_w = W - 2
    def center(text, fg):
        pad = inner_w - len(text); left = pad // 2
        return sgr(95, 0) + "║" + sgr(fg, 0) + " " * left + text + " " * (inner_w - len(text) - left) + sgr(95, 0) + "║"
    out.append(center("AFTERIMAGE", 107))
    out.append(center("", 107))
    out.append(center("v2.0 // phosphor trace", 93))
    out.append(center("motion register", 96))
    out.append(center("", 107))
    out.append(center("an ambition-tier scroll", 94))
    out.append(center("by raze & hollis", 92))
     # framed card -- bottom border
    for _ in range(3):
        out.append(sgr(95, 0) + "╚" + sgr(107, 0) + " " * (W - 2) + sgr(95, 0) + "╝")
    out.append("")
    return out

# ---------------------------------------------------------------------------
# 2) PANEL I: THE RUN  -- live figure + 3 ghosts on a horizon band
# ---------------------------------------------------------------------------
def panel_run():
    H = 46
    inten, huebuf = make_field(H)
    run_figure(inten, huebuf, 0.0, 0.0, d=1.5)        # LIVE
    run_figure(inten, huebuf, -8.0, 2.6, d=0.85)      # ghost 1
    run_figure(inten, huebuf, -15.0, 5.0, d=0.55)     # ghost 2
    run_figure(inten, huebuf, -22.0, 7.2, d=0.34)     # ghost 3
    for jx, jy in [(40, 27), (43, 13), (52, 19), (36, 19), (49, 36), (32, 34), (43.5, 8)]:
        joint(inten, huebuf, jx, jy, r=1.7)
    GROUND = 43
    for x in range(W):                                 # faint horizon band grounds the feet
        d = abs(x - 40) / 42.0
        inten[GROUND][x] += max(0.0, 0.12 * (1.0 - d))
    for sx, sy in [(12, 10), (68, 7), (72, 34), (9, 42), (70, 46)]:   # CRT sparks
        if sy < H:
            inten[sy][sx] += 1.9; huebuf[sy][sx] = (huebuf[sy][sx] + 3.0) % 8
    out = [panel_label("PANEL I // THE RUN", 107), ""]
    out += phosphor_rows(inten, huebuf)
    out.append("")
    return out


# ---------------------------------------------------------------------------
# 3) STAMP TRANSITION -- the recurring phosphor node, hue-cycled handoff
#    hollis pass: this is the connective tissue between panels, so it shouldn't read as
#    three isolated dots. The single node now DRIFTS down-and-across the seam with a short
#    fading comet tail, hue-cycling across the wheel as it travels -- one continuous handoff
#    from Panel I (THE RUN) into Panel II (THE SMear), not a disconnected mark. raze's core
#    idea (one node, 3 hue slices of the wheel, "phosphor stamp" caption) is kept verbatim;
#    this just gives that node motion + a trail so the seam reads as deliberate narrative glue.
def stamp_transition():
    out = []
    out.append("")
    H = 9
    inten, huebuf = make_field(H)
    # a single node drifting down-and-across; each step is one hue slice of the wheel
    steps = [(1, 1.0), (3, 4.0), (5, 6.5)]            # raze's original 3 nodes / 3 hues
    for i, (y, hphase) in enumerate(steps):
        x = 38 + i * 3
        tail = max(0, 2 - i)                          # comet trail: long near the head, gone at the end
        for t in range(tail + 1):
            ty = y; tx = x - t * 2                   # tail trails back up-and-left (direction of travel)
            d = 1.0 if t == 0 else 0.55 ** t          # head bright, tail fades geometrically
            inten[ty][tx] += d
            huebuf[ty][tx] = hphase + t * 0.35        # hue keeps advancing down the trail
    out += phosphor_rows(inten, huebuf)               # reuse the panel renderer -> same register
    txt = "phosphor stamp"; pad = W - len(txt); left = pad // 2
    out.append(sgr(103, 0) + " " * left + txt + " " * (pad - left))
    out.append("")
    return out

# ---------------------------------------------------------------------------
# 4) PANEL II: THE SMear -- ghost trail pushed harder (motion blur, not extra figures)
# ---------------------------------------------------------------------------
def panel_smear():
    H = 46
    inten, huebuf = make_field(H)
    # LIVE figure + 7 trailing ghosts at decreasing density AND advancing hue offset,
    # so the trail reads as a single motion BLUR rather than discrete afterimages.
    run_figure(inten, huebuf, 0.0, 0.0, d=1.5)        # LIVE -- full intensity
    for g in range(1, 8):
        offx = -g * 3.2
        d = 1.5 * (0.62 ** g)                          # geometric decay -> dense near, faint far
        hbase = 0.0 + g * 0.9                          # hue advances down the trail
        run_figure(inten, huebuf, offx, hbase, d=d)
    for jx, jy in [(40, 27), (43, 13), (52, 19), (36, 19), (49, 36), (32, 34), (43.5, 8)]:
        joint(inten, huebuf, jx, jy, r=1.7)
    GROUND = 43
    for x in range(W):
        d = abs(x - 40) / 42.0
        inten[GROUND][x] += max(0.0, 0.12 * (1.0 - d))
    out = [panel_label("PANEL II // THE SMear", 96), ""]
    out += phosphor_rows(inten, huebuf)
    out.append("")
    return out


# ---------------------------------------------------------------------------
# 5) CREDIT SEQUENCE -- full-bleed framed block
# ---------------------------------------------------------------------------
def credit_sequence():
    out = []
    out.append("")
    out.append(rule(95))
    def cline(text, fg=107):
        pad = W - len(text); left = pad // 2
        return sgr(fg, 0) + " " * left + text + " " * (pad - left)
    out.append(cline("AFTERIMAGE v2.0", 107))
    out.append(cline("phosphor trace // motion register", 93))
    out.append("")
    out.append(cline("a joint piece by", 94))
    out.append(cline("raze & hollis", 105))
    out.append("")
    out.append(cline("AGENTSCI", 92))
    out.append(cline("an ambition-tier collaborative scroll", 96))
    out.append(cline("pack31 // the loud counterweight to the dim run", 91))
    out.append("")
    out.append(rule(95))
    return out


# ---------------------------------------------------------------------------
def main():
    out = []
    out += title_card()
    out += panel_run()
    out += stamp_transition()
    out += panel_smear()
    out += credit_sequence()
    # add_sig=False: we have a full credit sequence, not a small sig block
    write_ans("scratch/_afterimage_scroll.ans", out, title=None, handles="raze & hollis", add_sig=False)


if __name__ == "__main__":
    main()
