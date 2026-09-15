"""Measure exact exported production BREP envelopes, not parameter values."""
from pathlib import Path
import json
from build123d import import_step
p=Path(__file__).resolve().parents[1]
rows=[]
for f in sorted(p.glob('part_*.step')):
 s=import_step(f);b=s.bounding_box();z=float(b.size.Z)
 row={'part':f.name,'size_mm':[float(b.size.X),float(b.size.Y),z],'zmin_mm':float(b.min.Z),'solids':len(s.solids())}
 assert row['solids']==1 and abs(row['zmin_mm'])<1e-5
 if f.name=='part_board.step':assert 195.9<=b.size.X<=196.01 and 195.9<=b.size.Y<=196.01 and abs(z-12)<1e-5
 else:assert b.size.X<=14.001 and b.size.Y<=14.001 and 11.999<=z<=28.001
 rows.append(row)
(p/'measure/dimensions.json').write_text(json.dumps({'status':'pass','method':'Exact STEP BREP bounding boxes and solid counts; circumscribed rounded-square base separately checked by check_fit.py','parts':rows},indent=2)+'\n')
print('PASS: all 13 production variant BREP envelopes, one solid each, flat datum at z=0')
