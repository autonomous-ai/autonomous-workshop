"""Exact shape connectivity for printable-part diagnostics."""
from __future__ import annotations

import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from build123d import Box, Solid


CHECK_FIT = (
    Path(__file__).resolve().parents[2]
    / "src/workshop/make/skills/cad/scripts/check_fit"
)


class CheckFitBodyCountTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        namespace = runpy.run_path(str(CHECK_FIT))
        cls.body_count = staticmethod(namespace["body_count"])
        cls.touch_tolerance = namespace["TOUCH_TOL"]

    def test_island_inside_frame_is_not_connected_by_overlapping_bounds(self):
        frame = (Box(10, 10, 2) - Box(8, 8, 3)).solids()[0]
        island = Box(2, 2, 2).solids()[0]
        self.assertAlmostEqual(frame.distance_to(island), 3.0)
        self.assertEqual(self.body_count([frame, island]), 2)

    def test_touching_and_overlapping_solids_remain_one_body(self):
        for offset in (1.5, 2.0):
            with self.subTest(offset=offset):
                solids = [Box(2, 2, 2).solids()[0],
                          Box(2, 2, 2).translate((offset, 0, 0)).solids()[0]]
                self.assertEqual(self.body_count(solids), 1)

    def test_touching_chain_remains_one_body(self):
        solids = [Box(2, 2, 2).translate((x, 0, 0)).solids()[0]
                  for x in (0, 2, 4)]
        self.assertEqual(self.body_count(solids), 1)

    def test_preserves_existing_contact_tolerance(self):
        for gap, expected in ((self.touch_tolerance / 2, 1),
                              (self.touch_tolerance * 2, 2)):
            with self.subTest(gap=gap):
                solids = [Box(2, 2, 2).solids()[0],
                          Box(2, 2, 2).translate((2 + gap, 0, 0)).solids()[0]]
                self.assertEqual(self.body_count(solids), expected)

    def test_separated_bounds_need_no_shape_distance_query(self):
        solids = [Box(2, 2, 2).solids()[0],
                  Box(2, 2, 2).translate((10, 0, 0)).solids()[0]]
        with mock.patch.object(Solid, "distance_to", side_effect=AssertionError):
            self.assertEqual(self.body_count(solids), 2)

    def test_empty_and_single_solid_need_no_distance_query(self):
        with mock.patch.object(Solid, "distance_to", side_effect=AssertionError):
            self.assertEqual(self.body_count([]), 0)
            self.assertEqual(self.body_count([Box(2, 2, 2).solids()[0]]), 1)

    def test_strict_cli_rejects_disconnected_part_with_overlapping_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "part_frame.step.py").write_text(
                "from build123d import Box, Compound\n"
                "def gen_step():\n"
                "    frame = Box(10, 10, 2) - Box(8, 8, 3)\n"
                "    island = Box(2, 2, 2)\n"
                "    return Compound(children=[frame, island]).translate((0, 0, 1))\n"
            )
            completed = subprocess.run(
                [sys.executable, str(CHECK_FIT), str(project), "--strict", "--json"],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual(result["parts"][0]["bodies"], 2)
            self.assertEqual([item["rule"] for item in result["findings"]],
                             ["multi-body-part"])

    def test_distance_failure_does_not_merge_solids(self):
        solids = [Box(2, 2, 2).solids()[0], Box(2, 2, 2).solids()[0]]
        with mock.patch.object(Solid, "distance_to", side_effect=RuntimeError("kernel failure")):
            with self.assertRaisesRegex(RuntimeError, "kernel failure"):
                self.body_count(solids)

    def test_invalid_distance_does_not_merge_solids(self):
        solids = [Box(2, 2, 2).solids()[0], Box(2, 2, 2).solids()[0]]
        for value in (float("nan"), float("inf"), -1.0):
            with self.subTest(value=value), mock.patch.object(Solid, "distance_to", return_value=value):
                with self.assertRaisesRegex(ValueError, "invalid separation"):
                    self.body_count(solids)


if __name__ == "__main__":
    unittest.main()
