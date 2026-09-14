"""Built-solid carrier and service audit, not a force or radio test."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from moon_lib import *
from moon_assembly import assemble

def overlap(a,b):
    c=a & b
    return sum(v.volume for v in c.solids()) if c is not None else 0.0

def require_clear(a,b,why):
    v=overlap(a,b)
    assert v<1e-5,(why,v)
    return v

body,rotor,lid,tag,ko=carrier(),leaf(),cover(),inlay_datum(),keepout()
report={}
report['named_carrier_solids']=['inlay_datum','pocket','window_wall','keepout','cover']
for name,obj,expected in [('inlay',tag,(11.5,21.5,0.75)),('pocket',pocket(),(12.5,22.5,1.05)),('window',window_wall(),(15.5,25.5,1.0)),('keepout',ko,(15.5,25.5,3.25))]:
    bb=obj.bounding_box().size
    dims=[bb.X,bb.Y,bb.Z]
    assert all(abs(a-b)<1e-6 for a,b in zip(dims,expected)),(name,dims)
    report[name+'_measured_mm']=dims
require_clear(body,pocket(),'actual pocket void')
assert abs(overlap(body,window_wall())-window_wall().volume)<1e-5,'window not continuous'
require_clear(tag,body,'flat inlay free of body')
require_clear(tag,lid,'inlay free of cover')
report['side_clearance_mm']=0.5
report['rear_clearance_mm']=lid.bounding_box().min.Z-tag.bounding_box().max.Z
assert abs(report['rear_clearance_mm']-0.3)<1e-6
pivot=Pos(*PIVOT,-1.6)*pin()
report['pivot_keepout_overlap_mm3']=require_clear(pivot,ko,'pivot keepout')
roofs=[box(8.8,1.2,1.05,COIL_X,sign*17.55,3.55) for sign in (-1,1)]
for r in roofs: require_clear(r,ko,'capture roof keepout')
for a in range(76):
    posed=rotor.rotate(Axis((*PIVOT,0),(0,0,1)),a)
    require_clear(posed,ko,'moving leaf/peg keepout')
report['keepout_obstruction_set']='pin; entire moving leaf including stop peg, each1degree; cover-capture roofs. Pocket enclosing sidewalls, floor, inlay and retaining cover are intended enclosure exclusions, not mechanism ribs.'
report['max_moving_keepout_overlap_mm3']=0
# Full tag extraction after removing lid, with leaf held open.
opened=rotor.rotate(Axis((*PIVOT,0),(0,0,1)),SWING)
for z in range(16):
    moving=Pos(0,0,z)*tag
    for obstacle in (body,opened,pivot): require_clear(moving,obstacle,'inlay +Z extraction')
# Once its tabs have been elastically released, lid rises from above roofs.
for z in range(3,19):
    moving=Pos(0,0,z)*lid
    for obstacle in (body,opened,pivot):require_clear(moving,obstacle,'released cover +Z extraction')
report['service_axis']='+Z, leaf held at75 degrees; tag0..15mm and released cover3..18mm sampled1mm'
report['cover_release_limit']='Elastic transition through first3mm separately modelled analytically, not established by rigid sweeps.'
for a in (0,75):
    posed=rotor.rotate(Axis((*PIVOT,0),(0,0,1)),a)
    assert posed.distance_to(body)<1e-6,('stop not touching',a,posed.distance_to(body))
    require_clear(posed,body,'nominal stop contact')
report['endpoint_contact_distance_mm']=[0,0]
# The load-bearing perimeter spine is actual material, clear of antenna footprint.
spine=body & box(4,25,4.6,-40)
assert spine.volume>200
require_clear(spine,ko,'perimeter spine bypass')
report['perimeter_spine_volume_mm3']=spine.volume
# Released elastic lid: parabolic beam estimate, 34.4mm span,0.5mm total shortening.
span,shortening,t=34.4,0.5,1.2
rise=math.sqrt(3*span*shortening/8)
strain=4*t*rise/span**2
report['cover_release_estimate']={'span_mm':span,'total_end_shortening_mm':shortening,'upward_bow_mm':rise,'surface_strain_fraction':strain,'physical_validation':'not performed; force and20 service cycles untested'}
# Pin legs close0.35mm each. Cantilever estimate excludes local notch stress.
report['pin_release_estimate']={'leg_length_mm':6.9,'inward_tip_mm':0.35,'surface_strain_fraction':1.5*1.7*0.35/6.9**2,'physical_validation':'not performed; actual elastic snap fit untested'}
report['closed_bounds_mm']=list(assemble().bounding_box().size)
report['open_bounds_mm']=list(assemble(75).bounding_box().size)
report['physical_claims']='No RF range, fit, fatigue, load rating or physical print has been measured.'
Path(__file__).with_name('carrier-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
