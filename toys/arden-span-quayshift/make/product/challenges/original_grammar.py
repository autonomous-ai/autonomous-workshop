"""Deterministic abstract construction probe. NOT CAD, fit, or playtest proof.

Original footprints, authored for this concept. Cell occupancy conservatively
reserves each complete arch envelope; high arch centers admit a point ferry,
low arch centers do not. Upright quarter-turns only; no vertical stacking.
"""
import json
from pathlib import Path

N = 5
ALL = {(x, y) for x in range(N) for y in range(N)}
PARTS = {
    'A': ([(0, 0), (2, 0)], (1, 0), 'high'),
    'B': ([(0, 0), (2, 0)], (1, 0), 'high'),
    'C': ([(0, 0), (2, 0)], (1, 0), 'low'),
    'D': ([(0, 0), (1, 0), (0, 1)], None, 'solid'),
    'E': ([(0, 0), (1, 0)], None, 'solid'),
    'F': ([(0, 0), (1, 0)], None, 'solid'),
    'G': ([(0, 0)], None, 'solid'),
    'H': ([(0, 0)], None, 'solid'),
}

def orientations(points, gap):
    seen = set()
    for r in range(4):
        def turn(p):
            x, y = p
            for _ in range(r):
                x, y = -y, x
            return x, y
        pp = [turn(p) for p in points]
        gg = turn(gap) if gap is not None else None
        envelope = pp + ([gg] if gg is not None else [])
        dx, dy = min(p[0] for p in envelope), min(p[1] for p in envelope)
        pp = tuple(sorted((x-dx, y-dy) for x, y in pp))
        gg = (gg[0]-dx, gg[1]-dy) if gg is not None else None
        key = (pp, gg)
        if key not in seen:
            seen.add(key)
            yield r * 90, pp, gg

def placements(name):
    pts, gap, kind = PARTS[name]
    for deg, pp, gg in orientations(pts, gap):
        for y in range(N):
            for x in range(N):
                feet = {(px+x, py+y) for px, py in pp}
                g = (gg[0]+x, gg[1]+y) if gg is not None else None
                env = feet | ({g} if g is not None else set())
                if env <= ALL:
                    yield {'part': name, 'rotation': deg, 'origin': [x,y],
                           'feet': feet, 'gap': g, 'kind': kind, 'envelope': env}

CANDIDATES = {p: list(placements(p)) for p in PARTS}

def find_build(route):
    water = set(route)
    assert len(water) == len(route)
    assert all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a,b in zip(route,route[1:]))
    candidates = {}
    for p, values in CANDIDATES.items():
        candidates[p] = [v for v in values if not v['feet'] & water
                         and (v['kind'] != 'low' or v['gap'] not in water)
                         and (v['kind'] != 'high' or v['gap'] in water)]
    nodes = 0
    def solve(left, used, build):
        nonlocal nodes
        nodes += 1
        if not left:
            return build
        choices = {p: [v for v in candidates[p] if not used & v['envelope']] for p in left}
        p = min(left, key=lambda n: (len(choices[n]), n))
        for v in choices[p]:
            found = solve([n for n in left if n != p], used | v['envelope'], build+[v])
            if found is not None:
                return found
        return None
    build = solve(list(PARTS), set(), [])
    assert build is not None, f'No abstract witness for {route}'
    return build, nodes

def simple_paths(build, start, end, ignore_low_height=False):
    blocked = set().union(*(p['feet'] for p in build))
    if not ignore_low_height:
        blocked |= {p['gap'] for p in build if p['kind']=='low'}
    needed = {p['gap'] for p in build if p['kind']=='high'}
    found = []
    def walk(path):
        here = path[-1]
        if here == end:
            if needed <= set(path): found.append(path)
            return
        x, y = here
        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if q in ALL and q not in blocked and q not in path:
                walk(path+[q])
    if start not in blocked: walk([start])
    return found

def encode(build):
    return [{k: sorted(v) if isinstance(v,set) else v for k,v in p.items()}
            for p in sorted(build,key=lambda p:p['part'])]

