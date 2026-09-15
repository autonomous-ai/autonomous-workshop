"""Source assembly pairwise overlap audit; native interfere remains mandatory."""
import argparse,hashlib,json
from pathlib import Path
from assemblies.product import build_product
from build123d import Compound

def volume(shape):
    if shape is None:return 0.0
    if hasattr(shape,'volume'):return abs(shape.volume)
    return sum(abs(s.volume) for s in shape)

def leaves(shape):
    if shape.children:
        for child in shape.children:yield from leaves(child)
    else:
        # Detach before any downstream pose copy: a parented leaf otherwise
        # deep-copies the complete assembly on every sampled transformation.
        leaf=Compound.cast(shape.wrapped).located(shape.global_location)
        leaf.label=shape.label
        leaf.color=shape.color
        yield leaf

def audit(mission='A',prefixes=()):
    assembled=build_product(mission=mission)
    parts=[(c.label,c,c.bounding_box()) for c in leaves(assembled)]
    clashes=[];checked=0
    for i,(name,a,ab) in enumerate(parts):
        for other,b,bb in parts[i+1:]:
            if prefixes and not any(name.startswith(p) or other.startswith(p) for p in prefixes):continue
            if any(getattr(ab.max,k)<getattr(bb.min,k)+1e-7 or getattr(bb.max,k)<getattr(ab.min,k)+1e-7 for k in 'XYZ'):continue
            checked+=1
            common=a.intersect(b)
            v=volume(common)
            if v>0.001:
                row={'a':name,'b':other,'volume_mm3':v}
                clashes.append(row)
                print(json.dumps(row),flush=True)
    return {'scope':'Source assembly overlaps only; not topology, retention or physical proof',
            'mission':mission,'filtered_prefixes':list(prefixes),'occurrences':len(parts),
            'checked_bbox_pairs':checked,'clashes':clashes,'pass':not clashes}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mission',choices=['A','B'],default='A')
    parser.add_argument('--prefix',action='append',default=[])
    parser.add_argument('--report',type=Path,default=Path(__file__).with_suffix('.json'))
    args=parser.parse_args()
    result=audit(args.mission,args.prefix)
    result['params_sha256']=hashlib.sha256((Path(__file__).parents[1]/'params.py').read_bytes()).hexdigest()
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='clashes'},indent=2))
    raise SystemExit(0 if result['pass'] else 1)
