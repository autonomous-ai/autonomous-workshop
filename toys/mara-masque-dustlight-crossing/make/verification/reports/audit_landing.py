"""Measure flat seating volumes in the written panel STEP BReps."""
from pathlib import Path
import sys,json,hashlib
from build123d import import_step, Box, Pos, Align
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dustlight_lib import PANEL_BOUNDS, PITCH, BORDER, SURFACE

cad=Path(__file__).resolve().parents[1]
names=('southwest','southeast','northwest','northeast')
rows=[]
for i,(x0,y0,x1,y1) in enumerate(PANEL_BOUNDS):
    path=cad/f'part_{names[i]}_panel.step';panel=import_step(path)
    for row in range(9):
        for col in range(7):
            x=BORDER+PITCH*(col+.5);y=BORDER+PITCH*(row+.5)
            if not(x0<x<x1 and y0<y<y1):continue
            probe=Pos(x-x0,y-y0,SURFACE-.1)*Box(24,24,.1,align=(Align.CENTER,Align.CENTER,Align.MIN))
            hit=panel.intersect(probe);v=sum(s.volume for s in hit) if isinstance(hit,list) else (hit.volume if hit is not None else 0)
            assert abs(v-57.6)<1e-5,(col,row,v)
            rows.append(dict(cell=f'{chr(97+col)}{row+1}',top_slab_volume_mm3=round(v,6)))
assert len(rows)==63
out=dict(status='pass',method='BRep intersection of each written STEP with a 24 x 24 x 0.1 mm slab immediately below Z5.',expected_volume_mm3=57.6,cells=rows,source_sha256={f'part_{n}_panel.step':hashlib.sha256((cad/f'part_{n}_panel.step').read_bytes()).hexdigest() for n in names},limitations='Digital flatness and geometry only; printed warping and tactile stability untested.')
(cad/'measure/landing-audit.json').write_text(json.dumps(out,indent=2))
print('PASS: all 63 landing centers contain the complete 24 x 24 mm flat top slab in written STEP geometry.')
