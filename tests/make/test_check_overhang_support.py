"""Support decisions must describe geometry rather than mesh record order."""
from __future__ import annotations

import itertools
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from build123d import Align, Box, Cylinder, Location, export_stl
from scipy.spatial import cKDTree


CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_overhang"


class OverhangSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    @staticmethod
    def box(x, y, z, dx, dy, dz):
        return Location((x, y, z)) * Box(dx, dy, dz, align=(Align.MIN, Align.MIN, Align.MIN))

    def triangles(self, solid):
        self.assertTrue(solid.is_valid)
        self.assertEqual(len(solid.solids()), 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "part.stl"
            export_stl(solid, str(path))
            return self.tool["load_stl"](path)

    def needs_support(self, triangles):
        return any(r["kind"] == "overhang" for r in self.tool["_measure"](triangles))

    def mushroom(self):
        return self.box(-2, -2, 0, 4, 4, 10) + self.box(-5, -5, 10, 10, 10, 2)

    def test_flat_cap_around_a_stem_is_a_cantilever(self):
        self.assertTrue(self.needs_support(self.triangles(self.mushroom())))

    def test_supported_block_and_short_bridge_keep_passing(self):
        block = self.box(0, 0, 0, 20, 20, 10)
        bridge = (self.box(0, 0, 0, 6, 20, 20)
                  + self.box(6, 0, 14, 10, 20, 6)
                  + self.box(16, 0, 0, 6, 20, 20))
        for name, solid in (("block", block), ("bridge", bridge)):
            with self.subTest(shape=name):
                self.assertFalse(self.needs_support(self.triangles(solid)))

    def test_shelf_and_overlong_bridge_keep_failing(self):
        shelf = self.box(0, 0, 0, 6, 20, 20) + self.box(6, 0, 14, 24, 20, 6)
        long_bridge = (self.box(0, 0, 0, 6, 20, 20)
                       + self.box(6, 0, 14, 40, 20, 6)
                       + self.box(46, 0, 0, 6, 20, 20))
        for name, solid in (("shelf", shelf), ("long_bridge", long_bridge)):
            with self.subTest(shape=name):
                self.assertTrue(self.needs_support(self.triangles(solid)))

    def test_report_is_invariant_under_triangle_order_and_cyclic_vertices(self):
        triangles = self.triangles(self.mushroom())
        expected = self.tool["_measure"](triangles)
        for seed in range(4):
            rng = np.random.default_rng(seed)
            variant = triangles[rng.permutation(len(triangles))].copy()
            for index in range(len(variant)):
                variant[index] = np.roll(variant[index], int(rng.integers(3)), axis=0)
            with self.subTest(seed=seed):
                self.assertEqual(self.tool["_measure"](variant), expected)

    def test_shared_triangle_edges_do_not_create_material_outside_a_block(self):
        triangles = np.array(self.tool["_box"](0, 0, 0, 4, 4, 10), dtype=float)
        # Change only the diagonal of the x=4 wall. The same closed block has
        # different coincident-hit counts on its two opposite walls.
        triangles[-2:] = [[[4, 0, 0], [4, 4, 0], [4, 0, 10]],
                         [[4, 4, 0], [4, 4, 10], [4, 0, 10]]]
        verts, faces = self.tool["weld"](triangles)
        points = np.array([[20, 1, 2.9], [20, 2, 5.4], [20, 3, 7.9], [-20, 1, 2.9]])
        supported, _ = self.tool["bridge_support"](verts, faces, points, 0.4, 12)
        self.assertFalse(supported.any())

    def test_bridge_limit_uses_distance_between_actual_supports(self):
        for gap, expected in ((10, True), (12, True), (14, False)):
            triangles = np.array(self.tool["_box"](-gap/2-2, -2, 0, -gap/2, 2, 10)
                                 + self.tool["_box"](gap/2, -2, 0, gap/2+2, 2, 10))
            verts, faces = self.tool["weld"](triangles)
            with self.subTest(gap=gap):
                supported, spans = self.tool["bridge_support"](
                    verts, faces, np.array([[0., 0., 5.4]]), 0.4, 12)
                self.assertEqual(bool(supported[0]), expected)
                if expected:
                    self.assertAlmostEqual(spans[0], gap)

    def test_rotated_short_bridges_keep_their_actual_supports(self):
        solid = (self.box(0, 0, 0, 6, 20, 20)
                 + self.box(6, 0, 14, 10, 20, 6)
                 + self.box(16, 0, 0, 6, 20, 20))
        tris = self.triangles(solid)
        for angle in (15, 30, 45, 60, 75, 90, 135, 225):
            radians = np.deg2rad(angle)
            rotation = np.array([[np.cos(radians), -np.sin(radians), 0],
                                 [np.sin(radians), np.cos(radians), 0], [0, 0, 1]])
            with self.subTest(angle=angle):
                self.assertFalse(self.needs_support(tris @ rotation.T))

    def test_rotated_caps_still_have_only_one_support(self):
        tris = self.triangles(self.mushroom())
        for angle in (15, 45, 75):
            radians = np.deg2rad(angle)
            rotation = np.array([[np.cos(radians), -np.sin(radians), 0],
                                 [np.sin(radians), np.cos(radians), 0], [0, 0, 1]])
            with self.subTest(angle=angle):
                self.assertTrue(self.needs_support(tris @ rotation.T))

    def test_small_collar_is_supported_by_the_preceding_layer(self):
        shaft = Cylinder(2, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
        collar = Location((0, 0, 10)) * Cylinder(2.15, 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        self.assertFalse(self.needs_support(self.triangles(shaft + collar)))

    def test_thin_ledge_is_not_hidden_by_a_coarse_grid(self):
        tris = self.triangles(self.box(0, 0, 0, 10, 20, 10)
                              + self.box(0, 0, 10, 10.3, 20, 2))
        for angle in (0, 30, 60):
            radians = np.deg2rad(angle)
            rotation = np.array([[np.cos(radians), -np.sin(radians), 0],
                                 [np.sin(radians), np.cos(radians), 0], [0, 0, 1]])
            with self.subTest(angle=angle):
                rotated = tris @ rotation.T
                self.assertTrue(self.needs_support(rotated))
                regions = self.tool["_measure"](rotated, layer=.4)
                self.assertFalse(any(r["kind"] == "overhang" for r in regions))

    def test_separate_small_surfaces_are_not_accumulated_into_one_failure(self):
        base = self.box(0, 0, 0, 10, 14, 10)
        separate = base
        for y in (0, 6, 12):
            separate += self.box(10, y, 9, .4, 2, 1)
        self.assertFalse(self.needs_support(self.triangles(separate)))
        connected = base + self.box(10, 0, 9, .4, 14, 1)
        self.assertTrue(self.needs_support(self.triangles(connected)))

    def test_sampling_is_symmetric_in_all_triangle_corners(self):
        vertices = np.array([[0., 0., 0.], [3., 0., 0.], [1., 2., 0.]])
        reference = None
        for permutation in itertools.permutations(range(3)):
            points, weights = self.tool["sample_faces"](
                vertices, np.array([permutation]), np.array([True]), np.array([3.]), .4)
            if reference is None:
                reference = points
            with self.subTest(permutation=permutation):
                self.assertAlmostEqual(float(weights.sum()), 3.)
                self.assertLess(float(cKDTree(points).query(reference)[0].max()), 1e-10)
                self.assertLess(float(cKDTree(reference).query(points)[0].max()), 1e-10)
        points, weights = self.tool["sample_faces"](
            vertices, np.array([[0, 1, 2]]), np.array([True]), np.array([3.]), .001, cap=10)
        self.assertLessEqual(len(points), 10)
        self.assertAlmostEqual(float(weights.sum()), 3.)

    def test_support_queries_include_material_ending_at_the_layer_plane(self):
        tris = np.array(self.tool["_box"](-7, -2, 0, -5, 2, 10)
                        + self.tool["_box"](5, -2, 0, 7, 2, 10))
        vertices, faces = self.tool["weld"](tris)
        supported, spans = self.tool["bridge_support"](
            vertices, faces, np.array([[0., 0., 10.5]]), .5, 12)
        self.assertTrue(supported[0])
        self.assertAlmostEqual(spans[0], 10.)

    def test_empty_samples_have_no_support_or_span(self):
        verts, faces = self.tool["weld"](np.array(self.tool["_box"](0, 0, 0, 4, 4, 10)))
        supported, spans = self.tool["bridge_support"](verts, faces, np.empty((0, 3)), .4, 12)
        self.assertEqual(supported.tolist(), [])
        self.assertEqual(spans.tolist(), [])

    def test_cli_and_report_reject_the_same_cantilever(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            part, report = root / "cap.stl", root / "support.md"
            export_stl(self.mushroom(), str(part))
            result = subprocess.run([sys.executable, str(CHECK), str(part), "--report", str(report)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("RESULT: NEEDS SUPPORT", result.stdout)
            self.assertIn("FAIL", report.read_text())


if __name__ == "__main__":
    unittest.main()
