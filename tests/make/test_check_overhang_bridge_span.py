"""`check_overhang` measures a bridge's span across the ceiling, not its box.

A ceiling over an underside ring groove is a 5 mm bridge on a 103 mm circle:
the print head crosses the groove from its inner wall to its outer one. Its
bounding box and principal width are both the circle, so the gate read the
span as 103 mm and asked for support under a ceiling any printer bridges. A
ceiling as wide as the circle, or a straight one, is still measured as before.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

from build123d import Box, Cylinder, Pos

CAD = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


def _load():
    loader = importlib.machinery.SourceFileLoader("check_overhang_gate", str(CAD / "check_overhang"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


GATE = _load()


def _tris(shape):
    verts, faces = shape.tessellate(0.02, 0.1)
    pts = [(v.X, v.Y, v.Z) for v in verts]
    return [[list(pts[i]) for i in face] for face in faces]


def _kinds(shape):
    regions = GATE._measure(_tris(shape))
    return [r["kind"] for r in regions if r["kind"] != "trace"], regions


def _disc():
    """A 110 mm coaster 5 mm thick, its underside on Z 0."""
    return Pos(0, 0, 2.5) * Cylinder(55.0, 5.0)


def _ring(r_in, r_out, z0, z1):
    return Pos(0, 0, (z0 + z1) / 2) * (Cylinder(r_out, z1 - z0) - Cylinder(r_in, z1 - z0))


class BridgeSpanTests(unittest.TestCase):
    def test_annular_groove_ceiling_five_mm_wide_is_a_bridge(self):
        # The beaver coaster's groove: 46.75 to 51.75 mm, 2 mm deep.
        kinds, regions = _kinds(_disc() - _ring(46.75, 51.75, 0.0, 2.0))
        self.assertEqual(kinds, ["bridge"], [(r["kind"], r["span"]) for r in regions[:3]])
        self.assertLess(regions[0]["span"], 7.0)

    def test_full_disc_ceiling_of_the_same_diameter_still_needs_support(self):
        kinds, regions = _kinds(_disc() - Pos(0, 0, 1.0) * Cylinder(51.75, 2.0))
        self.assertEqual(kinds[:1], ["overhang"], [(r["kind"], r["span"]) for r in regions[:3]])
        self.assertGreater(regions[0]["span"], 100.0)

    def test_inward_lip_anchored_outside_only_still_needs_support(self):
        # The same 5 mm annulus, but a lip held by the outer wall alone: there
        # is nothing at its inner edge to bridge to.
        tube = _ring(51.75, 55.0, 0.0, 5.0) + _ring(46.75, 51.75, 3.0, 5.0)
        kinds, regions = _kinds(tube)
        self.assertEqual(kinds[:1], ["overhang"], [(r["kind"], r["span"]) for r in regions[:3]])

    def test_long_straight_slot_five_mm_wide_is_a_bridge(self):
        slot = Pos(0, 0, 2.5) * Box(120, 20, 5) - Pos(0, 0, 1.0) * Box(100, 5, 2)
        kinds, regions = _kinds(slot)
        self.assertEqual(kinds, ["bridge"], [(r["kind"], r["span"]) for r in regions[:3]])

    def test_wide_rectangular_ceiling_still_needs_support(self):
        pocket = Pos(0, 0, 2.5) * Box(60, 60, 5) - Pos(0, 0, 1.0) * Box(40, 30, 2)
        kinds, regions = _kinds(pocket)
        self.assertEqual(kinds[:1], ["overhang"], [(r["kind"], r["span"]) for r in regions[:3]])
        self.assertGreater(regions[0]["span"], 25.0)

    def test_self_check_passes(self):
        self.assertEqual(GATE._self_check(), 0)


if __name__ == "__main__":
    unittest.main()
