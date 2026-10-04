"""design-a-toy Stage 3d: the camera-composition check (issue #95)."""

import importlib.util
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / ".claude" / "skills" / "design-a-toy" / "scripts" / "camera_composition.py"
RENDER_REVIEW = REPOSITORY / "src" / "workshop" / "make" / "skills" / "cad" / "scripts" / "render_review"


def _load_tool():
    spec = importlib.util.spec_from_file_location("camera_composition_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


camera_composition = _load_tool()

TILT = math.radians(4.3)
BLADES = [
    {"name": "wing#1 top blade", "from": [16, 17.5, 198.8],
     "along": [math.cos(TILT), 0, math.sin(TILT)], "length": 175},
    {"name": "wing#2 top blade", "from": [-16, 17.5, 198.8],
     "along": [-math.cos(TILT), 0, math.sin(TILT)], "length": 175},
]
V_CLAIM = {"name": "wings as a V", "kind": "v",
           "segments": ["wing#1 top blade", "wing#2 top blade"]}


def _broken_god(cameras, claims=(V_CLAIM,)):
    return {"cameras": cameras, "segments": BLADES, "claims": list(claims)}


class CameraConventionTest(unittest.TestCase):
    def test_the_basis_matches_render_review(self):
        source = RENDER_REVIEW.read_text()
        start = source.index("def camera_basis")
        self.assertIn("math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)",
                      source[start:start + 600])
        self.assertIn('"front": (-90.0, 0.0)', source)

    def test_named_views_project_as_expected(self):
        # From the front (-90, 0): +X is screen right, +Z screen up, -Y nearest.
        front = camera_composition.project((1, 0, 0), [-90, 0])
        self.assertAlmostEqual(front["x"], 1)
        self.assertAlmostEqual(camera_composition.project((0, 0, 1), [-90, 0])["y"], 1)
        self.assertAlmostEqual(camera_composition.project((0, -1, 0), [-90, 0])["depth"], 1)
        # AZ 0 looks from +X, so +X is nearest; from the back +X is screen left.
        self.assertAlmostEqual(camera_composition.project((1, 0, 0), [0, 0])["depth"], 1)
        self.assertAlmostEqual(camera_composition.project((1, 0, 0), [90, 0])["x"], -1)
        # Straight down: +Y is screen up, as render_review's top view.
        self.assertAlmostEqual(camera_composition.project((0, 1, 0), [-90, 90])["y"], 1)


class BrokenGodR01Test(unittest.TestCase):
    def _segments(self, camera):
        report = camera_composition.run_check(_broken_god({"c": camera}))
        return report, report["cameras"]["c"]["segments"]

    def test_from_r01s_camera_the_blades_are_a_tilted_line_not_a_v(self):
        report, segments = self._segments([35, 22])

        self.assertAlmostEqual(segments["wing#1 top blade"]["rise_deg"], -22.5, delta=0.1)
        self.assertAlmostEqual(segments["wing#2 top blade"]["rise_deg"], 33.3, delta=0.1)
        self.assertEqual(report["verdict"], "FAIL")

    def test_thirty_five_degrees_from_the_front_gives_the_runs_numbers(self):
        # The run's reviewer read "35 degrees azimuth" from the front: [-55, 22].
        report, segments = self._segments([-55, 22])

        self.assertAlmostEqual(segments["wing#1 top blade"]["rise_deg"], -10.1, delta=0.1)
        self.assertAlmostEqual(segments["wing#2 top blade"]["rise_deg"], 19.2, delta=0.1)
        self.assertEqual(report["verdict"], "FAIL")

    def test_from_the_front_the_blades_rise_in_mirror(self):
        report, segments = self._segments([-90, 15])

        first, second = segments["wing#1 top blade"], segments["wing#2 top blade"]
        self.assertEqual((first["side"], second["side"]), ("right", "left"))
        self.assertAlmostEqual(first["rise_deg"], 4.15, delta=0.05)
        self.assertAlmostEqual(first["rise_deg"], second["rise_deg"], places=6)
        self.assertEqual(report["verdict"], "PASS", report["claims"])


class ClaimTest(unittest.TestCase):
    def test_a_line_claim_measures_the_bend(self):
        claim = {"kind": "line", "segments": ["wing#1 top blade", "wing#2 top blade"],
                 "tolerance_deg": 5}
        report = camera_composition.run_check(_broken_god({"top": [-90, 90]}, [claim]))

        self.assertEqual(report["verdict"], "PASS", report["claims"])

        front = camera_composition.run_check(_broken_god({"front": [-90, 15]}, [claim]))
        self.assertEqual(front["verdict"], "FAIL")
        self.assertIn("bend 8.3", front["claims"][0]["detail"])

    def test_in_front_compares_depth_from_each_named_camera(self):
        check = {
            "cameras": {"front": [-90, 10], "back": [90, 10]},
            "points": {"shield": [0, -30, 100], "chest": [0, 0, 100]},
            "claims": [{"kind": "in_front", "near": "shield", "far": "chest", "margin_mm": 20}],
        }
        report = camera_composition.run_check(check)

        verdicts = {c["camera"]: c["verdict"] for c in report["claims"]}
        self.assertEqual(verdicts, {"front": "PASS", "back": "FAIL"})

    def test_a_segment_needs_a_direction(self):
        check = _broken_god({"c": [0, 0]})
        check["segments"] = [{"name": "x", "from": [0, 0, 0], "along": [0, 0, 0], "length": 5}]
        with self.assertRaises(ValueError):
            camera_composition.run_check(check)

    def test_the_command_line_exits_one_on_a_failed_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.json"
            path.write_text(json.dumps(_broken_god({"R01": [35, 22]})))
            saved, sys.stdout = sys.stdout, io.StringIO()
            try:
                code = camera_composition.main([str(path)])
                printed = sys.stdout.getvalue()
            finally:
                sys.stdout = saved

        self.assertEqual(code, 1)
        self.assertIn("FAIL wings as a V from R01", printed)


if __name__ == "__main__":
    unittest.main()
