import unittest

from inventor_workshop.cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    WORKSHOP_CHECKS,
    WORKSHOP_CHECK_MEASUREMENTS,
    WORKSHOP_REQUIRED_CHECKS,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
    assert_release_ready,
)
from inventor_workshop.errors import ContractError, TransitionError

SHA = "a" * 64
CONFIG = "b" * 64
EVIDENCE = "c" * 64
PROFILE = "d" * 64
SKILL = "e" * 64

SUBSTRATE_CHECKS = {
    "deterministic": tuple(
        sorted(
            name
            for name in WORKSHOP_REQUIRED_CHECKS
            if name
            not in {"form-review", "safety"}
        )
    ),
    "independent-review": ("form-review", "safety"),
    "physical": ("physical-claims",),
}

PASSING_MEASUREMENTS = {
    "manifest": {"inventory_valid": True},
    "brep": {"valid_solids": 1, "invalid_solids": 0},
    "mesh-topology": {"watertight_parts": 1, "non_manifold_edges": 0},
    "dimensions": {"measured_parts": 1, "out_of_tolerance": 0},
    "interference": {"poses_tested": 1, "forbidden_intersections": 0},
    "bed-packing": {"beds_used": 1, "out_of_bounds_parts": 0},
    "slicer": {
        "profiles_checked": 1,
        "slicer_errors": 0,
        "support_material_grams": 0.0,
    },
    "form-review": {"views_reviewed": 3, "blockers": 0},
    "safety": {"hazards_found": 0, "review_scope": "intended tabletop use"},
    "physical-claims": {"claims_tested": 1, "claims_failed": 0},
}


