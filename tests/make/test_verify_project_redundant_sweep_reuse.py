"""A redundant final sweep reuses its verdict instead of recomputing it.

ADR 0070 / issue #41: a full sweep on a project unchanged since its last
terminal (PASS or FAIL) verdict must not re-verify. It re-emits the recorded
verdict and exits with that verdict's own exit code, writing an auditable
`reused` row beside the preserved prior report. An UNVERIFIED verdict is never
reused -- the next sweep always runs in full.

Every geometry-bearing subprocess call is faked here (`Runner.command` and
`Runner.inspect_batch`), since this environment carries no OCP/cadgen native
backend. Faking those two entry points lets the rest of `verify_project`'s own
orchestration -- the reuse decision itself -- run for real.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest


VERIFIER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/verify_project"


class RedundantFinalSweepReuseTest(unittest.TestCase):
    def setUp(self):
        self.verifier = runpy.run_path(str(VERIFIER))
        Runner = self.verifier["Runner"]
        self.command_log: list[list[str]] = []
        self.failing_labels: set[str] = set()

        def fake_command(runner_self, argv, *, warm=False, env_extra=None,
                          replay_success_stdout=False):
            args = [str(item) for item in argv]
            self.command_log.append(args)
            failed = any(label in " ".join(args) for label in self.failing_labels)
            runner_self.records.append(
                {"command": " ".join(args), "status": f"rc={1 if failed else 0}", "seconds": 0.0}
            )
            return 1 if failed else 0

        def fake_inspect_batch(runner_self, requests):
            for request in requests:
                runner_self.inspection_checks.append({"id": request["id"], "status": "passed"})
            runner_self.records.append({"command": "inspect batch", "status": "rc=0", "seconds": 0.0})
            return 0

        original_command, original_inspect_batch = Runner.command, Runner.inspect_batch
        Runner.command = fake_command
        Runner.inspect_batch = fake_inspect_batch
        self.addCleanup(setattr, Runner, "command", original_command)
        self.addCleanup(setattr, Runner, "inspect_batch", original_inspect_batch)

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        origin = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, origin)

        self.project = self.verifier["_sc_project"](self.root)
        (self.project / "widget.step").write_bytes(b"assembly-v1")

    def _run(self, *extra_args: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = self.verifier["main"](["proj", *extra_args])
            except SystemExit as exc:
                code = exc.code
        return code, err.getvalue()

    def _report(self) -> str:
        return (self.project / "measure" / "verification-pipeline.md").read_text(encoding="utf-8")

    def test_second_sweep_on_unchanged_project_reuses_the_verdict(self):
        first_code, first_err = self._run()
        self.assertEqual(first_code, 0, first_err)
        first_report = self._report()
        self.assertNotIn("reused", first_report)
        self.assertIn("- Closure: sha256:", first_report)
        first_calls = len(self.command_log)

        second_code, second_err = self._run()

        self.assertEqual(second_code, 0, second_err)
        # A reused sweep still regenerates STEP (check_layout + gen, the cheap
        # ~1% ADR 0070 accepts paying every time) but runs none of the
        # expensive gates a full sweep would.
        self.assertEqual(len(self.command_log), first_calls + 2, "a reused sweep must skip the expensive gates")
        second_report = self._report()
        self.assertIn("| reused |", second_report)
        self.assertIn("Previous pipeline record (preserved)", second_report)
        self.assertIn(first_report.splitlines()[4], second_report)  # preserved Result line survives

    def test_reused_failing_verdict_exits_non_zero_and_is_not_upgraded(self):
        (self.project / "measure" / "mounts.json").write_text("{}", encoding="utf-8")
        self.failing_labels = {"check_mount"}

        first_code, _ = self._run()
        self.assertNotEqual(first_code, 0)
        first_calls = len(self.command_log)

        second_code, _ = self._run()

        self.assertEqual(second_code, first_code)
        self.assertEqual(len(self.command_log), first_calls + 2, "a reused FAIL must skip the expensive gates")
        self.assertIn("| reused |", self._report())

    def test_unverified_verdict_is_never_reused(self):
        original = self.verifier["_prior_terminal_verdict"]
        report_path = self.project / "measure" / "verification-pipeline.md"
        self._run()
        # Overwrite the recorded verdict as UNVERIFIED with a matching closure,
        # the way an interrupted inspection batch would leave it.
        text = report_path.read_text(encoding="utf-8")
        text = text.replace("**PASS**", "**UNVERIFIED**", 1)
        report_path.write_text(text, encoding="utf-8")
        self.assertIsNone(original(report_path))
        first_calls_before_rerun = len(self.command_log)

        code, err = self._run()

        self.assertEqual(code, 0, err)
        self.assertGreater(len(self.command_log), first_calls_before_rerun,
                            "an UNVERIFIED verdict must run a full sweep, not reuse")
        self.assertNotIn("reused", self._report())

    def test_no_recorded_verdict_runs_a_full_sweep(self):
        self.assertFalse((self.project / "measure" / "verification-pipeline.md").exists())
        code, err = self._run()
        self.assertEqual(code, 0, err)
        self.assertNotIn("reused", self._report())

    def test_changed_step_bytes_for_a_part_force_a_full_sweep(self):
        self._run()
        (self.project / "widget.step").write_bytes(b"assembly-v2")
        code, err = self._run()
        self.assertEqual(code, 0, err)
        self.assertNotIn("| reused |", self._report())

    def test_changed_verifier_arguments_force_a_full_sweep(self):
        self._run()
        code, err = self._run("--verbose")
        self.assertEqual(code, 0, err)
        self.assertNotIn("| reused |", self._report())

    def test_changed_documented_entry_map_forces_a_full_sweep(self):
        self._run()
        (self.project / "README.md").write_text("# Widget\n", encoding="utf-8")
        code, err = self._run()
        self.assertEqual(code, 0, err)
        self.assertNotIn("| reused |", self._report())

    def test_changed_signature_review_forces_a_full_sweep(self):
        self._run()
        review_path = self.project / self.verifier["SIGNATURE_REVIEW_RELATIVE"]
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["largest_risk"] = "A different fixture risk."
        review_path.write_text(
            json.dumps(review, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
        code, err = self._run()
        self.assertEqual(code, 0, err)
        self.assertNotIn("| reused |", self._report())

    def test_no_report_never_attempts_reuse(self):
        self._run()
        code, err = self._run("--no-report")
        self.assertEqual(code, 0, err)
        # --no-report writes nothing, so the prior PASS report is untouched.
        self.assertNotIn("reused", self._report())


class SweepClosureHashTest(unittest.TestCase):
    """Unit coverage for the closure hash itself: a miss on every input class."""

    def setUp(self):
        self.verifier = runpy.run_path(str(VERIFIER))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "proj"
        (self.project / "measure").mkdir(parents=True)
        self.entry = self.project / "widget.step.py"
        self.entry.write_text("PRINTABLE = False\n", encoding="utf-8")
        self.built_step = self.project / "widget.step"
        self.built_step.write_bytes(b"content-v1")
        self.tool = self.root / "tool.py"
        self.tool.write_text("print('v1')\n", encoding="utf-8")

    def _closure(self, **overrides):
        kwargs = dict(
            entries=[self.entry],
            cwd=self.root,
            project=self.project,
            raw_argv=["proj"],
            signature_review_sha256="deadbeef",
            tool_paths=[self.tool],
        )
        kwargs.update(overrides)
        return self.verifier["_sweep_closure_sha256"](**kwargs)

    def test_identical_inputs_hash_identically(self):
        self.assertEqual(self._closure(), self._closure())

    def test_changed_step_bytes_change_the_hash(self):
        original = self._closure()
        self.built_step.write_bytes(b"content-v2")
        self.assertNotEqual(original, self._closure())

    def test_changed_argv_changes_the_hash(self):
        original = self._closure()
        self.assertNotEqual(original, self._closure(raw_argv=["proj", "--verbose"]))

    def test_changed_tool_source_bytes_change_the_hash(self):
        original = self._closure()
        self.tool.write_text("print('v2')\n", encoding="utf-8")
        self.assertNotEqual(original, self._closure())

    def test_changed_signature_review_changes_the_hash(self):
        original = self._closure()
        self.assertNotEqual(original, self._closure(signature_review_sha256="other"))

    def test_changed_documented_entry_map_changes_the_hash(self):
        original = self._closure()
        (self.project / "README.md").write_text("# Widget\n", encoding="utf-8")
        self.assertNotEqual(original, self._closure())

    def test_missing_built_step_is_an_uncomputable_closure(self):
        self.built_step.unlink()
        self.assertIsNone(self._closure())

    def test_missing_tool_source_is_an_uncomputable_closure(self):
        self.tool.unlink()
        self.assertIsNone(self._closure())


class PriorTerminalVerdictTest(unittest.TestCase):
    def setUp(self):
        self.verifier = runpy.run_path(str(VERIFIER))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.report = Path(temporary.name).resolve() / "verification-pipeline.md"

    def _read(self):
        return self.verifier["_prior_terminal_verdict"](self.report)

    def test_missing_report_is_a_miss(self):
        self.assertIsNone(self._read())

    def test_corrupted_report_with_no_closure_line_is_a_miss(self):
        self.report.write_text("# Verification pipeline record\n\n- Result: **PASS** (exit 0)\n",
                                encoding="utf-8")
        self.assertIsNone(self._read())

    def test_unverified_verdict_is_a_miss(self):
        self.report.write_text(
            "- Result: **UNVERIFIED** (exit 0)\n- Closure: sha256:" + "a" * 64 + "\n",
            encoding="utf-8",
        )
        self.assertIsNone(self._read())

    def test_pass_verdict_yields_exit_code_and_closure(self):
        closure = "b" * 64
        self.report.write_text(
            f"- Result: **PASS** (exit 0)\n- Closure: sha256:{closure}\n", encoding="utf-8",
        )
        self.assertEqual(self._read(), (0, closure))

    def test_fail_verdict_yields_its_own_exit_code(self):
        closure = "c" * 64
        self.report.write_text(
            f"- Result: **FAIL** (exit 1)\n- Closure: sha256:{closure}\n", encoding="utf-8",
        )
        self.assertEqual(self._read(), (1, closure))


if __name__ == "__main__":
    unittest.main()
