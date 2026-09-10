"""Boolean consistency is judged at the kernel's precision, not a fixed cubic micrometre.

Replaying the published motion manifests of twelve host-accepted toys under the
fixed 0.000001 mm3 consistency band made five of them inconclusive: the
union-inferred intersection drifted by up to 3.4e-6 of the operand volumes in
seated-contact poses of curved parts, and the union itself came back invalid
in seated poses where the intersection was valid. The band now scales with the
operand volumes, keeps its absolute floor for tiny parts, still rejects a
missing or wrong intersection, and falls back to both Cut-based differences
when the union is unavailable.
"""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch, PropertyMock

from build123d import Box, Compound, Solid
import OCP.BRepAlgoAPI as operations

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class FakeOperation:
    done = True
    result = None

    def SetNonDestructive(self, value):
        self.non_destructive = value

    def SetArguments(self, value):
        self.arguments = value

    def SetTools(self, value):
        self.tools = value

    def Build(self):
        return None

    def IsDone(self):
        return self.done

    def Shape(self):
        return self.result


class ConsistencyToleranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def condition(self, expect="clear"):
        return {"id": "occupancy", "check": "linear_motion_collision", "expect": expect,
                "inputs": {"moving_part": "moving", "obstacle_parts": ["fixed"],
                           "translation": [0, 0, 0], "steps": 1, "allow_seated_contact": True}}

    def run_pair(self, volumes, expect="clear"):
        # One evaluated step: va, vb, common, union.
        with patch.object(Solid, "volume", new_callable=PropertyMock, side_effect=list(volumes)):
            return self.tool["run_condition"](
                self.condition(expect), {"moving": Box(2, 2, 2), "fixed": Box(2, 2, 2).translate((1, 0, 0))}, 0)

    def test_tolerance_scales_with_operand_volume_and_keeps_the_floor(self):
        tolerance = self.tool["consistency_tolerance"]
        self.assertEqual(tolerance(0.001, 0.001), self.tool["VOLUME_CONSISTENCY_MM3"])
        self.assertAlmostEqual(tolerance(30000.0, 30000.0), self.tool["VOLUME_CONSISTENCY_RELATIVE"] * 60000.0)
        self.assertGreater(tolerance(30000.0, 30000.0), self.tool["VOLUME_CONSISTENCY_MM3"])

    def test_kernel_scale_discrepancy_on_large_operands_is_consistent(self):
        # An empty intersection against operands-minus-union of 0.4 mm3 on 200,000 mm3
        # of material, as measured on an accepted toy's seated wheel.
        result = self.run_pair([34550.0, 169600.0, 0.0, 204150.0 - 0.4])
        self.assertEqual(result["status"], "pass", result)
        self.assertTrue(result["clear"])

    def test_large_operand_intersection_noise_is_consistent_for_blocked(self):
        # 559.626810 measured against 559.626819 inferred, as observed on an accepted toy.
        result = self.run_pair([3526.0, 9887.0, 559.626810, 13413.0 - 559.626819], expect="blocked")
        self.assertEqual(result["status"], "pass", result)
        self.assertFalse(result["clear"])

    def test_missing_intersection_on_large_operands_is_still_inconsistent(self):
        # Ten cubic millimetres unaccounted for is not integration noise.
        result = self.run_pair([30000.0, 30000.0, 0.0, 59990.0])
        self.assertEqual(result["status"], "inconclusive", result)
        self.assertIn("inconsistent", result["detail"])

    def test_tiny_operands_keep_the_absolute_floor(self):
        result = self.run_pair([0.001, 0.001, 0.0, 0.002 - 0.000005])
        self.assertEqual(result["status"], "inconclusive", result)
        self.assertIn("inconsistent", result["detail"])

    def test_duplicated_material_is_still_rejected(self):
        # Two 8 mm3 solids whose union is 8 mm3 cannot have an empty intersection.
        result = self.run_pair([8.0, 8.0, 0.0, 8.0])
        self.assertEqual(result["status"], "inconclusive", result)

    def test_intersection_larger_than_an_operand_is_rejected(self):
        result = self.run_pair([8.0, 8.0, 9.0, 8.0])
        self.assertEqual(result["status"], "inconclusive", result)
        self.assertIn("exceeds an operand", result["detail"])

    def test_group_union_noise_on_large_members_is_consistent(self):
        group = Compound(children=[Box(10, 10, 10), Box(10, 10, 10).translate((30, 0, 0))])
        with patch.object(Solid, "volume", new_callable=PropertyMock,
                          side_effect=[30000.0, 30000.0, 30000.0, 30000.05]):
            _shape, measured = self.tool["_material"](group)
        self.assertAlmostEqual(measured, 60000.05)

    def test_group_union_gross_excess_is_still_rejected(self):
        group = Compound(children=[Box(10, 10, 10), Box(10, 10, 10).translate((30, 0, 0))])
        with patch.object(Solid, "volume", new_callable=PropertyMock,
                          side_effect=[30000.0, 30000.0, 30000.0, 30010.0]):
            with self.assertRaisesRegex(ValueError, "inconsistent volume"):
                self.tool["_material"](group)

    def test_invalid_union_falls_back_to_agreeing_differences(self):
        # Overlapping 2 mm boxes offset by 1 mm intersect in 4 mm3. The union is
        # forced invalid; both differences (4 mm3 each) still confirm the intersection.
        broken = type("BrokenUnion", (FakeOperation,), {"done": False})
        with patch.object(operations, "BRepAlgoAPI_Fuse", broken):
            actual = self.tool["overlap_volume"](Box(2, 2, 2), Box(2, 2, 2).translate((1, 0, 0)))
        self.assertAlmostEqual(actual, 4.0)

    def test_invalid_union_with_disagreeing_differences_is_inconclusive(self):
        broken = type("BrokenUnion", (FakeOperation,), {"done": False})
        empty_cut = type("EmptyCut", (FakeOperation,), {"result": Compound([]).wrapped})
        for expect in ("clear", "blocked"):
            with self.subTest(expect=expect):
                with patch.object(operations, "BRepAlgoAPI_Fuse", broken), \
                        patch.object(operations, "BRepAlgoAPI_Cut", empty_cut):
                    result = self.tool["run_condition"](
                        self.condition(expect),
                        {"moving": Box(2, 2, 2), "fixed": Box(2, 2, 2).translate((1, 0, 0))}, 0)
                self.assertEqual(result["status"], "inconclusive", result)
                self.assertIn("union unavailable", result["detail"])

    def test_invalid_union_and_failed_difference_is_inconclusive(self):
        broken = type("BrokenUnion", (FakeOperation,), {"done": False})
        with patch.object(operations, "BRepAlgoAPI_Fuse", broken), \
                patch.object(operations, "BRepAlgoAPI_Cut", broken):
            result = self.tool["run_condition"](
                self.condition(), {"moving": Box(2, 2, 2), "fixed": Box(2, 2, 2).translate((1, 0, 0))}, 0)
        self.assertEqual(result["status"], "inconclusive", result)
        self.assertNotIn("clear", result)


if __name__ == "__main__":
    unittest.main()
