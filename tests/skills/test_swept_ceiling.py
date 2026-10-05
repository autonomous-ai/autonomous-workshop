"""design-a-toy Stage 3c: the swept-volume-over-ceiling check (issue #89)."""

import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / ".claude" / "skills" / "design-a-toy" / "scripts" / "swept_ceiling.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("swept_ceiling_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


swept_ceiling = _load_tool()

BOX = [[-30, 0], [30, 0], [30, 50], [-30, 50]]


def _check(**changes):
    check = {
        "part": "housing",
        "outline": BOX,
        "ceiling": {"height": 10.0, "max_height": 30.0},
        "movers": [{
            "name": "gear", "pivot": [0, 20], "start_deg": 0, "end_deg": 35, "top": 9.0,
            "shapes": [{"circle": {"center": [0, 20], "radius": 17.1}}],
        }],
        "seats": [{"name": "hinge seat", "at": [0, 20], "max_height": 10.0}],
        "clearance": 0.5, "bridge_mm": 12, "overhang_deg": 50, "grid_mm": 1.0, "step_deg": 5,
    }
    check.update(changes)
    return check


class SweptCeilingTest(unittest.TestCase):
    def test_a_seat_at_the_centre_of_a_turning_disc_cannot_print(self):
        # Broken God attempt 15 in miniature: the gear is a full disc round
        # its own hinge seat, so nothing can stand within 17.6 of the seat.
        report = swept_ceiling.run_check(_check())

        self.assertEqual(report["verdict"], "FAIL")
        seat = report["seats"][0]
        self.assertTrue(seat["swept"])
        self.assertEqual(seat["verdict"], "FAIL")
        self.assertGreaterEqual(seat["nearest_support"], 17.6)
        self.assertGreater(seat["vault_height"], 10 + math.tan(math.radians(50)) * 17.5)

    def test_a_ceiling_inside_the_clearance_is_reported(self):
        report = swept_ceiling.run_check(_check(ceiling={"height": 9.4, "max_height": 30.0}))

        self.assertTrue(any("inside gear's clearance" in p for p in report["problems"]))
        self.assertEqual(report["vault_base"], 9.5)

    def test_a_small_mover_away_from_the_seat_passes(self):
        mover = {"name": "pin", "pivot": [20, 40], "start_deg": 0, "end_deg": 90, "top": 9.0,
                 "shapes": [{"circle": {"center": [22, 40], "radius": 2.0}}]}
        report = swept_ceiling.run_check(_check(movers=[mover]))

        self.assertEqual(report["verdict"], "PASS", report["problems"])
        self.assertEqual(report["seats"][0], {"name": "hinge seat", "swept": False, "verdict": "PASS"})
        self.assertGreater(report["swept_points"], 0)

    def test_keeping_the_mover_low_gives_the_seat_a_nearby_support(self):
        movers = _check()["movers"]
        movers[0]["keep_below"] = 27.5  # free from Z 28.0 + clearance, so the first grid row is 29
        report = swept_ceiling.run_check(_check(movers=movers))

        seat = report["seats"][0]
        self.assertEqual(seat["nearest_support"], 9.0)
        self.assertAlmostEqual(seat["vault_height"], 10.0 + math.tan(math.radians(50)) * 9.0, places=2)

    def test_a_turning_bar_sweeps_only_its_travel(self):
        bar = {"name": "bar", "pivot": [0, 0], "start_deg": 0, "end_deg": 90, "top": 9.0,
               "shapes": [{"polygon": [[0, -1], [20, -1], [20, 1], [0, 1]]}]}
        angles = swept_ceiling._angles(bar, 5)

        self.assertTrue(swept_ceiling._swept_by((10, 10), bar, angles, 0.5))
        self.assertTrue(swept_ceiling._swept_by((0, 15), bar, angles, 0.5))
        self.assertFalse(swept_ceiling._swept_by((-10, -10), bar, angles, 0.5))
        self.assertFalse(swept_ceiling._swept_by((10, -10), bar, angles, 0.5))

    def test_a_narrow_slot_bridges(self):
        # A bar turning through a 10 mm wide band: every ceiling point over it
        # has support on both sides within 12 mm.
        bar = {"name": "slider", "pivot": [0, 25], "start_deg": 0, "end_deg": 0, "top": 9.0,
               "shapes": [{"polygon": [[-30, 21], [30, 21], [30, 29], [-30, 29]]}]}
        report = swept_ceiling.run_check(_check(movers=[bar], seats=[],
                                                ceiling={"height": 10.0, "max_height": 10.0}))

        self.assertEqual(report["verdict"], "PASS", report["problems"])

    def test_the_command_line_exits_one_on_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.json"
            path.write_text(json.dumps(_check()))
            with _quiet():
                self.assertEqual(swept_ceiling.main([str(path), "--map"]), 1)


class _quiet:
    def __enter__(self):
        import io

        self.saved = sys.stdout
        sys.stdout = io.StringIO()

    def __exit__(self, *exc):
        sys.stdout = self.saved
        return False


if __name__ == "__main__":
    unittest.main()
