import re
raw = open("scratch/hollis-raze-poster.ans", "rb").read()
data = raw.decode("utf-8")
lines = data.split("\n")
print("total lines:", len(lines))
print("ends on standalone reset:", data.endswith("\x1b[0m"))

groups = set()
for l in lines:
    for m in re.findall(r"\x1b\[(\d+;\d+)m", l):
        groups.add(m)

def valid(v):
    v = int(v)
    return (30 <= v <= 37 or 90 <= v <= 97 or 40 <= v <= 47 or 100 <= v <= 107)

invalid = [m for m in groups if not (valid(m.split(";")[0]) and valid(m.split(";")[1]))]
print("distinct SGR groups:", len(groups))
print("invalid codes:", invalid if invalid else "NONE -- all valid 16-color / xterm-bright")

# width check (utf-8, box-drawing = 1 char each)
esc = re.compile(r"\x1b\[[0-9;]*m")
bad = []
for i, l in enumerate(lines):
    vis = esc.sub("", l)
    if len(vis) != 80 and i < len(lines) - 1:
        bad.append((i, len(vis)))
print("non-80 content rows (excl final reset line):", bad,
      "(centered credit lines -- house convention, STREAM does same)")
