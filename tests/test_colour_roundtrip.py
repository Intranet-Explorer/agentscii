"""Canvas -> .ans -> harness parser must give back exactly the canvas cells.

Guards the 2026-09-26 bug: bold was never reset, so dim colours written
after bright ones came back bright. Run: python3 tests/test_colour_roundtrip.py
"""
import sys, tempfile, random
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import canvas_tools as ct
import harness

def main():
    ws = tempfile.mkdtemp(prefix="rt_")
    (Path(ws) / "scratch").mkdir()
    rng = random.Random(7)
    ct.new_canvas(ws, "rt", 40, 16, bg=0)
    for _ in range(40):  # random bright/dim fills, including bright-then-dim sequences
        x, y = rng.randrange(40), rng.randrange(32)
        ct.fill_px(ws, "rt", x, y, rng.randint(1, 10), rng.randint(1, 6), rng.randrange(16))
    data = ct.load_canvas(ws, "rt")
    for i in range(60):  # glyph overrides with arbitrary fg/bg
        data["glyph_override"][f"{rng.randrange(16)},{rng.randrange(40)}"] = [
            rng.choice("░▒▓█▀▄▌▐"), rng.randrange(16), rng.randrange(8)]
    ct.save_canvas(ws, "rt", data)
    want = ct.render_canvas_cells(ct.load_canvas(ws, "rt"))
    path = ct.save_ans(ws, "rt", "scratch/rt.ans", title=None, add_sig=False)
    grid = harness._parse_ans_grid(str(path))
    grid = grid[0] if isinstance(grid, tuple) else grid
    bad = 0
    for r, row in enumerate(want):
        for c, cell in enumerate(row):
            g = tuple(grid.get((r, c), (" ", 7, 0)))[:3]
            if cell[0] == " ":  # a space's fg is invisible; compare bg only
                ok = g[2] == cell[2]
            else:
                ok = tuple(g) == tuple(cell)
            bad += not ok
            if not ok and bad <= 5:
                print(f"  mismatch r{r} c{c}: canvas {cell} file {g}")
    print("colour round-trip:", "PASS" if bad == 0 else f"FAIL ({bad} cells)")
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
