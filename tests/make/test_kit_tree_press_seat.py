"""ADR 0104 amendment 2026-11-19: a press input and a seat face.

(d) A moving input of a peg-socket, tab-slot or pin-hinge step may declare
``press_mm``: its press ribs' bite a side. Its sweep uses the Part offset
inward by that depth, at the unchanged 0.001 mm3 limit. A Part the kernel
cannot offset sweeps against its obstacles offset inward by that depth
instead (same amendment, press obstacles). Where neither offsets whole,
the Part is offset only in windows round its overlaps (amendment
2026-11-26, press local offset), exactly the whole offset there; an offset
that cannot be made anywhere is refused.

(e) A flat joint face at an angle to the direction, or a round one whose
axis is off it, is accepted only as a seat face: the input's outward normal
has n.d > 0 at every sample point, so it leads into its stop, and the
input's sweep is clean.

Both are checked on real build123d solids through the component round's
own ``check_component``; a 0.3 mm shift sideways, a real collision, still
fails under each rule."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.make.test_kit_tree import kit_tree
from tests.wish.test_assembly_tree import _step  # noqa: F401 - the contract tests' helpers stay importable
from workshop.wish import assembly_tree as host_tree

OAK = "#b5834f"


def kit(joint="peg-socket", press=None, direction=(0, 0, -1)):
    moving = {"id": "A02-peg", "direction": list(direction)}
    if press is not None:
        moving["press_mm"] = press
    return {
        "kind": kit_tree.KIT_KIND, "schema_version": kit_tree.INSTALL_SCHEMA, "pieces": [],
        "geometries": [{"id": "block", "count": 1, "wall_min_mm": 1.2}],
        "catalogue": {"filaments": {"oak": {"hex": OAK}}, "bought_parts": {}},
        "assembly_tree": {
            "parts": [{"id": "A01-base", "name": "Base", "filament": "oak"},
                      {"id": "A02-peg", "name": "Peg", "filament": "oak"}],
            "steps": [{"id": "S01-peg", "output": "Block", "count": 1, "joint": joint, "text": "Peg in.",
                       "inputs": [{"id": "A01-base"}, moving]}],
            "components": [{"geometry": "block", "parts": ["A01-base", "A02-peg"]}],
        },
    }


class Built(kit_tree.CadGeometry):
    """The real build123d backend over solids given here, not a project."""

    def __init__(self, parts, refuse_offset=False):
        super().__init__(Path(tempfile.mkdtemp()))
        self.parts = parts
        self.refuse_offset = refuse_offset

    def instances(self, role):
        return [1]

    def component(self, role, instance):
        return [kit_tree.Body(label, shape, colours=(OAK,)) for label, shape in self.parts]

    def pressed(self, moving, depth, sharp=False):
        # refuse_offset: True refuses every offset; "input" only the moving peg's,
        # so its obstacles are offset instead (press obstacles)
        # "whole": both whole Parts refuse, as Kyoto's do; a window's cut is offset
        if self.refuse_offset is True or (self.refuse_offset == "input" and moving[0].key.startswith("A02-")) or (
                self.refuse_offset == "whole" and moving[0].key != "window"):
            return None, "the kernel refuses to offset %s: offset Error" % moving[0].key
        return super().pressed(moving, depth, sharp)


def check(parts, **options):
    refuse = options.pop("refuse_offset", False)
    plan = kit_tree.Plan(kit(**options))
    return kit_tree.check_component(plan, Built(parts, refuse), "block", 0.4)


class PressTest(unittest.TestCase):
    """A 4 mm square socket and a 4.1 mm peg: press ribs 0.05 a side."""

    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos = Box, Pos

    def parts(self, across=0.0, peg=4.1):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        return [("A01-base", base), ("A02-peg", Pos(across, 0, 10) * Box(peg, peg, 10))]

    def test_without_press_mm_the_ribs_block_it(self):
        report = check(self.parts())
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"], [])

    def test_a_declared_press_sweeps_the_shrunk_part_and_passes(self):
        report = check(self.parts(), press=0.06)
        self.assertEqual(report["failures"], [])
        (record,) = report["presses"]
        self.assertEqual((record["input"], record["press_mm"], record["verdict"]), ("A02-peg#1", 0.06, "PASS"))
        (sequence,) = report["conditions"]
        (condition,) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_mm"], 0.06)
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)

    def test_a_press_shifted_0_3_mm_sideways_still_fails(self):
        report = check(self.parts(across=0.3), press=0.06)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")

    def test_a_bite_deeper_than_its_declared_press_still_fails(self):
        report = check(self.parts(peg=4.4), press=0.06)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_a_part_the_kernel_cannot_offset_is_refused(self):
        report = check(self.parts(), press=0.06, refuse_offset=True)
        self.assertTrue(any("cannot be offset inward by its 0.06 mm press" in f and "refused" in f
                            for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")
        self.assertEqual(report["conditions"], [])

    def test_a_part_the_kernel_cannot_offset_sweeps_against_its_shrunk_obstacles(self):
        report = check(self.parts(), press=0.06, refuse_offset="input")
        self.assertEqual(report["failures"], [])
        (record,) = report["presses"]
        self.assertEqual((record["offset"], record["verdict"]), ("obstacles", "PASS"))
        (sequence,) = report["conditions"]
        (condition,) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_offset"], "obstacles")
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)

    def test_shrunk_obstacles_still_fail_a_shift_and_a_deeper_bite(self):
        for parts in (self.parts(across=0.3), self.parts(peg=4.4)):
            report = check(parts, press=0.06, refuse_offset="input")
            self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
            self.assertEqual((report["presses"][0]["offset"], report["presses"][0]["verdict"]), ("obstacles", "FAIL"))

    def test_an_obstacle_the_kernel_cannot_join_sharp_takes_the_stricter_arc_join(self):
        from unittest import mock

        import build123d

        real = build123d.offset

        def no_sharp(*args, **kwargs):
            if kwargs.get("kind") == build123d.Kind.INTERSECTION:
                raise RuntimeError("offset Error")
            return real(*args, **kwargs)

        with mock.patch.object(build123d, "offset", no_sharp):
            # the arc join rounds the socket's corners: the 4.1 peg's corners still bite at 0.06
            report = check(self.parts(), press=0.06, refuse_offset="input")
            self.assertEqual((report["presses"][0]["offset"], report["presses"][0]["verdict"]), ("obstacles", "FAIL"))
            # a round peg has no corners to bite: the arc join passes it
            Box, Pos = self.Box, self.Pos
            from build123d import Cylinder
            base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Cylinder(2.0, 5)
            report = check([("A01-base", base), ("A02-peg", Pos(0, 0, 10) * Cylinder(2.05, 10))], press=0.06,
                           refuse_offset="input")
            self.assertEqual(report["failures"], [])
            self.assertEqual(report["presses"][0]["offset"], "obstacles")

    def test_the_real_offset_shrinks_the_part(self):
        Box = self.Box
        body = kit_tree.Body("A02-peg", Box(4, 4, 4), key="A02-peg#1")
        (shrunk,), error = Built([]).pressed([body], 0.06)
        self.assertIsNone(error)
        size = shrunk.shape.bounding_box().size
        self.assertAlmostEqual(size.X, 3.88, places=3)
        self.assertLess(shrunk.shape.volume, body.shape.volume)

    def test_a_placed_part_is_offset_where_it_stands(self):
        from build123d import Location

        body = kit_tree.Body("A02-peg", self.Box(4, 4, 4).located(Location((62, 39, 8))), key="A02-peg#1")
        (shrunk,), error = Built([]).pressed([body], 0.06)
        self.assertIsNone(error)
        centre = shrunk.shape.bounding_box().center()
        self.assertAlmostEqual(centre.X, 62, places=3)
        self.assertAlmostEqual(centre.Z, 8, places=3)


class SeatFaceTest(unittest.TestCase):
    """A 45 degree wedge base and a piece resting on its slope, pushed down
    onto it; a wall at the slope's top end is what a sideways slip meets."""

    def setUp(self):
        try:
            from build123d import Axis, Box, Cylinder, Plane, Polygon, Pos, Rot, extrude
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.b = dict(Axis=Axis, Box=Box, Cylinder=Cylinder, Plane=Plane, Polygon=Polygon, Pos=Pos, Rot=Rot,
                      extrude=extrude)

    def prism(self, *points):
        b = self.b
        return b["extrude"](b["Plane"].XZ * b["Polygon"](*points, align=None), amount=-10)

    def wedge_parts(self, across=0.0, lid=False):
        b = self.b
        base = self.prism((0, 0), (10, 0), (10, 10)) + b["Pos"](11, 5, 10) * b["Box"](2, 10, 20)
        piece = b["Pos"](across, 0, 0) * self.prism((0, 0.0), (10, 10), (0, 10))
        parts = [("A01-base", base), ("A02-peg", piece)]
        if lid:
            parts[0] = ("A01-base", base + b["Pos"](5, 5, 13) * b["Box"](4, 4, 2))
        return parts

    def test_the_seat_is_a_flat_joint_face_at_45_degrees(self):
        report = check(self.wedge_parts())
        self.assertEqual(report["failures"], [])
        self.assertTrue(report["seats"])
        self.assertTrue(all("45 deg" in record["face"] for record in report["seats"]), report["seats"])

    def test_a_seat_shifted_0_3_mm_sideways_still_fails(self):
        report = check(self.wedge_parts(across=0.3))
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertTrue(any("not parallel" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["seats"], [])

    def test_a_seat_whose_sweep_is_blocked_is_still_judged_non_parallel(self):
        report = check(self.wedge_parts(lid=True))
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertTrue(any("flat joint face at 45 deg" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["seats"], [])

    def test_a_face_that_does_not_lead_into_its_stop_is_no_seat(self):
        from build123d import Vector

        piece = self.wedge_parts()[1][1]
        slope = next(face for face in piece.faces()
                     if abs(abs(face.normal_at(face.center()).X) - 0.7071) < 1e-3)
        self.assertTrue(kit_tree._seat_face(slope, Vector(0, 0, -1)))
        self.assertFalse(kit_tree._seat_face(slope, Vector(0, 0, 1)))
        self.assertFalse(kit_tree._seat_face(slope, Vector(-1, 0, 0)))

    def cradle_parts(self, across=0.0, whole=False):
        b = self.b
        rod = b["Pos"](0, 0, 5) * (b["Rot"](90, 0, 0) * b["Cylinder"](3, 10))
        base = b["Pos"](0, 0, 2.5) * b["Box"](14, 10, 5) - rod
        piece = rod if whole else rod + b["Pos"](0, 0, 7) * b["Box"](6, 10, 4)
        return [("A01-base", base), ("A02-peg", b["Pos"](across, 0, 0) * piece)]

    def test_a_round_seat_across_the_direction_is_accepted(self):
        report = check(self.cradle_parts())
        self.assertEqual(report["failures"], [])
        self.assertTrue(any("axis is 90 deg off" in record["face"] for record in report["seats"]),
                        report["seats"])

    def test_a_whole_rod_is_no_seat(self):
        report = check(self.cradle_parts(whole=True))
        self.assertTrue(any("axis is 90 deg off" in f for f in report["failures"]), report["failures"])

    def test_a_round_seat_shifted_0_3_mm_sideways_still_fails(self):
        report = check(self.cradle_parts(across=0.3))
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])


