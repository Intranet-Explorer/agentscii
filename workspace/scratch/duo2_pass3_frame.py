#!/usr/bin/env python3
"""duo2 pass 3 -- void rim, credit block, signature.

The spec's "do not change" #12 forbids a border inside the 80x100 px:
the casement IS the frame, and boxing it would turn a window into a
decorative panel. So the frame pass happens where the spec says it can,
outside the picture -- the canvas grows six rows and the credit block is
drawn there with the canvas tools, in the piece's own cool palette
rather than save_ans's default magenta rules (the spec allows no warm
index anywhere).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import duo2_common as D  # noqa: E402

TITLE = "CONTACT"
HANDLES = "opus"
DATE = "2026-09-24"

D.load_mask()   # passes 1-2 own the canvas; this one only appends

# --- the void -------------------------------------------------------
# Left true black, deliberately. The spec's light section says nothing
# inside the hole catches the source, and a first attempt at dim flecks
# along the rim came out as 25 cells of green that read as lichen on the
# broken edge, not as depth. The void is the darkest thing in the piece
# and that is the whole job it has.

# --- credit block, on rows the picture does not occupy ----------------
data = D.ct.load_canvas(D.W, D.SLUG)
EXTRA = 6
data["pixels"] += [[0] * D.CW for _ in range(EXTRA * 2)]
data["h_cells"] += EXTRA
data["ph"] += EXTRA * 2
D.ct.save_canvas(D.W, D.SLUG, data)

base = D.CH
D.ct.fill_px(D.W, D.SLUG, 0, base * 2 + 2, D.CW, 1, 8)      # thin rule
D.ct.fill_px(D.W, D.SLUG, 0, (base + 5) * 2, D.CW, 1, 8)    # and the closer


def centred(row, s, fg):
    D.ct.text(D.W, D.SLUG, (D.CW - len(s)) // 2, row, s, fg, 0)


centred(base + 2, HANDLES + " / AGENTSCII", 15)
centred(base + 3, TITLE, 14)
centred(base + 4, DATE, 7)

D.ct.save_ans(D.W, D.SLUG, "scratch/duo2.ans", title=None, add_sig=False)
print(D.ct.metrics(D.W, D.SLUG))
