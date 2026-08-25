from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from inventor_workshop.errors import ContractError
from inventor_workshop.handoff import ManagerAssignmentHandoff
from inventor_workshop.jobs import Invented, Need, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.manager import register_workshop_engine
from inventor_workshop.world_reference_vault import (
    LOCAL_STORAGE_SECURITY_BOUNDARY,
    WorldReferenceDescriptor,
    WorldReferenceReceipt,
    WorldReferenceScope,
)
from inventor_workshop.world_service import (
    WorldEvidenceCase,
    WorldEvidenceReference,
    WorldInventInputs,
    WorldPlaytestEvidence,
    WorldProviderIdentity,
    prepare_world_invent_inputs,
    prepare_world_playtest_evidence,
)
from inventor_workshop.workshop import Workshop, WorkshopTools


def canonical_sha(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class FakeReferenceService:
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.verified = []

    def descriptors(self, wish):
        self.wish = wish
        return (self.descriptor,)

    def verify_admission(self, admission, wish, *, expected_reference_id):
        if admission != self.descriptor.admission or wish != self.wish:
            raise ContractError("different descriptor context")
        if expected_reference_id != self.descriptor.scope.reference_id:
            raise ContractError("different descriptor id")
        self.verified.append(expected_reference_id)


class FakePlaytestService:
    def __init__(self, evidence):
        self.evidence = evidence
        self.verify_calls = 0

    def evaluate(self, wish, artifact_sha256, personalization_map, invent_inputs):
        del wish, artifact_sha256, personalization_map, invent_inputs
        return self.evidence

    def verify(self, evidence, wish, artifact_sha256, personalization_map, invent_inputs):
        if evidence is not self.evidence:
            raise ContractError("different evidence")
        evidence.assert_context(
            wish, artifact_sha256, personalization_map, invent_inputs
        )
        self.verify_calls += 1


class WorldServiceTest(unittest.TestCase):
    def setUp(self):
        self.wish = Wish.create(
            "wish-world-service-001",
            "a tiny garden guardian shaped like my dog",
            constraints={"lane": "little-worlds"},
        )
        self.scope = WorldReferenceScope(
            "customer-dog",
            "customer-owned-subject",
            "the customer's dog",
            "customer states they own the reference and authorize this toy",
            ("round ears",),
            ("home address",),
            "customer-order-42",
            "customer-supplied-attestation-record",
        )
        self.admission = {
            "payload": {
                "kind": "world-reference",
                "wish_sha256": canonical_sha(self.wish.to_dict()),
                "reference_id": self.scope.reference_id,
            },
            "authentication": {"algorithm": "test-signature", "value": "sealed"},
        }
        record_sha = canonical_sha(self.admission)
        self.descriptor = WorldReferenceDescriptor(
            self.scope,
            WorldReferenceReceipt(
                self.wish.product_id,
                canonical_sha(self.wish.to_dict()),
                self.scope.reference_id,
                record_sha,
                "a" * 64,
                128,
                "b" * 64,
                64,
                "image/png",
                self.scope.subject_kind,
                self.scope.reviewer_id,
                "c" * 64,
            ),
            self.admission,
        )
        self.identity = WorldProviderIdentity(
            "isolated-world-reference-service",
            "1.0.0",
            "d" * 64,
        )

    def bundle(self) -> WorldInventInputs:
        return prepare_world_invent_inputs(
            self.wish, FakeReferenceService(self.descriptor), self.identity
        )

    def personalization(self):
        return {
            "consented_references": [self.descriptor.invent_contract()],
            "feature_to_form_map": [
                {
                    "reference_id": "customer-dog",
                    "reference_feature": "round ears",
                    "physical_form": "two rounded ear silhouettes",
                    "recognition_test": "compare both ear silhouettes with the admitted reference",
                }
            ],
        }

    def test_manager_fetch_is_verified_compact_and_raw_free(self):
        service = FakeReferenceService(self.descriptor)
        bundle = prepare_world_invent_inputs(self.wish, service, self.identity)
        self.assertEqual(service.verified, ["customer-dog"])
        self.assertEqual(bundle.references[0].admission_sha256, self.descriptor.receipt.record_sha256)
        encoded = json.dumps(bundle.to_dict(), sort_keys=True)
        self.assertNotIn("reference_bytes", encoded)
        self.assertNotIn("consent_bytes", encoded)
        self.assertFalse(bundle.to_dict()["references"][0]["raw_private_bytes_included"])
        bundle.assert_lane_contract(
            {"schema_version": 1, "lane": "little-worlds", **self.personalization()}
        )

        changed = self.personalization()
        changed["consented_references"][0]["allowed_features"] = ["blue eyes"]
        with self.assertRaisesRegex(ContractError, "exact Manager-admitted"):
            bundle.assert_lane_contract(
                {"schema_version": 1, "lane": "little-worlds", **changed}
            )

    def test_descriptor_rejects_scope_identity_tampering(self):
        mismatches = (
            replace(self.descriptor.receipt, reference_id="customer-cat"),
            replace(self.descriptor.receipt, subject_kind="customer-self"),
            replace(self.descriptor.receipt, reviewer_id="different-order-43"),
        )
        for receipt in mismatches:
            with self.subTest(receipt=receipt), self.assertRaisesRegex(
                ContractError, "scope identity differs"
            ):
                WorldReferenceDescriptor(
                    self.scope,
                    receipt,
                    self.admission,
                )

    def test_v3_handoff_round_trip_binds_only_raw_free_values(self):
        bundle = self.bundle()
        handoff = ManagerAssignmentHandoff(
            self.wish,
            "eve",
            4,
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            "5" * 64,
            ("python3", "profile.py"),
            bundle,
            None,
            3,
        )
        parsed = ManagerAssignmentHandoff.from_dict(
            handoff.to_dict(), expected_inventor_id="eve"
        )
        self.assertEqual(parsed.to_dict(), handoff.to_dict())
        self.assertEqual(
            parsed.result_binding()["world_inputs_sha256"],
            bundle.binding_sha256,
        )
        self.assertNotIn("reference_bytes", json.dumps(handoff.to_dict()))

    def test_manager_strict_workshop_waits_before_calling_invent(self):
        calls = []

        def invent(context):
            calls.append(context)
            raise AssertionError("Invent must not run without admitted descriptors")

        with tempfile.TemporaryDirectory() as temporary:
            workshop = Workshop(
                Path("inventors/eve"),
                "little-worlds",
                inventor_id="eve",
                trusted_engine=register_workshop_engine(
                    WorkshopTools(invent=invent)
                ),
                runtime_root=Path(temporary).resolve(),
            )
            result = workshop.run(self.wish)
        self.assertEqual((result.status, result.job), ("waiting", "invent"))
        self.assertEqual(result.needs[0].capability, "world-reference-descriptors")
        self.assertEqual(calls, [])

    def test_exact_bundle_reaches_invent_and_is_bound_to_accepted_event(self):
        bundle = self.bundle()
        observed = []

        def invent(context):
            observed.append(context.world_inputs)
            return Invented(
                canonical_sha(context.wish.to_dict()),
                context.taste.sha256,
                "little-worlds",
                {
                    "title": "Round-Ear Moon Garden",
                    "summary": "A small guardian garden.",
                    "lane_contract": {
                        "schema_version": 1,
                        "lane": "little-worlds",
                        **self.personalization(),
                    },
                },
                90,
                88,
            )

        def missing_make(context):
            del context
            raise WaitingFor(
                Need("make", "test-make", "Make is intentionally absent.", "Install it.")
            )

        with tempfile.TemporaryDirectory() as temporary:
            workshop = Workshop(
                Path("inventors/eve"),
                "little-worlds",
                inventor_id="eve",
                trusted_engine=register_workshop_engine(
                    WorkshopTools(invent=invent, make=missing_make)
                ),
                runtime_root=Path(temporary).resolve(),
                world_inputs=bundle,
            )
            result = workshop.run(self.wish)
            events = workshop._runtime().events(self.wish.product_id)
        self.assertEqual((result.status, result.job), ("waiting", "make"))
        self.assertEqual(observed, [bundle])
        accepted = next(
            item["payload"]
            for item in events
            if item.get("from_stage") == "invent" and item.get("to_stage") == "make"
        )
        self.assertEqual(accepted["world_inputs_sha256"], bundle.binding_sha256)

    def test_manager_playtest_service_returns_context_bound_raw_free_evidence(self):
        bundle = self.bundle()
        personalization = self.personalization()
        artifact_sha = "e" * 64
        evidence = WorldPlaytestEvidence(
            self.wish.product_id,
            canonical_sha(self.wish.to_dict()),
            artifact_sha,
            canonical_sha(personalization),
            bundle.binding_sha256,
            WorldProviderIdentity(
                "isolated-world-comparison-service", "2.1.0", "f" * 64
            ),
            (
                WorldEvidenceReference(
                    "customer-dog",
                    self.descriptor.receipt.record_sha256,
                    self.descriptor.receipt.content_sha256,
                    self.descriptor.receipt.content_bytes,
                    self.descriptor.receipt.consent_sha256,
                    self.descriptor.receipt.consent_bytes,
                    "image/png",
                    "authenticated-customer-supplied-scope-record",
                    "2026-08-26T01:02:03Z",
                    {"authorization_sha256": "9" * 64},
                ),
            ),
            (
                WorldEvidenceCase(
                    "customer-dog",
                    "round ears",
                    "compare both ear silhouettes with the admitted reference",
                    self.descriptor.receipt.content_sha256,
                    True,
                    True,
                    "deterministic-feature-comparison",
                ),
            ),
            {"attestation_sha256": "8" * 64},
        )
        service = FakePlaytestService(evidence)
        observed = prepare_world_playtest_evidence(
            self.wish,
            artifact_sha,
            personalization,
            bundle,
            service,
        )
        self.assertIs(observed, evidence)
        self.assertEqual(service.verify_calls, 1)
        serialized = json.dumps(evidence.to_dict(), sort_keys=True)
        self.assertNotIn("reference_bytes", serialized)
        self.assertNotIn("consent_bytes", serialized)

    def test_provider_digest_envelopes_reject_secrets_base64_and_oversize_values(self):
        reference_args = (
            "customer-dog",
            self.descriptor.receipt.record_sha256,
            self.descriptor.receipt.content_sha256,
            self.descriptor.receipt.content_bytes,
            self.descriptor.receipt.consent_sha256,
            self.descriptor.receipt.consent_bytes,
            "image/png",
            "authenticated-customer-supplied-scope-record",
            "2026-08-26T01:02:03Z",
        )
        for unsafe in (
            {"api_key": "secret-provider-token"},
            {"authorization_sha256": "cHJpdmF0ZS1pbWFnZS1ieXRlcw=="},
            {"authorization_sha256": "a" * 100_000},
            {
                "authorization_sha256": "9" * 64,
                "reference_base64": "cHJpdmF0ZS1pbWFnZS1ieXRlcw==",
            },
        ):
            with self.subTest(unsafe=tuple(unsafe)), self.assertRaises(ContractError):
                WorldEvidenceReference(*reference_args, unsafe)

        bundle = self.bundle()
        personalization = self.personalization()
        safe_reference = WorldEvidenceReference(
            *reference_args, {"authorization_sha256": "9" * 64}
        )
        safe_case = WorldEvidenceCase(
            "customer-dog",
            "round ears",
            "compare both ear silhouettes with the admitted reference",
            self.descriptor.receipt.content_sha256,
            True,
            True,
            "deterministic-feature-comparison",
        )
        base_args = (
            self.wish.product_id,
            canonical_sha(self.wish.to_dict()),
            "e" * 64,
            canonical_sha(personalization),
            bundle.binding_sha256,
            WorldProviderIdentity(
                "isolated-world-comparison-service", "2.1.0", "f" * 64
            ),
            (safe_reference,),
            (safe_case,),
        )
        for unsafe in (
            {"password": "secret-provider-token"},
            {"attestation_sha256": "cHJpdmF0ZS1jb25zZW50"},
            {"attestation_sha256": "b" * 100_000},
            {
                "attestation_sha256": "8" * 64,
                "signature_base64": "cHJpdmF0ZS1jb25zZW50",
            },
        ):
            with self.subTest(unsafe=tuple(unsafe)), self.assertRaises(ContractError):
                WorldPlaytestEvidence(*base_args, unsafe)

    def test_same_user_local_boundary_cannot_attest_world_playtest(self):
        bundle = self.bundle()
        personalization = self.personalization()
        reference = WorldEvidenceReference(
            "customer-dog",
            self.descriptor.receipt.record_sha256,
            self.descriptor.receipt.content_sha256,
            self.descriptor.receipt.content_bytes,
            self.descriptor.receipt.consent_sha256,
            self.descriptor.receipt.consent_bytes,
            "image/png",
            "authenticated-customer-supplied-scope-record",
            "2026-08-26T01:02:03Z",
            {"authorization_sha256": "9" * 64},
        )
        case = WorldEvidenceCase(
            "customer-dog",
            "round ears",
            "compare both ear silhouettes with the admitted reference",
            self.descriptor.receipt.content_sha256,
            True,
            True,
            "deterministic-feature-comparison",
        )
        with self.assertRaisesRegex(ContractError, "external isolated provider"):
            WorldPlaytestEvidence(
                self.wish.product_id,
                canonical_sha(self.wish.to_dict()),
                "e" * 64,
                canonical_sha(personalization),
                bundle.binding_sha256,
                WorldProviderIdentity(
                    "same-user-local-vault",
                    "1.0.0",
                    "f" * 64,
                    LOCAL_STORAGE_SECURITY_BOUNDARY,
                ),
                (reference,),
                (case,),
                {"attestation_sha256": "8" * 64},
            )


if __name__ == "__main__":
    unittest.main()
