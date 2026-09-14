"""Independent board-first exhaustive verifier; imports no originating solver.
Run with $WORKSHOP_PYTHON design/independent_verify.py from run workspace.
"""
import json, hashlib
from pathlib import Path
from collections import Counter
from itertools import combinations
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'arden-design.json').read_text())
I={p:{int(k):v for k,v in ports.items()} for p,ports in D['inventory'].items()}
DELTA=((-1,0),(0,1),(1,0),(0,-1))
def neighbor(cell,d):
    r,c=divmod(cell,3); dr,dc=DELTA[d];r+=dr;c+=dc
    return r*3+c if 0<=r<3 and 0<=c<3 else None
def ports(p,r):return {(d+r)%4:h for d,h in I[p].items()}
# Derive each piece's true orientation quotient from port maps, including T.
ORIENT={}
for p in I:
    unique={}
    for r in range(4):unique.setdefault(tuple(sorted(ports(p,r).items())),r)
    ORIENT[p]=list(unique.values())
def norm(p,r):
    return next(q for q in ORIENT[p] if ports(p,q)==ports(p,r))
def key(state):return tuple(sorted((c,p,norm(p,r)) for c,p,r in state))
def rotate_cell(c):r,col=divmod(c,3);return col*3+2-r
def rotated(state):return key([(rotate_cell(c),p,r+1) for c,p,r in state])
def canonical(state):
    k=key(state); ks=[k]
    for _ in range(3):ks.append(rotated(ks[-1]))
    return min(ks)
def path_of(state):
    table={c:(p,ports(p,r)) for c,p,r in state}
    start=next(c for c,(p,_) in table.items() if p=='G1')
    finish=next(c for c,(p,_) in table.items() if p=='G2')
    path=[start]
    while path[-1]!=finish:
        c=path[-1]
        available=[neighbor(c,d) for d in table[c][1] if neighbor(c,d) not in path]
        if len(available)!=1 or available[0] is None:return None
        path.append(available[0])
    return path if len(path)==9 else None

def enumerate_board():
    # Local seam constraint is tested as each cell is filled, including closed
    # sides; boundary ports are excluded. No Hamiltonian paths are precomputed.
    domains={c:[(p,r,ports(p,r)) for p in I for r in ORIENT[p]
        if all(neighbor(c,d) is not None for d in ports(p,r))] for c in range(9)}
    table=[]; used=set(); solutions=[]; disconnected=[]; nodes=0
    def visit(c):
        nonlocal nodes
        nodes+=1
        if c==9:
            state=key([(i,p,r) for i,(p,r,_) in enumerate(table)])
            path=path_of(state)
            (solutions if path else disconnected).append(state)
            return
        for p,r,ps in domains[c]:
            if p in used:continue
            if c>=3 and ps.get(0)!=table[c-3][2].get(2):continue
            if c%3 and ps.get(3)!=table[c-1][2].get(1):continue
            table.append((p,r,ps));used.add(p);visit(c+1);used.remove(p);table.pop()
    visit(0)
    return solutions,disconnected,nodes

def matches(s,clues):return set(key(clues))<=set(s)
def defects(state):
    t={c:ports(p,r) for c,p,r in state}; out=[]
    for c in range(9):
        for d in range(4):
            n=neighbor(c,d)
            if n is None:
                if d in t[c]:out.append({'type':'boundary','cell':c,'direction':d})
            elif c<n:
                a=t[c].get(d);b=t[n].get((d+2)%4)
                if a!=b:out.append({'type':'height' if a is not None and b is not None else 'direction','cells':[c,n],'levels':[a,b], 'height_difference_mm': None if a is None or b is None else abs(D['board']['local_route_levels_mm'][a]-D['board']['local_route_levels_mm'][b])})
    return out

def path_shape(path):
    variants=[tuple(path)]
    for _ in range(3):variants.append(tuple(rotate_cell(c) for c in variants[-1]))
    return min(variants)

