import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.errors import StateConflict
from workshop.make.native_gate import (
    NATIVE_CAD_GATE_KIND,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
)
from workshop.workflow.agent_run import AgentArtifact
from workshop.workflow.native_run import _validate_legacy_full_tier_make_gate
from workshop.workflow.stage_gates import StageGateDecision, StageGateEvidence


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class LegacyCadCompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.host_root = Path(self.temporary.name).resolve() / "host"
        (self.host_root / "gates").mkdir(parents=True, mode=0o700)
        (self.host_root / "evidence" / "make").mkdir(parents=True, mode=0o700)
        self.made_sha = "a" * 64
        self.product_sha = "b" * 64
        self.verifier_sha = "c" * 64
        self.artifact = AgentArtifact(
            "artifacts/make/r0002/made.json", "d" * 64
        )
        self.made = SimpleNamespace(
            round=2,
            made_sha256=self.made_sha,
            product_manifest=SimpleNamespace(artifact_sha256=self.product_sha),
            cad_project_path="cad",
        )
        self.checkpoint = SimpleNamespace(
            stage="playtest",
            revision=6,
            stage_artifacts={"make": (self.artifact,)},
        )
        self.run = SimpleNamespace(
            host_state_root=self.host_root,
            assert_predecessor_gate_accepted=mock.Mock(),
        )

    def _write_private_json(self, path, value):
        path.write_bytes(_canonical(value) + b"\n")
        os.chmod(path, 0o600)

    def _write_fixture(self, *, cad_made_sha=None, tamper_gate=False):
        stream = {
            "captured_text": "",
            "captured_bytes": 0,
            "total_bytes": 0,
            "sha256": _sha(b""),
            "truncated": False,
        }
        cad_identity = {
            "schema_version": 1,
            "kind": NATIVE_CAD_GATE_KIND,
            "passed": True,
            "failure_code": None,
            "made_sha256": cad_made_sha or self.made_sha,
            "product_artifact_sha256": self.product_sha,
            "cad_project_path": "cad",
            "cad_project_sha256": "e" * 64,
            "verifier_path": NATIVE_CAD_VERIFIER_PATH,
            "verifier_sha256": self.verifier_sha,
            "verifier_mode": NATIVE_CAD_VERIFIER_MODE,
            "command": [
                "<python>",
                NATIVE_CAD_VERIFIER_PATH,
                "<isolated-cad-project>",
                "--fresh",
                "--exports",
                "--strict-fit",
            ],
            "returncode": 0,
            "duration_ms": 12,
            "timed_out": False,
            "stdout": stream,
            "stderr": stream,
            "source_tree_unchanged": True,
        }
        receipt_sha = _sha(_canonical(cad_identity))
        self._write_private_json(
            self.host_root / "evidence" / "make" / "r0002-cad-gate.json",
            {**cad_identity, "receipt_sha256": receipt_sha},
        )
        evidence = StageGateEvidence(
            stage="make",
            gate_id="make.sealed-revision-v1",
            validator_version="1.0.0",
            passed=True,
            checkpoint_sha256="f" * 64,
            subject_sha256="1" * 64,
            outcome_sha256="2" * 64,
            artifact_path=self.artifact.path,
            artifact_sha256=self.artifact.sha256,
            checks={
                "made_sha256": self.made_sha,
                "product_artifact_sha256": self.product_sha,
                "product_tree_rehashed": True,
                "upstream_bindings_valid": True,
                "cad_receipt_sha256": receipt_sha,
                "cad_verifier_sha256": self.verifier_sha,
                "cad_verification_passed": True,
            },
        )
        gate = StageGateDecision(evidence=evidence, transition="playtest").to_dict()
        if tamper_gate:
            gate["evidence"]["checks"]["made_sha256"] = "9" * 64
        self._write_private_json(self.host_root / "gates" / "0005-make.json", gate)

    def _validate(self):
        _validate_legacy_full_tier_make_gate(
            run=self.run,
            checkpoint=self.checkpoint,
            made_artifact=self.artifact,
            made=self.made,
            expected_verifier_sha256=self.verifier_sha,
        )

    def test_matching_history_bound_legacy_full_gate_is_accepted(self):
        self._write_fixture()

        self._validate()

        self.run.assert_predecessor_gate_accepted.assert_called_once()

    def test_playtest_retry_keeps_using_the_immutable_make_evidence(self):
        self._write_fixture()
        accepted_path = (
            self.host_root / "evidence" / "make" / "r0002-cad-gate.json"
        )
        accepted_bytes = accepted_path.read_bytes()
        (self.host_root / "evidence" / "playtest").mkdir(mode=0o700)
        self._write_private_json(
            self.host_root
            / "evidence"
            / "playtest"
            / "r0002-cad-gate.json",
            {"failed_replay": True},
        )

        self._validate()
        self._validate()

        self.assertEqual(accepted_path.read_bytes(), accepted_bytes)
        self.assertEqual(
            self.run.assert_predecessor_gate_accepted.call_count, 2
        )

    def test_mismatched_cad_evidence_hash_fails_closed(self):
        self._write_fixture(cad_made_sha="8" * 64)

        with self.assertRaisesRegex(StateConflict, "legacy CAD gate evidence"):
            self._validate()

    def test_tampered_make_gate_fails_before_history_trust(self):
        self._write_fixture(tamper_gate=True)

        with self.assertRaisesRegex(StateConflict, "accepted Make gate is invalid"):
            self._validate()
        self.run.assert_predecessor_gate_accepted.assert_not_called()


if __name__ == "__main__":
    unittest.main()
