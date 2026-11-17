"""ADR 0104 amendment 2026-11-17: a ``snap`` Assembly Step. Its snapping Part
may overlap its catch Part on the way in, no deeper across the direction than
the declared catch and inside the declared barb region; every other pair and
every other overlap still fails; the seat is clear; and a declared snap that
never overlaps is refused. The host mirrors the rule on the final report.

The fake geometry is the gate tests' box geometry with one change: a body
may be several boxes, so a clip can hang through a hole in the case shell
with a barb under it."""

from __future__ import annotations

import copy
import unittest

from workshop.errors import ContractError
from workshop.make import kit_tree as host_kit_tree
from workshop.wish import assembly_tree as host_tree
from tests.make.test_kit_tree import LAYOUT, BoxGeometry, box, kit_tree, overlap, sealed_block, sealed_kit
from tests.wish.test_assembly_tree import _step

# The case shell with a 2 mm slot at X 54-56, Y 45-55, through its 5 mm floor.
SHELL = [box((0, 0, 0), (54, 100, 5)), box((56, 0, 0), (100, 100, 5)),
         box((54, 0, 0), (56, 45, 5)), box((54, 55, 0), (56, 100, 5))]


def carcass(barb_lo=53.7, barb_hi=56.3, barb_z=(-1.0, -0.5)):
    """The cabinet carcass with a clip hanging through the slot: a shank
    0.05 clear a side and a barb under the floor, 0.3 a side past the slot
    by default."""

    return [box((40, 40, 5), (70, 60, 35)), box((54.05, 45, -1), (55.95, 55, 5)),
            box((barb_lo, 45, barb_z[0]), (barb_hi, 55, barb_z[1]))]


def snap_layout(clip=None, battery=None):
    layout = copy.deepcopy(LAYOUT)
    case = layout[("case", 1)]
    case[0] = ("A01-case-shell", SHELL)
    if battery is not None:
        case[2] = ("P04-battery-box", battery)
    cabinet = layout[("cabinet", 1)]
    cabinet[0] = ("B01-cabinet-carcass", clip if clip is not None else carcass())
    return layout


def boxes(shape):
    return list(shape) if isinstance(shape, list) else [shape]


def shift(shape, by):
    return [(tuple(v + d for v, d in zip(lo, by)), tuple(v + d for v, d in zip(hi, by))) for lo, hi in boxes(shape)]


def common(a, b):
    lo = tuple(max(a[0][i], b[0][i]) for i in range(3))
    hi = tuple(min(a[1][i], b[1][i]) for i in range(3))
    return (lo, hi) if all(lo[i] < hi[i] for i in range(3)) else None


class ClipGeometry(BoxGeometry):
    """BoxGeometry whose bodies may be lists of boxes."""

    def bounds(self, shapes):
        flat = [part for shape in shapes for part in boxes(shape)]
        return BoxGeometry.bounds(self, flat)

    def sweep(self, condition, moving, obstacles):
        self.sweeps.append(condition)
        inputs = condition["inputs"]
        steps, move = inputs["steps"], inputs["translation"]
        if sum(c * c for c in move) ** 0.5 / steps > condition["thresholds"].get("maxStepMm", 1e9) + 1e-9:
            return {"status": "inconclusive", "detail": "sampled too coarsely"}
        for i in range(1 if inputs["allow_seated_contact"] else 0, steps + 1):
            by = [c * i / steps for c in move]
            for body in moving:
                for placed in shift(body.shape, by):
                    for other in obstacles:
                        volume = sum(overlap(placed, part) for part in boxes(other.shape))
                        if volume > condition["thresholds"]["maxOverlapMm3"]:
                            return {"status": "fail", "obstacle": other.key, "overlapMm3": volume,
                                    "detail": "blocked by %s at step %d/%d" % (other.key, i, steps)}
        return {"status": "pass", "detail": "clear across %d steps" % steps}

    def snap_overlaps(self, condition, moving, obstacles):
        inputs = condition["inputs"]
        steps, move = inputs["steps"], inputs["translation"]
        found = []
        for i in range(0, steps + 1):
            by = [c * i / steps for c in move]
            for body in moving:
                for placed in shift(body.shape, by):
                    for other in obstacles:
                        for part in boxes(other.shape):
                            piece = common(placed, part)
                            if piece is not None and overlap(placed, part) > kit_tree.OVERLAP_MM3:
                                found.append({"step": i, "catch": other.key, "volume": overlap(placed, part),
                                              "bounds": piece})
        return found

    def nonparallel(self, moving, obstacles, direction):
        return []

    def route(self, points, size, obstacles):
        flat = [kit_tree.Body(o.label, part, key=o.key) for o in obstacles for part in boxes(o.shape)]
        return BoxGeometry.route(self, points, size, flat)


SNAP = {"part": "B01-cabinet-carcass", "catch": "A01-case-shell", "catch_mm": 0.35}


def snap_block(**snap):
    block = sealed_block()
    step = _step(block, "S07-furniture")
    step["joint"] = "snap"
    step["snap"] = {**SNAP, **snap}
    return block


