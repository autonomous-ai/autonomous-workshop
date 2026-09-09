from pathlib import Path
import unittest
from unittest.mock import patch
from build123d import Box, Compound, Location, Shell, Solid
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
_loader = SourceFileLoader('cached_motion_under_test', str(Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts/check_motion'))
_spec = spec_from_loader(_loader.name, _loader)
cached = module_from_spec(_spec)
_loader.exec_module(cached)

class ValidityCacheTests(unittest.TestCase):

    @staticmethod
    def open_solid():
        shell = Shell(list(Box(2, 2, 2).faces())[:-1])
        return Solid(BRepBuilderAPI_MakeSolid(shell.wrapped).Solid())

    def test_valid_and_invalid_topology_keep_decision_under_rigid_placement(self):
        for shape, expected in [(Box(2, 2, 2), True), (self.open_solid(), False)]:
            with self.subTest(expected=expected):
                cache = cached.ValidityCache()
                self.assertEqual(cache.is_valid(shape.wrapped), expected)
                for pose in [Location((12, -8, 31), (0, 0, 37)), Location((-53, 11, 20), (27, 13, 64))]:
                    moved = pose * shape
                    self.assertEqual(cache.is_valid(moved.wrapped), moved.is_valid)
                    self.assertEqual(cache.is_valid(moved.wrapped), expected)
                self.assertEqual(cache.checks, 1)
                self.assertGreaterEqual(cache.hits, 4)

    def test_geometrically_equal_new_topology_is_rechecked(self):
        cache = cached.ValidityCache()
        self.assertTrue(cache.is_valid(Box(2, 2, 2).wrapped))
        self.assertTrue(cache.is_valid(Box(2, 2, 2).wrapped))
        self.assertEqual(cache.checks, 2)

    def test_orientation_is_part_of_identity(self):
        shape = Box(2, 2, 2)
        cache = cached.ValidityCache()
        cache.is_valid(shape.wrapped)
        cache.is_valid(shape.wrapped.Reversed())
        self.assertEqual(cache.checks, 2)

    def test_hash_collision_cannot_reuse_a_different_shape_result(self):
        with patch.object(cached, 'hash', return_value=0, create=True):
            cache = cached.ValidityCache()
            self.assertTrue(cache.is_valid(Box(2, 2, 2).wrapped))
            self.assertFalse(cache.is_valid(self.open_solid().wrapped))
            self.assertEqual(cache.checks, 2)

    def test_nested_compound_cannot_hide_an_invalid_child(self):
        for invalid in [False, True]:
            with self.subTest(invalid=invalid):
                inner = Compound([self.open_solid() if invalid else Box(2, 2, 2)])
                model = Compound([Box(2, 2, 2), inner])
                cache = cached.ValidityCache()
                self.assertEqual(cache.is_valid(model.wrapped), model.is_valid)
                self.assertEqual(cache.is_valid(model.wrapped), not invalid)
                # Validate actual descendant solids as well as nested topology.
                geometry = Compound(model.solids())
                self.assertEqual(cache.is_valid(geometry.wrapped), not invalid)

    def test_validation_scope_restores_after_failure_and_does_not_leak(self):
        shape = Box(2, 2, 2)
        with self.assertRaisesRegex(RuntimeError, 'injected'):
            with cached.validation_scope() as outer:
                cached._is_valid(shape)
                with cached.validation_scope() as inner:
                    self.assertIs(outer, inner)
                raise RuntimeError('injected')
        with cached.validation_scope() as fresh:
            self.assertIsNot(fresh, outer)
            cached._is_valid(shape)
            self.assertEqual(fresh.checks, 1)
            self.assertEqual(fresh.hits, 0)

    def test_cache_capacity_causes_revalidation_without_changing_results(self):
        a, b, c = (Box(2, 2, 2), Box(3, 3, 3), self.open_solid())
        with patch.object(cached, '_MAX_VALIDITY_CACHE_ENTRIES', 2):
            cache = cached.ValidityCache()
            for shape, expected in [(a, True), (b, True), (c, False), (a, True)]:
                self.assertEqual(cache.is_valid(shape.wrapped), expected)
                self.assertLessEqual(cache.entries, 2)
            self.assertEqual(cache.checks, 4)
            self.assertGreaterEqual(cache.clears, 1)

    def test_repeated_overlap_still_counts_actual_material_once(self):
        shape = Compound(children=[Box(2, 2, 2), Box(2, 2, 2)])
        with cached.validation_scope():
            for pose in [Location(), Location((13, 20, -35), (17, 32, 61))]:
                self.assertAlmostEqual(cached.overlap_volume(pose * shape, pose * Box(12, 12, 12)), 8)
if __name__ == '__main__':
    unittest.main()
