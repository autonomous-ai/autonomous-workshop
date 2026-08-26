import unittest

import workshop.playtest.evidence as playtest_evidence
import workshop.runtime as runtime
from workshop.errors import ContractError
from workshop.playtest.evidence import PlaytestResult
from workshop.runtime import Receipt
from workshop._validation import require_exact_version, require_safe_evidence_path

SHA = "a" * 64


class SharedContractValidationTest(unittest.TestCase):
    def test_runtime_public_api_exposes_only_the_canonical_receipt(self):
        self.assertTrue(hasattr(runtime, "Receipt"))
        for legacy in (
            "PublicationOutcome",
            "PublicationReceipt",
            "SendResult",
            "Stamp",
        ):
            with self.subTest(legacy=legacy):
                self.assertFalse(hasattr(runtime, legacy))

    def test_playtest_public_api_has_no_inspection_or_gate_aliases(self):
        for legacy in ("GateResult", "InspectionResult"):
            with self.subTest(legacy=legacy):
                self.assertFalse(hasattr(playtest_evidence, legacy))

    def test_receipt_uses_one_canonical_in_memory_and_persisted_shape(self):
        receipt = Receipt.create(
            payload_sha256=SHA,
            artifact_sha256=SHA,
            adapter="example",
            status="accepted",
            reference="external-1",
            details={"verified": True},
        )
        self.assertEqual(receipt.payload_sha256, SHA)
        self.assertEqual(receipt.adapter, "example")
        persisted = receipt.to_dict()
        self.assertEqual(persisted["payload_sha256"], SHA)
        self.assertEqual(persisted["adapter"], "example")
        self.assertNotIn("pack_sha256", persisted)
        self.assertNotIn("door", persisted)
        self.assertEqual(Receipt.from_dict(persisted), receipt)

    def test_exact_versions_reject_ranges_wildcards_and_moving_labels(self):
        for value in (
            "latest",
            "1.*",
            "1.x",
            ">=1.2",
            "^1.2.3",
            "1.2-SNAPSHOT",
            "main-1",
            "version one",
        ):
            with self.subTest(value=value), self.assertRaises(ContractError):
                require_exact_version(value)
        for value in ("1", "v1.2.3", "2026.08.23", "1.0.0-rc1+build.7"):
            with self.subTest(value=value):
                self.assertEqual(require_exact_version(value), value)

    def test_evidence_path_is_a_file_like_control_free_relative_path(self):
        for value in (".", "../proof.json", "/proof.json", "proof\\x", "proof\n.json"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                require_safe_evidence_path(value)
        self.assertEqual(
            require_safe_evidence_path("evidence/proof.json"),
            "evidence/proof.json",
        )

    def test_playtest_result_is_finite_json_and_revalidated(self):
        evidence = {"score": 1.0}
        result = PlaytestResult(
            "novelty",
            True,
            SHA,
            evidence,
            "autonomous-workshop.novelty",
            "1.0.0",
            SHA,
            "evidence/novelty.json",
            SHA,
            "2026-08-23T00:00:00+00:00",
        )
        self.assertEqual(result.playtest_id, "novelty")
        self.assertFalse(hasattr(result, "gate_id"))
        evidence["score"] = float("nan")
        with self.assertRaises(ContractError):
            result.assert_valid()


if __name__ == "__main__":
    unittest.main()
