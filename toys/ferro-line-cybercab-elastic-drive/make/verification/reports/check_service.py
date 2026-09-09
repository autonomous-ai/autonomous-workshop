"""Exact BRep service and quarter-turn elastic clearance; not a dynamics test."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cybercab_lib import *
from elastic_lib import envelope_evidence

def vol(s): return 0.0 if s is None else s.volume
b=body(); c=chassis(); d=chassis(1.9)
rows=[]
assert vol(b&c)<.001, 'Seated latch interferes'
assert vol((Pos(-1,0,0)*b)&c)>.001, 'Latch fails to retain'
for shift,lift in [(0,0),(-.5,0),(-1,0),(-2,0),(-3,0),(-4,0),(-4,1),(-4,3),(-4,10),(-4,30),(-4,55)]:
 overlap=vol((Pos(shift,0,lift)*b)&d)
 rows.append(dict(shift=shift,lift=lift,overlap_mm3=overlap))
 assert overlap<.001, f'Released shell collision {rows[-1]}'
wind=[]
for a in [0,-15,-30,-45,-60,-75,-90]:
 e=elastic(a);v=vol(e&c)+vol(e&b)
 rear=Pos(REAR_X,0,AXLE_Z)*Rot(0,a,0)*axle_set(True)
 rv=vol(e&rear)
 assert rv<.001, f'Elastic drive interference at {a}: {rv}'
 row=dict(angle_deg=a,rigid_frame_overlap_mm3=v,drive_overlap_mm3=rv,**{k:x for k,x in envelope_evidence(a).items() if k!='angle_deg'})
 wind.append(row);assert v<.001, f'Elastic frame collision {row}'
assert wind[-1]['centreline_chord_perimeter_mm']>wind[0]['centreline_chord_perimeter_mm'], 'Winding fails to extend band'
report=dict(ok=True,service=rows,elastic=wind,rolling_relation='travel_mm=16.5*radians(angle); negative angle rolls backward, release to zero rolls forward',limitation='Sampled installed envelope, no material force, grip, fatigue or physical run prediction')
(ROOT/'measure/service-clearance.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS seated fit, latch retention,11 service poses,7 elastic quarter-turn poses')
