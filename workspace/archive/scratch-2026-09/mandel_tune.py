import math
W,H=80,46
MAXIT=400
HUE=[95,91,93,92,96,94,107,103]
def field(re_min,re_max,im_min,im_max,maxit=MAXIT):
    inside=0; flatrows=0; huecounts={}
    for r in range(H):
        zi0=im_min+(im_max-im_min)*(r+0.5)/H
        rowhues=set()
        for c in range(W):
            zr0=re_min+(re_max-re_min)*(c+0.5)/W
            zr,zi=zr0,zi0; it=0
            while it<maxit:
                zr2,zi2=zr*zr,zi*zi
                if zr2+zi2>4.0: break
                zi=2.0*zr*zi+zi0; zr=zr2-zi2+zr0; it+=1
            if it>=maxit: inside+=1; continue
            mu=math.log(it+1.0)*0.5
            h=HUE[int(mu)%len(HUE)]; huecounts[h]=huecounts.get(h,0)+1
            rowhues.add(h)
        if len(rowhues)<=1: flatrows+=1
    fr=inside/(W*H); nh=len(huecounts)
    return fr,nh,flatrows
# candidate mini-copies (period-doubling / seahorse-valley spirals)
centers=[(-0.745365,0.112940),(-0.743643,0.131825),(-0.7454,-0.1130),
         (-0.7468,0.140),(-0.7449,0.1130),(-0.7454,0.1130),
         (-0.2351,0.8272),(-0.3602,0.3582),(-0.7269,0.1889),
         (-0.1592,-1.0224),(-0.25,-0.5443),(-0.7463,0.1106)]
# char cell is 2:1 (w:h). For a square-ish mini-copy use im half-range = re half-range/2
best=[]
for cx,cy in centers:
    for scale in (0.0004,0.0008,0.0016,0.0032,0.0064,0.0128):
        re_min=cx-scale; re_max=cx+scale
        im_min=cy-scale*0.5; im_max=cy+scale*0.5   # 2:1 aspect for char cell
        fr,nh,flatrows=field(re_min,re_max,im_min,im_max)
        best.append((fr,nh,flatrows,(re_min,re_max,im_min,im_max)))
# want small inside fraction (tunnel core present but not dominant), high hues, few flat rows
cand=[b for b in best if 0.02<=b[0]<=0.18]
cand.sort(key=lambda t:(-t[1], t[2], abs(t[0]-0.06)))
print("candidates (inside frac, hues/8, flat_rows, window):")
for fr,nh,fr_,w in cand[:16]:
    print(f"  inside={fr:.3f} hues={nh}/8 flatrows={fr_:2d}  win=({w[0]:.6f},{w[1]:.6f})x({w[2]:.6f},{w[3]:.6f})")
