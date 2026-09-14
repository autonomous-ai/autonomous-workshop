import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import quayshift_lib as q
from build123d import *
def v(s):return 0 if s is None else sum(x.volume for x in s) if isinstance(s,list) else s.volume
for n in 'ABCDEFGH':
    s=q.part(n)
    assert len(s.solids())==1
    assert any(f.geom_type==GeomType.CYLINDER for f in s.faces()),(n,'missing recessed arched facade')
    assert s.bounding_box().max.Z>24
for n in 'AB':
    s=q.part(n);probe=q.box(35,19.6,0,26,12,26)
    assert v(s.intersect(probe))<1e-6,(n,'high aperture obstruction')
assert v(q.part('C').intersect(q.box(43,20,20,10,10,5)))>1
assert q.part('G').bounding_box().max.Z==84
assert v(q.part('D').intersect(q.box(32,32,0,32,32,90)))<1e-6
assert len(q.assemble().children)==10
print('PASS two open high portals, obstructing low gate, L void, recessed facades, varied skyline, ten occurrences')
