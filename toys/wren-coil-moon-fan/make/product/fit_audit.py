"""Algebraic fit/print audit; solid checks are owned by the CAD verifier."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'cad'))
import moon_lib as m
assert abs((m.BORE_R-m.PIN_R)-0.2)<1e-8
assert abs((m.LEAF_Z-m.BODY_H)-0.4)<1e-8
assert m.POCKET_X-m.INLAY_X == m.POCKET_Y-m.INLAY_Y == 1.0
assert abs(m.POCKET_D-m.INLAY_Z-0.3)<1e-8
assert m.WINDOW==1 and m.SWING==75
assert m.KEEP_X>m.POCKET_X and m.KEEP_Y>m.POCKET_Y
assert m.PEG_R==1.5 and m.PEG_ORBIT==8
readme=(Path(__file__).parent/'cad/README.md').read_text()
for name in ['leaf_axis','bearing_datum','stop peg','cover','pivot']:
    assert name in readme,name
assert 'Assembly: align' in readme and 'Insert the pivot' in readme
print('PASS: common pivot/bore dimensions, clearance applied once, pocket allowances, named connectors and assembly order; solid, swept and print gates are separate.')
