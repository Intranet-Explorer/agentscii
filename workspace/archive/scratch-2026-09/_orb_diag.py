import re
# decode _orb.v9.ans into a grid of (char, fg, bg) and print the color map for rows 14-38
data=open("rejected/_orb.v9.ans","rb").read().decode("utf-8",errors="replace")
lines=data.split("\n")
# parse SGR per cell
import re
def parse_line(line):
    cells=[]
    fg=0;bg=0
    i=0
    # strip leading ESC[...m and track
    tokens=re.findall(r'\x1b\[(\d+);(\d+)m|(.?)', line)
    for t in tokens:
        if t[0]=='' and t[2] is not None:
            ch=t[2]
            cells.append((ch,fg,bg))
        else:
            fg=int(t[0]); bg=int(t[1])
            # map 30/90 etc back to index
    return cells
# simpler: just print raw with color codes stripped but mark non-space
for r in range(14,40):
    if r>=len(lines): break
    line=lines[r]
    # strip escape sequences for display
    disp=re.sub(r'\x1b\[[0-9;]*m','',line)
    print(f"{r:2d} |{disp}|")
