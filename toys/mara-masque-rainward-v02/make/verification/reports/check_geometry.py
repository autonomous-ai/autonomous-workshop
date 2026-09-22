"""Current exact exported CAD checks for the correction requirements."""
from pathlib import Path
import json, math, sys
from build123d import import_step, GeomType
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import rainward_lib as p

def bounds(shape):return tuple(float(x) for x in shape.bounding_box().size)
def close(a,b):assert all(abs(x-y)<1e-5 for x,y in zip(a,b)),(a,b)

def main():
    sun=import_step(ROOT/'part_sun.step').solids()[0]
    close(bounds(sun),(190,190,28))
    # Top face is the entire uninterrupted circle, with no wires for blocks.
    tops=[f for f in sun.faces() if abs(f.center().Z-28)<1e-5 and f.geom_type==GeomType.PLANE]
    assert len(tops)==1
    assert abs(tops[0].area-math.pi*24**2)<1e-5
    assert len(tops[0].inner_wires())==0
    die=import_step(ROOT/'part_die_1.step').solids()[0]
    close(bounds(die),(16,16,16))
    cyl=[f for f in die.faces() if f.geom_type==GeomType.CONE]
    assert len(cyl)==21,len(cyl)
    for face in cyl:assert abs(face.area-math.pi*p.PIP_RADIUS*math.hypot(p.PIP_RADIUS,p.PIP_DEPTH))<1e-5
    floors=[f for f in die.faces() if f.geom_type==GeomType.PLANE and f.area<10]
    assert len(floors)==0
    for face in floors:assert abs(face.area-math.pi*p.PIP_RADIUS**2)<1e-5
    values={}
    for face in die.faces():
        if face.geom_type!=GeomType.PLANE or face.area<100:continue
        normal=tuple(round(x) for x in face.normal_at())
        n=round((256-face.area)/math.pi)
        values[str(normal)]=n
        expected=dict((tuple(normal),value) for value,normal in p.PIP_FACES)
        assert expected[normal]==n,(normal,n)
    assert len(values)==6 and sorted(values.values())==[1,2,3,4,5,6]
    assert abs(die.volume-(16**3-21*math.pi*1.1/3))<1e-5
    drops={}
    for kind in ['single','fork']:
        s=import_step(ROOT/f'part_{kind}_01.step').solids()[0]
        close(bounds(s),(12,8,4))
        planes=[f for f in s.faces() if f.geom_type==GeomType.PLANE and abs(abs(f.normal_at().Z)-1)<1e-5]
        assert len(planes)==2
        assert abs(planes[0].area-planes[1].area)<1e-5
        drops[kind]={'bbox_mm':bounds(s),'flat_contact_area_mm2':planes[0].area,'equal_planar_top_bottom':True}
    assert p.BAR_TOP==28 and p.DECK==16 and p.BAR_R==24
    assert p.RADII==(85.,72.,59.,46.,33.) and p.LANES==24
    result={'status':'PASS','sun_mm':bounds(sun),'bar_top_area_mm2':tops[0].area,'bar_top_inner_wires':0,'dice_face_values_by_outward_normal':values,'pip_cones':21,'pip_radius_mm':1,'pip_depth_mm':1.1,'dice_volume_mm3':die.volume,'checkers':drops,'limits':'Exact CAD only; no physical fairness or handling test.'}
    (ROOT/'measure/correction-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
