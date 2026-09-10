"""Finished-product images retain authored colors from exact nested STEP."""

from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image
from build123d import Axis, Box, Color, Compound, export_step


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=240, view="front", base=(35, 160, 160), accent=(245, 160, 70),
             background=(250, 240, 220))


class ProductColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))

    def parts(self, variant=0):
        red = Box(4, 5, 6 + variant * 5).translate((-5, 0, variant * 2.5))
        red.color = Color(1, 0, 0)
        red.label = "red"
        green = Box(4, 5, 6).translate((5, 0, 0))
        green.color = Color(0, 1, 0)
        green.label = "green"
        return red, green

    def scene(self, variant=0):
        red, green = self.parts(variant)
        inner = Compound(children=[red, Compound(children=[green])])
        inner.color = Color(0, 0, 1)
        inner = inner.rotate(Axis.Z, 23).translate((20, 4, 0))
        return Compound(children=[inner]).rotate(Axis.X, 12).translate((0, 7, 3))

    def load_shape(self, shape):
        with mock.patch.dict(self.tool["load_scene"].__globals__, {"_build_shape": lambda _: shape}):
            return self.tool["load_scene"](Path("unused.step"))

    def assert_red_and_green(self, image):
        pixels = np.asarray(image).astype(float)
        red = (pixels[:, :, 0] > pixels[:, :, 1] * 1.8) & (pixels[:, :, 0] > pixels[:, :, 2] * 1.8)
        green = (pixels[:, :, 1] > pixels[:, :, 0] * 1.8) & (pixels[:, :, 1] > pixels[:, :, 2] * 1.8)
        self.assertGreater(int(red.sum()), 200)
        self.assertGreater(int(green.sum()), 200)

    def test_nested_placements_and_leaf_colors_match_flat_without_mutation(self):
        shape = self.scene()
        nodes = [shape, *shape.descendants]
        before = [(id(node.parent), tuple(node.position), tuple(node.orientation),
                   tuple(node.color) if node.color is not None else None) for node in nodes]
        actual, colors = self.load_shape(shape)
        flat = Compound(children=[
            part.rotate(Axis.Z, 23).translate((20, 4, 0)).rotate(Axis.X, 12).translate((0, 7, 3))
            for part in self.parts()
        ])
        expected, expected_colors = self.load_shape(flat)
        np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=0)
        np.testing.assert_array_equal(colors, expected_colors)
        self.assertEqual({tuple(row) for row in colors}, {(255, 0, 0), (0, 255, 0)})
        after = [(id(node.parent), tuple(node.position), tuple(node.orientation),
                  tuple(node.color) if node.color is not None else None) for node in nodes]
        self.assertEqual(before, after)

    def test_step_round_trip_retains_world_bounds_and_authored_colors(self):
        shape = self.scene()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nested.step"
            export_step(shape, path)
            before = path.read_bytes()
            triangles, colors = self.tool["load_scene"](path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temporary).iterdir()), [path])
        bounds = shape.bounding_box()
        np.testing.assert_allclose(triangles.min(axis=(0, 1)), tuple(bounds.min), atol=1e-6, rtol=0)
        np.testing.assert_allclose(triangles.max(axis=(0, 1)), tuple(bounds.max), atol=1e-6, rtol=0)
        self.assertEqual({tuple(row) for row in colors}, {(255, 0, 0), (0, 255, 0)})
        self.assert_red_and_green(self.tool["render"](triangles, triangle_colors=colors, **STYLE))

    def test_group_color_inherits_and_linear_rgb_is_encoded_for_png(self):
        child = Box(2, 3, 4)
        group = Compound(children=[child])
        group.color = Color(0.5, 0.0, 0.0)
        before = tuple(child.color)
        _, colors = self.load_shape(Compound(children=[group]))
        self.assertEqual({tuple(row) for row in colors}, {(188, 0, 0)})
        self.assertEqual(tuple(child.color), before)

    def test_palette_and_nonprinted_midtones_round_trip_through_step(self):
        self.tool["_runtime_paths"]()
        from cadfilament import filament
        from cadgen.color import srgb

        printed, purchased = self.parts()
        printed.color = filament("cocoa brown")
        purchased.color = srgb("#d1822e")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "midtones.step"
            export_step(Compound(children=[printed, purchased]), path)
            before = path.read_bytes()
            _, colors = self.tool["load_scene"](path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temporary).iterdir()), [path])
        self.assertEqual({tuple(row) for row in colors}, {(142, 60, 6), (209, 130, 46)})

    def test_uncolored_shape_keeps_the_existing_palette_pixels(self):
        triangles, colors = self.load_shape(Box(2, 3, 4))
        self.assertTrue(np.all(colors == -1))
        actual = self.tool["render"](triangles, triangle_colors=colors, **STYLE)
        expected = self.tool["render"](triangles, **STYLE)
        np.testing.assert_array_equal(np.asarray(actual), np.asarray(expected))

    def test_bad_color_alignment_or_channels_fail_clearly(self):
        triangles, colors = self.load_shape(self.scene())
        for invalid in (colors[:-1], np.full(colors.shape, np.nan),
                        np.full(colors.shape, 256), np.tile((-1, 0, 0), (len(colors), 1))):
            with self.subTest(shape=invalid.shape):
                with self.assertRaisesRegex(ValueError, "triangle colors"):
                    self.tool["render"](triangles, triangle_colors=invalid, **STYLE)

    def test_recoloring_unchanged_geometry_cannot_pass_state_distinction(self):
        triangles, colors = self.load_shape(self.scene())
        changed = np.tile((0, 0, 255), (len(colors), 1))
        with self.assertRaisesRegex(ValueError, "visually indistinguishable"):
            self.tool["state_sheet"]((triangles, triangles), state_colors=(colors, changed), **STYLE)
        with self.assertRaisesRegex(ValueError, "one array per exact state"):
            self.tool["state_sheet"]((triangles, triangles), state_colors=(colors,), **STYLE)

    def test_cli_preserves_colors_in_hero_motion_and_state_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first.step", root / "second.step"
            export_step(self.scene(), first)
            export_step(self.scene(1), second)
            before = (first.read_bytes(), second.read_bytes())
            cases = {
                "motion": ["--motion-sheet", str(root / "motion.png")],
                "state": ["--state-sheet", str(root / "state.png"), "--state-source",
                          str(first), "--state-source", str(second)],
            }
            for name, options in cases.items():
                output = root / f"{name}-hero.png"
                result = subprocess.run(
                    [sys.executable, str(RENDERER), str(first), "-o", str(output),
                     "--size", "800", *options], capture_output=True, text=True, timeout=45,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                with Image.open(output) as image:
                    self.assert_red_and_green(image)
                with Image.open(root / f"{name}.png") as image:
                    for left in range(0, image.width, 800):
                        self.assert_red_and_green(image.crop((left, 0, left + 800, 800)))
            self.assertEqual((first.read_bytes(), second.read_bytes()), before)
            self.assertTrue(all(path.suffix in {".step", ".png"} for path in root.iterdir()))


if __name__ == "__main__":
    unittest.main()
