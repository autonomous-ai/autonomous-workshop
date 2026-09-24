"""A content-keyed cache lets an unchanged occurrence skip retessellation."""
from pathlib import Path
import os
import runpy
import tempfile
import unittest
from unittest import mock

import numpy as np
from build123d import Box, Shape, Sphere


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"


class TessellationCacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = runpy.run_path(str(RENDERER))
        # Functions loaded this way keep their own __globals__, a copy of the
        # dict runpy hands back rather than that dict itself; patch the copy
        # they actually resolve names against.
        cls.module_globals = cls.renderer["main"].__globals__

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.entry = Path(tmp.name) / "toy.step.py"
        self.entry.write_text("def gen_step(): pass\n", encoding="utf-8")
        self.calls = 0
        real_tessellate = Shape.tessellate

        def counting_tessellate(shape, *args, **kwargs):
            self.calls += 1
            return real_tessellate(shape, *args, **kwargs)

        patcher = mock.patch.object(Shape, "tessellate", counting_tessellate)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tessellate(self, shape, tolerance=0.08, angular=None):
        return self.renderer["tessellate_occurrences"](
            shape, tolerance, angular, cache_entry=self.entry
        )

    def cache_dir(self):
        return self.entry.parent / "__cadgen__" / self.renderer["TESSELLATION_CACHE_NAMESPACE"]

    def test_second_call_for_an_unchanged_occurrence_is_a_cache_hit(self):
        first = self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1)
        second = self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1, "an unchanged occurrence must not be retessellated")
        np.testing.assert_array_equal(first[0][0], second[0][0])
        np.testing.assert_array_equal(first[0][1], second[0][1])

    def test_cached_result_renders_byte_identical_pixels(self):
        shape = Box(20, 14, 6)
        fresh = self.tessellate(shape)
        fresh_image = self.renderer["render"](fresh, -45.0, 35.264, 200, 0.07)
        cached = self.tessellate(Box(20, 14, 6))
        self.assertEqual(self.calls, 1)
        cached_image = self.renderer["render"](cached, -45.0, 35.264, 200, 0.07)
        np.testing.assert_array_equal(np.asarray(fresh_image), np.asarray(cached_image))

    def test_changed_geometry_is_a_cache_miss(self):
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1)
        self.tessellate(Box(5, 6, 7))
        self.assertEqual(self.calls, 2)

    def test_changed_linear_tolerance_is_a_cache_miss(self):
        self.tessellate(Box(2, 3, 4), tolerance=0.08)
        self.assertEqual(self.calls, 1)
        self.tessellate(Box(2, 3, 4), tolerance=0.05)
        self.assertEqual(self.calls, 2)

    def test_changed_angular_tolerance_is_a_cache_miss(self):
        self.tessellate(Sphere(10), tolerance=0.05, angular=0.1)
        self.assertEqual(self.calls, 1)
        self.tessellate(Sphere(10), tolerance=0.05, angular=0.05)
        self.assertEqual(self.calls, 2)

    def test_changed_tool_source_bytes_is_a_cache_miss(self):
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1)
        with mock.patch.dict(self.module_globals, {"_self_source_identity": lambda: "changed"}):
            self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 2)

    def test_corrupted_cache_entry_is_a_miss_not_a_crash(self):
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1)
        entries = list(self.cache_dir().glob("*"))
        self.assertTrue(entries)
        for path in entries:
            path.write_text("not json", encoding="utf-8")
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 2)

    def test_missing_cache_directory_is_a_miss_not_a_crash(self):
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 1)
        for path in self.cache_dir().glob("*"):
            path.unlink()
        self.tessellate(Box(2, 3, 4))
        self.assertEqual(self.calls, 2)

    def test_disabling_the_geometry_cache_never_reuses_or_writes(self):
        with mock.patch.dict(os.environ, {"WORKSHOP_GEOMETRY_CACHE": "0"}):
            self.tessellate(Box(2, 3, 4))
            self.assertEqual(self.calls, 1)
            self.tessellate(Box(2, 3, 4))
            self.assertEqual(self.calls, 2)
        self.assertFalse((self.entry.parent / "__cadgen__").exists())

    def test_without_a_cache_entry_every_call_recomputes_and_nothing_is_written(self):
        self.renderer["tessellate_occurrences"](Box(2, 3, 4), 0.08)
        self.assertEqual(self.calls, 1)
        self.renderer["tessellate_occurrences"](Box(2, 3, 4), 0.08)
        self.assertEqual(self.calls, 2)
        self.assertFalse((self.entry.parent / "__cadgen__").exists())

    def test_main_builds_the_assembly_once_regardless_of_view_count(self):
        entry = self.entry.with_name("assembly.step.py")
        entry.write_text(
            "from build123d import Box\n"
            "def gen_step():\n"
            "    return Box(2, 3, 4)\n",
            encoding="utf-8",
        )
        out = entry.parent / "out"
        calls = []
        real_build_shape = self.renderer["build_shape"]

        def counting_build_shape(source):
            calls.append(source)
            return real_build_shape(source)

        with mock.patch.dict(self.module_globals, {"build_shape": counting_build_shape}):
            self.renderer["main"](
                [str(entry), "--view", "front", "--view", "top", "--view", "iso", "-o", str(out)]
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.calls, 1)


if __name__ == "__main__":
    unittest.main()
