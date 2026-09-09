"""Review pixels must show the nearest surface, independent of triangulation."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

import numpy as np

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"


class ReviewDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def scene(self, slope=1.0, near_z=2.0, diagonal=False):
        far = np.array([[-10, -10, -10*slope], [10, -10, 10*slope],
                        [10, 10, 10*slope], [-10, 10, -10*slope]], float)
        near = np.array([[-.7, -.7, near_z], [.7, -.7, near_z],
                         [.7, .7, near_z], [-.7, .7, near_z]], float)
        faces = np.array([[0, 1, 3], [1, 2, 3]] if diagonal else [[0, 1, 2], [0, 2, 3]])
        return [(far, faces, (80, 110, 140)),
                (near, np.array([[0, 1, 2], [0, 2, 3]]), (220, 110, 35))]

    def render(self, occurrences):
        return np.array(self.tool['render'](occurrences, -90, 90, 240, .07))

    def interior(self):
        # A 20 mm projected square occupies 86% of the 240 pixel frame.
        world = (np.arange(240) + .5 - 120) / (.86 * 240 / 20)
        x, y = np.meshgrid(world, world)
        return (abs(x) < .5) & (abs(y) < .5)

    def shade(self, colour, normal):
        light = np.array([.35, -.45, .82])
        light /= np.linalg.norm(light)
        return self.tool['_shade'](colour, np.array(normal, float), light, np.array([0, 0, 1]))

    def test_near_square_is_visible_over_every_sloped_background(self):
        mask = self.interior()
        expected = self.shade((220, 110, 35), [0, 0, 1])
        for slope in (.5, 1.0, 2.0):
            for height in (2.0, 4.0):
                with self.subTest(slope=slope, height=height):
                    pixels = self.render(self.scene(slope=slope, near_z=height))
                    self.assertTrue(np.all(pixels[mask] == expected))

    def test_square_behind_sloped_background_stays_hidden(self):
        mask = self.interior()
        for slope in (.5, 1.0, 2.0):
            for height in (-2.0, -4.0):
                with self.subTest(slope=slope, height=height):
                    expected = self.shade((80, 110, 140), [-slope, 0, 1])
                    pixels = self.render(self.scene(slope=slope, near_z=height))
                    self.assertTrue(np.all(pixels[mask] == expected))

    def test_equivalent_plane_triangulations_have_identical_pixels(self):
        np.testing.assert_array_equal(self.render(self.scene()), self.render(self.scene(diagonal=True)))

    def test_occurrence_and_triangle_order_do_not_change_visibility(self):
        scene = self.scene()
        reversed_scene = [(points, faces[::-1], colour) for points, faces, colour in reversed(scene)]
        np.testing.assert_array_equal(self.render(scene), self.render(reversed_scene))

    def test_cyclic_triangle_corners_do_not_change_visibility(self):
        scene = self.scene()
        cyclic = [(points, np.roll(faces, 1, axis=1), colour) for points, faces, colour in scene]
        np.testing.assert_array_equal(self.render(scene), self.render(cyclic))

    def test_intersecting_planes_switch_visibility_at_their_actual_crossing(self):
        sloped = self.scene()[0]
        flat_points = sloped[0].copy()
        flat_points[:, 2] = 0
        flat_colour = (190, 65, 85)
        pixels = self.render([sloped, (flat_points, sloped[1], flat_colour)])
        world = (np.arange(240) + .5 - 120) / (.86 * 240 / 20)
        x, y = np.meshgrid(world, world)
        left = (x < -2) & (x > -8) & (abs(y) < 8)
        right = (x > 2) & (x < 8) & (abs(y) < 8)
        self.assertTrue(np.all(pixels[left] == self.shade(flat_colour, [0, 0, 1])))
        self.assertTrue(np.all(pixels[right] == self.shade(sloped[2], [-1, 0, 1])))


if __name__ == '__main__':
    unittest.main()
