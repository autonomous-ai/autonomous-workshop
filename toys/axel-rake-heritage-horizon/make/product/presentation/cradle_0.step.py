"""Exact sample 0/20 from declared cradle withdrawal."""
from pathlib import Path
import sys,json
from build123d import Pos
from cadgen.assembly import AssemblyHelper
project=Path(__file__).resolve().parents[1]/"heritage"
sys.path.insert(0,str(project))
from assemblies.product import build
PRINTABLE=False
def gen_step():
    manifest=json.loads((project/"measure/motion.json").read_text())
    condition=next(c for c in manifest["conditions"] if c["id"]=="remove-cradle")
    inputs=condition["inputs"]
    delta=[v*0/inputs["steps"] for v in inputs["translation"]]
    result=AssemblyHelper("cradle_state_0")
    for child in build().children:
        placed=Pos(*delta)*child if child.label==inputs["moving_part"] else child
        result.add(placed,child.label,color=child.color)
    return result.compound()
