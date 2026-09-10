"""The isolated CAD gate is the expensive gate, and it had no rejection budget.

Its record was overwritten in place, so a Make that could not satisfy it
resubmitted until a token cap ended the invocation. These tests hold the
counter, the budget, the crash-replay exemption that must not consume it, and
the truthful failure the run ends with once it is spent.
"""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.errors import StateConflict, WorkshopError
from workshop.make.native_gate import (
    NATIVE_CAD_NON_PRINT_READY_TIER,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
    CapturedVerifierStream,
    NativeCadGateError,
    NativeCadGateEvidence,
)
from workshop.workflow.native_run import (
    _MAX_CAD_GATE_REJECTIONS,
    _cad_gate_budget_outcome,
    _cad_gate_rejection_number,
    _cad_gate_rejection_path,
    _persist_cad_gate_rejection,
    _read_cad_gate_rejection,
)


DIGEST = "a" * 64


def _evidence(*, duration_ms, failure_code="interference-gate-failed"):
    return NativeCadGateEvidence(
        passed=False,
        failure_code=failure_code,
        made_sha256=DIGEST,
        product_artifact_sha256="b" * 64,
        cad_project_path="product/cad",
        cad_project_sha256="c" * 64,
        verifier_sha256="d" * 64,
        command=(
            "<python>",
            NATIVE_CAD_VERIFIER_PATH,
            "<isolated-cad-project>",
            "--fresh",
            "--strict-fit",
        ),
        returncode=7,
        duration_ms=duration_ms,
        timed_out=False,
        stdout=CapturedVerifierStream.from_bytes(b"inspected\n", 64 * 1024),
        stderr=CapturedVerifierStream.from_bytes(b"failed\n", 64 * 1024),
        source_tree_unchanged=True,
        verification_tier=NATIVE_CAD_NON_PRINT_READY_TIER,
        verifier_mode=NATIVE_CAD_VERIFIER_MODE,
        evidence_stage="make",
    )


class CadGateRejectionBudgetTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        host_state = root / "host-state"
        host_state.mkdir(mode=0o700)
        self.applied = []
        self.run = SimpleNamespace(
            host_state_root=host_state,
            run_root=root / "workspace",
            apply_outcome=self._apply,
        )
        self.checkpoint = SimpleNamespace(
            product_id="wish-20260909-000000-aaaaaaaa",
            stage="make",
            round_index=0,
            input_sha256s={},
            checkpoint_sha256="e" * 64,
        )
        self.proposal = SimpleNamespace(
            subject_sha256="f" * 64,
            outcome=SimpleNamespace(sha256="0" * 64, artifacts=()),
        )
        # Evidence persistence is exercised by the gate's own tests; this suite
        # is about the counter that sits above it.
        patch = mock.patch(
            "workshop.workflow.native_run._assert_persisted_cad_gate_evidence"
        )
        patch.start()
        self.addCleanup(patch.stop)

    def _apply(self, outcome):
        self.applied.append(outcome)
        return SimpleNamespace(status=outcome.status, stage=outcome.stage)

    def reject(self, duration_ms, failure_code="interference-gate-failed"):
        evidence = _evidence(
            duration_ms=duration_ms, failure_code=failure_code
        )
        return _persist_cad_gate_rejection(
            self.run,
            self.checkpoint,
            self.proposal,
            NativeCadGateError(failure_code, evidence, Path("unused")),
        )

    def test_each_distinct_isolated_verification_advances_the_counter(self):
        for expected in (1, 2, 3):
            with self.subTest(rejection=expected):
                record = self.reject(duration_ms=1_000 + expected)
                self.assertEqual(record["rejection_number"], expected)
                self.assertEqual(
                    _read_cad_gate_rejection(self.run, self.checkpoint)[
                        "rejection_number"
                    ],
                    expected,
                )

    def test_an_unchanged_resubmission_still_costs_the_budget(self):
        # Identical geometry rejected again is a second attempt: the gate ran
        # twice, so its receipt differs even when nothing else does.
        first = self.reject(duration_ms=1_000)
        second = self.reject(duration_ms=1_001)
        self.assertEqual(first["rejection_number"], 1)
        self.assertEqual(second["rejection_number"], 2)
        self.assertNotEqual(
            first["cad_gate_receipt_sha256"],
            second["cad_gate_receipt_sha256"],
        )

    def test_reprocessing_one_verification_is_not_a_second_attempt(self):
        first = self.reject(duration_ms=1_000)
        replay = self.reject(duration_ms=1_000)
        self.assertEqual(replay, first)
        self.assertEqual(replay["rejection_number"], 1)

    def test_the_budget_refuses_to_record_past_its_bound(self):
        for index in range(_MAX_CAD_GATE_REJECTIONS):
            self.reject(duration_ms=1_000 + index)
        with self.assertRaisesRegex(
            WorkshopError, "bounded host rejection budget"
        ):
            self.reject(duration_ms=9_999)

    def test_the_stage_continues_below_the_budget_and_fails_at_it(self):
        for index in range(_MAX_CAD_GATE_REJECTIONS - 1):
            record = self.reject(duration_ms=1_000 + index)
            self.assertIs(
                _cad_gate_budget_outcome(
                    self.run, self.checkpoint, self.proposal, record
                ),
                self.checkpoint,
            )
        self.assertEqual(self.applied, [])

        last = self.reject(duration_ms=8_888, failure_code="validity-gate-failed")
        self.assertEqual(last["rejection_number"], _MAX_CAD_GATE_REJECTIONS)
        _cad_gate_budget_outcome(
            self.run, self.checkpoint, self.proposal, last
        )
        self.assertEqual(len(self.applied), 1)
        outcome = self.applied[0]
        self.assertEqual((outcome.stage, outcome.status), ("make", "failed"))
        self.assertIn("validity-gate-failed", outcome.needs[0])
        self.assertIn(str(_MAX_CAD_GATE_REJECTIONS), outcome.needs[0])

    def test_token_budget_has_no_rejection_count_stop(self):
        self.checkpoint.token_budgeted = True
        for index in range(_MAX_CAD_GATE_REJECTIONS + 2):
            record = self.reject(duration_ms=1000 + index)
            self.assertIs(
                _cad_gate_budget_outcome(self.run, self.checkpoint, self.proposal, record),
                self.checkpoint,
            )
        self.assertEqual(record["rejection_number"], _MAX_CAD_GATE_REJECTIONS + 2)
        self.assertEqual(self.applied, [])

    def test_a_new_subject_starts_its_own_count(self):
        for index in range(3):
            self.reject(duration_ms=1_000 + index)
        self.proposal.subject_sha256 = "9" * 64
        self.assertEqual(self.reject(duration_ms=2_000)["rejection_number"], 1)

    def test_a_record_written_before_the_budget_existed_still_reads(self):
        # An in-flight run stopped before this change carries no counter. It
        # must resume rather than fail closed, and it counts as the first.
        record = dict(self.reject(duration_ms=1_000))
        del record["rejection_number"]
        identity = {
            key: record[key]
            for key in set(record) - {"rejection_sha256"}
        }
        canonical = json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        import hashlib

        record["rejection_sha256"] = hashlib.sha256(canonical).hexdigest()
        path = _cad_gate_rejection_path(self.run, self.checkpoint)
        path.write_bytes(
            json.dumps(
                record,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
        os.chmod(path, 0o600)

        legacy = _read_cad_gate_rejection(self.run, self.checkpoint)
        self.assertNotIn("rejection_number", legacy)
        self.assertEqual(_cad_gate_rejection_number(legacy), 1)
        self.assertEqual(self.reject(duration_ms=5_000)["rejection_number"], 2)

    def test_a_tampered_counter_is_refused(self):
        self.reject(duration_ms=1_000)
        path = _cad_gate_rejection_path(self.run, self.checkpoint)
        record = json.loads(path.read_bytes())
        record["rejection_number"] = 1 + _MAX_CAD_GATE_REJECTIONS
        path.write_bytes(
            json.dumps(
                record,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
        os.chmod(path, 0o600)
        with self.assertRaises(StateConflict):
            _read_cad_gate_rejection(self.run, self.checkpoint)

    def test_the_record_stays_private(self):
        self.reject(duration_ms=1_000)
        path = _cad_gate_rejection_path(self.run, self.checkpoint)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
