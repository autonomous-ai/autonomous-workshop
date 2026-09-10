"""Exact STEP surfaces occlude by pixel depth, including partial overlap."""

from pathlib import Path
import runpy
import tempfile
import unittest

import numpy as np
from build123d import Box, Color, Compound


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=320, view="iso", base=(120, 90, 60), accent=(240, 200, 120),
             background=(250, 242, 231))


class ProductDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))
        cls.tool["_runtime_paths"]()

    def plates(self, *, lower_alpha=1, upper_alpha=1):
        lower = Box(260, 180, 12).translate((0, 0, 6))
        lower.color = Color(0, 0, 1, lower_alpha)
        upper = Box(220, 140, 3).translate((0, 0, 14))
        upper.color = Color(1, 0, 0, upper_alpha)
        self.assertTrue(lower.is_valid and upper.is_valid)
        self.assertAlmostEqual(upper.bounding_box().min.Z - lower.bounding_box().max.Z, 0.5)
        self.assertIsNone(lower.intersect(upper))
        from cadgen.step_export import export_build123d_step_file
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plates.step"
            export_build123d_step_file(Compound(children=[lower, upper]), path,
                                      text_to_cad_entry_kind="assembly")
            before = path.read_bytes()
            triangles, colors = self.tool["load_scene"](path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temporary).iterdir()), [path])
        self.assertEqual(len(triangles), 24)
        np.testing.assert_allclose(colors[colors[:, 0] == 255, 3], upper_alpha)
        np.testing.assert_allclose(colors[colors[:, 2] == 255, 3], lower_alpha)
        return triangles, colors

    def top_samples(self, triangles):
        x, y = np.meshgrid(np.linspace(-95, 95, 31), np.linspace(-55, 55, 23))
        points = np.column_stack((x.ravel(), y.ravel(), np.full(x.size, 15.5)))
        bounds = triangles.reshape(-1, 3)
        right, up, _ = self.tool["_camera"]("iso")
        center = (bounds.min(axis=0) + bounds.max(axis=0)) / 2
        bx, by = (bounds - center) @ right, -(bounds - center) @ up
        fit = STYLE["size"] * 0.72 / max(np.ptp(bx), np.ptp(by))
        screen_x = ((points-center) @ right - (bx.min()+bx.max())/2)*fit + STYLE["size"]/2
        screen_y = (-(points-center) @ up - (by.min()+by.max())/2)*fit + STYLE["size"]*0.46
        return screen_x.astype(int), screen_y.astype(int)

    def render(self, triangles, colors):
        return np.asarray(self.tool["render"](triangles, triangle_colors=colors, **STYLE))

    def test_real_step_lower_plate_never_paints_over_the_upper_surface(self):
        triangles, colors = self.plates()
        image = self.render(triangles, colors)
        x, y = self.top_samples(triangles)
        samples = image[y, x]
        # The former mean-depth sort paints blue over almost half this red top,
        # despite valid disjoint solids and only 24 complete STEP triangles.
        self.assertTrue(np.all(samples[:, 0] > 200))
        self.assertTrue(np.all(samples[:, 0] > 4 * samples[:, 2].astype(float)))

    def test_opaque_visibility_is_independent_of_triangle_order_and_subdivision(self):
        triangles, colors = self.plates()
        expected = self.render(triangles, colors)
        for order in (np.arange(len(triangles))[::-1], np.random.default_rng(41).permutation(len(triangles))):
            np.testing.assert_array_equal(self.render(triangles[order], colors[order]), expected)
        # Split every triangle into three coplanar triangles without changing
        # its oriented surface. Visibility cannot depend on triangle centroids.
        centers = triangles.mean(axis=1)
        split = np.stack([np.stack((triangles[:, corner], triangles[:, (corner+1) % 3], centers), axis=1)
                          for corner in range(3)], axis=1).reshape(-1, 3, 3)
        actual = self.render(split, np.repeat(colors, 3, axis=0))
        x, y = self.top_samples(triangles)
        np.testing.assert_array_equal(actual[y, x], expected[y, x])

    def test_rear_translucent_plate_cannot_tint_nearer_opaque_top(self):
        triangles, colors = self.plates(lower_alpha=0.6)
        actual = self.render(triangles, colors)
        clear = colors.copy()
        clear[clear[:, 2] == 255, 3] = 0
        expected = self.render(triangles, clear)
        x, y = self.top_samples(triangles)
        np.testing.assert_array_equal(actual[y, x], expected[y, x])

    def test_front_translucent_plate_tints_opaque_top_everywhere(self):
        triangles, colors = self.plates(upper_alpha=0.5)
        actual = self.render(triangles, colors)
        x, y = self.top_samples(triangles)
        samples = actual[y, x]
        self.assertTrue(np.all(samples[:, 0] > 100))
        self.assertTrue(np.all(samples[:, 2] > 100))
        # The unchanged lighting lifts saturated channels slightly toward white.
        self.assertTrue(np.all(samples[:, 1] < 40))

    def test_fragment_depth_interpolates_and_transparency_never_writes_depth(self):
        pixels = np.full((24, 24, 3), 255, dtype=np.uint8)
        depths = np.full((24, 24), -np.inf)
        points = ((2., 2.), (22., 2.), (2., 22.))
        raster = self.tool["_raster_triangle"]
        raster(pixels, depths, points, (0, 20, 0), (200, 0, 0), 1)
        self.assertAlmostEqual(depths[5, 5], 3.5)
        before = depths.copy()
        raster(pixels, depths, points, (2, 2, 2), (0, 200, 0), 0.5)
        self.assertEqual(tuple(pixels[5, 5]), (200, 0, 0))
        self.assertEqual(tuple(pixels[5, 2]), (100, 100, 0))
        raster(pixels, depths, points, (30, 30, 30), (0, 0, 200), 0.5)
        self.assertEqual(tuple(pixels[5, 5]), (100, 0, 100))
        np.testing.assert_array_equal(depths, before)


if __name__ == "__main__":
    unittest.main()
