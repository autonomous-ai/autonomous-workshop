"""`check_overhang` judges a ceiling just above the bed the way it judges a higher one.

Contract: the flank, reach and chord probes read the slice they always read
for a face, one to two pitches under it, but never a slice below all
material. A channel open to the bed, 2 mm wide under a 0.5 mm ceiling with walls on both
sides, is a short bridge, whether or not it touches a larger region. Before
the fix, its probe landed in the voxel slice whose centre is below the bed.
That slice holds no material, so any such ceiling under about 0.67 mm read
as unflanked with infinite reach, i.e. an overhang (Miami kit A05/A06,
2026-11-14). The 45 degree limit is unchanged: a low shelf with material on
one side only, and a low cap on a stem, still need support.
"""

from __future__ import annotations

import unittest

from build123d import Box, Pos

from tests.make.test_check_overhang_bridge_span import GATE, _kinds


def _plate():
    """A 30 x 20 mm wall 2.4 mm thick, lying on Z 0."""
    return Pos(15, 10, 1.2) * Box(30, 20, 2.4)


def _channel(x, ceiling, width=2.0, length=9.0):
    """An underside channel open to the bed: `width` wide, its ceiling at `ceiling`."""
    return Pos(x, 10, ceiling / 2) * Box(width, length, ceiling)


class LowCeilingTests(unittest.TestCase):
    def test_a_two_mm_channel_under_a_half_mm_ceiling_is_a_bridge(self):
        for ceiling in (0.5, 0.6, 0.7, 1.0):
            with self.subTest(ceiling=ceiling):
                kinds, regions = _kinds(_plate() - _channel(15, ceiling))
                self.assertEqual(kinds, ["bridge"], [(r["kind"], r["z"], r["reach"]) for r in regions])
                self.assertLess(regions[0]["reach"], 2.0)

    def test_two_such_channels_side_by_side_are_two_bridges_wherever_the_part_lies(self):
        # The pool-hotel side wall: two channels, and the same part moved on the sheet.
        for dx, dy in ((0.0, 0.0), (0.13, 0.0), (0.0, 0.29), (5.37, 61.9)):
            with self.subTest(dx=dx, dy=dy):
                shape = Pos(dx, dy, 0) * (_plate() - _channel(8, 0.5) - _channel(22, 0.5))
                kinds, regions = _kinds(shape)
                self.assertEqual(kinds, ["bridge", "bridge"], [(r["kind"], r["at"]) for r in regions])

    def test_a_low_shelf_held_on_one_side_still_needs_support(self):
        # A 5 mm shelf 0.5 mm above the bed, its wall on one side only.
        shelf = Pos(2, 10, 1.2) * Box(4, 20, 2.4) + Pos(6.5, 10, 1.45) * Box(5, 20, 1.9)
        kinds, regions = _kinds(shelf)
        self.assertEqual(kinds, ["overhang"], [(r["kind"], r["reach"]) for r in regions])

    def test_a_low_cap_on_a_stem_still_needs_support(self):
        cap = Pos(10, 10, 0.3) * Box(2, 2, 0.6) + Pos(10, 10, 1.1) * Box(8, 8, 1.0)
        kinds, regions = _kinds(cap)
        self.assertIn("overhang", kinds, [(r["kind"], r["reach"]) for r in regions])

    def test_a_face_above_the_bottom_slice_reads_the_slice_it_always_read(self):
        # Probing higher would cut a sloped region's own solid and shorten
        # its reach (a 2.5-4.7 mm door chamfer became a ledge in a trial).
        import numpy as np

        pitch, origin = 0.4, np.array([0.0, 0.0, -0.925])
        inside = np.zeros((4, 4, 20), dtype=bool)
        inside[:, :, 3:] = True  # the first slice with material is 3
        for z in (0.5, 0.6, 0.7, 1.2, 2.9, 3.03, 5.0):
            old = int(np.floor((z - pitch - origin[2]) / pitch))
            self.assertEqual(GATE.probe_slice(inside, origin, pitch, z), max(old, 3), z)
        self.assertEqual(GATE.probe_slice(np.zeros((2, 2, 5), dtype=bool), origin, pitch, 0.5), 2)

    def test_the_self_check_still_passes(self):
        self.assertEqual(GATE._self_check(), 0)


if __name__ == "__main__":
    unittest.main()
