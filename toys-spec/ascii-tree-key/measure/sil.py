"""Silhouette and holes of a top-down image: subject = pixels differing from the background."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
def load(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(int)
    bg = np.median(np.concatenate([a[:5].reshape(-1,3), a[-5:].reshape(-1,3), a[:,:5].reshape(-1,3), a[:,-5:].reshape(-1,3)]),axis=0)
    d = np.abs(a-bg).sum(axis=2)
    sub = d > 60
    thr = 0.5 * float(np.median(d[sub])) if sub.any() else 60
    return a, d, max(thr, 40)
def main(p, thr=60):
    a,d,t = load(p)
    m = d > t
    m = nd.binary_opening(m, iterations=1)
    lab,n = nd.label(m); m = lab==(1+np.argmax(nd.sum(m,lab,range(1,n+1))))
    filled = nd.binary_fill_holes(m)
    ys,xs = np.nonzero(filled)
    W,H = xs.max()-xs.min()+1, ys.max()-ys.min()+1
    print(f"{p}: bbox x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()} W{W} H{H} W/H {W/H:.3f}")
    holes = filled & ~m
    lab,n = nd.label(holes)
    for i in range(1,n+1):
        yy,xx = np.nonzero(lab==i)
        if len(yy) < 20: continue
        print(f"  hole c=({xx.mean():.1f},{yy.mean():.1f}) x{xx.min()}-{xx.max()} y{yy.min()}-{yy.max()} w{xx.max()-xx.min()+1} h{yy.max()-yy.min()+1} n{len(yy)}")
    return filled, m
if __name__ == "__main__":
    for p in sys.argv[1:]: main(p)
