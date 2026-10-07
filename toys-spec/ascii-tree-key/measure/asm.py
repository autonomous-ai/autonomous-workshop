"""Measure an assembly image against the contract (top view). Scale: shaft width = 6.2 mm cross-checked with bow width."""
import sys; sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from sil import load
import numpy as np
from scipy import ndimage as nd
C=dict(bowW=38.0,bowH=28.6,end=-41.1,win=(-17.0,17.0,2.2,24.0),rows=[20.3,15.5,10.7,5.9],px=5.8,dotsX=[-14.0,-10.4,-6.8],dotY=26.6)
for p in sys.argv[1:]:
    a,d,t=load(p); f=nd.binary_fill_holes(d>t); lab,n=nd.label(f); f=lab==(1+np.argmax(nd.sum(f,lab,range(1,n+1))))
    ys,xs=np.nonzero(f); W=xs.max()-xs.min()+1
    rows={y:np.nonzero(f[y])[0] for y in range(ys.min(),ys.max()+1)}
    bowb=max(y for y,r in rows.items() if r[-1]-r[0]+1>0.6*W)+1
    s=C['bowW']/W; cx=(xs.min()+xs.max()+1)/2
    Y=lambda y:(bowb-y)*s; X=lambda x:(x-cx)*s
    sh=np.median([rows[y][-1]-rows[y][0]+1 for y in range(bowb+int(3/s),bowb+int(12/s))])*s
    print(f"{p}: bow {C['bowW']} x {Y(ys.min()):.2f} (28.6)  aspect {W/(bowb-ys.min()):.3f} (1.329)  end {Y(ys.max()+1):.2f} (-41.1)  shaft {sh:.2f} (6.2)  key L/W {(ys.max()-ys.min()+1)/W:.3f} ({69.7/38:.3f})")
    lum=a.mean(axis=2).astype(float); r,g,b=a[...,0],a[...,1],a[...,2]
    scr=nd.binary_opening((lum<58)&f,iterations=1); lab,n=nd.label(scr); scr=nd.binary_fill_holes(lab==(1+np.argmax(nd.sum(scr,lab,range(1,n+1)))))
    yy,xx=np.nonzero(scr); print(f"   window X {X(xx.min()):.2f}..{X(xx.max()+1):.2f} Y {Y(yy.max()+1):.2f}..{Y(yy.min()):.2f}  (-17..17, 2.2..24.0)")
    green=(g>r+25)&(g>b+15)&f; yel=(r>170)&(g>130)&(b<120)&f; red=(r>110)&(r>g+50)&f
    out=[]
    for name,m in [("G",green),("Y",yel),("R",red)]:
        lab,n=nd.label(nd.binary_closing(m))
        for i in range(1,n+1):
            y2,x2=np.nonzero(lab==i)
            if len(y2)<6: continue
            out.append((name,round(X(x2.mean()),2),round(Y(y2.mean()),2),round((x2.max()-x2.min()+1)*s,2),round((y2.max()-y2.min()+1)*s,2)))
    for o in sorted(out,key=lambda o:(-o[2],o[1])): print("   ",o)
