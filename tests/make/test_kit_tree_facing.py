"""ADR 0104 amendment 2026-11-19, rule h: a face pair is a joint only when
its faces face each other.

Two faces of neighbouring Parts facing the same way (one flush surface
across a seam), or meeting only along an edge, are no joint, so the
non-parallel check does not judge them. A real collision is still the
sweep's: the same Part shifted 0.3 mm sideways into its neighbour fails."""

from __future__ import annotations

import unittest

from tests.make.test_kit_tree import kit_tree
from tests.make.test_kit_tree_press_seat import check, joint_failures


class FlushSurfaceTest(unittest.TestCase):
    """A 45 degree roof in two Parts: the moving Part, lowered beside the
    base, continues the base's slope across a vertical seam."""

    def setUp(self):
        try:
            from build123d import Plane, Polygon, Pos, extrude
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.Plane, self.Polygon, self.Pos, self.extrude = Plane, Polygon, Pos, extrude

    def prism(self, *points):
        return self.extrude(self.Plane.XZ * self.Polygon(*points, align=None), amount=-10)

    def parts(self, across=0.0):
        base = self.prism((0, 0), (10, 0), (10, 10))
        piece = self.Pos(across, 0, 0) * self.prism((10, 0), (20, 0), (20, 20), (10, 10))
        return [("A01-base", base), ("A02-peg", piece)]

    def test_a_flush_slope_across_a_seam_is_no_joint(self):
        report = check(self.parts())
        self.assertEqual(joint_failures(report), [])

    def test_the_same_part_shifted_0_3_mm_into_its_neighbour_still_fails(self):
        report = check(self.parts(across=-0.3))
        self.assertTrue(any("cannot go in alone" in f for f in report["failures"]), report["failures"])

    def test_a_slope_facing_its_mate_is_still_judged(self):
        """The base's slope under the piece's own 45 degree underside: the
        faces face each other, so the pair is judged and fails."""
        base = self.prism((0, 0), (10, 0), (10, 10))
        piece = self.prism((0, 0.1), (10, 10.1), (10, 15), (0, 15))
        report = check([("A01-base", base), ("A02-peg", piece)], direction=(0, 0, 1))
        self.assertTrue(any("flat joint face at 45 deg" in f for f in report["failures"]), report["failures"])


class FacesEachOtherTest(unittest.TestCase):

    def setUp(self):
        try:
            import build123d as b
        except ImportError:                                   # pragma: no cover
            self.skipTest("build123d")
        self.b = b

    def square(self, origin, down=False):
        b = self.b
        plane = b.Plane(origin, z_dir=(0, 0, -1) if down else (0, 0, 1))
        return (plane * b.Rectangle(10, 10)).face()

    def test_opposed_faces_across_a_gap_face_each_other(self):
        self.assertTrue(kit_tree._faces_each_other(self.square((0, 0, 0)), self.square((0, 0, 0.2), down=True)))

    def test_faces_facing_the_same_way_do_not(self):
        self.assertFalse(kit_tree._faces_each_other(self.square((0, 0, 0)), self.square((10, 0, 0))))
        self.assertFalse(kit_tree._faces_each_other(self.square((0, 0, 0)), self.square((0, 0, 0.2))))

    def test_opposed_faces_meeting_only_along_an_edge_do_not(self):
        self.assertFalse(kit_tree._faces_each_other(self.square((0, 0, 0)), self.square((10, 0, 0), down=True)))

    def round_face(self, solid):
        return next(f for f in solid.faces() if f.geom_type == self.b.GeomType.CYLINDER)

    def test_a_peg_and_its_bore_face_each_other(self):
        b = self.b
        peg = self.round_face(b.Cylinder(2.0, 10))
        bore = self.round_face(b.Box(10, 10, 10) - b.Cylinder(2.1, 12))
        self.assertTrue(kit_tree._faces_each_other(peg, bore))

    def test_two_flush_drums_face_the_same_way(self):
        b = self.b
        lower = self.round_face(b.Pos(0, 0, 5) * b.Cylinder(20.0, 10))
        upper = self.round_face(b.Pos(0, 0, 15) * b.Cylinder(20.0, 10))
        self.assertFalse(kit_tree._faces_each_other(upper, lower))


if __name__ == "__main__":
    unittest.main()
