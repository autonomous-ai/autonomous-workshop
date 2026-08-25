import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.agent_make import (
    MAKE_GENERATOR_ID,
    MAKE_GENERATOR_VERSION,
    CadSkillBuild,
    CodexMaker,
    LockedCadSkillBuilder,
    _MAKE_SCHEMA,
    _validate_action,
)
from inventor_workshop.agent_invent import InventResearch, InventResearchSource
from inventor_workshop.errors import ArtifactError
from inventor_workshop.jobs import (
    InventContext,
    Invented,
    MakeContext,
    PlaytestContext,
    Playtested,
    WaitingFor,
)
from inventor_workshop.lane_playtest_providers import WorkshopLanePlaytestProviders
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest
from inventor_workshop.playtest_release import playtest_release_needs
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.sealed_draft import _load_artifact_contract
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


def make_action(title="Orbit Press", *, overlap=False):
    second_x = 30 if overlap else 78
    return {
        "title": title,
        "summary": "A Wish-shaped desktop press assembled from three bold printable parts.",
        "interaction": "Turn the round handle and slide the marker through a short track.",
        "mechanical_principle": "A hand-turned wheel gives a tactile index for a separate sliding marker.",
        "assembly": [
            "Place the base on a stable table.",
            "Seat the wheel and marker in their labelled positions after printing.",
        ],
        "instructions": "Arrange the three printed pieces as shown, turn the wheel, and move the marker one station per turn.",
        "parts": [
            {
                "part_id": "base",
                "name": "one base",
                "purpose": "Supports the desktop interaction.",
                "shape": "box",
                "size_mm": {"x": 48, "y": 36, "z": 5},
                "print_center_mm": {"x": 28, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "index-wheel",
                "name": "one index wheel",
                "purpose": "Provides the hand-turned index.",
                "shape": "cylinder",
                "size_mm": {"x": 30, "y": 30, "z": 6},
                "print_center_mm": {"x": second_x, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 8},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "marker",
                "name": "one sliding marker",
                "purpose": "Marks progress through the interaction.",
                "shape": "cylinder",
                "size_mm": {"x": 14, "y": 14, "z": 8},
                "print_center_mm": {"x": 108, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 122, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
        ],
        "classic_spec": {
            "enabled": False,
            "known_game": "not applicable",
            "rules_reference": "not applicable",
            "rules_unchanged": False,
        },
        "game_spec": {
            "enabled": False,
            "resource_part_ids": [],
        },
        "motion_spec": {
            "enabled": True,
            "moving_part_id": "index-wheel",
            "axis": "z",
            "sweep_degrees": 360,
            "minimum_aabb_clearance_mm": 1,
        },
        "moving_machine_binding": {
            "joint": {
                "joint_id": "index-wheel-joint",
                "kind": "rigid-revolute-z",
                "moving_part_id": "index-wheel",
                "support_part_ids": ["base"],
                "obstacle_part_ids": ["marker"],
                "axis_point_mm": [80.0, 80.0, 8.0],
                "axis_direction": [0.0, 0.0, 1.0],
                "start_deg": 0.0,
                "end_deg": 360.0,
                "steps": 72,
            },
            "tolerance_bindings": [
                {
                    "contract_index": 0,
                    "moving_part_id": "index-wheel",
                    "stationary_part_ids": ["marker"],
                    "verification": "continuous-swept-envelope",
                }
            ],
            "load_bindings": [
                {
                    "contract_index": 0,
                    "loaded_part_id": "index-wheel",
                    "support_part_ids": ["base"],
                    "section_axis": "z",
                    "verification_modes": ["bulk-compression", "direct-shear"],
                }
            ],
            "failure_bindings": [
                {
                    "contract_index": 0,
                    "part_ids": ["base", "index-wheel", "marker"],
                    "load_case_indices": [0],
                    "verification_modes": [
                        "direct-shear",
                        "continuous-clearance",
                        "reverse-sweep",
                        "stall-envelope",
                    ],
                }
            ],
        },
        "design_limitations": [
            "This MVP does not yet model the final axle or sliding fit.",
        ],
    }


def verdict(score, feedback="Ready for digital Make."):
    return {
        "dimensions": {
            "concept_fidelity": score,
            "taste_fit": score,
            "interaction": score,
            "mechanical_coherence": score,
            "manufacturing_review": score,
        },
        "feedback": [feedback],
        "hard_tensions": [],
        "assessment": feedback,
    }


def executable_game_contract():
    return {
        "schema_version": 2,
        "lane": "invented-games",
        "game_protocol": {
            "schema_version": 1,
            "protocol": "workshop.resource-game.v1",
            "players": 2,
            "resources": [
                {"resource_id": "sparks", "label": "spark tokens", "initial": 7}
            ],
            "actions": [
                {
                    "action_id": "take-one",
                    "label": "Take one spark",
                    "removals": [{"resource_id": "sparks", "count": 1}],
                    "points": 0,
                },
                {
                    "action_id": "take-two",
                    "label": "Take two sparks",
                    "removals": [{"resource_id": "sparks", "count": 2}],
                    "points": 0,
                },
                {
                    "action_id": "take-three",
                    "label": "Take three sparks",
                    "removals": [{"resource_id": "sparks", "count": 3}],
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


def game_action():
    value = make_action("Seven Sparks")
    parts = []
    for index in range(7):
        part_id = "spark-%d" % (index + 1)
        parts.append(
            {
                "part_id": part_id,
                "name": "spark token %d" % (index + 1),
                "purpose": "One physical token in the shared finite supply.",
                "shape": "cylinder",
                "size_mm": {"x": 12, "y": 12, "z": 4},
                "print_center_mm": {"x": 14 + index * 18, "y": 18},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 70 + index * 14, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            }
        )
    value["parts"] = parts
    value["game_spec"] = {
        "enabled": True,
        "resource_part_ids": [
            {
                "resource_id": "sparks",
                "part_ids": [part["part_id"] for part in parts],
            }
        ],
    }
    value["motion_spec"] = {
        "enabled": False,
        "moving_part_id": "",
        "axis": "z",
        "sweep_degrees": 1,
        "minimum_aabb_clearance_mm": 0,
    }
    value.pop("moving_machine_binding")
    return value


class FakeCodex:
    cli_version = "9.8.7"
    reasoning_effort = "high"

    def __init__(self, model, outputs):
        self.model = model
        self.outputs = list(outputs)
        self.prompts = []

    def invoke(self, *, prompt, schema, workspace):
        self.prompts.append((prompt, schema, workspace))
        return self.outputs.pop(0)


class FakeCadBuilder:
    """Deterministic fixture for CodexMaker; locked-tool orchestration is tested separately."""

    def ensure_available(self):
        return {"cad": "a" * 64, "product-to-cad": "b" * 64}

    def build(self, action, *, lane, root):
        root.mkdir(parents=True)
        for relative, source in LockedCadSkillBuilder._project_sources(action).items():
            (root / relative).write_text(source, encoding="utf-8")
        stems = ["product", "print_plate"] + [
            "part_" + part["part_id"].replace("-", "_") for part in action["parts"]
        ]
        for stem in stems:
            (root / (stem + ".step")).write_bytes(
                ("ISO-10303-21;\n%s\nEND-ISO-10303-21;\n" % stem).encode("utf-8")
            )
            (root / (stem + ".stl")).write_bytes(
                ("solid %s\nendsolid %s\n" % (stem, stem)).encode("utf-8")
            )
        def bounds(part, pose):
            size = part["size_mm"]
            rotation = math.radians(float(part[pose + "_rotation_deg"]))
            half_x = (
                abs(math.cos(rotation)) * float(size["x"]) / 2
                + abs(math.sin(rotation)) * float(size["y"]) / 2
            )
            half_y = (
                abs(math.sin(rotation)) * float(size["x"]) / 2
                + abs(math.cos(rotation)) * float(size["y"]) / 2
            )
            center = part[pose + "_center_mm"]
            z = float(center.get("z", 0))
            return (
                float(center["x"]) - half_x,
                float(center["x"]) + half_x,
                float(center["y"]) - half_y,
                float(center["y"]) + half_y,
                z,
                z + float(size["z"]),
            )

        forbidden = 0
        for pose in ("print", "assembly"):
            boxes = [bounds(part, pose) for part in action["parts"]]
            for left_index, left in enumerate(boxes):
                for right in boxes[left_index + 1 :]:
                    if all(
                        min(left[axis + 1], right[axis + 1])
                        - max(left[axis], right[axis])
                        > 0
                        for axis in (0, 2, 4)
                    ):
                        forbidden += 1
        passed = forbidden == 0
        issues = [] if passed else [
            "assembly or print-layout pose has a CAD-kernel interference"
        ]
        checks = {
            "manifest": {"status": "passed", "measurements": {"inventory_valid": True}},
            "source-step-identity": {"status": "passed", "measurements": {"matched_outputs": len(action["parts"]) + 2, "mismatches": 0}},
            "brep": {"status": "passed", "measurements": {"valid_solids": len(action["parts"]), "invalid_solids": 0}},
            "dimensions": {"status": "passed", "measurements": {"measured_parts": len(action["parts"]), "out_of_tolerance": 0}},
            "interference": {"status": "passed" if passed else "failed", "measurements": {"poses_tested": 2, "forbidden_intersections": forbidden}},
            "bed-packing": {"status": "passed", "measurements": {"beds_used": 1, "out_of_bounds_parts": 0}},
            "mesh-topology": {"status": "passed", "measurements": {"watertight_parts": len(action["parts"]), "non_manifold_edges": 0}},
            "thickness": {"status": "passed", "measurements": {"parts_measured": len(action["parts"]), "below_minimum": 0}},
        }
        observation = {
            "schema_version": 2,
            "generator": {"id": MAKE_GENERATOR_ID, "version": MAKE_GENERATOR_VERSION},
            "skills": self.ensure_available(),
            "lane": lane,
            "claim_scope": "fixture STEP-first digital checks only",
            "checks": checks,
            "issues": issues,
            "passed": passed,
            "release_ready": False,
            "release_blockers": ["exact slicer profile", "physical QA"],
            "not_proven": [
                "slicer success or support requirements",
                "physical fit, loads, wear, safety, print quality, or motion",
            ],
            "inventory": {},
        }
        (root / "verification").mkdir()
        (root / "verification" / "cad-build.json").write_text(
            json.dumps(observation, sort_keys=True), encoding="utf-8"
        )
        return CadSkillBuild(root.resolve(), observation)


class AgentMakeTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Bob\n"
            "description: Kinetic machines where motion creates the spectacle.\n"
            "---\n"
            "# Bob's Taste\n\nMake motion the magic. Not for static character models.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(self.inventor)
        self.wish = Wish.create(
            "orbit-press",
            "A hand-operated desk toy where a tiny moon advances around my anniversary date",
            constraints={"lane": "moving-machines"},
            context={"inventor_id": "bob"},
        )
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.invented = Invented(
            wish_sha256=json_sha256(self.wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=self.blueprint.lane,
            concept={
                "title": "Anniversary Orbit",
                "summary": "A hand-driven orbital desk toy.",
                "mechanical_handoff": ["Make the advance tactile and visible."],
                "lane_contract": {
                    "schema_version": 1,
                    "lane": "moving-machines",
                    "kinematic_model": {
                        "input_motion": "A person turns the index wheel by hand.",
                        "transmission": ["The rigid wheel turns directly about Z."],
                        "output_motion": "The visible index completes one revolution.",
                        "degrees_of_freedom": 1,
                    },
                    "tolerances_mm": [
                        {
                            "interface": "Wheel swept envelope beside the marker",
                            "nominal_clearance_mm": 1.0,
                            "tolerance_mm": 0.2,
                        }
                    ],
                    "load_assumptions": [
                        {
                            "case": "A user stalls the wheel by hand.",
                            "force_n": 8.0,
                            "safety_factor": 2.0,
                            "basis": "A bounded concept-stage hand-force assumption.",
                        }
                    ],
                    "failure_modes": [
                        {
                            "mode": "Wheel shear or clearance stall",
                            "cause": "The bounded hand load exceeds the section or clearance closes.",
                            "effect": "The wheel stops or its primitive section shears.",
                            "mitigation": "Preserve swept clearance and the checked shear section.",
                        }
                    ],
                },
            },
            score=91,
            target_score=85,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, workspace="make", *, inventor_id="bob"):
        return MakeContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
            inventor_id,
        )

    def durable_context(
        self,
        workspace="make",
        *,
        journal="make-reward-journal",
        inventor_id="bob",
    ):
        return MakeContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
            inventor_id,
            (self.root / journal).absolute(),
        )

    def game_context(self, workspace="game-make"):
        wish = Wish.create(
            "seven-sparks",
            "A tiny strategy game about seven sparks from our first studio",
            constraints={"lane": "invented-games"},
            context={"inventor_id": "leo"},
        )
        blueprint = ToyBlueprint.for_lane("invented-games")
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept={
                "title": "Seven Sparks",
                "summary": "A finite shared-supply strategy game.",
                "lane_contract": executable_game_contract(),
            },
            score=90,
            target_score=85,
        )
        return MakeContext(
            wish,
            self.taste,
            blueprint,
            invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
            "leo",
        )

    def science_context(self, workspace="science-make"):
        wish = Wish.create(
            "phase-window",
            "A hand-sized toy that makes coupled periodic motion visible",
            constraints={"lane": "holdable-science"},
            context={"inventor_id": "ivy"},
        )
        blueprint = ToyBlueprint.for_lane("holdable-science")
        scale = {
            "real_quantity": "one represented relationship",
            "model_quantity": "one complete interaction",
            "scale_ratio": 1.0,
            "units": "represented relationships per interaction",
        }
        simplification = {
            "simplification": "The model presents one exact, cited source statement and does not claim unmodeled behavior.",
            "reason": "One observable relationship keeps the first interaction legible.",
            "disclosed_limit": "It is a qualitative teaching model, not a measurement or prediction instrument.",
        }
        primary = InventResearchSource(
            "periodic-source",
            "Periodic motion fixture",
            "Fixture Science Archive",
            "https://example.com/science/periodic-motion",
            "2026-08-25T00:00:00Z",
            "Coupled periodic motion. A bounded linkage maps rotary phase to visible periodic displacement.",
            ("prior-art", "use-context", "science"),
        )
        mapping = InventResearchSource(
            "science-mapping",
            "Qualitative model boundary",
            "Autonomous Workshop fixture",
            "https://example.com/science/qualitative-mapping",
            "2026-08-25T00:00:00Z",
            "%s\n%s %s"
            % (
                json.dumps(scale, sort_keys=True, separators=(",", ":")),
                simplification["simplification"],
                simplification["disclosed_limit"],
            ),
            ("science", "use-context"),
        )
        safety = InventResearchSource(
            "safety-source",
            "Toy safety fixture",
            "Fixture Safety Office",
            "https://example.com/safety/toys",
            "2026-08-25T00:00:00Z",
            "Toy safety requires an explicit hazard review.",
            ("safety",),
        )
        research = InventResearch(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            blueprint_sha256=blueprint.sha256,
            lane=blueprint.lane,
            provider="fixture-science-research",
            provider_version="1.0.0",
            provider_config_sha256="a" * 64,
            sources=(primary, mapping, safety),
        )
        contract = {
            "schema_version": 1,
            "lane": "holdable-science",
            "source_model": {
                "phenomenon": "Coupled periodic motion",
                "model": "A bounded linkage maps rotary phase to visible periodic displacement.",
                "source_ids": ["periodic-source", "science-mapping"],
            },
            "simplifications": [simplification],
            "scale": scale,
            "interaction": {
                "user_action": "Turn the wheel once.",
                "observable_response": "Two markers reveal their relative phase.",
                "teaching_point": "Coupled periodic motion",
                "misuse_boundary": simplification["disclosed_limit"],
            },
        }
        concept = {
            "title": "Phase Window",
            "summary": "A tactile window onto periodic relationships.",
            "mechanical_handoff": ["Make two phase markers legible."],
            "lane_contract": contract,
            "research_evidence": research.to_dict(),
            "evidence": {
                "research_sha256": research.research_sha256,
                "research_source_ids": ["periodic-source", "science-mapping"],
            },
        }
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept=concept,
            score=90,
            target_score=85,
        )
        return MakeContext(
            wish,
            self.taste,
            blueprint,
            invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
            "ivy",
        )

    def worker(self, actions, verdicts, **kwargs):
        creator = FakeCodex("gpt-5.6-terra", actions)
        evaluator = FakeCodex("gpt-5.6-luna", verdicts)
        evaluator.reasoning_effort = "low"
        kwargs.setdefault("cad_builder", FakeCadBuilder())
        return CodexMaker(creator=creator, evaluator=evaluator, **kwargs), creator, evaluator

    def test_make_improves_then_seals_step_first_cad_and_truthful_holds(self):
        worker, creator, evaluator = self.worker(
            [make_action("First Press"), make_action("Orbit Press")],
            [verdict(72, "Tie the wheel more closely to the Wish."), verdict(92)],
        )
        made = worker(self.context())

        self.assertEqual(made.product["title"], "Orbit Press")
        self.assertFalse(made.product["physical_prototype"])
        self.assertEqual(len(creator.prompts), 2)
        self.assertIn("previous reward", creator.prompts[1][0])
        self.assertIn("may not upgrade it", evaluator.prompts[0][0])
        self.assertEqual(
            (made.artifact_root / "assembled.stl").read_bytes(),
            (made.artifact_root / "cad" / "product.stl").read_bytes(),
        )
        self.assertEqual(
            (made.artifact_root / "assembled.step").read_bytes(),
            (made.artifact_root / "cad" / "product.step").read_bytes(),
        )
        occurrence_sidecar = json.loads(
            (made.artifact_root / "assembled.step.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            occurrence_sidecar,
            {
                "schemaVersion": 1,
                "entryKind": "assembly",
                "primaryPose": "assembled",
                "parts": [
                    {"name": "base", "stlPath": "cad/part_base.stl"},
                    {
                        "name": "index-wheel",
                        "stlPath": "cad/part_index_wheel.stl",
                    },
                    {"name": "marker", "stlPath": "cad/part_marker.stl"},
                ],
            },
        )

        for part_id in ("base", "index-wheel", "marker"):
            stem = "part_" + part_id.replace("-", "_")
            self.assertTrue((made.artifact_root / "cad" / (stem + ".step.py")).is_file())
            self.assertTrue((made.artifact_root / "cad" / (stem + ".step")).is_file())
            self.assertTrue((made.artifact_root / "cad" / (stem + ".stl")).is_file())
        geometry = json.loads(
            (made.artifact_root / "validation" / "cad-build.json").read_text(encoding="utf-8")
        )
        self.assertTrue(geometry["passed"])
        self.assertFalse(geometry["release_ready"])
        self.assertEqual(geometry["checks"]["brep"]["status"], "passed")
        self.assertEqual(geometry["checks"]["interference"]["status"], "passed")
        self.assertEqual(geometry["checks"]["mesh-topology"]["status"], "passed")
        self.assertIn("slicer success or support requirements", geometry["not_proven"])
        print_declaration = json.loads(
            (made.artifact_root / "playtest" / "print.json").read_text(encoding="utf-8")
        )
        self.assertEqual(print_declaration["slicer"]["status"], "held")
        motion = json.loads(
            (made.artifact_root / "playtest" / "motion.json").read_text(encoding="utf-8")
        )
        self.assertEqual(motion["status"], "ready-for-shared-verifier")
        paths = {entry.path for entry in made.artifact_manifest.entries}
        self.assertIn("cad/design.json", paths)
        self.assertIn("validation/cad-build.json", paths)
        self.assertIn("cad/part_base.step.py", paths)
        self.assertIn("cad/part_base.step", paths)
        self.assertIn("cad/part_base.stl", paths)
        self.assertIn("cad/print_plate.step", paths)
        self.assertIn("cad/print_plate.stl", paths)
        self.assertIn("assembled.step", paths)
        self.assertIn("assembled.step.json", paths)
        self.assertIn("cad/FORMAT-LIMITATIONS.md", paths)
        self.assertIn("playtest/mechanical.json", paths)
        self.assertIn("playtest/print.json", paths)
        self.assertIn("playtest/motion.json", paths)
        self.assertIn("playtest/moving-machine-binding.json", paths)
        self.assertIn("assembled.stl", paths)
        self.assertIn("cad/product.stl", paths)

    def test_durable_make_automatically_runs_later_batch_to_goal(self):
        worker, creator, evaluator = self.worker(
            [make_action("First sealed Make"), make_action("Improved sealed Make")],
            [
                verdict(72, "Tie the mechanism more closely to the Wish."),
                verdict(92),
            ],
            max_steps=1,
        )
        context = self.durable_context("automatic-make")

        made = worker(context)

        self.assertEqual(made.product["title"], "Improved sealed Make")
        self.assertEqual(len(creator.prompts), 2)
        self.assertEqual(len(evaluator.prompts), 2)
        self.assertIn("First sealed Make", creator.prompts[1][0])
        self.assertIn(
            "Tie the mechanism more closely to the Wish.", creator.prompts[1][0]
        )
        records = sorted(
            (context.reward_journal / "steps").glob("[0-9]*.json")
        )
        self.assertEqual(len(records), 2)
        self.assertIn(
            "cad_observation",
            json.loads(records[-1].read_text(encoding="utf-8"))["next_state"],
        )
        binding = json.loads(
            (context.reward_journal / "binding.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            binding["binding"]["creator"]["identity"],
            "codex-make-policy+locked-step-cad",
        )
        self.assertEqual(
            binding["binding"]["evaluator"]["identity"],
            "codex-make-reward+locked-step-cad",
        )
        self.assertEqual(
            binding["initial_state"]["inputs"]["inventor_id"], "bob"
        )

    def test_durable_make_crash_after_pass_reuses_models_and_replays_exact_cad(self):
        build_titles = []

        class CountingCadBuilder(FakeCadBuilder):
            def build(self, action, *, lane, root):
                build_titles.append(action["title"])
                return super().build(action, lane=lane, root=root)

        first_worker, first_creator, first_evaluator = self.worker(
            [make_action("Crash-sealed Make")],
            [verdict(92)],
            max_steps=1,
            cad_builder=CountingCadBuilder(),
        )
        first_context = self.durable_context("make-before-crash")
        with mock.patch.object(
            CodexMaker,
            "_materialize",
            side_effect=RuntimeError("fixture crash after sealed reward"),
        ):
            with self.assertRaisesRegex(RuntimeError, "fixture crash"):
                first_worker(first_context)

        resumed_worker, resumed_creator, resumed_evaluator = self.worker(
            [],
            [],
            max_steps=1,
            cad_builder=CountingCadBuilder(),
        )
        resumed_context = self.durable_context(
            "make-after-crash", journal="make-reward-journal"
        )
        made = resumed_worker(resumed_context)

        self.assertEqual(made.product["title"], "Crash-sealed Make")
        self.assertEqual(len(first_creator.prompts), 1)
        self.assertEqual(len(first_evaluator.prompts), 1)
        self.assertEqual(len(resumed_creator.prompts), 0)
        self.assertEqual(len(resumed_evaluator.prompts), 0)
        self.assertEqual(build_titles, ["Crash-sealed Make", "Crash-sealed Make"])

    def test_shared_make_requires_at_least_two_mechanical_parts(self):
        self.assertEqual(_MAKE_SCHEMA["properties"]["parts"]["minItems"], 2)
        action = make_action()
        action["parts"] = action["parts"][:1]
        with self.assertRaises(WaitingFor):
            _validate_action(action)

        worker, creator, unused_evaluator = self.worker(
            [action], [verdict(100)]
        )
        with self.assertRaises(WaitingFor):
            worker(self.context())
        self.assertEqual(len(creator.prompts), 1)

    def test_deterministic_action_produces_identical_content_address(self):
        first, _, _ = self.worker([make_action()], [verdict(95)])
        second, _, _ = self.worker([make_action()], [verdict(95)])
        made_one = first(self.context("make-one"))
        made_two = second(self.context("make-two"))
        self.assertEqual(made_one.artifact_sha256, made_two.artifact_sha256)

    def test_make_uses_exact_assignment_identity_not_wish_metadata_or_display_name(self):
        worker, _, _ = self.worker([make_action()], [verdict(95)])
        made = worker(self.context(inventor_id="machine-smith"))
        self.assertEqual(made.product["inventor"]["id"], "machine-smith")
        self.assertEqual(made.product["inventor"]["name"], "Bob")
        self.assertEqual(self.wish.context["inventor_id"], "bob")
        self.assertEqual(made.product["slug"], self.wish.product_id)
        self.assertTrue(made.product["description"].endswith("By Bob."))
        loaded_wish, loaded_made, loaded_blueprint = _load_artifact_contract(
            made.artifact_root,
            made.artifact_manifest,
            "machine-smith",
            self.taste,
        )
        self.assertEqual(loaded_wish.to_dict(), self.wish.to_dict())
        self.assertEqual(loaded_made.product, made.product)
        self.assertEqual(loaded_blueprint.lane, self.blueprint.lane)

    def test_make_waits_without_exact_assignment_identity(self):
        worker, creator, _ = self.worker([make_action()], [verdict(95)])
        with self.assertRaises(WaitingFor) as caught:
            worker(self.context(inventor_id=None))
        self.assertEqual(caught.exception.needs[0].capability, "inventor-assignment")
        self.assertEqual(creator.prompts, [])

    def test_geometry_failure_cannot_be_overruled_by_model_scores(self):
        worker, _, _ = self.worker(
            [make_action(overlap=True), make_action(overlap=True)],
            [verdict(100), verdict(100)],
            max_steps=2,
        )
        with self.assertRaises(WaitingFor) as caught:
            worker(self.context())
        self.assertEqual(
            caught.exception.needs[0].capability,
            "mechanical-design-target-score",
        )
        self.assertFalse((self.context().workspace / "artifact").exists())

    def test_sealed_made_detects_later_mesh_mutation(self):
        worker, _, _ = self.worker([make_action()], [verdict(95)])
        made = worker(self.context())
        (made.artifact_root / "assembled.stl").write_bytes(b"changed")
        with self.assertRaises(ArtifactError):
            made.assert_current()

    def test_invented_game_seals_full_rules_and_runs_one_thousand_seeded_games(self):
        worker, _, _ = self.worker([game_action()], [verdict(95)])
        made = worker(self.game_context())
        simulator = made.artifact_root / "game" / "simulate.py"
        request_path = self.root / "simulation-request.json"
        output_path = self.root / "simulation-output.json"
        styles = ["optimizing", "social", "exploratory", "adversarial"]
        request = {
            "protocol": "workshop-seeded-games-v2",
            "artifact_sha256": made.artifact_sha256,
            "requested_games": 1000,
            "base_seed": 260825,
            "games": [
                {
                    "index": index,
                    "seed": 260825 + index,
                    "player_styles": [styles[index % 4], styles[(index + 1) % 4]],
                }
                for index in range(1000)
            ],
        }
        request_path.write_text(json.dumps(request), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(simulator),
                "--request",
                str(request_path),
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result["completed_games"], 1000)
        self.assertEqual(result["issues"], [])
        self.assertTrue(all(game["completed"] for game in result["games"]))
        rules = json.loads(
            (made.artifact_root / "game" / "rules.json").read_text(encoding="utf-8")
        )
        self.assertEqual(rules["termination_bound_turns"], 7)
        self.assertEqual(
            rules["game_protocol"],
            executable_game_contract()["game_protocol"],
        )
        self.assertIn(
            "The player after the one who empties the final resource wins",
            (made.artifact_root / "game" / "RULES.md").read_text(encoding="utf-8"),
        )

    def test_science_make_seals_invent_research_for_the_default_playtest_provider(self):
        context = self.science_context()
        action = make_action("Phase Window")
        action["motion_spec"] = {
            "enabled": False,
            "moving_part_id": "",
            "axis": "z",
            "sweep_degrees": 1,
            "minimum_aabb_clearance_mm": 0,
        }
        action.pop("moving_machine_binding")
        science_contract = context.invented.concept["lane_contract"]
        action["instructions"] = "%s %s" % (
            science_contract["interaction"]["teaching_point"],
            science_contract["interaction"]["misuse_boundary"],
        )
        worker, creator, unused_evaluator = self.worker([action], [verdict(95)])
        made = worker(context)

        self.assertIn("exact teaching_point", creator.prompts[0][0])
        paths = {entry.path for entry in made.artifact_manifest.entries}
        self.assertIn("playtest/invent-research.json", paths)
        mechanical = json.loads(
            (made.artifact_root / "playtest" / "mechanical.json").read_text(
                encoding="utf-8"
            )
        )
        binding = mechanical["digital_test_plan"]["invent_science_research"]
        research_path = made.artifact_root / binding["path"]
        self.assertEqual(
            hashlib.sha256(research_path.read_bytes()).hexdigest(),
            binding["file_sha256"],
        )
        playtest_context = PlaytestContext(
            context.wish,
            context.taste,
            context.blueprint,
            1,
            made,
            (self.root / "science-playtest").absolute(),
            2,
        )
        prepared = WorkshopLanePlaytestProviders().prepare(
            playtest_context, "science-test"
        )
        self.assertTrue(prepared.passed)
        self.assertEqual(prepared.measurements["accuracy_cases"], 3)
        self.assertEqual(prepared.measurements["content_coverage_failures"], 0)
        self.assertIn(
            "invent-research", {source.role for source in prepared.product_sources}
        )
        evidence_root = playtest_context.workspace
        evidence_root.mkdir()
        proof = prepared.seal(evidence_root)
        evidence = {
            "schema_version": 1,
            "kind": "workshop-ai-player-review",
            "evidence_class": "ai-simulation",
            "human_playtest": False,
            "artifact_sha256": made.artifact_sha256,
            "agent_roles": ["independent-player", "adversarial-player"],
            "release_proof": proof,
        }
        result_ref = "results/science-test.json"
        result_payload = (
            json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        result_path = evidence_root / result_ref
        result_path.parent.mkdir()
        result_path.write_bytes(result_payload)
        result = PlaytestResult.create(
            "science-test",
            True,
            made.artifact_sha256,
            evidence,
            prepared.provider.name,
            prepared.provider.version,
            prepared.provider.config_sha256,
            result_ref,
            hashlib.sha256(result_payload).hexdigest(),
        )
        playtested = Playtested(
            Playtest(
                made.artifact_manifest,
                (result,),
                evidence_manifest=build_artifact_manifest(
                    evidence_root, created_at="content-addressed"
                ),
            )
        )
        needs = playtest_release_needs(
            context.blueprint, made, playtested, evidence_root
        )
        self.assertNotIn("science-test", {need.capability for need in needs})

    def test_default_science_provider_fails_closed_without_exact_product_text(self):
        context = self.science_context("science-make-missing-text")
        action = make_action("Phase Window")
        action["motion_spec"] = {
            "enabled": False,
            "moving_part_id": "",
            "axis": "z",
            "sweep_degrees": 1,
            "minimum_aabb_clearance_mm": 0,
        }
        action.pop("moving_machine_binding")
        action["instructions"] = "Turn the wheel and observe the markers."
        worker, unused_creator, unused_evaluator = self.worker(
            [action], [verdict(95)]
        )
        made = worker(context)
        prepared = WorkshopLanePlaytestProviders().prepare(
            PlaytestContext(
                context.wish,
                context.taste,
                context.blueprint,
                1,
                made,
                (self.root / "science-playtest-missing-text").absolute(),
                2,
            ),
            "science-test",
        )
        self.assertFalse(prepared.passed)
        self.assertEqual(prepared.measurements["content_coverage_failures"], 1)


if __name__ == "__main__":
    unittest.main()
