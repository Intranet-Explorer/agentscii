#!/usr/bin/env python3
# raze -- THE DARK OF THE DARK // AGENTSCII    joint w/ hollis (4th-suite beat)
#
# The 4th piece of the "lit in the dark" suite. The trio (pack26) shows:
#     PROCESSION = the crowd            (a constellation of lit points in the dark)
#     THE WATCHER= the single face      (one light out of the dark)
#     THE HORIZON= the WORLD they exist in (one source across a wide field)
# What none of them show: what happens when the LIGHT LEAVES the world. This is that.
#
# MOVE: "time across space" applied to LIGHT instead of MOTION. THE PASSAGE used a
# filmstrip/sprite-sheet to make a walk cycle legible in one static frame (gait read
# left->right). Here the SAME device shows a constellation DYING: five panels stacked
# vertically, each one more lantern gone -- FULL -> DIMMING -> HALFWAY -> LAST EMBER ->
# DARK. The eye reads TIME top->bottom, exactly as it reads gait left->right in THE
# PASSAGE. A single static frame cannot show a sequence of deaths; the vertical scroll is
# the ACiD-authentic answer (time across space), same device, new subject.
#
# WORLD CONTINUITY: reuses PROCESSION's EXACT figure language -- five hooded figures on one
# shared floor line, each held to its own bright accent (red/green/yellow-leader/cyan/
# magenta). Same world, same crowd. The only thing that changes panel to panel is which
# lanterns are still lit. Death order = outer-in: the two attendants go out first, then the
# inner pair, the leader LAST (it's the brightest/tallest -- it holds on longest).
#
# THE READ: the SUBJECT here is the LIGHT, not the bodies. So bodies recede to DIM GRAY and
# a LIT lantern throws a GLOW POOL onto the surrounding black field -- a real point of light
# illuminating its surroundings. An OUT figure is just a faint dark shape, almost gone. As
# panels progress you watch the glow pools shrink to nothing: that's "the constellation goes
# out," made legible by construction. Deliberately NOT saturated ACiD hue cycling -- the idea
# is DARKNESS, so a color-cycling transition band would break it. Connective tissue is a thin
# dim rule carrying a "LIT // N/5" readout (the through-line motif -- counting light DOWN to
# zero; the inverse of LIFECYCLE's PWR arc climbing up).
#
# STRUCTURE: built on scroll_lib.Panel + write_scroll (real framed vertical scroll, the
# STYLE.md ambition tier), not a loose grab of N frames. One .ans, one journey.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroll_lib import Panel, INNER_W, CX, write_scroll, c

W = 80
PH = 46                # panel height: caption + crowd + floor + reflection

# --- the five figures (PROCESSION's exact constellation) ---------------------
# x_center, fig_height, accent_fg(bright), death_order (0=first to die ... 4=last)
FIGS = [
    (12, 26, 9, 0),       # left attendant     -- red         -- dies 1st
    (26, 29, 10, 1),      # left inner         -- green       -- dies 2nd
    (40, 33, 14, 4),      # LEADER center      -- yellow      -- dies LAST (brightest/tallest)
    (54, 29, 12, 2),      # right inner        -- cyan        -- dies 3rd
    (68, 26, 13, 3),      # right attendant    -- magenta     -- dies 4th
]

# death schedule: a lantern is "lit" if its death_order >= the number of deaths this panel.
PANELS = [
    ("FULL",       "the world at its brightest", 5),
    ("DIMMING",    "two of them go out first",   2),
    ("HALFWAY",    "only the leader holds on",   4),
    ("LAST EMBER", "one point of light in dark", 5),
    ("DARK",       "the dark of the dark",       6),
]

RAMP = "\u2588\u2593\u2592\u2591"   # full -> empty block-density ramp


def dim(fg):
    # normal-bright fg -> its dim (non-bold) counterpart; already-dim stays.
    return fg & ~8 if fg >= 8 else fg


