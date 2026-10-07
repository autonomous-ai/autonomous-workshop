"""Stage 3d sweep for Daybreak v2 (module 2): XZ sections per Y layer from contract numbers."""
import math, sys
from shapely.geometry import Polygon, box, Point
from shapely.affinity import rotate, translate, scale
AX, AZ, RISE, H = 18.0, 33.0, 22.0, 43.5
def sector(r, a0, a1, n=80):
    return Polygon([(0,0)]+[(r*math.cos(math.radians(a0+(a1-a0)*i/n)), r*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)])
hub = Point(0,0).buffer(5.5, 64)
arm = hub.union(box(10.5,11,13.5,11.5)).convex_hull
plate = box(10.5, 11, 17.5, 69.5)            # 16.5 landscape face + 1.0 relief
sect = sector(16, -90-32.1, 32.1)             # 6 teeth x 25.71 deg, tip circle
skirt = sector(16, -90-32.1, 32.1)            # widest section of the 45-degree skirt
PL=lambda g,p: translate(rotate(g,p,origin=(0,0)),-AX,AZ)
PR=lambda g,p: scale(PL(g,p),-1,1,origin=(0,0))
sun = Polygon([(18*math.cos(math.radians(a)), 24.5+18*math.sin(math.radians(a))) for a in range(0,181,3)])
srplate = box(-4,3,4,40); rack = box(-6,3,6,40)
side = box(-33,0,-30,H).union(box(30,0,33,H)); floor = box(-33,0,33,3)
hubbay = side.union(floor)
sunbay = hubbay.union(box(-30,H-3,-19,H)).union(box(19,H-3,30,H))
cheek = hubbay.union(box(-30,3,-5,H)).union(box(5,3,30,H)).difference(Point(-AX,AZ).buffer(1.95)).difference(Point(AX,AZ).buffer(1.95))
front = box(-33,0,33,H)
L = {"Y-25..-22 front":(front,["plate"],[]),"Y-22..-21":(sunbay,["plate"],["srplate"]),
 "Y-21..-17 sun":(sunbay,["plate"],["sun","srplate"]),"Y-17..-16":(sunbay,["plate"],["srplate"]),
 "Y-16..-13 cheek":(cheek,["plate"],["srplate"]),"Y-13..-12.5":(hubbay,["plate"],["srplate"]),
 "Y-12.5..-12":(hubbay,["plate","hub","arm"],["rack"]),"Y-12..-4.5 gear":(hubbay,["plate","hub","arm","sect"],["rack"]),
 "Y-4.5..-4":(hubbay,["plate","hub","arm","sect"],[]),"Y-4..6.5 skirt":(hubbay,["plate","hub","arm","skirt"],[]),
 "Y6.5..25":(hubbay,["plate","hub","arm"],[])}
P={"plate":plate,"hub":hub,"arm":arm,"sect":sect,"skirt":skirt}; SR={"sun":sun,"srplate":srplate,"rack":rack}
res={}
for name,(sp,lp,sr) in L.items():
  for i in range(0,181):
    phi=i*0.5
    Lg=[(n,PL(P[n],phi)) for n in lp]; Rg=[(n,PR(P[n],phi)) for n in lp]
    Sg=[(n,translate(SR[n],0,RISE*phi/90)) for n in sr]
    pairs=[(f"left {a} vs spine",g,sp) for a,g in Lg]
    pairs+=[(f"left {a} vs {b}",g,s) for a,g in Lg for b,s in Sg if not(a=="sect" and b=="rack")]
    pairs+=[(f"left {a} vs right {b}",g,h) for a,g in Lg for b,h in Rg]
    pairs+=[(f"{b} vs spine",s,sp) for b,s in Sg]
    for lab,a,b in pairs:
      d=a.distance(b); ov=a.intersection(b).area; k=(name,lab)
      cur=res.get(k)
      if cur is None or ov>cur[2] or (cur[2]==0 and ov==0 and d<cur[0]): res[k]=(d,phi,ov)
for (n,l),(d,phi,ov) in sorted(res.items()):
  f="OVERLAP" if ov>1e-6 else "TIGHT" if d<0.5 else "ok"
  if f!="ok" or "-v" in sys.argv: print(f"{f:7s} {n:16s} {l:28s} gap {d:6.2f} @ {phi:5.1f}  ov {ov:.2f}")
print("left leaf max X:", round(max(PL(g,i/2).bounds[2] for g in P.values() for i in range(181)),2))
print("plate bottom Z at 90:", round(PL(plate,90).bounds[1],2), "plate X at 90:", [round(v,2) for v in PL(plate,90).bounds[::2]])
print("closed plate:", [round(v,2) for v in PL(plate,0).bounds], "closed leaf bounds:", [round(v,2) for v in PL(hub.union(arm).union(plate).union(sect),0).bounds])
# teeth: rack h at mesh (Z=AZ) closed/open, sector spare
print("rack mesh h closed", AZ-3, "open", AZ-3-RISE, "rack h top", 37, "pitch", round(2*math.pi,2))
print("rise", round(14*math.pi/2,2))
