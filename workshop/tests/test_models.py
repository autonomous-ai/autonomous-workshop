import unittest

from inventor_workshop.errors import ContractError
from inventor_workshop.models import (
    GateResult,
    require_exact_version,
    require_safe_evidence_path,
)

SHA = "a" * 64


class SharedModelValidationTest(unittest.TestCase):
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
            "inventor-workshop.novelty",
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
