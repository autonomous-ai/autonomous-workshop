"""Exact placed material reuse must preserve every sampled motion decision."""
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import unittest
from unittest.mock import patch

from build123d import Box, Compound, Location


_loader = SourceFileLoader(
    'material_cached_motion_under_test',
    str(Path(__file__).resolve().parents[2]
        / 'src/workshop/make/skills/cad/scripts/check_motion'))
_spec = spec_from_loader(_loader.name, _loader)
motion = module_from_spec(_spec)
_loader.exec_module(motion)


class MaterialCacheTests(unittest.TestCase):
    @staticmethod
    def group():
        return Compound([Box(2, 2, 2), Box(2, 2, 2).translate((1, 0, 0))])

    def test_placed_identity_includes_topology_location_and_orientation(self):
        shape = self.group()
        cache = motion.MaterialCache()
        first = cache.material(shape)
        equivalent = Compound(shape.wrapped.Located(shape.wrapped.Location()))
        self.assertIs(cache.material(equivalent), first)
        moved = shape.moved(Location((13, 5, -7), (17, 31, 43)))
        actual = cache.material(moved)
        self.assertAlmostEqual(actual[1], first[1])
        self.assertAlmostEqual((actual[0].center() - moved.center()).length, 0)
        cache.material(self.group())
        # Reversed topology can have a negative volume, so isolate key routing
        # from the intentionally unchanged normalization validity requirements.
        with patch.object(motion, '_normalize_material', return_value=first) as normalize:
            cache.material(Compound(shape.wrapped.Reversed()))
        self.assertEqual(normalize.call_count, 1)
        self.assertEqual(cache.misses, 4)
        self.assertEqual(cache.hits, 1)

    def test_key_snapshot_does_not_follow_mutated_wrapper_placement(self):
        for shape in (self.group(), Box(2, 2, 2)):
            with self.subTest(solids=len(shape.solids())):
                cache = motion.MaterialCache()
                original = cache.material(shape)
                original_key = shape.wrapped.Located(shape.wrapped.Location())
                original_center = original[0].center().X
                shape.wrapped.Location(Location((20, 0, 0)).wrapped)
                placed = cache.material(shape)
                self.assertEqual(cache.misses, 2)
                self.assertEqual(original[0].center().X, original_center)
                self.assertAlmostEqual(placed[0].center().X - original_center, 20)
                self.assertIs(cache.material(Compound(original_key)), original)

    def test_hash_collision_does_not_reuse_other_topology(self):
        with patch.object(motion, 'hash', return_value=0, create=True):
            cache = motion.MaterialCache()
            self.assertAlmostEqual(cache.material(Box(2, 2, 2))[1], 8)
            self.assertAlmostEqual(cache.material(Box(3, 3, 3))[1], 27)
            self.assertEqual(cache.misses, 2)

    def test_failure_is_never_cached_and_changed_pose_still_fails(self):
        shape = self.group()
        moved = shape.moved(Location((0.5, 0, 0)))
        cache = motion.MaterialCache()
        first = cache.material(shape)
        with patch.object(motion, '_normalize_material',
                          side_effect=ValueError('injected pose-specific failure')) as normalize:
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, 'pose-specific'):
                    cache.material(moved)
            self.assertIs(cache.material(shape), first)
        self.assertEqual(normalize.call_count, 2)
        self.assertEqual(len(cache.entries), 1)

    def test_empty_operand_keeps_existing_failure(self):
        with motion.validation_scope():
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, 'contains no solid'):
                    motion._material(Compound([]))
            self.assertEqual(len(motion._MATERIALS.get().entries), 0)

    def test_nested_scope_shares_cache_and_exception_discards_it(self):
        shape = self.group()
        with patch.object(motion, '_normalize_material', wraps=motion._normalize_material) as normalize:
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                with motion.validation_scope():
                    outer = motion._MATERIALS.get()
                    motion._material(shape)
                    with motion.validation_scope():
                        self.assertIs(motion._MATERIALS.get(), outer)
                        motion._material(shape)
                    raise RuntimeError('injected')
            self.assertIsNone(motion._MATERIALS.get())
            with motion.validation_scope():
                self.assertIsNot(motion._MATERIALS.get(), outer)
                motion._material(shape)
            self.assertEqual(normalize.call_count, 2)

    def test_capacity_is_bounded_and_recent_fixed_shape_survives(self):
        fixed = self.group()
        cache = motion.MaterialCache()
        with patch.object(motion, '_MAX_MATERIAL_CACHE_ENTRIES', 2):
            first = cache.material(fixed)
            for offset in range(1, 6):
                cache.material(fixed.moved(Location((offset, 0, 0))))
                self.assertIs(cache.material(fixed), first)
                self.assertLessEqual(len(cache.entries), 2)
            # The first transient pose was evicted and must be normalized anew.
            cache.material(fixed.moved(Location((1, 0, 0))))
            self.assertEqual(cache.misses, 7)
            self.assertEqual(cache.hits, 5)

    def test_clear_sweep_reuses_work_without_changing_samples_or_result(self):
        parts = {'moving': self.group(), 'frame': self.group().translate((0, 0, 5)),
                 'rail': self.group().translate((0, 0, -5)),
                 'cap': self.group().translate((0, 20, 0))}
        condition = {'id': 'multipart_stroke', 'check': 'linear_motion_collision',
                     'inputs': {'moving_part': 'moving',
                                'obstacle_parts': ['frame', 'rail', 'cap'],
                                'translation': [4, 0, 0], 'steps': 4}}
        actual_material = motion._material
        actual_overlap = motion.overlap_volume
        runs = []
        for use_cache in (False, True):
            pairs = []

            def overlap(a, b):
                pairs.append((tuple(a.center()), tuple(b.center())))
                return actual_overlap(a, b)

            with patch.object(motion, '_normalize_material', wraps=motion._normalize_material) as normalize:
                with patch.object(motion, '_material', actual_material if use_cache else normalize), \
                        patch.object(motion, 'overlap_volume', overlap):
                    result = motion.run_condition(condition, parts, 0)
                runs.append((result, pairs, normalize.call_count))
        self.assertEqual(runs[0][:2], runs[1][:2])
        self.assertEqual(runs[1][0]['status'], 'pass')
        self.assertEqual(len(runs[1][1]), 15)  # Every obstacle at all five poses.
        self.assertEqual(runs[0][2], 30)
        self.assertEqual(runs[1][2], 8)  # Five placed movers plus three obstacles.

    def test_first_collision_and_material_volume_are_unchanged(self):
        parts = {'moving': self.group(), 'fixed': self.group().translate((4, 0, 0))}
        condition = {'id': 'blocked_stroke', 'check': 'linear_motion_collision',
                     'inputs': {'moving_part': 'moving', 'obstacle_parts': ['fixed'],
                                'translation': [5, 0, 0], 'steps': 5}}
        with patch.object(motion, '_material', motion._normalize_material):
            expected = motion.run_condition(condition, parts, 0)
        self.assertEqual(expected['status'], 'fail')
        self.assertEqual(motion.run_condition(condition, parts, 0), expected)
        with motion.validation_scope():
            for _ in range(2):
                self.assertAlmostEqual(motion.overlap_volume(parts['moving'], Box(20, 20, 20)), 12)


if __name__ == '__main__':
    unittest.main()
