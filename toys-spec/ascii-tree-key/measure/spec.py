"""Contract geometry in plan (assembly XY, mm) for the Stage 3c checks. Computes; draws nothing."""
import math
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union
from shapely import affinity
def rrect(x0,y0,x1,y1,r): return box(x0+r,y0+r,x1-r,y1-r).buffer(r, quad_segs=16)
BOW = rrect(-21.0,0.0,21.0,38.8,4.0)
WINDOW = rrect(-18.3,4.0,18.3,33.0,1.5)
DOTS = [(-15.5,35.7),(-11.9,35.7),(-8.3,35.7)]; DOT_D=2.0
ROWS = [28.1,21.7,15.3,8.9]; PX=6.8
GLYPHS = [(PX*(i-(k)/2), ROWS[k]) for k in range(4) for i in range(k+1)]
POCKET = rrect(-11.15,12.55,11.15,24.45,0.5)
def asterisk(cx,cy,L=2.5,w=1.0,fillet=0.5):
    arms=[LineString([(0,0),(L*math.cos(math.radians(a)),L*math.sin(math.radians(a)))]).buffer(w/2,cap_style=2) for a in (90,30,-30,-90,-150,150)]
    g=unary_union(arms)
    if fillet: g=g.buffer(fillet,join_style=2).buffer(-fillet,quad_segs=16,join_style=1)
    return affinity.translate(g,cx,cy)
G = [asterisk(x,y) for x,y in GLYPHS]
if __name__=="__main__":
    print("glyph centres", [(round(x,2),y) for x,y in GLYPHS])
    g=G[0]; print("glyph bounds", [round(v,3) for v in g.bounds], "area", round(g.area,2))
    md=min(G[i].distance(G[j]) for i in range(10) for j in range(i+1,10)); print("min glyph-glyph web", round(md,3))
    print("min glyph to window edge", round(min(WINDOW.exterior.distance(g) for g in G),3))
    tree=unary_union(G); b=tree.bounds; print("tree bounds",[round(v,2) for v in b], "centre", round((b[0]+b[2])/2,2), round((b[1]+b[3])/2,2), "window centre", 0, (4.0+33.0)/2)
    D=[Point(x,y).buffer(DOT_D/2) for x,y in DOTS]
    print("dot-dot web", round(min(D[i].distance(D[j]) for i in range(3) for j in range(i+1,3)),3))
    print("dot to window", round(min(WINDOW.distance(d) for d in D),3), "dot to bow edge", round(min(BOW.exterior.distance(d) for d in D),3))
    print("pocket to bow edge", round(BOW.exterior.distance(POCKET),3), "pocket+2 inside window?", POCKET.buffer(2).within(WINDOW))
    for f in (0.0, 0.3, 0.5):
        gs=[asterisk(x,y,fillet=f) for x,y in GLYPHS]; scr=WINDOW.difference(unary_union(gs))
        thin=scr.difference(scr.buffer(-0.4).buffer(0.4))
        print(f"inner fillet R{f}: screen area under 0.8 across {thin.area:.2f} mm2 (side-wall band x1.0 high); glyph area {gs[0].area:.2f}; glyph bounds {[round(v,2) for v in gs[0].bounds]}")
    print("frame side", -18.3+21.0, "bottom", 4.0, "title", 38.8-33.0)
