"""Exact demonstrated manual capture path; no human-hand or dynamics claim."""
from pathlib import Path
import sys,json,hashlib
from build123d import import_step,Pos
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import rainward_lib as lib

def main():
    states=ROOT.parent/'evidence/states'
    before=import_step(states/'before.step'); after=import_step(states/'after.step')
    expected=lib.assembly('before').children
    solids=list(before.solids());named={}
    for part in expected:
        found=min(solids,key=lambda s:(s.center()-part.center()).length)
        assert (found.center()-part.center()).length<1e-5
        solids.remove(found);named[part.label]=found
    old,new=lib.piece_poses('before'),lib.piece_poses('after')
    victim=next(n for n in old if n.startswith('fork') and old[n]!=new[n])
    moving=named[victim]; obstacles=[s for n,s in named.items() if n!=victim]
    lift_bottom=max(s.bounding_box().max.Z for s in obstacles)+2
    start=old[victim][2];end=new[victim][2]
    # The vertical footprint remains fixed on extraction/descent; source
    # counter is a straight extrusion. Sampling21 positions per vertical leg checks contact
    # with stationary solids; horizontal transport has exact Z separation.
    checks=[]
    for phase,xy,z0,z1 in [('lift',start[:2],start[2],lift_bottom),('lower',end[:2],lift_bottom,end[2])]:
        for i in range(21):
            z=z0+(z1-z0)*i/20
            placed=Pos(xy[0]-start[0],xy[1]-start[1],z-start[2])*moving
            # AABB rejects remote solids before B-rep intersection.
            a=placed.bounding_box()
            for obstacle in obstacles:
                b=obstacle.bounding_box()
                if any(tuple(a.max)[k]<tuple(b.min)[k]-1e-7 or tuple(b.max)[k]<tuple(a.min)[k]-1e-7 for k in range(3)):continue
                overlap=placed.intersect(obstacle)
                volume=0 if overlap is None else sum(s.volume for s in overlap.solids())
                assert volume<1e-6,(phase,i,volume)
            checks.append({'phase':phase,'bottom_z_mm':z,'intersection_volume_mm3':0})
    max_z=max(s.bounding_box().max.Z for s in obstacles)
    assert lift_bottom-max_z>=2-1e-7
    report={'status':'PASS','scope':'Demonstrated before-state victim extraction, overhead transport, descent to free capture circle. Sampled vertical positions plus exact overhead Z clearance; not a continuous swept-volume guarantee or hand-access/physical test.','vertical_positions_checked':len(checks),'overhead_bottom_mm':lift_bottom,'highest_stationary_geometry_mm':max_z,'overhead_clearance_mm':lift_bottom-max_z,'sampled_positive_intersections':0,'state_sha256':{n:hashlib.sha256((states/f'{n}.step').read_bytes()).hexdigest() for n in ('before','after')}}
    Path(__file__).with_name('capture-clearance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
