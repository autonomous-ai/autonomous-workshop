#!/usr/bin/env python3
"""components.json -> the CadQuery file layout, written by machine.

The contract already fixes every id, bounding box and tolerance. text2cad let
the BUILD agent invent the layout each run, which spent turns on directory
structure and let it drift from the spec it was handed. Here the numbers become
constants before any agent starts, so a build can only fill in geometry.

    ./scaffold.py <out_dir>
"""
import json
import sys
from pathlib import Path

HEADER = '''"""{id} - {role}

Generated from components.json. The constants below are the CONTRACT: phase 1
committed to them and gate/fit check against them. Change one only by changing
components.json, never here.
"""
import cadquery as cq

QTY = {qty}
CLASS = "{cls}"
TOL = {tol}                 # mm of clearance this part's job survives
BBOX = ({bx}, {by}, {bz})   # mm, target envelope
MATES = {mates}
DUTY = """{duty}"""


def build():
    """Return a cadquery Workplane for this part."""
    raise NotImplementedError("phase 2 build fills this in")
'''


def load(out_dir: Path) -> list:
    data = json.loads((out_dir / "components.json").read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("components", [])


def generate(out_dir: Path) -> list:
    comps = load(out_dir)
    parts = out_dir / "parts"
    parts.mkdir(exist_ok=True)
    (parts / "__init__.py").write_text("", encoding="utf-8")
    written = []
    for c in comps:
        f = parts / f"{c['id']}.py"
        if f.exists():                       # never clobber a real build
            continue
        bb = c["target_bbox_mm"]
        f.write_text(HEADER.format(
            id=c["id"], role=c["role"].replace('"', "'"), qty=c["qty"],
            cls=c["class"], tol=c["tolerance_mm"],
            bx=bb[0], by=bb[1], bz=bb[2],
            mates=json.dumps(c.get("mates_with") or []),
            duty=c["duty"].replace('"""', "'''")), encoding="utf-8")
        written.append(c["id"])
    index = {c["id"]: {"qty": c["qty"], "class": c["class"],
                       "tol": c["tolerance_mm"], "bbox": c["target_bbox_mm"],
                       "mates": c.get("mates_with") or []} for c in comps}
    (out_dir / "parts_index.json").write_text(json.dumps(index, indent=2),
                                              encoding="utf-8")
    return written


if __name__ == "__main__":
    w = generate(Path(sys.argv[1]).resolve())
    print(f"scaffold: {len(w)} stub(s) written: {', '.join(w) or '(none new)'}")
