import sys; sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from sil import load
import numpy as np
from scipy import ndimage as nd
from PIL import Image
for p in sys.argv[1:]:
    a,d,t=load(p); f=nd.binary_fill_holes(d>t); lab,n=nd.label(f); f=lab==(1+np.argmax(nd.sum(f,lab,range(1,n+1))))
    ys,xs=np.nonzero(f); W=xs.max()-xs.min()+1; H=ys.max()-ys.min()+1
    k=(W/H)/(42/79.9)   # vertical scale to fix aspect
    s=42/W; sy=s*k; cx=(xs.min()+xs.max()+1)/2
    rows={y:np.nonzero(f[y])[0] for y in range(ys.min(),ys.max()+1)}
    bowb=max(y for y,r in rows.items() if r[-1]-r[0]+1>0.6*W)+1
    lum=nd.gaussian_filter(a.mean(axis=2),1.0); col=lum[:,int(cx)-3:int(cx)+4].mean(axis=1)
    g=np.gradient(col); seg=range(ys.min()+15,bowb-15)
    top=min(seg,key=lambda y:g[y]); bot=max([y for y in seg if y>top+20],key=lambda y:g[y],default=None)
    row=lum[(top+bot)//2-3:(top+bot)//2+4].mean(axis=0); gr=np.gradient(row)
    mid=int(cx); L=range(xs.min()+15,mid-20); R=range(mid+20,xs.max()-15)
    left=max(L,key=lambda x:abs(gr[x])); right=max(R,key=lambda x:abs(gr[x]))
    print(f"{p}: aspect fix x{1/k:.3f}; bow H {(bowb-ys.min())*sy:.2f} end {(bowb-ys.max())*sy:.2f}; pocket Y {(bowb-bot)*sy:.2f}..{(bowb-top)*sy:.2f} X {(left-cx)*s:.2f}..{(right-cx)*s:.2f}")
