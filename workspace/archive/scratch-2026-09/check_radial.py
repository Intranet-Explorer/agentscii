import re, collections, sys
d = open("hollis-raze-radial.ans", "rb").read().decode("utf-8")
rows = d.split("\n")
print("total split lines:", len(rows), "(last empty from trailing newline)")
bad = 0
for i, l in enumerate(rows):
    if l == "" and i == len(rows) - 1:
        continue
    w = len(re.sub(r'\x1b\[[0-9;]*m', '', l))
    if w != 80:
        print("  row %d: width %d" % (i, w))
        bad += 1
print("width errors:", bad)
nonempty = [r for r in rows if r]
print("last non-empty line is standalone reset:", nonempty[-1] == "\x1b[0m]")
plain = re.sub(r'\x1b\[[0-9;]*m', '', d)
c = collections.Counter(ch for ch in plain if ch not in ' \n')
print("non-space chars:", dict(c.most_common()))
