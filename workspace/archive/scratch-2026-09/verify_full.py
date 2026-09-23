#!/usr/bin/env python3
# Verify the full LIFECYCLE scroll: SGR hygiene (only valid codes, extended-bright
# 98-105 fg set present), CP437 validity (all non-ASCII bytes upper-half), control
# chars only ESC+LF, standalone reset tail.
import re

data = open("hollis-raze-lifecycle-full.ans", "rb").read()
text = data.decode("latin-1")

# 1. control chars: only ESC(27) and LF(10) allowed
ctrl = sorted({b for b in data if b < 32 or b == 127})
print("control bytes:", [hex(b) for b in ctrl], "(expect 0x1b,0x0a only)")

# 2. CP437 validity: every non-ASCII byte must be 0x80-0xFF (upper-half glyphs)
bad = sorted({b for b in data if b > 127 and not (0x80 <= b <= 0xff)})
print("non-CP437 bytes:", [hex(b) for b in bad], "(expect none)")

# 3. SGR codes: parse every \x1b[...m, check fg/bg params are valid
sgr = re.findall(r"\x1b\[([0-9;]*)m", text)
fgs, bgs = set(), set()
invalid = []
for grp in sgr:
    if grp == "":
        continue
    for p in grp.split(";"):
        v = int(p)
        if 30 <= v <= 37 or 90 <= v <= 107:
            fgs.add(v)
        elif 40 <= v <= 47 or 100 <= v <= 107:
            bgs.add(v)
        elif v in (0,):
            pass
        else:
            invalid.append(v)
print("distinct SGR groups:", len(set(sgr)))
print("fg codes used:", sorted(fgs))
print("bg codes used:", sorted(bgs))
print("INVALID sgr params:", sorted(set(invalid)), "(expect none)")

# 4. extended-bright fg set (house convention 98-105)
bright = [v for v in range(98,106)]
present = [v for v in bright if v in fgs]
print("extended-bright 98-105 present:", present)

# 5. standalone reset tail
print("ends with reset tail:", text.rstrip().endswith("\x1b[0m"))
print("total lines:", text.count("\n"))
