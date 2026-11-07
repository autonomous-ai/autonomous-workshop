"""ADR 0098: the seal's design batch runs final verification on the Proof.

Contract: `verify_project --design` is final mode outside a Workshop run. It
runs every final gate without the blind signature review, which the run's own
final verification binds, and records that it did. Inside a run (a WISH.json
above the project) it is refused, so the run's gate never loses its review
requirement; without --design an unreviewed project is still refused."""

from __future__ import annotations

import contextlib
import io
import os
import runpy
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class DesignFinalVerificationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "proof"
        self.project.mkdir()
        (self.project / "toy.step.py").write_text("PRINTABLE = False\ndef gen_step(): return None\n")
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        main = runpy.run_path(str(SCRIPTS / "verify_project"))["main"]
        self.commands, self.notes = [], []
        test = self

        class StopAtLayout(main.__globals__["Runner"]):
            """The tools are not run: the first one fails, ending the run."""

            def command(self, argv, **_kwargs):
                test.commands.append(Path(str(argv[1])).name)
                return 1

            def note(self, label, detail):
                test.notes.append(label)
                super().note(label, detail)

        main.__globals__["Runner"] = StopAtLayout
        self.main = main

    def _run(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                code = self.main(["proof", "--no-report", *argv])
            except SystemExit as exc:
                code = exc.code
        self.stderr = err.getvalue()
        return code

    def test_without_design_an_unreviewed_project_is_refused(self):
        self.assertEqual(self._run(), 2)
        self.assertIn("requires snap/SIGNATURE-REVIEW.json", self.stderr)
        self.assertEqual(self.commands, [])

    def test_design_runs_the_final_gates_without_the_review_and_says_so(self):
        self.assertEqual(self._run("--design", "--strict-fit"), 1)  # the stub's failing tool
        self.assertEqual(self.commands, ["check_layout"])
        self.assertEqual(self.notes, ["design"])

    def test_design_inside_a_run_is_refused(self):
        (self.root / "WISH.json").write_text("{}")
        self.assertEqual(self._run("--design"), 2)
        self.assertIn("--design is for a Contract Proof outside a Workshop run", self.stderr)
        self.assertEqual(self.commands, [])

    def test_design_is_final_mode_only(self):
        self.assertEqual(self._run("--design", "--quick"), 2)
        self.assertIn("--design is a final-mode option", self.stderr)


if __name__ == "__main__":
    unittest.main()