class SnapGateTest(unittest.TestCase):
    def final(self, layout=None, **snap):
        plan = kit_tree.Plan(sealed_kit(snap_block(**snap)))
        report = kit_tree.check_assembly(plan, ClipGeometry(layout or snap_layout()), 0.4, reconcile_all=True)
        return kit_tree.summarise(report)

    def test_a_snap_within_its_catch_passes_and_is_recorded(self):
        report = self.final()
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["verdict"], "PASS")
        (record,) = report["snaps"]
        self.assertEqual((record["step"], record["input"], record["part"], record["catch"]),
                         ("S07-furniture", "S03-hang-door#1", "B01-cabinet-carcass", "A01-case-shell"))
        self.assertAlmostEqual(record["max_depth_mm"], 0.3, places=6)
        self.assertGreater(record["overlapping_samples"], 0)
        self.assertEqual(record["seated_mm3"], 0.0)
        self.assertEqual(record["verdict"], "PASS")

    def test_without_the_snap_the_same_clip_is_blocked(self):
        # The exemption is the declared snap and nothing else: as a
        # peg-socket the same barb is a blocked insertion.
        plan = kit_tree.Plan(sealed_kit(sealed_block()))
        report = kit_tree.summarise(kit_tree.check_assembly(plan, ClipGeometry(snap_layout()), 0.4,
                                                            reconcile_all=True))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("S07-furniture: S03-hang-door#1 cannot go in alone along [0, 0, -1]: blocked by "
                      "A01-case-shell#1", report["failures"][0])

    def test_a_barb_deeper_than_its_catch_fails(self):
        report = self.final(catch_mm=0.25)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("passes A01-case-shell#1 0.300 mm deep", report["failures"][0])
        self.assertIn("deeper than its declared 0.25 mm catch", report["failures"][0])
        deep = self.final(snap_layout(carcass(53.4, 56.6)))
        self.assertIn("0.600 mm deep", deep["failures"][0])

    def test_an_overlap_with_a_third_part_fails_however_shallow(self):
        # The battery box hangs under the floor where the barb passes: 0.1 mm
        # into it, shallower than the catch, and still blocked.
        battery = box((50, 45, -0.4), (53.8, 55, 0))
        report = self.final(snap_layout(battery=battery))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("S07-furniture: S03-hang-door#1 cannot go in alone along [0, 0, -1]: blocked by "
                      "P04-battery-box#1", report["failures"][0])

    def test_another_body_of_the_snapping_input_may_not_overlap_the_catch(self):
        layout = snap_layout()
        # The jar now reaches down through the case floor.
        cabinet = layout[("cabinet", 1)]
        cabinet[1] = ("P02-jar", box((45, 35, 3), (50, 40, 27)))
        report = self.final(layout)
        self.assertIn("S07-furniture: S03-hang-door#1 cannot go in alone along [0, 0, -1]: blocked by "
                      "A01-case-shell#1", "\n".join(report["failures"]))

    def test_the_seat_is_still_checked(self):
        report = self.final(snap_layout(carcass(barb_z=(-0.3, 0.2))))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("S03-hang-door#1 is not clear of A01-case-shell at its seat", report["failures"][0])
        self.assertEqual(report["snaps"][0]["verdict"], "FAIL")

    def test_a_snap_that_never_overlaps_is_refused(self):
        report = self.final(snap_layout(carcass(54.1, 55.9)))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("never overlaps it on its way in", report["failures"][0])

    def test_the_overlap_stays_in_its_barb_region(self):
        inside = self.final(region_mm=[[53, 44, -1], [57, 56, 5]])
        self.assertEqual(inside["verdict"], "PASS")
        outside = self.final(region_mm=[[53, 44, 3], [57, 56, 5]])
        self.assertEqual(outside["verdict"], "FAIL")
        self.assertIn("outside its declared barb region", outside["failures"][0])

    def test_the_host_accepts_the_passing_report_and_refuses_a_widened_one(self):
        tree = sealed_kit(snap_block())["assembly_tree"]
        report = self.final()
        host_kit_tree.check_snaps(tree, report["snaps"])
        refused = {
            "deeper": {"max_depth_mm": 0.5},
            "seated": {"seated_mm3": 0.5},
            "never": {"overlapping_samples": 0},
            "failed": {"verdict": "FAIL"},
            "other catch": {"catch": "C01-desk-body"},
            "wider catch": {"catch_mm": 0.9},
        }
        for name, change in refused.items():
            with self.subTest(name), self.assertRaises(ContractError):
                host_kit_tree.check_snaps(tree, [{**report["snaps"][0], **change}])
        with self.assertRaises(ContractError) as caught:
            host_kit_tree.check_snaps(tree, [])
        self.assertIn("records 0 snap pass(es) for S07-furniture", str(caught.exception))
        plain = sealed_kit(sealed_block())["assembly_tree"]
        with self.assertRaises(ContractError) as caught:
            host_kit_tree.check_snaps(plain, report["snaps"])
        self.assertIn("declares no snap there", str(caught.exception))
        host_kit_tree.check_snaps(plain, [])

    def test_every_tool_knows_the_snap_joint(self):
        import importlib.util

        from workshop.runtime.package_data import product_run_domain_skill_roots

        path = product_run_domain_skill_roots()["make-round"] / "scripts" / "kit_manual.py"
        spec = importlib.util.spec_from_file_location("kit_manual_snap_test", path)
        manual = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manual)
        self.assertEqual(kit_tree.JOINS, host_tree.JOINS)
        self.assertEqual(manual.JOINS, host_tree.JOINS)
        self.assertIn("snap", host_tree.JOINS)
        self.assertEqual(set(manual.JOINT_LABELS), set(host_tree.JOINTS))
        self.assertEqual(kit_tree.SNAP_TOLERANCE_MM, host_kit_tree.SNAP_TOLERANCE_MM)
        self.assertEqual(kit_tree.OVERLAP_MM3, host_kit_tree.SEATED_MM3)


if __name__ == "__main__":
    unittest.main()
