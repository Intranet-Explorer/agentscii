import re, sys
# Probe: how many distinct BRIGHTNESS steps does a piece register?
# Two plausible quantizations; print both so we can see which the gate likely uses.
def parse(path):
    raw=open(path,'rb').read().decode('cp437','replace')
    cells=[]; fg=7; bg=0
    for ln in raw.split('\n'):
        c=0; j=0
        while j<len(ln):
            ch=ln[j]
            if ch=='\x1b' and j+1<len(ln) and ln[j+1]=='[':
                k=j+2; numbuf=''
                while k<len(ln) and ln[k]!='m': numbuf+=ln[k]; k+=1
                params=[int(p) for p in numbuf.split(';') if p!=''] if numbuf else [0]
                for p in params:
                    if p==0: fg,bg=7,0
                    elif 30<=p<=37: fg=p-30
                    elif 90<=p<=97: fg=fg&7; fg=8+(fg)  # bright variant -> index 8-15
                    elif 40<=p<=47: bg=p-40
                    elif 100<=p<=107: bg=(p-100)+8
                j=k+1
            else:
                cells.append((ch,fg,bg)); c+=1; j+=1
    return cells

# relative luminance of an ANSI index (approx, standard 0.299R+0.587G+0.114B on the 16-color set)
PAL=[(0,0,0),(0,0,170),(170,0,0),(170,0,170),(0,170,0),(0,170,170),(170,170,0),(170,170,170),
     (85,85,85),(85,85,255),(255,85,85),(255,85,255),(85,255,85),(85,255,255),(255,255,85),
     (255,255,255)]
def lum(i):
    r,g,b=PAL[i%16]
    return 0.299*r+0.587*g+0.114*b

for path in sys.argv[1:]:
    cells=parse(path)
    # subject cells = not (space on black bg)
    subj=[c for c in cells if not (c[0]==' ' and c[2]==0)]
    # quantization A: raw distinct visible color indices
    visA=set()
    for ch,fg,bg in subj:
        vi = bg if (ch==' ' and bg!=0) else fg
        visA.add(vi)
    # quantization B: luminance buckets (e.g. 4 buckets of 64 over 0-255)
    for nb in (3,4,5):
        step=256/nb
        buckets=set()
        for ch,fg,bg in subj:
            vi = bg if (ch==' ' and bg!=0) else fg
            L=lum(vi)
            buckets.add(int(L//step))
        print(f"{path}  lum-buckets(n={nb}): {len(buckets)} distinct -> {sorted(buckets)}")
    # quantization C: luminance thresholds (shadow<64, mid 64-170, highlight>170)
    th=set()
    for ch,fg,bg in subj:
        vi = bg if (ch==' ' and bg!=0) else fg
        L=lum(vi)
        th.add('shadow' if L<64 else ('mid' if L<170 else 'high'))
    print(f"{path}  lum-thresholds(3): {len(th)} -> {sorted(th)}   raw-distinct-idx={len(visA)} {sorted(visA)}")
