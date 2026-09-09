"""Metadata labels use actual sample identities and the shared pose table."""
from __future__ import annotations

import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class SampleAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = runpy.run_path(str(TOOLS / "check_motion"))
        cls.states = runpy.run_path(str(TOOLS / "motion_states.py"))

    def annotate(self, manifest, identities):
        # Exercise the real pose-table arithmetic with inert axis/vector holders.
        # No shape construction, tessellation, rendering or Boolean work occurs.
        self.assertIn("sample_annotations", self.states)
        function = self.states["sample_annotations"]
        fake_cad = types.SimpleNamespace(Axis=lambda *args: args, Vector=lambda *args: args)
        with mock.patch.dict(sys.modules, {"build123d": fake_cad}), mock.patch.dict(
            function.__globals__, {"helpers": lambda: (self.check, None)}
        ):
            return function(manifest, identities)

    def manifest(self, *, steps=72, movers=None):
        if movers is None:
            movers = [{"part": "crank", "rotation": {
                "axis_point": [0, 0, 72], "axis_direction": [0, 1, 0],
                "start_deg": 0, "end_deg": 360}}]
        return {"conditions": [{"id": "turn", "check": "coupled_motion_collision",
                                "inputs": {"steps": steps, "movers": movers}}]}

    def identities(self, *indices):
        return [{"condition_id": "turn", "sample_index": index} for index in indices]

    def test_file_ordinals_are_not_used_as_motion_samples_or_angles(self):
        rows = self.annotate(self.manifest(), self.identities(0, 19, 38, 58))
        self.assertEqual([r["movers"][0]["rotation_deg"] for r in rows], [0, 95, 190, 290])
        self.assertEqual([r["sample_index"] for r in rows], [0, 19, 38, 58])
        self.assertTrue(all(r["steps"] == 72 for r in rows))

    def test_uniform_motion_retains_origin_direction_and_multiple_revolutions(self):
        for steps in (8, 72, 120):
            for start, end in ((-45, 315), (90, -270), (15, 735)):
                with self.subTest(steps=steps, start=start, end=end):
                    m = self.manifest(steps=steps)
                    m["conditions"][0]["inputs"]["movers"][0]["rotation"].update(start_deg=start, end_deg=end)
                    rows = self.annotate(m, self.identities(0, steps // 2, steps))
                    self.assertEqual([r["movers"][0]["rotation_deg"] for r in rows], [start, (start + end) / 2, end])

    def test_explicit_nonuniform_tables_override_linear_shorthand(self):
        rotation = {"axis_point": [1, 2, 3], "axis_direction": [0, 0, 1],
                    "angles_deg": [0, 3, 27, 27, 48, 95, 110, 160, 360],
                    "start_deg": 100, "end_deg": 200}
        rows = self.annotate(self.manifest(steps=8, movers=[{"part": "indexed wheel", "rotation": rotation}]), self.identities(1, 3, 5))
        self.assertEqual([r["movers"][0]["rotation_deg"] for r in rows], [3, 27, 95])
        self.assertEqual(rows[0]["movers"][0]["axis_point"], [1, 2, 3])
        self.assertEqual(rows[0]["movers"][0]["axis_direction"], [0, 0, 1])

    def test_each_mover_keeps_its_own_rotation_and_translation(self):
        movers = [
            {"part": "driver", "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 1, 0], "end_deg": 360}},
            {"part": "follower", "rotation": {"axis_point": [3, 0, 0], "axis_direction": [0, 1, 0], "end_deg": -120},
             "translation": {"vector": [0, 0, 10], "start": 0.2, "end": 1}},
            {"part": "slider", "translation": {"offsets_mm": [[i, i*i, -i] for i in range(9)]}},
        ]
        row = self.annotate(self.manifest(steps=8, movers=movers), self.identities(4))[0]
        self.assertEqual([p["part"] for p in row["movers"]], ["driver", "follower", "slider"])
        self.assertEqual([p["rotation_deg"] for p in row["movers"]], [180, -60, None])
        self.assertEqual(row["movers"][0]["translation_mm"], None)
        self.assertAlmostEqual(row["movers"][1]["translation_mm"][2], 6)
        self.assertEqual(row["movers"][2]["translation_mm"], [4, 16, -4])
        self.assertIsNone(row["movers"][2]["axis_point"])

    def test_nested_conditions_and_identity_order_are_preserved(self):
        first = self.manifest()["conditions"][0]
        second = self.manifest()["conditions"][0]
        second["id"] = "reverse"
        second["inputs"]["movers"][0]["rotation"]["end_deg"] = -360
        manifest = {"conditions": [first, {"check": "assembly_sequence", "inputs": {"steps": [second]}}]}
        ids = [{"condition_id": "reverse", "sample_index": 18}, {"condition_id": "turn", "sample_index": 36}]
        rows = self.annotate(manifest, ids)
        self.assertEqual([r["condition_id"] for r in rows], ["reverse", "turn"])
        self.assertEqual([r["movers"][0]["rotation_deg"] for r in rows], [-90, 180])

    def test_invalid_samples_and_missing_conditions_are_rejected(self):
        cases = [[], self.identities(-1), self.identities(73), self.identities(True),
                 self.identities(1.5), self.identities(1, 1),
                 [{"condition_id": "missing", "sample_index": 0}],
                 [{"condition_id": "turn", "sample_index": 0, "angle_deg": 90}]]
        for ids in cases:
            with self.subTest(identities=ids), self.assertRaises(ValueError):
                self.annotate(self.manifest(), ids)

    def test_nonfinite_numeric_axis_strings_are_rejected_before_cad(self):
        for field in ("axis_point", "axis_direction"):
            for value in ("NaN", "Infinity", "-Infinity"):
                with self.subTest(field=field, value=value):
                    manifest = self.manifest()
                    manifest["conditions"][0]["inputs"]["movers"][0]["rotation"][field][0] = value
                    axis = mock.Mock(side_effect=AssertionError("invalid axis reached CAD constructor"))
                    fake = types.SimpleNamespace(Axis=axis, Vector=lambda *args: args)
                    fn = self.states["sample_annotations"]
                    with mock.patch.dict(sys.modules, {"build123d": fake}), mock.patch.dict(
                        fn.__globals__, {"helpers": lambda: (self.check, None)}
                    ), self.assertRaises(ValueError):
                        fn(manifest, self.identities(0))
                    axis.assert_not_called()

    def test_invalid_step_counts_and_overflowed_pose_arithmetic_are_rejected(self):
        for steps in (0, -1, True, 8.5, 10001):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                self.annotate(self.manifest(steps=steps), self.identities(0))
        manifest = self.manifest()
        manifest["conditions"][0]["inputs"]["movers"][0]["rotation"].update(start_deg=1e308, end_deg=-1e308)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            self.annotate(manifest, self.identities(0))

    def test_invalid_mover_data_cannot_become_authoritative_labels(self):
        cases = [[], [{}], [{"part": "", "translation": {"vector": [1, 0, 0]}}],
                 [{"part": "bad", "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 0, 0]}}],
                 [{"part": "bad", "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 1, 0], "angles_deg": [0, 1]}}],
                 [{"part": "bad", "translation": {"vector": [float("nan"), 0, 0]}}]]
        for movers in cases:
            with self.subTest(movers=movers), self.assertRaises(ValueError):
                self.annotate(self.manifest(movers=movers), self.identities(0))


if __name__ == "__main__":
    unittest.main()
