"""Prepared motion operands remain exact, bounded, and local to a condition."""
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import unittest
from unittest.mock import patch

from build123d import Box, Compound, Location

_loader = SourceFileLoader(
    'material_motion_under_test',
    str(Path(__file__).resolve().parents[2] /
        'src/workshop/make/skills/cad/scripts/check_motion'))
_spec = spec_from_loader(_loader.name, _loader)
motion = module_from_spec(_spec)
_loader.exec_module(motion)


class MaterialCacheTests(unittest.TestCase):
    def test_repeated_operands_are_prepared_once_inside_scope_only(self):
        a, b = Box(2, 2, 2), Box(2, 2, 2).translate((20, 0, 0))
        with patch.object(motion, '_material', wraps=motion._material) as prepare:
            with motion.validation_scope():
                for _ in range(3):
                    self.assertEqual(motion.overlap_volume(a, b), 0)
                self.assertEqual(prepare.call_count, 2)
            self.assertIsNone(motion._MATERIAL.get())
            for _ in range(2):
                self.assertEqual(motion.overlap_volume(a, b), 0)
            self.assertEqual(prepare.call_count, 6)

    def test_equal_occt_wrappers_reuse_material(self):
        a = Box(2, 2, 2)
        alias = Compound(a.wrapped)
        with patch.object(motion, '_material', wraps=motion._material) as prepare:
            cache = motion.MaterialCache()
            first = cache.prepare(a)
            second = cache.prepare(alias)
            self.assertEqual(prepare.call_count, 1)
            self.assertIs(first, second)

    def test_rigid_locations_do_not_share_prepared_bbox(self):
        a = Box(2, 4, 6)
        moved = Location((20, 0, 0), (0, 0, 90)) * a
        with patch.object(motion, '_material', wraps=motion._material) as prepare:
            cache = motion.MaterialCache()
            first = cache.prepare(a)
            second = cache.prepare(moved)
            self.assertEqual(prepare.call_count, 2)
            self.assertAlmostEqual(first[1], second[1])
            self.assertAlmostEqual(first[2].min.X, -1)
            self.assertAlmostEqual(second[2].min.X, 18)
        with motion.validation_scope():
            self.assertAlmostEqual(motion.overlap_volume(a, a), 48)
            self.assertEqual(motion.overlap_volume(a, moved), 0)

    def test_orientation_is_not_aliased_even_when_hash_collides(self):
        a = Box(2, 2, 2)
        reverse = Compound(a.wrapped.Reversed())
        self.assertFalse(a.wrapped.IsEqual(reverse.wrapped))
        # Reversed solids may have negative signed volume. Stub preparation to
        # isolate cache identity without weakening real volume checks elsewhere.
        with patch.object(motion, 'hash', return_value=0, create=True), \
                patch.object(motion, '_material', return_value=(a, 8.0)) as prepare:
            cache = motion.MaterialCache()
            cache.prepare(a)
            cache.prepare(reverse)
            cache.prepare(a)
            self.assertEqual(prepare.call_count, 2)

    def test_hash_collision_does_not_alias_distinct_topology(self):
        a, b = Box(2, 2, 2), Box(3, 3, 3)
        with patch.object(motion, 'hash', return_value=0, create=True):
            cache = motion.MaterialCache()
            self.assertAlmostEqual(cache.prepare(a)[1], 8)
            self.assertAlmostEqual(cache.prepare(b)[1], 27)
            self.assertAlmostEqual(cache.prepare(a)[1], 8)

    def test_nested_scopes_share_cache_and_failure_restores_context(self):
        a = Box(2, 2, 2)
        self.assertIsNone(motion._MATERIAL.get())
        with patch.object(motion, '_material', wraps=motion._material) as prepare:
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                with motion.validation_scope():
                    outer = motion._MATERIAL.get()
                    outer.prepare(a)
                    with motion.validation_scope():
                        self.assertIs(motion._MATERIAL.get(), outer)
                        motion._MATERIAL.get().prepare(a)
                    raise RuntimeError('injected')
            self.assertIsNone(motion._MATERIAL.get())
            with motion.validation_scope():
                self.assertIsNot(motion._MATERIAL.get(), outer)
                motion._MATERIAL.get().prepare(a)
            self.assertEqual(prepare.call_count, 2)

    def test_empty_operand_remains_error_even_with_distant_valid_operand(self):
        empty, distant = Compound([]), Box(2, 2, 2).translate((1000, 0, 0))
        with motion.validation_scope():
            for a, b in [(empty, distant), (distant, empty)]:
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError, 'no solid'):
                        motion.overlap_volume(a, b)

    def test_compounds_keep_union_volume_not_sum_and_input_geometry(self):
        a, b = Box(2, 2, 2), Box(2, 2, 2).translate((1, 0, 0))
        group = Compound(children=[a, b])
        before = [(tuple(s.position), s.volume) for s in group.children]
        with motion.validation_scope():
            cache = motion._MATERIAL.get()
            normalized, volume, bbox, solids = cache.prepare(group)
            self.assertAlmostEqual(volume, 12)
            self.assertAlmostEqual(sum(s.volume for s in solids), 12)
            for _ in range(2):
                self.assertAlmostEqual(motion.overlap_volume(group, Box(12, 12, 12)), 12)
        self.assertEqual(before, [(tuple(s.position), s.volume) for s in group.children])

    def test_failed_preparation_is_retried_not_cached(self):
        a = Box(2, 2, 2)
        actual = motion._material(a)
        with patch.object(motion, '_material', side_effect=[ValueError('injected'), actual]) as prepare:
            cache = motion.MaterialCache()
            with self.assertRaisesRegex(ValueError, 'injected'):
                cache.prepare(a)
            self.assertAlmostEqual(cache.prepare(a)[1], 8)
            self.assertAlmostEqual(cache.prepare(a)[1], 8)
            self.assertEqual(prepare.call_count, 2)

    def test_eviction_reprepares_without_changing_geometry(self):
        shapes = [Box(size, size, size) for size in (2, 3, 4)]
        with patch.object(motion, '_MAX_MATERIAL_CACHE_ENTRIES', 2), \
                patch.object(motion, '_material', wraps=motion._material) as prepare:
            cache = motion.MaterialCache()
            for shape in shapes:
                self.assertAlmostEqual(cache.prepare(shape)[1], shape.volume)
                self.assertLessEqual(cache.entries, 2)
            self.assertAlmostEqual(cache.prepare(shapes[0])[1], 8)
            self.assertEqual(prepare.call_count, 4)


if __name__ == '__main__':
    unittest.main()
