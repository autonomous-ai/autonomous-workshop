"""ADR 0098 amendment 2026-11-17: the seal fails fast and reuses its print gates.

Contract: the design batch runs every cheap gate (the project dry run, the
Shared Helper freeze and verify_project --preflight-only: check_layout,
generation, the preflight audits and the kit gates) before the print gates,
so a cheap failure refuses the seal without starting them. A passing
print-gates step is reused while its key holds: the command, make_round, every
source the part files reach (a kit module loaded with importlib included),
the contract, the skills' LOCK and the fit table, with its summary unchanged
and passed outright; anything else reruns it, and a failure is never reused.
`seal_proof.py preflight` runs only the cheap layers and writes no approval."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from unittest import mock

from tests.skills.test_seal_proof import SealProofTest, presentation_png


class SealFailFastTest(unittest.TestCase):
    _record = SealProofTest._record
    _seal = SealProofTest._seal
    _spec_tool = SealProofTest._spec_tool
    _final_inputs = SealProofTest._final_inputs
    _render_runner = SealProofTest._render_runner

    def setUp(self):
        SealProofTest.setUp(self)
        # A kit-like Component: its part file imports kitparts, which loads
        # base4 by name, as the Amsterdam kit does.
        (self.proof / "part_body.step.py").write_text("from params import PEG_D\nimport kitparts\n")
        (self.proof / "kitparts.py").write_text(
            "import importlib\n\ndef built(name):\n    return importlib.import_module(name).kit4()\n")
        (self.proof / "base4.py").write_text("def kit4():\n    return [1]\n")
        self._final_inputs()

    def ran(self, fragment):
        return [argv for argv in self.batch_calls if fragment in argv]

    def record(self, name="measure/seeded-batch.json"):
        return {item["id"]: item for item in json.loads((self.proof / name).read_text())["steps"]}

    def _preflight(self, *extra):
        argv = ["preflight", str(self.proof), "--contract", str(self.contract), "--nozzle", "0.4", *extra]
        with mock.patch.object(self.module, "identities", side_effect=self._record), \
                mock.patch.object(self.module, "read_contract", side_effect=lambda path: self.design_contract), \
                mock.patch.object(self.module, "batch_runner",
                                  return_value=lambda *a: SealProofTest._batch_runner(self, *a)), \
                mock.patch.object(self.module, "run_spec_tool",
                                  side_effect=lambda proof, tool: SealProofTest._spec_tool(self, proof, tool)), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.module.main(argv)
        self.stderr = err.getvalue()
        return code

    # -- order -------------------------------------------------------------

    def test_the_cheap_gates_run_before_the_print_gates(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        order = [next(name for name, fragment in (("project", "--dry-run"), ("helpers", "--shared-helpers"),
                                                  ("preflight", "--preflight-only"),
                                                  ("print-gates", "--print-gates-only"),
                                                  ("final", "--print-gates")) if fragment in argv)
                 for argv in self.batch_calls
                 if any(f in argv for f in ("--dry-run", "--shared-helpers", "--preflight-only",
                                            "--print-gates-only", "--print-gates"))]
        self.assertEqual(order, ["project", "helpers", "preflight", "print-gates", "final"])
        (preflight,) = self.ran("--preflight-only")
        self.assertNotIn("--print-gates", preflight, "the preflight runs no print gate")
        (final,) = self.ran("--print-gates")
        self.assertEqual([item for item in preflight if not item.endswith(".md") and item != "--preflight-only"],
                         [item for item in final if not item.endswith(".md") and item != "--print-gates"],
                         "the same command and thresholds as final verification")

    def test_a_cheap_failure_refuses_before_any_print_gate(self):
        from workshop.make.seeded_batch import RunResult

        cheap = {
            "--dry-run": "README/spec names a CAD entry that does not exist: part_ID.step.py",
            "--preflight-only": "kit_tree.py: S72 cannot go in alone along [0, 0, -1]",
        }
        for fragment, words in cheap.items():
            with self.subTest(fragment):
                self.batch_calls = []
                self.batch_exit = {fragment: RunResult(1, words)}
                self.assertEqual(self._seal(), 1)
                self.assertIn(words, self.stderr)
                self.assertEqual(self.ran("--print-gates-only"), [], "no print gate started")
                self.assertEqual(self.ran("--print-gates"), [])
                self.assertFalse((self.proof / "APPROVAL.json").exists())
                self.assertEqual(self.record()["print-gates"]["status"], "skipped")

    def test_a_missing_spec_audit_refuses_before_the_batch(self):
        (self.proof / "measure/check_spec.py").unlink()
        self.assertEqual(self._seal(), 1)
        self.assertIn("measure/check_spec.py", self.stderr)
        self.assertEqual(self.batch_calls, [])

    # -- reuse ---------------------------------------------------------------

    def test_a_passing_print_gate_is_reused_on_an_unchanged_proof(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(len(self.ran("--print-gates-only")), 1)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(len(self.ran("--print-gates-only")), 1, "the second seal reused it")
        self.assertEqual(self.record()["print-gates"]["status"], "reused")
        self.assertEqual(len(self.ran("--preflight-only")), 2, "only the print gates are reused")
        self.assertEqual(len(self.ran("--print-gates")), 2)

    def test_a_kit_module_change_reruns_the_print_gates(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        (self.proof / "base4.py").write_text("def kit4():\n    return [2]\n")
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(len(self.ran("--print-gates-only")), 2, "base4 is loaded by name, and still binds")

    def test_anything_else_the_key_binds_reruns_them(self):
        changes = {
            "a data file": lambda: (self.proof / "kitmap.json").write_text('{"a": 2}'),
            "the contract": lambda: self.contract.write_text("# Toy, amended\n"),
            "the fit table": lambda: self.env.setdefault("WORKSHOP_FIT_TABLE", "cadfits-2026-11-01"),
        }
        (self.proof / "kitmap.json").write_text('{"a": 1}')
        self.env = {}
        for name, change in changes.items():
            with self.subTest(name), mock.patch.dict("os.environ", self.env):
                self.batch_calls = []
                self.assertEqual(self._seal(), 0, self.stderr)
                change()
            with mock.patch.dict("os.environ", self.env):
                self.batch_calls = []
                code = self._seal()
                if name == "the fit table":
                    self.assertEqual(code, 1, "a seal under another table refuses at once")
                    continue
                self.assertEqual(code, 0, self.stderr)
                self.assertEqual(len(self.ran("--print-gates-only")), 1, name)

    def test_a_note_or_a_render_never_reruns_them(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        (self.proof / "toy_spec.md").write_text("# spec, reworded\n")
        (self.proof / "measure/notes.txt").write_text("a note")
        (self.proof / "snap/iso.png").write_bytes(presentation_png(800, 800, shade=40))
        self.batch_calls = []
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(self.ran("--print-gates-only"), [])

    def test_a_failed_or_unverified_or_rewritten_result_is_never_reused(self):
        from workshop.make.seeded_batch import RunResult

        self.batch_exit = {"--print-gates-only": RunResult(1, "print gates: body overhang 52 deg over 45")}
        self.assertEqual(self._seal(), 1)
        self.batch_exit = {}
        self.batch_calls = []
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(len(self.ran("--print-gates-only")), 1, "a failure is never reused")
        cases = {
            "unverified": {"interference": {"verdict": "unverified", "detail": "timed out"}},
            "rewritten": {"note": "a standalone run wrote this summary"},
        }
        for name, change in cases.items():
            with self.subTest(name):
                self._final_inputs(**change)
                self.batch_calls = []
                self.assertEqual(self._seal(), 0, self.stderr)
                self.assertEqual(len(self.ran("--print-gates-only")), 1, name)

    # -- preflight -----------------------------------------------------------

    def test_preflight_runs_the_cheap_gates_and_writes_no_approval(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = (self.proof / "APPROVAL.json").read_bytes()
        copies = sorted(path.name for path in (self.proof / "approved").iterdir())
        batch = (self.proof / "measure/seeded-batch.json").read_bytes()
        self.batch_calls = []
        self.assertEqual(self._preflight(), 0, self.stderr)
        self.assertTrue(self.ran("--preflight-only"))
        self.assertEqual(self.ran("--print-gates-only"), [])
        self.assertEqual(self.ran("--print-gates"), [])
        self.assertEqual((self.proof / "APPROVAL.json").read_bytes(), approval)
        self.assertEqual(sorted(path.name for path in (self.proof / "approved").iterdir()), copies)
        self.assertEqual((self.proof / "measure/seeded-batch.json").read_bytes(), batch,
                         "the seal's record, and its print-gate pass, are kept")
        self.assertEqual(set(self.record("measure/seal-preflight.json")),
                         {"project", "shared-helpers", "preflight"})
        self.assertFalse(any(path.name.startswith(".seal-proof") for path in self.proof.parent.iterdir()))

    def test_preflight_refuses_what_the_seal_would(self):
        from workshop.make.seeded_batch import RunResult

        self.batch_exit = {"--preflight-only": RunResult(1, "check_layout: base4.py 513 code lines > 400")}
        self.assertEqual(self._preflight(), 1)
        self.assertIn("513 code lines > 400", self.stderr)
        self.assertFalse((self.proof / "APPROVAL.json").exists())
        (self.proof / "CRITIC.json").write_text(json.dumps({"verdict": "disagree", "requirements": []}))
        self.assertEqual(self._preflight(), 1)
        self.assertIn("Proof Critic's verdict is 'disagree'", self.stderr)


if __name__ == "__main__":
    unittest.main()
