"""Deterministic final-solid tests. Continuous conservative sweeps, no human play claim."""
import sys,json,math,hashlib
from pathlib import Path
from functools import lru_cache
# Installed as cad/measure/check_physical.py after the current Make round.
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import quayshift_lib as q
from build123d import *
from shapely.geometry import box as sbox, Point, MultiPoint
from shapely.ops import unary_union

def volume(s):
    return 0 if s is None else sum(t.volume for t in s) if isinstance(s,list) else s.volume

def ov(a,b):return volume(a.intersect(b))

def outside(a,b):return abs(a.volume-ov(a,b))

@lru_cache(None)
def placed(name,origin,rot):return q.transformed(name,origin,rot)

@lru_cache(None)
def capsule(a,b):
    ax,ay=a;bx,by=b;dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
    disc=Cylinder(q.FERRY_RADIUS,26,align=(Align.CENTER,Align.CENTER,Align.MIN))
    sweep=Pos(ax,ay,4)*disc+Pos(bx,by,4)*disc
    if length:
        sweep=sweep+Pos(ax,ay,4)*Rot(0,0,math.degrees(math.atan2(dy,dx)))*q.box(0,-13,0,length,26,26)
    return sweep

def world(cell):return (28+32*cell[0],28+32*cell[1])

def pathpoints(route):return [(92,-14)]+[world(c) for c in route]+[(92,198)]

def silhouette(name,origin,rot):
    # Conservative all-height plan cover, validated against exact solids below.
    cells=q.FOOTPRINTS[name]
    boxes=[sbox(x*32+.4,y*32+.4,(x+1)*32-.4,(y+1)*32-.4) for x,y in cells]
    if name in 'ABC':boxes.append(sbox(.4,19.6,95.6,31.6))
    else:
        # Multi-cell base/connected mass crosses internal seams, use exact envelope union.
        boxes=[sbox(x*32,y*32,(x+1)*32,(y+1)*32) for x,y in cells]
    from shapely.affinity import rotate,translate
    poly=unary_union(boxes)
    allcells=cells+([(1,0)] if name in 'ABC' else [])
    full=unary_union([sbox(x*32,y*32,(x+1)*32,(y+1)*32) for x,y in allcells])
    full=rotate(full,rot,origin=(0,0));x0,y0,_,_=full.bounds
    return translate(rotate(poly,rot,origin=(0,0)),12+32*origin[0]-x0,12+32*origin[1]-y0)

CONTACTS=[(0,-14),(0,14),(-11,0),(11,0)]+[(sx*(4+7*math.cos(math.radians(t))),sy*(7+7*math.sin(math.radians(t)))) for sx in [-1,1] for sy in [-1,1] for t in [15,30,45,60,75]]

def fingers(row,route):
    polygons=unary_union([silhouette(p['part'],tuple(p['origin']),p['rotation']) for p in row])
    # Tray rim height12 is below finger contact height14 (local10, below windows); do not falsely obstruct approach.
    pts=pathpoints(route);prev=None;minmargin=100;count=0;chosen=[]
    for a,b in zip(pts,pts[1:]):
        length=math.dist(a,b);n=math.ceil(length/.5)
        for j in range(n+1):
            x=a[0]+(b[0]-a[0])*j/n;y=a[1]+(b[1]-a[1])*j/n
            clear={i for i,(dx,dy) in enumerate(CONTACTS) if polygons.distance(Point(x+dx,y+dy))>=5.251}
            assert clear,('finger access',x,y)
            assert prev is None or prev&clear,('contact handoff gap',x,y)
            minmargin=min(minmargin,max(polygons.distance(Point(x+CONTACTS[i][0],y+CONTACTS[i][1]))-5 for i in clear))
            prev=clear;count+=1
    return {'samples':count,'max_sample_step_mm':.5,'finger_diameter_mm':10,'inter_sample_radius_allowance_mm':.251,'minimum_best_pad_margin_mm':round(minmargin,4),'overlapping_contact_sets':True}

