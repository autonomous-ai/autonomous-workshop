"""Named rear views preserve exact geometry, winding, and left/right placement."""
from __future__ import annotations

import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=240, base=(66, 153, 111), accent=(228, 167, 55), background=(246, 238, 215))


def box(size, center):
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
    ], dtype=float) * np.array(size) / 2 + center
    faces = np.array([
        [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7],
    ])
    return vertices[faces]


def scene(variant):
    # Different heights and X/Y offsets expose a mistaken front or mirror view.
    return np.concatenate([
        box((25, 18, 2), (0, 0, 1)),
        box((5, 4, 6 + variant * 3), (-7, 5, 5 + variant * 1.5)),
        box((3 + variant, 7, 14), (6, -4, 9)),
        box((2, 2, 3), (-2, -6 + variant, 3.5)),
    ])


def write_step(path, variant):
    """The same asymmetric scene as ``scene``, as the STEP the CLI now reads."""
    from build123d import Box, Compound, Pos, export_step

    solids = [
        Pos(0, 0, 1) * Box(25, 18, 2),
        Pos(-7, 5, 5 + variant * 1.5) * Box(5, 4, 6 + variant * 3),
        Pos(6, -4, 9) * Box(3 + variant, 7, 14),
        Pos(-2, -6 + variant, 3.5) * Box(2, 2, 3),
    ]
    export_step(Compound(children=solids), str(path))


class ProductViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))

    def test_rear_camera_has_proper_handedness_and_looks_from_positive_y(self):
        right, up, forward = self.tool["_camera"]("rear")
        basis = np.array([right, up, forward])
        np.testing.assert_allclose(basis @ basis.T, np.eye(3), atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(basis), 1)
        np.testing.assert_allclose(right, [-1, 0, 0])
        self.assertGreater(up[2], 0)
        self.assertGreater(forward[1], 0)
        self.assertGreater(forward[2], 0)

    def test_rear_matches_rigid_rotation_for_asymmetric_scenes_without_mutation(self):
        for variant in (0, 1, 2):
            for pose in (-17, 0, 31):
                with self.subTest(variant=variant, pose=pose):
                    triangles = scene(variant)
                    before = triangles.copy()
                    rotated = triangles.copy()
                    rotated[:, :, :2] *= -1  # Proper 180-degree rotation about Z.
                    expected = self.tool["render"](rotated, view="front", pose_degrees=pose, **STYLE)
                    actual = self.tool["render"](triangles, view="rear", pose_degrees=pose, **STYLE)
                    np.testing.assert_array_equal(np.array(actual), np.array(expected))
                    np.testing.assert_array_equal(triangles, before)
                    front = self.tool["render"](triangles, view="front", pose_degrees=pose, **STYLE)
                    self.assertFalse(np.array_equal(np.array(front), np.array(actual)))

    def test_rear_cli_is_available_for_product_motion_and_state_sheets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first.step", root / "second.step"
            write_step(first, 0)
            write_step(second, 2)
            before = (first.read_bytes(), second.read_bytes())
            cases = {
                "product": ["--view", "rear"],
                "motion": ["--motion-sheet", str(root / "motion.png"), "--motion-view", "rear"],
                "state": ["--state-sheet", str(root / "state.png"), "--state-view", "rear",
                          "--state-source", str(first), "--state-source", str(second)],
            }
            for name, options in cases.items():
                with self.subTest(name=name):
                    output = root / f"{name}-product.png"
                    result = subprocess.run([sys.executable, str(RENDERER), str(first), "-o", str(output),
                                             "--size", "800", *options], capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    with Image.open(output) as image:
                        self.assertEqual((image.mode, image.size), ("RGB", (800, 800)))
                    if name != "product":
                        with Image.open(root / f"{name}.png") as image:
                            self.assertEqual(image.size, ((3 if name == "motion" else 2) * 800, 800))
            self.assertEqual((first.read_bytes(), second.read_bytes()), before)

    def test_rear_state_sheet_still_rejects_duplicate_geometry(self):
        triangles = scene(1)
        with self.assertRaisesRegex(ValueError, "visually indistinguishable"):
            self.tool["state_sheet"]((triangles, triangles), view="rear", **STYLE)


if __name__ == "__main__":
    unittest.main()