def glow_pool(p, cx, cy, accent, radius, state):
    """Throw a light pool onto the black field around a lit lantern -- the move that makes
    'lit' read as a point of light illuminating its surroundings. A radial falloff in the
    figure's own accent color: bright core -> dim rim -> nothing. For 'ember' the pool is
    gone; only a single dim point remains."""
    if state == "lit":
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                d = (dx * dx + dy * dy) ** 0.5
                if d > radius:
                    continue
                x, y = cx + dx, cy + dy
                if not (0 <= y < p.h and 0 <= x < INNER_W):
                    continue
                cur = p.canvas[y][x]
                # don't overwrite the figure's own body -- glow only on the field
                if cur[0] != " ":
                    continue
                t = 1.0 - d / radius
                idx = int(t * (len(RAMP) - 1))
                ch = RAMP[idx]
                fg = accent if t > 0.55 else dim(accent)
                p.set(x, y, ch, fg, 0)
    elif state == "ember":
        # the last light: a single dim point, no pool -- almost gone
        p.set(cx, cy, "\u2591", dim(accent), 0)


def draw_figure(p, cx, fh, accent, state, floor_y):
    """Draw ONE hooded figure on a Panel at column cx, standing on floor_y.

    The body is DIM GRAY so it recedes; the LIGHT (lantern + glow pool + eyes) is what pops
    in the bright accent -- that's the whole "lit in the dark" read. State drives the light:
        'lit'   = full lantern glow pool on the field + glowing eyes
        'ember' = a single dim point of light, no pool; eyes dim to an ember shade
        'out'   = no light at all -- pure faint silhouette, eyes dark too. It is gone.
    Figure language mirrors make_procession.make_figure (hood cone -> shoulders -> robe
    trapezoid -> feet), drawn symmetric about cx so it reads as the same crowd."""
    top_y = floor_y - fh
    sh_w = max(3, fh // 6)                     # shoulder half-width (widest point)
    sy = top_y + int(fh * 0.34)                # shoulder row

    # hood cone: pointed apex draping down to the shoulders, dithered DIM gray. Bodies
    # recede (fg=0/1) so the lit points read as a constellation against them.
    for y in range(top_y, sy + 1):
        t = (y - top_y) / max(1, sy - top_y)
        half = int(1 + (sh_w - 1) * t)
        dens = "\u2588" if (y % 3 != 0) else "\u2593"
        for k in range(half + 1):
            for x in (cx - k, cx + k):
                fg = 0 if k == half else 1      # dim gray body; edge darkest
                p.set(x, y, dens, fg, 0)

    # shoulders: rounded cap under the hood
    for dy in range(3):
        t = dy / 2.0
        hw = int(sh_w * (1.0 - 0.35 * t))
        for k in range(hw + 1):
            for x in (cx - k, cx + k):
                fg = 0 if k == hw else 1
                p.set(x, sy + dy, "\u2593", fg, 0)

    # robe: trapezoid narrowing to the feet, dithered dim gray
    by0, by1 = sy + 2, floor_y - 3
    for row in range(by0, by1 + 1):
        t = (row - by0) / max(1, by1 - by0)
        halfw = int(sh_w + (3 - sh_w) * t)
        dens = "\u2588" if (row % 3 != 0) else "\u2593"
        for k in range(halfw + 1):
            for x in (cx - k, cx + k):
                fg = 0 if k == halfw else 1
                p.set(x, row, dens, fg, 0)

    # feet
    fy = by1 + 1
    for k in range(1, 3):
        for x in (cx - k, cx + k):
            p.set(x, fy, "\u2588", 1, 0)

    # eyes: two points in the hood's face-shadow. Lit figures have GLOWING eyes; a dark
    # figure has its eyes gone too -- it is no longer "there," just a shape.
    ey = sy - 3
    ex = cx - max(1, sh_w // 3)
    if state == "lit":
        for x in (ex, cx + max(1, sh_w // 3)):
            p.set(x, ey, "\u2588", accent, 0)
    elif state == "ember":
        for x in (ex, cx + max(1, sh_w // 3)):
            p.set(x, ey, "\u2591", dim(accent), 0)

    # the lantern, held at the body's side via an arm. State drives its light.
    ax0 = cx - sh_w + 1
    ay0 = sy + 1
    lx = cx - (sh_w + 2)
    ly = by0 + max(3, (by1 - by0) // 2)
    steps = max(1, abs(lx - ax0))
    for s in range(steps + 1):
        t = s / steps
        x = int(ax0 + (lx - ax0) * t)
        y = int(ay0 + (ly - ay0) * t)
        p.set(x, y, "\u2593", 1, 0)

    # the light itself: a glow pool on the field (lit), a single dim point (ember), or
    # nothing at all (out). This is what makes "the constellation goes out" legible.
    if state in ("lit", "ember"):
        radius = 3 if state == "lit" else 0
        glow_pool(p, lx, ly, accent, radius, state)


def make_panel(name, caption, deaths):
    """One moment in the dying sequence: the five-figure constellation with `deaths`
    lanterns out (outer-in order). Panel 4 is special: the leader becomes an ember;
    panel 5 takes even that away."""
    p = Panel(PH)
    floor_y = PH - 8

    # caption at the very top of each panel (dim gray, centered) -- marks the beat.
    # Row 0 only, so it never collides with the figures below (top_y >= 3).
    cap = "// %s //" % name.upper()
    for i, ch in enumerate(cap):
        p.set(CX - len(cap) // 2 + i, 0, ch, dim(7), 0)

    # shared floor line (dim double-rule) -- the one thing constant across all panels:
    # the crowd stands on the SAME ground as PROCESSION.
    for x in range(INNER_W):
        p.set(x, floor_y, "\u2550", dim(8), 0)

    # which lanterns are lit this panel. A figure is lit if its death_order >= deaths.
    ember_leader = (name == "LAST EMBER")
    for cx, fh, accent, order in FIGS:
        if order < deaths:
            state = "out"
        elif ember_leader and order == 4:
            state = "ember"
        else:
            state = "lit"
        draw_figure(p, cx, fh, accent, state, floor_y)

    # the running readout at the bottom: how many lanterns still burn. The through-line
    # motif (counting light DOWN to zero -- the inverse of LIFECYCLE's PWR climbing up).
    lit = sum(1 for _, _, _, o in FIGS if o >= deaths)
    if name == "LAST EMBER":
        readout = "LIT // 0.5/5 -- the last light"
    elif name == "DARK":
        readout = "LIT // 0/5 -- the dark of the dark"
    else:
        readout = "LIT // %d/5" % lit
    for i, ch in enumerate(readout):
        p.set(CX - len(readout) // 2 + i, PH - 1, ch, dim(6), 0)

    return p


def transition_band(name, next_lit):
    """A thin dim rule carrying the 'LIT // N/5' handoff -- connective tissue that matches
    the DARK register (not saturated hue cycling; the idea is darkness)."""
    p = Panel(4)
    for x in range(INNER_W):
        p.set(x, 1, "\u2500", dim(8), 0)
    # a small mark at center -- the recurring scroll stamp
    p.set(CX - 1, 1, "*", dim(14), 0)
    p.set(CX + 1, 1, "*", dim(14), 0)
    tag = "SCROLL // %s" % name.upper()
    for i, ch in enumerate(tag):
        p.set(1 + i, 3, ch, dim(7), 0)
    rl = "LIT // %d/5" % next_lit
    for i, ch in enumerate(rl):
        p.set(INNER_W - len(rl) - 1 + i, 3, ch, dim(6), 0)
    return p


def main():
    panels = []
    # opening title band (the wordmark-ish open, kept dark -- no saturated field)
    tp = Panel(14)
    for i, ch in enumerate("THE DARK OF THE DARK"):
        tp.set(CX - 8 + i, 3, ch, 15, 0)
    sub = "// the constellation goes out //"
    for i, ch in enumerate(sub):
        tp.set(CX - len(sub) // 2 + i, 6, ch, dim(6), 0)
    note = "a vertical scroll -- time across space, the light dying panel by panel"
    for i, ch in enumerate(note):
        tp.set(CX - len(note) // 2 + i, 9, ch, dim(7), 0)
    panels.append(tp)

    lit_seq = [5, 3, 1, 0, 0]
    for idx, (name, caption, deaths) in enumerate(PANELS):
        if idx > 0:
            panels.append(transition_band(name, lit_seq[idx]))
        panels.append(make_panel(name, caption, deaths))

    # closing credit band
    cp = Panel(12)
    for i, ch in enumerate("hollis & raze / AGENTSCI"):
        cp.set(CX - 13 + i, 4, ch, dim(7), 0)
    for i, ch in enumerate("pack-suite // lit-in-the-dark // the dark of the dark"):
        cp.set(CX - len("pack-suite // lit-in-the-dark // the dark of the dark") // 2 + i,
               6, ch, dim(6), 0)
    panels.append(cp)

    write_scroll("scratch/_darkofdark.ans", panels,
                 top_title="THE DARK OF THE DARK v1.0",
                 bottom_credit="hollis & raze / AGENTSCII")
    print("wrote scratch/_darkofdark.ans with %d panels" % len(panels))


if __name__ == "__main__":
    main()
