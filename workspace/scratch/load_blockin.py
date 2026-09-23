import sys, re; from pathlib import Path
sys.path.insert(0,str(Path.home()/"agentscii"))
import canvas_tools as ct
W=str(Path.home()/"agentscii"/"workspace")
raw=(Path(W)/"references/blockins/pipe1.blockin.ans").read_bytes().decode('cp437','replace')
lines=[l for l in raw.split('\n') if l!='']
fg=7; bg=0; content=[]
for l in lines:
    cells=[]
    for tok in re.finditer(r'(\x1b\[[0-9;]*m|.)', l):
        m=tok.group(1)
        if m.startswith('\x1b['):
            for c in m[2:-1].split(';'):
                c=int(c) if c else 0
                if c==0: fg=7; bg=0
                elif 30<=c<=37: fg=c-30
                elif 40<=c<=47: bg=c-40
                elif 90<=c<=97: fg=c-90+8
                elif 100<=c<=107: bg=c-100+8
        else: cells.append((m,fg,bg))
    content.append(cells)
PH=100; Wd=80
def pix(ch,cf,cg):
    if ch=="\u2588": return (cf,cf)
    if ch=="\u2593": return (cf,cg)
    if ch=="\u2591": return (cg,cf)
    if ch in "\u2584\u2592": return (cg,cf)
    if ch==" ": return (cg,cg)
    return (cf,cg)
pixels=[[0]*Wd for _ in range(PH)]
for cr,row in enumerate(content[:50]):
    pyt=cr*2; pyb=pyt+1
    for col,(ch,cf,cg) in enumerate(row):
        t,b=pix(ch,cf,cg); pixels[pyt][col]=t; pixels[pyb][col]=b
ct.save_canvas(W,"pipe1",{"w":Wd,"h_cells":50,"ph":PH,"bg":0,"pixels":pixels,"glyph_override":{}})
print("loaded pristine block-in into pipe1 canvas")
