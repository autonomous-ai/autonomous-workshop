"""Regenerate the grid cradle from the archived, exact preceding STEP edition."""
from collections import Counter
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile

from build123d import Compound, import_step
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB, Quantity_TOC_sRGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_LabelSequence
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cradle_grid import enhance_cradle, FLOOR, MARK_DEPTH

spec = importlib.util.spec_from_file_location('color_base', ROOT/'colors/colorize.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
SOURCE_HASH = 'f84eadcc777ec00f35b0ac88008dcd8c3bd34103f57a5bd3829bf32e5952b531'


def colors(doc, shape):
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    result = Counter()
    for face in shape.faces():
        c = Quantity_Color()
        assert ct.GetColor(face.wrapped, XCAFDoc_ColorSurf, c)
        vertices = tuple(sorted(tuple(round(v, 6) for v in point.center()) for point in face.vertices()))
        result[(vertices, tuple(round(v, 7) for v in (c.Red(), c.Green(), c.Blue())))] += 1
    return result


def write(doc_or_label, target):
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    assert writer.Transfer(doc_or_label, STEPControl_AsIs)
    assert writer.Write(str(target)) == IFSelect_RetDone


def main():
    with zipfile.ZipFile(ROOT/'board/previous-edition.zip') as archive:
        source_bytes = archive.read('assembled.step')
    assert hashlib.sha256(source_bytes).hexdigest() == SOURCE_HASH
    with tempfile.TemporaryDirectory(prefix='ridgeline-grid-') as scratch:
        source = Path(scratch)/'assembled.step'
        source.write_bytes(source_bytes)
        doc = base.load_document(source)
        before = base.parts(doc)
        old_assembly = import_step(source)
    original_styles = {key: colors(doc, shape) for key, (_, shape) in before.items() if key != 'cradle'}
    old = before['cradle'][1].solids()[0]
    revised = enhance_cradle(old)
    removed, added = old.cut(revised), revised.cut(old)
    assert removed and added
    assert removed.bounding_box().min.Z >= FLOOR-MARK_DEPTH-1e-6
    assert removed.bounding_box().max.Z <= FLOOR+1e-6
    assert added.bounding_box().max.Z <= FLOOR+1e-6
    assert revised.bounding_box().size.X == 174 and revised.bounding_box().size.Y == 182
    for component in old_assembly.children:
        if component.label == 'cradle':
            continue
        intersection = revised.intersect(component)
        assert not intersection or sum(s.volume for s in intersection.solids()) < 1e-5

    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    palette = json.loads((ROOT/'colors/part-palette.json').read_text())
    for key, (part_label, _) in before.items():
        color = Quantity_Color(*base.rgb(palette[key]), Quantity_TOC_sRGB)
        ct.SetColor(part_label, color, XCAFDoc_ColorGen)
        ct.SetColor(part_label, color, XCAFDoc_ColorSurf)
    label = before['cradle'][0]
    labels = TDF_LabelSequence()
    st.GetSubShapes_s(label, labels)
    for i in range(1, labels.Length()+1):
        labels.Value(i).ForgetAllAttributes(True)
    st.SetShape(label, revised.wrapped)
    TDataStd_Name.Set_s(label, TCollection_ExtendedString('cradle'))
    marked_faces = 0
    for face in revised.faces():
        bounds = face.bounding_box()
        mark = bounds.min.Z > FLOOR-MARK_DEPTH-1e-5 and bounds.min.Z < FLOOR-1e-5 and bounds.max.Z <= FLOOR+1e-5
        face_label = st.AddSubShape(label, face.wrapped)
        assert not face_label.IsNull()
        color = '#f2dfb5' if mark else '#263b40'
        ct.SetColor(face_label, Quantity_Color(*base.rgb(color), Quantity_TOC_RGB), XCAFDoc_ColorSurf)
        TDataStd_Name.Set_s(face_label, TCollection_ExtendedString('engraving' if mark else 'cradle'))
        marked_faces += int(mark)
    st.UpdateAssemblies()
    output = ROOT/'assembled.step'
    write(doc, output)
    write(label, ROOT/'parts/cradle.step')

    # Fresh STEP readback, separate from the in-memory construction.
    check_doc = base.load_document(output)
    after = base.parts(check_doc)
    new_cradle = after['cradle'][1].solids()[0]
    assert new_cradle.is_valid and len(new_cradle.solids()) == 1
    for key in original_styles:
        assert base.metrics(before[key][1])['vertices'] == base.metrics(after[key][1])['vertices']
        assert colors(check_doc, after[key][1]) == original_styles[key]
    new_assembly = import_step(output)
    assert len(new_assembly.solids()) == 10
    for old_part, new_part in zip(old_assembly.children, new_assembly.children, strict=True):
        assert old_part.label == new_part.label
        if old_part.label != 'cradle':
            assert base.metrics(old_part)['vertices'] == base.metrics(new_part)['vertices']
    # Probe the engraved floor at every cell's digit and at all four grid lines.
    digit_probes = [(0, 5), (0, 0), (0, 5), (0, 5), (0, 0), (0, 5), (0, 5), (0, 5), (0, 5)]
    for cell, (dx, dy) in enumerate(digit_probes):
        x, y = 56*(cell%3-1)+dx, 56*(1-cell//3)+dy
        assert not new_cradle.is_inside((x, y, 3.9))
        assert new_cradle.is_inside((x, y, 3.3))
    for x, y in [(-28, 10), (28, 10), (10, -28), (10, 28)]:
        assert not new_cradle.is_inside((x, y, 3.9))
        assert new_cradle.is_inside((x, y, 3.3))
    report = {
        'source_sha256': SOURCE_HASH, 'assembly_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'cradle_sha256': hashlib.sha256((ROOT/'parts/cradle.step').read_bytes()).hexdigest(),
        'solids': 10, 'cradle_valid': True, 'cradle_faces': len(new_cradle.faces()),
        'engraved_faces': marked_faces, 'minimum_floor_mm': FLOOR-MARK_DEPTH,
        'cradle_bbox_mm': list(new_cradle.bounding_box().size),
        'assembly_bbox_mm': list(new_assembly.bounding_box().size),
        'added_volume_mm3': sum(s.volume for s in added.solids()),
        'removed_volume_mm3': sum(s.volume for s in removed.solids()),
        'nine_modules_geometry_and_face_colors_unchanged': True,
        'assembly_placements_unchanged': True, 'nine_cell_numbers_probed': True,
        'four_grid_lines_probed': True, 'no_added_volume_above_tile_support_plane': True,
        'no_module_cradle_intersection': True, 'physical_testing': 'not performed',
    }
    (ROOT/'board/grid-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
