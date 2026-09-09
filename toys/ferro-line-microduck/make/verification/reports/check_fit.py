"""Exact project-specific fit and assembly-path audit; no physical-run claim."""
from pathlib import Path
import sys,json,itertools,hashlib
PROJECT=Path(__file__).resolve().parents[1]
# CAD dependencies are provided by the verifier/runtime, independent of host workspace.
sys.path.insert(0,str(PROJECT))
from build123d import Pos,Axis,CenterOf
import duck_lib as f
import drive_lib as d
TOL=1e-5
rows=[]
def clear(name,a,b):
    v=(a&b).volume
    assert v<TOL,(name,v)
    rows.append({'check':name,'intersection_mm3':v})
def main():
    frame=f.build_frame();rotor=d.build_rotor();wheel=d.build_left_drive_wheel();anchor=d.build_fixed_anchor()
    parts={'frame':frame,'rotor':rotor,'wheel':wheel,'anchor':anchor,'bill':f.build_bill(),'lens':f.build_lens()}
    for name in ['head_rim','dark_lens','sensor','neck_skin']:
        parts[name]=getattr(f,'build_'+name)()
    for side in [-1,1]:
        parts[f'boot{side}']=f.build_boot(side)
        parts[f'sole{side}']=f.build_boot(side,True)
        parts[f'shin{side}']=f.build_shin_skin(side)
        parts[f'roller{side}']=d.build_rear_roller(side);parts[f'pin{side}']=d.build_rear_pin(side)
    for name,p in parts.items():
        assert p.is_valid and len(p.solids())==1 and p.volume>0,name
    for (n,a),(m,b) in itertools.combinations(parts.items(),2):clear(n+' / '+m,a,b)
    assert abs(d.BEARING_D-d.AXLE_D-.4)<1e-9
    assert abs(d.ROLLER_BORE_D-d.PIN_D-.4)<1e-9
    assert abs(d.BONDED_WHEEL_BORE_D-d.AXLE_D-.2)<1e-9
    assert abs(d.AXIAL_GAP-.4)<1e-9
    for off in [100,80,60,40,20,10,5,2,0]:clear(f'rotor insertion +{off}',frame,Pos(off,0,0)*rotor)
    for off in [20,15,10,5,2,0]:clear(f'left wheel insertion -{off}',frame+rotor+parts['shin-1'],Pos(-off,0,0)*wheel)
    for side in [-1,1]:
        for off in [20,15,10,5,2,0]:
            clear(f'rear roller {side} insertion {off}',frame,Pos(side*off,0,0)*parts[f'roller{side}'])
            clear(f'rear pin {side} insertion {off}',frame+parts[f'roller{side}'],Pos(side*off,0,0)*parts[f'pin{side}'])
    for off in [-20,-10,-5,-2,0]:clear(f'anchor below-up {off}',frame+rotor+wheel,Pos(0,0,off)*anchor)
    fixed=frame+anchor
    for name,p in parts.items():
        if name not in ['frame','anchor','rotor','wheel','roller-1','roller1']:fixed+=p
    axis=Axis((0,d.DRIVE_Y,d.DRIVE_Z),(1,0,0))
    for angle in range(0,361,30):clear(f'drive rotation {angle}',fixed,(rotor+wheel).rotate(axis,angle))
    # Check full conservative revolved cylinders, not merely angular samples.
    envelope=d.x_cylinder(d.AXLE_D/2,-34.7,42)+d.x_cylinder(10,29,38)+d.x_cylinder(10,-35,-29)+d.x_cylinder(8,38,42)
    clear('continuous rotor revolved envelope',fixed,envelope)
    for side in [-1,1]:
        pin=parts[f'pin{side}'];roller=parts[f'roller{side}']
        for angle in [0,90,180,270]:clear(f'rear rotation {side} {angle}',fixed,roller.rotate(Axis((0,12,6),(1,0,0)),angle))
    volume=sum(p.volume for p in parts.values())
    c=[sum(p.volume*tuple(p.center(CenterOf.MASS))[i] for p in parts.values())/volume for i in range(3)]
    assert -32<c[0]<32 and -6<c[1]<12,('COM outside support',c)
    report={'ok':True,'source_sha256':{n:hashlib.sha256((PROJECT/n).read_bytes()).hexdigest() for n in ['duck_lib.py','drive_lib.py']},'frame_solids':len(frame.solids()),'uniform_density_com_mm':c,'total_solid_volume_mm3':volume,'checks':rows,'limitations':['Axial assembly sampled at listed offsets; cylindrical swept envelope independently checked for full installed rotation.','Permanent keyed-wheel/pin bonds require physical bond and wear validation.','Elastic torque, lacing, traction, fatigue and print performance not certified by this geometric audit.']}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
