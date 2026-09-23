import math
W,H=80,46
MAXIT=300
def field(re_min,re_max,im_min,im_max):
    inside=0; hues=set(); its=[]
    for r in range(H):
        zi0=im_min+(im_max-im_min)*(r+0.5)/H
        for c in range(W):
            zr0=re_min+(re_max-re_min)*(c+0.5)/W
            zr,zi=zr0,zi0; it=0
            while it<MAXIT:
                zr2,zi2=zr*zr,zi*zi
                if zr2+zi2>4.0: break
                zi=2*zr*zi+zi0; zr=zr2-zi2+zr0; it+=1
            if it>=MAXIT: inside+=1; continue
            # span full wheel across iteration range, multiple loops for rich banding
            hue=int(it*8/MAXIT)%8
            hues.add(hue); its.append(it)
    return inside/(W*H), len(hues), (max(its) if its else 0)
centers=[(-0.745365,0.112940),(-0.743,0.145),(-0.7468,0.140),(-0.2351,0.8272),
          (-0.3602,0.3582),(-0.7269,0.1889),(-0.1592,-1.0224),(-0.25,-0.5443),
          (-0.7449,0.1130),(-0.7454,0.1130)]
best=[]
for cx,cy in centers:
    for scale in (0.0008,0.0016,0.0032,0.0064,0.0128,0.0256):
        re_min=cx-scale; re_max=cx+scale*1.6
        im_min=cy-scale*0.575; im_max=cy+scale*0.575
        fr,nh,mx=field(re_min,re_max,im_min,im_max)
        best.append((fr,nh,(re_min,re_max,im_min,im_max),mx))
# want: inside small-ish (<=0.12) but >0 so there's a core; hues high; maxit reached
cand=[b for b in best if b[0]<=0.15]
cand.sort(key=lambda t:(-t[1], abs(t[0]-0.06)))
for fr,nh,w,mx in cand[:14]:
    print(f"inside={fr:.3f} hues={nh}/8 maxit={mx:3d}  win=({w[0]:.6f},{w[1]:.6f})x({w[2]:.6f},{w[3]:.6f})")
