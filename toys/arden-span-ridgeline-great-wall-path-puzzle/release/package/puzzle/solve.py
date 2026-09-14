import json,itertools
from pathlib import Path
INV={'A':{0:0,1:1},'B':{0:1,1:1},'C':{0:1,1:2},'D':{0:2,1:1},'S':{0:0,2:1},'T':{0:1,2:1},'U':{0:1,2:2},'G1':{0:1},'G2':{0:2}}
DIR=[(-1,0),(0,1),(1,0),(0,-1)]
def side(a,b):
 r,c=divmod(a,3);s,t=divmod(b,3);return DIR.index((s-r,t-c))
def neighbors(a):
 r,c=divmod(a,3)
 return [3*(r+dr)+c+dc for dr,dc in DIR if 0<=r+dr<3 and 0<=c+dc<3]
def rotate_cell(c):
 r,c=divmod(c,3);return 3*c+2-r
def rotate(state):return tuple(sorted((rotate_cell(c),p,(r+1)%(2 if p in EQUAL_STRAIGHTS else 4)) for c,p,r in state))
EQUAL_STRAIGHTS={'T'}
def canon(state):
 states=[tuple(sorted(state))]
 for _ in range(3):states.append(rotate(states[-1]))
 return min(states)
def solve(inv):
 sols=[]
 def walk(path):
  if len(path)==9:
   dirs=[(side(path[i],path[i-1]),side(path[i],path[i+1])) for i in range(1,8)]
   if sum((a-b)%2==0 for a,b in dirs)!=sum(set(v)=={0,2} for v in inv.values()):return
   def fit(i,h,remaining,state):
    if i==8:
     if h==2:sols.append({'path':path[:],'state':sorted(state+[(path[8],'G2',side(path[8],path[7]))])})
     return
    a,b=dirs[i-1]
    for p in sorted(remaining):
     for rot in range(2 if set(inv[p])=={0,2} and len(set(inv[p].values()))==1 else 4):
      ports={(d+rot)%4:v for d,v in inv[p].items()}
      if set(ports)=={a,b} and ports[a]==h:fit(i+1,ports[b],remaining-{p},state+[(path[i],p,rot)])
   fit(1,1,set(inv)-{'G1','G2'},[(path[0],'G1',side(path[0],path[1]))])
  else:
   for b in neighbors(path[-1]):
    if b not in path:walk(path+[b])
 for a in range(9):walk([a])
 return sols
if __name__=='__main__':
 # The standalone entry point reproduces the shipped inventory and evidence.
 import runpy
 runpy.run_path(str(Path(__file__).resolve().with_name('finalize_design.py')), run_name='__main__')
