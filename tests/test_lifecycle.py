import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.cad import (
    WORKSHOP_REQUIRED_CHECKS,
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from inventor_workshop.errors import TransitionError
from inventor_workshop.lifecycle import GatePolicy, Pipeline, PipelineSpec
from inventor_workshop.models import GateResult, PublicationReceipt
from inventor_workshop.store import InventorStore

ARTIFACT = "a" * 64
PACKET = "b" * 64
CONFIG = "c" * 64
EVIDENCE = "d" * 64
PROFILE = "e" * 64
SKILL = "f" * 64

PASSING_CAD_MEASUREMENTS = {
    "manifest": {"inventory_valid": True},
    "brep": {"valid_solids": 1, "invalid_solids": 0},
    "mesh-topology": {"watertight_parts": 1, "non_manifold_edges": 0},
    "dimensions": {"measured_parts": 1, "out_of_tolerance": 0},
    "interference": {"poses_tested": 1, "forbidden_intersections": 0},
    "bed-packing": {"beds_used": 1, "out_of_bounds_parts": 0},
    "slicer": {
        "profiles_checked": 1,
        "slicer_errors": 0,
        "support_material_grams": 0,
    },
    "form-review": {"views_reviewed": 3, "blockers": 0},
    "safety": {"hazards_found": 0, "review_scope": "intended tabletop use"},
    "physical-claims": {"claims_tested": 1, "claims_failed": 0},
}


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = InventorStore(Path(self.temp.name) / "state.sqlite")
        self.spec = PipelineSpec(
            initial_stage="built",
            stages=("built", "validated", "draft", "live"),
            edges={
                "built": {"validated"},
                "validated": {"draft"},
                "draft": {"live"},
                "live": set(),
            },
            required_gates={"validated": ("geometry",)},
            gate_policies={
                "geometry": GatePolicy("geometry", "validator", "1", CONFIG),
                "safety": GatePolicy("safety", "validator", "1", CONFIG),
            },
        )
        self.pipeline = Pipeline(self.spec)
        self.pipeline.register(self.store, "game", artifact_sha256=ARTIFACT)

    def receipt(self, status, design_id="d1"):
        return PublicationReceipt(
            packet_sha256=PACKET,
            artifact_sha256=ARTIFACT,
            design_id=design_id,
            slug="game",
            owner_id="owner",
            root_id="d1",
            current_history_id="h1",
            published_history_id="h1" if status == "public" else None,
            status=status,
            project_url="https://cdn.example/game/",
            observed_at="2026-08-23T00:00:00+00:00",
            listing_active=True if status == "public" else None,
            listing_price_cents=4000 if status == "public" else None,
            listing_currency="USD" if status == "public" else None,
            listing_sku="GAME-001" if status == "public" else None,
        )

    def record_draft(self):
        intent = self.store.prepare_publish(
            "game",
            PACKET,
            {
                "status": "draft",
                "_workshop_artifact_sha256": ARTIFACT,
                "_workshop_owner_id": "owner",
                "_workshop_api_origin": "https://panda-social-api.autonomous.ai",
            },
        )
        sending = self.store.begin_publish(intent["id"])
        self.store.mark_publish_succeeded(
            intent["id"], sending["effect_token"], self.receipt("draft")
        )
        return intent["id"]

    def record_live(self, intent_id):
        publishing = self.store.begin_live(
            intent_id,
            {
                "api_origin": "https://panda-social-api.autonomous.ai",
                "owner_id": "owner",
                "listing": {"price_cents": 4000},
            },
        )
        self.store.mark_publish_live(
            intent_id, publishing["effect_token"], self.receipt("public")
        )

    def test_gate_must_pass_and_match_exact_artifact(self):
        wrong = self.gate("geometry", True, "e" * 64)
        with self.assertRaises(TransitionError):
            self.pipeline.advance(self.store, "game", "validated", 0, gates=(wrong,))
        failed = self.gate("geometry", False, ARTIFACT)
        with self.assertRaises(TransitionError):
            self.pipeline.advance(self.store, "game", "validated", 0, gates=(failed,))
        passed = self.gate("geometry", True, ARTIFACT)
        product = self.pipeline.advance(self.store, "game", "validated", 0, gates=(passed,))
        self.assertEqual(product["stage"], "validated")

    def test_draft_and_live_need_remote_receipts(self):
        passed = self.gate("geometry", True, ARTIFACT)
        self.pipeline.advance(self.store, "game", "validated", 0, gates=(passed,))
        intent_id = self.record_draft()
        draft = self.pipeline.advance(
            self.store,
            "game",
            "draft",
            1,
            receipt=self.receipt("draft"),
            publication_packet_sha256=PACKET,
            publication_intent_id=intent_id,
            expected_owner_id="owner",
        )
        self.assertEqual(draft["stage"], "draft")
        with self.assertRaises(TransitionError):
            self.pipeline.advance(
                self.store,
                "game",
                "live",
                2,
                receipt=self.receipt("draft"),
                publication_packet_sha256=PACKET,
                publication_intent_id=intent_id,
            )
        self.record_live(intent_id)
        live = self.pipeline.advance(
            self.store,
            "game",
            "live",
            2,
            receipt=self.receipt("public"),
            publication_packet_sha256=PACKET,
            publication_intent_id=intent_id,
            expected_owner_id="owner",
        )
        self.assertEqual(live["stage"], "live")

    def test_live_must_match_the_recorded_draft_design(self):
        passed = self.gate("geometry", True, ARTIFACT)
        self.pipeline.advance(self.store, "game", "validated", 0, gates=(passed,))
        intent_id = self.record_draft()
        self.pipeline.advance(
            self.store,
            "game",
            "draft",
            1,
            receipt=self.receipt("draft"),
            publication_packet_sha256=PACKET,
            publication_intent_id=intent_id,
            expected_owner_id="owner",
        )
        self.record_live(intent_id)
        with self.assertRaises(TransitionError):
            self.pipeline.advance(
                self.store,
                "game",
                "live",
                2,
                receipt=self.receipt("public", design_id="other"),
                publication_packet_sha256=PACKET,
                publication_intent_id=intent_id,
                expected_owner_id="owner",
            )

    def test_supplied_optional_failure_is_retained_as_feedback(self):
        required = self.gate("geometry", True, ARTIFACT)
        safety = self.gate("safety", False, ARTIFACT)
        product = self.pipeline.advance(
            self.store, "game", "validated", 0, gates=(required, safety)
        )
        self.assertEqual(product["stage"], "validated")
        payload = self.store.events("game")[-1]["payload"]
        self.assertEqual(payload["required_inspection_ids"], ["geometry"])
        by_id = {
            result["inspection_id"]: result
            for result in payload["inspections"]
        }
        self.assertFalse(by_id["safety"]["passed"])

    def test_gate_policy_rejects_stale_and_future_evidence(self):
        self.spec = PipelineSpec(
            initial_stage="built",
            stages=("built", "validated"),
            edges={"built": {"validated"}, "validated": set()},
            required_gates={"validated": ("geometry",)},
            gate_policies={
                "geometry": GatePolicy(
                    "geometry", "validator", "1", CONFIG, max_age_seconds=60
                )
            },
        )
        pipeline = Pipeline(self.spec)
        other_store = InventorStore(Path(self.temp.name) / "freshness.sqlite")
        pipeline.register(other_store, "part", artifact_sha256=ARTIFACT)

        def observed(at):
            policy = self.spec.gate_policies["geometry"]
            return GateResult(
                "geometry",
                True,
                ARTIFACT,
                {"summary": "fixture"},
                policy.evaluator,
                policy.evaluator_version,
                policy.config_sha256,
                "evidence/geometry.json",
                EVIDENCE,
                at,
            )

        with mock.patch(
            "inventor_workshop.lifecycle.utc_now",
            return_value="2026-08-23T12:00:00+00:00",
        ):
            with self.assertRaises(TransitionError):
                pipeline.advance(
                    other_store,
                    "part",
                    "validated",
                    0,
                    gates=(observed("2026-08-23T11:58:59+00:00"),),
                )
            with self.assertRaises(TransitionError):
                pipeline.advance(
                    other_store,
                    "part",
                    "validated",
                    0,
                    gates=(observed("2026-08-23T12:05:01+00:00"),),
                )

    def gate(self, gate_id, passed, artifact):
        policy = self.spec.gate_policies[gate_id]
        return GateResult.create(
            gate_id,
            passed,
            artifact,
            {"summary": "deterministic fixture"},
            policy.evaluator,
            policy.evaluator_version,
            policy.config_sha256,
            "evidence/%s.json" % gate_id,
            EVIDENCE,
        )


class BoardGameLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = InventorStore(Path(self.temp.name) / "state.sqlite")
        self.pipeline = Pipeline(PipelineSpec.board_game())
        self.pipeline.register(self.store, "game", artifact_sha256=ARTIFACT)

    @staticmethod
    def cad_release(artifact):
        substrate_checks = {
            "deterministic": tuple(
                sorted(
                    name
                    for name in WORKSHOP_REQUIRED_CHECKS
                    if name not in {"form-review", "safety"}
                )
            ),
            "independent-review": ("form-review", "safety"),
            "physical": ("physical-claims",),
        }
        evidence_files = {
            "evidence/claim.json": EVIDENCE,
            **{
                "evidence/%s.json" % check: EVIDENCE
                for checks in substrate_checks.values()
                for check in checks
            },
        }
        manifest = CadProjectManifest(
            1,
            "game",
            artifact,
            {"name": "build123d", "version": "0.9.1"},
            {"cad": SKILL},
            (
                CadPart(
                    "token",
                    "Token",
                    1,
                    "parts/token.py",
                    "parts/token.step",
                    "parts/token.stl",
                    "PLA",
                    (0, 0, 0),
                ),
            ),
            (),
            (),
            (),
            {"process": "FDM", "profile_sha256": PROFILE},
            evidence_files,
            (
                PhysicalClaim(
                    "fit",
                    "calibrated fit works physically",
                    True,
                    "passed",
                    "evidence/claim.json",
                    EVIDENCE,
                ),
            ),
        )
        receipts = []
        requirements = []
        for substrate, checks in substrate_checks.items():
            validator = "%s-validator" % substrate
            receipts.append(
                VerificationReceipt.create(
                    artifact,
                    validator,
                    "1.0.0",
                    CONFIG,
                    substrate,
                    tuple(
                        VerificationCheck(
                            check,
                            "passed",
                            PASSING_CAD_MEASUREMENTS[check],
                            "evidence/%s.json" % check,
                            EVIDENCE,
                        )
                        for check in checks
                    ),
                )
            )
            requirements.append(
                ValidatorRequirement(
                    validator, "1.0.0", CONFIG, substrate, checks
                )
            )
        return CadReleaseBundle(manifest, tuple(receipts), tuple(requirements))

    def gates(self, artifact, *names, cad_release=None):
        results = []
        for name in names:
            policy = self.pipeline.spec.gate_policies[name]
            evidence = {"summary": "deterministic fixture"}
            evidence_sha = EVIDENCE
            if name == "cad":
                if cad_release is None:
                    raise AssertionError("cad gate fixture needs a release bundle")
                evidence = {"cad_release_sha256": cad_release.sha256}
            results.append(
                GateResult.create(
                    name,
                    True,
                    artifact,
                    evidence,
                    policy.evaluator,
                    policy.evaluator_version,
                    policy.config_sha256,
                    "evidence/%s.json" % name,
                    evidence_sha,
                )
            )
        return tuple(results)

    def test_parked_can_only_resume_the_stage_that_was_parked(self):
        parked = self.pipeline.advance(self.store, "game", "parked", 0)
        with self.assertRaises(TransitionError):
            self.pipeline.advance(self.store, "game", "draft", parked["revision"])
        resumed = self.pipeline.advance(self.store, "game", "idea", parked["revision"])
        self.assertEqual(resumed["stage"], "idea")

    def test_changed_review_artifact_requires_cumulative_evidence(self):
        other = "c" * 64
        self.pipeline.advance(self.store, "game", "researched", 0, ARTIFACT)
        self.pipeline.advance(self.store, "game", "rules", 1, ARTIFACT)
        self.pipeline.advance(
            self.store,
            "game",
            "simulated",
            2,
            ARTIFACT,
            self.gates(ARTIFACT, "rules-lint"),
        )
        self.pipeline.advance(self.store, "game", "built", 3, ARTIFACT)
        cad_policy = self.pipeline.spec.gate_policies["cad"]
        fake_cad = GateResult.create(
            "cad",
            True,
            ARTIFACT,
            {"cad_release_sha256": EVIDENCE},
            cad_policy.evaluator,
            cad_policy.evaluator_version,
            cad_policy.config_sha256,
            "evidence/cad.json",
            EVIDENCE,
        )
        with self.assertRaises(TransitionError):
            self.pipeline.advance(
                self.store,
                "game",
                "validated",
                4,
                ARTIFACT,
                self.gates(ARTIFACT, "rules-lint", "printability")
                + (fake_cad,),
            )
        cad_release = self.cad_release(ARTIFACT)
        validated_gates = self.gates(
            ARTIFACT,
            "rules-lint",
            "cad",
            "printability",
            cad_release=cad_release,
        )
        cad_gate = next(gate for gate in validated_gates if gate.gate_id == "cad")
        self.assertEqual(
            cad_gate.evidence["cad_release_sha256"], cad_release.sha256
        )
        self.assertEqual(cad_gate.evidence_sha256, EVIDENCE)
        self.assertNotEqual(cad_gate.evidence_sha256, cad_release.sha256)
        self.pipeline.advance(
            self.store,
            "game",
            "validated",
            4,
            ARTIFACT,
            validated_gates,
            cad_release=cad_release,
        )
        with self.assertRaises(TransitionError):
            self.pipeline.advance(
                self.store,
                "game",
                "reviewed",
                5,
                other,
                self.gates(other, "playtest", "novelty"),
            )


if __name__ == "__main__":
    unittest.main()
