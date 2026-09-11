"""Copy selected assembly geometry without retaining or copying its parent graph."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Box, Color, Compound, Cylinder, Location, Shape, import_step


SCRIPTS = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts'
copy_subtree = runpy.run_path(str(SCRIPTS / 'packages/cadgen/src/cadgen/assembly.py'))['copy_subtree']


def scene():
    prototype = Compound([Box(2, 3, 1), Cylinder(0.7, 3).translate((3, 0, 1))])
    leaves = []
    for index in range(2):
        leaf = Compound.cast(prototype.wrapped.Located(prototype.wrapped.Location()))
        leaf.label = f'shared_{index}'
        leaf.location = Location((index * 8, 2, 1), (23, 11, 7 + index * 19))
        leaves.append(leaf)
    marker = Box(1, 2, 3)
    marker.label = 'marker'
    marker.color = Color(0.2, 0.7, 0.1, 0.8)
    marker.location = Location((-3, 0, 2), (13, 21, 29))
    group = Compound(children=leaves, label='nested')
    group.location = Location((2, 4, -1), (19, 17, 31))
    selected = Compound(children=[group, marker], label='selected')
    selected.location = Location((9, 8, 7), (31, -7, 19))
    sibling = Box(500, 500, 500)
    sibling.label = 'unselected_sibling'
    root = Compound(children=[selected, sibling], label='external_root')
    root.color = Color(0.7, 0.1, 0.2, 0.4)
    root.location = Location((100, 200, 300), (11, 29, 53))
    return root, selected


def snapshot(root):
    return [(id(node), id(node.parent), tuple(id(child) for child in getattr(node, 'children', ())),
             None if node._wrapped is None else node.wrapped.Located(node.wrapped.Location()),
             node.label, None if node._color is None else tuple(node._color))
            for node in [root, *root.descendants]]


class CopySubtreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = runpy.run_path(str(SCRIPTS / 'render_product'))
        cls.product['_runtime_paths']()
        from cadgen.step_export import export_build123d_step_file
        from render_assembly import colored_leaves
        cls.export = staticmethod(export_build123d_step_file)
        cls.leaves = staticmethod(colored_leaves)

    def assert_snapshot(self, root, expected):
        actual = snapshot(root)
        self.assertEqual(len(actual), len(expected))
        for after, before in zip(actual, expected):
            self.assertEqual(after[:3], before[:3])
            self.assertEqual(after[4:], before[4:])
            if before[3] is None:
                self.assertIsNone(after[3])
            else:
                self.assertTrue(after[3].IsEqual(before[3]))

    def product_scene(self, shape):
        with mock.patch.dict(self.product['load_scene'].__globals__, {'_build_shape': lambda _: shape}):
            return self.product['load_scene'](Path('synthetic.step'))

    def test_nested_local_placements_hierarchy_labels_and_native_topology_are_exact(self):
        root, selected = scene()
        before = snapshot(root)
        cloned = copy_subtree(selected)
        self.assertIsNone(cloned.parent)
        originals = [selected, *selected.descendants]
        copies = [cloned, *cloned.descendants]
        self.assertEqual(len(copies), 5)
        self.assertEqual([node.label for node in copies], [node.label for node in originals])
        self.assertEqual([len(getattr(node, 'children', ())) for node in copies], [2, 2, 0, 0, 0])
        self.assertEqual(cloned.children[0].parent, cloned)
        self.assertEqual(cloned.children[0].children[0].parent, cloned.children[0])
        for original, replica in zip(originals, copies):
            self.assertIsNot(original, replica)
            self.assertIsNot(original.wrapped, replica.wrapped)
            self.assertTrue(original.wrapped.IsEqual(replica.wrapped))
            self.assertEqual(tuple(original.location), tuple(replica.location))
            self.assertEqual(len(original.solids()), len(replica.solids()))
            self.assertAlmostEqual(original.volume, replica.volume, places=9)
        first, second = cloned.children[0].children
        self.assertTrue(first.wrapped.IsPartner(second.wrapped))
        self.assert_snapshot(root, before)

    def test_no_copy_protocol_parent_joint_or_custom_metadata_traversal(self):
        root, selected = scene()
        class Bomb:
            def __copy__(self):
                raise AssertionError('unexpected metadata copy')
            def __deepcopy__(self, memo):
                raise AssertionError('unexpected metadata deepcopy')
        root.joints['outside'] = Bomb()
        selected.joints['external_joint'] = Bomb()
        selected.custom_metadata = Bomb()
        selected.topo_parent = root.children[1]
        before = snapshot(root)
        with mock.patch.object(Shape, '__copy__', side_effect=AssertionError('Shape copied')):
            with mock.patch.object(Shape, '__deepcopy__', side_effect=AssertionError('Shape deepcopied')):
                cloned = copy_subtree(selected)
        self.assertEqual(cloned.joints, {})
        self.assertIsNone(cloned.topo_parent)
        self.assertFalse(hasattr(cloned, 'custom_metadata'))
        self.assertNotIn('unselected_sibling', [node.label for node in cloned.descendants])
        self.assertFalse({id(node) for node in [root, *root.descendants]} &
                         {id(node) for node in [cloned, *cloned.descendants]})
        self.assert_snapshot(root, before)

    def test_inherited_color_is_snapshotted_without_mutating_source(self):
        root, selected = scene()
        before = snapshot(root)
        cloned = copy_subtree(selected)
        self.assertIsNone(selected._color)
        self.assertEqual(tuple(cloned.color), tuple(root._color))
        self.assertEqual(tuple(cloned.children[0].children[0].color), tuple(root._color))
        np.testing.assert_allclose(tuple(cloned.children[1].color), (.2, .7, .1, .8), atol=1e-7)
        self.assert_snapshot(root, before)
        self.assertIsNot(cloned.color.wrapped, root._color.wrapped)
        cloned.color.wrapped.SetAlpha(0.2)
        cloned.children[1].color.wrapped.SetAlpha(0.3)
        self.assert_snapshot(root, before)
        cloned.color = Color(0.9, 0.5, 0.1, 0.6)
        cloned.children[1].color = None
        self.assert_snapshot(root, before)

    def test_changing_clone_pose_orientation_and_hierarchy_does_not_change_source(self):
        root, selected = scene()
        before = snapshot(root)
        cloned = copy_subtree(selected)
        cloned.location = Location((90, 80, 70), (13, 17, 23))
        cloned.wrapped.Reverse()
        leaf = cloned.children[0].children[0]
        leaf.location = Location((30, 40, 50))
        leaf.wrapped.Reverse()
        leaf.parent = None
        self.assert_snapshot(root, before)

    def test_exact_render_arrays_and_png_match_selected_source(self):
        _, selected = scene()
        cloned = copy_subtree(selected)
        actual_triangles, actual_colors = self.product_scene(cloned)
        expected_triangles, expected_colors = self.product_scene(selected)
        np.testing.assert_array_equal(actual_triangles, expected_triangles)
        np.testing.assert_array_equal(actual_colors, expected_colors)
        style = dict(size=180, view='iso', base=(40, 160, 160), accent=(240, 160, 70),
                     background=(250, 240, 220))
        np.testing.assert_array_equal(
            np.asarray(self.product['render'](actual_triangles, triangle_colors=actual_colors, **style)),
            np.asarray(self.product['render'](expected_triangles, triangle_colors=expected_colors, **style)))

    def test_step_roundtrip_preserves_selected_occurrences_geometry_and_rgba(self):
        root, selected = scene()
        # Shared definitions use one label; occurrence-specific labels can live
        # on parent nodes. STEP readers may take labels from the definition.
        for leaf in selected.children[0].children:
            leaf.label = 'shared_piece'
        before = snapshot(root)
        cloned = copy_subtree(selected)
        # STEP's exported assembly root is a definition frame; place the selected
        # subtree as an occurrence beneath an identity root to retain its pose.
        exported = Compound(children=[cloned], label='selection_export')
        expected = list(self.leaves(exported))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'selected.step'
            self.export(exported, path, text_to_cad_entry_kind='assembly')
            loaded = import_step(path)
            actual = list(self.leaves(loaded))
        self.assertEqual(len(actual), 3)
        self.assertEqual([node.label for node in [loaded, *loaded.descendants]],
                         [node.label for node in [exported, *exported.descendants]])
        for (actual_part, actual_color), (expected_part, expected_color) in zip(actual, expected):
            np.testing.assert_allclose(tuple(actual_color), tuple(expected_color), rtol=0, atol=1e-7)
            self.assertEqual(len(actual_part.solids()), len(expected_part.solids()))
            self.assertAlmostEqual(actual_part.volume, expected_part.volume, places=8)
            for bound in ('min', 'max'):
                np.testing.assert_allclose(tuple(getattr(actual_part.bounding_box(), bound)),
                                           tuple(getattr(expected_part.bounding_box(), bound)), rtol=0, atol=1e-7)
        self.assert_snapshot(root, before)

    def test_single_leaf_empty_uncolored_and_invalid_input(self):
        leaf = Box(2, 3, 4)
        leaf.location = Location((11, 21, 31), (13, 23, 33))
        leaf.wrapped.Reverse()
        replica = copy_subtree(leaf)
        self.assertTrue(replica.wrapped.IsEqual(leaf.wrapped))
        self.assertIsNone(replica.color)
        self.assertIsNone(replica.parent)
        empty = Compound(label='empty', color=Color(.1, .2, .3, .4))
        cloned_empty = copy_subtree(empty)
        self.assertIsNone(cloned_empty._wrapped)
        self.assertEqual(cloned_empty.label, 'empty')
        self.assertEqual(tuple(cloned_empty.color), tuple(empty.color))
        with self.assertRaisesRegex(TypeError, 'build123d Shape'):
            copy_subtree(object())


if __name__ == '__main__':
    unittest.main()