def canonical_route(route):
    # Translation, reversal, rotation and reflection all quotiented.
    variants = []
    for mirror in (1,-1):
        for rot in range(4):
            points=[]
            for xx, yy in route:
                x,y=mirror*xx,yy
                for _ in range(rot): x,y=-y,x
                points.append((x,y))
            mx,my=min(x for x,y in points),min(y for x,y in points)
            normalized=tuple((x-mx,y-my) for x,y in points)
            variants.extend([normalized,normalized[::-1]])
    return min(variants)

def starter_completions(build, start, end):
    fixed = [p for p in build if p['part'] not in ('A','C')]
    used = set().union(*(p['envelope'] for p in fixed))
    winners=[]
    examined=0
    for a in CANDIDATES['A']:
        if used & a['envelope']: continue
        for c in CANDIDATES['C']:
            if (used | a['envelope']) & c['envelope']: continue
            examined+=1
            candidate=fixed+[a,c]
            paths=simple_paths(candidate,start,end)
            if paths: winners.append({'A':encode([a])[0], 'C':encode([c])[0], 'route':paths[0]})
    return {'fixed_parts': sorted(p['part'] for p in fixed),
            'loose_parts':['A','C'], 'nonoverlapping_candidates_examined':examined,
            'valid_abstract_completions':len(winners),
            'completions':winners,
            'claim':'Counts are complete only for these two loose pieces and this point-ferry model.'}

def main():
    routes = [
        [(2,0),(2,1),(2,2),(2,3),(2,4)],
        [(2,0),(2,1),(1,1),(1,2),(1,3),(2,3),(2,4)],
        [(2,0),(2,1),(1,1),(1,2),(1,3),(2,3),(3,3),(3,4),(2,4)],
    ]
    outcomes=[]
    for i,route in enumerate(routes,1):
        build,nodes=find_build(route)
        paths=simple_paths(build,route[0],route[-1])
        assert route in paths
        footprints=set().union(*(p['feet'] for p in build))
        assert len(footprints)==15
        # Swap a low arch with each high arch. Same footprints, different headroom.
        negatives=[]
        for name in ('A','B'):
            altered=[dict(p) for p in build]
            for p in altered:
                if p['part']==name: p['kind']='low'
                elif p['part']=='C': p['kind']='high'
            # Specifically test the promised witness through the lower opening.
            blocked={p['gap'] for p in altered if p['kind']=='low'}
            assert blocked & set(route)
            negatives.append({'swapped': [name,'C'], 'advertised_route_blocked':True,
                              'any_alternative_valid_trip': bool(simple_paths(altered,route[0],route[-1]))})
        outcomes.append({'id':f'witness-{i}', 'route':route,'route_cells':len(route),
                         'search_nodes_to_first_witness':nodes,
                         'paths_through_both_high_arches_in_this_build':len(paths),
                         'placements':encode(build), 'low_arch_swap_checks':negatives})
        if i==1:
            outcomes[-1]['starter_challenge']=starter_completions(build,route[0],route[-1])
    assert len({canonical_route(r) for r in routes})==3
    report={'status':'abstract-witnesses-only','board':[N,N],
            'piece_count':8,'lower_occupied_cells':15,
            'distinct_route_shapes_under_dihedral_symmetry_and_reversal':3,
            'limitations':['No CAD, surface continuity, arch profile or finite-size swept-volume checks.',
                          'No grip, print, assembly access, stability or physical playtest.',
                          'No complete challenge enumeration or difficulty/uniqueness claim.',
                          'Search reserves arch envelopes and models each high gap as a full free cell.',
                          'All parts sit at ground level; elevation comes from each rigid module.',
                          'Point ferry only; actual ferry envelope and fingers must be checked next.'],
            'witnesses':outcomes}
    Path(__file__).with_name('concept-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='witnesses'},indent=2))
    print('Witness route counts:', [p['paths_through_both_high_arches_in_this_build'] for p in outcomes])
    print('Starter valid completions:',outcomes[0]['starter_challenge']['valid_abstract_completions'])

if __name__=='__main__': main()