class ContractSyntaxTest(unittest.TestCase):
    """``press_mm`` in the contract: a moving input of a peg-socket,
    tab-slot or pin-hinge step, above 0 and at most 0.1."""

    def errors(self, joint="peg-socket", press=0.06, on_base=False):
        tree = kit(joint, press)["assembly_tree"]
        if on_base:
            tree["steps"][0]["inputs"][0]["press_mm"] = press
            del tree["steps"][0]["inputs"][1]["press_mm"]
        if joint == "snap":
            tree["steps"][0]["snap"] = {"part": "A02-peg", "catch": "A01-base", "catch_mm": 0.3}
        errors = []
        steps, _ = host_tree._parse_steps(tree["steps"], {"A01-base": "block", "A02-peg": "block"},
                                          host_tree._Ids(errors), errors)
        return errors

    def test_a_press_on_each_pressing_joint_is_accepted(self):
        for joint in host_tree.PRESSES:
            self.assertEqual(self.errors(joint), [], joint)

    def test_a_press_elsewhere_or_out_of_range_is_refused(self):
        self.assertTrue(any("press_mm belongs to" in e for e in self.errors("snap")))
        self.assertTrue(any("press_mm belongs to" in e for e in self.errors("glue")))
        self.assertTrue(any("press_mm belongs to" in e for e in self.errors(on_base=True)))
        for bad in (0, -0.05, 0.11, True, "0.06"):
            self.assertTrue(any("press_mm must be" in e for e in self.errors(press=bad)), bad)



