"""Validity of explicit STEP bytes must not be replaced by a sibling generator."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from build123d import Box, export_step


INSPECT = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/inspect"
BOX_SOURCE = "from build123d import Box\n\ndef gen_step():\n    return Box(7, 11, 13)\n"


class InspectValidityTargetTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "model.step.py"
        self.step = self.root / "model.step"

    def inspect(self, target):
        result = subprocess.run(
            [sys.executable, str(INSPECT), "validate", str(target)],
            cwd=self.root,
            env=dict(os.environ, CADGEN_WARM="0", PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True, text=True, timeout=60,
        )
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def write_step(self, *, open_face=False):
        shape = Box(7, 11, 13)
        if open_face:
            shape = shape.faces()[0]
        self.assertTrue(export_step(shape, self.step, timestamp="1970-01-01T00:00:00"))

    def assert_open_step_rejected(self):
        code, result = self.inspect(self.step)
        self.assertEqual(code, 2, result)
        self.assertFalse(result["ok"])
        self.assertTrue(any("noSolid" in part["reasons"] for part in result["parts"]), result)

    def test_explicit_step_rejects_open_geometry_with_valid_sibling_generator(self):
        self.source.write_text(BOX_SOURCE)
        self.write_step(open_face=True)
        self.assert_open_step_rejected()

    def test_explicit_python_checks_generator_despite_invalid_sibling_step(self):
        self.source.write_text(BOX_SOURCE)
        self.write_step(open_face=True)
        code, result = self.inspect(self.source)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])

    def test_explicit_step_does_not_execute_broken_sibling_generator(self):
        self.write_step()
        for source in (
            "def gen_step():\n    raise RuntimeError('generator must not run')\n",
            "from build123d import Box\n\ndef gen_step():\n"
            "    raise RuntimeError('generator must not run')\n    return Box(7, 11, 13)\n",
        ):
            with self.subTest(source=source):
                self.source.write_text(source)
                code, result = self.inspect(self.step)
                self.assertEqual(code, 0, result)
                self.assertTrue(result["ok"])

    def test_generator_without_export_remains_available(self):
        self.source.write_text(BOX_SOURCE)
        code, result = self.inspect(self.source)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])

    def test_logical_entry_keeps_existing_generator_resolution(self):
        self.source.write_text(BOX_SOURCE)
        self.write_step(open_face=True)
        code, result = self.inspect("model")
        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"])

    def test_standalone_open_step_is_rejected(self):
        self.write_step(open_face=True)
        self.assert_open_step_rejected()

    def test_explicit_step_rechecks_changed_bytes(self):
        self.source.write_text(BOX_SOURCE)
        self.write_step()
        original = self.step.read_bytes()
        code, result = self.inspect(self.step)
        self.assertEqual(code, 0, result)
        self.write_step(open_face=True)
        self.assertNotEqual(original, self.step.read_bytes())
        self.assert_open_step_rejected()


if __name__ == "__main__":
    unittest.main()