class CadContractTest(unittest.TestCase):
    def manifest(self, claim_status="passed", orientation=(0, 0, 0)):
        return CadProjectManifest(
            schema_version=1,
            project_id="game",
            artifact_sha256=SHA,
            engine={"name": "build123d", "version": "0.9.1"},
            skill_versions={"cad": SKILL},
            parts=(
                CadPart(
                    "token",
                    "Token",
                    4,
                    "parts/token.py",
                    "parts/token.step",
                    "parts/token.stl",
                    "PLA",
                    orientation,
                ),
            ),
            assemblies=(),
            fits=(),
            motions=(),
            print_profile={"process": "FDM", "profile_sha256": PROFILE},
            evidence_files={
                "evidence/coupon-1.json": EVIDENCE,
                **{
                    "evidence/%s.json" % name: EVIDENCE
                    for names in SUBSTRATE_CHECKS.values()
                    for name in names
                },
            },
            physical_claims=(
                PhysicalClaim(
                    "snap-life",
                    "snap survives repeated use",
                    True,
                    claim_status,
                    "evidence/coupon-1.json" if claim_status == "passed" else None,
                    EVIDENCE if claim_status == "passed" else None,
                ),
            ),
        )

    def receipt(self, substrate, status="passed", artifact=SHA, evidence=EVIDENCE):
        checks = SUBSTRATE_CHECKS[substrate]
        return VerificationReceipt.create(
            artifact,
            "%s-validator" % substrate,
            "1.0.0",
            CONFIG,
            substrate,
            tuple(
                VerificationCheck(
                    name,
                    status,
                    dict(PASSING_MEASUREMENTS[name]) if status == "passed" else {},
                    "evidence/%s.json" % name,
                    evidence,
                )
                for name in checks
            ),
        )

    def requirements(self, deterministic_version="1.0.0"):
        return tuple(
            ValidatorRequirement(
                "%s-validator" % substrate,
                deterministic_version if substrate == "deterministic" else "1.0.0",
                CONFIG,
                substrate,
                checks,
            )
            for substrate, checks in SUBSTRATE_CHECKS.items()
        )

    def receipts(self, status="passed"):
        return tuple(self.receipt(substrate, status) for substrate in SUBSTRATE_CHECKS)

    def test_release_ready_requires_exact_passed_evidence(self):
        assert_release_ready(self.manifest(), self.receipts(), self.requirements())
        with self.assertRaises(TransitionError):
            assert_release_ready(self.manifest(), (), self.requirements())
        with self.assertRaises(TransitionError):
            assert_release_ready(
                self.manifest("held"), self.receipts(), self.requirements()
            )
        with self.assertRaises(TransitionError):
            assert_release_ready(
                self.manifest(), self.receipts(), self.requirements("2.0.0")
            )
        with self.assertRaises(TransitionError):
            assert_release_ready(
                self.manifest(),
                self.receipts(),
                (
                    ValidatorRequirement(
                        "deterministic-validator",
                        "1.0.0",
                        CONFIG,
                        "deterministic",
                        ("mesh-topology",),
                    ),
                ),
            )

    def test_empty_or_unbound_evidence_and_floating_versions_fail_closed(self):
        with self.assertRaises(ContractError):
            VerificationCheck(
                "mesh-topology", "passed", {}, "evidence/mesh.json", EVIDENCE
            )
        with self.assertRaises(ContractError):
            ValidatorRequirement(
                "self-report", "latest", CONFIG, "deterministic", ("mesh-topology",)
            )
        receipts = list(self.receipts())
        receipts[0] = self.receipt("deterministic", evidence="f" * 64)
        with self.assertRaises(TransitionError):
            assert_release_ready(self.manifest(), tuple(receipts), self.requirements())

    def test_all_ten_workshop_checks_have_typed_release_floors(self):
        self.assertEqual(set(WORKSHOP_CHECK_MEASUREMENTS), set(WORKSHOP_CHECKS))
        self.assertEqual(set(PASSING_MEASUREMENTS), set(WORKSHOP_CHECKS))
        for check_id in sorted(WORKSHOP_CHECKS):
            VerificationCheck(
                check_id,
                "passed",
                PASSING_MEASUREMENTS[check_id],
                "evidence/%s.json" % check_id,
                EVIDENCE,
            )
            with self.subTest(check_id=check_id), self.assertRaises(ContractError):
                VerificationCheck(
                    check_id,
                    "passed",
                    {},
                    "evidence/%s.json" % check_id,
                    EVIDENCE,
                )

    def test_workshop_pass_thresholds_cannot_be_replaced_by_truthy_claims(self):
        failing_measurements = {
            "manifest": {"inventory_valid": False},
            "brep": {"valid_solids": 1, "invalid_solids": 1},
            "mesh-topology": {"watertight_parts": 1, "non_manifold_edges": 1},
            "dimensions": {"measured_parts": 1, "out_of_tolerance": 1},
            "interference": {"poses_tested": 1, "forbidden_intersections": 1},
            "bed-packing": {"beds_used": 1, "out_of_bounds_parts": 1},
            "slicer": {
                "profiles_checked": 1,
                "slicer_errors": 1,
                "support_material_grams": 0,
            },
            "form-review": {"views_reviewed": 2, "blockers": 0},
            "safety": {"hazards_found": 1, "review_scope": "tabletop use"},
            "physical-claims": {"claims_tested": 1, "claims_failed": 1},
        }
        for check_id, measurements in sorted(failing_measurements.items()):
            with self.subTest(check_id=check_id), self.assertRaises(ContractError):
                VerificationCheck(
                    check_id,
                    "passed",
                    measurements,
                    "evidence/%s.json" % check_id,
                    EVIDENCE,
                )
        with self.assertRaises(ContractError):
            VerificationCheck(
                "brep",
                "passed",
                {"valid_solids": True, "invalid_solids": 0},
                "evidence/brep.json",
                EVIDENCE,
            )
        with self.assertRaises(ContractError):
            VerificationCheck(
                "slicer",
                "passed",
                {
                    "profiles_checked": 1,
                    "slicer_errors": 0,
                    "support_material_grams": float("nan"),
                },
                "evidence/slicer.json",
                EVIDENCE,
            )
        with self.assertRaises(ContractError):
            VerificationCheck(
                "safety",
                "passed",
                {"hazards_found": 0, "review_scope": "   "},
                "evidence/safety.json",
                EVIDENCE,
            )

    def test_nonpassing_workshop_checks_may_record_partial_valid_measurements(self):
        VerificationCheck(
            "brep", "held", {}, "evidence/brep.json", EVIDENCE
        )
        VerificationCheck(
            "brep",
            "failed",
            {"valid_solids": 0, "invalid_solids": 1},
            "evidence/brep.json",
            EVIDENCE,
        )
        with self.assertRaises(ContractError):
            VerificationCheck(
                "brep",
                "failed",
                {"valid_solids": -1},
                "evidence/brep.json",
                EVIDENCE,
            )

    def test_mutated_measurement_mapping_is_revalidated_at_release(self):
        receipts = list(self.receipts())
        deterministic = next(
            receipt for receipt in receipts if receipt.substrate == "deterministic"
        )
        manifest_check = next(
            check for check in deterministic.checks if check.check_id == "manifest"
        )
        manifest_check.measurements["inventory_valid"] = False
        with self.assertRaises(TransitionError):
            assert_release_ready(self.manifest(), tuple(receipts), self.requirements())

    def test_release_revalidates_mutated_manifest_maps_and_parts(self):
        mutations = (
            lambda manifest: manifest.engine.__setitem__("version", "latest"),
            lambda manifest: manifest.print_profile.__setitem__(
                "profile_sha256", "not-a-hash"
            ),
            lambda manifest: manifest.skill_versions.__setitem__("cad", "not-a-hash"),
            lambda manifest: manifest.evidence_files.__setitem__(
                "evidence/brep.json", "not-a-hash"
            ),
        )
        for mutate in mutations:
            manifest = self.manifest()
            mutate(manifest)
            with self.subTest(mutation=mutate), self.assertRaises(TransitionError):
                assert_release_ready(manifest, self.receipts(), self.requirements())

        manifest = self.manifest(orientation=[0, 0, 0])
        manifest.parts[0].print_orientation.append(float("nan"))
        with self.assertRaises(TransitionError):
            assert_release_ready(manifest, self.receipts(), self.requirements())

    def test_release_revalidates_mutated_validator_policy(self):
        requirements = list(self.requirements())
        original = requirements[0]
        mutable_checks = list(original.required_checks)
        requirements[0] = ValidatorRequirement(
            original.validator,
            original.validator_version,
            original.config_sha256,
            original.substrate,
            mutable_checks,
        )
        assert_release_ready(self.manifest(), self.receipts(), requirements)
        mutable_checks.append(mutable_checks[0])
        with self.assertRaises(TransitionError):
            assert_release_ready(self.manifest(), self.receipts(), requirements)

    def test_release_revalidates_mutated_receipt_check_list_and_status(self):
        receipts = list(self.receipts())
        original = receipts[0]
        mutable_checks = list(original.checks)
        receipts[0] = VerificationReceipt(
            original.schema_version,
            original.artifact_sha256,
            original.validator,
            original.validator_version,
            original.config_sha256,
            original.substrate,
            original.status,
            mutable_checks,
            original.observed_at,
        )
        assert_release_ready(self.manifest(), receipts, self.requirements())
        mutable_checks.append(
            VerificationCheck(
                "project-extra",
                "held",
                {},
                "evidence/manifest.json",
                EVIDENCE,
            )
        )
        with self.assertRaises(TransitionError):
            assert_release_ready(self.manifest(), receipts, self.requirements())

    def test_bundle_hash_revalidates_all_nested_contracts(self):
        manifest = self.manifest()
        receipts = list(self.receipts())
        requirements = list(self.requirements())
        bundle = CadReleaseBundle(manifest, receipts, requirements)
        first_sha = bundle.sha256
        self.assertEqual(len(first_sha), 64)

        manifest.engine["version"] = "latest"
        with self.assertRaises(TransitionError):
            _ = bundle.sha256

        second_bundle = CadReleaseBundle(
            self.manifest(), list(self.receipts()), list(self.requirements())
        )
        second_bundle.receipts.pop()
        with self.assertRaises(TransitionError):
            _ = second_bundle.sha256

    def test_cad_paths_reject_ascii_control_characters(self):
        for unsafe in ("parts/token\n.py", "parts/token\t.py", "evidence/\x7f.json"):
            with self.subTest(path=repr(unsafe)), self.assertRaises(ContractError):
                if unsafe.startswith("parts/"):
                    CadPart(
                        "token",
                        "Token",
                        1,
                        unsafe,
                        "parts/token.step",
                        "parts/token.stl",
                        "PLA",
                        (0, 0, 0),
                    )
                else:
                    VerificationCheck(
                        "custom",
                        "held",
                        {},
                        unsafe,
                        EVIDENCE,
                    )

    def test_nested_cad_documents_require_finite_json(self):
        with self.assertRaises(ContractError):
            VerificationCheck(
                "custom",
                "held",
                {"score": float("nan")},
                "evidence/custom.json",
                EVIDENCE,
            )
        manifest = self.manifest()
        with self.assertRaises(ContractError):
            CadProjectManifest(
                **{
                    **manifest.to_dict(),
                    "parts": manifest.parts,
                    "physical_claims": manifest.physical_claims,
                    "assemblies": ({"payload": b"not-json"},),
                }
            )


if __name__ == "__main__":
    unittest.main()