class PressLocalOffsetTest(unittest.TestCase):
    """ADR 0104 amendment 2026-11-26, press local offset: a peg with a name
    embossed on its top, which the kernel cannot offset whole (it returns a
    null shape, as Kyoto's Parts do), pressed into a 4 mm socket whose base
    the kernel cannot offset either."""

    def setUp(self):
        try:
            from build123d import Box, Pos, Rot, Text, extrude
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos, self.Rot, self.Text, self.extrude = Box, Pos, Rot, Text, extrude

    def peg(self, size=4.1, lug=None):
        Box, Pos, Rot = self.Box, self.Pos, self.Rot
        name = Pos(0, size / 2, 17) * Rot(-90, 0, 0) * self.extrude(self.Text("KYOTO", 1.5), 0.12)
        peg = Pos(0, 0, 12.5) * Box(size, size, 15) + name
        if lug is not None:
            # an arm out to x = 7, its foot ``lug`` mm into the base's top at the seat
            peg = peg + Pos(4.5, 0, 12.5 - lug) * Box(5, 2, 5)
        return peg

    def parts(self, **peg):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        return [("A01-base", base), ("A02-peg", self.peg(**peg))]

    def test_the_kernel_cannot_offset_the_named_peg_whole(self):
        body = kit_tree.Body("A02-peg", self.peg(), key="A02-peg#1")
        shrunk, error = Built([]).pressed([body], 0.06)
        self.assertIsNone(shrunk)
        self.assertIn("A02-peg#1", error)

    def test_a_part_offset_round_its_overlaps_passes_a_rib_bite(self):
        report = check(self.parts(), press=0.06, refuse_offset="whole")
        self.assertEqual(report["failures"], [])
        (record,) = report["presses"]
        self.assertEqual((record["offset"], record["verdict"]), ("local", "PASS"))
        (sequence,) = report["conditions"]
        (condition,) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_offset"], "local")
        self.assertGreater(condition["inputs"]["press_windows"], 0)
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)

    def test_the_real_kernel_failure_takes_the_local_offset(self):
        # Only the base's offset is refused here: the peg's whole offset fails in the kernel itself.
        class BaseRefused(Built):
            def pressed(self, moving, depth, sharp=False):
                if moving[0].key.startswith("A01-"):
                    return None, "the kernel refuses to offset %s: offset Error" % moving[0].key
                return kit_tree.CadGeometry.pressed(self, moving, depth, sharp)

        plan = kit_tree.Plan(kit(press=0.06))
        report = kit_tree.check_component(plan, BaseRefused(self.parts()), "block", 0.4)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["presses"][0]["offset"], "local")

    def test_a_bite_of_0_3_mm_still_fails(self):
        report = check(self.parts(size=4.6), press=0.06, refuse_offset="whole")
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual((report["presses"][0]["offset"], report["presses"][0]["verdict"]), ("local", "FAIL"))

    def test_a_press_shifted_0_3_mm_sideways_still_fails(self):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        report = check([("A01-base", base), ("A02-peg", Pos(0.3, 0, 0) * self.peg())], press=0.06,
                       refuse_offset="whole")
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_interference_away_from_the_joint_still_fails(self):
        # An arm 5 mm off the socket whose foot ploughs 1 mm into the base's top: it
        # still overlaps after the first step out (the seat itself is seated contact).
        report = check(self.parts(lug=1.0), press=0.06, refuse_offset="whole")
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual((report["presses"][0]["offset"], report["presses"][0]["verdict"]), ("local", "FAIL"))

    def test_an_offset_no_window_can_take_is_refused_never_passed(self):
        report = check(self.parts(), press=0.06, refuse_offset=True)
        (failure,) = [f for f in report["failures"] if "press input" in f]
        self.assertIn("cannot be offset inward by its 0.06 mm press", failure)
        self.assertIn("nor in windows round its overlaps", failure)
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")
        self.assertEqual(report["conditions"], [])

    def test_a_simple_part_takes_the_whole_offset_and_never_the_windows(self):
        from unittest import mock

        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        parts = [("A01-base", base), ("A02-peg", Pos(0, 0, 10) * Box(4.1, 4.1, 10))]
        with mock.patch.object(kit_tree.CadGeometry, "pressed_local", side_effect=AssertionError("not used")):
            report = check(parts, press=0.06)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["presses"][0]["offset"], "input")

    def test_the_windows_measure_what_the_whole_offset_measures(self):
        # Where the kernel can offset the Part whole, both give the same overlap at every depth.
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        geometry = Built([])
        moving = [kit_tree.Body("A02-peg", Pos(0, 0, 10) * Box(4.2, 4.2, 10), key="A02-peg#1")]
        obstacles = [kit_tree.Body("A01-base", base, key="A01-base#1")]
        for depth in (0.03, 0.06, 0.12):
            condition = {"id": "c", "check": "linear_motion_collision", "expect": "clear",
                         "inputs": {"moving_part": "A02-peg#1", "obstacle_parts": ["A01-base#1"],
                                    "translation": [0, 0, 11.0], "steps": 14, "allow_seated_contact": True},
                         "thresholds": {"maxOverlapMm3": kit_tree.OVERLAP_MM3, "maxStepMm": 0.8}}
            whole, _ = geometry.pressed(moving, depth)
            local, error = geometry.pressed_local(dict(condition, inputs=dict(condition["inputs"])), moving,
                                                  obstacles, depth)
            self.assertIsNone(error)
            a, b = geometry.sweep(condition, whole, obstacles), geometry.sweep(condition, local, obstacles)
            self.assertEqual(a.get("status"), b.get("status"), depth)
            self.assertAlmostEqual(float(a.get("overlapMm3") or 0), float(b.get("overlapMm3") or 0), places=6)

    def test_windows_cover_every_overlap_and_split_long_ones(self):
        boxes = [((0, 0, 0), (1, 1, 1)), ((0.2, 0.2, 0.2), (0.8, 0.8, 0.8)), ((0, 0, 0), (20, 1, 1))]
        windows = kit_tree._press_windows(boxes, tile=8.0)
        # the inner box drops; the 20 mm one is three tiles; the unit box lies inside the first tile
        self.assertEqual(len(windows), 3)
        self.assertEqual(windows[0][0], (0, 0, 0))
        self.assertAlmostEqual(windows[-1][1][0], 20)
        for lo, hi in boxes:
            # every point of every overlap box lies in some window: its corners do, per tile
            for corner in (lo, hi):
                self.assertTrue(any(all(a - 1e-9 <= c <= b + 1e-9 for a, c, b in zip(wlo, corner, whi))
                                    for wlo, whi in windows), corner)


if __name__ == "__main__":
    unittest.main()
