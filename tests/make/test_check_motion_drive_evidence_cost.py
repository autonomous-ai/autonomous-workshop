"""Drive-evidence cost controls must not change what the rule measures.

A published product's coupled cycle took 369 s at HEAD: 244 s in 1,094
whole-part distance queries for pairs that never touch and 70 s deep-copying
the same placements for every pair. Placements are now made once per mover
and sample, and the contact query runs on the faces that can realize a
contact, with an exact answer whenever it is within the contact tolerance.
"""
from dataclasses import dataclass
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from build123d import Box, Compound

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


@dataclass(frozen=True)
class NumericBox:
    center: float
    size: float


class PlacementCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def test_each_mover_is_placed_once_per_sample(self):
        steps = 6
        calls = []

        def place_for(name, offsets):
            def place(shape, index):
                calls.append((name, index))
                return NumericBox(shape.center + offsets[index], shape.size)
            return place

        def overlap(a, b, *_):
            width = max(0., min(a.center + a.size / 2, b.center + b.size / 2)
                        - max(a.center - a.size / 2, b.center - b.size / 2))
            return width * min(a.size, b.size) ** 2

        placed = [
            ("input", NumericBox(0, 1), place_for("input", [i * 0.5 for i in range(steps + 1)]), False),
            ("out_a", NumericBox(1, 1), place_for("out_a", [i * 0.5 for i in range(steps + 1)]), True),
            ("out_b", NumericBox(2, 1), place_for("out_b", [i * 0.5 for i in range(steps + 1)]), True),
        ]
        with patch.dict(self.tool["sampled_drive_evidence"].__globals__,
                        overlap_volume=overlap,
                        surface_distance=lambda a, b, **_: max(0., abs(a.center - b.center) - (a.size + b.size) / 2)):
            evidence = self.tool["sampled_drive_evidence"](placed, steps, 1e-3, False)
        self.assertEqual(evidence["unreachedDrivenParts"], [])
        self.assertLessEqual(len(calls), len(placed) * (steps + 1))
        self.assertEqual(len(calls), len(set(calls)), "a mover/sample pair was placed twice")


class NearFaceDistanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def distance(self, *args, **kwargs):
        return self.tool["surface_distance"](*args, **kwargs)

    def test_default_remains_the_exact_whole_part_distance(self):
        self.assertAlmostEqual(self.distance(Box(2, 2, 2), Box(2, 2, 2).translate((2.5, 0, 0))), 0.5)

    def test_contact_within_tolerance_is_exact(self):
        touching = Box(2, 2, 2).translate((2, 0, 0))
        self.assertEqual(self.distance(Box(2, 2, 2), touching, within=1e-6), 0.0)
        # A pocket whose floor touches the insert: contact realized by inner faces.
        pocket = Box(10, 10, 10) - Box(2, 2, 6).translate((0, 0, 2))
        insert = Box(2, 2, 2).translate((0, 0, 0))
        self.assertEqual(self.distance(pocket, insert, within=1e-6), 0.0)

    def test_far_parts_certify_only_that_the_gap_exceeds_the_tolerance(self):
        value = self.distance(Box(2, 2, 2), Box(2, 2, 2).translate((2.5, 0, 0)), within=1e-6)
        self.assertGreater(value, 1e-6)
        self.assertAlmostEqual(value, 0.5)

    def test_small_gap_inside_the_bounding_overlap_is_not_a_contact(self):
        # Boxes whose bounding boxes overlap while the nearest faces stay 0.01 mm apart.
        first = Box(4, 4, 4)
        second = Box(2, 2, 2).translate((3.01, 0, 0))
        self.assertGreater(self.distance(first, second, within=1e-6), 1e-6)
        self.assertLessEqual(self.distance(first, second, within=1e-6), 0.01 + 1e-9)

    def test_nested_material_with_a_thin_gap_is_measured_from_its_near_faces(self):
        ring = Box(10, 10, 4) - Box(4.02, 4.02, 6)
        core = Box(4, 4, 4)
        value = self.distance(ring, core, within=1e-6)
        self.assertGreater(value, 1e-6)
        self.assertAlmostEqual(self.distance(ring, core), 0.01, places=6)

    def test_invalid_tolerance_is_refused(self):
        for bad in (float("nan"), -1.0):
            with self.subTest(within=bad):
                with self.assertRaises(self.tool["ManifestError"]):
                    self.distance(Box(2, 2, 2), Box(2, 2, 2).translate((2, 0, 0)), within=bad)


if __name__ == "__main__":
    unittest.main()
