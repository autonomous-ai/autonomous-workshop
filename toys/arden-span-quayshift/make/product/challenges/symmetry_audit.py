"""Compare ordered-port and unordered-port completion equivalence; no CAD claim."""
import json
from pathlib import Path
import solver
ROOT=Path(__file__).resolve().parent

def key(poses,rx=False,ry=False):
    build=[next(v for v in solver.p.CANDIDATES[p['part']] if v['origin']==p['origin'] and v['rotation']==p['rotation']) for p in poses]
    def q(v):return (4-v[0] if rx else v[0],4-v[1] if ry else v[1])
    return tuple(sorted((solver.GROUP[v['part']],tuple(sorted(map(q,v['feet']))),q(v['gap']) if v['gap'] is not None else (-1,-1)) for v in build))

def main():
    data=json.loads((ROOT/'challenges.json').read_text())
    rows=[]
    for c in data['challenges']:
        c2={min(key(w['placements'],rx) for rx in (False,True)) for w in c['completions']}
        d2={min(key(w['placements'],rx,ry) for rx in (False,True) for ry in (False,True)) for w in c['completions']}
        rows.append({'id':c['id'],'ordered_ports_C2':len(c2),'unordered_ports_D2':len(d2)})
    out={'scope':'Requotient existing exhaustively enumerated completions; setup clues already enforced. Footprints only; not physical facing equivalence.','ordered_ports_C2':['identity','x reflection'],'unordered_ports_D2':['identity','x reflection','y reflection with route reversal','180-degree rotation with route reversal'],'results':rows}
    (ROOT/'symmetry-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(rows))
if __name__=='__main__':main()
