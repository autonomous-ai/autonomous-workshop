import sys; sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from sil import load
import numpy as np
from scipy import ndimage as nd
BIT=[(-17.5,-23.2,9.7),(-23.2,-24.4,6.0),(-24.4,-29.6,12.6),(-29.6,-31.6,8.0),(-31.6,-37.2,11.5)]
for p in sys.argv[1:]:
    a,d,t=load(p); f=nd.binary_fill_holes(d>t); f=nd.binary_opening(f,iterations=1)
    lab,n=nd.label(f); f=lab==(1+np.argmax(nd.sum(f,lab,range(1,n+1))))
    ys,xs=np.nonzero(f); W=xs.max()-xs.min()+1
    rows={y:np.nonzero(f[y])[0][[0,-1]] for y in range(ys.min(),ys.max()+1)}
    bowb=max(y for y,(l,r) in rows.items() if r-l+1>0.6*W)+1
    s=42.0/W; cx=(xs.min()+xs.max()+1)/2
    Y=lambda y:(bowb-y)*s
    print(p, f"bow H {Y(ys.min()):.2f} (38.8) key end Y {Y(ys.max()+1):.2f} (-41.1) aspect bow+key {W/(ys.max()-ys.min()+1):.3f} ({42/79.9:.3f})")
    sh=[(rows[y][0]+0.0, rows[y][1]+1.0) for y in range(int(bowb+3/s), int(bowb+15/s))]
    print(f"  shaft X {(np.median([l for l,r in sh])-cx)*s:.2f}..{(np.median([r for l,r in sh])-cx)*s:.2f} (-3.1..3.1)")
    for y0,y1,xr in BIT:
        ym=bowb-((y0+y1)/2)/s; print(f"  bit Y {y0}..{y1}: right X {(rows[int(ym)][1]+1-cx)*s:.2f} ({xr})")
    lum=a.mean(axis=2); bow=f.copy(); bow[bowb-3:]=False
    inner=nd.binary_erosion(bow,iterations=10); med=np.median(lum[inner])
    pk=inner&(np.abs(lum-med)>5); pk=nd.binary_opening(pk,iterations=2); pk=nd.binary_fill_holes(nd.binary_closing(pk,iterations=3))
    lab,n=nd.label(pk)
    if n:
        k=1+np.argmax(nd.sum(pk,lab,range(1,n+1))); yy,xx=np.nonzero(lab==k)
        print(f"  pocket X {(xx.min()-cx)*s:.2f}..{(xx.max()+1-cx)*s:.2f} (-11.15..11.15) Y {Y(yy.max()+1):.2f}..{Y(yy.min()):.2f} (12.55..24.45)")
