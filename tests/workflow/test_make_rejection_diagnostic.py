"""Issue #231: a Make proposal rejection names what refused it.

Contract: every rejection the host records carries a `diagnostic` naming the
innermost Workshop function that raised (`module:function`, the check), the
host's own message (which names the field and file), and the exception that
caused it. Each is one bounded line, run paths made relative. A record
written before the diagnostic existed stays valid; a malformed diagnostic is
refused."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.seed_check import verify_made_seed
from workshop.workflow.native_run import (
    _MAKE_PROPOSAL_REJECTION_FEEDBACK,
    _MAX_MAKE_REJECTION_DETAIL_CHARS,
    _make_rejection_for_error,
    _valid_make_rejection_diagnostic,
)


def _raise_from(cause, message):
    try:
        raise cause
    except Exception as exc:
        raise ContractError(message) from exc


class MakeRejectionDiagnosticTest(unittest.TestCase):
    def _rejection(self, function, run_root=None):
        try:
            function()
        except ContractError as error:
            return _make_rejection_for_error(error, run_root)
        self.fail("no error raised")

    def test_a_seed_comparison_that_could_not_run_is_named(self):
        """The arcade run's case: the host's proof_diff could not import the
        CAD kernel, and the rejection said only make-contract-invalid."""
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            project = run_root / "artifacts/make/r0001/product/cad"
            rounds = project / "measure/component-rounds/bezel"
            (rounds / "r0001").mkdir(parents=True)
            (rounds / "make-round-state.json").write_text(json.dumps({"round": 1}))
            (rounds / "r0001/summary.json").write_text(json.dumps({
                "identity": "A",
                "review": {"agrees": True, "seed": "exact", "carried_from": "seed-approval"},
            }))
            (project / "part_bezel.step").write_bytes(b"made")

            def compare(approved, made):
                raise ImportError("%s/lib/pyexpat.so: undefined symbol: XML_SetAlloc" % run_root)

            rejection = self._rejection(lambda: verify_made_seed(
                project, run_root,
                {"bezel": {"identity": "A", "approved_step": "approved/part_bezel.step"}},
                compare=compare,
            ), run_root)
        self.assertEqual(rejection.failure_code, "make-contract-invalid")
        self.assertEqual(rejection.feedback, _MAKE_PROPOSAL_REJECTION_FEEDBACK["make-contract-invalid"])
        diagnostic = rejection.diagnostic
        self.assertEqual(diagnostic["check"], "workshop.make.seed_check:verify_made_seed")
        self.assertIn("part_bezel.step", diagnostic["message"])
        self.assertIn("could not compare them (ImportError: lib/pyexpat.so", diagnostic["message"])
        self.assertNotIn(str(run_root), diagnostic["message"])
        self.assertIsNone(diagnostic["cause"])  # the compare error is folded into the message
        self.assertTrue(_valid_make_rejection_diagnostic(diagnostic))

    def test_the_cause_is_named_and_every_line_is_bounded(self):
        rejection = self._rejection(lambda: _raise_from(
            OSError("disk\nfull"), "made.json field 'x' is invalid:\t" + "v" * 2000,
        ))
        diagnostic = rejection.diagnostic
        self.assertEqual(diagnostic["check"], "unknown")  # raised outside Workshop code
        self.assertEqual(diagnostic["cause"], "OSError: disk full")
        self.assertEqual(len(diagnostic["message"]), _MAX_MAKE_REJECTION_DETAIL_CHARS)
        self.assertTrue(diagnostic["message"].startswith("made.json field 'x' is invalid: vvv"))
        self.assertTrue(diagnostic["message"].endswith("..."))
        self.assertTrue(_valid_make_rejection_diagnostic(diagnostic))

    def test_every_rejection_class_carries_a_diagnostic(self):
        for message in ("Make must use Workshop's accepted inventor selection",
                        "Made product title must be text", "anything else"):
            with self.subTest(message):
                rejection = self._rejection(lambda: _raise_from(ValueError("v"), message))
                self.assertEqual(rejection.diagnostic["message"], message)
                self.assertTrue(_valid_make_rejection_diagnostic(rejection.diagnostic))

    def test_a_malformed_diagnostic_is_refused(self):
        good = {"check": "workshop.make.seed_check:verify_made_seed", "message": "seed: x", "cause": None}
        self.assertTrue(_valid_make_rejection_diagnostic(good))
        for bad in (
            None, [], {**good, "extra": "x"}, {key: good[key] for key in ("check", "message")},
            {**good, "check": ""}, {**good, "message": "two\nlines"},
            {**good, "message": "m" * (_MAX_MAKE_REJECTION_DETAIL_CHARS + 1)},
            {**good, "check": "c" * 161}, {**good, "cause": 3}, {**good, "message": None},
        ):
            with self.subTest(bad):
                self.assertFalse(_valid_make_rejection_diagnostic(bad))


if __name__ == "__main__":
    unittest.main()
