import base64
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_invent import (
    InventResearch,
    InventResearchSource,
    _science_relevance_record,
)
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import (
    CustomerReview,
    Delivered,
    Feedback,
    Invented,
    Made,
    Need,
    Playtested,
    WaitingFor,
)
from inventor_workshop.invented_game import (
    GAME_ANALYSIS_CRITERIA,
    GAME_CONTRACT_PATH,
    GAME_RULES_PATH,
    GAME_SIMULATOR_ID,
    GAME_SIMULATOR_PATH,
    GAME_SIMULATOR_SOURCE,
    GAME_SIMULATOR_VERSION,
    canonical_json_bytes,
    game_simulation_plan,
    game_trace_analysis,
    game_rules_document,
    simulate_game_protocol,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.runtime import Runtime
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.reviews import ReviewAuthentication, review_sha256
from inventor_workshop.workshop import Workshop, WorkshopTools
from inventor_workshop.world_reference_vault import (
    CONSENT_CLAIM_BOUNDARY,
    WorldReferenceScope,
)
from inventor_workshop.world_service import (
    WorldEvidenceCase,
    WorldEvidenceReference,
    WorldInventInputs,
    WorldInventReference,
    WorldPlaytestEvidence,
    WorldProviderIdentity,
)
from tests.delivery_support import fixture_delivery_evidence


CONFIG_SHA256 = "c" * 64


def fixture_game_contract():
    return {
        "schema_version": 2,
        "lane": "invented-games",
        "game_protocol": {
            "schema_version": 1,
            "protocol": "workshop.resource-game.v1",
            "players": 2,
            "resources": [
                {"resource_id": "beats", "label": "beat tokens", "initial": 7}
            ],
            "actions": [
                {
                    "action_id": "take-one",
                    "label": "Take one beat",
                    "removals": [{"resource_id": "beats", "count": 1}],
                    "points": 0,
                },
                {
                    "action_id": "take-two",
                    "label": "Take two beats",
                    "removals": [{"resource_id": "beats", "count": 2}],
                    "points": 0,
                },
                {
                    "action_id": "take-three",
                    "label": "Take three beats",
                    "removals": [{"resource_id": "beats", "count": 3}],
                    "points": 0,
                },
            ],
            "ending": {
                "condition": "all-resources-empty",
                "winner": "next-actor",
                "score_tie_break": "last-actor",
            },
        },
        "simulation_gate": {
            "minimum_complete_games": 1_000,
            "fixed_seed_strategy": "artifact-sha256-plus-index",
            "player_policies": [
                "optimizing",
                "social",
                "exploratory",
                "adversarial",
            ],
        },
    }


def fixture_game_release_documents(
    artifact_sha256, contract, product_inventory
):
    """Build only the exact core-replayable game proof fixture."""

    plan = game_simulation_plan(artifact_sha256, 1_000)
    games = []
    for request in plan["games"]:
        raw = simulate_game_protocol(contract["game_protocol"], request)
        games.append(
            {
                **raw,
                "outcome": json.dumps(
                    raw["outcome"], sort_keys=True, separators=(",", ":")
                ),
            }
        )
    recomputed = game_trace_analysis(
        contract["game_protocol"], games, requested_games=1_000
    )
    protocol_sha256 = json_sha256(contract["game_protocol"])
    provenance = {
        "simulator": GAME_SIMULATOR_ID,
        "simulator_version": GAME_SIMULATOR_VERSION,
        "source_path": GAME_SIMULATOR_PATH,
        "source_sha256": product_inventory[GAME_SIMULATOR_PATH],
        "contract_path": GAME_CONTRACT_PATH,
        "contract_sha256": product_inventory[GAME_CONTRACT_PATH],
        "rules_path": GAME_RULES_PATH,
        "rules_sha256": product_inventory[GAME_RULES_PATH],
        "game_protocol_sha256": protocol_sha256,
    }
    trace_document = {
        "schema_version": 1,
        "kind": "workshop-seeded-game-traces",
        "artifact_sha256": artifact_sha256,
        "plan_sha256": json_sha256(plan),
        "provenance": provenance,
        "games": games,
    }
    analysis_document = {
        "schema_version": 1,
        "kind": "workshop-seeded-game-release-analysis",
        "artifact_sha256": artifact_sha256,
        "protocol_binding": {
            "contract_path": GAME_CONTRACT_PATH,
            "contract_sha256": product_inventory[GAME_CONTRACT_PATH],
            "rules_path": GAME_RULES_PATH,
            "rules_sha256": product_inventory[GAME_RULES_PATH],
            "game_protocol_sha256": protocol_sha256,
        },
        "criteria": dict(GAME_ANALYSIS_CRITERIA),
        "seat_wins": recomputed["seat_wins"],
        "style_wins": recomputed["style_wins"],
        "forced_turns": recomputed["forced_turns"],
        "measurements": recomputed["measurements"],
    }
    return recomputed["measurements"], trace_document, analysis_document


class ToyWorkshopTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Small playthings with one surprising interaction.\n"
            "---\n"
            "# Taste\n\n"
            "Small playthings with one surprising interaction.\n",
            encoding="utf-8",
        )
        self.runtime = self.root / "runtime"

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def invent_job(context):
        wish_sha256 = hashlib.sha256(
            json.dumps(
                context.wish.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        concept = {
            "title": "Rhythm Top concept",
            "summary": "A pocket top whose changing rhythm invites another spin.",
        }
        if context.blueprint.lane == "invented-games":
            concept["lane_contract"] = fixture_game_contract()
        return Invented(
            wish_sha256=wish_sha256,
            taste_sha256=context.taste.sha256,
            lane=context.blueprint.lane,
            concept=concept,
            score=92,
            target_score=90,
        )

    @classmethod
    def world_invent_job(cls, context):
        """Return the exact Manager-admitted little-world contract."""

        invented = cls.invent_job(context)
        if not isinstance(context.world_inputs, WorldInventInputs):
            return invented
        return Invented(
            invented.wish_sha256,
            invented.taste_sha256,
            invented.lane,
            {
                **dict(invented.concept),
                "lane_contract": {
                    "schema_version": 1,
                    "lane": "little-worlds",
                    "consented_references": (
                        context.world_inputs.expected_consent_contracts()
                    ),
                    "feature_to_form_map": [
                        {
                            "reference_id": "fixture-reference",
                            "reference_feature": "fixture feature",
                            "physical_form": "fixture silhouette",
                            "recognition_test": "feature remains recognizable",
                        }
                    ],
                },
            },
            invented.score,
            invented.target_score,
        )

    @staticmethod
    def world_inputs(wish):
        scope = WorldReferenceScope(
            "fixture-reference",
            "customer-owned-subject",
            "fixture subject",
            "signed fixture authorization",
            ("fixture feature",),
            ("private address",),
            "customer-order-42",
            "customer-supplied-attestation-record",
        )
        wish_sha256 = json_sha256(wish.to_dict())
        return WorldInventInputs(
            wish.product_id,
            wish_sha256,
            WorldProviderIdentity(
                "isolated-world-reference-service", "1.0.0", "1" * 64
            ),
            (
                WorldInventReference(
                    scope,
                    wish.product_id,
                    wish_sha256,
                    "2" * 64,
                    "3" * 64,
                    128,
                    "4" * 64,
                    64,
                    "image/jpeg",
                    "2" * 64,
                    "5" * 64,
                ),
            ),
        )

    @staticmethod
    def world_evidence(wish, artifact_sha256, inputs, *, attestation="8"):
        personalization = {
            "consented_references": inputs.expected_consent_contracts(),
            "feature_to_form_map": [
                {
                    "reference_id": "fixture-reference",
                    "reference_feature": "fixture feature",
                    "physical_form": "fixture silhouette",
                    "recognition_test": "feature remains recognizable",
                }
            ],
        }
        return WorldPlaytestEvidence(
            wish.product_id,
            json_sha256(wish.to_dict()),
            artifact_sha256,
            json_sha256(personalization),
            inputs.binding_sha256,
            WorldProviderIdentity(
                "isolated-world-comparison-service", "2.0.0", "6" * 64
            ),
            (
                WorldEvidenceReference(
                    "fixture-reference",
                    "2" * 64,
                    "3" * 64,
                    128,
                    "4" * 64,
                    64,
                    "image/jpeg",
                    "authenticated-customer-supplied-scope-record",
                    "2026-08-26T01:02:03Z",
                    {"authorization_sha256": "7" * 64},
                ),
            ),
            (
                WorldEvidenceCase(
                    "fixture-reference",
                    "fixture feature",
                    "feature remains recognizable",
                    "3" * 64,
                    True,
                    True,
                    "deterministic-feature-comparison",
                ),
            ),
            {"attestation_sha256": attestation * 64},
        )

    @staticmethod
    def make_job(context):
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        (artifact / "toy.step").write_text(
            "round %d\n" % context.round, encoding="utf-8"
        )
        (artifact / "instructions.md").write_text(
            "Spin it and discover the hidden rhythm.\n", encoding="utf-8"
        )
        (artifact / "part_toy.stl").write_text(
            "solid toy\nendsolid toy\n", encoding="utf-8"
        )
        (artifact / "wish.json").write_text(
            json.dumps(context.wish.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (artifact / "edition-rules.json").write_text(
            '{"known_game":"fixture classic","rules_reference":"https://example.org/fixture-rules","rules":["take one legal turn"]}\n',
            encoding="utf-8",
        )
        science_source_model = {
            "phenomenon": "fixture rhythm",
            "model": "one turn advances one beat",
            "source_ids": ["fixture-source"],
        }
        science_simplifications = [
            {
                "simplification": "ignore drag",
                "reason": "bounded fixture",
                "disclosed_limit": "not a physical prediction",
            },
            {
                "simplification": "one beat per turn",
                "reason": "legible interaction",
                "disclosed_limit": "not continuous time",
            },
        ]
        science_scale = {
            "real_quantity": "one beat",
            "model_quantity": "one turn",
            "scale_ratio": 1,
            "units": "beats per turn",
        }
        science_interaction = {
            "user_action": "Spin the top.",
            "observable_response": "Watch one turn advance one beat.",
            "teaching_point": "fixture rhythm",
            "misuse_boundary": "not a physical prediction",
        }
        canonical_scale = json.dumps(
            science_scale, sort_keys=True, separators=(",", ":")
        )
        science_source_bytes = (
            "fixture rhythm\n"
            "one turn advances one beat\n"
            + canonical_scale
            + "\nignore drag; not a physical prediction\n"
            "one beat per turn; not continuous time"
        ).encode("utf-8")
        science_binding = None
        if context.blueprint.lane == "holdable-science":
            research = InventResearch(
                hashlib.sha256(
                    json.dumps(
                        context.wish.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest(),
                context.taste.sha256,
                context.blueprint.sha256,
                context.blueprint.lane,
                "fixture-invent-science",
                "1.0.0",
                "7" * 64,
                (
                    InventResearchSource(
                        "fixture-source",
                        "Fixture science source",
                        "Fixture Observatory",
                        "https://example.org/fixture-science",
                        "2026-08-25T00:00:00Z",
                        science_source_bytes.decode("utf-8"),
                        ("prior-art", "use-context", "science"),
                    ),
                    InventResearchSource(
                        "fixture-safety",
                        "Fixture toy safety",
                        "Fixture Safety Office",
                        "https://example.org/fixture-safety",
                        "2026-08-25T00:00:00Z",
                        "Toy safety requires an explicit bounded hazard review.",
                        ("safety",),
                    ),
                ),
            )
            research_document = {
                "schema_version": 1,
                "kind": "workshop.sealed-invent-science-research",
                "wish_sha256": research.wish_sha256,
                "taste_sha256": research.taste_sha256,
                "blueprint_sha256": research.blueprint_sha256,
                "invented_concept_sha256": context.invented.concept_sha256,
                "research_sha256": research.research_sha256,
                "content_scope": "Exact provider-observed fixture excerpts.",
                "research": research.to_dict(),
            }
            research_path = artifact / "playtest" / "invent-research.json"
            research_path.parent.mkdir(parents=True, exist_ok=True)
            research_path.write_text(
                json.dumps(research_document, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            science_binding = {
                "path": "playtest/invent-research.json",
                "file_sha256": hashlib.sha256(research_path.read_bytes()).hexdigest(),
                "research_sha256": research.research_sha256,
                "invented_concept_sha256": context.invented.concept_sha256,
            }
        (artifact / "source-model.json").write_text(
            json.dumps(
                {
                    "source_model": science_source_model,
                    "simplifications": science_simplifications,
                    "scale": science_scale,
                    "interaction": science_interaction,
                    "invent_science_research": science_binding,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (artifact / "personalization-map.json").write_text(
            json.dumps(
                {
                    "consented_references": [
                        {
                            "reference_id": "fixture-reference",
                            "subject": "fixture subject",
                            "consent_or_rights_basis": "signed fixture authorization",
                            "allowed_features": ["fixture feature"],
                            "excluded_features": ["private address"],
                        }
                    ],
                    "feature_to_form_map": [
                        {
                            "reference_id": "fixture-reference",
                            "reference_feature": "fixture feature",
                            "physical_form": "fixture silhouette",
                            "recognition_test": "feature remains recognizable",
                        }
                    ],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (artifact / "role_a.step").write_text("STEP role a\n", encoding="utf-8")
        (artifact / "role_a.stl").write_text("solid role_a\nendsolid role_a\n", encoding="utf-8")
        (artifact / "role_b.step").write_text("STEP role b\n", encoding="utf-8")
        (artifact / "role_b.stl").write_text("solid role_b\nendsolid role_b\n", encoding="utf-8")
        (artifact / "game-rules.json").write_text(
            '{"end":"finite","legal_actions":["play"]}\n', encoding="utf-8"
        )
        (artifact / "simulator.py").write_text(
            "def play(seed):\n    return {'completed': True, 'seed': seed}\n",
            encoding="utf-8",
        )
        if context.blueprint.lane == "invented-games":
            contract = context.invented.concept["lane_contract"]
            contract_path = artifact / GAME_CONTRACT_PATH
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_bytes(canonical_json_bytes(contract))
            rules = game_rules_document(
                lane_contract=contract,
                physical_binding={
                    "enabled": True,
                    "resource_part_ids": [
                        {
                            "resource_id": "beats",
                            "part_ids": ["beat-%d" % index for index in range(1, 8)],
                        }
                    ],
                },
                title="Rhythm Top",
                theme="A pocket rhythm game.",
            )
            rules_path = artifact / GAME_RULES_PATH
            rules_path.write_text(
                json.dumps(rules, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            simulator_path = artifact / GAME_SIMULATOR_PATH
            simulator_path.write_text(
                GAME_SIMULATOR_SOURCE,
                encoding="utf-8",
            )
        product = {
            "schema_version": 1,
            "kind": "workshop-fixture-product",
            "product_id": context.wish.product_id,
            "title": "Rhythm Top",
            "summary": "A pocket top that reveals a changing beat.",
            "description": "A source-bound fixture rhythm toy.",
            "lane": context.blueprint.lane,
            "wish": context.wish.to_dict(),
            "instructions": (
                "fixture rhythm; not a physical prediction"
                if context.blueprint.lane == "holdable-science"
                else "Spin, listen, and try to repeat the rhythm."
            ),
            "components": ["one spinning top"],
            "limitations": ["Fixture evidence is not a physical print."],
        }
        (artifact / "product.json").write_text(
            json.dumps(product, sort_keys=True) + "\n", encoding="utf-8"
        )
        return Made.from_root(artifact, product)

    @staticmethod
    def _playtest(
        context,
        *,
        passed,
        valid_invented=False,
        ai_simulation=True,
        valid_proofs=True,
        placeholder_receipts=(),
        tampered_receipts=(),
        unsealed_print_outputs=False,
        legacy_world_terms=False,
    ):
        context.workspace.mkdir(parents=True)
        product_inventory = {
            entry.path: entry.sha256
            for entry in context.made.artifact_manifest.entries
        }

        def write_json(name, value):
            path = context.workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return path.name, hashlib.sha256(path.read_bytes()).hexdigest()

        def write_bytes(name, value):
            path = context.workspace / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
            return name, hashlib.sha256(value).hexdigest()

        def source(role, scope, path, digest):
            return {"role": role, "scope": scope, "path": path, "sha256": digest}

        def write_receipt(
            capability,
            proof_class,
            role,
            measurements,
            source_sha256,
            payload,
        ):
            document = {
                "schema_version": 1,
                "kind": "workshop.capability-release-receipt",
                "artifact_sha256": context.made.artifact_sha256,
                "capability": capability,
                "proof_class": proof_class,
                "role": role,
                "source_sha256": source_sha256,
                "measurements": measurements,
                "payload": payload,
            }
            if capability in placeholder_receipts:
                document = {"computed": True}
            elif capability in tampered_receipts:
                document["artifact_sha256"] = "f" * 64
            return write_json(role + ".json", document)

        def release_proof(capability):
            artifact_sha256 = context.made.artifact_sha256
            if capability == "mechanical-test":
                measurements = {
                    "brep_valid": True,
                    "interference_cases": 2,
                    "fit_cases": 2,
                    "assembly_paths_tested": 1,
                    "motion_cases": 1,
                    "load_cases": 1,
                    "failure_modes_tested": 2,
                    "forbidden_intersections": 0,
                    "fit_failures": 0,
                    "assembly_failures": 0,
                    "motion_failures": 0,
                    "load_failures": 0,
                    "unresolved_critical_failures": 0,
                }
                receipt, receipt_sha256 = write_receipt(
                    capability,
                    "computed-mechanical-proof",
                    "mechanical-receipt",
                    measurements,
                    {"product:toy.step": product_inventory["toy.step"]},
                    {
                        "method": "fixture-exact-mechanical-computation",
                        "case_ids": ["fit-a", "fit-b", "load-a"],
                    },
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "computed-mechanical-proof",
                    "sources": [
                        source(
                            "step-model",
                            "product",
                            "toy.step",
                            product_inventory["toy.step"],
                        ),
                        source(
                            "mechanical-receipt",
                            "playtest",
                            receipt,
                            receipt_sha256,
                        ),
                    ],
                    "measurements": measurements,
                }
            if capability == "print-test":
                profiles = {}
                profile_sources = []
                for role in ("printer", "process", "filament"):
                    path, digest = write_bytes(
                        "profiles/%s.ini" % role,
                        ("[%s]\nfixture=1\n" % role).encode("utf-8"),
                    )
                    profiles[role] = {"path": path, "sha256": digest}
                    profile_sources.append(source("slicer-profile", "playtest", path, digest))
                gcode, gcode_sha256 = write_bytes(
                    "gcode/part_toy.gcode",
                    b"; generated by PrusaSlicer 2.9.6\nG28\nG1 X1 Y1\n",
                )
                measurements = {
                    "slicer": "PrusaSlicer",
                    "slicer_version": "2.9.6",
                    "profiles": profiles,
                    "parts": [
                        {
                            "input_ref": "part_toy.stl",
                            "input_sha256": product_inventory["part_toy.stl"],
                            "gcode_ref": gcode,
                            "gcode_sha256": gcode_sha256,
                            "gcode_bytes": len(
                                b"; generated by PrusaSlicer 2.9.6\nG28\nG1 X1 Y1\n"
                            ),
                            "returncode": 0,
                        }
                    ],
                    "slicer_errors": 0,
                }
                cited_profile_sources = profile_sources
                cited_gcode_sources = [
                    source("gcode-output", "playtest", gcode, gcode_sha256)
                ]
                dependencies = {
                    "product:part_toy.stl": product_inventory["part_toy.stl"],
                    **{
                        "playtest:%s" % item["path"]: item["sha256"]
                        for item in profile_sources
                    },
                    "playtest:%s" % gcode: gcode_sha256,
                }
                if unsealed_print_outputs:
                    measurements = {
                        "slicer": "PrusaSlicer",
                        "slicer_version": "2.9.6",
                        "profiles": {
                            "printer": "1" * 64,
                            "process": "2" * 64,
                            "filament": "3" * 64,
                        },
                        "parts": [
                            {
                                "input_ref": "part_toy.stl",
                                "input_sha256": product_inventory["part_toy.stl"],
                                "gcode_sha256": "4" * 64,
                                "gcode_bytes": 100,
                                "returncode": 0,
                            }
                        ],
                        "slicer_errors": 0,
                    }
                    cited_profile_sources = []
                    cited_gcode_sources = []
                    dependencies = {
                        "product:part_toy.stl": product_inventory["part_toy.stl"]
                    }
                receipt, receipt_sha256 = write_receipt(
                    capability,
                    "exact-slicer-proof",
                    "slicer-receipt",
                    measurements,
                    dependencies,
                    {
                        "command": "PrusaSlicer --export-gcode",
                        "exit_codes": [0],
                    },
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "exact-slicer-proof",
                    "sources": [
                        source(
                            "print-part",
                            "product",
                            "part_toy.stl",
                            product_inventory["part_toy.stl"],
                        ),
                        source(
                            "slicer-receipt",
                            "playtest",
                            receipt,
                            receipt_sha256,
                        ),
                        *cited_profile_sources,
                        *cited_gcode_sources,
                    ],
                    "measurements": measurements,
                }
            if capability == "motion-test":
                measurements = {
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
                }
                receipt, receipt_sha256 = write_receipt(
                    capability,
                    "kinematic-motion-proof",
                    "motion-receipt",
                    measurements,
                    {"product:toy.step": product_inventory["toy.step"]},
                    {"state_ids": list(range(10)), "continuous_sweep": True},
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "kinematic-motion-proof",
                    "sources": [
                        source(
                            "step-model",
                            "product",
                            "toy.step",
                            product_inventory["toy.step"],
                        ),
                        source(
                            "motion-receipt",
                            "playtest",
                            receipt,
                            receipt_sha256,
                        ),
                    ],
                    "measurements": measurements,
                }
            if capability == "classic-rules-test":
                provider = {
                    "name": "fixture-classic-provider",
                    "version": "1.0.0",
                    "config_sha256": "1" * 64,
                    "method_class": "deterministic-reference-rules-simulation",
                }
                measurements = {
                    "seeded_games": 1,
                    "rule_conformance_cases": 3,
                    "rule_mismatches": 0,
                    "role_legibility_cases": 2,
                    "role_legibility_failures": 0,
                }
                dependencies = {
                    "product:edition-rules.json": product_inventory[
                        "edition-rules.json"
                    ],
                    "product:role_a.step": product_inventory["role_a.step"],
                    "product:role_a.stl": product_inventory["role_a.stl"],
                    "product:role_b.step": product_inventory["role_b.step"],
                    "product:role_b.stl": product_inventory["role_b.stl"],
                }
                rules_model = {
                    "schema_version": 1,
                    "game": "fixture classic",
                    "rules": ["take one legal turn"],
                }
                reference, reference_sha256 = write_receipt(
                    capability,
                    "classic-rule-conformance-proof",
                    "reference-rules",
                    measurements,
                    dependencies,
                    {
                        "provider": provider,
                        "rules_model": rules_model,
                        "rules_model_sha256": hashlib.sha256(
                            json.dumps(
                                rules_model,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                        "comparison": {
                            "declaration_known_game": "fixture classic",
                            "rules_reference": "https://example.org/fixture-rules",
                            "no_rule_mutation_fields": True,
                        },
                        "conformance_cases": [
                            {
                                "case_id": "rule-1",
                                "passed": True,
                                "source": "fixture-reference",
                            },
                            {
                                "case_id": "rule-2",
                                "passed": True,
                                "source": "fixture-reference",
                            },
                            {
                                "case_id": "rule-3",
                                "passed": True,
                                "source": "fixture-reference",
                            },
                        ],
                    },
                )
                geometry_a = {
                    "shape": "cylinder",
                    "size_mm": {"x": 20.0, "y": 20.0, "z": 6.0},
                }
                geometry_b = {
                    "shape": "cylinder",
                    "size_mm": {"x": 18.0, "y": 18.0, "z": 8.0},
                }
                traces, traces_sha256 = write_receipt(
                    capability,
                    "classic-rule-conformance-proof",
                    "game-traces",
                    measurements,
                    dependencies,
                    {
                        "provider": provider,
                        "games": [
                            {"seed": 1, "completed": True, "rule_mismatches": 0}
                        ],
                        "role_cases": [
                            {
                                "part_id": "role-a",
                                "geometry": geometry_a,
                                "geometry_sha256": hashlib.sha256(
                                    json.dumps(
                                        geometry_a,
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest(),
                                "step_path": "role_a.step",
                                "step_sha256": product_inventory["role_a.step"],
                                "stl_path": "role_a.stl",
                                "stl_sha256": product_inventory["role_a.stl"],
                                "exact_body_bound": True,
                            },
                            {
                                "part_id": "role-b",
                                "geometry": geometry_b,
                                "geometry_sha256": hashlib.sha256(
                                    json.dumps(
                                        geometry_b,
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest(),
                                "step_path": "role_b.step",
                                "step_sha256": product_inventory["role_b.step"],
                                "stl_path": "role_b.stl",
                                "stl_sha256": product_inventory["role_b.stl"],
                                "exact_body_bound": True,
                            },
                        ],
                        "distinct_geometry_signatures": 2,
                    },
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "classic-rule-conformance-proof",
                    "sources": [
                        source(
                            "edition-rules",
                            "product",
                            "edition-rules.json",
                            product_inventory["edition-rules.json"],
                        ),
                        source(
                            "edition-part-step",
                            "product",
                            "role_a.step",
                            product_inventory["role_a.step"],
                        ),
                        source(
                            "edition-part-stl",
                            "product",
                            "role_a.stl",
                            product_inventory["role_a.stl"],
                        ),
                        source(
                            "edition-part-step",
                            "product",
                            "role_b.step",
                            product_inventory["role_b.step"],
                        ),
                        source(
                            "edition-part-stl",
                            "product",
                            "role_b.stl",
                            product_inventory["role_b.stl"],
                        ),
                        source("reference-rules", "playtest", reference, reference_sha256),
                        source("game-traces", "playtest", traces, traces_sha256),
                    ],
                    "measurements": measurements,
                }
            if capability == "science-test":
                provider = {
                    "name": "fixture-science-provider",
                    "version": "1.0.0",
                    "config_sha256": "2" * 64,
                    "method_class": "source-bound-comparison",
                }
                source_bytes = (
                    b"fixture rhythm\n"
                    b"one turn advances one beat\n"
                    + json.dumps(
                        {
                            "real_quantity": "one beat",
                            "model_quantity": "one turn",
                            "scale_ratio": 1,
                            "units": "beats per turn",
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                    b"ignore drag; not a physical prediction\n"
                    b"one beat per turn; not continuous time"
                )
                source_model = {
                    "phenomenon": "fixture rhythm",
                    "model": "one turn advances one beat",
                    "source_ids": ["fixture-source"],
                }
                simplifications = [
                    {
                        "simplification": "ignore drag",
                        "reason": "bounded fixture",
                        "disclosed_limit": "not a physical prediction",
                    },
                    {
                        "simplification": "one beat per turn",
                        "reason": "legible interaction",
                        "disclosed_limit": "not continuous time",
                    },
                ]
                scale = {
                    "real_quantity": "one beat",
                    "model_quantity": "one turn",
                    "scale_ratio": 1,
                    "units": "beats per turn",
                }
                canonical_scale = json.dumps(
                    scale, sort_keys=True, separators=(",", ":")
                )
                research_path = "playtest/invent-research.json"
                research_document = json.loads(
                    (context.made.artifact_root / research_path).read_text(
                        encoding="utf-8"
                    )
                )
                measurements = {
                    "accuracy_cases": 3,
                    "accuracy_failures": 0,
                    "simplifications_checked": 2,
                    "dishonest_simplifications": 0,
                    "content_coverage_traces": 1,
                    "content_coverage_failures": 0,
                }
                dependencies = {
                    "product:source-model.json": product_inventory[
                        "source-model.json"
                    ],
                    "product:wish.json": product_inventory["wish.json"],
                    "product:product.json": product_inventory["product.json"],
                    "product:%s" % research_path: product_inventory[research_path],
                }
                sources, sources_sha256 = write_receipt(
                    capability,
                    "source-bound-science-proof",
                    "science-sources",
                    measurements,
                    dependencies,
                    {
                        "provider": provider,
                        "source_model_sha256": hashlib.sha256(
                            json.dumps(
                                source_model,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                        "invent_research_file_sha256": product_inventory[
                            research_path
                        ],
                        "invent_research_sha256": research_document[
                            "research_sha256"
                        ],
                        "sources": [
                            {
                                "source_id": "fixture-source",
                                "title": "Fixture science source",
                                "publisher": "Fixture Observatory",
                                "url": "https://example.org/fixture-science",
                                "retrieved_at": "2026-08-25T00:00:00Z",
                                "media_type": "text/plain",
                                "content_sha256": hashlib.sha256(source_bytes).hexdigest(),
                                "content_bytes": len(source_bytes),
                                "content_encoding": "base64",
                                "content_base64": base64.b64encode(source_bytes).decode("ascii"),
                            }
                        ],
                        "accuracy_cases": [
                            {
                                "case_id": "phenomenon-1",
                                "source_ids": ["fixture-source"],
                                "product_field": "phenomenon",
                                "expected": source_model["phenomenon"],
                                "observed": source_model["phenomenon"],
                                "source_excerpt": source_model["phenomenon"],
                                "source_excerpt_sha256": hashlib.sha256(
                                    source_model["phenomenon"].encode("utf-8")
                                ).hexdigest(),
                                "passed": True,
                            },
                            {
                                "case_id": "model-1",
                                "source_ids": ["fixture-source"],
                                "product_field": "model",
                                "expected": source_model["model"],
                                "observed": source_model["model"],
                                "source_excerpt": source_model["model"],
                                "source_excerpt_sha256": hashlib.sha256(
                                    source_model["model"].encode("utf-8")
                                ).hexdigest(),
                                "passed": True,
                            },
                            {
                                "case_id": "scale-1",
                                "source_ids": ["fixture-source"],
                                "product_field": "scale",
                                "expected": canonical_scale,
                                "observed": canonical_scale,
                                "source_excerpt": canonical_scale,
                                "source_excerpt_sha256": hashlib.sha256(
                                    canonical_scale.encode("utf-8")
                                ).hexdigest(),
                                "passed": True,
                            },
                        ],
                        "simplification_checks": [
                            {
                                "simplification_sha256": hashlib.sha256(
                                    json.dumps(
                                        item,
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest(),
                                "source_ids": ["fixture-source"],
                                "disclosed_limit_present": True,
                                "source_supported": True,
                                "source_excerpt": "%s; %s"
                                % (item["simplification"], item["disclosed_limit"]),
                                "source_excerpt_sha256": hashlib.sha256(
                                    ("%s; %s" % (item["simplification"], item["disclosed_limit"])).encode("utf-8")
                                ).hexdigest(),
                                "passed": True,
                            }
                            for item in simplifications
                        ],
                        "wish_source_relevance": _science_relevance_record(
                            context.wish.objective,
                            source_model,
                            {"fixture-source": source_bytes.decode("utf-8")},
                        ),
                    },
                )
                traces, traces_sha256 = write_receipt(
                    capability,
                    "source-bound-science-proof",
                    "content-coverage-traces",
                    measurements,
                    dependencies,
                    {
                        "provider": provider,
                        "measurement_kind": "deterministic-product-text-coverage",
                        "traces": [
                            {
                                "seed": 1,
                                "measurement_kind": "deterministic-product-text-coverage",
                                "required_text": [
                                    "fixture rhythm",
                                    "not a physical prediction",
                                ],
                                "recovered_text": [
                                    "fixture rhythm",
                                    "not a physical prediction",
                                ],
                                "passed": True,
                            }
                        ],
                    },
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "source-bound-science-proof",
                    "sources": [
                        source(
                            "source-model",
                            "product",
                            "source-model.json",
                            product_inventory["source-model.json"],
                        ),
                        source(
                            "wish-context",
                            "product",
                            "wish.json",
                            product_inventory["wish.json"],
                        ),
                        source(
                            "product-copy",
                            "product",
                            "product.json",
                            product_inventory["product.json"],
                        ),
                        source(
                            "invent-research",
                            "product",
                            research_path,
                            product_inventory[research_path],
                        ),
                        source("science-sources", "playtest", sources, sources_sha256),
                        source(
                            "content-coverage-traces",
                            "playtest",
                            traces,
                            traces_sha256,
                        ),
                    ],
                    "measurements": measurements,
                }
            if capability == "world-test":
                manager_evidence = context.world_evidence
                if isinstance(manager_evidence, WorldPlaytestEvidence):
                    provider = {
                        "name": manager_evidence.provider.provider_id,
                        "version": manager_evidence.provider.version,
                        "config_sha256": manager_evidence.provider.config_sha256,
                        "method_class": "independent-private-reference-measurement",
                    }
                    manager_reference = manager_evidence.references[0]
                    manager_scope = context.world_inputs.references[0].scope
                    material_sha256 = manager_reference.content_sha256
                    consent_records = [
                        {
                            "reference_id": manager_reference.reference_id,
                            "subject": manager_scope.subject,
                            "rights_basis": manager_scope.rights_basis,
                            "allowed_features": list(manager_scope.allowed_features),
                            "excluded_features": list(manager_scope.excluded_features),
                            "verification_method": (
                                manager_reference.scope_authentication_method
                            ),
                            "verified_at": manager_reference.observed_at,
                            "consent_sha256": manager_reference.declaration_sha256,
                            "consent_bytes": manager_reference.declaration_bytes,
                        }
                    ]
                    reference_records = [
                        {
                            "reference_id": manager_reference.reference_id,
                            "media_type": manager_reference.media_type,
                            "content_sha256": manager_reference.content_sha256,
                            "content_bytes": manager_reference.content_bytes,
                            "reference_bytes_included": False,
                        }
                    ]
                    likeness_cases = [
                        {
                            "reference_id": item.reference_id,
                            "reference_feature": item.reference_feature,
                            "recognition_test": item.recognition_test,
                            "reference_sha256": item.reference_sha256,
                            "recognized": item.recognized,
                            "consent_safe": item.scope_safe,
                            "method_class": item.method_class,
                            "passed": item.passed,
                        }
                        for item in manager_evidence.cases
                    ]
                    manager_binding = {
                        "world_evidence_sha256": manager_evidence.evidence_sha256,
                        "world_inputs_sha256": context.world_inputs.binding_sha256,
                        "provider_attestation": dict(
                            manager_evidence.provider_attestation
                        ),
                        "provider_authorizations": [
                            {
                                "reference_id": item.reference_id,
                                "authorization_sha256": item.provider_authorization[
                                    "authorization_sha256"
                                ],
                            }
                            for item in manager_evidence.references
                        ],
                        "claim_boundary": CONSENT_CLAIM_BOUNDARY,
                    }
                    consent_scope = (
                        "authenticated customer/operator scope record; not legal "
                        "consent or ownership proof; raw bytes are intentionally "
                        "not public-replayable"
                    )
                    reference_scope = (
                        "isolated provider measurement over admitted private-reference "
                        "digests; raw bytes are intentionally not public-replayable"
                    )
                else:
                    # A deliberately legacy/self-authored proof. Canonical Workshop
                    # release must reject it without the exact Manager envelope.
                    provider = {
                        "name": "fixture-consent-reference-provider",
                        "version": "1.0.0",
                        "config_sha256": "3" * 64,
                        "method_class": "private-reference-feature-comparison",
                    }
                    material_sha256 = hashlib.sha256(
                        b"private fixture reference"
                    ).hexdigest()
                    consent_records = [
                        {
                            "reference_id": "fixture-reference",
                            "subject": "fixture subject",
                            "rights_basis": "signed fixture authorization",
                            "allowed_features": ["fixture feature"],
                            "excluded_features": ["private address"],
                            "verification_method": "signed-fixture-record",
                            "verified_at": "2026-08-25T00:00:00Z",
                            "consent_sha256": hashlib.sha256(
                                b"private fixture consent"
                            ).hexdigest(),
                            "consent_bytes": len(b"private fixture consent"),
                        }
                    ]
                    reference_records = [
                        {
                            "reference_id": "fixture-reference",
                            "media_type": "image/jpeg",
                            "content_sha256": material_sha256,
                            "content_bytes": len(b"private fixture reference"),
                            "reference_bytes_included": False,
                        }
                    ]
                    likeness_cases = [
                        {
                            "reference_id": "fixture-reference",
                            "reference_feature": "fixture feature",
                            "recognition_test": "feature remains recognizable",
                            "reference_sha256": material_sha256,
                            "recognized": True,
                            "consent_safe": True,
                            "method_class": "vision-feature-comparison",
                            "passed": True,
                        }
                    ]
                    manager_binding = {}
                    consent_scope = (
                        "trusted-provider verification over private consent digests; "
                        "raw bytes are intentionally not public-replayable"
                    )
                    reference_scope = (
                        "trusted-provider verification over authorized private "
                        "reference digests; raw bytes are intentionally not public-replayable"
                    )
                if legacy_world_terms:
                    measurements = {
                        "consent_verified": True,
                        "personalization_features": 1,
                        "likeness_cases": 1,
                        "recognition_failures": 0,
                        "consent_violations": 0,
                    }
                    for record in reference_records:
                        record["private_bytes_sealed"] = record.pop(
                            "reference_bytes_included"
                        )
                    scope_bytes_key = "raw_consent_bytes_sealed"
                    reference_bytes_key = "raw_private_bytes_sealed"
                else:
                    measurements = {
                        "scope_record_authenticated": True,
                        "personalization_features": 1,
                        "likeness_cases": 1,
                        "recognition_failures": 0,
                        "scope_violations": 0,
                    }
                    scope_bytes_key = "raw_scope_record_bytes_included"
                    reference_bytes_key = "raw_reference_bytes_included"
                dependencies = {
                    "product:personalization-map.json": product_inventory[
                        "personalization-map.json"
                    ]
                }
                consent, consent_sha256 = write_receipt(
                    capability,
                    "reference-bound-world-proof",
                    "consent-record",
                    measurements,
                    dependencies,
                    {
                        "attestation": provider,
                        "attestation_scope": consent_scope,
                        "records": consent_records,
                        scope_bytes_key: False,
                        **manager_binding,
                    },
                )
                reference, reference_sha256 = write_receipt(
                    capability,
                    "reference-bound-world-proof",
                    "reference-material",
                    measurements,
                    dependencies,
                    {
                        "attestation": provider,
                        "attestation_scope": reference_scope,
                        "references": reference_records,
                        reference_bytes_key: False,
                        **manager_binding,
                    },
                )
                traces, traces_sha256 = write_receipt(
                    capability,
                    "reference-bound-world-proof",
                    "likeness-traces",
                    measurements,
                    dependencies,
                    {
                        "attestation": provider,
                        "cases": likeness_cases,
                        **manager_binding,
                    },
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "reference-bound-world-proof",
                    "sources": [
                        source(
                            "personalization-map",
                            "product",
                            "personalization-map.json",
                            product_inventory["personalization-map.json"],
                        ),
                        source("consent-record", "playtest", consent, consent_sha256),
                        source(
                            "reference-material", "playtest", reference, reference_sha256
                        ),
                        source("likeness-traces", "playtest", traces, traces_sha256),
                    ],
                    "measurements": measurements,
                }
            if capability == "game-simulation":
                measurements, trace_document, analysis_document = (
                    fixture_game_release_documents(
                        artifact_sha256,
                        fixture_game_contract(),
                        product_inventory,
                    )
                )
                traces, traces_sha256 = write_json(
                    "game-traces.json",
                    trace_document,
                )
                analysis, analysis_sha256 = write_json(
                    "game-analysis.json",
                    analysis_document,
                )
                return {
                    "schema_version": 1,
                    "capability": capability,
                    "artifact_sha256": artifact_sha256,
                    "proof_class": "seeded-game-analysis-proof",
                    "sources": [
                        source(
                            "simulator-source",
                            "product",
                            GAME_SIMULATOR_PATH,
                            product_inventory[GAME_SIMULATOR_PATH],
                        ),
                        source(
                            "game-rules",
                            "product",
                            GAME_RULES_PATH,
                            product_inventory[GAME_RULES_PATH],
                        ),
                        source(
                            "invent-game-contract",
                            "product",
                            GAME_CONTRACT_PATH,
                            product_inventory[GAME_CONTRACT_PATH],
                        ),
                        source("game-traces", "playtest", traces, traces_sha256),
                        source("game-analysis", "playtest", analysis, analysis_sha256),
                    ],
                    "measurements": measurements,
                }
            return None

        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence = {
                "evidence_class": (
                    "ai-simulation" if ai_simulation else "deterministic-fixture"
                ),
                "artifact_sha256": context.made.artifact_sha256,
                "agent_roles": ["optimizing-player", "adversarial-breaker"],
                "claims": ["Synthetic contract evidence for %s." % capability],
            }
            if (
                passed
                and valid_proofs
                and (capability != "game-simulation" or valid_invented)
            ):
                proof = release_proof(capability)
                if proof is not None:
                    evidence["release_proof"] = proof
            evidence_ref, evidence_sha256 = write_json(
                capability + ".json", evidence
            )
            results.append(
                PlaytestResult.create(
                    capability,
                    passed,
                    context.made.artifact_sha256,
                    evidence,
                    "workshop-contract-fixture",
                    "1.0.0",
                    CONFIG_SHA256,
                    evidence_ref,
                    evidence_sha256,
                )
            )
        evidence_manifest = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        )
        feedback = ()
        if not passed:
            feedback = (
                Feedback(
                    "cycle-too-short",
                    "mechanics",
                    "improve",
                    "The first rhythm ends too quickly.",
                    "Add a second beat before the mechanism resets.",
                    ("simulation.json",),
                ),
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=evidence_manifest,
            ),
            feedback,
        )

    @classmethod
    def playtest_job(cls, context):
        return cls._playtest(context, passed=context.round >= 2)

    @classmethod
    def passing_playtest(cls, context):
        return cls._playtest(context, passed=True)

    @classmethod
    def passing_invented_playtest(cls, context):
        return cls._playtest(context, passed=True, valid_invented=True)

    @staticmethod
    def site_writer(context, sealed_root, sealed_manifest):
        del sealed_root
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-" + context.wish.product_id,
            slug=context.wish.product_id,
            owner_id="owner-test",
            root_id="design-" + context.wish.product_id,
            current_history_id="history-1",
            published_history_id="history-1",
            status="public",
            project_url=(
                "https://www.autonomous.ai/factory/product/"
                + context.wish.product_id
            ),
            observed_at="2026-08-23T12:00:00+00:00",
            listing_active=True,
            listing_price_cents=3500,
            listing_currency="USD",
            listing_sku="TEST-001",
            details={"instructions_sha256": sealed_manifest.artifact_sha256},
        )

    @staticmethod
    def fulfiller(context):
        return Delivered(
            context.made.artifact_sha256,
            context.instructions.instructions_sha256,
            "USPS",
            "Priority Mail",
            "9400100000000000000000",
            "handed-off",
            "2026-08-23T12:00:00+00:00",
            fixture_delivery_evidence(
                context.made.artifact_sha256,
                context.instructions.instructions_sha256,
            ),
        )

    @staticmethod
    def review_authenticator(delivered, review):
        return ReviewAuthentication(
            authentication_id="review-auth-" + review.review_id,
            provider="fixture-order-service",
            provider_version="1.0.0",
            provider_config_sha256="e" * 64,
            order_id="order-" + delivered.tracking_id,
            reviewer_id="customer-1",
            review_id=review.review_id,
            review_sha256=review_sha256(review),
            product_artifact_sha256=review.product_artifact_sha256,
            instructions_sha256=review.instructions_sha256,
            delivery_tracking_id=review.delivery_tracking_id,
            authenticated_at=review.observed_at,
        )

    def complete_tools(self, playtest=None):
        return WorkshopTools(
            invent=self.invent_job,
            make=self.make_job,
            playtest=playtest or self.playtest_job,
            instructions=DefaultInstructions(site_writer=self.site_writer),
            deliver=DefaultDeliver(self.fulfiller),
        )

    def test_taste_only_inventor_runs_shared_feedback_loop_to_deliver(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.runtime,
        )
        self.assertEqual(workshop.customization_level, "taste-only")
        result = workshop.run(Wish.create("rhythm-top", "A delightful desk spinner"))
        self.assertEqual((result.status, result.job, result.round), ("delivered", "deliver", 2))
        self.assertEqual(result.playtest_rounds, 4)
        self.assertIsNotNone(result.delivery)
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("rhythm-top"))
        transitions = [event["to_stage"] for event in state.events("rhythm-top")]
        self.assertEqual(
            transitions,
            [
                "wish",
                "invent",
                "make",
                "playtest",
                "make",
                "playtest",
                "instructions",
                "instructions",
                "deliver",
                "deliver",
            ],
        )

    def test_workshop_passes_exact_inventor_identity_without_rewriting_wish(self):
        seen = []

        def make(context):
            seen.append(context.inventor_id)
            return self.make_job(context)

        wish = Wish.create("identity-top", "A top for one exact inventor")
        original = wish.to_dict()
        result = Workshop(
            self.inventor,
            "moving-machines",
            inventor_id="machine-smith",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=make,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.root / "identity-runtime",
        ).run(wish, playtest_rounds=1)
        self.assertEqual((result.status, seen), ("delivered", ["machine-smith"]))
        self.assertEqual(wish.to_dict(), original)
        self.assertNotEqual("machine-smith", "Test Inventor".casefold())

    def test_instructions_resume_cannot_switch_inventor_identity(self):
        wish = Wish.create("identity-resume", "A top owned by one inventor")
        waiting = Workshop(
            self.inventor,
            "moving-machines",
            inventor_id="machine-smith",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(),
            ),
            runtime_root=self.root / "identity-resume-runtime",
        ).run(wish, playtest_rounds=1)
        self.assertEqual((waiting.status, waiting.job), ("waiting", "instructions"))
        with self.assertRaisesRegex(ContractError, "different inventor identity"):
            Workshop(
                self.inventor,
                "moving-machines",
                inventor_id="other-smith",
                tools=WorkshopTools(
                    invent=self.invent_job,
                    make=self.make_job,
                    playtest=self.passing_playtest,
                    instructions=DefaultInstructions(site_writer=self.site_writer),
                ),
                runtime_root=self.root / "identity-resume-runtime",
            ).resume_instructions(wish)

    def test_resume_instructions_uses_checkpoint_without_repeating_make_or_playtest(self):
        calls = {"make": 0, "playtest": 0, "site": 0}

        def counted_make(context):
            calls["make"] += 1
            return self.make_job(context)

        def counted_playtest(context):
            calls["playtest"] += 1
            return self.passing_playtest(context)

        def counted_site(context, root, manifest):
            calls["site"] += 1
            return self.site_writer(context, root, manifest)

        wish = Wish.create("resumable-top", "A top whose page can resume")
        waiting_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        waiting = waiting_workshop.run(wish, playtest_rounds=3)
        self.assertEqual((waiting.status, waiting.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 0})

        resumed_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=counted_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        with self.assertRaisesRegex(ContractError, "original Wish"):
            resumed_workshop.resume_instructions(
                Wish.create("resumable-top", "A different Wish must not attach")
            )
        resumed = resumed_workshop.resume_instructions(wish)
        self.assertEqual((resumed.status, resumed.job), ("delivered", "deliver"))
        self.assertEqual(resumed.artifact_sha256, waiting.artifact_sha256)
        self.assertEqual(resumed.playtest_rounds, 3)
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 1})
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain(wish.product_id))

    def test_resume_reuses_sealed_instructions_and_only_retries_the_site(self):
        calls = {"make": 0, "playtest": 0, "site": 0}

        def counted_make(context):
            calls["make"] += 1
            return self.make_job(context)

        def counted_playtest(context):
            calls["playtest"] += 1
            return self.passing_playtest(context)

        def waiting_site(context, root, manifest):
            del context, root, manifest
            calls["site"] += 1
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The sealed page is waiting for a site account.",
                    "Configure the site account and resume this exact page.",
                )
            )

        wish = Wish.create("sealed-top", "A top with one sealed page")
        first = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=waiting_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=2)
        self.assertEqual((first.status, first.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 1})
        waiting_payload = Runtime(
            self.runtime / "workshop.sqlite3"
        ).events(wish.product_id)[-1]["payload"]
        self.assertEqual(len(waiting_payload["resume_checkpoint_sha256"]), 64)
        self.assertEqual(len(waiting_payload["instructions_sha256"]), 64)
        self.assertEqual(
            first.instructions_sha256,
            waiting_payload["instructions_sha256"],
        )

        def successful_site(context, root, manifest):
            calls["site"] += 1
            return self.site_writer(context, root, manifest)

        resumed = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=successful_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).resume_instructions(wish)
        self.assertEqual((resumed.status, resumed.job), ("delivered", "deliver"))
        self.assertEqual(resumed.artifact_sha256, first.artifact_sha256)
        self.assertIsNotNone(first.invented)
        self.assertEqual(resumed.invented, first.invented)
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 2})

    def test_resume_rejects_changed_sealed_instructions_before_site_effect(self):
        site_calls = 0

        def waiting_site(context, root, manifest):
            del context, root, manifest
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The sealed page is waiting.",
                    "Resume after site capability is configured.",
                )
            )

        wish = Wish.create("tampered-page", "A top with immutable Instructions")
        Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=waiting_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=1)
        instructions_path = (
            self.runtime
            / "runs"
            / wish.product_id
            / "instructions"
            / "INSTRUCTIONS.md"
        )
        instructions_path.write_text("changed while waiting\n", encoding="utf-8")

        def forbidden_site(context, root, manifest):
            nonlocal site_calls
            site_calls += 1
            return self.site_writer(context, root, manifest)

        resumed_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=forbidden_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        with self.assertRaisesRegex(ContractError, "changed while waiting"):
            resumed_workshop.resume_instructions(wish)
        self.assertEqual(site_calls, 0)

    def test_customer_reviews_follow_deliver_and_feed_only_a_future_make(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(self.passing_playtest),
            review_authenticator=self.review_authenticator,
            runtime_root=self.runtime,
        )
        result = workshop.run(
            Wish.create("reviewed-top", "A top a customer can review"),
            playtest_rounds=1,
        )
        review = CustomerReview(
            "review-1",
            result.artifact_sha256,
            result.instructions_sha256,
            result.delivery.tracking_id,
            4,
            "The second rhythm is delightful; make the winding grip larger next time.",
            "2026-08-24T12:00:00+00:00",
        )
        self.assertEqual(workshop.record_review("reviewed-top", review), review)
        self.assertEqual(workshop.record_review("reviewed-top", review), review)
        self.assertEqual(workshop.reviews("reviewed-top"), (review,))
        learning = workshop.review_learnings("reviewed-top")[0]
        self.assertEqual(learning["applies_to"], "future-make")
        self.assertTrue(learning["delivered_revision_immutable"])
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertEqual(state.get_product("reviewed-top")["stage"], "deliver")
        self.assertTrue(state.verify_event_chain("reviewed-top"))

        changed = CustomerReview(
            "review-1",
            result.artifact_sha256,
            result.instructions_sha256,
            result.delivery.tracking_id,
            1,
            "Different feedback under the same id must not replace history.",
            "2026-08-24T12:00:00+00:00",
        )
        with self.assertRaisesRegex(ContractError, "already bound"):
            workshop.record_review("reviewed-top", changed)

    def test_customer_review_fails_closed_without_order_authenticator(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(self.passing_playtest),
            runtime_root=self.runtime,
        )
        result = workshop.run(
            Wish.create("unauthenticated-review", "A top someone might review"),
            playtest_rounds=1,
        )
        review = CustomerReview(
            "review-no-order-proof",
            result.artifact_sha256,
            result.instructions_sha256,
            result.delivery.tracking_id,
            5,
            "Lovely, but this must still be order-authenticated.",
            "2026-08-24T12:00:00+00:00",
        )
        with self.assertRaisesRegex(ContractError, "order/reviewer authenticator"):
            workshop.record_review("unauthenticated-review", review)
        self.assertEqual(workshop.reviews("unauthenticated-review"), ())

    def test_three_levels_are_explicit_and_playtest_requires_make(self):
        taste_only = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(self.passing_playtest),
            runtime_root=self.root / "taste-runtime",
        )
        custom_make = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            runtime_root=self.root / "make-runtime",
        )
        custom_playtest = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            playtest=self.passing_playtest,
            runtime_root=self.root / "playtest-runtime",
        )
        self.assertEqual(
            (
                taste_only.customization_level,
                custom_make.customization_level,
                custom_playtest.customization_level,
            ),
            ("taste-only", "custom-make", "custom-playtest"),
        )
        with self.assertRaisesRegex(ContractError, "requires custom Make"):
            Workshop(
                self.inventor,
                "moving-machines",
                playtest=self.passing_playtest,
                runtime_root=self.root / "invalid-runtime",
            )

    def test_missing_shared_make_waits_without_fabricating_a_product(self):
        wish = Wish.create("tiny-friend", "A tiny desk companion")
        inputs = self.world_inputs(wish)
        with mock.patch.dict(
            os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
        ):
            workshop = Workshop(
                self.inventor,
                "little-worlds",
                tools=WorkshopTools(invent=self.world_invent_job),
                runtime_root=self.runtime,
                world_inputs=inputs,
            )
        result = workshop.run(
            wish,
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job, result.round), ("waiting", "make", 1))
        self.assertEqual(result.playtest_rounds, 2)
        self.assertEqual(result.needs[0].capability, "model-and-cad-maker")
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("tiny-friend"))
        self.assertIsNone(state.get_product("tiny-friend")["artifact_sha256"])
        self.assertEqual(state.get_product("tiny-friend")["metadata"]["playtest_rounds"], 2)

    def test_invent_must_reach_its_reward_target_before_make(self):
        make_calls = 0

        def unfinished_invent(context):
            complete = self.invent_job(context)
            return Invented(
                complete.wish_sha256,
                complete.taste_sha256,
                complete.lane,
                complete.concept,
                84,
                90,
            )

        def forbidden_make(context):
            nonlocal make_calls
            make_calls += 1
            return self.make_job(context)

        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=unfinished_invent, make=forbidden_make),
            runtime_root=self.root / "unfinished-invent-runtime",
        ).run(
            Wish.create("unfinished-concept", "A machine with an unresolved shape"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job), ("waiting", "invent"))
        self.assertEqual(
            result.needs[0].capability, "industrial-design-target-score"
        )
        self.assertEqual(make_calls, 0)

    def test_each_wish_can_buy_a_different_bounded_round_allowance(self):
        two_rounds = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.root / "two-round-runtime",
        )
        result = two_rounds.run(
            Wish.create("small-tier", "A small playtest allowance"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.round, result.playtest_rounds), ("delivered", 2, 2))

        one_round = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.root / "one-round-runtime",
        )
        held = one_round.run(
            Wish.create("smallest-tier", "One chance to improve"),
            playtest_rounds=1,
        )
        self.assertEqual(
            (held.status, held.job, held.round, held.playtest_rounds),
            ("stopped", "playtest", 1, 1),
        )
        self.assertIsNone(held.instructions_sha256)
        self.assertIsNone(held.delivery)

        with self.assertRaisesRegex(ContractError, "from 1 to 100"):
            Workshop(
                self.inventor,
                "moving-machines",
                tools=self.complete_tools(),
                runtime_root=self.root / "invalid-round-runtime",
            ).run(
                Wish.create("bad-tier", "An invalid allowance"),
                playtest_rounds=0,
            )

    def test_custom_playtest_cannot_silently_narrow_the_lane_policy(self):
        def incomplete_playtest(context):
            complete = self.passing_playtest(context)
            first = complete.evidence.results[:1]
            return Playtested(
                Playtest(
                    context.made.artifact_manifest,
                    first,
                    evidence_manifest=complete.evidence.evidence_manifest,
                )
            )

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=self.invent_job),
            make=self.make_job,
            playtest=incomplete_playtest,
            runtime_root=self.root / "incomplete-policy-runtime",
        )
        result = workshop.run(
            Wish.create("narrow-policy", "A machine with one precise movement"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs},
            set(workshop.blueprint.required_capabilities("playtest"))
            - {workshop.blueprint.required_capabilities("playtest")[0]},
        )

    def test_custom_playtest_labels_cannot_release_a_moving_machine(self):
        calls = {"instructions": 0, "deliver": 0}

        def synthetic_playtest(context):
            return self._playtest(
                context,
                passed=True,
                valid_proofs=False,
            )

        def forbidden_instructions(context):
            del context
            calls["instructions"] += 1
            raise AssertionError("Instructions must not see synthetic Playtest labels")

        def forbidden_deliver(context):
            del context
            calls["deliver"] += 1
            raise AssertionError("Deliver must not see synthetic Playtest labels")

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                instructions=forbidden_instructions,
                deliver=forbidden_deliver,
            ),
            make=self.make_job,
            playtest=synthetic_playtest,
            runtime_root=self.root / "synthetic-moving-policy-runtime",
        )
        result = workshop.run(
            Wish.create("synthetic-machine", "A moving toy with pretend pass labels"),
            playtest_rounds=1,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs},
            {"mechanical-test", "print-test", "motion-test"},
        )
        self.assertEqual(calls, {"instructions": 0, "deliver": 0})

    def test_custom_playtest_pass_labels_cannot_bypass_any_lane_release_proof(self):
        expected_by_lane = {
            "classics-made-yours": {
                "classic-rules-test",
                "mechanical-test",
                "print-test",
            },
            "invented-games": {
                "game-simulation",
                "mechanical-test",
                "print-test",
            },
            "moving-machines": {
                "motion-test",
                "mechanical-test",
                "print-test",
            },
            "holdable-science": {
                "science-test",
                "mechanical-test",
                "print-test",
            },
            "little-worlds": {
                "world-test",
                "mechanical-test",
                "print-test",
            },
        }

        def synthetic_playtest(context):
            return self._playtest(context, passed=True, valid_proofs=False)

        for lane, expected in expected_by_lane.items():
            with self.subTest(lane=lane):
                wish = Wish.create(
                    lane + "-synthetic", "Pretend every check passed"
                )
                world_inputs = (
                    self.world_inputs(wish) if lane == "little-worlds" else None
                )
                workshop = Workshop(
                    self.inventor,
                    lane,
                    tools=WorkshopTools(
                        invent=(
                            self.world_invent_job
                            if lane == "little-worlds"
                            else self.invent_job
                        )
                    ),
                    make=self.make_job,
                    playtest=synthetic_playtest,
                    runtime_root=self.root / (lane + "-synthetic-runtime"),
                    world_inputs=world_inputs,
                )
                result = workshop.run(
                    wish,
                    playtest_rounds=1,
                )
                self.assertEqual((result.status, result.job), ("waiting", "playtest"))
                self.assertEqual(
                    {need.capability for need in result.needs}, expected
                )

    def test_valid_engine_neutral_custom_proofs_can_advance_every_lane(self):
        def valid_playtest(context):
            return self._playtest(
                context,
                passed=True,
                valid_invented=True,
            )

        for lane in (
            "classics-made-yours",
            "invented-games",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        ):
            with self.subTest(lane=lane):
                wish = Wish.create(
                    lane + "-valid-custom",
                    (
                        "Use exact fixture rhythm evidence"
                        if lane == "holdable-science"
                        else "Use exact custom evidence"
                    ),
                )
                runtime_root = self.root / (lane + "-valid-custom-runtime")
                world_inputs = (
                    self.world_inputs(wish) if lane == "little-worlds" else None
                )
                tools = WorkshopTools(
                    invent=(
                        self.world_invent_job
                        if lane == "little-worlds"
                        else self.invent_job
                    ),
                    instructions=DefaultInstructions(site_writer=self.site_writer),
                    deliver=DefaultDeliver(self.fulfiller),
                )
                workshop = Workshop(
                    self.inventor,
                    lane,
                    tools=tools,
                    make=self.make_job,
                    playtest=valid_playtest,
                    runtime_root=runtime_root,
                    world_inputs=world_inputs,
                )
                result = workshop.run(wish, playtest_rounds=1)
                if lane == "little-worlds":
                    self.assertEqual((result.status, result.job), ("waiting", "playtest"))
                    self.assertEqual(
                        {need.capability for need in result.needs}, {"world-test"}
                    )
                    evidence = self.world_evidence(
                        wish, result.artifact_sha256, world_inputs
                    )
                    result = Workshop(
                        self.inventor,
                        lane,
                        tools=tools,
                        make=self.make_job,
                        playtest=valid_playtest,
                        runtime_root=runtime_root,
                        world_inputs=world_inputs,
                        world_evidence=evidence,
                    ).resume(wish)
                self.assertEqual((result.status, result.job), ("delivered", "deliver"))

    def test_world_custom_make_exact_personalization_reaches_playtest(self):
        wish = Wish.create(
            "world-exact-custom-make-map",
            "Keep one exact admitted feature in a tiny world",
        )
        inputs = self.world_inputs(wish)
        calls = {"playtest": 0}

        def observed_playtest(context):
            calls["playtest"] += 1
            return self.passing_invented_playtest(context)

        result = Workshop(
            self.inventor,
            "little-worlds",
            tools=WorkshopTools(invent=self.world_invent_job),
            make=self.make_job,
            playtest=observed_playtest,
            runtime_root=self.root / "world-exact-custom-make-runtime",
            world_inputs=inputs,
        ).run(wish, playtest_rounds=1)

        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual({need.capability for need in result.needs}, {"world-test"})
        self.assertEqual(calls["playtest"], 1)

    def test_world_custom_make_cannot_change_accepted_personalization(self):
        for field, changed in (
            ("physical_form", "a different silhouette"),
            ("recognition_test", "a different recognition test"),
        ):
            with self.subTest(field=field):
                wish = Wish.create(
                    "world-changed-custom-map-" + field.replace("_", "-"),
                    "Keep one exact admitted feature in a tiny world",
                )
                inputs = self.world_inputs(wish)
                calls = {"playtest": 0}

                def changed_make(context, selected=field, value=changed):
                    made = self.make_job(context)
                    path = made.artifact_root / "personalization-map.json"
                    document = json.loads(path.read_text(encoding="utf-8"))
                    document["feature_to_form_map"][0][selected] = value
                    path.write_text(
                        json.dumps(document, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    return Made.from_root(made.artifact_root, made.product)

                def forbidden_playtest(context):
                    calls["playtest"] += 1
                    return self.passing_invented_playtest(context)

                with self.assertRaisesRegex(
                    ContractError,
                    "Made personalization map differs from the accepted Invent contract",
                ):
                    Workshop(
                        self.inventor,
                        "little-worlds",
                        tools=WorkshopTools(invent=self.world_invent_job),
                        make=changed_make,
                        playtest=forbidden_playtest,
                        runtime_root=self.root
                        / ("world-changed-custom-map-runtime-" + field),
                        world_inputs=inputs,
                    ).run(wish, playtest_rounds=1)
                self.assertEqual(calls["playtest"], 0)

    def test_canonical_world_release_rejects_legacy_consent_overclaim_terms(self):
        wish = Wish.create(
            "world-legacy-consent-overclaim",
            "Keep one exact admitted feature in a tiny world",
        )
        inputs = self.world_inputs(wish)
        runtime_root = self.root / "world-legacy-consent-overclaim-runtime"

        def legacy_playtest(context):
            return self._playtest(
                context,
                passed=True,
                valid_invented=True,
                legacy_world_terms=True,
            )

        first = Workshop(
            self.inventor,
            "little-worlds",
            tools=WorkshopTools(invent=self.world_invent_job),
            make=self.make_job,
            playtest=legacy_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
        ).run(wish, playtest_rounds=1)
        self.assertEqual((first.status, first.job), ("waiting", "playtest"))
        evidence = self.world_evidence(wish, first.artifact_sha256, inputs)

        resumed = Workshop(
            self.inventor,
            "little-worlds",
            tools=WorkshopTools(invent=self.world_invent_job),
            make=self.make_job,
            playtest=legacy_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
            world_evidence=evidence,
        ).resume(wish)
        self.assertEqual((resumed.status, resumed.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in resumed.needs}, {"world-test"}
        )

    def test_world_resume_rejects_manager_evidence_for_another_make(self):
        wish = Wish.create(
            "world-wrong-resume-artifact",
            "Use one exact admitted reference in a tiny world",
        )
        inputs = self.world_inputs(wish)
        runtime_root = self.root / "world-wrong-resume-runtime"
        tools = WorkshopTools(
            invent=self.world_invent_job,
            instructions=DefaultInstructions(site_writer=self.site_writer),
            deliver=DefaultDeliver(self.fulfiller),
        )

        first = Workshop(
            self.inventor,
            "little-worlds",
            tools=tools,
            make=self.make_job,
            playtest=self.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
        ).run(wish, playtest_rounds=1)
        self.assertEqual((first.status, first.job), ("waiting", "playtest"))

        evidence_for_another_make = self.world_evidence(
            wish, "f" * 64, inputs
        )
        resumed = Workshop(
            self.inventor,
            "little-worlds",
            tools=tools,
            make=self.make_job,
            playtest=self.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
            world_evidence=evidence_for_another_make,
        ).resume(wish)
        self.assertEqual((resumed.status, resumed.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in resumed.needs}, {"world-test"}
        )

    def test_world_resume_cannot_swap_the_accepted_manager_inputs(self):
        wish = Wish.create(
            "world-swapped-resume-inputs",
            "Keep one exact admitted feature in a tiny world",
        )
        inputs = self.world_inputs(wish)
        runtime_root = self.root / "world-swapped-inputs-runtime"
        tools = WorkshopTools(invent=self.world_invent_job)
        first = Workshop(
            self.inventor,
            "little-worlds",
            tools=tools,
            make=self.make_job,
            playtest=self.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
        ).run(wish, playtest_rounds=1)
        self.assertEqual((first.status, first.job), ("waiting", "playtest"))

        swapped = WorldInventInputs(
            wish.product_id,
            json_sha256(wish.to_dict()),
            WorldProviderIdentity(
                "different-world-reference-service", "1.0.0", "9" * 64
            ),
            inputs.references,
        )
        with self.assertRaisesRegex(
            ContractError, "different Manager world inputs"
        ):
            Workshop(
                self.inventor,
                "little-worlds",
                tools=tools,
                make=self.make_job,
                playtest=self.passing_invented_playtest,
                runtime_root=runtime_root,
                world_inputs=swapped,
            ).resume(wish)

    def test_placeholder_custom_receipts_cannot_release_any_capability(self):
        lanes = {
            "mechanical-test": "moving-machines",
            "print-test": "moving-machines",
            "motion-test": "moving-machines",
            "classic-rules-test": "classics-made-yours",
            "science-test": "holdable-science",
            "world-test": "little-worlds",
        }
        for capability, lane in lanes.items():
            with self.subTest(capability=capability):
                def placeholder_playtest(context, selected=capability):
                    return self._playtest(
                        context,
                        passed=True,
                        valid_invented=True,
                        placeholder_receipts=(selected,),
                    )

                wish = Wish.create(
                    capability + "-placeholder", "Reject placeholder JSON"
                )
                world_inputs = (
                    self.world_inputs(wish) if lane == "little-worlds" else None
                )
                result = Workshop(
                    self.inventor,
                    lane,
                    tools=WorkshopTools(
                        invent=(
                            self.world_invent_job
                            if lane == "little-worlds"
                            else self.invent_job
                        )
                    ),
                    make=self.make_job,
                    playtest=placeholder_playtest,
                    runtime_root=self.root / (capability + "-placeholder-runtime"),
                    world_inputs=world_inputs,
                ).run(
                    wish,
                    playtest_rounds=1,
                )
                self.assertEqual((result.status, result.job), ("waiting", "playtest"))
                self.assertEqual(
                    {need.capability for need in result.needs}, {capability}
                )

    def test_mismatched_custom_receipts_cannot_release_any_capability(self):
        lanes = {
            "mechanical-test": "moving-machines",
            "print-test": "moving-machines",
            "motion-test": "moving-machines",
            "classic-rules-test": "classics-made-yours",
            "science-test": "holdable-science",
            "world-test": "little-worlds",
        }
        for capability, lane in lanes.items():
            with self.subTest(capability=capability):
                def mismatched_playtest(context, selected=capability):
                    return self._playtest(
                        context,
                        passed=True,
                        valid_invented=True,
                        tampered_receipts=(selected,),
                    )

                wish = Wish.create(
                    capability + "-mismatched", "Reject mismatched proof"
                )
                world_inputs = (
                    self.world_inputs(wish) if lane == "little-worlds" else None
                )
                result = Workshop(
                    self.inventor,
                    lane,
                    tools=WorkshopTools(
                        invent=(
                            self.world_invent_job
                            if lane == "little-worlds"
                            else self.invent_job
                        )
                    ),
                    make=self.make_job,
                    playtest=mismatched_playtest,
                    runtime_root=self.root / (capability + "-mismatched-runtime"),
                    world_inputs=world_inputs,
                ).run(
                    wish,
                    playtest_rounds=1,
                )
                self.assertEqual((result.status, result.job), ("waiting", "playtest"))
                self.assertEqual(
                    {need.capability for need in result.needs}, {capability}
                )

    def test_custom_print_hash_claims_do_not_replace_sealed_profiles_and_gcode(self):
        def unsealed_print_playtest(context):
            return self._playtest(
                context,
                passed=True,
                valid_invented=True,
                unsealed_print_outputs=True,
            )

        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=self.invent_job),
            make=self.make_job,
            playtest=unsealed_print_playtest,
            runtime_root=self.root / "unsealed-print-output-runtime",
        ).run(
            Wish.create("unsealed-print-output", "Reject typed-in output hashes"),
            playtest_rounds=1,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual({need.capability for need in result.needs}, {"print-test"})

    def test_result_mapping_must_equal_its_exact_sealed_evidence_document(self):
        def mismatched_playtest(context):
            complete = self._playtest(context, passed=True)
            replaced = []
            for result in complete.evidence.results:
                if result.playtest_id != "mechanical-test":
                    replaced.append(result)
                    continue
                value = result.to_dict()
                value["evidence"] = {
                    **dict(result.evidence),
                    "claims": ["This mapping was never written to the sealed file."],
                }
                replaced.append(PlaytestResult(**value))
            return Playtested(
                Playtest(
                    context.made.artifact_manifest,
                    tuple(replaced),
                    evidence_manifest=complete.evidence.evidence_manifest,
                )
            )

        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=self.invent_job),
            make=self.make_job,
            playtest=mismatched_playtest,
            runtime_root=self.root / "mismatched-result-runtime",
        ).run(
            Wish.create("mismatched-result", "A toy with two evidence stories"),
            playtest_rounds=1,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs}, {"mechanical-test"}
        )

    def test_changed_custom_playtest_evidence_fails_before_instructions(self):
        instructions_calls = 0

        def tampering_playtest(context):
            result = self._playtest(context, passed=True)
            (context.workspace / "mechanical-receipt.json").write_text(
                '{"computed":false}\n', encoding="utf-8"
            )
            return result

        def forbidden_instructions(context):
            del context
            nonlocal instructions_calls
            instructions_calls += 1
            raise AssertionError("tampered evidence must not reach Instructions")

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                instructions=forbidden_instructions,
            ),
            make=self.make_job,
            playtest=tampering_playtest,
            runtime_root=self.root / "tampered-playtest-runtime",
        )
        with self.assertRaisesRegex(ContractError, "evidence bytes changed"):
            workshop.run(
                Wish.create("tampered-playtest", "A toy with changed proof bytes"),
                playtest_rounds=1,
            )
        self.assertEqual(instructions_calls, 0)

    def test_instructions_resume_revalidates_sealed_playtest_evidence(self):
        wish = Wish.create("resume-proof", "A top whose proof must stay exact")
        waiting = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                invent=self.invent_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(),
            ),
            runtime_root=self.root / "resume-proof-runtime",
        ).run(wish, playtest_rounds=1)
        self.assertEqual((waiting.status, waiting.job), ("waiting", "instructions"))
        receipt = next(
            (
                self.root
                / "resume-proof-runtime"
                / "runs"
                / wish.product_id
                / "attempts"
            ).glob("playtest-r001-*/workspace/mechanical-receipt.json")
        )
        receipt.write_text('{"computed":false}\n', encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "evidence bytes changed"):
            Workshop(
                self.inventor,
                "moving-machines",
                tools=WorkshopTools(
                    invent=self.invent_job,
                    make=self.make_job,
                    playtest=self.passing_playtest,
                    instructions=DefaultInstructions(site_writer=self.site_writer),
                    deliver=DefaultDeliver(self.fulfiller),
                ),
                runtime_root=self.root / "resume-proof-runtime",
            ).resume_instructions(wish)

    def test_playtest_requires_ai_agent_simulation_evidence(self):
        def non_ai_playtest(context):
            return self._playtest(
                context,
                passed=True,
                ai_simulation=False,
            )

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=self.invent_job),
            make=self.make_job,
            playtest=non_ai_playtest,
            runtime_root=self.root / "non-ai-playtest-runtime",
        )
        result = workshop.run(
            Wish.create("not-ai-proof", "A machine tested without AI players"),
            playtest_rounds=1,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs},
            set(workshop.blueprint.required_capabilities("playtest")),
        )

    def test_invented_game_requires_meaningful_ai_simulation(self):
        invalid = Workshop(
            self.inventor,
            "invented-games",
            tools=WorkshopTools(invent=self.invent_job),
            make=self.make_job,
            playtest=self.passing_playtest,
            runtime_root=self.root / "invalid-invented-runtime",
        ).run(
            Wish.create("new-game-no-proof", "Invent a game for our table"),
            playtest_rounds=2,
        )
        self.assertEqual((invalid.status, invalid.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in invalid.needs},
            {"game-simulation"},
        )

        valid = Workshop(
            self.inventor,
            "invented-games",
            tools=self.complete_tools(self.passing_invented_playtest),
            runtime_root=self.root / "valid-invented-runtime",
        ).run(
            Wish.create("new-game-with-proof", "Invent a game for our table"),
            playtest_rounds=1,
        )
        self.assertEqual((valid.status, valid.job, valid.round), ("delivered", "deliver", 1))

    def test_preview_preserves_wish_taste_and_playful_rule(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            runtime_root=self.runtime,
        )
        preview = workshop.preview(Wish.create("kinetic-cable", "A cable holder"))
        self.assertEqual(preview["blueprint"]["lane"], "moving-machines")
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)
        self.assertIn("merely useful", preview["brief"]["utility_rule"])
        self.assertIn("Cool beats cute", preview["brief"]["tone"])


if __name__ == "__main__":
    unittest.main()
