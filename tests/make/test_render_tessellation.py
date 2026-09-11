"""Indexed native extraction must match the actual Shape.tessellate path."""
from contextlib import redirect_stderr, redirect_stdout
import importlib
import io
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Box, Color, Compound, Cylinder, Location, Shape, Sphere, export_step, import_step


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


def original_arrays(shape, tolerance, angular_tolerance=0.1):
    vertices, triangles = Shape.tessellate(shape, tolerance, angular_tolerance)
    return (np.asarray([[point.X, point.Y, point.Z] for point in vertices], dtype=np.float64),
            np.asarray(triangles, dtype=np.int64))


def assembly():
    part = Compound([Box(3, 4, 2), Cylinder(.7, 3).translate((3, 0, 1))])
    leaves = []
    for index, alpha in enumerate((0., .35, 1.)):
        leaf = Compound.cast(part.wrapped.Located(
            Location((index * 9, index % 2 * 5, 1), (index * 17, 13, index * 29)).wrapped))
        leaf.label = f"repeated-{index}"
        if index == 1:
            leaf.wrapped.Reverse()
        group = Compound(children=[leaf], label=f"group-{index}")
        group.color = Color(.1 + .3 * index, .2, .7, alpha)
        group.location = Location((0, 2, 3), (23, index * 11, 7))
        leaves.append(group)
    # Similar dimensions are independent topology and must remain independent.
    for index in range(2):
        box = Box(3, 4, 2 + index * .01).translate((-7, index * 7, 1))
        box.label = f"independent-{index}"
        leaves.append(box)
    root = Compound(children=leaves, label="assembly")
    root.location = Location((11, -5, 8), (31, -7, 19))
    return root


class RenderTessellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = runpy.run_path(str(SCRIPTS / "render_product"))
        cls.review = runpy.run_path(str(SCRIPTS / "render_review"))
        cls.product["_runtime_paths"]()
        cls.helper = importlib.import_module("render_tessellation")

    def assert_arrays(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for value, control in zip(actual, expected):
            np.testing.assert_array_equal(value, control)
            self.assertEqual(value.dtype, control.dtype)

    def test_original_arrays_match_for_curves_transforms_orientation_and_tolerance(self):
        for shape in (Box(2, 3, 4), Sphere(2), Compound([Box(3, 4, 2), Cylinder(.7, 3)])):
            shape.location = Location((11, -3, 17), (31, 7, -23))
            for reverse in (False, True):
                if reverse:
                    shape.wrapped.Reverse()
                for tolerance, angular in ((.08, .1), (.2, .3)):
                    with self.subTest(type=type(shape).__name__, reverse=reverse,
                                      tolerance=tolerance, angular=angular):
                        # Exercise the new path first too; compare native meshing,
                        # not only extraction of a mesh primed by the old path.
                        actual = self.helper.tessellate_arrays(shape, tolerance, angular)
                        self.assert_arrays(actual, original_arrays(shape, tolerance, angular))

    def capture(self, shape):
        with mock.patch.dict(self.product["load_scene"].__globals__, {"_build_shape": lambda _: shape}):
            product = self.product["load_scene"](Path("synthetic.step"))
        review = self.review["tessellate_occurrences"](shape, .08)
        return product, review

    @staticmethod
    def png(image):
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    def assert_renderers_match(self, shape):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with mock.patch.object(self.helper, "tessellate_arrays", side_effect=original_arrays):
                old_product, old_review = self.capture(shape)
            product, review = self.capture(shape)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assert_arrays(product, old_product)
        self.assertEqual(len(review), 5)
        for (points, faces, color), (old_points, old_faces, old_color) in zip(review, old_review):
            self.assert_arrays((points, faces), (old_points, old_faces))
            self.assertEqual(color, old_color)
        # Compare serialized PNGs, not a perceptual metric or approximate pixels.
        for view in ("front", "iso"):
            style = dict(size=128, view=view, base=(40, 160, 160), accent=(240, 160, 70),
                         background=(250, 240, 220))
            self.assertEqual(
                self.png(self.product["render"](product[0], triangle_colors=product[1], **style)),
                self.png(self.product["render"](old_product[0], triangle_colors=old_product[1], **style)))
            azimuth, elevation = self.review["NAMED_VIEWS"][view]
            self.assertEqual(
                self.png(self.review["render"](review, azimuth, elevation, 128, .07)),
                self.png(self.review["render"](old_review, azimuth, elevation, 128, .07)))
        return product

    def test_both_renderers_keep_nested_repeated_independent_and_alpha_pngs_exact(self):
        shape = assembly()
        nodes = [shape, *shape.descendants]
        before = [(id(node.parent), node.wrapped.Located(node.wrapped.Location()),
                   tuple(node.color) if node.color is not None else None) for node in nodes]
        _, colors = self.assert_renderers_match(shape)
        self.assertEqual(set(colors[:, 3]), {0., .35, 1.})
        for node, (parent, wrapped, color) in zip(nodes, before):
            self.assertEqual(id(node.parent), parent)
            self.assertTrue(node.wrapped.IsEqual(wrapped))
            self.assertEqual(tuple(node.color) if node.color is not None else None, color)

    def test_imported_step_arrays_and_pngs_match_without_file_or_scene_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "assembly.step"
            export_step(assembly(), path)
            before = path.read_bytes()
            self.assert_renderers_match(import_step(path))
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temporary).iterdir()), [path])

    def test_exact_mesh_parameters_and_no_persistent_array_reuse(self):
        shape = Box(2, 3, 4)
        with mock.patch.object(shape, "mesh", wraps=shape.mesh) as mesher:
            points, faces = self.helper.tessellate_arrays(shape, .123, .456)
        mesher.assert_called_once_with(.123, .456)
        expected = original_arrays(shape, .123, .456)
        points[:] = 99
        faces[:] = 0
        self.assert_arrays(self.helper.tessellate_arrays(shape, .123, .456), expected)

    def test_empty_and_native_failures_propagate_without_partial_geometry(self):
        with self.assertRaisesRegex(ValueError, "Cannot tessellate an empty shape"):
            self.helper.tessellate_arrays(Compound(), .08)
        shape = assembly()
        failure = RuntimeError("native triangulation unavailable")
        with mock.patch.object(self.helper.BRep_Tool, "Triangulation_s", side_effect=failure):
            for load in (lambda: self.review["tessellate_occurrences"](shape, .08),
                         lambda: self.capture(shape)):
                with self.assertRaises(RuntimeError) as raised:
                    load()
                self.assertIs(raised.exception, failure)

    def test_missing_later_face_triangulation_fails_like_original_instead_of_omitting_it(self):
        shape = Box(2, 3, 4)
        native = self.helper.BRep_Tool.Triangulation_s
        errors = []
        for tessellate in (original_arrays, self.helper.tessellate_arrays):
            calls = 0
            def missing_second_face(*args):
                nonlocal calls
                calls += 1
                return None if calls == 2 else native(*args)
            with mock.patch.object(self.helper.BRep_Tool, "Triangulation_s", side_effect=missing_second_face):
                with self.assertRaises(AttributeError) as raised:
                    tessellate(shape, .08)
            self.assertEqual(calls, 2)
            errors.append(str(raised.exception))
        self.assertEqual(errors[0], errors[1])
        self.assertIn("NbNodes", errors[0])


if __name__ == "__main__":
    unittest.main()
