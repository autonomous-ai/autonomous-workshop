"""ADR 0104 amendment 2026-11-19 (rules i and j): the tilt hold and walls
before the base, on real build123d solids through ``check_component``.

(i) Every input set down from above by a mechanical joint is a unit, held
against what is already assembled: it stays seated with the tray tilted
45 deg in any direction when it is held down against a lift, or every way
either tips no sooner than 45 deg or catches within 3 deg and is held
against a sideways push.

(j) A plate Part set on its own onto a base it stands across, touching two
walls already set on that base that flank it, goes in between parts
already fixed: the walls are joined to each other first."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.make.test_kit_tree import kit_tree

OAK = "#b5834f"


class Built(kit_tree.CadGeometry):
    def __init__(self, parts):
        super().__init__(Path(tempfile.mkdtemp()))
        self.parts = parts

    def instances(self, role):
        return [1]

    def component(self, role, instance):
        return [kit_tree.Body(label, shape, colours=(OAK,)) for label, shape in self.parts]


def kit(parts, steps):
    return {
        "kind": kit_tree.KIT_KIND, "schema_version": kit_tree.INSTALL_SCHEMA, "pieces": [],
        "geometries": [{"id": "block", "count": 1, "wall_min_mm": 1.2}],
        "catalogue": {"filaments": {"oak": {"hex": OAK}}, "bought_parts": {}},
        "assembly_tree": {
            "parts": [{"id": part, "name": part, "filament": "oak"} for part in parts],
            "steps": steps,
            "components": [{"geometry": "block", "parts": list(parts)}],
        },
    }


def step(sid, base, *moving, joint="peg-socket", direction=(0, 0, -1)):
    return {"id": sid, "output": sid, "count": 1, "joint": joint, "text": sid,
            "inputs": [{"id": base}] + [{"id": item, "direction": list(direction)} for item in moving]}


def check(parts, steps):
    plan = kit_tree.Plan(kit([label for label, _ in parts], steps))
    return kit_tree.check_component(plan, Built(parts), "block", 0.4)


def held(report, needle="tilted 45"):
    return [failure for failure in report["failures"] if needle in failure]


class HoldTest(unittest.TestCase):
    """A 10 mm column on a 4 mm peg in a bore 0.1 mm larger a side."""

    def setUp(self):
        try:
            import build123d as b
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.b = b

    def parts(self, depth, height=40.0, width=10.0, barb=False):
        b = self.b
        base = b.Pos(0, 0, 2.5) * b.Box(60, 60, 5)
        bore = 5.0 if barb else depth + 0.5
        base -= b.Pos(0, 0, 5 - bore / 2) * b.Cylinder(2.1, bore)
        unit = b.Pos(0, 0, 5 + height / 2) * b.Box(width, width, height)
        peg_length = 5.6 if barb else depth
        unit += b.Pos(0, 0, 5 - peg_length / 2) * b.Cylinder(2.0, peg_length)
        if barb:
            # A ring 0.1 mm under the base: lifted 0.3 mm, it meets it.
            unit += b.Pos(0, 0, -0.35) * b.Cylinder(2.6, 0.5)
        return [("A01-base", base), ("A02-unit", unit)]

    def run_unit(self, parts):
        report = check(parts, [step("S01-unit", "A01-base", "A02-unit")])
        (record,) = report["holds"]
        return report, record

    def test_a_tall_unit_on_a_shallow_peg_falls(self):
        report, record = self.run_unit(self.parts(depth=1.0))
        self.assertEqual(record["verdict"], "FAIL")
        self.assertAlmostEqual(record["H"], 40.0, places=2)
        self.assertAlmostEqual(record["d"], 1.0, places=2)
        self.assertLess(min(record["tip"].values()), 45)
        self.assertTrue(all(record["slide"].values()), record)
        self.assertFalse(record["lift"])
        (failure,) = held(report)
        self.assertIn("S01-unit: A02-unit#1 does not stay seated", failure)
        self.assertIn("H 40.0 mm", failure)

    def test_the_same_unit_on_a_deep_peg_stays(self):
        report, record = self.run_unit(self.parts(depth=6.0))
        self.assertEqual(record["verdict"], "PASS", record)
        self.assertTrue(all(c is not None and c <= kit_tree.HOLD_CATCH_DEG for c in record["catch"].values()))
        self.assertEqual(held(report), [])

    def test_a_snap_that_holds_it_down_stays(self):
        report, record = self.run_unit(self.parts(depth=1.0, barb=True))
        self.assertTrue(record["lift"], record)
        self.assertEqual(record["verdict"], "PASS")
        self.assertEqual(held(report), [])

    def test_a_low_wide_unit_stays_by_its_tip_angle(self):
        report, record = self.run_unit(self.parts(depth=1.0, height=5.0, width=40.0))
        self.assertTrue(all(tip >= 45 for tip in record["tip"].values()), record)
        self.assertEqual(record["verdict"], "PASS")
        self.assertEqual(held(report), [])

    def test_a_glued_or_sideways_input_is_no_unit(self):
        parts = self.parts(depth=1.0)
        glued = check(parts, [step("S01-unit", "A01-base", "A02-unit", joint="glue")])
        self.assertEqual(glued["holds"], [])
        sideways = check(parts, [step("S01-unit", "A01-base", "A02-unit", direction=(1, 0, 0))])
        self.assertEqual(sideways["holds"], [])


class StaysTest(unittest.TestCase):
    """The verdict on measured quantities alone."""

    def record(self, tip=10.0, catch=1.0, slide=True, lift=False):
        ways = kit_tree.WAYS
        return {"tip": dict.fromkeys(ways, tip), "catch": dict.fromkeys(ways, catch),
                "slide": dict.fromkeys(ways, slide), "lift": lift}

    def test_the_rule(self):
        self.assertTrue(kit_tree.hold_stays(self.record()))
        self.assertTrue(kit_tree.hold_stays(self.record(tip=45.0, catch=None, slide=False)))
        self.assertTrue(kit_tree.hold_stays(self.record(catch=None, slide=False, lift=True)))
        self.assertFalse(kit_tree.hold_stays(self.record(catch=None)))
        self.assertFalse(kit_tree.hold_stays(self.record(catch=5.0)))
        self.assertFalse(kit_tree.hold_stays(self.record(slide=False)))
        one_way = self.record()
        one_way["catch"]["-Y"] = None
        self.assertFalse(kit_tree.hold_stays(one_way))


class WallOrderTest(unittest.TestCase):
    """A 40 mm base plate and four 2 mm walls standing on it, 0.1 mm apart
    at the corners: a box."""

    WALLS = ("A02-front", "A03-left", "A04-back", "A05-right")

    def setUp(self):
        try:
            import build123d as b
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.b = b

    def parts(self, apart=False):
        b = self.b
        gap = 6.0 if apart else 0.1
        base = b.Pos(0, 0, 1.5) * b.Box(60, 60, 3)
        front = b.Pos(0, -19, 13) * b.Box(40, 2, 20)
        back = b.Pos(0, 19, 13) * b.Box(40, 2, 20)
        side = 36 - 2 * gap
        left = b.Pos(-19, 0, 13) * b.Box(2, side, 20)
        right = b.Pos(19, 0, 13) * b.Box(2, side, 20)
        return [("A01-base", base), ("A02-front", front), ("A03-left", left), ("A04-back", back),
                ("A05-right", right)]

    def order(self, report):
        return [failure for failure in report["failures"] if "join these walls" in failure]

    def test_four_walls_pressed_onto_the_base_one_by_one_fail(self):
        steps, base = [], "A01-base"
        for n, wall in enumerate(self.WALLS, 1):
            steps.append(step("S0%d-%s" % (n, wall[4:]), base, wall))
            base = steps[-1]["id"]
        report = check(self.parts(), steps)
        (failure,) = self.order(report)
        self.assertIn("join these walls to each other first, then set them on A01-base#1", failure)
        for n, wall in enumerate(self.WALLS, 1):
            self.assertIn("S0%d-" % n, failure)
            self.assertIn(wall + "#1", failure)
        (record,) = report["wall_orders"]
        self.assertEqual(record["base"], "A01-base#1")
        self.assertEqual(record["between"], ["A05-right#1"])

    def test_the_walls_in_one_step_onto_the_base_fail_too(self):
        report = check(self.parts(), [step("S01-box", "A01-base", *self.WALLS)])
        self.assertEqual(len(self.order(report)), 1, report["failures"])

    def test_the_walls_joined_first_then_set_on_the_base_pass(self):
        steps = [step("S01-walls", "A02-front", "A03-left", "A04-back", "A05-right", direction=(0, 0, -1)),
                 {"id": "S02-box", "output": "Box", "count": 1, "joint": "tab-slot", "text": "Set on.",
                  "inputs": [{"id": "A01-base"}, {"id": "S01-walls", "direction": [0, 0, -1]}]}]
        report = check(self.parts(), steps)
        self.assertEqual(self.order(report), [])
        self.assertEqual(report["wall_orders"], [])

    def test_one_wall_alone_or_walls_that_do_not_meet_pass(self):
        alone = check(self.parts()[:2], [step("S01-front", "A01-base", "A02-front")])
        self.assertEqual(self.order(alone), [])
        steps, base = [], "A01-base"
        for n, wall in enumerate(self.WALLS, 1):
            steps.append(step("S0%d-%s" % (n, wall[4:]), base, wall))
            base = steps[-1]["id"]
        apart = check(self.parts(apart=True), steps)
        self.assertEqual(self.order(apart), [])

    def shelf_parts(self, inside):
        """A standing back plate, two sides pushed onto it and a shelf
        lowered last: on the sides' tops, or slid down between them."""
        b = self.b
        back = b.Pos(0, 1.5, 20) * b.Box(40, 3, 40)
        left = b.Pos(-19, 13, 20) * b.Box(2, 20, 40)
        right = b.Pos(19, 13, 20) * b.Box(2, 20, 40)
        shelf = (b.Pos(0, 13, 21) * b.Box(35.8, 20, 2) if inside else b.Pos(0, 11.5, 41) * b.Box(40, 23, 2))
        return [("A01-base", back), ("A02-front", left), ("A03-left", right), ("A04-back", shelf)]

    def shelf_steps(self):
        return [step("S01-sides", "A01-base", "A02-front", "A03-left", direction=(0, -1, 0)),
                step("S02-shelf", "S01-sides", "A04-back")]

    def test_a_plate_set_on_the_tops_of_two_walls_is_not_between_them(self):
        report = check(self.shelf_parts(inside=False), self.shelf_steps())
        self.assertEqual(self.order(report), [])

    def test_a_plate_slid_down_between_two_fixed_walls_fails(self):
        report = check(self.shelf_parts(inside=True), self.shelf_steps())
        (failure,) = self.order(report)
        self.assertIn("A04-back#1 goes in between walls already fixed", failure)

    def test_two_walls_in_a_corner_pass(self):
        report = check(self.parts()[:3], [step("S01-front", "A01-base", "A02-front"),
                                          step("S02-left", "S01-front", "A03-left")])
        self.assertEqual(self.order(report), [])


if __name__ == "__main__":
    unittest.main()
