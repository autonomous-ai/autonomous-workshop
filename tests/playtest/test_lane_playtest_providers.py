import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts.core import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.contracts import Made
from workshop.playtest.contracts import PlaytestContext, Playtested
from workshop.outcomes import WaitingFor
from workshop.playtest.providers import (
    ProviderIdentity,
    PublicScienceSource,
    ScienceAccuracyCase,
    ScienceComprehensionTrace,
    ScienceSimplificationCheck,
    ScienceVerification,
    WorkshopLanePlaytestProviders,
    WorldConsentRecord,
    WorldLikenessCase,
    WorldReferenceMaterial,
    WorldVerification,
    canonical_science_scale,
)
from workshop.wish import Wish
from workshop.playtest.evidence import PlaytestResult
from workshop.playtest.service import Playtest
from workshop.playtest.release import playtest_release_needs
from workshop.runtime.reward import json_sha256
from workshop.contributors.taste import load_taste
from workshop.product.blueprints import ToyBlueprint


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class LanePlaytestProvidersTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Provider Test\n"
            "description: Exact evidence for playful physical objects.\n"
            "---\n"
            "# Taste\n\nNo source-free claims.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, lane, contract, *, suffix, distinct_roles=True):
        artifact = self.root / ("artifact-" + suffix)
        artifact.mkdir()
        _write_json(
            artifact / "playtest" / "mechanical.json",
            {
                "schema_version": 2,
                "kind": "workshop.locked-cad-mechanical-declaration",
                "digital_test_plan": {
                    "invent_lane_contract": contract,
                    "invent_lane_contract_sha256": json_sha256(contract),
                },
            },
        )
        _write_json(
            artifact / "cad" / "design.json",
            {
                "schema_version": 2,
                "kind": "workshop-step-first-parametric-design",
                "action": {
                    "parts": [
                        {
                            "part_id": "night-piece",
                            "name": "Night pieces",
                            "purpose": "One player role",
                            "shape": "cylinder",
                            "size_mm": {"x": 20, "y": 20, "z": 6},
                        },
                        {
                            "part_id": "dawn-piece",
                            "name": "Dawn pieces",
                            "purpose": "The other player role",
                            "shape": "cylinder",
                            "size_mm": (
                                {"x": 18, "y": 18, "z": 8}
                                if distinct_roles
                                else {"x": 20, "y": 20, "z": 6}
                            ),
                        },
                    ]
                },
            },
        )
        for part_id in ("night_piece", "dawn_piece"):
            (artifact / "cad" / ("part_%s.step" % part_id)).write_bytes(
                ("ISO-10303-21;%s;END-ISO-10303-21;" % part_id).encode("ascii")
            )
            (artifact / "cad" / ("part_%s.stl" % part_id)).write_bytes(
                ("solid %s\nendsolid %s\n" % (part_id, part_id)).encode("ascii")
            )
        if lane == "classics-made-yours":
            _write_json(
                artifact / "playtest" / "classic-rules.json",
                {
                    "schema_version": 1,
                    "kind": "workshop.classic-rules-declaration",
                    "enabled": True,
                    "known_game": "checkers",
                    "rules_reference": "https://wcdf.net/rules/rules_of_checkers_english.pdf",
                    "rules_unchanged": True,
                },
            )
        made = Made.from_root(
            artifact,
            {
                "title": "Exact Lane Toy",
                "summary": "A source-bound provider fixture.",
                "lane": lane,
            },
        )
        return PlaytestContext(
            Wish.create("wish-" + suffix, "Make this exact thing playful"),
            self.taste,
            ToyBlueprint.for_lane(lane),
            1,
            made,
            self.root / ("evidence-" + suffix),
            2,
        )

    def release_needs(self, context, capability, prepared, *, tamper=None):
        evidence_root = context.workspace
        evidence_root.mkdir()
        proof = prepared.seal(evidence_root)
        if tamper is not None:
            tamper(evidence_root, proof)
        evidence = {
            "schema_version": 1,
            "kind": "workshop-ai-player-review",
            "evidence_class": "ai-simulation",
            "human_playtest": False,
            "artifact_sha256": context.made.artifact_sha256,
            "agent_roles": ["independent-player", "adversarial-player"],
            "release_proof": proof,
        }
        result_ref = "results/%s.json" % capability
        payload = (
            json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        path = evidence_root / result_ref
        path.parent.mkdir(parents=True)
        path.write_bytes(payload)
        result = PlaytestResult.create(
            capability,
            True,
            context.made.artifact_sha256,
            evidence,
            prepared.provider.name,
            prepared.provider.version,
            prepared.provider.config_sha256,
            result_ref,
            hashlib.sha256(payload).hexdigest(),
        )
        playtested = Playtested(
            Playtest(
                context.made.artifact_manifest,
                (result,),
                evidence_manifest=build_artifact_manifest(
                    evidence_root, created_at="content-addressed"
                ),
            )
        )
        return playtest_release_needs(
            context.blueprint, context.made, playtested, evidence_root
        )

    @staticmethod
    def rewrite_receipt(root, proof, role, mutate):
        source = next(item for item in proof["sources"] if item["role"] == role)
        path = root / source["path"]
        document = json.loads(path.read_text(encoding="utf-8"))
        mutate(document)
        _write_json(path, document)
        source["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def assert_core_accepts_capability(self, context, capability, prepared):
        needs = self.release_needs(context, capability, prepared)
        self.assertNotIn(capability, {item.capability for item in needs})

    def test_pinned_checkers_provider_emits_core_valid_release(self):
        contract = {
            "schema_version": 1,
            "lane": "classics-made-yours",
            "known_game": "checkers",
            "rules_preserved": True,
            "rules_preservation": {
                "canonical_ruleset": "WCDF Rules of Checkers (2012)",
                "preserved_invariants": ["Moves, captures, promotion, and wins stay unchanged."],
                "allowed_physical_changes": ["Piece form and material may change."],
            },
            "personalization_map": [
                {
                    "wish_detail": "night and dawn",
                    "physical_feature": "two distinct silhouettes",
                    "rules_effect": "none",
                }
            ],
        }
        context = self.context("classics-made-yours", contract, suffix="classic")
        prepared = WorkshopLanePlaytestProviders().prepare(
            context, "classic-rules-test"
        )
        self.assertTrue(prepared.passed)
        self.assertEqual(prepared.deterministic_check["passed"], True)
        self.assertEqual(prepared.measurements["seeded_games"], 32)
        self.assert_core_accepts_capability(
            context, "classic-rules-test", prepared
        )
        tampered_context = self.context(
            "classics-made-yours", contract, suffix="classic-forged-traces"
        )
        tampered = WorkshopLanePlaytestProviders().prepare(
            tampered_context, "classic-rules-test"
        )

        def forge_games(root, proof):
            self.rewrite_receipt(
                root,
                proof,
                "game-traces",
                lambda document: document["payload"].update({"games": []}),
            )

        needs = self.release_needs(
            tampered_context,
            "classic-rules-test",
            tampered,
            tamper=forge_games,
        )
        self.assertIn("classic-rules-test", {item.capability for item in needs})

    def test_classic_role_gate_uses_exact_geometry_not_role_names(self):
        contract = {
            "schema_version": 1,
            "lane": "classics-made-yours",
            "known_game": "checkers",
            "rules_preserved": True,
            "rules_preservation": {
                "canonical_ruleset": "WCDF Rules of Checkers (2012)",
                "preserved_invariants": ["Rules stay unchanged."],
                "allowed_physical_changes": ["Physical form may change."],
            },
            "personalization_map": [
                {
                    "wish_detail": "two named sides",
                    "physical_feature": "different prose labels only",
                    "rules_effect": "none",
                }
            ],
        }
        context = self.context(
            "classics-made-yours",
            contract,
            suffix="classic-same-geometry",
            distinct_roles=False,
        )
        prepared = WorkshopLanePlaytestProviders().prepare(
            context, "classic-rules-test"
        )
        self.assertFalse(prepared.passed)
        self.assertEqual(prepared.measurements["role_legibility_failures"], 1)
        self.assertEqual(
            prepared.receipt_payloads["game-traces"]["distinct_geometry_signatures"],
            1,
        )
        context.workspace.mkdir()
        with self.assertRaisesRegex(ContractError, "failed lane verification"):
            prepared.seal(context.workspace)

    def test_science_provider_binds_sources_simplifications_and_traces(self):
        simplification = {
            "simplification": "Ignore air resistance.",
            "reason": "Keep the hand interaction legible.",
            "disclosed_limit": "The model diverges at high speed.",
        }
        contract = {
            "schema_version": 1,
            "lane": "holdable-science",
            "source_model": {
                "phenomenon": "Orbital resonance",
                "model": "A ratio of periods reveals repeated alignment.",
                "source_ids": ["nasa-orbits"],
            },
            "simplifications": [simplification],
            "scale": {
                "real_quantity": "orbital period",
                "model_quantity": "gear turns",
                "scale_ratio": 1000,
                "units": "days per turn",
            },
            "interaction": {
                "user_action": "Turn the wheel.",
                "observable_response": "Markers realign.",
                "teaching_point": "Ratios create repeating alignment.",
                "misuse_boundary": "Not an ephemeris.",
            },
        }
        context = self.context("holdable-science", contract, suffix="science")
        scale_excerpt = canonical_science_scale(contract["scale"])
        simplification_excerpt = (
            "Ignore air resistance. The model diverges at high speed."
        )
        public_bytes = (
            "A ratio of periods reveals repeated alignment.\n"
            + scale_excerpt
            + "\n"
            + simplification_excerpt
        ).encode("utf-8")
        source = PublicScienceSource(
            "nasa-orbits",
            "Orbital Periods",
            "NASA",
            "https://science.nasa.gov/orbits/",
            "2026-08-25T00:00:00Z",
            public_bytes,
        )
        verification = ScienceVerification(
            ProviderIdentity(
                "workshop-science-source-checker",
                "1.0.0",
                "a" * 64,
                "source-bound-comparison",
            ),
            (source,),
            (
                ScienceAccuracyCase(
                    "period-ratio",
                    ("nasa-orbits",),
                    "model",
                    "A ratio of periods reveals repeated alignment.",
                    "A ratio of periods reveals repeated alignment.",
                    "A ratio of periods reveals repeated alignment.",
                ),
                ScienceAccuracyCase(
                    "scale-ratio",
                    ("nasa-orbits",),
                    "scale",
                    scale_excerpt,
                    scale_excerpt,
                    scale_excerpt,
                ),
            ),
            (
                ScienceSimplificationCheck(
                    json_sha256(simplification),
                    ("nasa-orbits",),
                    True,
                    True,
                    simplification_excerpt,
                ),
            ),
            (
                ScienceComprehensionTrace(
                    7,
                    ("ratio", "repeating alignment"),
                    ("ratio", "repeating alignment", "period"),
                ),
            ),
        )
        providers = WorkshopLanePlaytestProviders(
            science_provider=lambda unused_context, unused_model: verification
        )
        prepared = providers.prepare(context, "science-test")
        self.assertTrue(prepared.passed)
        source_payload = prepared.receipt_payloads["science-sources"]["sources"][0]
        self.assertEqual(source_payload["content_encoding"], "base64")
        self.assertEqual(
            base64.b64decode(source_payload["content_base64"]), source.content
        )
        self.assertEqual(
            hashlib.sha256(base64.b64decode(source_payload["content_base64"])).hexdigest(),
            source_payload["content_sha256"],
        )
        self.assert_core_accepts_capability(context, "science-test", prepared)
        scale_context = self.context(
            "holdable-science", contract, suffix="science-scale-mismatch"
        )
        scale_prepared = WorkshopLanePlaytestProviders(
            science_provider=lambda unused_context, unused_model: verification
        ).prepare(scale_context, "science-test")

        def forge_scale(root, proof):
            def mutate(document):
                case = next(
                    item
                    for item in document["payload"]["accuracy_cases"]
                    if item["product_field"] == "scale"
                )
                case["observed"] = '{"scale_ratio":999}'

            self.rewrite_receipt(root, proof, "science-sources", mutate)

        scale_needs = self.release_needs(
            scale_context,
            "science-test",
            scale_prepared,
            tamper=forge_scale,
        )
        self.assertIn("science-test", {item.capability for item in scale_needs})

    def test_core_rejects_mutated_embedded_science_source_receipt(self):
        simplification = {
            "simplification": "Use a two-body approximation.",
            "reason": "Keep one relationship visible.",
            "disclosed_limit": "Additional bodies perturb the result.",
        }
        contract = {
            "schema_version": 1,
            "lane": "holdable-science",
            "source_model": {
                "phenomenon": "orbital period",
                "model": "period depends on orbit size",
                "source_ids": ["public-orbit-source"],
            },
            "simplifications": [simplification],
            "scale": {
                "real_quantity": "period",
                "model_quantity": "turns",
                "scale_ratio": 1,
                "units": "turns",
            },
            "interaction": {
                "user_action": "turn",
                "observable_response": "align",
                "teaching_point": "period",
                "misuse_boundary": "not predictive",
            },
        }
        context = self.context("holdable-science", contract, suffix="science-tamper")
        source = PublicScienceSource(
            "public-orbit-source",
            "Orbit source",
            "Public Observatory",
            "https://example.org/orbits",
            "2026-08-25T00:00:00Z",
            (
                b"period depends on orbit size\n"
                b"Use a two-body approximation. Additional bodies perturb the result."
            ),
        )
        verification = ScienceVerification(
            ProviderIdentity(
                "workshop-source-checker",
                "1.0.0",
                "e" * 64,
                "source-bound-comparison",
            ),
            (source,),
            (
                ScienceAccuracyCase(
                    "orbit-period",
                    ("public-orbit-source",),
                    "model",
                    "period depends on orbit size",
                    "period depends on orbit size",
                    "period depends on orbit size",
                ),
            ),
            (
                ScienceSimplificationCheck(
                    json_sha256(simplification),
                    ("public-orbit-source",),
                    True,
                    True,
                    "Use a two-body approximation. Additional bodies perturb the result.",
                ),
            ),
            (ScienceComprehensionTrace(1, ("period",), ("period",)),),
        )
        prepared = WorkshopLanePlaytestProviders(
            science_provider=lambda unused_context, unused_model: verification
        ).prepare(context, "science-test")

        def tamper(root, proof):
            def mutate(document):
                unrelated = b"unrelated but internally hash-consistent public bytes"
                source_record = document["payload"]["sources"][0]
                source_record["content_base64"] = base64.b64encode(unrelated).decode(
                    "ascii"
                )
                source_record["content_sha256"] = hashlib.sha256(unrelated).hexdigest()
                source_record["content_bytes"] = len(unrelated)

            self.rewrite_receipt(root, proof, "science-sources", mutate)

        needs = self.release_needs(
            context, "science-test", prepared, tamper=tamper
        )
        self.assertIn("science-test", {item.capability for item in needs})

    def test_world_provider_keeps_private_bytes_out_of_evidence(self):
        contract = {
            "schema_version": 1,
            "lane": "little-worlds",
            "consented_references": [
                {
                    "reference_id": "customer-dog",
                    "subject": "the customer's dog",
                    "consent_or_rights_basis": "customer upload authorization",
                    "allowed_features": ["proud neck posture"],
                    "excluded_features": ["home address"],
                }
            ],
            "feature_to_form_map": [
                {
                    "reference_id": "customer-dog",
                    "reference_feature": "proud neck posture",
                    "physical_form": "raised miniature silhouette",
                    "recognition_test": "posture remains recognizable in profile",
                }
            ],
        }
        context = self.context("little-worlds", contract, suffix="world")
        private_reference = b"PRIVATE-REFERENCE-BYTES-MUST-NOT-BE-WRITTEN"
        private_consent = b"PRIVATE-SIGNED-CONSENT-MUST-NOT-BE-WRITTEN"
        material = WorldReferenceMaterial(
            "customer-dog", "image/jpeg", private_reference
        )
        verification = WorldVerification(
            ProviderIdentity(
                "workshop-consent-vault-and-vision",
                "1.0.0",
                "b" * 64,
                "private-reference-feature-comparison",
            ),
            (
                WorldConsentRecord(
                    "customer-dog",
                    "the customer's dog",
                    "customer upload authorization",
                    ("proud neck posture",),
                    ("home address",),
                    "signed-order-authorization",
                    "2026-08-25T00:00:00Z",
                    private_consent,
                ),
            ),
            (material,),
            (
                WorldLikenessCase(
                    "customer-dog",
                    "proud neck posture",
                    "posture remains recognizable in profile",
                    material.sha256,
                    True,
                    True,
                    "vision-feature-comparison",
                ),
            ),
        )
        providers = WorkshopLanePlaytestProviders(
            world_provider=lambda unused_context, unused_map: verification
        )
        prepared = providers.prepare(context, "world-test")
        self.assert_core_accepts_capability(context, "world-test", prepared)
        sealed = b"".join(
            path.read_bytes()
            for path in context.workspace.rglob("*")
            if path.is_file()
        )
        self.assertNotIn(private_reference, sealed)
        self.assertNotIn(private_consent, sealed)
        self.assertIn(material.sha256.encode("ascii"), sealed)
        reference_receipt = json.loads(
            (
                context.workspace
                / "release"
                / "world-test"
                / "reference-material.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            reference_receipt["payload"]["attestation"]["name"],
            "workshop-consent-vault-and-vision",
        )
        self.assertIn(
            "not public-replayable",
            reference_receipt["payload"]["attestation_scope"],
        )
        tampered_context = self.context(
            "little-worlds", contract, suffix="world-forged-likeness"
        )
        tampered = WorkshopLanePlaytestProviders(
            world_provider=lambda unused_context, unused_map: verification
        ).prepare(tampered_context, "world-test")

        def forge_likeness(root, proof):
            def mutate(document):
                document["payload"]["cases"][0]["recognized"] = False

            self.rewrite_receipt(root, proof, "likeness-traces", mutate)

        needs = self.release_needs(
            tampered_context,
            "world-test",
            tampered,
            tamper=forge_likeness,
        )
        self.assertIn("world-test", {item.capability for item in needs})

    def test_missing_independent_inputs_are_typed_workshop_needs(self):
        science_contract = {
            "schema_version": 1,
            "lane": "holdable-science",
            "source_model": {
                "phenomenon": "waves",
                "model": "a source model",
                "source_ids": ["public-source"],
            },
            "simplifications": [
                {
                    "simplification": "one dimension",
                    "reason": "clarity",
                    "disclosed_limit": "not a full field",
                }
            ],
            "scale": {
                "real_quantity": "wavelength",
                "model_quantity": "spacing",
                "scale_ratio": 1,
                "units": "mm",
            },
            "interaction": {
                "user_action": "move",
                "observable_response": "wave",
                "teaching_point": "periodicity",
                "misuse_boundary": "not predictive",
            },
        }
        context = self.context(
            "holdable-science", science_contract, suffix="science-missing"
        )
        with self.assertRaises(WaitingFor) as caught:
            WorkshopLanePlaytestProviders().prepare(context, "science-test")
        self.assertEqual(caught.exception.needs[0].job, "playtest")
        self.assertEqual(caught.exception.needs[0].capability, "science-test")
        self.assertIn("Workshop-managed", caught.exception.needs[0].instructions)

        world_contract = {
            "schema_version": 1,
            "lane": "little-worlds",
            "consented_references": [
                {
                    "reference_id": "private-ref",
                    "subject": "private subject",
                    "consent_or_rights_basis": "pending",
                    "allowed_features": ["shape"],
                    "excluded_features": ["address"],
                }
            ],
            "feature_to_form_map": [
                {
                    "reference_id": "private-ref",
                    "reference_feature": "shape",
                    "physical_form": "silhouette",
                    "recognition_test": "recognizable",
                }
            ],
        }
        world = self.context("little-worlds", world_contract, suffix="world-missing")
        with self.assertRaises(WaitingFor) as caught:
            WorkshopLanePlaytestProviders().prepare(world, "world-test")
        self.assertEqual(caught.exception.needs[0].capability, "world-test")
        self.assertIn("Never", caught.exception.needs[0].instructions)

    def test_language_model_opinion_cannot_be_provider_identity(self):
        with self.assertRaisesRegex(Exception, "opinion alone"):
            ProviderIdentity(
                "terra-panel", "1.0.0", "c" * 64, "language-model-opinion"
            )


if __name__ == "__main__":
    unittest.main()
