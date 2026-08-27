from __future__ import annotations

import math
import sys
import tempfile
import time
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from build123d import Box, import_step

from cadgen.step_export import CANONICAL_STEP_TIMESTAMP, export_build123d_step_file


class StepExportReproducibilityTest(unittest.TestCase):
    def test_fresh_exports_are_byte_identical_and_round_trip_valid_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_path = root / "first.step"
            second_path = root / "second.step"

            first_shape = Box(7, 11, 13)
            first_shape.label = "canonical-solid"
            first_hash = export_build123d_step_file(first_shape, first_path)

            # Open CASCADE's default header timestamp has one-second resolution.
            # Crossing that boundary makes this a regression test for fresh
            # generations rather than two writes that happen to share a clock tick.
            time.sleep(1.1)
            second_shape = Box(7, 11, 13)
            second_shape.label = "canonical-solid"
            second_hash = export_build123d_step_file(second_shape, second_path)

            first_bytes = first_path.read_bytes()
            self.assertEqual(first_bytes, second_path.read_bytes())
            self.assertEqual(first_hash, second_hash)
            self.assertIn(
                b"FILE_NAME('canonical-solid','"
                + CANONICAL_STEP_TIMESTAMP.encode("ascii"),
                first_bytes,
            )
            self.assertIn(b"'build123d'", first_bytes)

            for step_path in (first_path, second_path):
                with self.subTest(step_path=step_path.name):
                    restored = import_step(step_path)
                    solids = restored.solids()
                    self.assertTrue(restored.is_valid)
                    self.assertEqual(len(solids), 1)
                    self.assertTrue(solids[0].is_valid)
                    self.assertTrue(math.isclose(restored.volume, 1001.0, rel_tol=1e-9))


if __name__ == "__main__":
    unittest.main()