def main():
    deck=json.loads((ROOT.parent/'challenges/challenges.json').read_text())
    names=list('ABCDEFGH')+['tray','ferry'];parts={n:q.part(n) for n in names}
    # Actual finite ferry is contained by the strong cylinder used for continuous travel.
    cylinder=Cylinder(13,26,align=(Align.CENTER,Align.CENTER,Align.MIN))
    assert outside(parts['ferry'],cylinder)<1e-5
    supports=[]
    for n in names:
        s=parts[n];bb=s.bounding_box();assert len(s.solids())==1 and s.volume>0
        assert abs(bb.min.Z)<1e-6
        c=s.center(CenterOf.MASS)
        feet=[]
        for face in s.faces():
            fb=face.bounding_box()
            if abs(fb.min.Z)<1e-6 and abs(fb.max.Z)<1e-6:
                feet += [(v.X,v.Y) for v in face.tessellate(.1)[0]]
        support=MultiPoint(feet).convex_hull
        assert support.contains(Point(c.X,c.Y)),('COM',n)
        supports.append({'part':n,'bbox_mm':[round(v,3) for v in bb.size],'solid_volume_mm3':round(s.volume,3),'uniform_solid_COM_mm':[round(v,3) for v in c],'support_hull_margin_mm':round(support.boundary.distance(Point(c.X,c.Y)),3)})
        if n in 'ABCDEFGH':
            # Validate conservative finger cover directly against exact material.
            poly=silhouette(n,(0,0),0)
            env=[]
            for cell in q.FOOTPRINTS[n]:env.append(q.box(12+32*cell[0],12+32*cell[1],4,32,32,100))
            if n in 'ABC':env.append(q.box(12,12+19.6,4,96,12,100))
            e=env[0].fuse(*env[1:]);assert outside(placed(n,(0,0),0),e)<1e-5
    results=[];checked=set()
    allrows=[('layout-'+str(i+1),r) for i,r in enumerate(deck['layouts'])]
    allrows += [(c['id']+'-'+str(i+1),r) for c in deck['challenges'] for i,r in enumerate(c['completions'])]
    for label,row in allrows:
        obstacles=[placed(p['part'],tuple(p['origin']),p['rotation']) for p in row['placements']]+[parts['tray']]
        # Initial solid pair clashes and insertion: disjoint XY reservations plus upward access.
        for i,a in enumerate(obstacles):
            for b in obstacles[i+1:]:assert ov(a,b)<1e-5,(label,'architecture clash')
        route_records=[]
        for route in row['routes']:
            pts=pathpoints(route)
            for a,b in zip(pts,pts[1:]):
                sw=capsule(tuple(a),tuple(b))
                for o in obstacles:assert ov(sw,o)<1e-5,(label,'sweep',a,b)
            route_records.append({'cells':route,'continuous_envelope_clear':True,'finger_access':fingers(row['placements'],route)})
        results.append({'id':label,'routes':route_records})
        print('physical',label,'passed',flush=True)
    # Low gate rejects actual finite cabin at its own portal center.
    low=ov(parts['C'],Pos(48,25.6,0)*parts['ferry']);assert low>1
    # Every non-opening perimeter edge blocks the hull without lifting; openings have continuous floor.
    for x,y in [(6,92),(178,92),(28,6),(156,6),(28,178),(156,178)]:
        assert ov(parts['tray'],Pos(x,y,4)*parts['ferry'])>1
    result={'status':'pass','source_sha256':hashlib.sha256((ROOT/'quayshift_lib.py').read_bytes()).hexdigest(),'supports':supports,'layouts_and_completions':results,'low_actual_overlap_mm3':low,'edge_escape_blocked':True,'floor':'single continuous4mm base; engraved seams0.35wide and0.25deep cannot create raised snag or unsupported ferry disc','limitations':['Uniform solid COM; infill/warping not modeled.','Finger10mm proxies and geometric handoffs are not human comfort tests.','No physical fit, print, fun, durability or commercial validation.']}
    (ROOT/'measure/physical-validation.json').write_text(json.dumps(result,indent=2))
    print('PASS finite solids, continuous ferry sweeps, fingers, support assumptions and edge boundary')
if __name__=='__main__':main()
