"""Reconcile independently declared JSON specification against built geometry/source AST."""
import ast,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import cybercab_lib as c
spec=(root/'cybercab_spec.md').read_text()
blocks=re.findall(r'```json\s*(.*?)```',spec,re.S)
assert blocks,'Audit targets JSON missing'
target=json.loads(blocks[-1])
print('Spec audit targets:',json.dumps(target,sort_keys=True))
# Numerical reconciliation remains explicit and fails on an unrecorded repair.
expected={'length':180,'width':78,'height':60,'shaft_d':6,'bore_d':6.5,'wheel_r':16.5,'rear_x':34,'front_x':148,'axle_z':16.5,'journal_w':5,'spool_r':4.2,'anchor_x':134,'printed_occurrences':8,'unique_printables':6,'wall':2.4,'roof_vertical':3.6,'rail_release':4.0}
# Accept the documented target keys below; the markdown is the approved declaration.
assert target==expected,f'Spec audit rows differ: expected {expected}, actual {target}'
a=c.assembly();b=a.bounding_box()
actual={'length':b.size.X,'width':b.size.Y,'height':b.size.Z,'shaft_d':c.SHAFT_D,'bore_d':c.BORE_D,'wheel_r':c.WHEEL_R,'rear_x':c.REAR_X,'front_x':c.FRONT_X,'axle_z':c.AXLE_Z,'journal_w':c.JOURNAL_W,'spool_r':c.SPOOL_R,'anchor_x':c.BAND_ANCHOR_X,'printed_occurrences':len([p for p in a.children if p.label!='elastic']),'unique_printables':len([p for p in root.glob('part_*.step.py') if 'PRINTABLE = False' not in p.read_text() and 'PRINTABLE=False' not in p.read_text()]),'wall':c.WALL,'roof_vertical':c.BODY_PROFILE[0][1]-c.INNER_PROFILE[0][1],'rail_release':c.RAIL_RELEASE}
for key,value in expected.items():
    assert abs(actual[key]-value)<.02,f'Spec row {key}: expected {value},actual {actual[key]}'
    print(f'PASS {key}: expected {value}, actual {actual[key]}')
# Check defining operation families, not identifier presence.
tree=ast.parse((root/'cybercab_lib.py').read_text())
funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for fname,required in {'prism_xz':{'extrude','Polygon'},'body':{'prism_xz','Box','y_cylinder'},'chassis':{'Box','Cylinder','extrude','Polygon'},'complete_axle':{'y_cylinder','Cylinder'},'axle_set':{'Box','Cone'},'end_wheel':{'Box'},'window':{'prism_xz'}}.items():
    calls={n.func.id for n in ast.walk(funcs[fname]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
    assert required<=calls,f'Spec construction {fname}: expected {required},actual {calls}'
    print('PASS construction',fname,sorted(required))
for name in ['body','chassis']:
    part=getattr(c,name)();assert len(part.solids())==1,f'{name} must be one solid'
print('PASS connected principal structures')
