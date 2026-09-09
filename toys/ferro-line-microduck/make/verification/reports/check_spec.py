"""Reconcile the local dimensional contract with evaluated source and its AST.
No mesh sampling; actual assembly bounds and solids are measured once.
"""
from pathlib import Path
import sys,json,re,ast
PROJECT=Path(__file__).resolve().parents[1]
# CAD dependencies are provided by the verifier/runtime, independent of host workspace.
sys.path.insert(0,str(PROJECT))
import duck_lib as f
import drive_lib as d

def contract():
    text=(PROJECT/'microduck_spec.md').read_text()
    return json.loads(re.search(r'```json\n(.*?)\n```',text,re.S).group(1))

def near(row,actual,expected,tol=1e-5):
    assert abs(actual-expected)<=tol, f'{row}: expected {expected} ± {tol}, actual {actual}'

def main():
    c=contract();assert c['likeness_floor']==0.90, 'likeness floor must equal 0.90'
    for module,rows in c['parameters'].items():
        for key,val in rows.items(): near(f'parameter {module}.{key}',getattr({'duck_lib':f,'drive_lib':d}[module],key),val)
    for name,points in c['observed_contours'].items():
        assert [list(p) for p in getattr(f,name)]==points,f'observed contour {name}: source coordinates differ from reviewed reference trace'
    trees={n:ast.parse((PROJECT/(n+'.py')).read_text()) for n in ['duck_lib','drive_lib']}
    for row in c['construction']:
        tree=trees[row['module']]
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==row['function'])
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
        assert set(row['calls'])<=calls, f"construction {row['feature']}: expected calls {row['calls']}, actual {sorted(calls)}"
        ops={type(n.op).__name__ for n in ast.walk(fn) if isinstance(n,(ast.BinOp,ast.AugAssign))}
        assert set(row.get('operators',[]))<=ops, f"construction {row['feature']}: expected operations {row.get('operators')}, actual {sorted(ops)}"
    a=f.build_assembly();parts={p.label:p for p in a.children}
    assert sorted(parts)==sorted(c['labels']),f"assembly labels: expected {c['labels']}, actual {list(parts)}"
    assert len(parts)==c['printed_parts'],f"printed count expected {c['printed_parts']}, actual {len(parts)}"
    for name,p in parts.items():
        assert p.is_valid and len(p.solids())==1, f'{name}: expected one valid solid, actual {len(p.solids())}'
    bb=a.bounding_box()
    for end in ['min','max']:
        for i,axis in enumerate('XYZ'):
            near(f'overall bbox {end}.{axis}',tuple(getattr(bb,end))[i],c['overall_bbox'][end][i],c['overall_bbox']['tolerance_mm'])
    # Coordinate convention is a real conversion, not only a keyword claim.
    near('scale: 560 observed pixels -> chosen 180 mm',f.PIXEL_SCALE*560,180)
    near('face insert seam',f.FACE_GAP,0.2)
    print(json.dumps({'ok':True,'spec':'microduck_spec.md','printed_parts':len(parts),'bbox_mm':{'min':list(bb.min),'max':list(bb.max)},'parameter_rows':sum(len(v) for v in c['parameters'].values()),'construction_rows':len(c['construction']),'likeness_floor':c['likeness_floor']}))
if __name__=='__main__':
    try: main()
    except (AssertionError,StopIteration,KeyError) as e: print('FAIL spec:',e);sys.exit(1)
