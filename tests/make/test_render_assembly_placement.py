"""Renderer placement preserves exact leaves without copying parent graphs."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Box, Color, Compound, Cylinder, Location, Shape, export_step, import_step


SCRIPTS = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts'


def old_colored_leaves(shape, parent_location=None, inherited_color=None):
    """The previous traversal, retained only as a bounded comparison oracle."""
    color = shape.color if shape.color is not None else inherited_color
    children = list(getattr(shape, 'children', ()) or ())
    if children:
        location = shape.location
        if parent_location is not None:
            location = parent_location * location
        for child in children:
            yield from old_colored_leaves(child, location, color)
    else:
        yield shape if parent_location is None else shape.moved(parent_location), color


def old_review_leaves(shape):
    for placed, color in old_colored_leaves(shape):
        if placed.color is None and color is not None:
            placed.color = color
        yield placed


def scene(count=4):
    groups = []
    for index in range(count):
        # Bare compound remains one appearance leaf with two complete solids.
        film = Compound([Box(2, 3, 1), Cylinder(0.7, 3).translate((2, 0, 1))],
                        label=f'film_{index}')
        film.location = Location((0, 2, 1), (23, 11, 7))
        marker = Box(1, 2, 3)
        marker.label = f'marker_{index}'
        marker.color = Color(0.2, 0.7, 0.1, 1)
        marker.location = Location((-3, 0, 2), (13, 21, 29))
        group = Compound(children=[film, marker], label=f'group_{index}')
        group.color = Color(0.7, 0.1, 0.2, 0.4)
        group.location = Location((index * 9, index % 2 * 8, 0), (0, 0, index * 17))
        groups.append(group)
    root = Compound(children=groups, label='root')
    root.location = Location((11, -5, 8), (31, -7, 19))
    return root


class RenderAssemblyPlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = runpy.run_path(str(SCRIPTS / 'render_assembly.py'))
        cls.product = runpy.run_path(str(SCRIPTS / 'render_product'))
        cls.review = runpy.run_path(str(SCRIPTS / 'render_review'))

    def product_scene(self, shape, old=False):
        replacements = {'_build_shape': lambda _: shape}
        if old:
            replacements['_colored_leaves'] = old_colored_leaves
        with mock.patch.dict(self.product['load_scene'].__globals__, replacements):
            return self.product['load_scene'](Path('synthetic.step'))

    def review_scene(self, shape, old=False):
        replacements = {'_leaves': old_review_leaves} if old else {}
        with mock.patch.dict(self.review['tessellate_occurrences'].__globals__, replacements):
            return self.review['tessellate_occurrences'](shape, 0.08)

    def assert_exact_scene(self, shape):
        expected_triangles, expected_colors = self.product_scene(shape, old=True)
        triangles, colors = self.product_scene(shape)
        np.testing.assert_array_equal(triangles, expected_triangles)
        np.testing.assert_array_equal(colors, expected_colors)
        expected_occurrences = self.review_scene(shape, old=True)
        occurrences = self.review_scene(shape)
        self.assertEqual(len(occurrences), len(expected_occurrences))
        for actual, expected in zip(occurrences, expected_occurrences):
            np.testing.assert_array_equal(actual[0], expected[0])
            np.testing.assert_array_equal(actual[1], expected[1])
            self.assertEqual(actual[2], expected[2])
        return (triangles, colors), (expected_triangles, expected_colors), occurrences, expected_occurrences

    def test_nested_rotations_bare_compounds_colors_and_pngs_are_exact(self):
        actual, expected, occurrences, expected_occurrences = self.assert_exact_scene(scene())
        self.assertEqual(len(occurrences), 8)
        self.assertIn(0.4, set(actual[1][:, 3]))
        style = dict(size=180, view='iso', base=(40, 160, 160), accent=(240, 160, 70),
                     background=(250, 240, 220))
        np.testing.assert_array_equal(
            np.asarray(self.product['render'](actual[0], triangle_colors=actual[1], **style)),
            np.asarray(self.product['render'](expected[0], triangle_colors=expected[1], **style)))
        np.testing.assert_array_equal(
            np.asarray(self.review['render'](occurrences, -45, 35.264, 180, 0.07)),
            np.asarray(self.review['render'](expected_occurrences, -45, 35.264, 180, 0.07)))

    def test_step_import_has_exact_geometry_and_color_without_file_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'synthetic.step'
            export_step(scene(2), path)
            before = path.read_bytes()
            loaded = import_step(path)
            self.assert_exact_scene(loaded)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temporary).iterdir()), [path])

    def test_no_deepcopy_and_no_source_hierarchy_or_location_mutation(self):
        assembly = scene(6)
        nodes = [assembly, *assembly.descendants]
        before = [(id(node.parent), tuple(node.location), tuple(node.color)
                   if node.color is not None else None) for node in nodes]
        with mock.patch.object(Shape, '__deepcopy__', side_effect=AssertionError('assembly copied')):
            leaves = list(self.helper['colored_leaves'](assembly))
            self.product_scene(assembly)
            self.review_scene(assembly)
        self.assertEqual(len(leaves), 12)
        for leaf, _color in leaves:
            self.assertIsNone(leaf.parent)
            self.assertFalse(getattr(leaf, 'children', ()))
        self.assertEqual([len(leaf.solids()) for leaf, _ in leaves], [2, 1] * 6)
        after = [(id(node.parent), tuple(node.location), tuple(node.color)
                  if node.color is not None else None) for node in nodes]
        self.assertEqual(after, before)

    def test_exact_native_identity_orientation_and_detached_location(self):
        assembly = scene(2)
        # Preserve orientation too; do not replace it by a newly built solid.
        assembly.children[0].children[0].wrapped.Reverse()
        expected = list(old_colored_leaves(assembly))
        actual = list(self.helper['colored_leaves'](assembly))
        for (leaf, color), (previous, previous_color) in zip(actual, expected):
            self.assertTrue(leaf.wrapped.IsEqual(previous.wrapped))
            self.assertEqual(tuple(color), tuple(previous_color))
        source_leaf = assembly.children[0].children[0]
        original_location = tuple(source_leaf.location)
        actual[0][0].wrapped.Location(Location((99, 88, 77)).wrapped)
        self.assertEqual(tuple(source_leaf.location), original_location)

    def test_single_root_leaf_keeps_own_pose_and_fallback_pixels(self):
        root = Box(2, 3, 4)
        root.location = Location((11, 21, 31), (13, 23, 33))
        actual, expected, _, _ = self.assert_exact_scene(root)
        self.assertTrue(np.all(actual[1][:, :3] == -1))
        leaf, color = next(self.helper['colored_leaves'](root))
        self.assertIsNone(color)
        self.assertTrue(root.wrapped.IsEqual(leaf.wrapped))
        leaf.wrapped.Location(Location().wrapped)
        np.testing.assert_array_equal(actual[0], expected[0])
        self.assertNotEqual(tuple(root.location), tuple(leaf.location))

    def test_tessellation_failure_is_not_replaced_with_partial_scene(self):
        assembly = scene(2)
        with mock.patch.object(Shape, 'tessellate', side_effect=RuntimeError('injected failure')):
            for load in (self.product_scene, self.review_scene):
                with self.assertRaisesRegex(RuntimeError, 'injected failure'):
                    load(assembly)


if __name__ == '__main__':
    unittest.main()
