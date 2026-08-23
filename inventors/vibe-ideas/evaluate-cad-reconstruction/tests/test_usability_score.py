import tempfile
import unittest
from pathlib import Path

from autoimprove.common.usability_score import score_usability_project
from tests.test_printability_score import _cube_triangles, _write_ascii_stl


def _translated(triangles, offset):
    ox, oy, oz = offset
    return [
        tuple((x + ox, y + oy, z + oz) for x, y, z in tri)
        for tri in triangles
    ]


class UsabilityScoreTests(unittest.TestCase):
    def test_separate_parts_score_easy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.stl"
            b = root / "b.stl"
            assembly = root / "assembly.stl"
            _write_ascii_stl(a, _cube_triangles(size=10.0))
            _write_ascii_stl(b, _translated(_cube_triangles(size=10.0), (15.0, 0.0, 0.0)))
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=10.0)
                + _translated(_cube_triangles(size=10.0), (15.0, 0.0, 0.0)),
            )

            report = score_usability_project(assembly=assembly, parts=[a, b])

            self.assertEqual(report["class"], "easy")
            self.assertGreaterEqual(report["score"], 9.0)
            self.assertEqual(report["hard_failures"], [])
            self.assertEqual(report["metrics"]["part_count"], 2)

    def test_overlapping_part_bounding_boxes_do_not_affect_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.stl"
            b = root / "b.stl"
            assembly = root / "assembly.stl"
            _write_ascii_stl(a, _cube_triangles(size=10.0))
            _write_ascii_stl(b, _translated(_cube_triangles(size=10.0), (5.0, 0.0, 0.0)))
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=10.0)
                + _translated(_cube_triangles(size=10.0), (5.0, 0.0, 0.0)),
            )

            report = score_usability_project(assembly=assembly, parts=[a, b])

            self.assertEqual(report["score"], 10.0)
            self.assertEqual(report["class"], "easy")
            self.assertEqual(report["hard_failures"], [])
            self.assertNotIn("max_pairwise_bbox_overlap_ratio", report["metrics"])

    def test_assembly_component_count_mismatch_is_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.stl"
            b = root / "b.stl"
            assembly = root / "assembly.stl"
            _write_ascii_stl(a, _cube_triangles(size=10.0))
            _write_ascii_stl(b, _translated(_cube_triangles(size=10.0), (20.0, 0.0, 0.0)))
            _write_ascii_stl(assembly, _cube_triangles(size=10.0))

            report = score_usability_project(assembly=assembly, parts=[a, b])

            self.assertIn(
                "assembly has 1 connected components but 2 part files were supplied",
                report["risk_factors"],
            )
            self.assertLess(report["score"], 10.0)

    def test_multi_component_assembly_without_parts_is_inventory_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assembly = root / "assembly.stl"
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=10.0)
                + _translated(_cube_triangles(size=10.0), (20.0, 0.0, 0.0)),
            )

            report = score_usability_project(assembly=assembly, parts=[])

            self.assertIn(
                "assembly has 2 disconnected components but no separate part STLs were supplied",
                report["risk_factors"],
            )
            self.assertLess(report["score"], 10.0)


if __name__ == "__main__":
    unittest.main()
