"""Exact common-world service, exposed winding, and closed rolling states; no dynamics."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cybercab_lib import *
from build123d import export_stl,export_step
out=ROOT/'measure/states';out.mkdir(exist_ok=True)
states=[dict(body_shift=-4,body_lift=55,latch_deflection=1.9,angle=a) for a in (0,-30,-60,-90,-60,-30,0)]
states += [dict(body_shift=-4,body_lift=25,latch_deflection=1.9),dict(body_shift=-4,body_lift=0,latch_deflection=1.9),dict(latch_deflection=1.9),dict()]
states += [dict(angle=a,travel=WHEEL_R*math.radians(a)) for a in (-30,-60,-90,-60,-30,0)]
for i,kw in enumerate(states):
 model=assembly(**kw)
 export_stl(model,str(out/f'{i:02d}.stl'),tolerance=.05,angular_tolerance=.1)
 if i in (0,3,10): export_step(model,str(out/f'{i:02d}.step'))
 print('state',i,kw,flush=True)
(out/'states.json').write_text(json.dumps({'kind':'kinematic-envelope-not-physical-test','states':states},indent=2)+'\n')
