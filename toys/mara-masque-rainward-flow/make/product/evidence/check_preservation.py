"""Exact source preservation audit against immutable baseline; no CAD construction."""
from pathlib import Path
import ast, hashlib, json, zipfile
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'STAGE.json').exists())
PRODUCT=Path(__file__).resolve().parents[1]
archive=ROOT/'revision-source.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='8c281a08a6425800675acb75648a8e227b0bb509856d70aa0d283d0b448c8566'
with zipfile.ZipFile(archive) as z:
    old=ast.parse(z.read('make/source/cad/rainward_lib.py').decode())
new=ast.parse((PRODUCT/'cad/rainward_lib.py').read_text())
def functions(tree):return {x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,ast.FunctionDef)}
a,b=functions(old),functions(new)
unchanged=['xy','theta','cup','piece_poses']
for name in unchanged: assert a[name]==b[name],name
# piece_poses retains original inventory, setup and all point-state transitions;
# its revised BAR_HIT_R datum is independently checked for the80mm displacement.
report={'status':'PASS','snapshot_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'unchanged_functions':unchanged,'scope':'Exact unchanged source functions; dimensions, revised geometry and rules trace checked separately.'}
(PRODUCT/'evidence/preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
