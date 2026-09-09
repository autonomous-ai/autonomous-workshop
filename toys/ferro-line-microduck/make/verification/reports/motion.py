"""Emit source-aligned rigid motion claims; no physical bond/run qualification."""
from pathlib import Path
import json
P=Path(__file__).parent
fixed=['frame','anchor','bill','lens','head_rim','dark_lens','sensor','neck_skin','boot_left','boot_right','sole_left','sole_right','shin_left','shin_right','pin_left','pin_right']
conditions=[]
def linear(name,part,obs,vec,expect='clear',steps=20):
    conditions.append(dict(id=name,check='linear_motion_collision',expect=expect,inputs=dict(moving_part=part,obstacle_parts=obs,translation=vec,steps=steps,allow_seated_contact=True),thresholds={'maxOverlapMm3':.001}))
linear('rotor-insertion-removal-before-wheel-and-anchor','rotor',['frame'],[100,0,0],steps=50)
linear('left-wheel-insertion-before-bond','left_wheel',['frame','rotor','shin_left'],[-20,0,0])
linear('anchor-service-assembly-before-bond','anchor',['frame','rotor','left_wheel'],[0,0,-20])
for side,sign in [('left',-1),('right',1)]:
    linear('roller-'+side+'-insertion','roller_'+side,['frame'],[sign*20,0,0])
    linear('pin-'+side+'-insertion-before-bond','pin_'+side,['frame','roller_'+side],[sign*20,0,0])
for part in ['bill','lens','head_rim','dark_lens','sensor','neck_skin','boot_left','boot_right','sole_left','sole_right','shin_left','shin_right']:
    linear(part+('-lateral-assembly-before-bond' if part=='shin_left' else '-front-assembly-before-bond'),part,[n for n in fixed if n!=part and not (part=='neck_skin' and n=='bill')]+['rotor','roller_left','roller_right']+([] if part=='shin_left' else ['left_wheel']),[-60,0,0] if part=='shin_left' else [0,-40,0],steps=30 if part=='shin_left' else 20)
linear('integral-right-wheel-stops-leftward-rotor','rotor',['frame'],[-5,0,0],'blocked')
linear('left-wheel-stops-rightward-wheel','left_wheel',['frame'],[5,0,0],'blocked')
def rot(part,y,z,end,driven=False):
    row={'part':part,'rotation':{'axis_point':[0,y,z],'axis_direction':[1,0,0],'start_deg':0,'end_deg':end}}
    if driven:row['driven']=True
    return row
conditions.append({'id':'drive-full-cycle-ground-rolling-assumed','check':'coupled_motion_collision','expect':'clear','description':'D-flat directly transmits rotor torque to left wheel; idler angles assume no-slip ground contact, not a shaft linkage. Whole-body translation omitted in body coordinates.','inputs':{'steps':72,'movers':[rot('rotor',-6,10,360),rot('left_wheel',-6,10,360,True),rot('roller_left',12,6,600),rot('roller_right',12,6,600)],'obstacle_parts':fixed},'thresholds':{'maxOverlapMm3':.001,'maxStepMm':1.8}})
manifest={'assembly':'microduck.step.py','conditions':conditions,'limitations':['Anchor, axle pins, cosmetic panels and left wheel require permanent adhesive joints. No rigid-body sweep proves their bond strength; they are obstacles in installed operation only, not declared fixed retention roots.','Only the stated integral-frame shoulder directions have blocked proofs. Opposite rotor retention requires the physically unqualified wheel bond.','Rear idlers are ground driven under no-slip rolling assumption. Elastic cord is checked separately by check_drive.py; deformable knot and material stress are outside this rigid-motion manifest.']}
(P/'motion.json').write_text(json.dumps(manifest,indent=2)+'\n')
