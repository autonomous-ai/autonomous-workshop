import unittest

from inventor_workshop import CapabilityReleaseProof, ReleaseProofSource
from inventor_workshop.errors import ContractError


class PlaytestReleaseProofContractTest(unittest.TestCase):
    def source(self, role="step-model", scope="product", path="toy.step"):
        return ReleaseProofSource(role, scope, path, "a" * 64)

    def test_public_typed_proof_round_trips_for_custom_adapters(self):
        proof = CapabilityReleaseProof(
            capability="motion-test",
            artifact_sha256="b" * 64,
            proof_class="kinematic-motion-proof",
            sources=(
                self.source(),
                self.source(
                    "motion-receipt", "playtest", "motion-receipt.json"
                ),
            ),
            measurements={
                "states_tested": 10,
                "continuous_sweep": True,
                "tolerance_cases_tested": 3,
                "load_cases_tested": 2,
                "orientations_tested": 3,
                "wear_cycles": 100,
                "misuse_cases_tested": 2,
                "collisions": 0,
                "stalls": 0,
                "failures": 0,
            },
        )
        self.assertEqual(
            CapabilityReleaseProof.from_dict(proof.to_dict()).to_dict(),
            proof.to_dict(),
        )

    def test_proof_class_cannot_be_relabelled_for_another_capability(self):
        with self.assertRaisesRegex(ContractError, "class does not match"):
            CapabilityReleaseProof(
                capability="mechanical-test",
                artifact_sha256="b" * 64,
                proof_class="kinematic-motion-proof",
                sources=(self.source(),),
                measurements={"brep_valid": True},
            )

    def test_one_file_cannot_be_relabelled_as_independent_sources(self):
        with self.assertRaisesRegex(ContractError, "cannot be relabelled"):
            CapabilityReleaseProof(
                capability="mechanical-test",
                artifact_sha256="b" * 64,
                proof_class="computed-mechanical-proof",
                sources=(
                    self.source("step-model"),
                    self.source("mechanical-receipt"),
                ),
                measurements={"brep_valid": True},
            )

    def test_sources_must_be_safe_exact_paths_and_hashes(self):
        with self.assertRaises(ContractError):
            ReleaseProofSource(
                "motion-receipt", "playtest", "../outside.json", "a" * 64
            )
        with self.assertRaises(ContractError):
            ReleaseProofSource(
                "motion-receipt", "playtest", "receipt.json", "not-a-hash"
            )


if __name__ == "__main__":
    unittest.main()