def main():
    sol,disconnected,nodes=enumerate_board(); solset=set(sol)
    assert len(sol)==len(solset)
    source=json.loads((ROOT/'solutions.json').read_text())
    assert solset=={key(s['state']) for s in source['solutions']},'independent solution set differs'
    assert len(sol)==56 and len({canonical(s) for s in sol})==14
    assert ORIENT['T']==[0,1]
    challenges=[]
    for ch in D['challenges']:
        c=ch['clues'];g=[x for x in c if x[1].startswith('G')]; extras=[x for x in c if x not in g]
        hit=[s for s in sol if matches(s,c)]; gh=[s for s in sol if matches(s,g)]
        assert len(hit)==1 and hit[0]==key(ch['solution']['state'])
        assert path_of(hit[0])==ch['solution']['path']
        assert not defects(hit[0])
        assert len(gh)==ch['solutions_with_gates']
        # Check global minimal extra clues among ALL nongate entries in solution.
        nongates=[x for x in hit[0] if not x[1].startswith('G')]
        minimal=next(k for k in range(8) if any(sum(matches(s,g+list(sub)) for s in sol)==1 for sub in combinations(nongates,k)))
        assert minimal==ch['minimal_extra_clue_count']
        challenges.append({'id':ch['id'],'solutions':len(hit),'gate_only_solutions':len(gh),'minimum_extra_clues':minimal,'path_verified':True,'clue_prefix_solution_counts':[sum(matches(s,c[:j]) for s in sol) for j in range(len(c)+1)],'path_shape_mod_rotation':list(path_shape(path_of(hit[0])))})
    published=D['challenges'][:12]
    assert len({canonical(c['clues']) for c in published})==12
    assert len({canonical(c['solution']['state']) for c in published})==12
    negative=defects(D['negative']['state'])
    assert [(n['cells'],n['type'],n['height_difference_mm']) for n in negative]==[([0,1],'height',12),([1,2],'height',12)]
    repaired=[(c,p,r+2 if p=='S' else r) for c,p,r in D['negative']['state']]
    assert key(repaired)==key(published[0]['solution']['state'])
    assert not defects(repaired)
    path_count=len({path_shape(path_of(s)) for s in sol})
    undirected_path_count=len({min(path_shape(path_of(s)),path_shape(path_of(s)[::-1])) for s in sol})
    assert path_count==6 and undirected_path_count==4
    behavior={p:{tuple(sorted(ports(p,r).items())) for r in range(4)} for p in I}
    assert all(not behavior[p]&behavior[q] for p,q in combinations(I,2))
    reflected_a=tuple(sorted(((-d)%4,h) for d,h in I['A'].items()))
    assert not any(reflected_a in b for b in behavior.values())
    report={'status':'passed','method':'Independent exhaustive row-major board constraint search; compare full sets only after enumeration. Orientations deduplicated by exact port-map equality. Connectivity independently traced from G1 to G2.', 'input_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['arden-design.json','solutions.json']},'search_nodes':nodes,'oriented_solutions':len(sol),'rotation_classes':len({canonical(s) for s in sol}),'orientation_representatives':ORIENT,'locally_matching_disconnected_boards':len(disconnected),'disconnected_example_state':disconnected[0],'accepted_disconnected_loops':0,'source_full_set_equal':True,'published_unique_setups_mod_rotation':12,'published_unique_solutions_mod_rotation':12,'directed_path_shapes_mod_rotation':path_count,'undirected_path_shapes_mod_rotation':undirected_path_count,'challenges':challenges,'negative_defects':negative,'negative_repair_verified':True,'deduction_diversity':{'published_gate_only_solution_distribution':dict(Counter(c['gate_only_solutions'] for c in challenges[:12])),'published_extra_clue_distribution':dict(Counter(c['minimum_extra_clues'] for c in challenges[:12])),'published_path_shapes':len({tuple(c['path_shape_mod_rotation']) for c in challenges[:12]}),'all_14_directed_path_shapes':len({tuple(c['path_shape_mod_rotation']) for c in challenges}),'published_undirected_path_shapes':len({min(path_shape(c['solution']['path']),path_shape(c['solution']['path'][::-1])) for c in published}),'all_14_undirected_path_shapes':undirected_path_count,'all_14_extra_clue_distribution':dict(Counter(c['minimum_extra_clues'] for c in challenges))},'limits':['Finite abstract route verification only; no CAD reconciliation or physical test.','No human difficulty or enjoyment claim.','Directed path count is 6; the inventor count 4 treats reversal as equivalent when describing only undirected path shape. Reflection is not an inventory symmetry.']}
    example={c:ports(p,r) for c,p,r in disconnected[0]}
    unseen=set(example); components=[]
    while unseen:
        component={min(unseen)}; frontier=list(component)
        while frontier:
            c=frontier.pop()
            for d in example[c]:
                n=neighbor(c,d)
                if n not in component:component.add(n);frontier.append(n)
        unseen-=component;components.append(sorted(component))
    report['disconnected_example_components']=components
    (ROOT/'independent-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Independent finite puzzle verification','','PASS: independently enumerated 56 oriented connected solutions and 14 global quarter-turn classes. The complete solution set equals the inventor output. T half-turn symmetry was inferred from port equality; mirrors are excluded because the inventory is not reflection invariant.','',f'Board-first search visited {nodes:,} partial assignments and found {len(disconnected)} locally matching disconnected boards. All accepted solutions trace G1 to G2 through all nine cells; none contains a disconnected loop.','','All 12 published clue sets are unique, and both their setups and full solutions are pairwise distinct modulo legal rotations. All advertised paths and minimum extra clue counts match exhaustive results. Both reserve challenges also have unique solutions.','','| Challenge | Gate-only solutions | Minimum extra clues | Prefix counts |','|---|---:|---:|---|']
    lines += [f"| {c['id']} | {c['gate_only_solutions']} | {c['minimum_extra_clues']} | {c['clue_prefix_solution_counts']} |" for c in challenges]
    lines += ['', f"A locally matching disconnected counterexample is {disconnected[0]}. Its separate components are {components}. Every seam matches but the full-board route rule rejects it.", '', 'The negative example has exactly two height defects: seams 0–1 and 1–2 each mismatch by 12 mm. All port directions still align. Reversing S restores the R01 solution exactly.', '',f"There are 6 directed G1-to-G2 path shapes modulo rotation, or 4 undirected shapes when reversal is identified. Structural diversity: {report['deduction_diversity']}. The set exercises gate constraints, low/high end orientation, turn handedness, and limited straight allocation. These are combinatorial properties, not measured human difficulty.",'','Reproduce: `$WORKSHOP_PYTHON design/independent_verify.py`. This script imports no originating solver. JSON binds exact design and solution bytes. CAD geometry and physical handling need separate verification.']
    (ROOT/'independent-verification.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:report[k] for k in ['status','oriented_solutions','rotation_classes','locally_matching_disconnected_boards','search_nodes','deduction_diversity']}))
if __name__=='__main__':main()
