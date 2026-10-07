"""Stage 3b: coloured bauble centroids in a top-down assembly reference vs spec. usage: IMAGE X0 Y0PX S"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0]); import spec
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
x0,y0,s=map(float,sys.argv[2:5])
r,g,b=im[...,0],im[...,1],im[...,2]
for c,m in (('R',(r>150)&(g<100)&(b<100)),('G',(r>200)&(g>140)&(b<120))):
    lab,n=ndimage.label(m); cents=[]
    for i in range(1,n+1):
        ys,xs=np.nonzero(lab==i)
        if 20<len(ys)<1500: cents.append(((xs.mean()-x0)*s,(y0-ys.mean())*s,(np.ptp(xs)+1)*s))
    ks=[k for k in spec.BAUBLES if k[0]==c]
    print(c,'count image',len(cents),'contract',len(ks))
    for k in ks:
        X,Y=spec.BAUBLES[k]; f=min(cents,key=lambda q:np.hypot(q[0]-X,q[1]-Y)); d=np.hypot(f[0]-X,f[1]-Y)
        print('  %s contract (%.2f,%.2f) image (%.2f,%.2f) off %.2f %s'%(k,X,Y,f[0],f[1],d,'DISAGREE' if d>max(0.5,0.05*np.hypot(X,Y)) else 'ok'))
