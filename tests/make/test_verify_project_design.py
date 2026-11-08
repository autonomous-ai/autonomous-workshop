"""ADR 0098: the seal's design batch runs final verification on the Proof.

Contract: `verify_project --design` is final mode outside a Workshop run. It
runs every final gate without the blind signature review, which the run's own
final verification binds, and records that it did. Inside a run (a WISH.json
above the project) it is refused, so the run's gate never loses its review
requirement; without --design an unreviewed project is still refused.

Issue #241: --design needs the Proof's Design Contract file (--contract), which
gives the Bought Parts model the circuit and catalogue a run would seal, and
--contract belongs to --design. --geometry-seconds sets the one shared
geometry allowance, so a batch can give its analyses the layer's whole
deadline instead of the 600 s default that leaves them UNVERIFIED."""

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
        (self.root / "CONTRACT.md").write_text("# contract\n")
        previous = os.environ.get("WORKSHOP_GEOMETRY_TIMEOUT")
        self.addCleanup(lambda: os.environ.pop("WORKSHOP_GEOMETRY_TIMEOUT", None) if previous is None
                        else os.environ.__setitem__("WORKSHOP_GEOMETRY_TIMEOUT", previous))
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
        self.assertEqual(self._run("--design", "--contract", "CONTRACT.md", "--strict-fit"), 1)  # the stub's failing tool
        self.assertEqual(self.commands, ["check_layout"])
        self.assertEqual(self.notes, ["design"])

    def test_design_inside_a_run_is_refused(self):
        (self.root / "WISH.json").write_text("{}")
        self.assertEqual(self._run("--design", "--contract", "CONTRACT.md"), 2)
        self.assertIn("--design is for a Contract Proof outside a Workshop run", self.stderr)
        self.assertEqual(self.commands, [])

    def test_design_and_contract_come_together(self):
        for argv in (("--design",), ("--contract", "CONTRACT.md")):
            with self.subTest(argv):
                self.assertEqual(self._run(*argv), 2)
                self.assertIn("--design needs --contract CONTRACT.md", self.stderr)
                self.assertEqual(self.commands, [])

    def test_a_missing_contract_file_is_refused(self):
        self.assertEqual(self._run("--design", "--contract", "MISSING.md"), 2)
        self.assertIn("--contract is not a file", self.stderr)

    def test_geometry_seconds_sets_the_shared_allowance(self):
        self.assertEqual(self._run("--design", "--contract", "CONTRACT.md", "--geometry-seconds", "3300"), 1)
        self.assertEqual(os.environ["WORKSHOP_GEOMETRY_TIMEOUT"], "3300")
        for bad in ("0", "-5", "86401"):
            with self.subTest(bad):
                self.assertEqual(self._run("--design", "--contract", "CONTRACT.md", "--geometry-seconds", bad), 2)
                self.assertIn("--geometry-seconds must be in (0, 86400]", self.stderr)

    def test_the_bought_parts_model_is_given_the_contract(self):
        """Before #241 the model step was silently skipped outside a run."""
        stub = self.root / "bought_model_stub.py"
        stub.write_text("SEEN = []\ndef applies(project, contract=None):\n"
                        "    return contract is not None\n")
        run_bought_model = self.main.__globals__["_run_bought_model"]
        self.main.__globals__["BOUGHT_MODEL_SCRIPT"] = stub
        runner = self.main.__globals__["Runner"](cwd=self.root, dry_run=False, verbose=False)
        self.assertEqual(run_bought_model(runner, self.project), 0)  # no contract: does not apply
        self.assertEqual(self.commands, [])
        runner.design_contract = self.root / "CONTRACT.md"
        self.assertEqual(run_bought_model(runner, self.project), 1)  # the stub's failing tool
        self.assertEqual(self.commands, ["bought_model_stub.py"])

    def test_design_is_final_mode_only(self):
        self.assertEqual(self._run("--design", "--quick"), 2)
        self.assertIn("--design is a final-mode option", self.stderr)


if __name__ == "__main__":
    unittest.main()
