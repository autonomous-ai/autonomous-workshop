"""Deterministic manifest generation from the authored mechanism equations."""
import json,math
from pathlib import Path
N=120
angles=[i*360/N for i in range(N+1)]
q=[3*math.sin(math.radians(a)) for a in angles]
phi=[math.degrees(math.asin(-v/7)) for v in q]
axisrot=lambda x:{'axis_point':[x,0,86],'axis_direction':[0,1,0]}
rotor={'part':'rotor','rotation':{'axis_point':[0,0,22],'axis_direction':[1,0,0],'angles_deg':angles}}
follower={'part':'follower','driven':True,'translation':{'offsets_mm':[[0,0,v] for v in q]}}
wr={'part':'right_wing','driven':True,'rotation':dict(axisrot(10),angles_deg=[-v for v in phi])}
wl={'part':'left_wing','driven':True,'rotation':dict(axisrot(-10),angles_deg=phi)}
conditions=[{'id':'full-cycle-coupled','check':'coupled_motion_collision','expect':'clear','description':'Full cycle, all physical leaves covered. Bulk clearance at <=1.0 mm point steps; exact continuous cam/slot geometry and close root clearances are separately audited. Adhesive groups require cured positive-area lands.','inputs':{'movers':[rotor,follower,wl,wr],'steps':N,'obstacle_parts':['stationary']},'thresholds':{'maxOverlapMm3':0.001,'maxStepMm':1.0}}]
for side in ('left','right'):
 c=dict(rotor,part='cam_'+side)
 conditions.append({'id':side+'-cam-contact','check':'coupled_motion_collision','expect':'clear','description':'Isolated contact witness for this specific cam; all obstacles checked in full-cycle-coupled.','inputs':{'movers':[c,follower],'steps':N,'obstacle_parts':[]},'thresholds':{'maxOverlapMm3':0.001,'maxStepMm':1.0}})

def linear(id,part,obstacles,vec,expect='clear',description=''):
 length=math.sqrt(sum(v*v for v in vec));steps=max(8,math.ceil(length))
 conditions.append({'id':id,'check':'linear_motion_collision','expect':expect,'description':description,'inputs':{'moving_part':part,'obstacle_parts':obstacles,'translation':vec,'steps':steps,'allow_seated_contact':True},'thresholds':{'maxOverlapMm3':0.001,'maxStepMm':1.0}})

linear('cam-left-into-yoke','cam_left',['yoke'],[-24,0,0],description='Off-frame preassembly; shaft and frame not yet present.')
linear('cam-right-into-yoke','cam_right',['yoke'],[24,0,0],description='Off-frame preassembly; shaft and frame not yet present.')
conditions.append({'id':'load-yoke-cam-trio','check':'coupled_motion_collision','expect':'clear','description':'Reverse of placing hand-held yoke and loose cams through front opening, before shaft or rod is installed. All three are placement inputs, not operating outputs.','inputs':{'steps':45,'movers':[{'part':k,'translation':{'start':[0,0,0],'end':[0,45,0]}} for k in ('yoke','cam_left','cam_right')],'obstacle_parts':['frame'],'allow_seated_contact':True},'thresholds':{'maxOverlapMm3':0.001,'maxStepMm':1.0}})
installed=['frame','yoke','cam_left','cam_right']
linear('rod-from-above','rod',installed,[0,0,65],description='Rod through empty guide to yoke floor; crosshead absent.')
installed+=['rod']
linear('shaft-from-left','shaft',installed,[-65,0,0],description='Thread keyed shaft through prepared cams and bearings; crank absent.')
installed+=['shaft']
linear('crank-from-right','crank',installed,[15,0,0],description='Seat crank onto shaft end before upper moving parts.')
installed+=['crank']
for side in ('left','right'):
 linear('shoulder-pin-'+side,'shoulder_pin_'+side,installed,[0,-28,0],description='Pin enters rear access before wing and keeper.')
 installed+=['shoulder_pin_'+side]
