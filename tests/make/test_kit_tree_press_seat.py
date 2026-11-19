"""ADR 0104 amendment 2026-11-19: a press input and a seat face.

(d) A moving input of a peg-socket, tab-slot or pin-hinge step may declare
``press_mm``: its press ribs' bite a side. Its sweep uses the Part offset
inward by that depth, at the unchanged 0.001 mm3 limit; a Part the kernel
cannot offset is refused.

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

    def pressed(self, moving, depth):
        if self.refuse_offset:
            return None, "the kernel refuses to offset %s: offset Error" % moving[0].key
        return super().pressed(moving, depth)


def joint_failures(report):
    """The failures of the joint rules these fixtures test. A loose piece
    resting on a slope or in a cradle also fails the tilt hold (rule i),
    which tests/make/test_kit_tree_hold_walls.py covers."""

    return [failure for failure in report["failures"] if "does not stay seated" not in failure]


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
        self.assertEqual(joint_failures(report), [])
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
        self.assertEqual(joint_failures(report), [])
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


if __name__ == "__main__":
    unittest.main()
