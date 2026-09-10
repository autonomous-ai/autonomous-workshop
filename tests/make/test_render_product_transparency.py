"""Authored STEP alpha gives schematic transparency without changing geometry."""

from pathlib import Path
from collections import Counter
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
from PIL import Image
from build123d import Box, Color, Compound


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_product"
STYLE = dict(size=240, view="front", base=(35, 160, 160), accent=(245, 160, 70),
             background=(250, 240, 220))


class ProductTransparencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(RENDERER))
        cls.tool["_runtime_paths"]()

    def scene(self, alpha, sheet_y=-10, reverse=False, variant=0):
        sheet = Box(28, 1, 28 + variant * 16).translate((0, sheet_y, 0))
        sheet.label = "sheet"
        sheet.color = Color(0, 0, 1, alpha)
        solid = Box(12 + variant * 8, 6, 12)
        solid.label = "solid"
        solid.color = Color(1, 0, 0)
        return Compound(children=[solid, sheet] if reverse else [sheet, solid])

    def load_shape(self, shape):
        with mock.patch.dict(self.tool["load_scene"].__globals__, {"_build_shape": lambda _: shape}):
            return self.tool["load_scene"](Path("unused.step"))

    def render(self, triangles, colors, **options):
        return self.tool["render"](triangles, triangle_colors=colors, **(STYLE | options))

    def test_real_step_alpha_front_and_behind_is_independent_of_child_order(self):
        from cadgen.step_export import export_build123d_step_file

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sheet.step"
            for sheet_y in (-10, 10):
                images = {}
                for alpha in (0.0, 0.2, 1.0):
                    for reverse in (False, True):
                        with self.subTest(y=sheet_y, alpha=alpha, reverse=reverse):
                            export_build123d_step_file(self.scene(alpha, sheet_y, reverse), path,
                                                      text_to_cad_entry_kind="assembly")
                            before = path.read_bytes()
                            triangles, colors = self.tool["load_scene"](path)
                            np.testing.assert_allclose(colors[colors[:, 2] == 255, 3], alpha, atol=1e-7)
                            image = np.asarray(self.render(triangles, colors))
                            if reverse:
                                np.testing.assert_array_equal(image, images[alpha])
                            else:
                                images[alpha] = image
                            self.assertEqual(path.read_bytes(), before)
                clear, partial, opaque = (images[value][110, 120] for value in (0.0, 0.2, 1.0))
                if sheet_y < 0:
                    self.assertGreater(clear[0], 150)
                    self.assertEqual(clear[2], 0)
                    self.assertEqual(opaque[0], 0)
                    self.assertGreater(opaque[2], 150)
                    self.assertTrue(0 < partial[0] < clear[0])
                    self.assertTrue(0 < partial[2] < opaque[2])
                else:
                    # An opaque object in front cannot receive the rear sheet's tint.
                    np.testing.assert_array_equal(clear, partial)
                    np.testing.assert_array_equal(clear, opaque)
            self.assertEqual(list(Path(temporary).iterdir()), [path])

    def test_zero_alpha_has_no_fill_outline_or_shadow_at_fixed_exact_framing(self):
        triangles, colors = self.load_shape(self.scene(0.0))
        solid = colors[:, 3] == 1
        framing = triangles.reshape(-1, 3)
        expected = self.render(triangles[solid], colors[solid], framing=framing)
        actual = self.render(triangles, colors, framing=framing)
        np.testing.assert_array_equal(np.asarray(actual), np.asarray(expected))
        invisible = colors.copy()
        invisible[:, 3] = 0
        blank = np.asarray(self.render(triangles, invisible))
        # Only the horizontal background gradient remains; no silhouette/shadow.
        np.testing.assert_array_equal(blank, np.broadcast_to(blank[:, :1], blank.shape))

    def test_two_transparent_sheets_use_depth_order_over_an_opaque_solid(self):
        shape = self.scene(0.2)
        green = Box(28, 1, 28).translate((0, -5, 0))
        green.color = Color(0, 1, 0, 0.5)
        shape = Compound(children=[*shape.children, green])
        triangles, colors = self.load_shape(shape)
        actual = np.asarray(self.render(triangles, colors))
        reversed_triangles, reversed_colors = self.load_shape(Compound(children=list(reversed(shape.children))))
        np.testing.assert_array_equal(actual, np.asarray(self.render(reversed_triangles, reversed_colors)))
        controls = []
        for channel in range(3):
            only = colors.copy()
            only[:, 3] = only[:, channel] == 255
            controls.append(np.asarray(self.render(triangles, only))[110, 130].astype(float))
        red, green, blue = controls
        expected = blue * 0.2 + (green * (128 / 255) + red * (127 / 255)) * 0.8
        np.testing.assert_allclose(actual[110, 130], expected, atol=1)

    def test_partial_sheet_does_not_receive_an_opaque_outline(self):
        triangles, colors = self.load_shape(self.scene(0.2))
        # No fully opaque triangle means no silhouette mask is painted.
        sheet = colors[:, 2] == 255
        masks = []
        original = self.tool["ImageDraw"].Draw
        def record(image, *args, **kwargs):
            pen = original(image, *args, **kwargs)
            if image.mode == "L":
                tracked = mock.Mock(wraps=pen)
                masks.append(tracked)
                return tracked
            return pen
        with mock.patch.object(self.tool["ImageDraw"], "Draw", side_effect=record):
            self.render(triangles[sheet], colors[sheet])
        self.assertEqual(len(masks), 1)
        masks[0].polygon.assert_not_called()

    def test_translucent_triangulation_blends_each_surface_once_without_seams(self):
        triangulations = (
            (((2, 2), (78, 2), (78, 78)), ((2, 2), (78, 78), (2, 78))),
            (((2, 2), (78, 2), (2, 78)), ((78, 2), (78, 78), (2, 78))),
        )
        for triangles in triangulations:
            for reverse in (False, True):
                image = Image.new("RGB", (80, 80), (100, 100, 100))
                for points in reversed(triangles) if reverse else triangles:
                    self.tool["_translucent_triangle"](image, points, (200, 0, 0), 0.2)
                pixels = np.asarray(image)
                np.testing.assert_array_equal(pixels[2:78, 2:78], np.full((76, 76, 3), (120, 80, 80)))
                self.assertEqual(image.getpixel((1, 1)), (100, 100, 100))
                # A genuinely separate second layer must blend again.
                for points in triangles:
                    self.tool["_translucent_triangle"](image, points, (200, 0, 0), 0.2)
                np.testing.assert_array_equal(np.asarray(image)[2:78, 2:78], np.full((76, 76, 3), (136, 64, 64)))

    def test_inherited_alpha_survives_nested_placements_without_mutation(self):
        leaf = Box(3, 4, 5)
        group = Compound(children=[leaf]).translate((8, 0, 0))
        group.color = Color(0.5, 0, 0, 0.25)
        before = [(node.position, tuple(node.color) if node.color is not None else None) for node in (leaf, group)]
        _, colors = self.load_shape(Compound(children=[group]))
        self.assertEqual({tuple(row) for row in colors}, {(188, 0, 0, 0.25)})
        self.assertEqual([(node.position, tuple(node.color) if node.color is not None else None) for node in (leaf, group)], before)

    def test_opaque_rgba_and_legacy_rgb_keep_exact_same_pixels(self):
        triangles, colors = self.load_shape(self.scene(1.0))
        for view in ("front", "iso", "rear"):
            for pose in (-17, 0, 31):
                with self.subTest(view=view, pose=pose):
                    rgba = self.render(triangles, colors, view=view, pose_degrees=pose)
                    rgb = self.render(triangles, colors[:, :3], view=view, pose_degrees=pose)
                    self.assertEqual(rgba.tobytes(), rgb.tobytes())

    def test_large_scene_keeps_every_triangle_and_its_rgb_alpha(self):
        triangle = np.array([[0., 0., 0.], [2., 0., 0.], [0., 0., 2.]])
        triangles = np.tile(triangle, (76800, 1, 1))
        colors = np.tile((0., 0., 255., 1.), (len(triangles), 1))
        colors[:38400] = (0., 255., 0., 0.4)
        # Both late, small components fell between the former sampling indices.
        triangles[76756] = triangle * 0.1 + (-5, 0, 0)
        triangles[76798] = triangle * 0.1 + (5, 0, 0)
        colors[76756] = (255., 0., 0., 1.)
        colors[76798] = (255., 0., 255., 0.2)
        calls = Counter()
        # Count complete surface coverage without repeatedly painting the same
        # probe face. The real pixel control below checks the small occurrence.
        def draw(image, *args):
            def polygon(points, *, fill):
                calls[(image.mode, fill)] += 1
            return SimpleNamespace(polygon=polygon, ellipse=lambda *args, **kwargs: None)
        def transparent(image, points, color, alpha):
            calls[("transparent", color, alpha)] += 1
        with mock.patch.object(self.tool["ImageDraw"], "Draw", side_effect=draw), \
             mock.patch.dict(self.tool["render"].__globals__, {"_translucent_triangle": transparent}):
            self.render(triangles, colors)
        light = self.tool["_normal"](np.array([-0.55, -0.75, 1.6]))
        intensity = 0.52 + 0.63 * abs(light[1])
        shaded = lambda color: self.tool["_shade"](color, intensity)
        self.assertEqual(calls, Counter({
            ("RGB", shaded((0, 0, 255))): 38398,
            ("RGB", shaded((255, 0, 0))): 1,
            ("transparent", shaded((0, 255, 0)), 0.4): 38400,
            ("transparent", shaded((255, 0, 255)), 0.2): 1,
            ("L", 255): 38399,
        }))

    def test_late_small_translucent_component_keeps_exact_pixels_above_old_limit(self):
        triangle = np.array([[0., 0., 0.], [2., 0., 0.], [0., 0., 2.]])
        triangles = np.tile(triangle, (76800, 1, 1))
        colors = np.tile((0., 0., 255., 1.), (len(triangles), 1))
        triangles[-2] = triangle * 0.2 + (3, 0, 0)
        colors[-2] = (255., 0., 0., 0.4)
        # Repainting an opaque filler face adds no coverage. Every surface and
        # the one translucent occurrence must match this complete small scene.
        expected = self.render(triangles[[0, -2]], colors[[0, -2]])
        actual = self.render(triangles, colors)
        self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_motion_and_exact_state_frames_keep_each_alpha_array_aligned(self):
        first, first_colors = self.load_shape(self.scene(0.2))
        second, second_colors = self.load_shape(self.scene(0.7, variant=1))
        angles = (-14.0, 14.0)
        motion = self.tool["motion_sheet"](first, angles=angles, triangle_colors=first_colors, **STYLE)
        for index, angle in enumerate(angles):
            expected = self.render(first, first_colors, pose_degrees=angle)
            self.assertEqual(motion.crop((index*240, 0, (index+1)*240, 240)).tobytes(), expected.tobytes())
        states, _ = self.tool["state_sheet"]((first, second), state_colors=(first_colors, second_colors), **STYLE)
        for index, (triangles, colors) in enumerate(((first, first_colors), (second, second_colors))):
            self.assertEqual(states.crop((index*240, 0, (index+1)*240, 240)).tobytes(), self.render(triangles, colors).tobytes())
        with self.assertRaisesRegex(ValueError, "visually indistinguishable"):
            self.tool["state_sheet"]((first, first), state_colors=(first_colors, second_colors), **STYLE)

    def test_invalid_alpha_is_refused_in_source_and_triangle_arrays(self):
        triangles, colors = self.load_shape(self.scene(0.2))
        for alpha in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(alpha=alpha):
                invalid = colors.copy()
                invalid[0, 3] = alpha
                with self.assertRaisesRegex(ValueError, "triangle colors"):
                    self.render(triangles, invalid)
                with self.assertRaisesRegex(ValueError, "alpha"):
                    self.tool["_authored_rgba"]((0, 0, 1, alpha))


if __name__ == "__main__":
    unittest.main()