for side in ('left','right'):
 linear('drive-pin-'+side+'-off-frame','drive_pin_'+side,['wing_'+side],[0,-24,0],description='Off-frame: seat drive pin head against loose wing rear face before mounting wing.')
 conditions.append({'id':'wing-'+side+'-onto-pin','check':'coupled_motion_collision','expect':'clear','description':'Wing and prebonded drive pin slide together onto shoulder axle; crosshead and drive caps absent.','inputs':{'steps':24,'movers':[{'part':k,'translation':{'start':[0,0,0],'end':[0,24,0]}} for k in ('wing_'+side,'drive_pin_'+side)],'obstacle_parts':list(installed),'allow_seated_contact':True},'thresholds':{'maxOverlapMm3':0.001,'maxStepMm':1.0}})
 installed+=['wing_'+side,'drive_pin_'+side]
 linear('shoulder-cap-'+side,'shoulder_cap_'+side,installed,[0,12,0],description='Seat blind keeper against shoulder pin tip.')
 installed+=['shoulder_cap_'+side]
linear('crosshead-from-front','crosshead',installed,[0,24,0],description='Slide slots onto both projecting drive pins at neutral while tongue reaches rod top; bird and drive caps absent.')
installed+=['crosshead']
for side in ('left','right'):
 linear('drive-cap-'+side,'drive_cap_'+side,installed,[0,12,0],description='Blind drive keeper seats against pin tip, ahead of crosshead.')
 installed+=['drive_cap_'+side]
for side in ('left','right'):
 linear('bird-'+side+'-to-seat','bird_'+side,installed,[0,0,25],description='Lower fixed body half onto frame foot seat last.')
 installed+=['bird_'+side]
proofs=[]
def seat(part,supports,vec,why):
 id=part+'-seat-stop'
 linear(id,part,supports,vec,'blocked',why+' This one-sided geometric seat does not prove adhesive pull-out strength.')
 proofs.append({'part':part,'condition':id,'supports':supports})
seat('shaft',['frame'],[2,0,0],'Left integral flange arrests positive axial travel.')
for side in ('left','right'): seat('cam_'+side,['shaft'],[0,-1,0],'D bore flat arrests radial translation through shaft.')
seat('crank',['shaft'],[-1,0,0],'Blind socket floor meets shaft end.')
seat('yoke',['cam_left','cam_right'],[0,0,2],'Lower return rail meets cam undersides after lash.')
seat('rod',['yoke'],[0,0,-1],'Rod end meets socket floor.')
seat('crosshead',['rod'],[0,0,-1],'Tongue underside meets rod end.')
for side in ('left','right'):
 seat('shoulder_pin_'+side,['frame'],[0,1,0],'Rear pin flange meets boss seat.')
 seat('shoulder_cap_'+side,['shoulder_pin_'+side],[0,-1,0],'Blind keeper floor meets pin tip.')
 seat('wing_'+side,['shoulder_cap_'+side],[0,2,0],'Wing hub meets keeper rear face.')
 seat('drive_pin_'+side,['wing_'+side],[0,1,0],'Drive pin head meets wing rear face.')
 seat('drive_cap_'+side,['drive_pin_'+side],[0,-1,0],'Blind drive keeper floor meets pin tip.')
 seat('bird_'+side,['frame'],[0,0,-1],'Body foot meets fixed frame seat.')
linear('rotor-negative-x-capture','rotor',['frame'],[-2,0,0],'blocked','Right crank collar meets bearing; relies on cured rotor bonds.')
linear('rod-positive-x-guide','rod',['frame'],[1,0,0],'blocked','Square guide limits lateral rod displacement.')
linear('rod-positive-y-guide','rod',['frame'],[0,1,0],'blocked','Square guide limits lateral rod displacement.')
for side in ('left','right'):
 linear('wing-'+side+'-rear-stop','wing_'+side,['frame'],[0,-2,0],'blocked','Rear boss arrests wing rearward axial travel.')
 linear('wing-'+side+'-radial-stop','wing_'+side,['shoulder_pin_'+side],[0,0,1],'blocked','Shoulder axle limits radial wing displacement.')
manifest={'assembly':'hummingbird.step.py','conditions':conditions,'retention':{'fixed_parts':['frame'],'proofs':proofs}}
Path(__file__).with_name('motion.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(len(conditions),'conditions;',len(proofs),'leaf seat proofs')
