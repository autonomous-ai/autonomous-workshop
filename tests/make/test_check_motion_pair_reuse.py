"""Repeated pose pairs keep exact outcomes and first-collision ordering."""
import inspect
import time
import unittest
from unittest.mock import patch
from build123d import Box, Location
from tests.make.test_check_motion_material_cache import motion


class PairReuseTests(unittest.TestCase):
    def condition(self):
        return {"id": "sequential-controls", "check": "coupled_motion_collision",
                "inputs": {"steps": 12, "obstacle_parts": ["frame"], "movers": [
                    {"part": "moving", "translation": {"vector": [6, 0, 0]}},
                    {"part": "held", "translation": {"vector": [0, 0, 0]}},
                    {"part": "held2", "translation": {"vector": [0, 0, 0]}}]}}

    def test_exact_results_and_less_boolean_work_for_held_pairs(self):
        # Execute the same handler with only memoized calls replaced by the
        # original measurement, retaining every loop, sample and threshold.
        source = inspect.getsource(motion.check_coupled)
        source = source.replace("measured_pair((pair, second), posed[pair][1], posed[second][1])", "overlap_volume(posed[pair][1], posed[second][1])")
        source = source.replace("measured_pair((pair, len(posed) + obstacle_index), posed[pair][1], obstacle)", "overlap_volume(posed[pair][1], obstacle)")
        namespace = dict(motion.__dict__)
        exec(source, namespace)
        baseline = namespace['check_coupled']
        for blocked in (False, True):
            parts = {"moving": Box(2,2,2), "held": Box(2,2,2).moved(Location((0,8,0))),
                     "held2": Box(2,2,2).moved(Location((0,16,0))),
                     "frame": Box(2,2,2).moved(Location((5 if blocked else 20,0,0)))}
            condition = self.condition()
            actual_overlap = motion.overlap_volume
            measurements = []
            for handler in (baseline, motion.check_coupled):
                with patch.object(motion, 'overlap_volume', wraps=actual_overlap) as measured:
                    namespace['overlap_volume'] = measured
                    with motion.validation_scope(), motion.decision_scope(1.0):
                        result = handler(condition['inputs'], {}, parts)
                    measurements.append((result, measured.call_count))
            self.assertEqual(measurements[0][0], measurements[1][0])
            self.assertLess(measurements[1][1], measurements[0][1])
            if not blocked:
                self.assertEqual(measurements[0][1], 78)
                self.assertEqual(measurements[1][1], 42)

    def test_changed_pose_is_measured_and_failure_is_not_hidden(self):
        parts = {"moving": Box(2,2,2), "held": Box(2,2,2).moved(Location((0,8,0))),
                 "held2": Box(2,2,2).moved(Location((0,16,0))),
                 "frame": Box(2,2,2).moved(Location((20,0,0)))}
        original = motion.overlap_volume
        def measure(a,b):
            if a.center().X > 2: raise ValueError('changed pose failure')
            return original(a,b)
        with patch.object(motion, 'overlap_volume', side_effect=measure):
            result = motion.run_condition(self.condition(), parts, 0)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertIn('changed pose failure', str(result))
