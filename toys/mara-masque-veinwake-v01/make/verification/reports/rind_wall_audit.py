"""Measure the written rind's narrowest top annulus from its exact wires."""
import hashlib
import json
from pathlib import Path
from build123d import import_step

project=Path(__file__).resolve().parents[1]
path=project/'part_rind.step'
shape=import_step(path)
assert shape.is_valid and len(shape.solids())==1
distances=[]
for face in shape.faces():
    box=face.bounding_box()
    if abs(box.min.Z-14)<1e-4 and abs(box.max.Z-14)<1e-4:
        outer=face.outer_wire()
        distances += [outer.distance_to(w) for w in face.wires() if not w.is_same(outer)]
assert distances and min(distances)>=3-1e-4
result={'status':'pass','step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'minimum_top_rind_mm':min(distances),'required_mm':3,'kernel_tolerance_mm':1e-4,
        'method':'Exact minimum distance between inner and outer wires of the written z14 top face. Lower outer surface expands downward and lower openings contract, so this is the limiting outer rind section.',
        'limits':'Digital geometry; no physical wall or print measurement.'}
(project/'measure/rind-wall-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
