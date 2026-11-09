"""A rigid mover is fused once per condition, never once per pose, and the
verdicts are those of fusing it at every pose."""
from __future__ import annotations

import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from unittest.mock import patch

from build123d import Box, Compound

_loader = SourceFileLoader(
    'rigid_material_motion_under_test',
    str(Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts/check_motion'))
_spec = spec_from_loader(_loader.name, _loader)
motion = module_from_spec(_spec)
_loader.exec_module(motion)


def box(label, center, size=(2, 2, 2)):
    shape = Box(*size).translate(center)
    shape.label = label
    return shape


def figure():
    """Two overlapping bodies moving as one, like a figure's body and arm."""
    return Compound(children=[box('body', (0, 0, 0), (4, 2, 2)), box('arm', (2, 0, 0), (2, 2, 2))],
                    label='figure')


def assembly(wall_x):
    root = Compound(children=[figure(), box('wall', (wall_x, 0, 0))], label='root')
    return motion.index_parts(root)


def rotation_condition(steps):
    return {'id': 'swing', 'check': 'rotation_motion_collision', 'expect': 'clear',
            'inputs': {'moving_part': 'figure', 'obstacle_parts': ['wall'], 'axis_point': [0, 0, 0],
                       'axis_direction': [0, 0, 1], 'start_deg': 0, 'end_deg': 180, 'steps': steps}}


def coupled_condition(steps):
    return {'id': 'swing', 'check': 'coupled_motion_collision', 'expect': 'clear',
            'inputs': {'steps': steps, 'obstacle_parts': ['wall'],
                       'movers': [{'part': 'figure', 'rotation': {'axis_point': [0, 0, 0], 'axis_direction': [0, 0, 1],
                                                                  'start_deg': 0, 'end_deg': 180}}]}}


class RigidMaterialTests(unittest.TestCase):
    def test_a_single_solid_is_returned_unfused(self):
        solid = box('pin', (0, 0, 0))
        with patch.object(motion, '_material', wraps=motion._material) as prepare:
            self.assertIs(motion.rigid_material(solid), solid)
            self.assertEqual(prepare.call_count, 0)

    def test_the_fused_group_has_the_union_volume(self):
        fused = motion.rigid_material(figure())
        self.assertEqual(len(fused.solids()), 1)
        self.assertAlmostEqual(sum(s.volume for s in fused.solids()), 4 * 2 * 2 + 1 * 2 * 2)

    def test_each_sweep_fuses_its_group_once_however_many_poses(self):
        for name, condition in (('rotation', rotation_condition), ('coupled', coupled_condition)):
            fuses = []
            for steps in (4, 12):
                with patch.object(motion, 'rigid_material', wraps=motion.rigid_material) as rigid, \
                        patch.object(motion, '_material', wraps=motion._material) as prepare:
                    with motion.validation_scope():
                        motion.run_condition(condition(steps), assembly(30), 0)
                    self.assertEqual(rigid.call_count, 1, name)
                    fuses.append(sum(1 for call in prepare.call_args_list
                                     if len(list(call.args[0].solids())) > 1))
            with self.subTest(check=name):
                self.assertEqual(fuses, [1, 1])

    def test_verdicts_are_those_of_the_unfused_group(self):
        # The arm reaches x = 3; a wall at x = -3.5 is met only when the arm swings round.
        for name, condition in (('rotation', rotation_condition), ('coupled', coupled_condition)):
            for wall_x, clear in ((30, True), (-3.5, False)):
                with self.subTest(check=name, wall_x=wall_x):
                    result = motion.run_condition(condition(12), assembly(wall_x), 0)
                    self.assertEqual(result['clear'],
                                     clear, result)


if __name__ == '__main__':
    unittest.main()
