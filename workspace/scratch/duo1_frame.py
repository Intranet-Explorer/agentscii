#!/usr/bin/env python3
"""duo1 pass 4 -- FRAME + TITLE CARD ONLY.  Nothing inside the art moves.

The art is 80x100 px and fills its field edge to edge, so the frame cannot
be drawn *on* it without eating the casement jambs.  Instead the 100 px
composition is re-seated, unchanged, into a taller canvas with 4 cells of
margin above and 2 below; the border lives entirely in that new margin.

The side rails are 5 px wide and grey 8 -- the same width and value as the
pane's own jambs -- so the rail is read as the jamb simply continuing past
the picture into the top and bottom rules.  The border closes as one
rectangle instead of appearing as a second frame stacked around the first.

Type: one letterspaced line in the top band, dim grey, inside the rails.
Credits are the house sig block (canvas_save, handles 'opus'), appended
below the canvas -- nothing lands on the hand or the pane.

Tool gap used here: region copy/paste (STYLE "Gaps" list, old
copy_region()/paste_block()).  Offsetting a finished canvas into a larger
one is 6 lines of dict work below; it wants to be canvas_reframe.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import canvas_tools as ct  # noqa: E402

W = str(Path(__file__).resolve().parents[1])
SRC, DST = "duo1", "duo1f"
GREY, DIM = 8, 7
TOP_ROWS, BOT_ROWS = 4, 1          # cells of margin above / below the art
# Only the top gets a mat, for the title.  The art bleeds straight into the
# rule on the other three sides, so the forearm still exits the frame
# instead of stopping short of it on a strip of black.
JAMB_W = 5                          # matches the casement jambs in the art

src = ct.load_canvas(W, SRC)
assert src["w"] == 80 and src["ph"] == 100, (src["w"], src["ph"])

H = src["h_cells"] + TOP_ROWS + BOT_ROWS
DY = TOP_ROWS * 2                   # pixel offset of the art
if ct.canvas_exists(W, DST):
    (Path(W) / ct.CANVAS_DIR_NAME / f"{DST}.json").unlink()
ct.new_canvas(W, DST, src["w"], H, bg=0)

# --- region paste: the art, verbatim, DY px down -----------------------
dst = ct.load_canvas(W, DST)
for y, row in enumerate(src["pixels"]):
    dst["pixels"][y + DY] = list(row)
for key, val in src["glyph_override"].items():
    r, c = key.split(",")
    dst["glyph_override"][f"{int(r) + TOP_ROWS},{c}"] = val
ct.save_canvas(W, DST, dst)

PH = H * 2
# --- border: flat bars only (fill_px), no volume, no light -------------
ct.fill_px(W, DST, 0, 0, 80, 2, GREY)              # top rule
ct.fill_px(W, DST, 0, PH - 2, 80, 2, GREY)         # bottom rule
for x in (0, 80 - JAMB_W):                          # rails = jambs continued
    ct.fill_px(W, DST, x, 0, JAMB_W, DY, GREY)
    ct.fill_px(W, DST, x, DY + src["ph"], JAMB_W, PH - DY - src["ph"], GREY)

# --- title card: one quiet line in the top band ------------------------
TITLE = "AGAINST THE PANE"
spaced = " ".join(TITLE)
ct.text(W, DST, (80 - len(spaced)) // 2, 2, spaced, DIM, 0)

out = ct.save_ans(W, DST, "scratch/duo1.ans", title=TITLE, handles="opus")
print(out)
print(ct.metrics(W, DST))
