import sys; sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from sil import main
import numpy as np
from scipy import ndimage as nd
ROWS=[21.5,16.7,11.9,7.1]; PX=5.8
want=sorted([(round(PX*(i-k/2),2),ROWS[k]) for k in range(4) for i in range(k+1)])
for p in sys.argv[1:]:
    f,m=main(p) if False else (None,None)
    import io,contextlib
    with contextlib.redirect_stdout(io.StringIO()): f,m=main(p)
    ys,xs=np.nonzero(f); W=xs.max()-xs.min()+1; H=ys.max()-ys.min()+1
    sx=34.0/W; sy=22.0/H; cx=(xs.min()+xs.max()+1)/2
    lab,n=nd.label(f&~m); got=[]
    for i in range(1,n+1):
        yy,xx=np.nonzero(lab==i)
        if len(yy)<20: continue
        got.append(((xx.mean()-cx)*sx, 3.3+(ys.max()+1-yy.mean())*sy, (xx.max()-xx.min()+1)*sx, (yy.max()-yy.min()+1)*sy))
    print(f"{p}: W/H {W/H:.3f} (1.545) holes {len(got)}")
    worst=0
    for wx,wy in want:
        g=min(got,key=lambda g:(g[0]-wx)**2+(g[1]-wy)**2); off=((g[0]-wx)**2+(g[1]-wy)**2)**.5; worst=max(worst,off)
        print(f"   ({wx:5.1f},{wy:4.1f}) image ({g[0]:5.2f},{g[1]:5.2f}) {g[2]:.2f}x{g[3]:.2f} off {off:.2f}")
    print("   worst",round(worst,2))
