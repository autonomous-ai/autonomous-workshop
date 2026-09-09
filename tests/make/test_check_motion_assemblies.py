"""Motion checks must measure the same solids in equivalent assembly trees."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

from build123d import Box, Compound, Location

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class MotionAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    @staticmethod
    def box(label, center=(0, 0, 0)):
        shape = Box(2, 2, 2).translate(center)
        shape.label = label
        return shape

    def test_grouped_and_wrapped_solids_have_the_same_collision(self):
        obstacle = self.box('obstacle', (0, 3, 0))
        for hierarchy in (False, True):
            leaf = self.box('pin')
            group = Compound(children=[leaf], label='rotor') if hierarchy else Compound([leaf], label='rotor')
            moved = group.translate((0, 3, 0))
            with self.subTest(hierarchy=hierarchy):
                self.assertAlmostEqual(self.tool['overlap_volume'](moved, obstacle), 8)

    def test_grouped_obstacles_have_the_same_collision(self):
        obstacle = Compound(children=[self.box('wall', (0, 3, 0))], label='frame')
        self.assertAlmostEqual(self.tool['overlap_volume'](self.box('pin', (0, 3, 0)), obstacle), 8)

    def test_separated_groups_stay_clear(self):
        first = Compound(children=[self.box('first')], label='first_group')
        second = Compound(children=[self.box('second', (20, 0, 0))], label='second_group')
        self.assertEqual(self.tool['overlap_volume'](first, second), 0)

    def nested_assembly(self):
        pin = self.box('pin', (2, 0, 0))
        module = Compound(children=[pin], label='module')
        module.location = Location((10, 0, 0), (0, 0, 90))
        root = Compound(children=[module], label='root')
        root.location = Location((0, 20, 0), (0, 0, 90))
        return root

    def test_named_leaf_and_module_include_all_ancestor_placements(self):
        parts = self.tool['index_parts'](self.nested_assembly())
        # (2,0) becomes (10,2) in the module, then (-2,30) at the root.
        expected = self.box('expected', (-2, 30, 0))
        for name in ('pin', 'module', 'root.module.pin', 'root.module'):
            with self.subTest(name=name):
                self.assertAlmostEqual(self.tool['overlap_volume'](parts[name], expected), 8)
                self.assertAlmostEqual(parts[name].bounding_box().center().X, -2)
                self.assertAlmostEqual(parts[name].bounding_box().center().Y, 30)

    def test_nested_leaf_does_not_leave_a_collision_at_its_local_position(self):
        parts = self.tool['index_parts'](self.nested_assembly())
        self.assertEqual(self.tool['overlap_volume'](parts['pin'], self.box('local', (2, 0, 0))), 0)

    def test_group_translation_reports_barrier_for_both_expectations(self):
        rotor = Compound(children=[self.box('pin')], label='rotor')
        model = Compound(children=[rotor, self.box('wall', (5, 0, 0))], label='root')
        parts = self.tool['index_parts'](model)
        for expect, status in [('clear', 'fail'), ('blocked', 'pass')]:
            condition = {'id': 'slide', 'check': 'linear_motion_collision', 'expect': expect,
                         'inputs': {'moving_part': 'rotor', 'obstacle_parts': ['wall'],
                                    'translation': [10, 0, 0], 'steps': 20}}
            with self.subTest(expect=expect):
                result = self.tool['run_condition'](condition, parts, 0)
                self.assertEqual(result['status'], status, result)
                self.assertGreater(result['overlapMm3'], .001)

    def test_group_rotation_hits_a_stationary_obstacle(self):
        rotor = Compound(children=[self.box('pin', (5, 0, 0))], label='rotor')
        model = Compound(children=[rotor, self.box('wall', (0, 5, 0))], label='root')
        condition = {'id': 'turn', 'check': 'coupled_motion_collision', 'expect': 'clear',
                     'inputs': {'steps': 18, 'movers': [{'part': 'rotor', 'rotation': {
                         'axis_point': [0, 0, 0], 'axis_direction': [0, 0, 1],
                         'start_deg': 0, 'end_deg': 90}}], 'obstacle_parts': ['wall']}}
        result = self.tool['run_condition'](condition, self.tool['index_parts'](model), 0)
        self.assertEqual(result['status'], 'fail', result)
        self.assertGreater(result['overlapMm3'], .001)

    def test_indexing_keeps_original_assembly_placements(self):
        model = self.nested_assembly()
        before = [(node.label, tuple(node.position), tuple(node.orientation)) for node in [model, *model.descendants]]
        self.tool['index_parts'](model)
        after = [(node.label, tuple(node.position), tuple(node.orientation)) for node in [model, *model.descendants]]
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
