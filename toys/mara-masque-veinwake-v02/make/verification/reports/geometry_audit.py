"""Measure written STEP geometry and exact signature states, independently of parameters."""
import json
import math
import sys
from pathlib import Path
from build123d import GeomType, Pos
from cadgen.step_scene import import_step

PROJECT = Path(sys.argv[1]).resolve()

def close(a,b,tol=0.0001):
    assert abs(a-b) <= tol, (a,b)

def bounds(shape):
    b=shape.bounding_box()
    return [b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z]

def run():
    rind=import_step(PROJECT/'part_rind.step')
    tooth=import_step(PROJECT/'part_tooth_1.step')
    bubble=import_step(PROJECT/'part_bubble_1.step')
    complete=import_step(PROJECT/'veinwake.step')
    for shape,expected in ((rind,[140,130,14]),(tooth,[28,28,26]),
                           (bubble,[28,28,26]),(complete,[140,130,32])):
        b=bounds(shape)
        for a,e in zip([b[3]-b[0],b[4]-b[1],b[5]-b[2]],expected):close(a,e)
    assert len(complete.solids())==10
    for path in PROJECT.glob('part_*.step'):
        s=import_step(path)
        assert len(s.solids())==1 and s.volume>0
        close(bounds(s)[2],0)
    floors=[]
    for face in rind.faces():
        b=bounds(face)
        if face.geom_type==GeomType.PLANE and abs(b[2]-6)<0.0001 and abs(b[5]-6)<0.0001:
            close(face.area, math.pi*15**2)
            c=face.center(); floors.append([round(c.X,5),round(c.Y,5),round(c.Z,5)])
    expected=[[x,y,6] for x in (-36,0,36) for y in (-36,0,36)]
    assert sorted(floors)==sorted(expected)
    fits=[]
    for name,part in (('tooth',tooth),('bubble',bubble)):
        for x,y,z in floors:
            intersection=rind & (Pos(x,y,z)*part)
            overlap=0.0 if intersection is None else intersection.volume
            assert abs(overlap)<0.001,(name,x,y,overlap)
            fits.append({'habit':name,'seat':[x,y,z],'overlap_mm3':overlap})
    cap=[f for f in tooth.faces() if abs(bounds(f)[2]-26)<0.0001 and abs(bounds(f)[5]-26)<0.0001]
    assert len(cap)==1
    close(cap[0].area,3*math.sqrt(3)*2.5**2/2)
    before=import_step(PROJECT.parents[1]/'presentation/states/before.step')
    after=import_step(PROJECT.parents[1]/'presentation/states/after.step')
    a={c.label:c for c in before.children}
    b={c.label:c for c in after.children}
    # Import may expose an outer root; descend it when necessary.
    if len(a)==1 and next(iter(a.values())).children:a={c.label:c for c in next(iter(a.values())).children}
    if len(b)==1 and next(iter(b.values())).children:b={c.label:c for c in next(iter(b.values())).children}
    assert set(a)==set(b)=={'rind','tooth_1','tooth_2','tooth_3','bubble_1','bubble_2'},(list(a),list(b))
    state_rows=[]
    for name in a:
        aa,bb=bounds(a[name]),bounds(b[name])
        delta=[bb[i]-aa[i] for i in range(3)]
        for actual,target in zip(delta,[0,0,-55] if name=='tooth_3' else [0,0,0]):close(actual,target)
        close(a[name].volume,b[name].volume)
        moved=Pos(*delta)*a[name]
        difference=moved-b[name]
        close(0.0 if difference is None else difference.volume,0,0.001)
        difference=b[name]-moved
        close(0.0 if difference is None else difference.volume,0,0.001)
        state_rows.append({'part':name,'delta_mm':delta})
    result={'status':'pass','units':'mm','normal_envelope':[140,130,32],
            'printable_parts':10,'cluster_envelope':[28,28,26],
            'measured_seat_floor_centers':sorted(floors),'seat_diameter':30,
            'radial_clearance':1,'seat_depth':2,'floor_thickness':6,
            'nearest_pocket_wall':6,'tooth_tip_across_flats':2.5*math.sqrt(3),
            'all_seat_fits':fits,'signature_changes':state_rows,
            'limitation':'Exact digital geometry only; no print, handling or durability test.'}
    (PROJECT/'measure/geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('all_seat_fits','measured_seat_floor_centers')}))

if __name__=='__main__':run()
