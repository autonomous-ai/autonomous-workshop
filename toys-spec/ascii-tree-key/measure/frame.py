import sys; sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from sil import main
import numpy as np
for p in sys.argv[1:]:
    f,m = main(p)
    ys,xs=np.nonzero(f); W=xs.max()-xs.min()+1; H=ys.max()-ys.min()+1
    sx=42.0/W; sy=38.8/H
    from scipy import ndimage as nd
    holes=f&~m; lab,n=nd.label(holes)
    big=1+np.argmax(nd.sum(holes,lab,range(1,n+1))); yy,xx=np.nonzero(lab==big)
    cx=(xs.min()+xs.max())/2
    print(f"  scale x {sx:.4f} y {sy:.4f} (aspect off {(W/H)/(42/38.8)-1:+.3f})")
    print(f"  window X {(xx.min()-cx)*sx:.2f}..{(xx.max()+1-cx)*sx:.2f} (contract -18.3..18.3)  Y {(ys.max()+1-yy.max()-1)*sy:.2f}..{(ys.max()+1-yy.min())*sy:.2f} (contract 4.0..33.0)")
    print(f"  borders: left {(xx.min()-xs.min())*sx:.2f} right {(xs.max()-xx.max())*sx:.2f} (2.7) bottom {(ys.max()-yy.max())*sy:.2f} (4.0) title {(yy.min()-ys.min())*sy:.2f} (5.8)")
    for i in range(1,n+1):
        if i==big: continue
        y2,x2=np.nonzero(lab==i)
        if len(y2)<20: continue
        print(f"  dot hole X {(x2.mean()-cx)*sx:.2f} Y {(ys.max()+1-y2.mean())*sy:.2f} d {(x2.max()-x2.min()+1)*sx:.2f}x{(y2.max()-y2.min()+1)*sy:.2f}")
