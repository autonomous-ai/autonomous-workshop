"""Finite source checks of repaired apron clearance; not physical finger safety."""
import json,math
from pathlib import Path
from build123d import Align,Axis,Cylinder,Pos
import params as p
from parts.apron_shell import build,thumb_centers
from parts.flipper import rotor
from parts.flipper_guard_base import guard_base

def volume(shape):
    return 0.0 if shape is None else sum(abs(s.volume) for s in shape.solids())

def gap(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    return math.sqrt(sum(max(0,getattr(aa.min,k)-getattr(bb.max,k),getattr(bb.min,k)-getattr(aa.max,k))**2 for k in 'XYZ'))

def audit():
    targets={}
    for side in ('left','right'):
        targets['apron_'+side]=build(side)
        targets['flipper_'+side+'_guard_base']=Pos(*p.FLIPPER_PIVOTS[side],0)*guard_base(side)
    results=[]
    for side in ('left','right'):
        px,py=p.FLIPPER_PIVOTS[side];direction=1 if side=='left' else -1
        source=rotor(side);centers=thumb_centers(side)
        for i,(tx,ty) in enumerate(centers):
            angle=direction*p.FLIPPER_TRAVEL*i/(len(centers)-1)
            moving=Pos(px,py,0)*source.rotate(Axis.Z,angle)
            thumb=Pos(tx,ty,p.FLIPPER_ROTOR_Z)*Cylinder(p.FLIPPER_THUMB_R,p.FLIPPER_ROTOR_T+p.FLIPPER_THUMB_EXTRA+p.FLIPPER_TEXTURE_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
            row={'side':side,'angle_deg':angle,'intersections':{},'thumb_clearances_mm':{}}
            for name,target in targets.items():
                overlap=0.0 if gap(moving,target)>0 else volume(moving.intersect(target))
                lower=gap(thumb,target)
                distance=lower if lower>=p.APRON_THUMB_CLEARANCE else thumb.distance_to(target)
                row['intersections'][name]=overlap
                row['thumb_clearances_mm'][name]={'value':distance,'kind':'bbox_lower_bound' if lower>=p.APRON_THUMB_CLEARANCE else 'exact_BRep_distance'}
            row['pass']=all(v<=.001 for v in row['intersections'].values()) and all(v['value']>=p.APRON_THUMB_CLEARANCE-1e-6 for v in row['thumb_clearances_mm'].values())
            results.append(row)
            print(json.dumps({'side':side,'angle':angle,'pass':row['pass']}),flush=True)
    return {'pass':all(r['pass'] for r in results),'poses':len(results),'results':results,
            'scope':'Sampled rigid intersections and thumb-pad clearance only; no interpolation, impact, friction, access certification or physical-play claim'}

if __name__=='__main__':
    result=audit();Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'}))
    raise SystemExit(not result['pass'])
