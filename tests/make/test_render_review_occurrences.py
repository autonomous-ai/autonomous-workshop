"""CAD review must retain leaf materials and assembly placements."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Axis, Box, Color, Compound, Shape, export_step, import_step


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"


class ReviewOccurrencesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = runpy.run_path(str(RENDERER))

    def parts(self):
        red = Box(4, 5, 6).translate((5, 0, 0))
        red.color = Color(1, 0, 0)
        red.label = "red"
        green = Box(3, 4, 5).translate((-5, 0, 0))
        green.color = Color(0, 1, 0)
        green.label = "green"
        return red, green

    def scene(self):
        red, green = self.parts()
        nested = Compound(children=[red, Compound(children=[green], label="inner")], label="moving")
        nested.color = Color(0, 0, 1)
        nested = nested.rotate(Axis.Z, 90).translate((20, 0, 0))
        return Compound(children=[nested], label="assembly").rotate(Axis.X, 90).translate((0, 7, 3))

    def flat_control(self):
        return Compound(children=[
            part.rotate(Axis.Z, 90).translate((20, 0, 0)).rotate(Axis.X, 90).translate((0, 7, 3))
            for part in self.parts()
        ])

    def occurrences(self, shape):
        return self.renderer["tessellate_occurrences"](shape, 0.08)

    def assert_same_occurrences(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for (points, faces, color), (wanted_points, wanted_faces, wanted_color) in zip(actual, expected):
            np.testing.assert_allclose(points, wanted_points, atol=1e-10, rtol=0)
            np.testing.assert_array_equal(faces, wanted_faces)
            self.assertEqual(color, wanted_color)

    def test_nested_leaf_colors_and_all_parent_transforms_match_flat_assembly(self):
        actual = self.occurrences(self.scene())
        self.assertEqual([color for _, _, color in actual], [(255, 0, 0), (0, 255, 0)])
        self.assert_same_occurrences(actual, self.occurrences(self.flat_control()))

    def test_grouping_does_not_change_rendered_pixels(self):
        for view in ("front", "iso"):
            with self.subTest(view=view):
                azimuth, elevation = self.renderer["NAMED_VIEWS"][view]
                render = self.renderer["render"]
                nested = render(self.occurrences(self.scene()), azimuth, elevation, 320, 0.07)
                flat = render(self.occurrences(self.flat_control()), azimuth, elevation, 320, 0.07)
                np.testing.assert_array_equal(np.asarray(nested), np.asarray(flat))

    def test_imported_step_keeps_nested_colors_and_world_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nested.step"
            export_step(self.scene(), path)
            loaded = import_step(path)
        actual = self.occurrences(loaded)
        self.assertEqual([color for _, _, color in actual], [(255, 0, 0), (0, 255, 0)])
        points = np.concatenate([points for points, _, _ in actual])
        bounds = loaded.bounding_box()
        np.testing.assert_allclose(points.min(axis=0), tuple(bounds.min), atol=1e-6, rtol=0)
        np.testing.assert_allclose(points.max(axis=0), tuple(bounds.max), atol=1e-6, rtol=0)

    def test_rendering_does_not_mutate_source_hierarchy_or_placements(self):
        scene = self.scene()
        nodes = [scene, *scene.descendants]
        before = [(id(node), id(node.parent), tuple(node.position), tuple(node.orientation)) for node in nodes]
        self.occurrences(scene)
        after = [(id(node), id(node.parent), tuple(node.position), tuple(node.orientation)) for node in [scene, *scene.descendants]]
        self.assertEqual(after, before)

    def test_uncolored_leaves_retain_explicit_group_color(self):
        group = Compound(children=[Box(2, 2, 2), Box(2, 2, 2).translate((4, 0, 0))])
        group.color = Color(0, 0, 1)
        occurrences = self.occurrences(Compound(children=[group]))
        self.assertEqual([color for _, _, color in occurrences], [(0, 0, 255), (0, 0, 255)])

    def test_repeated_part_instances_are_not_deduplicated(self):
        part, _ = self.parts()
        scene = Compound(children=[Compound(children=[part]), Compound(children=[part.translate((12, 0, 0))])])
        occurrences = self.occurrences(scene)
        self.assertEqual(len(occurrences), 2)
        self.assertEqual(occurrences[0][2], occurrences[1][2])
        np.testing.assert_allclose(occurrences[1][0] - occurrences[0][0], np.tile((12, 0, 0), (len(occurrences[0][0]), 1)), atol=1e-10)

    def test_single_uncolored_solid_keeps_existing_fallback(self):
        occurrences = self.occurrences(Box(2, 3, 4))
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0][2], self.renderer["FALLBACK_COLOURS"][0])

    def test_nested_tessellation_failure_is_not_silently_dropped(self):
        with mock.patch.object(Shape, "tessellate", side_effect=RuntimeError("kernel tessellation failed")):
            with self.assertRaisesRegex(RuntimeError, "kernel tessellation failed"):
                self.occurrences(self.scene())


if __name__ == "__main__":
    unittest.main()
