"""Stage 3b: measure a top-down reference against spec.py bands.
usage: measure.py IMAGE Y_TOP_MM Y_BOT_MM [star]"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0]); import spec
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
ytop,ybot=float(sys.argv[2]),float(sys.argv[3])
bands = spec.STAR if len(sys.argv)>4 else [b for b in spec.bands() if ytop>=b[2]-1e-9 and b[1]>=ybot-1e-9]
bg=np.median(np.r_[im[:5].reshape(-1,3),im[-5:].reshape(-1,3)],0)
obj=np.abs(im-bg).sum(2)>float(__import__("os").environ.get("THR","150"))
lab,n=ndimage.label(obj); sizes=ndimage.sum(obj,lab,range(1,n+1)); obj=lab==(np.argmax(sizes)+1)
obj=ndimage.binary_fill_holes(obj)
face=obj & (im.sum(2)>200) | (obj & ~ndimage.binary_erosion(obj,iterations=1))
face=ndimage.binary_opening(obj & (im.sum(2)>200), iterations=1) if False else obj
ys,xs=np.nonzero(obj)
# side bands at lower edges: estimate from dark bottom rows: use top edge and bottom edge minus band
s=(ytop-ybot)/(ys.max()-ys.min()+1-4)   # mm/px, 4 px side band at the bottom
y0=ys.min()
def py(Y): return int(round(y0+(ytop-Y)/s))
# X centre: middle of the widest row in the upper half
rows=[(np.nonzero(obj[y])[0]) for y in range(ys.min(),ys.max()+1)]
cx=np.median([ (r.min()+r.max())/2 for r in rows if len(r) and (r.max()-r.min())>0.5*np.ptp(xs)]) if len(sys.argv)<=4 else (xs.min()+xs.max())/2
print('scale %.4f mm/px  centre px %.1f' % (s,cx))
worst=0
print('%-8s %-14s %-14s %s'%('band','contract xl..xr','image xl..xr','verdict'))
for name,lo,hi,xl,xr in bands:
    yy=[py(lo+(hi-lo)*f) for f in (0.35,0.5,0.65)]
    ext=[]
    for y in yy:
        r=np.nonzero(obj[y])[0]
        if len(r): ext.append(((r.min()-cx)*s,(r.max()+1-cx)*s))
    il=np.median([e[0] for e in ext]); ir=np.median([e[1] for e in ext])
    dl,dr=il-xl,ir-xr
    bad=[d for d,v in ((dl,xl),(dr,xr)) if abs(d)>0.5 and abs(d)>0.05*max(abs(v),1e-9)]
    print('%-8s %6.2f..%6.2f  %6.2f..%6.2f  %s'%(name,xl,xr,il,ir,'DISAGREE' if bad else 'ok'))
