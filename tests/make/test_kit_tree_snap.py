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
from pathlib import Path

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

    def __init__(self, layout=None, faces=()):
        BoxGeometry.__init__(self, layout)
        # (moving label, obstacle label, face box, message): a flat mating
        # pair at an angle to the direction, as the B-rep backend reads one.
        self.faces = list(faces)

    def _label(self, shape):
        return next(item[0] for items in self.layout.values() for item in items if item[1] == shape)

    def nonparallel(self, moving, obstacles, direction, exempt=(), seats=None):
        found = []
        for mover, holder, face, message in self.faces:
            for shape in moving:
                if self._label(shape) != mover:
                    continue
                for other in obstacles:
                    if self._label(other) != holder:
                        continue
                    ramp = kit_tree._ramp_of(exempt, shape, other, Box(face))
                    if ramp is not None:
                        ramp["faces"].append(message)
                    else:
                        found.append(message)
        return found

    def route(self, points, size, obstacles):
        flat = [kit_tree.Body(o.label, part, key=o.key) for o in obstacles for part in boxes(o.shape)]
        return BoxGeometry.route(self, points, size, flat)


class Box:
    """A face's bounding box as build123d gives it."""

    def __init__(self, face):
        (x0, y0, z0), (x1, y1, z1) = face
        self.min = type("V", (), {"X": x0, "Y": y0, "Z": z0})
        self.max = type("V", (), {"X": x1, "Y": y1, "Z": z1})


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


# The case shell with a second 2 mm slot at X 20-22, Y 45-55, and the
# inkwell given its own clip through it: two barbs of one input snap into
# the one shell.
SHELL_TWO = [box((0, 0, 0), (20, 100, 5)), box((22, 0, 0), (54, 100, 5)), box((56, 0, 0), (100, 100, 5)),
             box((20, 0, 0), (22, 45, 5)), box((20, 55, 0), (22, 100, 5)),
             box((54, 0, 0), (56, 45, 5)), box((54, 55, 0), (56, 100, 5))]
INKWELL_CLIP = [box((55, 35, 20), (58, 40, 24)), box((20.05, 45, -1), (21.95, 55, 5)),
                box((19.7, 45, -1.0), (22.3, 55, -0.5))]
INKWELL = {"part": "D01-inkwell", "catch": "A01-case-shell", "catch_mm": 0.35}
# The carcass barb's ramp face, at 60 deg to the direction, on the barb
# under the slot; and the same face reaching up the shank above the floor.
RAMP = ((53.7, 45, -1.0), (54.05, 55, -0.5))
RAMP_TALL = ((53.7, 45, -1.0), (54.05, 55, 6.0))
RAMP_TEXT = "a flat joint face at 60 deg to it near (53.88, 50.00, -0.75)"
REGION = [[53, 44, -1], [57, 56, 5]]


def two_clip_layout():
    layout = snap_layout()
    layout[("case", 1)][0] = ("A01-case-shell", SHELL_TWO)
    layout[("cabinet", 1)][2] = ("D01-inkwell", INKWELL_CLIP)
    return layout


def pairs_block(pairs):
    block = sealed_block()
    step = _step(block, "S07-furniture")
    step["joint"] = "snap"
    step["snap"] = pairs
    return block


