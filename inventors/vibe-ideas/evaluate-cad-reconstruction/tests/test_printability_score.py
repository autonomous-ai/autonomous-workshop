import json
import math
import tempfile
import unittest
from pathlib import Path

from autoimprove.common.printability_score import (
    PrintabilityAssumptions,
    score_manifest,
    score_mesh_file,
    score_project,
)


def _normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def _write_ascii_stl(path, triangles):
    lines = ["solid fixture"]
    for tri in triangles:
        n = _normal(*tri)
        lines.append(f"  facet normal {n[0]} {n[1]} {n[2]}")
        lines.append("    outer loop")
        for v in tri:
            lines.append(f"      vertex {v[0]} {v[1]} {v[2]}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid fixture")
    Path(path).write_text("\n".join(lines) + "\n")


def _cube_triangles(size=20.0):
    s = size
    v = {
        "000": (0, 0, 0),
        "100": (s, 0, 0),
        "110": (s, s, 0),
        "010": (0, s, 0),
        "001": (0, 0, s),
        "101": (s, 0, s),
        "111": (s, s, s),
        "011": (0, s, s),
    }
    return [
        (v["000"], v["010"], v["110"]), (v["000"], v["110"], v["100"]),
        (v["001"], v["101"], v["111"]), (v["001"], v["111"], v["011"]),
        (v["000"], v["100"], v["101"]), (v["000"], v["101"], v["001"]),
        (v["010"], v["011"], v["111"]), (v["010"], v["111"], v["110"]),
        (v["000"], v["001"], v["011"]), (v["000"], v["011"], v["010"]),
        (v["100"], v["110"], v["111"]), (v["100"], v["111"], v["101"]),
    ]


def _horizontal_plate_triangles():
    return [
        ((0, 0, 25), (80, 0, 25), (80, 40, 25)),
        ((0, 0, 25), (80, 40, 25), (0, 40, 25)),
    ]


def _thin_box_triangles(size=(80.0, 40.0, 4.0), offset=(0.0, 0.0, 0.0)):
    sx, sy, sz = size
    ox, oy, oz = offset
    base = _cube_triangles(size=1.0)
    return [
        tuple((ox + x * sx, oy + y * sy, oz + z * sz) for x, y, z in tri)
        for tri in base
    ]


def _cube_with_tiny_seam_triangles():
    triangles = _cube_triangles(size=20.0)
    tiny = (
        (30.0, 0.0, 0.0),
        (30.2, 0.0, 0.0),
        (30.0, 0.2, 0.0),
    )
    return triangles + [tiny]


