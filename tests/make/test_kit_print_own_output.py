"""A tool never refuses its own kit print layout as a stale STEP.

``kit_print.py layout`` (ADR 0104 decision 4) writes
``measure/kit/print.step`` into the project and records its sha256 in
``measure/kit/print.json``. Final verification, and so ``seal_proof
preflight``, runs that layout; the next preflight or seal dry run used to
refuse the same file as a bought/foreign or stale STEP (Amsterdam seal 11,
the Miami preflight). The component preflight now excludes exactly the
recorded bytes. A STEP the record does not name, or whose bytes changed, is
still refused.
"""

from __future__ import annotations

import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.make import test_kit_print as kit_print_tests

VERIFIER = kit_print_tests.SCRIPT.parents[2] / "cad" / "scripts" / "verify_project"
STEP_TEXT = "ISO-10303-21;\nEND-ISO-10303-21;\n"
REFUSAL = "foreign or stale STEP"


def write(project: Path, relative: str, text: str) -> Path:
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def record(project: Path, **changes) -> None:
    step = project / "measure/kit/print.step"
    report = {"kind": "kit-print-layout", "schema_version": 2, "step": "measure/kit/print.step",
              "sha256": hashlib.sha256(step.read_bytes()).hexdigest()}
    report.update(changes)
    write(project, "measure/kit/print.json", json.dumps(report))


class ComponentPreflightTest(unittest.TestCase):
    """verify_project's component preflight, on a small project."""

    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        self.project = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.project)
        write(self.project, "widget.step.py", "def gen_step():\n    return None\n")
        write(self.project, "measure/kit/print.step", STEP_TEXT + "layout\n")

    def strays(self):
        return sorted(p.relative_to(self.project).as_posix()
                      for p in self.verifier["_component_steps"](self.project)[1])

    def dry_run(self):
        return subprocess.run([sys.executable, str(VERIFIER), ".", "--dry-run"], cwd=self.project,
                              capture_output=True, text=True, timeout=300)

    def test_the_recorded_layout_is_no_stray(self):
        record(self.project)
        self.assertEqual(self.strays(), [])

    def test_a_dry_run_twice_in_a_row_accepts_its_own_layout(self):
        record(self.project)
        for attempt in (1, 2):
            done = self.dry_run()
            self.assertNotIn(REFUSAL, done.stdout + done.stderr, "attempt %d" % attempt)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_an_unrecorded_layout_is_still_refused(self):
        self.assertEqual(self.strays(), ["measure/kit/print.step"])
        done = self.dry_run()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn(REFUSAL, done.stderr)

    def test_a_layout_whose_bytes_changed_is_still_refused(self):
        record(self.project)
        write(self.project, "measure/kit/print.step", STEP_TEXT + "edited by hand\n")
        self.assertEqual(self.strays(), ["measure/kit/print.step"])
        done = self.dry_run()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn(REFUSAL, done.stderr)

    def test_a_record_of_another_kind_or_path_excludes_nothing(self):
        record(self.project, kind="bought-bodies")
        self.assertEqual(self.strays(), ["measure/kit/print.step"])
        write(self.project, "measure/kit/other.step", STEP_TEXT + "layout\n")
        record(self.project, step="measure/kit/other.step")
        self.assertEqual(self.strays(), ["measure/kit/other.step", "measure/kit/print.step"])

    def test_a_foreign_step_beside_the_layout_is_still_refused(self):
        record(self.project)
        write(self.project, "measure/kit/supplier.step", STEP_TEXT + "foreign\n")
        self.assertEqual(self.strays(), ["measure/kit/supplier.step"])

    def test_a_symlinked_layout_is_still_refused(self):
        real = write(self.project, "elsewhere/print.step", STEP_TEXT + "layout\n")
        (self.project / "measure/kit/print.step").unlink()
        (self.project / "measure/kit/print.step").symlink_to(real)
        record(self.project)
        self.assertIn("measure/kit/print.step", self.strays())


class RealLayoutTwiceTest(unittest.TestCase):
    """The layout kit_print.py writes passes the component preflight, and
    still does after a second layout run (a second preflight)."""

    PANEL = kit_print_tests.KitPrintLayoutTest.PANEL
    setUp = kit_print_tests.KitPrintLayoutTest.setUp
    install = kit_print_tests.KitPrintLayoutTest.install
    write_parts = kit_print_tests.KitPrintLayoutTest.write_parts
    layout = kit_print_tests.KitPrintLayoutTest.layout

    def test_preflight_twice_in_a_row_accepts_the_layout(self):
        verifier = runpy.run_path(str(VERIFIER))
        for attempt in (1, 2):
            done = self.layout()
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            strays = [p.relative_to(self.project).as_posix()
                      for p in verifier["_component_steps"](self.project)[1]]
            self.assertNotIn("measure/kit/print.step", strays, "attempt %d" % attempt)
        with (self.project / "measure/kit/print.step").open("ab") as handle:
            handle.write(b"\n")
        strays = [p.relative_to(self.project).as_posix() for p in verifier["_component_steps"](self.project)[1]]
        self.assertIn("measure/kit/print.step", strays)


if __name__ == "__main__":
    unittest.main()
