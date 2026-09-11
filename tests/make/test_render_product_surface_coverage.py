"""Dense product meshes retain the same closed surfaces as coarse meshes."""

from __future__ import annotations

from pathlib import Path
import runpy
import unittest
from unittest import mock

import numpy as np


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=320, view="iso", base=(44, 183, 190), accent=(255, 178, 66),
             background=(255, 246, 229))


def dense_closed_cube(coarse, subdivisions=180):
    """The same cube surface, with densely tessellated sides and broad caps.

    Every face points outward. Uneven face density models flat CAD panels
    alongside small curved details without requiring an expensive CAD build.
    """
    coordinates = np.linspace(-1.0, 1.0, subdivisions + 1)
    u, v = np.meshgrid(coordinates[:-1], coordinates[:-1])
    uv = np.column_stack([u.ravel(), v.ravel()])
    step = 2 / subdivisions
    sides = []
    for origin, axis_u, axis_v in [
        ([1, 0, 0], [0, 1, 0], [0, 0, 1]),
        ([-1, 0, 0], [0, -1, 0], [0, 0, 1]),
        ([0, 1, 0], [-1, 0, 0], [0, 0, 1]),
        ([0, -1, 0], [1, 0, 0], [0, 0, 1]),
    ]:
        a = np.array(origin) + uv[:, 0, None] * np.array(axis_u) + uv[:, 1, None] * np.array(axis_v)
        b = a + step * np.array(axis_u)
        c = b + step * np.array(axis_v)
        d = a + step * np.array(axis_v)
        sides.extend([np.stack([a, b, c], axis=1), np.stack([a, c, d], axis=1)])
    return np.concatenate([coarse[2:4], *sides, coarse[0:2]])


class ProductSurfaceCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))
        cls.coarse = cls.tool["_cube_triangles"]()
        cls.dense = dense_closed_cube(cls.coarse)

    def test_dense_closed_cube_keeps_the_coarse_surface_and_framing(self):
        before = self.dense.copy()
        # The dense fixture is the same closed cube: equal extents, area and
        # oriented volume, with no zero-area or inward-pointing triangles.
        cross = np.cross(self.dense[:, 1] - self.dense[:, 0],
                         self.dense[:, 2] - self.dense[:, 0])
        self.assertGreater(len(self.dense), 75_000)
        self.assertTrue(np.all(np.linalg.norm(cross, axis=1) > 0))
        self.assertTrue(np.all(np.einsum("ti,ti->t", cross, self.dense.mean(axis=1)) > 0))
        self.assertAlmostEqual(float(np.linalg.norm(cross, axis=1).sum() / 2), 24)
        self.assertAlmostEqual(float(np.einsum("ti,ti->t", self.dense[:, 0], cross).sum() / 6), 8)
        framing = self.coarse.reshape(-1, 3)
        expected = np.asarray(self.tool["render"](self.coarse, framing=framing, **STYLE))
        actual = np.asarray(self.tool["render"](self.dense, framing=framing, **STYLE))
        difference = np.abs(actual.astype(float) - expected.astype(float))
        # Allow only small rasterization differences along subdivided edges;
        # missing broad faces and holes across an entire wall must fail.
        self.assertLess(float(difference.mean()), 0.5)
        self.assertLess(float((difference.max(axis=2) > 25).mean()), 0.005)
        np.testing.assert_array_equal(self.dense, before)

    def test_above_old_cap_every_visible_face_and_silhouette_triangle_is_drawn(self):
        coarse = self.coarse
        # Closed cubes with many coincident copies keep this draw-count test
        # cheap while exercising an input above the former cap.
        triangles = np.tile(coarse, (6_251, 1, 1))
        triangles = np.concatenate([triangles, np.zeros((1, 3, 3))])
        normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        lengths = np.linalg.norm(normal, axis=1)
        valid = lengths > 1e-12
        normal[valid] /= lengths[valid, None]
        forward = self.tool["_camera"](STYLE["view"])[2]
        expected_visible = int((valid & ((normal @ forward) > 1e-8)).sum())
        counts = {"RGB": 0, "L": 0}
        original = self.tool["ImageDraw"].Draw

        def tracked(image, *args, **kwargs):
            draw = original(image, *args, **kwargs)
            if image.mode in counts:
                def count_polygon(*arguments, **options):
                    counts[image.mode] += 1
                    # No pixels are needed to assert the exact draw inventory.

                draw.polygon = count_polygon
            return draw

        with mock.patch.object(self.tool["ImageDraw"], "Draw", side_effect=tracked):
            self.tool["render"](triangles, **STYLE)
        self.assertEqual(counts["RGB"], expected_visible)
        self.assertEqual(counts["L"], int(valid.sum()))

    def test_empty_and_nonfinite_geometry_still_fail(self):
        with self.assertRaisesRegex(ValueError, "no renderable triangles"):
            self.tool["render"](np.empty((0, 3, 3)), **STYLE)
        invalid = self.coarse.copy()
        invalid[0, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            self.tool["render"](invalid, **STYLE)


if __name__ == "__main__":
    unittest.main()
