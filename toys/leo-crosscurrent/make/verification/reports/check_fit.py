"""Independent STEP fit probes; no physical friction/print claims."""
from pathlib import Path
from build123d import import_step, Pos
root=Path(__file__).resolve().parents[1]
parts={name:import_step(root/f'part_{name}.step') for name in ('shore','inner','outer','boat_1','boat_2','boat_3','boat_4','boat_5')}
def overlap(a,b):
    result=a.intersect(b)
    return 0 if result is None else (abs(result.volume) if hasattr(result, "volume") else sum(abs(x.volume) for x in result))
def check(label,condition):
    print(('PASS ' if condition else 'FAIL ')+label,flush=True)
    assert condition,label
for name,part in parts.items():
    box=part.bounding_box()
    check(name+' is one valid solid',len(part.solids())==1 and part.is_valid)
    check(name+' sits on bed and fits 220 mm',abs(box.min.Z)<0.01 and box.size.X<=220 and box.size.Y<=220)
shore=parts['shore']
for name,diameter in [('inner',84),('outer',160)]:
    part=parts[name]
    check(name+' diameter matches independent drawing',abs(part.bounding_box().size.X-diameter)<0.01)
    check(name+' centered seat clear',overlap(shore,Pos(0,0,4)*part)<0.001)
    check(name+' 0.45 mm lateral play clear',overlap(shore,Pos(0.45,0,4)*part)<0.001)
    check(name+' guide stops 0.60 mm offset',overlap(shore,Pos(0.60,0,4)*part)>0.001)
    check(name+' vertical installation open',overlap(shore,Pos(0,0,16)*part)<0.001)
boat=parts['boat_1']
check('counter 20 mm by 5.2 mm drawing',abs(boat.bounding_box().size.X-20)<0.01 and abs(boat.bounding_box().size.Z-5.2)<0.01)
check('berth accepts counter',overlap(parts['inner'],Pos(28,0,3)*boat)<0.001)
check('berth wall arrests 3 mm lateral displacement',overlap(parts['inner'],Pos(31,0,3)*boat)>0.001)
check('nest seats at 3.6 mm pitch',overlap(boat,Pos(0,0,3.6)*parts['boat_2'])<0.001)
check('nest cannot sink another 0.1 mm',overlap(boat,Pos(0,0,3.5)*parts['boat_2'])>0.001)
check('nest lifts out freely',overlap(boat,Pos(0,0,6)*parts['boat_2'])<0.001)
check('ten-counter stack fits 45 mm assembled envelope',7+9*3.6+boat.bounding_box().size.Z<=45)
print('Assembly order: shore flat; carriers lower vertically; counters lower into berths; subsequent counters nest. No captive joints, hardware or friction-dependent retention.')
