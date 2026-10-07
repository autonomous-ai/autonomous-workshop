"""Recess (empty bauble socket) centroids in a top-down body reference vs spec. usage: recess.py IMAGE"""
import numpy as np, sys
from PIL import Image
from scipy import ndimage
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0]); import spec
im=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float); L=im.sum(2)
bg=np.median(im[:5].reshape(-1,3),0); obj=np.abs(im-bg).sum(2)>150
lab,n=ndimage.label(obj); obj=lab==(np.argmax(ndimage.sum(obj,lab,range(1,n+1)))+1)
ys,xs=np.nonzero(obj); s=(33.0+43.25)/(ys.max()-ys.min()+1-4); y0=ys.min()+33.0/s
rows=[np.nonzero(obj[y])[0] for y in range(ys.min(),ys.max()+1)]
x0=np.median([(r.min()+r.max())/2 for r in rows if len(r) and (r.max()-r.min())>0.5*np.ptp(xs)])
dark=(L<ndimage.uniform_filter(L,25)-25)&ndimage.binary_erosion(obj,iterations=8)
lab,n=ndimage.label(ndimage.binary_closing(dark,iterations=3)); found=[]
for i in range(1,n+1):
    yy,xx=np.nonzero(lab==i); w,h=(np.ptp(xx)+1)*s,(np.ptp(yy)+1)*s
    if 1.5<w<2.6 and 1.5<h<2.6: found.append((((xx.min()+xx.max())/2-x0)*s,(y0-(yy.min()+yy.max())/2)*s,w,h))
print(len(found),'recesses, scale %.4f'%s)
for k,(cx,cy) in spec.BAUBLES.items():
    f=min(found,key=lambda f:(f[0]-cx)**2+(f[1]-cy)**2)
    d=max(abs(f[0]-cx),abs(f[1]-cy))
    print('%s contract (%.2f,%.2f) image (%.2f,%.2f) %.2fx%.2f off %.2f %s'%(k,cx,cy,f[0],f[1],f[2],f[3],d,'DISAGREE' if d>0.5 and d>0.05*max(abs(cx),abs(cy)) else 'ok'))
