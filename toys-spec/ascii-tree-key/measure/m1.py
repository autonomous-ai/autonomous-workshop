import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
r,g,b = im[...,0],im[...,1],im[...,2]
lum = (r+g+b)/3
key = lum < 150
lab,n = nd.label(key); sizes = nd.sum(key,lab,range(1,n+1)); key = lab==(1+np.argmax(sizes))
key = nd.binary_fill_holes(key)
ys,xs = np.nonzero(key); print("key bbox x",xs.min(),xs.max(),"y",ys.min(),ys.max(), "W",xs.max()-xs.min()+1,"H",ys.max()-ys.min()+1)
# width profile
for y in range(ys.min(), ys.max()+1, 8):
    row = np.nonzero(key[y])[0]; print(f"  y{y}: {row.min()}..{row.max()} w{row.max()-row.min()+1}")
green = (g > r+25) & (g > b+15) & key
yel = (r > 180) & (g > 140) & (b < 120)
red = (r > 120) & (r > g+50) & key
for name,m in [("green",green),("yellow",yel),("red",red)]:
    lab,n = nd.label(nd.binary_closing(m,iterations=1))
    for i in range(1,n+1):
        yy,xx = np.nonzero(lab==i)
        if len(yy)<15: continue
        print(name, f"c=({xx.mean():.1f},{yy.mean():.1f}) bbox x{xx.min()}-{xx.max()} y{yy.min()}-{yy.max()} w{xx.max()-xx.min()+1} h{yy.max()-yy.min()+1} px{len(yy)}")
