import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.agent_invent import InventResearch, InventResearchSource
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import Made, PlaytestContext, Playtested, WaitingFor
from inventor_workshop.lane_playtest_providers import (
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
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest
from inventor_workshop.playtest_release import playtest_release_needs
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


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

    def context(
        self,
        lane,
        contract,
        *,
        suffix,
        distinct_roles=True,
        objective=None,
        science_sources=(),
        science_product_text=None,
    ):
        artifact = self.root / ("artifact-" + suffix)
        artifact.mkdir()
        if objective is None:
            objective = "Make this exact thing playful"
            if lane == "holdable-science":
                objective = "A holdable toy about %s" % contract[
                    "source_model"
                ]["phenomenon"]
        wish = Wish.create("wish-" + suffix, objective)
        _write_json(artifact / "wish.json", wish.to_dict())
        product = {
            "schema_version": 1,
            "kind": "workshop-step-first-parametric-prototype",
            "product_id": wish.product_id,
            "title": "Exact Lane Toy",
            "summary": "A source-bound provider fixture.",
            "description": "Exact fixture copy.",
            "instructions": "Use this exact source-bound fixture.",
            "lane": lane,
            "wish": wish.to_dict(),
        }
        science_binding = None
        invented_concept_sha256 = "c" * 64
        if lane == "holdable-science":
            interaction = contract.get("interaction", {})
            product["instructions"] = science_product_text or "%s %s" % (
                interaction.get("teaching_point", "missing teaching point"),
                interaction.get("misuse_boundary", "missing misuse boundary"),
            )
        if lane == "holdable-science" and science_sources:
            research_sources = tuple(
                InventResearchSource(
                    source.source_id,
                    source.title,
                    source.publisher,
                    source.url,
                    source.retrieved_at,
                    source.content.decode("utf-8"),
                    ("prior-art", "use-context", "science"),
                )
                for source in science_sources
            ) + (
                InventResearchSource(
                    "fixture-safety",
                    "Fixture toy safety",
                    "Fixture Safety Office",
                    "https://example.org/toy-safety",
                    "2026-08-25T00:00:00Z",
                    "Toy safety requires an explicit bounded hazard review.",
                    ("safety",),
                ),
            )
            research = InventResearch(
                json_sha256(wish.to_dict()),
                self.taste.sha256,
                ToyBlueprint.for_lane(lane).sha256,
                lane,
                "fixture-invent-research",
                "1.0.0",
                "f" * 64,
                research_sources,
            )
            research_document = {
                "schema_version": 1,
                "kind": "workshop.sealed-invent-science-research",
                "wish_sha256": json_sha256(wish.to_dict()),
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": ToyBlueprint.for_lane(lane).sha256,
                "invented_concept_sha256": invented_concept_sha256,
                "research_sha256": research.research_sha256,
                "content_scope": "Exact provider-observed fixture excerpts.",
                "research": research.to_dict(),
            }
            research_path = artifact / "playtest" / "invent-research.json"
            _write_json(research_path, research_document)
            science_binding = {
                "path": "playtest/invent-research.json",
                "file_sha256": hashlib.sha256(research_path.read_bytes()).hexdigest(),
                "research_sha256": research.research_sha256,
                "invented_concept_sha256": invented_concept_sha256,
            }
        _write_json(artifact / "product.json", product)
        _write_json(
            artifact / "playtest" / "mechanical.json",
            {
                "schema_version": 2,
                "kind": "workshop.locked-cad-mechanical-declaration",
                "digital_test_plan": {
                    "invent_lane_contract": contract,
                    "invent_lane_contract_sha256": json_sha256(contract),
                    "invent_science_research": science_binding,
                },
            },
        )
        _write_json(
            artifact / "cad" / "design.json",
            {
                "schema_version": 2,
                "kind": "workshop-step-first-parametric-design",
                "invented_concept_sha256": invented_concept_sha256,
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
            product,
        )
        return PlaytestContext(
            wish,
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
                "teaching_point": "Orbital resonance",
                "misuse_boundary": "The model diverges at high speed.",
            },
        }
        scale_excerpt = canonical_science_scale(contract["scale"])
        simplification_excerpt = (
            "Ignore air resistance. The model diverges at high speed."
        )
        public_bytes = (
            "Orbital resonance.\nA ratio of periods reveals repeated alignment.\n"
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
        context = self.context(
            "holdable-science",
            contract,
            suffix="science",
            science_sources=(source,),
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
                    "orbital-resonance",
                    ("nasa-orbits",),
                    "phenomenon",
                    "Orbital resonance",
                    "Orbital resonance",
                    "Orbital resonance",
                ),
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
                    ("Orbital resonance", "The model diverges at high speed."),
                    ("Orbital resonance", "The model diverges at high speed."),
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
        serialized_receipts = json.dumps(prepared.receipt_payloads, sort_keys=True)
        self.assertNotIn("comprehension", serialized_receipts)
        self.assertIn("deterministic-product-text-coverage", serialized_receipts)
        self.assert_core_accepts_capability(context, "science-test", prepared)

        substituted_source = PublicScienceSource(
            source.source_id,
            source.title,
            source.publisher,
            source.url,
            source.retrieved_at,
            source.content + b"\nprovider-authored substitute bytes",
        )
        substituted_verification = ScienceVerification(
            verification.identity,
            (substituted_source,),
            verification.accuracy_cases,
            verification.simplification_checks,
            verification.content_coverage_traces,
        )
        substituted_context = self.context(
            "holdable-science",
            contract,
            suffix="science-provider-substitution",
            science_sources=(source,),
        )
        with self.assertRaises(WaitingFor):
            WorkshopLanePlaytestProviders(
                science_provider=lambda unused_context, unused_model: (
                    substituted_verification
                )
            ).prepare(substituted_context, "science-test")

        dishonest_copy_context = self.context(
            "holdable-science",
            contract,
            suffix="science-dishonest-copy",
            science_sources=(source,),
            science_product_text="Turn the wheel and inspect the markers.",
        )
        with self.assertRaises(WaitingFor):
            providers.prepare(dishonest_copy_context, "science-test")

        unrelated_context = self.context(
            "holdable-science",
            contract,
            suffix="science-unrelated-wish",
            objective="A tactile model of ocean tides and lunar gravity",
            science_sources=(source,),
        )
        with self.assertRaises(WaitingFor) as caught:
            providers.prepare(unrelated_context, "science-test")
        self.assertEqual(caught.exception.needs[0].capability, "science-test")

        relevance_context = self.context(
            "holdable-science",
            contract,
            suffix="science-relevance-tamper",
            science_sources=(source,),
        )
        relevance_prepared = WorkshopLanePlaytestProviders(
            science_provider=lambda unused_context, unused_model: verification
        ).prepare(relevance_context, "science-test")

        def forge_relevance(root, proof):
            def mutate(document):
                document["payload"]["wish_source_relevance"][
                    "matched_terms"
                ] = ["fabricated-topic"]

            self.rewrite_receipt(root, proof, "science-sources", mutate)

        relevance_needs = self.release_needs(
            relevance_context,
            "science-test",
            relevance_prepared,
            tamper=forge_relevance,
        )
        self.assertIn("science-test", {item.capability for item in relevance_needs})

        scale_context = self.context(
            "holdable-science",
            contract,
            suffix="science-scale-mismatch",
            science_sources=(source,),
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
                "teaching_point": "orbital period",
                "misuse_boundary": "Additional bodies perturb the result.",
            },
        }
        source = PublicScienceSource(
            "public-orbit-source",
            "Orbit source",
            "Public Observatory",
            "https://example.org/orbits",
            "2026-08-25T00:00:00Z",
            (
                b"orbital period\nperiod depends on orbit size\n"
                + canonical_science_scale(contract["scale"]).encode("utf-8")
                + b"\nUse a two-body approximation. Additional bodies perturb the result."
            ),
        )
        context = self.context(
            "holdable-science",
            contract,
            suffix="science-tamper",
            science_sources=(source,),
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
                    "orbital-period-phenomenon",
                    ("public-orbit-source",),
                    "phenomenon",
                    "orbital period",
                    "orbital period",
                    "orbital period",
                ),
                ScienceAccuracyCase(
                    "orbit-period",
                    ("public-orbit-source",),
                    "model",
                    "period depends on orbit size",
                    "period depends on orbit size",
                    "period depends on orbit size",
                ),
                ScienceAccuracyCase(
                    "orbital-period-scale",
                    ("public-orbit-source",),
                    "scale",
                    canonical_science_scale(contract["scale"]),
                    canonical_science_scale(contract["scale"]),
                    canonical_science_scale(contract["scale"]),
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
            (
                ScienceComprehensionTrace(
                    1,
                    ("orbital period", "Additional bodies perturb the result."),
                    ("orbital period", "Additional bodies perturb the result."),
                ),
            ),
        )
        prepared = WorkshopLanePlaytestProviders(
            science_provider=lambda unused_context, unused_model: verification
        ).prepare(context, "science-test")

        def tamper(root, proof):
            def mutate(document):
                # Keep every cited excerpt and recompute every local hash.  The
                # common core must still reject bytes that differ from sealed
                # Invent research; excerpt self-consistency is insufficient.
                unrelated = source.content + b"\nforged provider appendix"
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
