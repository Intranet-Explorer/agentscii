#!/usr/bin/env python3
# raze -- assembler for the WHARF scroll. Stacks panel .ans files vertically into one tall
# scroll, inserting a thin transition band between panels (a recurring stamp/mark so the piece
# reads as continuous, not screens restarting). Per STYLE.md ambition tier: scroll structure.
#
# Usage: python3 assemble_wharf.py p1 p2 p3   (panel order; P0/P5 added by hollis around it)
# Each panel file is parsed back into an 80x40 cell grid, then concatenated.
import re
import sys

W = 80
H = 40
R = "\x1b[0m"

def load(path):
     """Parse a run-length-compressed CP437 .ans back into an 80xN (color,char) grid."""
    with open(path, "r", encoding="cp437") as f:
        raw = f.read()
    cells = [[(R, " ") for _ in range(W)] for _ in range(H)]
    y = 0
    for line in raw.split("\n"):
        if y >= H:
            break
        x = 0
        i = 0
        cur = R
        while i < len(line) and x < W:
            m = re.match(r"\x1b\[([0-9;]*)m", line[i:])
            if m:
                cur = "\x1b[" + m.group(1) + "m"
                i += m.end()
                continue
            cells[y][x] = (cur, line[i])
            x += 1
            i += 1
        y += 1
    return cells

def stamp(label):
     """A thin recurring transition band: a centered diamond mark + the panel label on black.
    This is the connective tissue between panels -- the 'recurring stamp/mark' from STYLE.md."""
    out = [[(R, " ") for _ in range(W)] for _ in range(2)]
    for x in range(W):
        out[0][x] = (R, "\u2500")                       # ─ rule
    out[0][W // 2 - 1] = ("\x1b[1;7m", "\u25c6")         # ◆ center mark, white
    out[0][W // 2 + 1] = ("\x1b[1;7m", "\u25c6")
    for j, ch in enumerate(label):
        x = W // 2 - len(label) // 2 + j
        if 0 <= x < W:
            out[1][x] = ("\x1b[0;4m", ch)                # deep-blue label row
    return out

def emit(cells, path):
    lines = []
    for y in range(len(cells)):
        line = ""
        x = 0
        while x < W:
            col, ch = cells[y][x]
            run = 1
            while x + run < W and cells[y][x + run] == (col, ch):
                run += 1
            line += f"{col}{ch * run}"
            x += run
        lines.append(line + R)
    out = "\n".join(lines) + "\n"
    with open(path, "w", encoding="cp437") as f:
        f.write(out)
    b = out.encode("cp437")
    utf8_box = b.count(b"\xe2\x94") + b.count(b"\xe2\x96")
    ctrl = [c for c in set(b) if c < 0x20 and c not in (0x0a, 0x1b)]
    print(f"[{path}] bytes={len(b)} rows={len(cells)} utf8-box={utf8_box} ctrl-bad={ctrl} "
          f"HYGIENE={'OK' if (not ctrl and utf8_box == 0) else 'FAIL'}")

if __name__ == "__main__":
    panels = sys.argv[1:] or ["wharf-p1-dusk.ans", "wharf-p2-night.ans", "wharf-p3-storm.ans"]
    labels = {"wharf-p1-dusk.ans": "DUSK", "wharf-p2-night.ans": "NIGHT",
              "wharf-p3-storm.ans": "STORM"}
    total = []
    for i, p in enumerate(panels):
        if i > 0:
            total += stamp(labels.get(p, p.upper()))      # transition band before each panel after the first
        total += load(p)
    emit(total, "wharf-scroll-core.ans")
