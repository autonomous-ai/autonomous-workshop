"""ADR 0104 amendment 2026-11-19: a press input and a seat face.

(d) A moving input of a peg-socket, tab-slot or pin-hinge step may declare
``press_mm``: its press ribs' bite a side. Its sweep uses the Part offset
inward by that depth, at the unchanged 0.001 mm3 limit. A Part the kernel
cannot offset sweeps against its obstacles offset inward by that depth
instead (same amendment, press obstacles). Where neither offsets whole,
the Part is offset only in windows round its overlaps (amendment
2026-11-26, press local offset), exactly the whole offset there; a window
the kernel cannot offset either is shrunk by booleans, never looser than
the offset; a shrink that cannot be made anywhere is refused. Both sides
are held to the press (amendment 2026-11-27, #392): the real Part must
also clear its obstacles offset inward by it, so a rib thinner than twice
the press cannot vanish from the check.

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
        self.assertEqual((record["offset"], record["obstacles"]), ("input", "offset"))
        (sequence,) = report["conditions"]
        # both sides of the press (#392): the shrunk Part, then the real Part against shrunk obstacles
        (condition, other) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_mm"], 0.06)
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)
        self.assertEqual(other["id"], condition["id"] + ".obstacles-pressed")
        self.assertEqual(other["inputs"]["press_offset"], "obstacles")
        self.assertEqual(other["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)
        self.assertEqual(other["result"]["status"], "pass")

    def test_a_press_shifted_0_3_mm_sideways_still_fails(self):
        report = check(self.parts(across=0.3), press=0.06)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")

    def test_a_bite_deeper_than_its_declared_press_still_fails(self):
        report = check(self.parts(peg=4.4), press=0.06)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_a_part_the_kernel_cannot_offset_is_refused(self):
        from unittest import mock

        with mock.patch.object(kit_tree.CadGeometry, "eroded", return_value=(None, "the kernel's boolean fails")):
            report = check(self.parts(), press=0.06, refuse_offset=True)
        self.assertTrue(any("cannot be offset inward by its 0.06 mm press" in f and "refused" in f
                            for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")
        self.assertEqual(report["conditions"], [])

    def test_a_part_the_kernel_cannot_offset_whole_takes_windows_and_its_obstacles_still_shrink(self):
        report = check(self.parts(), press=0.06, refuse_offset="input")
        self.assertEqual(report["failures"], [])
        (record,) = report["presses"]
        self.assertEqual((record["offset"], record["obstacles"], record["verdict"]), ("local", "offset", "PASS"))
        (sequence,) = report["conditions"]
        (condition, other) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_offset"], "local")
        self.assertEqual(other["inputs"]["press_offset"], "obstacles")
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)

    def test_shrunk_obstacles_still_fail_a_shift_and_a_deeper_bite(self):
        for parts in (self.parts(across=0.3), self.parts(peg=4.4)):
            report = check(parts, press=0.06, refuse_offset="input")
            self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
            self.assertEqual(report["presses"][0]["verdict"], "FAIL")

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
            self.assertEqual((report["presses"][0]["obstacles"], report["presses"][0]["verdict"]), ("offset", "FAIL"))
            self.assertTrue(any("deeper than its press into them" in f for f in report["failures"]),
                            report["failures"])
            # a round peg has no corners to bite: the arc join passes it
            Box, Pos = self.Box, self.Pos
            from build123d import Cylinder
            base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Cylinder(2.0, 5)
            report = check([("A01-base", base), ("A02-peg", Pos(0, 0, 10) * Cylinder(2.05, 10))], press=0.06,
                           refuse_offset="input")
            self.assertEqual(report["failures"], [])
            self.assertEqual(report["presses"][0]["obstacles"], "offset")

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
        self.assertEqual((record["offset"], record["obstacles"], record["verdict"]), ("local", "local", "PASS"))
        (sequence,) = report["conditions"]
        (condition, other) = sequence["inputs"]["steps"]
        self.assertEqual(condition["inputs"]["press_offset"], "local")
        self.assertGreater(condition["inputs"]["press_windows"], 0)
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)
        # the base, which the kernel cannot offset whole either, is offset in windows round the peg
        self.assertEqual(other["inputs"]["press_offset"], "obstacles-local")
        self.assertNotIn("press_windows", other["inputs"])

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
        from unittest import mock

        with mock.patch.object(kit_tree.CadGeometry, "eroded", return_value=(None, "the kernel's boolean fails")):
            report = check(self.parts(), press=0.06, refuse_offset=True)
        (failure,) = [f for f in report["failures"] if "press input" in f]
        self.assertIn("cannot be offset inward by its 0.06 mm press", failure)
        self.assertIn("nor in windows round its overlaps", failure)
        self.assertIn("nor by booleans: the kernel's boolean fails", failure)
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


class PressErodeTest(unittest.TestCase):
    """ADR 0104 amendment 2026-11-26: a window cut the kernel cannot offset
    (Kyoto's crops: thin flat features the press removes whole) is shrunk
    by booleans, the common of the cut with copies of itself moved the
    press depth along each face normal. It keeps everything the arc offset
    keeps, so it is never looser."""

    def setUp(self):
        try:
            from build123d import Box, Cylinder, Kind, Pos, fillet, offset
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Cylinder, self.Kind, self.Pos = Box, Cylinder, Kind, Pos
        self.fillet, self.offset = fillet, offset
        self.local = PressLocalOffsetTest("test_windows_cover_every_overlap_and_split_long_ones")
        self.local.setUp()

    def test_a_rib_bite_passes_by_booleans_where_no_offset_can_be_made(self):
        # 0.03 a side: the boolean shrink of the socket keeps its inner corners
        # as a ball would, so the peg's corners bite 0.042 there, under the press
        report = check(self.local.parts(size=4.06), press=0.06, refuse_offset=True)
        self.assertEqual(report["failures"], [])
        (record,) = report["presses"]
        self.assertEqual((record["offset"], record["obstacles"], record["verdict"]), ("local", "local", "PASS"))
        (sequence,) = report["conditions"]
        (condition, other) = sequence["inputs"]["steps"]
        self.assertGreater(condition["inputs"]["press_eroded"], 0)
        self.assertEqual(condition["thresholds"]["maxOverlapMm3"], kit_tree.OVERLAP_MM3)

    def test_a_bite_of_0_3_mm_still_fails_by_booleans(self):
        report = check(self.local.parts(size=4.6), press=0.06, refuse_offset=True)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")

    def test_interference_away_from_the_joint_still_fails_by_booleans(self):
        report = check(self.local.parts(lug=1.0), press=0.06, refuse_offset=True)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_a_press_shifted_0_3_mm_sideways_still_fails_by_booleans(self):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        report = check([("A01-base", base), ("A02-peg", Pos(0.3, 0, 0) * self.local.peg())], press=0.06,
                       refuse_offset=True)
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_the_boolean_shrink_keeps_all_the_arc_offset_keeps(self):
        Box, Cylinder, Pos = self.Box, self.Cylinder, self.Pos
        shapes = {
            "box": Box(4, 4, 4),
            "L": Box(4, 4, 4) - Pos(1, 1, 0) * Box(2, 2, 5),
            "cylinder": Cylinder(2, 4),
            "fillet": self.fillet(Box(4, 4, 4).edges(), 0.5),
        }
        geometry = Built([])
        for name, shape in shapes.items():
            kept, error = geometry.eroded(shape, 0.1)
            self.assertIsNone(error, name)
            arc = self.offset(shape, amount=-0.1, kind=self.Kind.ARC)
            from build123d import Compound

            shrunk = Compound(kept)
            # nothing of the arc offset is missing, and nothing lies outside the Part
            self.assertLess(sum(s.volume for s in (arc - shrunk).solids()), 1e-6, name)
            self.assertLess(sum(s.volume for s in (shrunk - shape).solids()), 1e-6, name)
            self.assertGreaterEqual(shrunk.volume, arc.volume - 1e-6, name)
        # on flat faces it is the offset itself
        kept, _ = geometry.eroded(shapes["box"], 0.1)
        self.assertAlmostEqual(sum(s.volume for s in kept), 3.8 ** 3, places=6)

    def test_the_boolean_shrink_clears_a_socket_s_inner_corner(self):
        # Face normals alone keep a press-deep square along a concave edge;
        # the bisector of its two faces clears it, as the arc offset does.
        from build123d import Compound
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.gp import gp_Pnt
        from OCP.TopAbs import TopAbs_IN

        Box = self.Box
        socket = Box(10, 10, 4) - Box(4, 4, 5)
        kept, error = Built([]).eroded(socket, 0.06)
        self.assertIsNone(error)
        corner = gp_Pnt(2.03, 2.03, 0)    # 0.042 from the socket's inner corner edge
        self.assertFalse(any(BRepClass3d_SolidClassifier(k.wrapped, corner, 1e-7).State() == TopAbs_IN
                             for k in kept))
        arc = self.offset(socket, amount=-0.06, kind=self.Kind.ARC)
        self.assertLess(sum(x.volume for x in (arc - Compound(kept)).solids()), 1e-6)

    def test_a_boolean_that_silently_drops_material_is_refused(self):
        from unittest import mock

        from OCP.TopoDS import TopoDS_Compound
        from OCP.BRep import BRep_Builder

        class Empty:
            def __init__(self, *args):
                self.shape = TopoDS_Compound()
                BRep_Builder().MakeCompound(self.shape)

            def IsDone(self):
                return True

            def Shape(self):
                return self.shape

        with mock.patch("OCP.BRepAlgoAPI.BRepAlgoAPI_Common", Empty):
            kept, error = Built([]).eroded(self.Box(4, 4, 4), 0.1)
        self.assertIsNone(kept)
        self.assertIn("drops a point", error)

    def test_a_boolean_the_kernel_reports_failed_is_refused(self):
        from unittest import mock

        class Failed:
            def __init__(self, *args):
                pass

            def IsDone(self):
                return False

        with mock.patch("OCP.BRepAlgoAPI.BRepAlgoAPI_Common", Failed):
            kept, error = Built([]).eroded(self.Box(4, 4, 4), 0.1)
        self.assertIsNone(kept)
        self.assertIn("boolean fails", error)

    def test_windows_the_kernel_cannot_sweep_as_one_sweep_solid_by_solid(self):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        obstacles = [kit_tree.Body("A01-base", base, key="A01-base#1")]

        def sweep(pieces, local="local"):
            geometry = Built([])
            run = geometry.motion["run_condition"]

            def refuse_groups(condition, parts, index):
                if len(parts[condition["inputs"]["moving_part"]].solids()) > 1:
                    return {"status": "inconclusive", "detail": "motion Boolean operation returned invalid geometry"}
                return run(condition, parts, index)

            geometry.motion = dict(geometry.motion, run_condition=refuse_groups)
            condition = {"id": "c", "check": "linear_motion_collision", "expect": "clear",
                         "inputs": {"moving_part": "A02-peg#1", "obstacle_parts": ["A01-base#1"],
                                    "translation": [0, 0, 11.0], "steps": 14, "allow_seated_contact": True},
                         "thresholds": {"maxOverlapMm3": kit_tree.OVERLAP_MM3, "maxStepMm": 0.8}}
            if local:
                condition["inputs"]["press_offset"] = local
            moving = [kit_tree.Body("A02-peg", piece, key="A02-peg#1@%d" % i) for i, piece in enumerate(pieces)]
            return geometry.sweep(condition, moving, obstacles), geometry.fallbacks

        clear = [Pos(0, 0, 7.5) * Box(3.9, 3.9, 5), Pos(0, 0, 12.5) * Box(3.9, 3.9, 5)]
        # the Part's windows, and a group against its obstacles' shrink (#392)
        for kind in ("local", "obstacles", "obstacles-local"):
            result, fallbacks = sweep(clear, kind)
            self.assertEqual(result["status"], "pass", kind)
            (record,) = fallbacks
            self.assertEqual(record["solids"], 2)
            self.assertAlmostEqual(record["max_overlap_mm3_each"], kit_tree.OVERLAP_MM3 / 2)
        # a piece that bites still fails solid by solid
        result, _ = sweep([Pos(0, 0, 7.5) * Box(4.4, 4.4, 5), clear[1]])
        self.assertEqual(result["status"], "fail")
        # only a press offset's group takes this path
        result, fallbacks = sweep(clear, local=None)
        self.assertEqual((result["status"], fallbacks), ("inconclusive", []))

    def test_a_thin_part_has_no_deep_point_to_miss(self):
        # a 0.15 mm sheet is wholly within 0.1 of its faces: an empty shrink is right
        self.assertIsNone(kit_tree._deep_point_missing(self.Box(4, 4, 0.15), [], 0.1))
        self.assertIsNotNone(kit_tree._deep_point_missing(self.Box(4, 4, 4), [], 0.1))


class PressTwoSidedTest(unittest.TestCase):
    """ADR 0104 amendment 2026-11-27 (#392): a 4.0 mm peg in a 4.0 mm socket
    with four ribs 5 mm long, at ``press_mm`` 0.1. A rib thinner than twice
    the press vanishes when the Part is offset; the real Part against the
    socket offset by the press still measures its bite."""

    def setUp(self):
        try:
            from build123d import Box, Pos
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Box, self.Pos = Box, Pos

    def base(self, rib=None):
        Box, Pos = self.Box, self.Pos
        base = Pos(0, 0, 5) * Box(20, 20, 10) - Pos(0, 0, 7.5) * Box(4, 4, 5)
        if rib is not None:
            # a rib on the socket's wall, into the cavity
            width, bite = rib
            base = base + Pos(2 - bite / 2, 0, 7.5) * Box(bite, width, 5)
        return base

    def peg(self, width=None, bite=None):
        Box, Pos = self.Box, self.Pos
        peg = Pos(0, 0, 10) * Box(4, 4, 10)
        if width is not None:
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                size = (bite, width) if sx else (width, bite)
                peg = peg + Pos(sx * (2 + bite / 2), sy * (2 + bite / 2), 7.5) * Box(size[0], size[1], 5)
        return peg

    def verdict(self, peg, base=None):
        report = check([("A01-base", base or self.base()), ("A02-peg", peg)], press=0.1)
        return report["presses"][0]["verdict"], report

    def test_a_rib_0_19_wide_biting_1_mm_now_fails(self):
        verdict, report = self.verdict(self.peg(0.19, 1.0))
        self.assertEqual(verdict, "FAIL")
        (failure,) = report["failures"]
        self.assertIn("against its obstacles offset inward by its 0.1 mm press", failure)
        self.assertIn("deeper than its press into them", failure)
        (sequence,) = report["conditions"]
        (condition, other) = sequence["inputs"]["steps"]
        self.assertEqual((condition["result"]["status"], other["result"]["status"]), ("pass", "fail"))

    def test_thin_ribs_biting_deeper_than_the_press_fail(self):
        for width, bite in ((0.15, 0.3), (0.19, 0.3)):
            self.assertEqual(self.verdict(self.peg(width, bite))[0], "FAIL", (width, bite))

    def test_a_rib_0_25_wide_biting_0_3_still_fails(self):
        verdict, report = self.verdict(self.peg(0.25, 0.3))
        self.assertEqual(verdict, "FAIL")
        # the shrunk Part already fails: the other side is not swept
        (sequence,) = report["conditions"]
        (condition,) = sequence["inputs"]["steps"]
        self.assertEqual(condition["result"]["status"], "fail")

    def test_ribs_biting_at_most_the_press_still_pass(self):
        for width, bite in ((0.5, 0.1), (0.5, 0.08), (0.19, 0.1), (0.3, 0.05)):
            verdict, report = self.verdict(self.peg(width, bite))
            self.assertEqual(verdict, "PASS", (width, bite, report["failures"]))

    def test_a_thin_rib_on_the_socket_biting_deeper_than_the_press_fails(self):
        self.assertEqual(self.verdict(self.peg(), self.base(rib=(0.19, 1.0)))[0], "FAIL")
        self.assertEqual(self.verdict(self.peg(), self.base(rib=(0.19, 0.1)))[0], "PASS")

    def test_an_obstacle_side_that_cannot_be_shrunk_is_refused(self):
        from unittest import mock

        with mock.patch.object(kit_tree.CadGeometry, "shrunk_obstacles",
                               return_value=(None, None, "the kernel refuses to offset A01-base#1")):
            report = check([("A01-base", self.base()), ("A02-peg", self.peg(0.5, 0.1))], press=0.1)
        (failure,) = report["failures"]
        self.assertIn("its obstacles cannot be offset inward by it either", failure)
        self.assertIn("refused", failure)
        self.assertEqual(report["presses"][0]["verdict"], "FAIL")
        self.assertEqual(report["conditions"], [])

    def test_an_offset_that_fills_the_socket_is_not_taken(self):
        # Kyoto S11 (#392): the kernel's sharp offset of a cropped kerb was a
        # valid, smaller solid that filled the hole the trunk goes into. A
        # shrink holding material outside its body is not taken: the arc
        # join is, and an honest peg still passes.
        from unittest import mock

        import build123d

        Box, Pos = self.Box, self.Pos
        real = build123d.offset

        def filled(shape, *args, **kwargs):
            result = real(shape, *args, **kwargs)
            if kwargs.get("kind") == build123d.Kind.INTERSECTION:
                result = result + Pos(0, 0, 7.5) * Box(1, 1, 1)
            return result

        with mock.patch.object(build123d, "offset", side_effect=filled):
            verdict, report = self.verdict(self.peg(0.5, 0.1))
            self.assertEqual(verdict, "PASS", report["failures"])
            shrunk, error = Built([]).pressed([kit_tree.Body(None, self.base(), key="A01-base#1")], 0.1,
                                              sharp=True)
        self.assertIsNone(error)
        self.assertEqual(len((shrunk[0].shape & (Pos(0, 0, 7.5) * Box(1, 1, 1))).solids()), 0)

    def test_a_kernel_crash_in_the_sharp_offset_takes_the_arc_join(self):
        # Kyoto S13 (#392): the intersection join crashed the process. It
        # runs in a child, so the crash is a refused offset and the
        # stricter arc join decides; the round goes on.
        import os
        from unittest import mock

        import build123d

        real = build123d.offset

        def crashing(shape, *args, **kwargs):
            if kwargs.get("kind") == build123d.Kind.INTERSECTION:
                os.abort()
            return real(shape, *args, **kwargs)

        with mock.patch.object(build123d, "offset", side_effect=crashing):
            verdict, report = self.verdict(self.peg(0.5, 0.1))
            self.assertEqual(verdict, "PASS", report["failures"])
            self.assertEqual(report["presses"][0]["obstacles"], "offset")
            self.assertEqual(self.verdict(self.peg(0.19, 1.0))[0], "FAIL")

    def test_a_sharp_offset_that_never_finishes_takes_the_arc_join(self):
        # Kyoto S61 (#392): the intersection join ran for half an hour. A
        # child still running after PRESS_OFFSET_SECONDS is refused.
        import time
        from unittest import mock

        import build123d

        real = build123d.offset

        def stalling(shape, *args, **kwargs):
            if kwargs.get("kind") == build123d.Kind.INTERSECTION:
                time.sleep(60)
            return real(shape, *args, **kwargs)

        started = time.monotonic()
        with mock.patch.object(build123d, "offset", side_effect=stalling), \
                mock.patch.dict(kit_tree._isolated_offset.__globals__, {"PRESS_OFFSET_SECONDS": 1}):
            verdict, report = self.verdict(self.peg(0.5, 0.1))
        self.assertEqual(verdict, "PASS", report["failures"])
        self.assertLess(time.monotonic() - started, 30)

    def test_an_obstacle_sweep_the_kernel_cannot_run_is_refused_not_a_bite(self):
        from unittest import mock

        real = kit_tree.CadGeometry.sweep

        def broken(self, condition, moving, obstacles):
            if condition["id"].endswith(".obstacles-pressed"):
                return {"status": "inconclusive", "detail": "motion Boolean operation returned invalid geometry"}
            return real(self, condition, moving, obstacles)

        with mock.patch.object(kit_tree.CadGeometry, "sweep", broken):
            verdict, report = self.verdict(self.peg(0.5, 0.1))
        self.assertEqual(verdict, "FAIL")
        (failure,) = report["failures"]
        self.assertIn("cannot be checked: motion Boolean operation returned invalid geometry: refused", failure)
        self.assertNotIn("bites deeper", failure)

    def test_a_shrink_outside_its_body_is_not_smaller(self):
        Box, Pos = self.Box, self.Pos
        whole = Box(10, 10, 10)
        self.assertIsNotNone(kit_tree._smaller(Box(9, 9, 9), whole))
        self.assertIsNone(kit_tree._smaller(Pos(1, 0, 0) * Box(9, 9, 9), whole))


if __name__ == "__main__":
    unittest.main()
