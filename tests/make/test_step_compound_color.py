"""Uniform compound appearance survives STEP readers that inspect face styles."""
import copy
import importlib
import io
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Box, Color, Compound, Cylinder, Location, import_step
from OCP.TDF import TDF_LabelSequence
from OCP.TopAbs import TopAbs_FACE
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


def scene(*, shared=False, inherited=False, different=False, uncolored=False, solid=False):
    prototype = (Box(3, 4, 2).solid() if solid else
                 Compound([Box(3, 4, 2), Cylinder(.7, 2).translate((5, 0, 0))]))
    children = []
    for index in range(3):
        leaf = copy.copy(prototype) if shared else copy.deepcopy(prototype)
        leaf.label = "piece"  # Unique occurrence names belong to the parent nodes.
        leaf.location = Location((1, -2, 3), (11, 17, 23))
        color = Color(.8, .1, .2, .35) if not different or index % 2 == 0 else Color(.2, .8, .1, .75)
        if not inherited and not uncolored:
            leaf.color = color
        group = Compound(children=[leaf], label=f"unit_{index}")
        group.location = Location((index * 13, index % 2 * 7, 0), (index * 7, 19, index * 31))
        if inherited and not uncolored:
            group.color = color
        children.append(group)
    return Compound(children=[Compound(children=children, label="nested")], label="assembly")


class CompoundStepColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = runpy.run_path(str(SCRIPTS / "render_product"))
        cls.product["_runtime_paths"]()
        cls.exporter = importlib.import_module("cadgen.step_export")
        cls.leaves = staticmethod(importlib.import_module("render_assembly").colored_leaves)

    def write(self, shape, path):
        self.exporter.export_build123d_step_file(shape, path, text_to_cad_entry_kind="assembly")

    def assert_roundtrip(self, shape, path):
        nodes = [shape, *shape.descendants]
        before = [(id(node.parent), node.wrapped.Located(node.wrapped.Location()), node.label,
                   tuple(node.color) if node.color is not None else None) for node in nodes]
        expected = list(self.leaves(shape))
        self.write(shape, path)
        loaded = import_step(path)
        actual = list(self.leaves(loaded))
        self.assertEqual(len(actual), len(expected))
        for (part, color), (source, source_color) in zip(actual, expected):
            if source_color is None:
                self.assertIsNone(color)
            else:
                self.assertIsNotNone(color)
                np.testing.assert_allclose(tuple(color), tuple(source_color), rtol=0, atol=1e-7)
            self.assertEqual(len(part.solids()), len(source.solids()))
            self.assertAlmostEqual(part.volume, source.volume, places=8)
            for bound in ("min", "max"):
                np.testing.assert_allclose(tuple(getattr(part.bounding_box(), bound)),
                                           tuple(getattr(source.bounding_box(), bound)), rtol=0, atol=1e-7)
        for node, (parent, wrapped, label, color) in zip(nodes, before):
            self.assertEqual(id(node.parent), parent)
            self.assertTrue(node.wrapped.IsEqual(wrapped))
            self.assertEqual(node.label, label)
            self.assertEqual(tuple(node.color) if node.color is not None else None, color)
        return loaded

    def test_uniform_compounds_preserve_explicit_inherited_alpha_and_same_color_sharing(self):
        with tempfile.TemporaryDirectory() as temporary:
            for shared in (False, True):
                for inherited in (False, True):
                    with self.subTest(shared=shared, inherited=inherited):
                        self.assert_roundtrip(scene(shared=shared, inherited=inherited),
                                              Path(temporary) / "assembly.step")

    def test_distinct_color_definitions_and_simple_solids_keep_each_rgba(self):
        with tempfile.TemporaryDirectory() as temporary:
            for solid in (False, True):
                for inherited in (False, True):
                    with self.subTest(solid=solid, inherited=inherited):
                        self.assert_roundtrip(scene(different=True, solid=solid, inherited=inherited),
                                              Path(temporary) / "assembly.step")

    def test_uncolored_compounds_remain_uncolored(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "assembly.step"
            self.assert_roundtrip(scene(shared=True, uncolored=True), path)
            self.assertNotIn(b"COLOUR_RGB", path.read_bytes())

    def without_face_styles(self, shape):
        """Keep valid original compound/solid styles as a geometry control."""
        doc = self.original_doc(shape)
        shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
        color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
        definitions = TDF_LabelSequence()
        shape_tool.GetShapes(definitions)
        for index in range(1, definitions.Length() + 1):
            subshapes = TDF_LabelSequence()
            shape_tool.GetSubShapes_s(definitions.Value(index), subshapes)
            for subindex in range(1, subshapes.Length() + 1):
                label = subshapes.Value(subindex)
                if shape_tool.GetShape_s(label).ShapeType() == TopAbs_FACE:
                    color_tool.UnSetColor(label, XCAFDoc_ColorType.XCAFDoc_ColorSurf)
        return doc

    @staticmethod
    def png(image):
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()

    def test_face_styles_do_not_change_geometry_hierarchy_or_same_color_definitions(self):
        self.original_doc = self.exporter._create_bin_xcaf_doc
        with tempfile.TemporaryDirectory() as temporary:
            for shared in (False, True):
                with self.subTest(shared=shared):
                    shape = scene(shared=shared)
                    styled = Path(temporary) / "styled.step"
                    original = Path(temporary) / "solid-styles.step"
                    self.write(shape, styled)
                    with mock.patch.object(self.exporter, "_create_bin_xcaf_doc", side_effect=self.without_face_styles):
                        self.write(shape, original)
                    new, old = import_step(styled), import_step(original)
                    hierarchy = lambda sh: [(node.label, len(getattr(node, "children", ())))
                                            for node in [sh, *sh.descendants]]
                    self.assertEqual(hierarchy(new), hierarchy(old))
                    self.assertEqual(len(list(self.leaves(new))), 3)
                    for key in (b"MANIFOLD_SOLID_BREP", b"ADVANCED_FACE", b"NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
                        count = lambda path: len(re.findall(rb"\b" + key + rb"\s*\(", path.read_bytes()))
                        self.assertEqual(count(styled), count(original))
                        if key == b"MANIFOLD_SOLID_BREP":
                            self.assertEqual(count(styled), 2 if shared else 6)
                    # The old STEP contains valid solid colors which this importer
                    # overlooks. Apply the known intended RGBA only to the control
                    # wrappers; geometry still comes from its independently read STEP.
                    for (new_part, color), (old_part, old_color) in zip(self.leaves(new), self.leaves(old)):
                        self.assertIsNotNone(color)
                        self.assertIsNone(old_color)
                    for new_node, old_node in zip(new.descendants, old.descendants):
                        old_node.color = new_node.color
                    with mock.patch.dict(self.product["load_scene"].__globals__, {"_build_shape": lambda _: old}):
                        old_arrays = self.product["load_scene"](original)
                    new_arrays = self.product["load_scene"](styled)
                    for actual, control in zip(new_arrays, old_arrays):
                        np.testing.assert_array_equal(actual, control)
                    style = dict(size=128, view="iso", base=(30, 160, 160), accent=(240, 160, 80),
                                 background=(250, 240, 230))
                    self.assertEqual(
                        self.png(self.product["render"](new_arrays[0], triangle_colors=new_arrays[1], **style)),
                        self.png(self.product["render"](old_arrays[0], triangle_colors=old_arrays[1], **style)))


if __name__ == "__main__":
    unittest.main()
