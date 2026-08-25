import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.agent_invent import (
    InventResearch,
    InventResearchSource,
    _science_relevance_record,
)
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.errors import ContractError
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.invented_game import (
    GAME_CONTRACT_PATH,
    GAME_RULES_PATH,
    GAME_SIMULATOR_PATH,
    GAME_SIMULATOR_SOURCE,
    canonical_json_bytes,
    game_rules_document,
)
from inventor_workshop.jobs import (
    Delivered,
    Invented,
    Made,
    Need,
    Playtested,
    WaitingFor,
)
from inventor_workshop.make import Wish
from inventor_workshop.manager import register_workshop_engine
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.playtest_release import (
    CapabilityReleaseProof,
    ReleaseProofSource,
)
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
from tests.test_toy_workshop import (
    fixture_game_contract,
    fixture_game_release_documents,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_SHA256 = "c" * 64
FIXED_TIME = "2026-08-25T12:00:00+00:00"
CANONICAL_PROFILES = {
    "alice": "classics-made-yours",
    "bob": "moving-machines",
    "eve": "little-worlds",
    "ivy": "holdable-science",
    "leo": "invented-games",
}


def load_profile(inventor_id):
    path = ROOT / "inventors" / inventor_id / "profile.py"
    spec = importlib.util.spec_from_file_location(
        "ownership_matrix_%s" % inventor_id, path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class DeterministicWorkshopFakes:
    """One set of shared workers, parameterized only by bound Workshop inputs."""

    def __init__(self, case, inventor_id, lane, wish, taste_sha256):
        self.case = case
        self.inventor_id = inventor_id
        self.lane = lane
        self.wish = wish
        self.wish_sha256 = canonical_sha256(wish.to_dict())
        self.taste_sha256 = taste_sha256
        self.calls = []

    def tools(self, *, instructions=None):
        return WorkshopTools(
            invent=self.invent,
            make=self.make,
            playtest=self.playtest,
            instructions=instructions or self.instructions,
            deliver=self.deliver,
        )

    def _record(self, stage, context):
        self.case.assertEqual(context.wish.to_dict(), self.wish.to_dict())
        self.case.assertEqual(
            context.wish.context["manager_assignment"]["inventor_id"],
            self.inventor_id,
        )
        self.case.assertEqual(
            context.wish.context["manager_assignment"]["assignment_sha256"],
            "a" * 64,
        )

        taste_sha256 = None
        if hasattr(context, "taste"):
            taste_sha256 = context.taste.sha256
            self.case.assertEqual(taste_sha256, self.taste_sha256)
            self.case.assertEqual(context.taste.path.parent.name, self.inventor_id)

        lane = None
        if hasattr(context, "blueprint"):
            lane = context.blueprint.lane
            self.case.assertEqual(lane, self.lane)

        made = getattr(context, "made", None)
        if made is not None:
            self.case.assertEqual(made.product["wish_sha256"], self.wish_sha256)
            self.case.assertEqual(made.product["taste_sha256"], self.taste_sha256)
            self.case.assertEqual(made.product["inventor_id"], self.inventor_id)
            self.case.assertEqual(made.product["lane"], self.lane)
            taste_sha256 = taste_sha256 or made.product["taste_sha256"]
            lane = lane or made.product["lane"]

        explicit_inventor_id = getattr(context, "inventor_id", None)
        if explicit_inventor_id is not None:
            self.case.assertEqual(explicit_inventor_id, self.inventor_id)

        # The exact assignment identity is in the immutable Wish at every stage;
        # Make additionally receives the engine's explicit operational identity.
        observed_inventor_id = (
            explicit_inventor_id
            or (made.product["inventor_id"] if made is not None else None)
            or context.wish.context["manager_assignment"]["inventor_id"]
        )
        self.case.assertEqual(observed_inventor_id, self.inventor_id)
        self.case.assertEqual(taste_sha256, self.taste_sha256)
        self.case.assertEqual(lane, self.lane)
        self.calls.append(
            {
                "stage": stage,
                "wish": context.wish.to_dict(),
                "taste_sha256": taste_sha256,
                "lane": lane,
                "inventor_id": observed_inventor_id,
            }
        )

    def invent(self, context):
        self._record("invent", context)
        concept = {
            "title": "%s ownership fixture" % self.inventor_id.title(),
            "summary": "A deterministic industrial-design handoff for the shared engine.",
            "bindings": {
                "wish_sha256": self.wish_sha256,
                "taste_sha256": self.taste_sha256,
                "lane": self.lane,
                "inventor_id": self.inventor_id,
            },
        }
        if self.lane == "little-worlds":
            self.case.assertIsInstance(context.world_inputs, WorldInventInputs)
            concept["lane_contract"] = {
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
            }
        if self.lane == "invented-games":
            concept["lane_contract"] = fixture_game_contract()
        return Invented(
            wish_sha256=self.wish_sha256,
            taste_sha256=self.taste_sha256,
            lane=self.lane,
            concept=concept,
            score=95,
            target_score=90,
        )

    def make(self, context):
        self._record("make", context)
        self.case.assertEqual(
            context.invented.concept["bindings"],
            {
                "wish_sha256": self.wish_sha256,
                "taste_sha256": self.taste_sha256,
                "lane": self.lane,
                "inventor_id": self.inventor_id,
            },
        )
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        science_scale = {
            "real_quantity": "one observation",
            "model_quantity": "one action",
            "scale_ratio": 1,
            "units": "observations per action",
        }
        science_interaction = {
            "user_action": "Move the fixture once.",
            "observable_response": "Watch one observation appear.",
            "teaching_point": "fixture motion",
            "misuse_boundary": "not physical evidence",
        }
        canonical_scale = json.dumps(
            science_scale, sort_keys=True, separators=(",", ":")
        )
        science_source_bytes = (
            "fixture motion\n"
            "one action produces one observation\n"
            + canonical_scale
            + "\nbounded state; not physical evidence\n"
            "one observation; not continuous time"
        ).encode("utf-8")
        science_binding = None
        if self.lane == "holdable-science":
            research = InventResearch(
                self.wish_sha256,
                self.taste_sha256,
                context.blueprint.sha256,
                self.lane,
                "ownership-invent-science",
                "1.0.0",
                "7" * 64,
                (
                    InventResearchSource(
                        "fixture-source",
                        "Ownership fixture source",
                        "Fixture Observatory",
                        "https://example.org/ownership-science",
                        "2026-08-25T00:00:00Z",
                        science_source_bytes.decode("utf-8"),
                        ("prior-art", "use-context", "science"),
                    ),
                    InventResearchSource(
                        "fixture-safety",
                        "Ownership fixture safety",
                        "Fixture Safety Office",
                        "https://example.org/ownership-safety",
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
                "content_scope": "Exact provider-observed ownership fixture excerpts.",
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
        files = {
            "toy.step": "ISO-10303-21; deterministic ownership fixture\n",
            "part_body.stl": "solid body\nendsolid body\n",
            "wish.json": json.dumps(context.wish.to_dict(), sort_keys=True) + "\n",
            "edition-rules.json": '{"known_game":"fixture classic","rules_reference":"https://example.org/fixture-rules","known_rules":["one legal turn"]}\n',
            "source-model.json": json.dumps(
                {
                    "source_model": {
                        "phenomenon": "fixture motion",
                        "model": "one action produces one observation",
                        "source_ids": ["fixture-source"],
                    },
                    "simplifications": [
                        {
                            "simplification": "bounded state",
                            "reason": "deterministic fixture",
                            "disclosed_limit": "not physical evidence",
                        },
                        {
                            "simplification": "one observation",
                            "reason": "legible fixture",
                            "disclosed_limit": "not continuous time",
                        },
                    ],
                    "scale": science_scale,
                    "interaction": science_interaction,
                    "invent_science_research": science_binding,
                },
                sort_keys=True,
            )
            + "\n",
            "personalization-map.json": json.dumps(
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
            "role_a.step": "STEP role a\n",
            "role_a.stl": "solid role_a\nendsolid role_a\n",
            "role_b.step": "STEP role b\n",
            "role_b.stl": "solid role_b\nendsolid role_b\n",
            "game-rules.json": '{"end":"finite","legal_actions":["play"]}\n',
            "simulator.py": (
                "def play(seed):\n"
                "    return {'seed': seed, 'completed': True, 'turns': 1}\n"
            ),
        }
        for relative, payload in files.items():
            (artifact / relative).write_text(payload, encoding="utf-8")
        if self.lane == "invented-games":
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
                title="Leo ownership fixture",
                theme="A deterministic ownership-matrix rhythm game.",
            )
            (artifact / GAME_RULES_PATH).write_text(
                json.dumps(rules, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (artifact / GAME_SIMULATOR_PATH).write_text(
                GAME_SIMULATOR_SOURCE,
                encoding="utf-8",
            )
        product = {
            "schema_version": 1,
            "kind": "workshop-ownership-fixture",
            "product_id": context.wish.product_id,
            "title": "%s ownership fixture" % self.inventor_id.title(),
            "summary": "A deterministic product from the shared mechanical-design worker.",
            "description": "An exact shared-stage ownership fixture.",
            "lane": self.lane,
            "inventor_id": self.inventor_id,
            "wish_sha256": self.wish_sha256,
            "taste_sha256": self.taste_sha256,
            "wish": context.wish.to_dict(),
            "instructions": (
                "fixture motion; not physical evidence"
                if self.lane == "holdable-science"
                else "Use the exact deterministic fixture as described."
            ),
            "components": ["one fixture body"],
            "limitations": ["Contract fixture; not human-use evidence."],
        }
        (artifact / "product.json").write_text(
            json.dumps(product, sort_keys=True) + "\n", encoding="utf-8"
        )
        return Made.from_root(artifact, product)

    @staticmethod
    def _write_json(root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return relative, hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _write_bytes(root, relative, payload):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return relative, hashlib.sha256(payload).hexdigest(), len(payload)

    @staticmethod
    def _source(role, scope, path, sha256):
        return ReleaseProofSource(role, scope, path, sha256)

    def _canonical_receipt(
        self,
        context,
        *,
        capability,
        proof_class,
        role,
        dependencies,
        measurements,
        payload,
    ):
        return self._write_json(
            context.workspace,
            "proof/%s.json" % role,
            {
                "schema_version": 1,
                "kind": "workshop.capability-release-receipt",
                "artifact_sha256": context.made.artifact_sha256,
                "capability": capability,
                "proof_class": proof_class,
                "role": role,
                "source_sha256": {
                    "%s:%s" % (item.scope, item.path): item.sha256
                    for item in dependencies
                },
                "measurements": measurements,
                "payload": payload,
            },
        )

    def _release_proof(self, capability, context, product_inventory):
        artifact_sha256 = context.made.artifact_sha256
        source = self._source
        write_json = lambda name, value: self._write_json(
            context.workspace, name, value
        )

        if capability == "mechanical-test":
            proof_class = "computed-mechanical-proof"
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
            step_source = source(
                "step-model",
                "product",
                "toy.step",
                product_inventory["toy.step"],
            )
            receipt, receipt_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="mechanical-receipt",
                dependencies=(step_source,),
                measurements=measurements,
                payload={
                    "method": "deterministic ownership-matrix mechanical fixture",
                    "checks": ["brep", "fit", "assembly", "load"],
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    step_source,
                    source("mechanical-receipt", "playtest", receipt, receipt_sha256),
                ),
                measurements,
            )

        if capability == "print-test":
            proof_class = "exact-slicer-proof"
            part_source = source(
                "print-part",
                "product",
                "part_body.stl",
                product_inventory["part_body.stl"],
            )
            profile_sources = []
            profiles = {}
            for role, payload in (
                ("printer", b"printer_technology = FFF\nnozzle_diameter = 0.4\n"),
                ("process", b"layer_height = 0.2\nperimeters = 3\n"),
                ("filament", b"filament_type = PLA\ntemperature = 210\n"),
            ):
                path, digest, unused_bytes = self._write_bytes(
                    context.workspace,
                    "proof/profiles/%s.ini" % role,
                    payload,
                )
                del unused_bytes
                profile_sources.append(
                    source("slicer-profile", "playtest", path, digest)
                )
                profiles[role] = {"path": path, "sha256": digest}
            gcode_payload = (
                b"; generated by PrusaSlicer 2.9.6\n"
                b"G90\n"
                b"G1 X1.0 Y1.0 E0.1\n"
            )
            gcode_ref, gcode_sha256, gcode_bytes = self._write_bytes(
                context.workspace,
                "proof/gcode/part_body.gcode",
                gcode_payload,
            )
            gcode_source = source(
                "gcode-output", "playtest", gcode_ref, gcode_sha256
            )
            measurements = {
                "slicer": "PrusaSlicer",
                "slicer_version": "2.9.6",
                "profiles": profiles,
                "parts": [
                    {
                        "input_ref": "part_body.stl",
                        "input_sha256": product_inventory["part_body.stl"],
                        "gcode_ref": gcode_ref,
                        "gcode_sha256": gcode_sha256,
                        "gcode_bytes": gcode_bytes,
                        "returncode": 0,
                    }
                ],
                "slicer_errors": 0,
            }
            dependencies = (
                part_source,
                *profile_sources,
                gcode_source,
            )
            receipt, receipt_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="slicer-receipt",
                dependencies=dependencies,
                measurements=measurements,
                payload={
                    "command": "PrusaSlicer --export-gcode part_body.stl",
                    "returncode": 0,
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    *dependencies,
                    source("slicer-receipt", "playtest", receipt, receipt_sha256),
                ),
                measurements,
            )

        if capability == "motion-test":
            proof_class = "kinematic-motion-proof"
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
            step_source = source(
                "step-model",
                "product",
                "toy.step",
                product_inventory["toy.step"],
            )
            receipt, receipt_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="motion-receipt",
                dependencies=(step_source,),
                measurements=measurements,
                payload={
                    "method": "deterministic ownership-matrix motion fixture",
                    "sweeps": 10,
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    step_source,
                    source("motion-receipt", "playtest", receipt, receipt_sha256),
                ),
                measurements,
            )

        if capability == "classic-rules-test":
            proof_class = "classic-rule-conformance-proof"
            provider = {
                "name": "ownership-classic-provider",
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
            edition_source = source(
                "edition-rules",
                "product",
                "edition-rules.json",
                product_inventory["edition-rules.json"],
            )
            role_sources = (
                source("edition-part-step", "product", "role_a.step", product_inventory["role_a.step"]),
                source("edition-part-stl", "product", "role_a.stl", product_inventory["role_a.stl"]),
                source("edition-part-step", "product", "role_b.step", product_inventory["role_b.step"]),
                source("edition-part-stl", "product", "role_b.stl", product_inventory["role_b.stl"]),
            )
            dependencies = (edition_source, *role_sources)
            rules_model = {
                "schema_version": 1,
                "game": "fixture classic",
                "rules": ["one legal turn"],
            }
            reference, reference_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="reference-rules",
                dependencies=dependencies,
                measurements=measurements,
                payload={
                    "provider": provider,
                    "rules_model": rules_model,
                    "rules_model_sha256": hashlib.sha256(
                        json.dumps(rules_model, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                    "comparison": {
                        "declaration_known_game": "fixture classic",
                        "rules_reference": "https://example.org/fixture-rules",
                        "no_rule_mutation_fields": True,
                    },
                    "conformance_cases": [
                        {"case_id": "rule-1", "passed": True, "source": "fixture"},
                        {"case_id": "rule-2", "passed": True, "source": "fixture"},
                        {"case_id": "rule-3", "passed": True, "source": "fixture"},
                    ],
                },
            )
            geometry_a = {"shape": "cylinder", "size_mm": {"x": 20.0, "y": 20.0, "z": 6.0}}
            geometry_b = {"shape": "cylinder", "size_mm": {"x": 18.0, "y": 18.0, "z": 8.0}}
            traces, traces_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="game-traces",
                dependencies=dependencies,
                measurements=measurements,
                payload={
                    "provider": provider,
                    "games": [{"seed": 1, "completed": True, "rule_mismatches": 0}],
                    "role_cases": [
                        {
                            "part_id": "role-a",
                            "geometry": geometry_a,
                            "geometry_sha256": hashlib.sha256(json.dumps(geometry_a, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                            "step_path": "role_a.step",
                            "step_sha256": product_inventory["role_a.step"],
                            "stl_path": "role_a.stl",
                            "stl_sha256": product_inventory["role_a.stl"],
                            "exact_body_bound": True,
                        },
                        {
                            "part_id": "role-b",
                            "geometry": geometry_b,
                            "geometry_sha256": hashlib.sha256(json.dumps(geometry_b, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
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
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    edition_source,
                    *role_sources,
                    source("reference-rules", "playtest", reference, reference_sha256),
                    source("game-traces", "playtest", traces, traces_sha256),
                ),
                measurements,
            )

        if capability == "science-test":
            proof_class = "source-bound-science-proof"
            provider = {
                "name": "ownership-science-provider",
                "version": "1.0.0",
                "config_sha256": "2" * 64,
                "method_class": "source-bound-comparison",
            }
            source_bytes = (
                b"fixture motion\n"
                b"one action produces one observation\n"
                + json.dumps(
                    {
                        "real_quantity": "one observation",
                        "model_quantity": "one action",
                        "scale_ratio": 1,
                        "units": "observations per action",
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
                b"bounded state; not physical evidence\n"
                b"one observation; not continuous time"
            )
            source_model = {
                "phenomenon": "fixture motion",
                "model": "one action produces one observation",
                "source_ids": ["fixture-source"],
            }
            simplifications = [
                {
                    "simplification": "bounded state",
                    "reason": "deterministic fixture",
                    "disclosed_limit": "not physical evidence",
                },
                {
                    "simplification": "one observation",
                    "reason": "legible fixture",
                    "disclosed_limit": "not continuous time",
                },
            ]
            scale = {
                "real_quantity": "one observation",
                "model_quantity": "one action",
                "scale_ratio": 1,
                "units": "observations per action",
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
            model_source = source(
                "source-model",
                "product",
                "source-model.json",
                product_inventory["source-model.json"],
            )
            wish_source = source(
                "wish-context",
                "product",
                "wish.json",
                product_inventory["wish.json"],
            )
            product_source = source(
                "product-copy",
                "product",
                "product.json",
                product_inventory["product.json"],
            )
            research_source = source(
                "invent-research",
                "product",
                research_path,
                product_inventory[research_path],
            )
            sources, sources_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="science-sources",
                dependencies=(model_source, wish_source, product_source, research_source),
                measurements=measurements,
                payload={
                    "provider": provider,
                    "source_model_sha256": hashlib.sha256(json.dumps(source_model, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                    "invent_research_file_sha256": product_inventory[research_path],
                    "invent_research_sha256": research_document["research_sha256"],
                    "sources": [
                        {
                            "source_id": "fixture-source",
                            "title": "Ownership fixture source",
                            "publisher": "Fixture Observatory",
                            "url": "https://example.org/ownership-science",
                            "retrieved_at": "2026-08-25T00:00:00Z",
                            "media_type": "text/plain",
                            "content_sha256": hashlib.sha256(source_bytes).hexdigest(),
                            "content_bytes": len(source_bytes),
                            "content_encoding": "base64",
                            "content_base64": base64.b64encode(source_bytes).decode("ascii"),
                        }
                    ],
                    "accuracy_cases": [
                        {"case_id": "phenomenon-1", "source_ids": ["fixture-source"], "product_field": "phenomenon", "expected": source_model["phenomenon"], "observed": source_model["phenomenon"], "source_excerpt": source_model["phenomenon"], "source_excerpt_sha256": hashlib.sha256(source_model["phenomenon"].encode("utf-8")).hexdigest(), "passed": True},
                        {"case_id": "model-1", "source_ids": ["fixture-source"], "product_field": "model", "expected": source_model["model"], "observed": source_model["model"], "source_excerpt": source_model["model"], "source_excerpt_sha256": hashlib.sha256(source_model["model"].encode("utf-8")).hexdigest(), "passed": True},
                        {"case_id": "scale-1", "source_ids": ["fixture-source"], "product_field": "scale", "expected": canonical_scale, "observed": canonical_scale, "source_excerpt": canonical_scale, "source_excerpt_sha256": hashlib.sha256(canonical_scale.encode("utf-8")).hexdigest(), "passed": True},
                    ],
                    "simplification_checks": [
                        {
                            "simplification_sha256": hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                            "source_ids": ["fixture-source"],
                            "disclosed_limit_present": True,
                            "source_supported": True,
                            "source_excerpt": "%s; %s" % (item["simplification"], item["disclosed_limit"]),
                            "source_excerpt_sha256": hashlib.sha256(("%s; %s" % (item["simplification"], item["disclosed_limit"])).encode("utf-8")).hexdigest(),
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
            traces, traces_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="content-coverage-traces",
                dependencies=(model_source, wish_source, product_source, research_source),
                measurements=measurements,
                payload={
                    "provider": provider,
                    "measurement_kind": "deterministic-product-text-coverage",
                    "traces": [
                        {
                            "seed": 1,
                            "measurement_kind": "deterministic-product-text-coverage",
                            "required_text": ["fixture motion", "not physical evidence"],
                            "recovered_text": ["fixture motion", "not physical evidence"],
                            "passed": True,
                        }
                    ],
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    model_source,
                    wish_source,
                    product_source,
                    research_source,
                    source("science-sources", "playtest", sources, sources_sha256),
                    source(
                        "content-coverage-traces",
                        "playtest",
                        traces,
                        traces_sha256,
                    ),
                ),
                measurements,
            )

        if capability == "world-test":
            proof_class = "reference-bound-world-proof"
            self.case.assertIsInstance(
                context.world_evidence, WorldPlaytestEvidence
            )
            self.case.assertIsInstance(context.world_inputs, WorldInventInputs)
            manager_evidence = context.world_evidence
            manager_reference = manager_evidence.references[0]
            manager_scope = context.world_inputs.references[0].scope
            provider = {
                "name": manager_evidence.provider.provider_id,
                "version": manager_evidence.provider.version,
                "config_sha256": manager_evidence.provider.config_sha256,
                "method_class": "independent-private-reference-measurement",
            }
            material_sha256 = manager_reference.content_sha256
            manager_binding = {
                "world_evidence_sha256": manager_evidence.evidence_sha256,
                "world_inputs_sha256": context.world_inputs.binding_sha256,
                "provider_attestation": dict(manager_evidence.provider_attestation),
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
            measurements = {
                "scope_record_authenticated": True,
                "personalization_features": 1,
                "likeness_cases": 1,
                "recognition_failures": 0,
                "scope_violations": 0,
            }
            map_source = source(
                "personalization-map",
                "product",
                "personalization-map.json",
                product_inventory["personalization-map.json"],
            )
            consent, consent_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="consent-record",
                dependencies=(map_source,),
                measurements=measurements,
                payload={
                    "attestation": provider,
                    "attestation_scope": "authenticated customer/operator scope record; not legal consent or ownership proof; raw bytes are intentionally not public-replayable",
                    "records": [
                        {
                            "reference_id": manager_reference.reference_id,
                            "subject": manager_scope.subject,
                            "rights_basis": manager_scope.rights_basis,
                            "allowed_features": list(manager_scope.allowed_features),
                            "excluded_features": list(manager_scope.excluded_features),
                            "verification_method": manager_reference.scope_authentication_method,
                            "verified_at": manager_reference.observed_at,
                            "consent_sha256": manager_reference.declaration_sha256,
                            "consent_bytes": manager_reference.declaration_bytes,
                        }
                    ],
                    "raw_scope_record_bytes_included": False,
                    **manager_binding,
                },
            )
            reference, reference_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="reference-material",
                dependencies=(map_source,),
                measurements=measurements,
                payload={
                    "attestation": provider,
                    "attestation_scope": "isolated provider measurement over admitted private-reference digests; raw bytes are intentionally not public-replayable",
                    "references": [
                        {
                            "reference_id": manager_reference.reference_id,
                            "media_type": manager_reference.media_type,
                            "content_sha256": material_sha256,
                            "content_bytes": manager_reference.content_bytes,
                            "reference_bytes_included": False,
                        }
                    ],
                    "raw_reference_bytes_included": False,
                    **manager_binding,
                },
            )
            traces, traces_sha256 = self._canonical_receipt(
                context,
                capability=capability,
                proof_class=proof_class,
                role="likeness-traces",
                dependencies=(map_source,),
                measurements=measurements,
                payload={
                    "attestation": provider,
                    "cases": [
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
                    ],
                    **manager_binding,
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                proof_class,
                (
                    map_source,
                    source("consent-record", "playtest", consent, consent_sha256),
                    source(
                        "reference-material",
                        "playtest",
                        reference,
                        reference_sha256,
                    ),
                    source("likeness-traces", "playtest", traces, traces_sha256),
                ),
                measurements,
            )

        if capability == "game-simulation":
            measurements, trace_document, analysis_document = (
                fixture_game_release_documents(
                    artifact_sha256,
                    fixture_game_contract(),
                    product_inventory,
                )
            )
            traces, traces_sha256 = write_json(
                "proof/game-traces.json",
                trace_document,
            )
            analysis, analysis_sha256 = write_json(
                "proof/game-analysis.json",
                analysis_document,
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "seeded-game-analysis-proof",
                (
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
                ),
                measurements,
            )

        raise AssertionError("unexpected release capability %s" % capability)

    def playtest(self, context):
        if self.lane == "little-worlds" and context.world_evidence is None:
            raise WaitingFor(
                Need(
                    "playtest",
                    "world-test",
                    "The exact Make needs independent Manager world evidence.",
                    "Evaluate this artifact outside the Inventor and resume it.",
                )
            )
        self._record("playtest", context)
        context.workspace.mkdir(parents=True)
        product_inventory = {
            entry.path: entry.sha256
            for entry in context.made.artifact_manifest.entries
        }
        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence = {
                "evidence_class": "ai-simulation",
                "artifact_sha256": context.made.artifact_sha256,
                "agent_roles": ["optimizing-player", "adversarial-breaker"],
                "claims": ["Deterministic shared evidence for %s." % capability],
            }
            if capability != "agent-playtest":
                evidence["release_proof"] = self._release_proof(
                    capability, context, product_inventory
                ).to_dict()
            evidence_ref, evidence_sha256 = self._write_json(
                context.workspace,
                "results/%s.json" % capability,
                evidence,
            )
            results.append(
                PlaytestResult(
                    capability,
                    True,
                    context.made.artifact_sha256,
                    evidence,
                    "deterministic-shared-playtest",
                    "1.0.0",
                    CONFIG_SHA256,
                    evidence_ref,
                    evidence_sha256,
                    FIXED_TIME,
                )
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=build_artifact_manifest(
                    context.workspace, created_at="content-addressed"
                ),
            )
        )

    def _site_writer(self, context, sealed_root, sealed_manifest):
        del sealed_root
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-" + context.wish.product_id,
            slug=context.wish.product_id,
            owner_id="owner-" + self.inventor_id,
            root_id="design-" + context.wish.product_id,
            current_history_id="history-1",
            published_history_id=None,
            status="draft",
            project_url="https://cdn.autonomous.ai/projects/history-1/",
            observed_at=FIXED_TIME,
            details={
                "instructions_sha256": sealed_manifest.artifact_sha256,
                "page_url": (
                    "https://www.autonomous.ai/factory/product/"
                    + context.wish.product_id
                ),
            },
        )

    def instructions(self, context):
        self._record("instructions", context)
        return DefaultInstructions(site_writer=self._site_writer)(context)

    def deliver(self, context):
        self._record("deliver", context)
        return DefaultDeliver(
            lambda selected: Delivered(
                selected.made.artifact_sha256,
                selected.instructions.instructions_sha256,
                "UPS",
                "Ground",
                "1Z999AA10123456784",
                "handed-off",
                FIXED_TIME,
                fixture_delivery_evidence(
                    selected.made.artifact_sha256,
                    selected.instructions.instructions_sha256,
                    carrier="UPS",
                    service="Ground",
                    tracking_id="1Z999AA10123456784",
                    observed_at=FIXED_TIME,
                ),
            )
        )(context)


class SharedEngineOwnershipMatrixTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def exact_wish(inventor_id, product_id):
        objective = "I wish for a pocket toy\nthat keeps the midnight-blue hinge exactly."
        if inventor_id == "ivy":
            objective = (
                "I wish for a pocket fixture-motion toy\n"
                "that keeps the midnight-blue hinge exactly."
            )
        return Wish.create(
            product_id,
            objective,
            constraints={
                "maximum_mm": [90, 70, 25],
                "must_keep": ["hinge", "midnight blue"],
                "audience": {"minimum_age": 14, "locale": "vi-VN"},
            },
            context={
                "customer": {"name": "Example Customer", "locale": "vi-VN"},
                "manager_assignment": {
                    "inventor_id": inventor_id,
                    "decision_sha256": "d" * 64,
                    "assignment_sha256": "a" * 64,
                },
            },
        )

    @staticmethod
    def world_inputs(wish):
        wish_sha256 = canonical_sha256(wish.to_dict())
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
    def world_evidence(wish, artifact_sha256, inputs):
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
            canonical_sha256(wish.to_dict()),
            artifact_sha256,
            canonical_sha256(personalization),
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
            {"attestation_sha256": "8" * 64},
        )

    def fixture_for(self, inventor_id, lane, wish, runtime_name):
        profile = load_profile(inventor_id)
        runtime_root = self.root / runtime_name
        preview_workshop = profile.build_workshop(runtime_root=runtime_root)
        fixture = DeterministicWorkshopFakes(
            self,
            inventor_id,
            lane,
            wish,
            preview_workshop.taste.sha256,
        )
        return profile, fixture, runtime_root

    def assert_exact_matrix(self, fixture):
        self.assertEqual(
            [call["stage"] for call in fixture.calls],
            ["invent", "make", "playtest", "instructions", "deliver"],
        )
        for call in fixture.calls:
            self.assertEqual(call["wish"], fixture.wish.to_dict())
            self.assertEqual(call["taste_sha256"], fixture.taste_sha256)
            self.assertEqual(call["lane"], fixture.lane)
            self.assertEqual(call["inventor_id"], fixture.inventor_id)

    def test_all_five_taste_only_profiles_use_every_shared_stage(self):
        for inventor_id, lane in CANONICAL_PROFILES.items():
            with self.subTest(inventor_id=inventor_id):
                wish = self.exact_wish(inventor_id, "matrix-" + inventor_id)
                profile, fixture, runtime_root = self.fixture_for(
                    inventor_id, lane, wish, "all-shared-" + inventor_id
                )
                workshop = profile.build_workshop(
                    trusted_engine=register_workshop_engine(fixture.tools()),
                    runtime_root=runtime_root,
                    max_rounds=1,
                    **(
                        {"world_inputs": self.world_inputs(wish)}
                        if inventor_id == "eve"
                        else {}
                    ),
                )

                result = workshop.run(wish, playtest_rounds=1)
                if inventor_id == "eve":
                    self.assertEqual((result.status, result.job), ("waiting", "playtest"))
                    world_inputs = workshop.world_inputs
                    world_evidence = self.world_evidence(
                        wish, result.artifact_sha256, world_inputs
                    )
                    workshop = profile.build_workshop(
                        trusted_engine=register_workshop_engine(fixture.tools()),
                        runtime_root=runtime_root,
                        max_rounds=1,
                        world_inputs=world_inputs,
                        world_evidence=world_evidence,
                    )
                    result = workshop.resume(wish)

                self.assertEqual(workshop.customization_level, "taste-only")
                self.assertEqual(workshop.inventor_id, inventor_id)
                self.assertEqual(workshop.lane, lane)
                self.assertEqual(result.status, "delivered")
                self.assertEqual(result.job, "deliver")
                self.assertIsNotNone(result.delivery)
                self.assert_exact_matrix(fixture)

    def test_built_in_taste_only_profiles_reject_undeclared_substitution(self):
        for inventor_id, lane in CANONICAL_PROFILES.items():
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                root = ROOT / "inventors" / inventor_id
                runtime = self.root / ("hostile-" + inventor_id)
                forbidden = lambda context: context
                with self.assertRaisesRegex(
                    ContractError, "do not match its declared taste-only level"
                ):
                    Workshop(
                        root,
                        lane,
                        make=forbidden,
                        runtime_root=runtime,
                    )
                with self.assertRaisesRegex(
                    ContractError,
                    "manifested Inventors cannot supply raw WorkshopTools",
                ):
                    Workshop(
                        root,
                        lane,
                        tools=WorkshopTools(invent=forbidden),
                        runtime_root=runtime,
                    )
                self.assertNotIn("tools", profile.build_workshop.__annotations__)

    def test_missing_external_provider_waits_on_a_shared_capability(self):
        wish = self.exact_wish("alice", "matrix-shared-site-wait")
        profile, fixture, runtime_root = self.fixture_for(
            "alice", "classics-made-yours", wish, "shared-site-wait"
        )

        def shared_instructions_without_site_provider(context):
            fixture._record("instructions", context)
            return DefaultInstructions()(context)

        workshop = profile.build_workshop(
            trusted_engine=register_workshop_engine(
                fixture.tools(instructions=shared_instructions_without_site_provider)
            ),
            runtime_root=runtime_root,
            max_rounds=1,
        )
        result = workshop.run(wish, playtest_rounds=1)

        self.assertEqual(result.status, "waiting")
        self.assertEqual(result.job, "instructions")
        self.assertEqual([need.capability for need in result.needs], ["site-page"])
        self.assertEqual(
            [call["stage"] for call in fixture.calls],
            ["invent", "make", "playtest", "instructions"],
        )
        for need in result.needs:
            rendered = json.dumps(need.to_dict()).casefold()
            self.assertNotIn("alice", rendered)
            self.assertNotIn("inventor-specific", rendered)
            self.assertIn("shared", rendered)


if __name__ == "__main__":
    unittest.main()
