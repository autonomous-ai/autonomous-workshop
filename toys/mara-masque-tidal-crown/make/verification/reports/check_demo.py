"""Exact three-piece chess audit; not a full chess engine or human playtest."""
import json
from pathlib import Path

def sq(name):
    return (ord(name[0])-97, int(name[1])-1)

def king_attacks(a,b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1])) == 1

def queen_attacks(a,b,occupied):
    dx,dy=b[0]-a[0],b[1]-a[1]
    if not (dx==0 or dy==0 or abs(dx)==abs(dy)) or a==b:
        return False
    sx=(dx>0)-(dx<0); sy=(dy>0)-(dy<0)
    p=(a[0]+sx,a[1]+sy)
    while p!=b:
        if p in occupied:
            return False
        p=(p[0]+sx,p[1]+sy)
    return True

wk,bk,q0,q1=map(sq,['f6','f8','h1','h8'])
assert not king_attacks(wk,bk)
assert not queen_attacks(q0,bk,{wk,bk,q0})
assert queen_attacks(q0,q1,{wk,bk,q0})
assert queen_attacks(q1,bk,{wk,bk,q1})
escapes=[]; response_evidence=[]
for dx in [-1,0,1]:
    for dy in [-1,0,1]:
        if dx==dy==0: continue
        p=(bk[0]+dx,bk[1]+dy)
        if not (0<=p[0]<8 and 0<=p[1]<8): continue
        by_king=king_attacks(wk,p)
        by_queen=p!=q1 and queen_attacks(q1,p,{wk,p,q1})
        legal=p!=wk and not by_king and not by_queen
        name=chr(p[0]+97)+str(p[1]+1)
        response_evidence.append(dict(square=name,attacked_by_white_king=by_king,attacked_by_white_queen=by_queen,legal=legal))
        if legal: escapes.append(name)
assert not escapes
result={'status':'pass','before':'5k2/8/5K2/8/8/8/8/7Q w - - 0 1','after':'5k1Q/8/5K2/8/8/8/8/8 b - - 1 1','move':'Qh8#','queen_displacement_mm':18*(q1[1]-q0[1]),'black_king_responses':response_evidence,'limitations':'Three-piece move legality and mate only; not full rules, human usability or physical testing.'}
if __name__=='__main__':
    out=Path(__file__).with_name('demo-audit.json')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
