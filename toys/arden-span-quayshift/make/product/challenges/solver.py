"""Exhaustive finite *cell-grammar* solver, not physical ferry proof.

All modules upright. Identical footprints at 180/270 are quotiented here;
CAD must independently establish any architectural-detail equivalence.
"""
import importlib.util
import itertools
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('probe', ROOT/'original_grammar.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
GROUP = {'A':'high','B':'high','C':'low','D':'court','E':'pair','F':'pair','G':'tower','H':'tower'}
START, END = (2,0), (2,4)

def key(build, mirror=False):
    def point(q): return (4-q[0],q[1]) if mirror else tuple(q)
    return tuple(sorted((GROUP[v['part']],tuple(sorted(map(point,v['feet']))),
                         point(v['gap']) if v['gap'] is not None else (-1,-1)) for v in build))

def canonical(build):
    # Only identity and left/right reflection fix the labeled C1 and C5 ports.
    # Translations and quarter-turn board rotations are not legal equivalences.
    return min(key(build),key(build,True))

def paths(build):
    blocked = set().union(*(v['feet'] for v in build))
    blocked |= {v['gap'] for v in build if v['kind']=='low'}
    gaps = {v['gap']: (v['rotation']%180==0) for v in build if v['kind']=='high'}
    # True: strip runs x, ferry must move y; False: ferry must move x.
    def edge(a,b):
        for q in (a,b):
            if q in gaps:
                if gaps[q] and a[0]!=b[0]: return False
                if not gaps[q] and a[1]!=b[1]: return False
        return True
    found=[]
    def walk(route):
        at=route[-1]
        if at==END:
            if set(gaps)<=set(route) and edge(at,(2,5)): found.append(route)
            return
        x,y=at
        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if q in p.ALL and q not in blocked and q not in route and edge(at,q):
                walk(route+[q])
    if START not in blocked and edge((2,-1),START): walk([START])
    return found

def encode(build):
    return [{'part':v['part'],'origin':v['origin'],'rotation':v['rotation']} for v in sorted(build,key=lambda v:v['part'])]

def solve(build, loose):
    fixed=[v for v in build if v['part'] not in loose]
    examined=0
    winners={}
    occupied=set().union(*(v['envelope'] for v in fixed))
    def rec(left,used,chosen):
        nonlocal examined
        if not left:
            examined+=1
            whole=fixed+chosen
            route=paths(whole)
            if route:
                ck=canonical(whole)
                winners.setdefault(ck,{'placements':encode(whole),'routes':route,'route_count':len(route)})
            return
        choices={n:[v for v in p.CANDIDATES[n] if not used&v['envelope']] for n in left}
        name=min(left,key=lambda n:(len(choices[n]),n))
        for v in choices[name]:
            # Quotient permutations of interchangeable *loose* modules.
            peers=[w for w in chosen if GROUP[w['part']]==GROUP[name]]
            if peers and key([v]) <= key([peers[-1]]): continue
            rec([n for n in left if n!=name],used|v['envelope'],chosen+[v])
    rec(list(loose),occupied,[])
    return {'fixed':encode(fixed),'loose':list(loose),'nonoverlapping_candidates_examined':examined,
            'valid_completion_classes':len(winners),'completions':list(winners.values())}

def witnesses():
    routes=[[(2,0),(2,1),(2,2),(2,3),(2,4)],
            [(2,0),(2,1),(1,1),(1,2),(1,3),(2,3),(2,4)],
            [(2,0),(2,1),(1,1),(1,2),(1,3),(2,3),(3,3),(3,4),(2,4)]]
    return [p.find_build(r)[0] for r in routes]

def main():
    builds=witnesses()
    challenges=[]
    selections=[(0,'First passage',('A','C'),'Put the high arch on the ferry line; park the low gate away from it. Two completions are allowed.'),
                (1,'Around the corner',('A','D','F'),'Orient the long building and courtyard to preserve the westward detour and its return to C5; then keep the entrance bridge open.'),
                (2,'The open court',('D','E','F'),'Place both interchangeable long buildings and the courtyard around two fixed high passages. Preserve a return corridor to C5; unused water is allowed.')]
    for i,(wi,title,loose,deduction) in enumerate(selections,1):
        result=solve(builds[wi],loose)
        result.update(id=f'Q{i:02}',title=title,witness=f'layout-{wi+1}',deduction=deduction)
        challenges.append(result)
    layouts=[]
    for i,build in enumerate(builds,1):
        failures=[]
        for name in ('A','B'):
            altered=[dict(v) for v in build]
            for v in altered:
                if v['part']==name: v['kind']='low'
                if v['part']=='C': v['kind']='high'
            failures.append({'swap':[name,'C'],'valid_routes':len(paths(altered)),
                             'reason':'The low opening occupies a required high passage; no alternative visits both high openings.'})
        # Concrete tempting single-piece changes that still obey non-overlap.
        for name in ('D','E','F'):
            original=next(v for v in build if v['part']==name)
            rest=[v for v in build if v['part']!=name]
            used=set().union(*(v['envelope'] for v in rest))
            wrong=next((v for v in p.CANDIDATES[name] if v['rotation']!=original['rotation']
                        and not v['envelope']&used and not paths(rest+[v])),None)
            if wrong is not None:
                failures.append({'replace':name,'placement':encode([wrong])[0],
                                 'valid_routes':0,'nonoverlapping':True,
                                 'reason':'All pieces fit on the grid, but this orientation cuts the required connected trip through both high passages.'})
        layouts.append({'id':f'layout-{i}','placements':encode(build),'routes':paths(build),
                        'route_count':len(paths(build)),'tempting_failures':failures})
    assert len({canonical(b) for b in builds})==3
    assert challenges[0]['valid_completion_classes']==2
    report={'scope':'Exhaustive abstract cell-grammar evidence only; every advertised completion and route still needs exact finite-solid validation.',
            'symmetry':'A/B, E/F, G/H interchangeable; identity and x reflection preserve each labeled entry/exit. Fixed clues are retained before quotienting full solutions.',
            'high_gap_rule':'Traverse perpendicular to the arch strip, straight through consecutively. No turn inside any gap. Virtual outside cells enforce entry/exit direction.',
            'quarter_turns':'0/90/180/270 upright; geometrically duplicate footprint orientations collapsed. Finite CAD details must be invariant or separately checked.',
            'difficulty':'Editorial intended progression only, not human playtest or measured difficulty.',
            'deck_shortfall':'Three edited challenges, not the aspirational 24; do not describe this as a completed 24-card set.',
            'layouts':layouts,'challenges':challenges}
    evidence_path=ROOT/'validation-scope.json'
    if evidence_path.exists():
        evidence=json.loads(evidence_path.read_text())
        subject=[[(v['placements'],v['routes']) for v in c['completions']] for c in challenges]
        subject_sha=hashlib.sha256(json.dumps(subject,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if subject_sha==evidence['representative_poses_routes_sha256']:
            report['finite_validation']=evidence
            report['scope']='Exhaustive footprint completion classes, each with at least one exact representative pose checked by the linked CAD evidence. Counts do not enumerate all facade facings or prove hands-on comfort.'
    (ROOT/'challenges.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{'id':c['id'],'candidates':c['nonoverlapping_candidates_examined'],'completions':c['valid_completion_classes'],'routes':sorted({v['route_count'] for v in c['completions']})} for c in challenges],indent=2))

if __name__=='__main__': main()
