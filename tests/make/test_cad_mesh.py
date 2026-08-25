from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.make.cad import (
    KernelBodyObservation,
    StlInspectionLimits,
    StlPathInspectionError,
    fits_bed_envelope,
    inspect_stl_path,
    inspect_stl_topology,
)
from workshop.make.cad.mesh import UPSTREAM_MIT_NOTICE


TETRA_STL = b"""solid workshop
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 1 0 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 0 0 1
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 1 0 0
      vertex 0 1 0
      vertex 0 0 1
    endloop
  endfacet
endsolid workshop
"""


class SharedMeshTests(unittest.TestCase):
    def test_public_stdlib_inspector_is_source_bound_and_preserves_notice(self):
        receipt = inspect_stl_topology(TETRA_STL, expected_shell_count=1)

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.source_sha256, hashlib.sha256(TETRA_STL).hexdigest())
        self.assertEqual(receipt.observed_shell_count, 1)
        self.assertEqual(receipt.boundary_edge_count, 0)
        self.assertIn("MIT License", UPSTREAM_MIT_NOTICE)
        self.assertIsInstance(StlInspectionLimits(), StlInspectionLimits)

    def test_kernel_observation_round_trips_strict_json_mapping(self):
        observation = KernelBodyObservation(
            source_sha256=hashlib.sha256(TETRA_STL).hexdigest(),
            evaluator_id="kernel-test-v1",
            status="completed",
            body_count=1,
            evidence_sha256="e" * 64,
        )

        self.assertEqual(
            KernelBodyObservation.from_mapping(observation.to_dict()), observation)
        with self.assertRaises(ValueError):
            KernelBodyObservation.from_mapping(
                dict(observation.to_dict(), invented_field=True))

    def test_bed_envelope_accepts_axis_or_45_degree_xy_placement(self):
        self.assertTrue(
            fits_bed_envelope((0, 0, 0), (200, 50, 20), (220, 220, 250)))
        self.assertTrue(
            fits_bed_envelope((0, 0, 0), (224, 57, 20), (220, 220, 250)))
        self.assertFalse(
            fits_bed_envelope(
                (0, 0, 0), (224, 57, 20), (220, 220, 250),
                allow_xy_rotation=False))
        self.assertFalse(
            fits_bed_envelope((0, 0, 0), (400, 400, 20), (220, 220, 250)))
        self.assertFalse(
            fits_bed_envelope((0, 0, 0), (10, 10, 300), (220, 220, 250)))

    def test_bed_envelope_finds_non_45_degree_rectangular_bed_rotation(self):
        self.assertTrue(
            fits_bed_envelope((0, 0, 0), (105, 10, 20), (100, 60, 25)))
        self.assertFalse(
            fits_bed_envelope((0, 0, 0), (105, 10, 20), (100, 60, 25),
                              allow_xy_rotation=False))
        self.assertFalse(
            fits_bed_envelope((0, 0, 0), (110, 10, 20), (100, 60, 25)))

    def test_path_inspector_binds_exact_regular_file_bytes(self):
        with tempfile.TemporaryDirectory() as raw_root:
            path = Path(raw_root) / "part.stl"
            path.write_bytes(TETRA_STL)

            receipt = inspect_stl_path(
                path,
                expected_shell_count=1,
                expected_source_sha256=hashlib.sha256(TETRA_STL).hexdigest(),
                expected_source_bytes=len(TETRA_STL),
            )

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.source_sha256, hashlib.sha256(TETRA_STL).hexdigest())

    def test_path_inspector_rejects_symlinks_and_non_regular_files(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            target = root / "target.stl"
            target.write_bytes(TETRA_STL)
            link = root / "link.stl"
            link.symlink_to(target)

            with self.assertRaisesRegex(StlPathInspectionError, "path_is_symlink"):
                inspect_stl_path(link, expected_shell_count=1)
            with self.assertRaisesRegex(
                StlPathInspectionError, "path_is_not_regular_file"
            ):
                inspect_stl_path(root, expected_shell_count=1)

    def test_path_inspector_checks_size_before_any_bounded_read(self):
        with tempfile.TemporaryDirectory() as raw_root:
            path = Path(raw_root) / "large.stl"
            path.write_bytes(TETRA_STL)
            with mock.patch("workshop.make.cad.mesh.os.read") as read:
                with self.assertRaisesRegex(
                    StlPathInspectionError, "source_byte_limit_exceeded"
                ):
                    inspect_stl_path(
                        path,
                        expected_shell_count=1,
                        limits=StlInspectionLimits(max_source_bytes=10),
                    )
                read.assert_not_called()

    def test_path_inspector_rejects_a_file_that_changes_during_read(self):
        with tempfile.TemporaryDirectory() as raw_root:
            path = Path(raw_root) / "changing.stl"
            path.write_bytes(TETRA_STL)
            original_read = os.read
            changed = [False]

            def read_after_append(descriptor, count):
                if not changed[0]:
                    changed[0] = True
                    with path.open("ab") as handle:
                        handle.write(b"x")
                return original_read(descriptor, count)

            with mock.patch(
                "workshop.make.cad.mesh.os.read", side_effect=read_after_append
            ):
                with self.assertRaisesRegex(
                    StlPathInspectionError, "source_changed_while_reading"
                ):
                    inspect_stl_path(path, expected_shell_count=1)

    def test_malformed_nonempty_mesh_never_passes(self):
        source = b"solid present\n  facet normal 0 0 0\nendsolid present\n"
        receipt = inspect_stl_topology(source, expected_shell_count=1)

        self.assertNotEqual(receipt.status, "passed")
        self.assertIn("missing_ascii_outer_loop", receipt.hold_reasons)


if __name__ == "__main__":
    unittest.main()
