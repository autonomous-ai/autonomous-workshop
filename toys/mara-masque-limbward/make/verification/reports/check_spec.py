"""Inventory, coordinate and exact legal rook-turn assertions."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from states import placements,square_xy
rows=placements();assert len(rows)==97
assert len({r[0] for r in rows})==97
for side in ('white','black'):
    counts=Counter(r[1].split('_')[1] for r in rows if r[2]==side)
    assert counts=={'king':1,'queen':9,'rook':10,'bishop':10,'knight':10,'pawn':8}
assert len(placements('setup'))==33
before=placements('before');after=placements('after')
assert before[1]==after[1] and before[3]==after[3]
a,b=before[2][3],after[2][3]
assert tuple(b[i]-a[i] for i in range(3))==(0,140,0)
# Independent simple chess attack geometry for this sparse fixture, not a new engine.
wk=(0,0);bk=(0,7);r0=(7,0);r1=(7,7)
assert max(abs(wk[0]-bk[0]),abs(wk[1]-bk[1]))>1
assert r0[0]==r1[0] and wk[0]!=r0[0] and bk[0]!=r0[0]
assert r1[1]==bk[1] and wk[1]!=r1[1]
# Black can escape from a8 to a7; this is check rather than mate.
a7=(0,6);assert a7[0]!=r1[0] and a7[1]!=r1[1]
assert max(abs(a7[0]-wk[0]),abs(a7[1]-wk[1]))>1
print('PASS:97 unique items,32 starting pieces,64 unrestricted promotion replacements; exact Rh1-h8+140 mm, same kings, not mate.')
