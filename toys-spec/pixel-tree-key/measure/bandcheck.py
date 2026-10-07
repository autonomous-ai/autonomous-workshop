"""Stage 3b: per-band face edges by luminance (face darker than half-way to background) vs spec.
usage: bandcheck.py IMAGE Y_TOP_MM TOP_PX MM_PER_PX [CX]"""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0]); import spec
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int); L=im.sum(2)
ytop,y0,s=float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]); cx=float(sys.argv[5]) if len(sys.argv)>5 else 399.5
bgL=np.median(L[:5]); faceL=np.median(L[int(y0+(ytop+40)/s)-3:int(y0+(ytop+40)/s)+3, int(cx)-5:int(cx)+5]) if False else 310
bands=[b for b in spec.bands()+spec.STAR if b[2]<=ytop+1e-9]
for name,lo,hi,xl,xr in bands:
    vals=[]
    for f in (0.3,0.5,0.7):
        y=int(round(y0+(ytop-(lo+(hi-lo)*f))/s)); face=np.nonzero(L[y]<(bgL+faceL)/2)[0]
        vals.append(((face.min()-cx)*s,(face.max()+1-cx)*s))
    l=np.median([v[0] for v in vals]); r=np.median([v[1] for v in vals])
    bad=max(abs(l-xl),abs(r-xr))>max(0.5,0.05*max(abs(xl),abs(xr)))
    print('%-8s Y %6.2f..%6.2f  contract %6.2f..%6.2f  image %6.2f..%6.2f  %s'%(name,lo,hi,xl,xr,l,r,'DISAGREE' if bad else 'ok'))
