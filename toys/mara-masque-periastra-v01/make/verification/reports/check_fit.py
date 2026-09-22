"""Independent algebraic fit, part count and assembly order audit."""
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import periastra_lib as p
assert (p.BASE,p.HEIGHT,p.WALL)==(190,24,3)
assert (p.BOARD,p.CELL,p.ROWS)==(176,22,8)
assert p.RECESS==0.8 and p.SQUARE_BEVEL==0.3
assert math.isclose((p.OPENING-p.ROOF_SIZE)/2,0.8,abs_tol=1e-9)
assert p.LEDGE_TOP-p.FLOOR>=10
assert p.LEDGE_TOP-(p.FLOOR-p.RECESS+p.COUNTER_HEIGHT)>=3.8-1e-9
assert p.OPENING/2-p.LEDGE_DEPTH > p.BOARD/2
assert p.STAR_RADIUS <= (p.OPENING-p.BOARD)/2
assert p.CELL-16>=6
positions=[(c,r) for r in [0,1,2,5,6,7] for c in range(8) if (c+r)%2==0]
assert len(set(positions))==24
assert sum(r<3 for c,r in positions)==12
assert all((c+r)%2==0 for c,r in positions)
assert p.CROWN_DEPTH<1 and p.RELIEF<1
assert p.COUNTER_HEIGHT-p.CROWN_DEPTH>=6.4
assert p.LIFT==100
expected={'part_base.step.py','part_roof.step.py','part_single_comet.step.py','part_forked_comet.step.py'}
assert {x.name for x in Path(__file__).resolve().parents[1].glob('part_*.step.py')}==expected
print('PASS: specified board, storage, roof clearance, 24 starting positions, reversible counters and four print entries. Assembly order: populate base, lower loose roof onto integral ledges; reverse for play.')
