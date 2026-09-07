"""Exact-solid mass audit and rolling states; prescribed damping is illustrative."""
import json, math
from pathlib import Path
from build123d import Axis, CenterOf, export_stl
from rocker_lib import rocker_rest, RADIUS
ROOT=Path(__file__).parent
body=rocker_rest()
center=body.center(CenterOf.MASS)
d=RADIUS-center.Z
assert len(body.solids())==1 and d>0 and abs(center.X)<1e-6 and abs(center.Y)<1e-6
angles=[20*math.exp(-i/12)*math.cos(i*math.pi/4) for i in range(25)]
angles[-1]=0.0
out=ROOT/'measure/states'
out.mkdir(parents=True,exist_ok=True)
rows=[]
for i,angle in enumerate(angles):
 theta=math.radians(angle)
 shape=body.rotate(Axis((0,0,RADIUS),(0,1,0)),angle).translate((RADIUS*theta,0,0))
 bb=shape.bounding_box()
 assert abs(bb.min.Z)<1e-5
 export_stl(shape,str(out/f'{i:02d}.stl'),tolerance=0.05,angular_tolerance=0.1)
 rows.append({'angle_deg':angle,'translation_mm':[RADIUS*theta,0,0],'minimum_z_mm':bb.min.Z,'com_height_mm':shape.center(CenterOf.MASS).Z})
checks=[]
for a in range(-20,21):
 t=math.radians(a)
 rise=d*(1-math.cos(t))
 restoring=-d*math.sin(t)
 assert rise>=0 and (a==0 or restoring*a<0)
 checks.append({'angle_deg':a,'com_rise_mm':rise,'torque_per_unit_weight_mm':restoring})
bb=body.bounding_box()
audit={'volume_mm3':body.volume,'solid_count':len(body.solids()),'center_of_mass_mm':list(center),'curvature_center_mm':[0,0,RADIUS],'com_below_curvature_center_mm':d,'bounds_mm':{'min':list(bb.min),'max':list(bb.max)},'assumption':'Homogeneous solid, uniform 100% infill. No-slip rolling on level rigid plane. Damping animation prescribed, not a dynamics or physical test.','potential':'U(theta)-U(0)=m*g*d*(1-cos(theta)); restoring generalized torque=-m*g*d*sin(theta)','range_deg':[-20,20],'restoring_checks':checks,'states':rows,'result':'PASS'}
(ROOT/'measure/balance.json').write_text(json.dumps(audit,indent=2)+'\n')
manifest={'assembly':'rocker.step.py','conditions':[{'id':'one-body-roll','description':'One rigid body rolls on a mathematical desk plane; balance.json separately checks plane tangency and restoring potential. No other product parts exist.','check':'coupled_motion_collision','expect':'clear','inputs':{'steps':24,'obstacle_parts':[],'movers':[{'part':'Solid circular-segment rocker','rotation':{'axis_point':[0,0,40],'axis_direction':[0,1,0],'angles_deg':angles},'translation':{'offsets_mm':[r['translation_mm'] for r in rows]}}]},'thresholds':{'maxOverlapMm3':0.01}}]}
(ROOT/'measure/motion.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ('states','restoring_checks')},indent=2))
