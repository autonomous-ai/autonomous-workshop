"""Current exported B-rep geometry; also reusable face extraction for fit audit."""
from pathlib import Path
import hashlib,json,math,sys
from build123d import import_step,GeomType
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import rainward_lib as p
TOL=0.002

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def bounds(s): return tuple(float(v) for v in s.bounding_box().size)
def close(a,b,tol=1e-5): assert all(abs(x-y)<tol for x,y in zip(a,b)),(a,b)
def horizontal(f,z):
    b=f.bounding_box()
    return f.geom_type==GeomType.PLANE and abs(b.min.Z-z)<1e-5 and abs(b.max.Z-z)<1e-5

def projected(f,tight=False):
    vertices,triangles=f.tessellate(0.0001 if tight else TOL,0.01 if tight else 0.03)
    polygons=[]
    for tri in triangles:
        poly=Polygon([(vertices[i].X,vertices[i].Y) for i in tri])
        if poly.area>1e-12: polygons.append(poly)
    return unary_union(polygons)

def load():
    shapes={name:import_step(ROOT/name).solids()[0] for name in ['part_sun.step','part_single_01.step','part_fork_01.step','part_die_1.step','part_cup_1.step']}
    sun=shapes['part_sun.step']
    flats=[f for f in sun.faces() if horizontal(f,16.8)]
    lanes={}
    for f in flats:
        c=f.center(); angle=math.degrees(math.atan2(c.Y,c.X))
        lane=min(range(1,25),key=lambda n:abs((angle-p.theta(n)+180)%360-180))
        assert lane not in lanes,('duplicate_lane',lane)
        poly=projected(f)
        assert abs(poly.area-f.area)<max(.08,f.area*.0001),('face_mesh_area',lane,poly.area,f.area)
        lanes[lane]=poly
    tops=[f for f in sun.faces() if horizontal(f,17)]
    center=[f for f in tops if f.area>1000]
    assert len(center)==1
    marker_tops=[f for f in tops if f.area<20]
    markers={}
    for lane in (6,12,18,24):
        angle=p.theta(lane)+7.5; x,y=p.xy(65,angle)
        faces=[]
        for f in sun.faces():
            b=f.bounding_box(); c=f.center()
            if b.min.Z>=16-1e-5 and b.max.Z>16+1e-5 and f.area<25 and math.hypot(c.X-x,c.Y-y)<6:
                faces.append(projected(f))
        markers[lane]=unary_union(faces)
        assert not markers[lane].is_empty,('missing_marker',lane)
    footprints={}
    for kind in ('single','fork'):
        shape=shapes[f'part_{kind}_01.step']
        bottom=[f for f in shape.faces() if horizontal(f,0)]
        top=[f for f in shape.faces() if horizontal(f,4)]
        assert len(bottom)==len(top)==1
        poly=projected(bottom[0],True); upper=projected(top[0],True)
        assert poly.symmetric_difference(upper).area<.002
        assert abs(poly.area-bottom[0].area)<.002
        footprints[kind]=poly
    return shapes,lanes,projected(center[0]),markers,footprints,center[0],marker_tops

def main():
    shapes,lanes,bar,markers,footprints,center,marker_tops=load()
    sun=shapes['part_sun.step']; close(bounds(sun),(190,190,17))
    assert set(lanes)==set(range(1,25))
    assert len(center.inner_wires())==0 and abs(center.area-math.pi*24**2)<1e-5
    assert len(marker_tops)==4
    horizontal_levels=[]
    for face in sun.faces():
        box=face.bounding_box()
        if face.geom_type==GeomType.PLANE and abs(box.max.Z-box.min.Z)<1e-6:
            level=float(box.max.Z); horizontal_levels.append(level)
            assert min(abs(level-z) for z in (0,16,16.8,17))<1e-5,('unexpected_horizontal_feature',level)
    assert len([f for f in sun.faces() if horizontal(f,17)])==5,'unexpected endpoint dots or top features'
    marker_rows=[]
    for lane,poly in markers.items():
        a=math.radians(p.theta(lane)+7.5); c=poly.centroid
        longitudinal=c.x*math.cos(a)+c.y*math.sin(a)
        lateral=-c.x*math.sin(a)+c.y*math.cos(a)
        assert abs(longitudinal-65)<.02 and abs(lateral)<.01
        from shapely.affinity import rotate
        local=rotate(poly,-math.degrees(a),origin=(0,0)); b=local.bounds
        assert abs(b[0]-60)<.01 and abs(b[2]-70)<.01
        assert abs(b[1]+.4)<.01 and abs(b[3]-.4)<.01
        assert all(poly.intersection(flat).area<1e-7 for flat in lanes.values())
        clearance=min(poly.distance(flat) for flat in lanes.values())
        assert clearance>=.39
        marker_rows.append({'after_lane':lane,'radius_mm':longitudinal,'boundary_offset_mm':lateral,'footprint_bounds_in_boundary_frame':b,'minimum_lane_flat_clearance_mm':clearance})
    floors=unary_union([projected(f) for f in sun.faces() if horizontal(f,16)])
    gaps=[]
    for lane in range(1,25):
        a=math.radians(p.theta(lane)+7.5); x,y=p.xy(45,math.degrees(a)); t=(-math.sin(a),math.cos(a))
        line=LineString([(x-2*t[0],y-2*t[1]),(x+2*t[0],y+2*t[1])])
        crossing=floors.intersection(line)
        measured=crossing.length; expected=1.6 if lane%6==0 else .8
        assert abs(measured-expected)<.01,(lane,measured,expected)
        gaps.append({'after_lane':lane,'floor_width_mm':measured,'expected_mm':expected})
    die=shapes['part_die_1.step']; close(bounds(die),(16,16,16))
    cones=[f for f in die.faces() if f.geom_type==GeomType.CONE]; assert len(cones)==21
    for f in cones: assert abs(f.area-math.pi*math.hypot(1,1.1))<1e-5
    values={}; expected={tuple(n):v for v,n in p.PIP_FACES}
    for f in die.faces():
        if f.geom_type==GeomType.PLANE and f.area>100:
            n=tuple(round(v) for v in f.normal_at()); count=round((256-f.area)/math.pi)
            assert expected[n]==count
            values[str(n)]=count
    assert sorted(values.values())==[1,2,3,4,5,6]
    assert abs(die.volume-(4096-21*math.pi*1.1/3))<1e-5
    for kind in footprints: close(bounds(shapes[f'part_{kind}_01.step']),(12,8,4))
    close(bounds(shapes['part_cup_1.step']),(42,42,28))
    result={'status':'PASS','method':'Actual STEP B-rep planes and faces projected by tessellation, 0.002mm deflection; exact B-rep face areas and bounds checked separately. No nominal sector substitution.','source_sha256':sha(ROOT/'rainward_lib.py'),'step_sha256':{k:sha(ROOT/k) for k in shapes},'sun_mm':bounds(sun),'continuous_bar_area_mm2':center.area,'bar_radius_mm':24,'bar_inner_wires':0,'lane_flat_count':len(lanes),'lane_top_mm':16.8,'marker_top_count':len(marker_tops),'markers':marker_rows,'gaps':gaps,'dice_pips_by_normal':values,'pip_cones':21,'counter_planar_footprints_mm2':{k:v.area for k,v in footprints.items()},'limitations':'CAD evidence only, not physical testing or statistical dice fairness.'}
    Path(__file__).with_name('correction-geometry.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
if __name__=='__main__':main()
