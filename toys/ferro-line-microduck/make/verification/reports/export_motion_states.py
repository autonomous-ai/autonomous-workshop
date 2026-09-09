"""Exact CAD winding, lowering and conditional no-slip release states."""
from pathlib import Path
import sys,json,hashlib,math
P=Path(__file__).resolve().parents[1]
# CAD dependencies are provided by the verifier/runtime, independent of host workspace.
sys.path.insert(0,str(P))
from build123d import Axis,Compound,Pos,export_stl
import duck_lib as f
assembly=f.build_assembly()
parts=list(assembly.children)
assert len(parts)==20,(len(parts),[p.label for p in parts])
D=P/'measure/states';D.mkdir(exist_ok=True)
rows=[]
phases=[('winding',-360*i/7,0,[0,0,3]) for i in range(8)]
phases.append(('lowering',-360,0,[0,0,0]))
phases.extend(('release',-360+360*i/11,(360*i/11)*10/6,
               [0,-10*math.radians(360*i/11),0]) for i in range(12))
for i,(phase,angle,rear_angle,translation) in enumerate(phases):
    state=[]
    for p in parts:
        if p.label in ('rotor','left_wheel'):q=p.rotate(Axis((0,-6,10),(1,0,0)),angle)
        elif p.label in ('roller_left','roller_right'):q=p.rotate(Axis((0,12,6),(1,0,0)),rear_angle)
        else:q=p
        # Positive X rotation moves the contact point toward +Y relative to
        # the axle; matching -Y translation makes ground contact stationary.
        q=Pos(*translation)*q
        state.extend(q.solids())
    file=D/f'{i:02}.stl'
    export_stl(Compound(children=state),file,tolerance=.08,angular_tolerance=.12)
    rows.append({'file':str(file.relative_to(P)),'phase':phase,'drive_angle_deg':angle,'rear_angle_deg':rear_angle,'translation_mm':translation,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
report={'source_sha256':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ('duck_lib.py','drive_lib.py','measure/motion.json','measure/export_motion_states.py')},'state_count':len(rows),'coordinate_frame':'stationary ground Z=0; winding lifted Z=3 mm at fixed XY; release translates all parts forward -Y by 10 mm times unwound angle in radians','kinematics':'Eight user-held winding states turn the shaft and bonded D-wheel from 0 to -360 degrees about X while rear rollers remain stationary. The user lowers the toy while restraining the knob. Twelve release states unwind from -360 to 0 degrees; rear rollers rotate 10/6 of unwound angle under no-slip ground contact. One turn is within the two-turn limit. The 62.832 mm ideal release is illustrative kinematics, not physical dynamics or measured performance; user support and restraint are required during winding and lowering.','states':rows}
(D/'STATES.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