class MultiPairSnapTest(unittest.TestCase):
    """ADR 0104 amendment 2026-11-17 (multi-pair): one snap step declares
    several pairs, each held to every rule of the single snap; a barb's ramp
    face wholly inside its pair's region is no non-parallel joint; every
    undeclared pair and every other face is checked as before."""

    def final(self, pairs, layout=None, faces=()):
        plan = kit_tree.Plan(sealed_kit(pairs_block(pairs)))
        geometry = ClipGeometry(layout or two_clip_layout(), faces)
        return kit_tree.summarise(kit_tree.check_assembly(plan, geometry, 0.4, reconcile_all=True))

    def test_two_declared_pairs_pass_and_each_is_recorded(self):
        report = self.final([SNAP, INKWELL])
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(sorted((r["id"].rsplit(".", 1)[1], r["part"], r["verdict"]) for r in report["snaps"]),
                         [("snap1", "B01-cabinet-carcass", "PASS"), ("snap2", "D01-inkwell", "PASS")])
        for record in report["snaps"]:
            self.assertAlmostEqual(record["max_depth_mm"], 0.3, places=6)
        tree = sealed_kit(pairs_block([SNAP, INKWELL]))["assembly_tree"]
        host_kit_tree.check_snaps(tree, report["snaps"])
        with self.assertRaises(ContractError) as caught:
            host_kit_tree.check_snaps(tree, report["snaps"][:1])
        self.assertIn("records 0 snap pass(es) for S07-furniture (D01-inkwell into A01-case-shell)",
                      str(caught.exception))
        with self.assertRaises(ContractError) as caught:
            host_kit_tree.check_snaps(sealed_kit(snap_block())["assembly_tree"], report["snaps"])
        self.assertIn("a pair the sealed tree does not declare", str(caught.exception))

    def test_a_second_undeclared_pair_is_still_blocked(self):
        for declared in (SNAP, [SNAP]):
            with self.subTest(form=type(declared).__name__):
                report = self.final(declared)
                self.assertEqual(report["verdict"], "FAIL")
                self.assertIn("S07-furniture: S03-hang-door#1 cannot go in alone along [0, 0, -1]: blocked by "
                              "A01-case-shell#1", "\n".join(report["failures"]))
                self.assertEqual([r["part"] for r in report["snaps"]], ["B01-cabinet-carcass"])

    def test_each_pair_keeps_its_own_catch_depth(self):
        report = self.final([SNAP, {**INKWELL, "catch_mm": 0.25}])
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("deeper than its declared 0.25 mm catch", "\n".join(report["failures"]))
        self.assertEqual({r["part"]: r["verdict"] for r in report["snaps"]},
                         {"B01-cabinet-carcass": "PASS", "D01-inkwell": "FAIL"})

    def test_a_ramp_face_inside_its_region_is_exempt_and_recorded(self):
        report = self.final([{**SNAP, "region_mm": REGION}, INKWELL],
                            faces=[("B01-cabinet-carcass", "A01-case-shell", RAMP, RAMP_TEXT)])
        self.assertEqual(report["failures"], [])
        record = next(r for r in report["snaps"] if r["part"] == "B01-cabinet-carcass")
        self.assertEqual(record["ramp_faces"], [RAMP_TEXT])

    def test_a_ramp_face_outside_its_region_still_fails(self):
        report = self.final([{**SNAP, "region_mm": REGION}, INKWELL],
                            faces=[("B01-cabinet-carcass", "A01-case-shell", RAMP_TALL, RAMP_TEXT)])
        self.assertEqual(report["verdict"], "FAIL")
        self.assertIn("engages a joint that is not parallel to its direction [0, 0, -1]: " + RAMP_TEXT,
                      "\n".join(report["failures"]))

    def test_without_a_region_no_face_is_exempt(self):
        report = self.final([SNAP, INKWELL], faces=[("B01-cabinet-carcass", "A01-case-shell", RAMP, RAMP_TEXT)])
        self.assertIn(RAMP_TEXT, "\n".join(report["failures"]))

    def test_the_exemption_is_only_on_its_own_pairs_part_and_catch(self):
        # The same face inside the carcass pair's region, but on the inkwell
        # (whose pair states no region), or against a Part no pair catches.
        for mover, holder in (("D01-inkwell", "A01-case-shell"), ("B01-cabinet-carcass", "P04-battery-box")):
            with self.subTest(mover=mover, holder=holder):
                report = self.final([{**SNAP, "region_mm": REGION}, INKWELL],
                                    faces=[(mover, holder, RAMP, RAMP_TEXT)])
                self.assertIn(RAMP_TEXT, "\n".join(report["failures"]))

    def test_the_contract_takes_a_list_and_refuses_a_repeated_or_empty_one(self):
        sealed_kit(pairs_block([SNAP, INKWELL]))
        sealed_kit(pairs_block([SNAP]))
        for pairs, text in (([SNAP, dict(SNAP)], "names one pair of Part and catch more than once"),
                            ([], "names at least one snap pair"),
                            ([SNAP, {**INKWELL, "catch_mm": 1.5}], ".snap[1].catch_mm must be")):
            with self.subTest(text=text), self.assertRaises(ContractError) as caught:
                sealed_kit(pairs_block(pairs))
            self.assertIn(text, str(caught.exception))


