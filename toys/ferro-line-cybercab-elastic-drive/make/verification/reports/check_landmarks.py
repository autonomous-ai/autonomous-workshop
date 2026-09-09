"""Read topology and positioned solids; no search through sampled space."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cybercab_lib as c
from build123d import GeomType,Compound

def check(label,actual,expected,tol=.02):
    assert abs(actual-expected)<=tol, f'{label}: expected {expected}, actual {actual}'
    print(f'PASS {label}: {actual:g} (target {expected:g})')
a=c.assembly(); bb=a.bounding_box()
for key,actual,expected in [('overall length',bb.size.X,180),('overall width',bb.size.Y,78),('roof height',bb.max.Z,60),('ground wheels',bb.min.Z,0)]:check(key,actual,expected)
children={x.label:x for x in a.children}
assert {'body','chassis','rear_wheelset','front_wheelset','left_window','right_window'}<=set(children),f'missing visual occurrence: {list(children)}'
for name,x in [('rear_wheelset',34),('front_wheelset',148)]:
    p=Compound(children=[children[name],children[name.replace('_wheelset','_rightwheel')]]); b=p.bounding_box()
    check(name+' centre X',b.center().X,x); check(name+' centre Z',b.center().Z,16.5)
    check(name+' diameter',b.size.Z,33);check(name+' width',b.size.Y,77)
    circles=[e for e in p.edges() if e.geom_type==GeomType.CIRCLE and abs(e.radius-16.5)<.01]
    assert len(circles)==4,f'{name} disc rims expected4,actual{len(circles)}'
    print('PASS',name,'four tyre rim circles')
for name,y in [('left_window',-38.3),('right_window',38.3)]:
    b=children[name].bounding_box();check(name+' station',b.center().Y,y);check(name+' insert thickness',b.size.Y,1.4)
    check(name+' swept glazing span',b.size.X,80);check(name+' upper roof offset',b.max.Z,55.8)
b=c.body(); check('one connected shell',len(b.solids()),1)
# Actual shell topology must retain the characteristic stations from the observed profile.
verts=[v.center() for v in b.vertices()]
for x,z in [(0,39),(45,52),(82,59.5),(97,60),(140,42),(180,25)]:
    assert any(abs(v.X-x)<.01 and abs(v.Z-z)<.01 and abs(abs(v.Y)-39)<.01 for v in verts),f'roof landmark ({x},{z}) omitted'
    print(f'PASS roof landmark ({x},{z})')
# The exact cylindrical axle journal surfaces survive the open-top subtraction.
faces=[f for f in c.chassis().faces() if f.geom_type==GeomType.CYLINDER]
assert len(faces)>=4,f'journal cylinders missing: {len(faces)}'
print('PASS journal cylinder topology',len(faces))
