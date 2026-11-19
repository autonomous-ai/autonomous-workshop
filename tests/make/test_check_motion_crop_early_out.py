"""A sweep's crop is decided by the obstacle's own box before any boolean runs."""
from pathlib import Path
import runpy
import unittest

from build123d import Box, Location

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class BigObstacle:
    """A many-faced obstacle that records every boolean asked of it."""

    def __init__(self, center, size=10.0):
        self.box = Location(center) * Box(size, size, size)
        self.booleans = []

    def faces(self):
        return [None] * 201

    def bounding_box(self):
        return self.box.bounding_box()

    def __and__(self, other):
        self.booleans.append("&")
        raise RuntimeError("boolean")

    def __sub__(self, other):
        self.booleans.append("-")
        raise RuntimeError("boolean")


class Piece:
    """A boolean result with a volume and a validity flag."""

    def __init__(self, volume, valid=True):
        self.volume, self.is_valid = volume, valid

    def solids(self):
        return [self]


class InvalidCropObstacle(BigObstacle):
    """Its crop conserves volume but fails validation, as OCC returned for a many-faced drum."""

    volume = 1000.0

    def solids(self):
        return [self]

    def __and__(self, other):
        self.booleans.append("&")
        return Piece(400.0, valid=False)

    def __sub__(self, other):
        self.booleans.append("-")
        return Piece(600.0)


class CropEarlyOutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))
        cls.sweep = [Box(20, 20, 20).bounding_box(), (Location((10, 0, 0)) * Box(20, 20, 20)).bounding_box()]

    def test_obstacle_beyond_the_sweep_has_nothing_near_the_path(self):
        far = BigObstacle((500, 0, 0))
        self.assertIsNone(self.tool["crop_to_sweep"](far, self.sweep))
        self.assertEqual(far.booleans, [])

    def test_obstacle_inside_the_sweep_is_kept_whole_without_a_boolean(self):
        inside = BigObstacle((5, 0, 0), size=4.0)
        self.assertIs(self.tool["crop_to_sweep"](inside, self.sweep), inside)
        self.assertEqual(inside.booleans, [])

    def test_straddling_obstacle_still_pays_the_crop(self):
        edge = BigObstacle((22, 0, 0))
        self.assertIs(self.tool["crop_to_sweep"](edge, self.sweep), edge)   # the throwing crop keeps the whole
        self.assertEqual(edge.booleans, ["&"])

    def test_an_invalid_crop_keeps_the_whole_obstacle(self):
        edge = InvalidCropObstacle((22, 0, 0))
        self.assertIs(self.tool["crop_to_sweep"](edge, self.sweep), edge)
        self.assertEqual(edge.booleans, ["&", "-"])

    def test_touching_the_margin_is_not_a_miss(self):
        lo_edge = BigObstacle((-16.0, 0, 0))      # max x = -11.0 = the window's padded min
        self.tool["crop_to_sweep"](lo_edge, self.sweep)
        self.assertEqual(lo_edge.booleans, ["&"])

    def test_small_obstacles_are_untouched(self):
        small = Box(1, 1, 1).moved(Location((500, 0, 0)))
        self.assertIs(self.tool["crop_to_sweep"](small, self.sweep), small)


if __name__ == "__main__":
    unittest.main()