class FusedFallbackTest(unittest.TestCase):
    """When the moving group's union fails, each solid is swept on its own
    against every obstacle, each at the overlap limit over the solid count,
    and the fallback is recorded."""

    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        import runpy

        geometry = kit_tree.CadGeometry.__new__(kit_tree.CadGeometry)
        scripts = Path(kit_tree.__file__).resolve().parents[2] / "cad" / "scripts"
        geometry.motion = runpy.run_path(str(scripts / "check_motion"), run_name="kit_tree_check_motion")
        geometry.fallbacks = []

        def refuse(shape):
            raise ValueError("motion group union has inconsistent volume")

        geometry.motion["rigid_material"] = refuse
        self.geometry, self.Box, self.Pos = geometry, Box, Pos

    def body(self, key, *solids):
        from build123d import Compound

        shape = solids[0] if len(solids) == 1 else Compound(list(solids))
        return kit_tree.Body(key.split("#")[0], shape, solids=len(solids), key=key)

    def condition(self):
        return {"id": "S01.X#1", "check": "linear_motion_collision", "expect": "clear",
                "inputs": {"moving_part": "X#1", "obstacle_parts": [], "translation": [0, 0, 20], "steps": 40,
                           "allow_seated_contact": True},
                "thresholds": {"maxOverlapMm3": 0.001, "maxStepMm": 0.5}}

    def test_a_real_clash_of_one_solid_is_still_caught(self):
        Box, Pos = self.Box, self.Pos
        moving = [self.body("X#1", Pos(0, 0, 0) * Box(2, 2, 2), Pos(10, 0, 0) * Box(2, 2, 2))]
        lid = self.body("L#1", Pos(10, 0, 8) * Box(4, 4, 1))
        result = self.geometry.sweep(self.condition(), moving, [lid])
        self.assertEqual(result["status"], "fail")
        self.assertIn("swept solid by solid, 2 solids", result["detail"])
        (record,) = self.geometry.fallbacks
        self.assertEqual((record["solids"], record["status"], record["max_overlap_mm3_each"]), (2, "fail", 0.0005))

    def test_a_clear_path_passes_solid_by_solid(self):
        Box, Pos = self.Box, self.Pos
        moving = [self.body("X#1", Pos(0, 0, 0) * Box(2, 2, 2), Pos(10, 0, 0) * Box(2, 2, 2))]
        beside = self.body("L#1", Pos(30, 0, 8) * Box(4, 4, 1))
        result = self.geometry.sweep(self.condition(), moving, [beside])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(self.geometry.fallbacks[0]["status"], "pass")

    def test_a_fused_group_does_not_fall_back(self):
        import runpy

        scripts = Path(kit_tree.__file__).resolve().parents[2] / "cad" / "scripts"
        self.geometry.motion = runpy.run_path(str(scripts / "check_motion"), run_name="kit_tree_check_motion")
        Box, Pos = self.Box, self.Pos
        moving = [self.body("X#1", Pos(0, 0, 0) * Box(2, 2, 2), Pos(10, 0, 0) * Box(2, 2, 2))]
        lid = self.body("L#1", Pos(10, 0, 8) * Box(4, 4, 1))
        self.assertEqual(self.geometry.sweep(self.condition(), moving, [lid])["status"], "fail")
        self.assertEqual(self.geometry.fallbacks, [])


if __name__ == "__main__":
    unittest.main()


class SnapStepOrderTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: the host walks snap steps in numeric
    Manual order, so S11 comes before S100."""

    def test_snap_steps_are_checked_in_numeric_order(self):
        from unittest import mock

        spans = {"S100-roof": [({"part": "A01-x", "catch": "A02-y"}, "A01-x")],
                 "S11-door": [({"part": "A03-x", "catch": "A04-y"}, "A03-x")],
                 "S99-wall": [({"part": "A05-x", "catch": "A06-y"}, "A05-x")]}
        seen = []
        with mock.patch.object(host_kit_tree, "_snap_spans", return_value=spans), \
                mock.patch.object(host_kit_tree, "tree_totals", return_value={}), \
                mock.patch.object(host_kit_tree, "_check_pair", side_effect=lambda step, *rest: seen.append(step)):
            host_kit_tree.check_snaps({}, [])
        self.assertEqual(seen, ["S11-door", "S99-wall", "S100-roof"])
