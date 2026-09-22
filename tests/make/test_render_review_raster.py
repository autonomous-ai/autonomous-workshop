"""The batched rasteriser must draw what a face-at-a-time pass draws.

`render` composites whole batches of triangles at once because a whole-set
review frame carries over a million of them. The pixels it produces are the
contract, so every scene here is drawn twice: once by the renderer and once by
the plain per-face reference below, which is the algorithm the batched pass
replaced.
"""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

import numpy as np

TOOL = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"
BACKGROUND = (237, 240, 244)


def reference_render(tool, occurrences, azimuth, elevation, size, pad, framing=None):
    """One triangle at a time, nearest surface wins — no batching, no classes."""
    toward_viewer, right, up = tool["camera_basis"](azimuth, elevation)
    light = np.array([0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    all_points = (np.concatenate([points for points, _faces, _colour in occurrences])
                  if framing is None else np.asarray(framing, dtype=float))
    sx, sy = all_points @ right, all_points @ up
    width = float(sx.max() - sx.min())
    height = float(sy.max() - sy.min())
    scale = (1.0 - 2.0 * pad) * size / max(width, height)
    x_offset = (size - width * scale) / 2.0 - float(sx.min()) * scale
    y_offset = (size - height * scale) / 2.0 + float(sy.max()) * scale
    pixels = np.empty((size, size, 3), dtype=np.uint8)
    pixels[:] = BACKGROUND
    depths = np.full((size, size), -np.inf)
    for points, faces, colour in occurrences:
        px = points @ right * scale + x_offset
        py = y_offset - points @ up * scale
        depth = points @ toward_viewer
        for a, b, c in faces:
            corners = points[[a, b, c]]
            normal = np.cross(corners[1] - corners[0], corners[2] - corners[0])
            xs, ys = px[[a, b, c]], py[[a, b, c]]
            denominator = ((ys[1] - ys[2]) * (xs[0] - xs[2])
                           + (xs[2] - xs[1]) * (ys[0] - ys[2]))
            if abs(denominator) < 1e-12:
                continue
            fill = tool["_shade"](colour, normal, light, toward_viewer)
            for row in range(max(0, int(np.floor(ys.min()))),
                             min(size - 1, int(np.ceil(ys.max()))) + 1):
                for column in range(max(0, int(np.floor(xs.min()))),
                                    min(size - 1, int(np.ceil(xs.max()))) + 1):
                    x, y = column + 0.5, row + 0.5
                    w0 = ((ys[1] - ys[2]) * (x - xs[2]) + (xs[2] - xs[1]) * (y - ys[2])) / denominator
                    w1 = ((ys[2] - ys[0]) * (x - xs[2]) + (xs[0] - xs[2]) * (y - ys[2])) / denominator
                    w2 = 1.0 - w0 - w1
                    if w0 < -1e-9 or w1 < -1e-9 or w2 < -1e-9:
                        continue
                    z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]
                    if z > depths[row, column] + 1e-9:
                        depths[row, column] = z
                        pixels[row, column] = fill
    return pixels


def sphere(rings, segments, radius=10.0, centre=(0.0, 0.0, 0.0)):
    theta = np.linspace(0, np.pi, rings)
    phi = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    grid_theta, grid_phi = np.meshgrid(theta, phi, indexing="ij")
    points = np.stack([radius * np.sin(grid_theta) * np.cos(grid_phi),
                       radius * np.sin(grid_theta) * np.sin(grid_phi),
                       radius * np.cos(grid_theta)], axis=-1).reshape(-1, 3)
    points = points + np.asarray(centre, dtype=float)
    index = np.arange(rings * segments).reshape(rings, segments)
    east = index[:, (np.arange(segments) + 1) % segments]
    faces = np.concatenate([
        np.stack([index[:-1, :], east[:-1], index[1:, :]], -1).reshape(-1, 3),
        np.stack([east[:-1], east[1:], index[1:, :]], -1).reshape(-1, 3),
    ])
    return points, faces.astype(np.int64)


def plane(steps, z=0.0, tilt=0.0, size=20.0):
    line = np.linspace(-size / 2, size / 2, steps)
    x, y = np.meshgrid(line, line, indexing="ij")
    points = np.stack([x, y, z + tilt * x], -1).reshape(-1, 3)
    index = np.arange(steps * steps).reshape(steps, steps)
    faces = np.concatenate([
        np.stack([index[:-1, :-1], index[:-1, 1:], index[1:, :-1]], -1).reshape(-1, 3),
        np.stack([index[:-1, 1:], index[1:, 1:], index[1:, :-1]], -1).reshape(-1, 3),
    ])
    return points, faces.astype(np.int64)


class RasterEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(TOOL))

    def assert_matches_reference(self, occurrences, azimuth, elevation, size, framing=None):
        drawn = np.asarray(
            self.tool["render"](occurrences, azimuth, elevation, size, 0.07, framing=framing)
        )
        expected = reference_render(
            self.tool, occurrences, azimuth, elevation, size, 0.07, framing
        )
        differing = int((drawn != expected).any(axis=2).sum())
        self.assertEqual(differing, 0, f"{differing} pixels differ from the per-face pass")

    def test_curved_surface_of_sub_pixel_triangles(self):
        # 3,540 triangles across 300 px: most of them are smaller than a pixel,
        # which is the regime a whole-set review frame is entirely made of.
        self.assert_matches_reference([(*sphere(31, 60), (231, 168, 62))], -45.0, 35.264, 300)

    def test_faces_far_larger_than_one_batch_box(self):
        self.assert_matches_reference([(*plane(3, tilt=0.5), (74, 168, 162))], -90.0, 90.0, 240)

    def test_mixed_face_sizes_in_one_occurrence(self):
        points, faces = plane(3)
        small_points, small_faces = sphere(21, 40, radius=4.0, centre=(0.0, 0.0, 4.0))
        merged = np.concatenate([points, small_points])
        merged_faces = np.concatenate([faces, small_faces + len(points)])
        self.assert_matches_reference([(merged, merged_faces, (197, 88, 92))], -45.0, 35.264, 260)

    def test_occlusion_between_occurrences(self):
        near = np.array([[-3, -3, 6], [3, -3, 6], [3, 3, 6], [-3, 3, 6]], dtype=float)
        square = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)
        self.assert_matches_reference(
            [(*plane(9, tilt=0.4), (80, 110, 140)), (near, square, (220, 110, 35))],
            -90.0, 90.0, 200,
        )

    def test_coincident_faces_keep_the_one_drawn_first(self):
        points, faces = plane(5)
        twin = points.copy()
        self.assert_matches_reference(
            [(points, faces, (190, 65, 85)), (twin, faces, (80, 110, 140))], -90.0, 90.0, 160
        )

    def test_coplanar_faces_in_one_batch_keep_the_first_shading(self):
        # Same triangles, opposite winding: the normals flip, so the two sets
        # shade differently and every pixel is an exact depth tie between them.
        points, faces = plane(5)
        self.assert_matches_reference(
            [(points, np.concatenate([faces, faces[:, ::-1]]), (190, 65, 85))],
            -90.0, 90.0, 160,
        )

    def test_faces_clipped_by_the_frame_edge(self):
        # Framing on the near square pushes the plane off every edge, so a
        # face's padded batch box runs past the last column of the image.
        near = np.array([[-3, -3, 6], [3, -3, 6], [3, 3, 6], [-3, 3, 6]], dtype=float)
        square = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)
        points, faces = plane(7, z=0.0, size=60.0)
        self.assert_matches_reference(
            [(points, faces, (80, 110, 140)), (near, square, (220, 110, 35))],
            -90.0, 90.0, 200, framing=near,
        )

    def test_degenerate_and_off_frame_faces_are_skipped(self):
        points = np.array([
            [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],      # zero area
            [400.0, 400.0, 0.0], [420.0, 400.0, 0.0], [400.0, 420.0, 0.0],  # off frame
            [-8.0, -8.0, 0.0], [8.0, -8.0, 0.0], [0.0, 8.0, 3.0],   # the only visible face
        ])
        faces = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]], dtype=np.int64)
        self.assert_matches_reference([(points, faces, (115, 102, 189))], -90.0, 90.0, 180)

    def test_a_batch_budget_smaller_than_one_face_still_matches(self):
        """The budget splits batches and bands a single oversized face's rows.

        A production frame reaches both paths only at a large size, so the
        budget is lowered here instead to keep the test fast.
        """
        points, faces = plane(4, tilt=0.6)
        small_points, small_faces = sphere(15, 30, radius=3.0, centre=(0.0, 0.0, 5.0))
        merged = np.concatenate([points, small_points])
        merged_faces = np.concatenate([faces, small_faces + len(points)])
        scene = [(merged, merged_faces, (129, 149, 75))]
        expected = reference_render(self.tool, scene, -90.0, 90.0, 180, 0.07)
        budget = self.tool["BATCH_CELLS"]
        try:
            for self.tool["BATCH_CELLS"] in (1, 37, 512):
                drawn = np.asarray(self.tool["render"](scene, -90.0, 90.0, 180, 0.07))
                with self.subTest(budget=self.tool["BATCH_CELLS"]):
                    self.assertEqual(int((drawn != expected).any(axis=2).sum()), 0)
        finally:
            self.tool["BATCH_CELLS"] = budget

    def test_batched_shading_equals_shading_one_face_at_a_time(self):
        rng = np.random.default_rng(7)
        normals = np.concatenate([rng.normal(size=(64, 3)), np.zeros((1, 3))])
        light = np.array([0.35, -0.45, 0.82])
        light /= np.linalg.norm(light)
        toward_viewer = np.array([0.0, 0.0, 1.0])
        colour = (231, 168, 62)
        batched = self.tool["shade_faces"](colour, normals, light, toward_viewer)
        for index, normal in enumerate(normals):
            expected = self.tool["_shade"](colour, normal, light, toward_viewer)
            self.assertEqual(tuple(int(value) for value in batched[index]), expected)


if __name__ == "__main__":
    unittest.main()
