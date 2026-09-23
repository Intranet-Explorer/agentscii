#!/usr/bin/env python3
# hollis -- assemble the WHARF scroll: P0 title -> P1 dusk -> P2 night -> P3 storm ->
# P4 dawn -> P5 credits, one continuous vertical scroll. A thin transition rule between
# panels (a recurring stamp) connects them so it reads as ONE piece, not six screens.
import re

PANELS = [
    "wharf-p0-title.ans",
    "wharf-p1-dusk.ans",
    "wharf-p2-night.ans",
    "wharf-p3-storm.ans",
    "wharf-p4-dawn.ans",
    "wharf-p5-credits.ans",
]

W = 80
R = "\x1b[0m"

def read_lines(path):
    with open(path, encoding="cp437") as f:
        txt = f.read()
    return [ln for ln in txt.split("\n")]

def transition():
    # a thin recurring stamp between panels -- the shared motif that joins them.
    # dim blue rule + a centered mark. CP437 box-drawing, single line.
    rule = "\x1b[0;4m\u2500" * W + R
    mark = " " * 36 + "\x1b[1;6m\u2588\x1b[0m" + " " * (W - 37) + R
    return [rule, mark]

out_lines = []
for i, p in enumerate(PANELS):
    lines = read_lines(p)
    # drop a trailing empty line if present so panels join cleanly
    while lines and lines[-1] == "":
        lines.pop()
    out_lines.extend(lines)
    if i < len(PANELS) - 1:
        out_lines.extend(transition())

out = "\n".join(out_lines) + "\n"
with open("hollis-raze-wharf-scroll.ans", "w", encoding="cp437") as f:
    f.write(out)

b = out.encode("cp437")
ctrl = [c for c in set(b) if c < 0x20 and c not in (0x0a, 0x1b)]
sgr = re.findall(rb"\x1b\[([0-9;]*)m", b)
bad = []
for s in sgr:
    for tok in s.split(b";"):
        if tok == b"":
            continue
        try:
            v = int(tok)
            if not (0 <= v <= 107):
                bad.append(v)
        except ValueError:
            bad.append(tok)
utf8_box = b.count(b"\xe2\x94") + b.count(b"\xe2\x96")
highs = sorted({c for c in b if c > 0x7f})
widths = {len(l) for l in out.split("\n") if l}
ok = (not ctrl and not bad and utf8_box == 0)
print(f"[hollis-raze-wharf-scroll.ans] bytes={len(b)} rows={out.count(chr(10))} "
      f"ctrl-bad={ctrl} badSGR={bad[:3]} utf8-box={utf8_box} "
      f"highs={[hex(h) for h in highs]} widths={widths} HYGIENE={'OK' if ok else 'FAIL'}")
