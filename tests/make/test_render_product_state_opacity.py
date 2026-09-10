"""State distinction sees motion through fixed clear covers, not appearance edits."""

from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image
from build123d import Box, Color, Compound


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=240, view="front", base=(35, 160, 160), accent=(245, 160, 70),
             background=(250, 240, 220))


class StateOpacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))
        cls.tool["_runtime_paths"]()

    def scene(self, x):
        cover = Box(100, 1, 100).translate((0, -20, 0))
        cover.label = "fixed_clear_cover"
        cover.color = Color(0, 0, 1, 0.2)
        mover = Box(18, 8, 28).translate((x, 0, 0))
        mover.label = "moving_block"
        mover.color = Color(1, 0, 0)
        return Compound(children=[cover, mover])

    def load(self, x):
        with mock.patch.dict(self.tool["load_scene"].__globals__,
                             {"_build_shape": lambda _: self.scene(x)}):
            return self.tool["load_scene"](Path("unused.step"))

    def sheet(self, scenes):
        return self.tool["state_sheet"](
            tuple(row[0] for row in scenes), state_colors=tuple(row[1] for row in scenes), **STYLE
        )

    def comparison(self, scenes):
        return self.tool["_state_comparison_colors"](
            tuple(row[0] for row in scenes), tuple(row[1] for row in scenes)
        )

    def test_exported_step_motion_under_fixed_clear_cover_passes_actual_cli(self):
        from cadgen.step_export import export_build123d_step_file

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = [root / "left.step", root / "right.step"]
            for path, x in zip(paths, (-25, 25)):
                export_build123d_step_file(self.scene(x), path, text_to_cad_entry_kind="assembly")
            before = [path.read_bytes() for path in paths]
            scenes = [self.tool["load_scene"](path) for path in paths]
            sheet, differences = self.sheet(scenes)
            self.assertGreater(differences[0], 2.0)
            for index, (triangles, colors) in enumerate(scenes):
                actual = self.tool["render"](triangles, triangle_colors=colors, **STYLE)
                self.assertEqual(sheet.crop((240*index, 0, 240*(index+1), 240)).tobytes(), actual.tobytes())
            completed = subprocess.run([
                sys.executable, str(RENDERER), str(paths[0]), "-o", str(root / "hero.png"),
                "--size", "800", "--state-view", "front", "--state-sheet", str(root / "states.png"),
                "--state-source", str(paths[0]), "--state-source", str(paths[1]),
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with Image.open(root / "states.png") as image:
                self.assertEqual(image.size, (1600, 800))
            self.assertEqual([path.read_bytes() for path in paths], before)

    def test_color_opacity_and_opacity_reassignment_alone_are_not_motion(self):
        triangles, colors = self.load(-25)
        for change in ("rgb", "alpha", "reassign"):
            with self.subTest(change=change):
                altered = colors.copy()
                if change == "rgb":
                    altered[:, :3] = (0, 255, 0)
                elif change == "alpha":
                    altered[colors[:, 3] < 1, 3] = 0.8
                else:
                    altered[:, 3] = np.where(colors[:, 3] < 1, 1.0, 0.2)
                # State and vertex ordering supply no actor identity assumption.
                reordered = triangles[::-1][:, [1, 2, 0]]
                with self.assertRaisesRegex(ValueError, "visually indistinguishable"):
                    self.sheet(((triangles, colors), (reordered, altered[::-1])))

    def test_one_changed_state_makes_cover_opaque_in_all_comparisons(self):
        for change in ("alpha", "geometry"):
            with self.subTest(change=change):
                scenes = [self.load(x) for x in (-25, 0, 25)]
                cover = scenes[2][1][:, 3] < 1
                if change == "alpha":
                    scenes[2][1][cover, 3] = 0.8
                else:
                    scenes[2][0][cover, :, 2] += 0.25
                self.assertEqual(self.comparison(scenes), (None, None, None))
                with self.assertRaisesRegex(ValueError, "visually indistinguishable"):
                    self.sheet(scenes)

    def test_triangle_and_vertex_order_preserve_fixed_cover_opacity(self):
        first = self.load(-25)
        triangles, colors = self.load(25)
        second = (triangles[::-1][:, [1, 2, 0]], colors[::-1])
        comparisons = self.comparison((first, second))
        for (_, authored), comparison in zip((first, second), comparisons):
            np.testing.assert_array_equal(comparison[:, 3], authored[:, 3])
            self.assertTrue(np.all(comparison[:, :3] == -1))
        self.assertGreater(self.sheet((first, second))[1][0], 2.0)

    def test_changed_topology_retains_fixed_cover_and_mixed_rgb_rgba_is_supported(self):
        first = self.load(-25)
        triangles, colors = self.load(25)
        extra = triangles[colors[:, 3] == 1].copy() + np.array([0, 0, 30])
        second = (np.concatenate((triangles, extra)),
                  np.concatenate((colors, np.tile((255, 0, 0, 1), (len(extra), 1)))))
        comparisons = self.comparison((first, second))
        self.assertNotEqual(len(comparisons[0]), len(comparisons[1]))
        for comparison in comparisons:
            self.assertEqual(np.count_nonzero(comparison[:, 3] < 1), 12)
        self.assertGreater(self.sheet((first, second))[1][0], 2.0)
        self.assertEqual(self.comparison((first, (triangles, colors[:, :3]))), (None, None))

    def test_coincident_ambiguity_and_changed_multiplicity_are_opaque(self):
        first, second = self.load(-25), self.load(25)
        for ambiguous in (True, False):
            with self.subTest(ambiguous=ambiguous):
                scenes = []
                for index, (triangles, colors) in enumerate((first, second)):
                    sheet = colors[:, 3] < 1
                    if ambiguous or index == 1:
                        duplicate = colors[sheet].copy()
                        if ambiguous:
                            duplicate[:, 3] = 0.7
                        scenes.append((np.concatenate((triangles, triangles[sheet])),
                                       np.concatenate((colors, duplicate))))
                    else:
                        scenes.append((triangles, colors))
                self.assertEqual(self.comparison(scenes), (None, None))

    def test_matching_unambiguous_coincident_multiplicity_is_preserved(self):
        scenes = []
        for x in (-25, 25):
            triangles, colors = self.load(x)
            sheet = colors[:, 3] < 1
            scenes.append((np.concatenate((triangles, triangles[sheet])),
                           np.concatenate((colors, colors[sheet]))))
        for comparison in self.comparison(scenes):
            self.assertEqual(np.count_nonzero(comparison[:, 3] == 0.2), 24)

    def test_geometry_keys_use_exact_coordinates(self):
        triangle = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])
        shifted = triangle.copy()
        shifted[0, 1, 0] = np.nextafter(1.0, 2.0)
        colors = np.array([[0., 0., 255., 0.2]])
        self.assertEqual(self.comparison(((triangle, colors), (shifted, colors))), (None, None))

    def test_opaque_comparison_keeps_exact_legacy_pixels_and_differences(self):
        cube = self.tool["_cube_triangles"]()
        states = (cube, cube * np.array([1., 1., 1.35]))
        legacy = [self.tool["render"](state, **STYLE) for state in states]
        arrays = [np.asarray(frame.resize((96, 96)), dtype=float) for frame in legacy]
        expected = float(np.abs(arrays[0] - arrays[1]).mean())
        for channels in (3, 4):
            with self.subTest(channels=channels):
                colors = tuple(np.tile((255, 0, 0, 1)[:channels], (len(state), 1)) for state in states)
                comparison = self.comparison(tuple(zip(states, colors)))
                self.assertEqual(comparison, (None, None))
                for state, image, color in zip(states, legacy, comparison):
                    self.assertEqual(self.tool["render"](state, triangle_colors=color, **STYLE).tobytes(), image.tobytes())
                _, differences = self.tool["state_sheet"](states, state_colors=colors, **STYLE)
                self.assertEqual(differences, (expected,))


if __name__ == "__main__":
    unittest.main()