class PrintabilityScoreTests(unittest.TestCase):
    def test_watertight_cube_scores_easy(self):
        with tempfile.TemporaryDirectory() as tmp:
            cube = Path(tmp) / "cube.stl"
            _write_ascii_stl(cube, _cube_triangles())

            report = score_mesh_file(cube)

            self.assertGreaterEqual(report["score"], 8.0)
            self.assertEqual(report["class"], "easy")
            self.assertTrue(report["metrics"]["watertight"])
            self.assertEqual(report["hard_failures"], [])

    def test_open_mesh_is_capped_and_reports_hard_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            open_cube = Path(tmp) / "open_cube.stl"
            _write_ascii_stl(open_cube, _cube_triangles()[:-2])

            report = score_mesh_file(open_cube)

            self.assertLessEqual(report["score"], 4.0)
            self.assertEqual(report["class"], "hard")
            self.assertFalse(report["metrics"]["watertight"])
            self.assertIn("mesh has severe open/non-manifold boundaries", report["hard_failures"])

    def test_tiny_non_watertight_defect_is_not_hard_capped(self):
        with tempfile.TemporaryDirectory() as tmp:
            seam = Path(tmp) / "tiny_seam.stl"
            _write_ascii_stl(seam, _cube_with_tiny_seam_triangles())

            report = score_mesh_file(seam)

            self.assertGreater(report["score"], 4.0)
            self.assertFalse(report["metrics"]["watertight"])
            self.assertIn("mesh has minor non-watertight edges", report["risk_factors"])
            self.assertNotIn("mesh has severe open/non-manifold boundaries", report["hard_failures"])

    def test_unsupported_horizontal_plate_records_risks(self):
        with tempfile.TemporaryDirectory() as tmp:
            plate = Path(tmp) / "floating_plate.stl"
            _write_ascii_stl(plate, _horizontal_plate_triangles())

            report = score_mesh_file(plate)

            self.assertLess(report["score"], 4.0)
            self.assertIn("mesh has severe open/non-manifold boundaries", report["hard_failures"])
            self.assertIn("mesh has zero thickness in at least one axis", report["hard_failures"])
            self.assertGreater(report["metrics"]["bed_contact_area_mm2"], 25.0)

    def test_thin_box_uses_best_orientation_for_bed_contact_and_overhang(self):
        with tempfile.TemporaryDirectory() as tmp:
            lid = Path(tmp) / "lid_on_edge.stl"
            _write_ascii_stl(lid, _thin_box_triangles(size=(188.5, 290.0, 3.75), offset=(0, 0, 0)))

            report = score_mesh_file(lid)

            self.assertEqual(report["score"], 10.0)
            self.assertEqual(report["metrics"]["selected_orientation"], "z_min")
            self.assertGreater(report["metrics"]["bed_contact_area_mm2"], 25.0)
            self.assertEqual(report["metrics"]["unsupported_overhang_fraction"], 0.0)

    def test_project_score_is_capped_by_bad_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            assembly = Path(tmp) / "assembly.stl"
            good = Path(tmp) / "good_part.stl"
            bad = Path(tmp) / "bad_part.stl"
            _write_ascii_stl(assembly, _cube_triangles())
            _write_ascii_stl(good, _cube_triangles())
            _write_ascii_stl(bad, _cube_triangles()[:-2])

            report = score_project(assembly=assembly, parts=[good, bad])

            self.assertLessEqual(report["score"], 4.0)
            self.assertEqual(len(report["parts"]), 2)
            self.assertIn(
                "one or more parts have severe open/non-manifold boundaries",
                report["hard_failures"],
            )

    def test_manifest_loads_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assembly = root / "assembly.stl"
            part = root / "part.stl"
            manifest = root / "printability_manifest.json"
            _write_ascii_stl(assembly, _cube_triangles())
            _write_ascii_stl(part, _cube_triangles())
            manifest.write_text(json.dumps({
                "assembly": "assembly.stl",
                "parts": ["part.stl"],
            }))

            report = score_manifest(manifest)

            self.assertGreaterEqual(report["score"], 8.0)
            self.assertEqual(report["assembly"]["path"], str(assembly))
            self.assertEqual(report["parts"][0]["path"], str(part))

    def test_build_volume_is_not_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            huge = Path(tmp) / "huge.stl"
            _write_ascii_stl(huge, _cube_triangles(size=300.0))

            report = score_mesh_file(
                huge,
                assumptions=PrintabilityAssumptions(build_volume_mm=(220.0, 220.0, 250.0)),
            )

            self.assertEqual(report["score"], 10.0)
            self.assertNotIn("mesh exceeds build volume", report["hard_failures"])
            self.assertNotIn("exceeds_build_volume", report["metrics"])

    def test_assembly_build_volume_does_not_cap_project_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            assembly = Path(tmp) / "large_assembly.stl"
            part = Path(tmp) / "printable_part.stl"
            _write_ascii_stl(assembly, _cube_triangles(size=300.0))
            _write_ascii_stl(part, _cube_triangles(size=20.0))

            report = score_project(
                assembly=assembly,
                parts=[part],
                assumptions=PrintabilityAssumptions(build_volume_mm=(220.0, 220.0, 250.0)),
            )

            self.assertGreater(report["score"], 2.0)
            self.assertNotIn("mesh exceeds build volume", report["assembly"]["hard_failures"])
            self.assertFalse(
                any("build volume" in risk for risk in report["risk_factors"])
            )


if __name__ == "__main__":
    unittest.main()
