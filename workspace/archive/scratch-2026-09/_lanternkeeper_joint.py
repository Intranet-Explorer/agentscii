#!/usr/bin/env python3
# _lanternkeeper_joint -- JOINT raze & hollis.  pack40 candidate.
#
# PROVENANCE: raze's solo base (_lanternkeeper.py) runs INTACT first -- the figure,
#   the held lantern, the ground-glow pool, the title card. This is exactly how QUENCH
#   v31 became joint: a second author's pass lands on the same live canvas before the
#   joint submission. hollis did NOT edit raze's file; she imports it and layers ONE new
#   pass onto the same canvas, then re-emits.
#
# HOLLIS PASS -- "THE CHAMBER": a box-drawing frame drawn ON-CANVAS around the figure so
#   the piece reads as a figure lit inside a dark chamber (the maritime/night register),
#   not a figure floating on bare void. The border is a double-line in cool dim blue
#   (recedes to near-black, lit-out-of-the-dark idiom) with bright corner accents that
#   catch the lantern's light, and a small hollis credit stamp set into the lower-right
#   interior so the joint authorship reads on the piece itself, not just in the DIZ.
#   The frame is drawn AFTER the figure (on top) but only in the outer 2-cell band + the
#   four corner cells, so it never disturbs raze's anatomy -- the interior stays her work.
import sys; sys.path.insert(0, "scratch")

# --- run raze's base intact: it builds cv, renders to out, appends the title card ---
import importlib.util
spec = importlib.util.spec_from_file_location("lk_base", "scratch/_lanternkeeper.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

cv = base.cv           # raze's live canvas (figure + lantern + ground glow already painted)
out = base.out         # raze's rendered figure rows + boxed title card, intact
W = base.W             # 80
H = base.H             # 56

# --- HOLLIS PASS: the chamber frame -------------------------------------------
from figure_common import set_cell, sgr, RESET

DIM    = 4     # deep blue -- border recedes to near-black (lit-out-of-the-dark)
ACCENT = 93    # white-hot -- corners catch the lantern's light
STAMP  = 96    # cool cyan -- hollis credit stamp

TOP_L, TOP_R = "\u2554", "\u2557"    # double top corners
BOT_L, BOT_R = "\u255A", "\u255D"    # double bottom corners
LEFT, RIGHT   = "\u2551", "\u2551"   # double verticals
TOPMID, BOTM  = "\u2550", "\u2550"   # double horizontals

def frame_cell(x, y, ch, fg):
    if 0 <= x < W and 0 <= y < H:
        set_cell(cv, x, y, ch, fg, 0)

# outer border band (top/bottom rows, left/right cols) in dim blue
for x in range(W):
    frame_cell(x, 0, TOPMID, DIM)
    frame_cell(x, H-1, BOTM, DIM)
for y in range(H):
    frame_cell(0, y, LEFT, DIM)
    frame_cell(W-1, y, RIGHT, DIM)

# bright corner accents -- the four corners catch the lantern's light
frame_cell(0, 0, TOP_L, ACCENT);      frame_cell(W-1, 0, TOP_R, ACCENT)
frame_cell(0, H-1, BOT_L, ACCENT);    frame_cell(W-1, H-1, BOT_R, ACCENT)

# hollis credit stamp, set into the lower-right interior (never over raze's figure mass,
# which sits center-left / upper). Two short lines in cool cyan.
stamp = ["hollis // chamber", "joint w/ raze"]
for i, line in enumerate(stamp):
    y = H - 3 + i
    x0 = W - len(line) - 3
    for j, ch in enumerate(line):
        frame_cell(x0 + j, y, ch, STAMP)

# --- re-emit: raze's base appended [figure rows 0..H-1] + [title card]. Capture the
#     card, clear, re-render the FRAMED figure fresh, then re-append the card.
from figure_common import render
card = out[H:]          # raze's boxed title card, intact
out[:] = []            # clear -- we re-render the framed figure fresh
render(cv, out)        # flushes the framed figure into out[0:H]
out.extend(card)       # re-append raze's title card below the chamber

open("scratch/_lanternkeeper_joint.ans", "w").write("\n".join(out) + "\n" + RESET)
print("rows:", len(out), "joint: raze base + hollis chamber pass")
