"""Parallel geometry preserves B-reps and ordered fail-closed results."""
from pathlib import Path
import multiprocessing
import runpy
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from build123d import Box, Compound, Location

SCRIPTS = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts'
sys.path.insert(0, str(SCRIPTS))
import motion_parallel


class MotionParallelTests(unittest.TestCase):
    def setUp(self):
        self.existing_children = {child.pid for child in multiprocessing.active_children()}

    def tearDown(self):
        added = [child for child in multiprocessing.active_children()
                 if child.pid not in self.existing_children]
        self.assertEqual(added, [], 'parallel sweep returned before reaping children')

    def test_worker_retains_bounded_material_scope_across_poses(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.brep', Path(directory) / 'b.brep'
            motion_parallel._write_shape(Box(2, 2, 2), a)
            motion_parallel._write_shape(Box(2, 2, 2).translate((20, 0, 0)), b)
            motion_parallel._initialize(str(SCRIPTS / 'check_motion'),
                [('a', str(a), {'translation': {'vector': [0, 0, 0]}})],
                [('b', str(b))], 1, .001)
            try:
                self.assertEqual(motion_parallel._pose(0), {'hit': None})
                self.assertEqual(motion_parallel._pose(1), {'hit': None})
                tool = motion_parallel._STATE[0]
                cache = tool['_MATERIAL'].get()
                self.assertEqual(cache.checks, 2)
                self.assertEqual(cache.hits, 2)
            finally:
                motion_parallel._STATE[-1].__exit__(None, None, None)
                motion_parallel._STATE = None

    def test_binary_roundtrip_retains_precise_placement_and_volume(self):
        shape = Location((1.234567890123456, -17.654321098765432, 3), (13, 27, 49)) * Box(2, 4, 6)
        group = Compound(children=[shape, Box(1, 2, 3).translate((50, 0, 0))])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'model.brep'
            motion_parallel._write_shape(group, path)
            restored = motion_parallel._read_shape(path)
        self.assertEqual(len(restored.solids()), 2)
        for original, copy in zip(group.solids(), restored.solids()):
            self.assertEqual(original.volume, copy.volume)
            for actual, expected in zip(original.position, copy.position):
                self.assertAlmostEqual(actual, expected, places=12)
            self.assertEqual(original.wrapped.Orientation(), copy.wrapped.Orientation())
            for corner in ("min", "max"):
                for actual, expected in zip(getattr(original.bounding_box(), corner),
                                            getattr(copy.bounding_box(), corner)):
                    self.assertAlmostEqual(actual, expected, places=12)

    def test_real_process_sweep_matches_serial_first_collision_and_pairs(self):
        tool = runpy.run_path(str(SCRIPTS / 'check_motion'))
        spec = {'translation': {'vector': [6, 0, 0]}}
        movers = [('a', Box(2, 2, 2), spec),
                  ('b', Box(2, 2, 2).translate((100, 0, 0)), spec)]
        obstacles = [('first', Box(2, 2, 2).translate((5, 0, 0))),
                     ('second', Box(2, 2, 2).translate((5, 0, 0)))]
        serial = tool['check_coupled'](
            {'movers': [dict(spec, part=name) for name, _, spec in movers],
             'obstacle_parts': [name for name, _ in obstacles], 'steps': 6},
            {}, dict([(name, shape) for name, shape, _ in movers] + obstacles))
        advanced = []
        hit = motion_parallel.sweep(SCRIPTS / 'check_motion', movers, obstacles,
                                    6, 0, .001, 2, time.monotonic() + 30,
                                    lambda: advanced.append(True))
        self.assertEqual(hit['step'], serial['step'])
        self.assertEqual(' x '.join(hit['between']), serial['obstacle'])
        self.assertEqual(hit['overlapMm3'], serial['overlapMm3'])
        self.assertEqual(len(advanced), hit['step'])

    def test_real_process_clear_sweep_visits_all_nonseated_samples(self):
        advanced = []
        hit = motion_parallel.sweep(
            SCRIPTS / 'check_motion',
            [('a', Box(2, 2, 2), {'translation': {'vector': [1, 0, 0]}})],
            [('distant', Box(2, 2, 2).translate((20, 0, 0)))],
            3, 1, .001, 2, time.monotonic() + 30,
            lambda: advanced.append(True))
        self.assertIsNone(hit)
        self.assertEqual(len(advanced), 3)

    def fake_tool(self, directory, earlier):
        path = Path(directory) / 'tool.py'
        path.write_text(
            'from contextlib import nullcontext\n'
            'import time\n'
            'validation_scope = nullcontext\n'
            'def decision_scope(tolerance): return nullcontext()\n'
            'def _pose_table(spec, steps, field):\n'
            '    return lambda shape, step: shape.translate((step * 10, 0, 0))\n'
            'def overlap_volume(a, b):\n'
            '    step = round(a.bounding_box().center().X / 10)\n'
            '    if step == 0:\n'
            '        time.sleep(.2)\n' +
            ('        raise ValueError("earlier failure")\n' if earlier == 'error' else
             '        return 8.0\n') +
            '    if step == 1: raise ValueError("later failure")\n'
            '    time.sleep(10)\n'
            '    return 0.0\n')
        return path

    def test_later_worker_error_cannot_replace_earlier_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            hit = motion_parallel.sweep(
                self.fake_tool(directory, 'hit'), [('a', Box(2, 2, 2), {})],
                [('b', Box(2, 2, 2))], 5, 0, .001, 2,
                time.monotonic() + 30, lambda: self.fail('collision advanced'))
        self.assertEqual(hit['step'], 0)
        self.assertEqual(hit['between'], ['a', 'b'])

    def test_earliest_worker_error_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(motion_parallel.GeometryError, 'ValueError: earlier failure'):
                motion_parallel.sweep(
                    self.fake_tool(directory, 'error'), [('a', Box(2, 2, 2), {})],
                    [('b', Box(2, 2, 2))], 5, 0, .001, 2,
                    time.monotonic() + 30, lambda: self.fail('error advanced'))

    def test_deadline_terminates_pending_workers_and_bounds_submission(self):
        class Pending:
            def result(self, timeout=None):
                raise TimeoutError('waiting')
        class Executor:
            def __init__(self, **kwargs):
                self.terminated = False
                self.submitted = 0
            def submit(self, *args):
                self.submitted += 1
                return Pending()
            def terminate_workers(self):
                self.terminated = True
        executor = Executor()
        with patch.object(motion_parallel, 'ProcessPoolExecutor', return_value=executor) as factory:
            factory.terminate_workers = True
            with self.assertRaises(TimeoutError):
                motion_parallel.sweep('unused', [], [], 100, 0, .001, 2,
                                      time.monotonic() + 30, lambda: None)
        self.assertTrue(executor.terminated)
        self.assertEqual(executor.submitted, 4)

    def test_callback_cancellation_terminates_workers(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = Path(directory) / 'tool.py'
            tool.write_text(
                'from contextlib import nullcontext\n'
                'import time\n'
                'validation_scope = nullcontext\n'
                'def decision_scope(tolerance): return nullcontext()\n'
                'def _pose_table(spec, steps, field):\n'
                '    return lambda shape, step: shape.translate((step * 10, 0, 0))\n'
                'def overlap_volume(a, b):\n'
                '    if a.bounding_box().center().X > 5: time.sleep(10)\n'
                '    return 0.0\n')
            def cancel():
                raise RuntimeError('cancel requested')
            with self.assertRaisesRegex(RuntimeError, 'cancel requested'):
                motion_parallel.sweep(tool, [('a', Box(2, 2, 2), {})],
                                      [('b', Box(2, 2, 2))], 5, 0, .001, 2,
                                      time.monotonic() + 30, cancel)


if __name__ == '__main__':
    unittest.main()
