import sys,re
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p))
import quayshift_lib as q
s=(p/'quayshift_spec.md').read_text()
for n in ['PITCH','BOARD','MARGIN','FLOOR','INSET','FERRY_HEIGHT','FERRY_RADIUS','CABIN_WIDTH','CABIN_LENGTH','PORTAL_DEPTH','PORTAL_Y','HIGH_SPRING']:
    m=re.search(r'\b'+n+r'=(\d+(?:\.\d+)?)',s)
    assert m and float(m[1])==getattr(q,n),(n,'spec/source mismatch')
assert len(list(p.glob('part_*.step.py')))==10
assert set(q.COLORS)==set('ABCDEFGH')|{'tray','ferry'}
print('PASS specification parameter ledger and ten-part inventory')
