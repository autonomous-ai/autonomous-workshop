"""Apply RIDGELINE's editable palette to exact STEP faces, without remodeling.

Run with Workshop's build123d/OCP Python. The source STEP is hash-bound; all
styles are written to a new STEP and independently read back before delivery.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys

from build123d import Compound, Vector, import_step
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "geometry"))
from ridgeline_lib import PORTS, LEVELS, BASE, ridge_terrain

SOURCE_HASH = "17bd5ad6f7c898bb0a6e1eda5e5c92b7fb24b1f355c01f40972616f66a2394a2"
SOURCE = ROOT / "input/assembled.step"
OUTPUT = ROOT / "ridgeline-colored.step"
PALETTE = json.loads((ROOT / "palette.json").read_text())


def load_document(path):
    doc = TDocStd_Document(TCollection_ExtendedString("RIDGELINE"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    assert reader.ReadFile(str(path)) == IFSelect_RetDone
    assert reader.Transfer(doc)
    return doc


def parts(doc):
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = TDF_LabelSequence()
    tool.GetShapes(labels)
    result = {}
    for index in range(1, labels.Length() + 1):
        label = labels.Value(index)
        if tool.IsAssembly_s(label):
            continue
        name = TDataStd_Name()
        assert label.FindAttribute(TDataStd_Name.GetID_s(), name)
        key = name.Get().ToExtString()
        assert key not in result
        result[key] = (label, Compound(tool.GetShape_s(label)))
    assert set(result) == {key.lower() for key in PORTS} | {"cradle"}
    return result


def face_role(face, key, terrain_shell, high):
    if key == "cradle":
        return "cradle"
    p = face.center()
    bounds = face.bounding_box()
    normal = face.normal_at()
    # The original modules use local coordinates, including these raised IDs.
    if -28 < p.X < -14 and -27 < p.Y < -17 and p.Z > BASE + 1e-5 and p.Z < 10.1:
        return "label_text" if p.Z > 8.80001 else "label_plaque"
    if bounds.max.Z <= BASE + 1e-5:
        return "tile_base"
    # Match the source terrain surface, not a guessed screen-space selection.
    if terrain_shell.distance_to(Vector(p.X, p.Y, p.Z)) < 1e-5:
        return "terrain_upper" if p.Z > BASE + (high - 12 - BASE) * .58 else "terrain"
    if key in ("g1", "g2") and bounds.min.Z >= high - 1e-5 and normal.Z < .99:
        return "gate_" + key
    if normal.Z > .99 and p.Z >= LEVELS[0] - 1e-5:
        return "walkway"
    return "stone"


def rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5))


def metrics(shape):
    bounds = shape.bounding_box()
    return {
        "solids": len(shape.solids()), "faces": len(shape.faces()),
        "volume_mm3": sum(s.volume for s in shape.solids()), "area_mm2": shape.area,
        "bbox": list(bounds.min) + list(bounds.max), "valid": shape.is_valid,
        "vertices": sorted(set(tuple(round(v, 7) for v in vertex.center()) for vertex in shape.vertices())),
    }


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
    doc = load_document(SOURCE)
    original_parts = parts(doc)
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    expected = {}
    roles = {}
    for key, (label, shape) in original_parts.items():
        high = 0 if key == "cradle" else LEVELS[max(PORTS[key.upper()].values())]
        terrain = None if key == "cradle" else ridge_terrain(high, PORTS[key.upper()]).shells()[0]
        counts = Counter()
        expected[key] = []
        for face in shape.faces():
            role = face_role(face, key, terrain, high)
            color_hex = PALETTE[role]
            face_label = shape_tool.AddSubShape(label, face.wrapped)
            assert not face_label.IsNull()
            color_tool.SetColor(face_label, Quantity_Color(*rgb(color_hex), Quantity_TOC_RGB), XCAFDoc_ColorSurf)
            TDataStd_Name.Set_s(face_label, TCollection_ExtendedString(role))
            expected[key].append(color_hex)
            counts[role] += 1
        roles[key] = dict(counts)
        print(json.dumps({"part": key, "faces": len(expected[key]), "roles": roles[key]}), flush=True)
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    assert writer.Transfer(doc, STEPControl_AsIs)
    assert writer.Write(str(OUTPUT)) == IFSelect_RetDone

    # Verify the exported bytes through a fresh reader: all faces have colors.
    reread = load_document(OUTPUT)
    output_parts = parts(reread)
    reread_color_tool = XCAFDoc_DocumentTool.ColorTool_s(reread.Main())
    audit = {}
    for key, (_, shape) in output_parts.items():
        before = metrics(original_parts[key][1])
        after = metrics(shape)
        assert after["valid"] and after["solids"] == before["solids"] == 1
        assert before["faces"] == after["faces"]
        # OCCT's numerical surface integration varies slightly after STEP
        # roundtrip (observed <0.0015 mm2 on these ~10000 mm2 parts).
        assert before["volume_mm3"] > 0
        assert abs(before["volume_mm3"] - after["volume_mm3"]) < before["volume_mm3"] * 1e-6
        assert abs(before["area_mm2"] - after["area_mm2"]) < before["area_mm2"] * 1e-6
        assert max(abs(a-b) for a,b in zip(before["bbox"], after["bbox"])) < 1e-6
        assert before["vertices"] == after["vertices"]
        # Check both directional solid differences, not only scalar metrics.
        old_solid = original_parts[key][1].solids()[0]
        new_solid = shape.solids()[0]
        removed = old_solid.cut(new_solid)
        added = new_solid.cut(old_solid)
        removed_volume = sum(s.volume for s in removed.solids()) if removed else 0.0
        added_volume = sum(s.volume for s in added.solids()) if added else 0.0
        assert removed_volume < 1e-5 and added_volume < 1e-5
        actual_colors = []
        for face in shape.faces():
            color = Quantity_Color()
            assert reread_color_tool.GetColor(face.wrapped, XCAFDoc_ColorSurf, color)
            channels = (color.Red(), color.Green(), color.Blue())
            actual_colors.append('#' + ''.join(f'{round(c*255):02x}' for c in channels))
        assert Counter(actual_colors) == Counter(expected[key]), (key, Counter(actual_colors), Counter(expected[key]))
        audit[key] = {k:v for k,v in after.items() if k != "vertices"}
        audit[key]["roles"] = roles[key]
        audit[key]["colors_read_back"] = dict(Counter(actual_colors))
        audit[key]["geometry_matches_source"] = True
        audit[key]["added_volume_mm3"] = added_volume
        audit[key]["removed_volume_mm3"] = removed_volume
    # Assembly positions must also survive, not just individual prototypes.
    original_assembly = import_step(SOURCE)
    output_assembly = import_step(OUTPUT)
    for old, new in zip(original_assembly.children, output_assembly.children, strict=True):
        assert old.label == new.label
        assert metrics(old)["vertices"] == metrics(new)["vertices"]
    report = {
        "status": "color-edit-verified-not-pipeline-sealed", "source_sha256": SOURCE_HASH,
        "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "palette": PALETTE, "parts": audit,
        "geometry_unchanged": True, "assembly_placements_unchanged": True,
        "face_colors_read_back": True,
        "physical_testing": "not-performed", "published": False,
    }
    (ROOT / "color-audit.json").write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({"ok": True, "output": str(OUTPUT), "sha256": report["output_sha256"]}), flush=True)


if __name__ == "__main__":
    main()
