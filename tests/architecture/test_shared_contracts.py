import unittest

from workshop.errors import ContractError
from workshop.playtest.evidence import GateResult
from workshop.runtime import Receipt, Stamp
from workshop._validation import require_exact_version, require_safe_evidence_path

SHA = "a" * 64


class SharedContractValidationTest(unittest.TestCase):
    def test_receipt_is_canonical_while_persisted_fields_stay_readable(self):
        receipt = Receipt.create(
            payload_sha256=SHA,
            artifact_sha256=SHA,
            adapter="example",
            status="accepted",
            reference="external-1",
            details={"verified": True},
        )
        self.assertIs(Stamp, Receipt)
        self.assertEqual(receipt.payload_sha256, SHA)
        self.assertEqual(receipt.pack_sha256, SHA)
        self.assertEqual(receipt.adapter, "example")
        self.assertEqual(receipt.door, "example")
        persisted = receipt.to_dict()
        self.assertIn("pack_sha256", persisted)
        self.assertIn("door", persisted)
        self.assertNotIn("payload_sha256", persisted)
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

    def test_gate_evidence_is_finite_json_and_revalidated(self):
        evidence = {"score": 1.0}
        gate = GateResult(
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
        evidence["score"] = float("nan")
        with self.assertRaises(ContractError):
            gate.assert_valid()


if __name__ == "__main__":
    unittest.main()
