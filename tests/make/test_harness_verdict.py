"""verify_project projects its pipeline record onto Harness's verdict file.

Autonomous Harness runs the CAD skill as the Workshop domain harness and reads
``<workspace>/.harness/verdict.json`` for the pane header. The projection is
gated on ``HARNESS_WORKSPACE`` so Workshop's own product runs never gain a
file, it never fails a run, and quick previews never read as verified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class HarnessVerdictTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve()
        self.project = self.workspace / "cad"
        self.project.mkdir()
        self.verifier = runpy.run_path(str(SCRIPTS / "verify_project"))
        self.write = self.verifier["_write_harness_verdict"]

    def verdict(self):
        return json.loads((self.workspace / ".harness/verdict.json").read_text(encoding="utf-8"))

    def test_nothing_is_written_outside_harness(self):
        with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": ""}):
            written = self.write(self.project, [], mode="final", result=0)
        self.assertIsNone(written)
        self.assertFalse((self.workspace / ".harness").exists())

    def test_final_pass_is_ready_and_names_the_step(self):
        step = self.project / "model.step"
        step.write_bytes(b"ISO-10303-21;\n")
        records = [
            {"command": "python3 /skills/cad/scripts/check_layout cad", "status": "rc=0", "seconds": 0.1},
            {"command": "check_motion  # NOT RUN: motion verification disabled", "status": "skipped", "seconds": 0.0},
        ]
        with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": str(self.workspace)}):
            written = self.write(self.project, records, mode="final", result=0, artifact=step)
        self.assertEqual(written, self.workspace / ".harness/verdict.json")
        verdict = self.verdict()
        self.assertEqual(verdict["spec"], 1)
        self.assertTrue(verdict["ready"])
        self.assertEqual(verdict["artifact"], "cad/model.step")
        self.assertEqual(verdict["summary"], "final verification passed")
        self.assertEqual(
            [(item["severity"], item["kind"]) for item in verdict["findings"]],
            [("info", "gate-skipped")],
        )
        self.assertIn("check_motion: motion verification disabled", verdict["findings"][0]["message"])
        self.assertTrue(verdict["updatedAt"].endswith("Z"))

    def test_final_failure_reports_the_failing_gate(self):
        records = [
            {"command": "python3 /skills/cad/scripts/check_layout cad", "status": "rc=0", "seconds": 0.1},
            {"command": "python3 /skills/cad/scripts/check_fit cad/part_body.step.py", "status": "rc=1", "seconds": 4.0},
            {"command": "python3 /skills/cad/scripts/check_thickness cad/part_lid.step.py", "status": "accepted-fail", "seconds": 8.0},
        ]
        with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": str(self.workspace)}):
            self.write(self.project, records, mode="final", result=1)
        verdict = self.verdict()
        self.assertFalse(verdict["ready"])
        self.assertEqual(verdict["summary"], "final verification failed: check_fit exited 1")
        severities = [item["severity"] for item in verdict["findings"]]
        self.assertEqual(severities, ["error", "warning"])
        self.assertNotIn("artifact", verdict)

    def test_quick_preview_is_never_ready(self):
        step = self.project / "model.step"
        step.write_bytes(b"ISO-10303-21;\n")
        with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": str(self.workspace)}):
            self.write(self.project, [{"command": "gen", "status": "rc=0", "seconds": 1.0}], mode="quick", result=0, artifact=step)
        verdict = self.verdict()
        self.assertFalse(verdict["ready"])
        self.assertEqual(verdict["summary"], "preview built; not yet verified")
        self.assertEqual(verdict["artifact"], "cad/model.step")
        self.assertEqual([item["kind"] for item in verdict["findings"]], ["quick-preview"])

    def test_artifact_outside_the_workspace_is_omitted(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            step = Path(elsewhere) / "model.step"
            step.write_bytes(b"ISO-10303-21;\n")
            with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": str(self.workspace)}):
                self.write(self.project, [], mode="final", result=0, artifact=step)
        self.assertNotIn("artifact", self.verdict())

    def test_a_refused_preflight_leaves_a_verdict(self):
        # No combined entry at all: main() refuses before any gate runs and
        # exits through argparse. Harness still learns why from the verdict.
        # verify_project requires the project inside its cwd, so run from the workspace.
        previous = Path.cwd()
        os.chdir(self.workspace)
        self.addCleanup(os.chdir, previous)
        with mock.patch.dict(os.environ, {"HARNESS_WORKSPACE": str(self.workspace)}):
            with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                self.verifier["main"](["cad", "--quick", "--no-report"])
        verdict = self.verdict()
        self.assertFalse(verdict["ready"])
        self.assertEqual(verdict["findings"][0]["kind"], "preflight-refused")
        self.assertIn("expected one combined entry", verdict["findings"][0]["message"])


if __name__ == "__main__":
    unittest.main()
