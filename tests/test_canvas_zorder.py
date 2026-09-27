"""A later pixel fill must show over earlier shading (z-order).
Run: python3 tests/test_canvas_zorder.py"""
import sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import canvas_tools as ct

def main():
    ws = tempfile.mkdtemp(prefix="zo_")
    ct.new_canvas(ws, "z", 30, 12, bg=0)
    ct.fill_px(ws, "z", 0, 0, 20, 20, 4)
    ct.shade(ws, "z", 12, 4, "top-left")               # writes glyph overrides
    shaded = len(ct.load_canvas(ws, "z")["glyph_override"])
    ct.fill_px(ws, "z", 0, 0, 20, 20, 14)              # later paint over all of it
    cells = ct.render_canvas_cells(ct.load_canvas(ws, "z"))
    region = [cells[r][c] for r in range(10) for c in range(20)]
    stale = sum(1 for ch, fg, bg in region if not (ch == " " and bg == 14))
    ct.sphere_px(ws, "z", 10, 10, 6, 12, light_x=4, light_y=4)   # shading tools still shade
    after = len(ct.load_canvas(ws, "z")["glyph_override"])
    ok = shaded > 0 and stale == 0 and after > 0
    print(f"z-order: shaded {shaded} cells, stale after refill {stale}, sphere overrides {after}:",
          "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
