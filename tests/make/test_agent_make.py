import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.make.agent import (
    MAKE_GENERATOR_ID,
    MAKE_GENERATOR_VERSION,
    CadSkillBuild,
    CodexMaker,
    LockedCadSkillBuilder,
    _MAKE_SCHEMA,
    _REWARD_SCHEMA,
    _invented_game_rule_kind,
    _make_schema_for_lane,
    _validate_action,
    _validate_invented_game_binding,
)
from workshop.errors import ArtifactError
from workshop.invent.contracts import InventContext, Invented
from workshop.make.contracts import MakeContext
from workshop.outcomes import WaitingFor
from workshop.playtest.gameplay import FINITE_GAME_SIMULATOR_SOURCE
from workshop.wish import Wish
from workshop.runtime.reward import json_sha256
from workshop.integrations.sealed_draft import _load_artifact_contract
from workshop.contributors.taste import load_taste
from workshop.product.blueprints import ToyBlueprint


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
                "top_grooves_mm": [],
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
                "top_grooves_mm": [],
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
                "top_grooves_mm": [],
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
            "title": "not applicable",
            "rule_kind": "shared-supply-take-away",
            "starting_tokens": 7,
            "max_take": 3,
            "last_take_wins": True,
            "theme": "not applicable",
            "token_part_ids": [],
            "token_sweep_values": [],
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


def verdict(
    score,
    feedback="Ready for digital Make.",
    *,
    make_findings=None,
    playtest_holds=None,
):
    if make_findings is None:
        deduction = 100 - score
        make_findings = []
        if deduction:
            make_findings = [
                {
                    "category": "interaction-definition",
                    "blocking": False,
                    "deductions": {
                        "concept_fidelity": deduction,
                        "taste_fit": deduction,
                        "interaction": deduction,
                        "mechanical_coherence": deduction,
                        "manufacturing_review": deduction,
                    },
                    "finding": feedback,
                    "change": "Address this Make-owned review finding.",
                }
            ]
    return {
        "make_findings": make_findings,
        "playtest_holds": list(playtest_holds or []),
        "make_feedback": [feedback],
        "assessment": feedback,
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
                "top_grooves_mm": [],
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
        "title": "Seven Sparks",
        "rule_kind": "shared-supply-take-away",
        "starting_tokens": 7,
        "max_take": 3,
        "last_take_wins": True,
        "theme": "Players coax the final spark from a shared constellation.",
        "token_part_ids": [part["part_id"] for part in parts],
        "token_sweep_values": [],
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


def shore_sweep_contract():
    return {
        "schema_version": 1,
        "lane": "invented-games",
        "complete_rules": {
            "setup": "Arrange seven unique tokens in a fixed ordered North-to-South shore line.",
            "legal_action": (
                "Choose one exposed shore: the North leftmost or South rightmost remaining "
                "token. Read that exposed token's raised sweep s in 1..3 and take "
                "k=1..min(s, remaining) contiguous tokens inward from that same shore."
            ),
            "forbidden": "Never use both shores, skip a token, take zero, or reorder tokens.",
            "ending": "The player making the final legal removal wins immediately.",
        },
        "simulator_design": {
            "minimum_complete_games": 1000,
            "fixed_seed_strategy": (
                "Run exactly 1,000 games indexed g=0..999 with unsigned 32-bit "
                "seed (20260825+g) mod 2^32 using Mulberry32; log every value used."
            ),
            "state_variables": "An ordered remaining list of token records {id,sweep}.",
            "legal_actions": "Enumerate N:k and S:k from the two exposed end tokens.",
            "transition": (
                "For N:k use remaining=slice(k); for S:k use "
                "remaining=slice(0,len-k)."
            ),
            "termination": "Stop exactly when the ordered remaining list is empty.",
            "league": "Run 1,000 seeds across all 16 ordered style pairings.",
        },
    }


def shore_game_action():
    value = game_action()
    sweeps = [1, 2, 3, 1, 3, 2, 1]
    groove_centers = {
        1: [0.0],
        2: [-4.0, 4.0],
        3: [-6.0, 0.0, 6.0],
    }
    parts = []
    for index, sweep in enumerate(sweeps):
        part_id = "signal-%d" % (index + 1)
        parts.append(
            {
                "part_id": part_id,
                "name": "signal token %d" % (index + 1),
                "purpose": "Ordered shore token whose grooves encode sweep %d." % sweep,
                "shape": "box",
                "size_mm": {"x": 18, "y": 14, "z": 6},
                "top_grooves_mm": [
                    {"center_x": center, "width": 1.2, "depth": 1.0}
                    for center in groove_centers[sweep]
                ],
                "print_center_mm": {"x": 12 + index * 22, "y": 18},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 12 + index * 22, "y": 80, "z": 3},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            }
        )
    value["parts"] = parts
    value["title"] = "Signal Spine"
    value["summary"] = "An ordered line whose exposed end marks govern each sweep."
    value["interaction"] = "Choose one exposed shore and sweep inward by that end token's marks."
    value["mechanical_principle"] = "Recessed top grooves physically encode each ordered token's 1-3 sweep limit."
    value["assembly"] = ["Arrange the seven exact token IDs North-to-South in sealed order."]
    value["instructions"] = "Remove a legal contiguous sweep from one exposed shore; final removal wins."
    value["game_spec"] = {
        "enabled": True,
        "title": "Signal Spine",
        "rule_kind": "ordered-shore-sweep",
        "starting_tokens": 7,
        "max_take": 3,
        "last_take_wins": True,
        "theme": "Signals wash inward from either exposed shore.",
        "token_part_ids": [part["part_id"] for part in parts],
        "token_sweep_values": sweeps,
    }
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

    def __init__(self):
        self.availability_calls = 0
        self.build_calls = []

    def ensure_available(self):
        self.availability_calls += 1
        return {"cad": "a" * 64, "product-to-cad": "b" * 64}

    def build(self, action, *, lane, root):
        self.build_calls.append((action, lane, root))
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


class DiagnosticCadBuilder(FakeCadBuilder):
    """Return repeatable locked-evidence details for retry-feedback coverage."""

    def build(self, action, *, lane, root):
        build = super().build(action, lane=lane, root=root)
        observation = json.loads(json.dumps(build.observation))
        observation["passed"] = False
        observation["issues"] = [
            "measured STEP bounds differ from the declared part dimensions",
            "a declared assembly or print-layout pose has a CAD-kernel interference",
        ]
        observation["checks"]["dimensions"] = {
            "status": "failed",
            "measurements": {
                "measured_parts": 3,
                "out_of_tolerance": 1,
                "parts": [
                    {
                        "part_id": "base",
                        "expected_mm": [48.0, 36.0, 5.0],
                        "measured_mm": [47.8, 36.0, 5.0],
                        "effective_tolerance_mm": [0.05, 0.05, 0.05],
                        "within_tolerance": False,
                    }
                ],
            },
        }
        repeated_clash = {
            "a": {"name": "base"},
            "b": {"name": "index-wheel"},
        }
        observation["checks"]["interference"] = {
            "status": "failed",
            "measurements": {
                "poses_tested": 2,
                "forbidden_intersections": 3,
                "poses": [
                    {
                        "target": "product.step",
                        "result": {
                            "clashes": [
                                repeated_clash,
                                {
                                    "a": {"name": "marker"},
                                    "b": {"name": "base"},
                                },
                            ]
                        },
                    },
                    {
                        "target": "print_plate.step",
                        "result": {"clashes": [repeated_clash]},
                    },
                ],
            },
        }
        (build.root / "verification" / "cad-build.json").write_text(
            json.dumps(observation, sort_keys=True), encoding="utf-8"
        )
        return CadSkillBuild(build.root, observation)


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
            concept={"title": "Seven Sparks", "summary": "A finite shared-supply strategy game."},
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

    def shore_game_context(self, workspace="shore-game-make"):
        wish = Wish.create(
            "signal-spine",
            "A tactile strategy line where marked signals sweep in from either end",
            constraints={"lane": "invented-games"},
            context={"inventor_id": "leo"},
        )
        blueprint = ToyBlueprint.for_lane("invented-games")
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept={
                "title": "Signal Spine",
                "summary": "A fixed ordered shore-sweep game.",
                "lane_contract": shore_sweep_contract(),
            },
            score=91,
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

    def worker(self, actions, verdicts, **kwargs):
        creator = FakeCodex("gpt-5.6-terra", actions)
        evaluator = FakeCodex("gpt-5.6-luna", verdicts)
        evaluator.reasoning_effort = "low"
        kwargs.setdefault("cad_builder", FakeCadBuilder())
        kwargs.setdefault("game_simulator_source", FINITE_GAME_SIMULATOR_SOURCE)
        return CodexMaker(creator=creator, evaluator=evaluator, **kwargs), creator, evaluator

    def test_invented_game_requires_composed_playtest_simulator_provider(self):
        worker, _, _ = self.worker(
            [game_action()],
            [verdict(95)],
            game_simulator_source=None,
        )
        with self.assertRaises(WaitingFor) as caught:
            worker(self.game_context("missing-game-simulator"))
        self.assertEqual(
            caught.exception.needs[0].capability,
            "game-simulator-provider",
        )
        self.assertFalse(
            (self.root / "missing-game-simulator" / "artifact").exists()
        )

    def test_invalid_invent_seed_strategy_stops_before_creator_or_cad(self):
        cases = {
            "wrong-game-count": (
                1_024,
                "Run exactly 1,024 games with seed (20260825+g) mod 2^32 using Mulberry32.",
                "exactly 1,000 complete games",
            ),
            "unsupported-prng": (
                1_000,
                "Run exactly 1,000 games with seed (20260825+g) mod 2^32 using xorshift32.",
                "pinned Mulberry32",
            ),
        }
        for label, (game_count, declaration, expected_reason) in cases.items():
            with self.subTest(label=label):
                base = self.shore_game_context("bad-seed-" + label)
                lane_contract = json.loads(json.dumps(shore_sweep_contract()))
                lane_contract["simulator_design"][
                    "minimum_complete_games"
                ] = game_count
                lane_contract["simulator_design"][
                    "fixed_seed_strategy"
                ] = declaration
                invented = Invented(
                    wish_sha256=json_sha256(base.wish.to_dict()),
                    taste_sha256=base.taste.sha256,
                    lane=base.blueprint.lane,
                    concept={
                        "title": "Signal Spine",
                        "summary": "A fixed ordered shore-sweep game.",
                        "lane_contract": lane_contract,
                    },
                    score=91,
                    target_score=85,
                )
                context = MakeContext(
                    base.wish,
                    base.taste,
                    base.blueprint,
                    invented,
                    base.round,
                    base.workspace,
                    base.feedback,
                    base.playtest_rounds,
                    base.inventor_id,
                )
                cad_builder = FakeCadBuilder()
                worker, creator, evaluator = self.worker(
                    [shore_game_action()],
                    [verdict(100)],
                    cad_builder=cad_builder,
                )
                with self.assertRaises(WaitingFor) as caught:
                    worker(context)
                need = caught.exception.needs[0]
                self.assertEqual(need.capability, "invented-game-seed-strategy")
                self.assertIn(expected_reason, need.reason)
                self.assertEqual(creator.prompts, [])
                self.assertEqual(evaluator.prompts, [])
                self.assertEqual(cad_builder.availability_calls, 0)
                self.assertEqual(cad_builder.build_calls, [])

    def test_make_improves_then_seals_step_first_cad_and_truthful_holds(self):
        worker, creator, evaluator = self.worker(
            [make_action("First Press"), make_action("Orbit Press")],
            [verdict(72, "Tie the wheel more closely to the Wish."), verdict(92)],
        )
        made = worker(self.context())

        self.assertEqual(made.product["title"], "Orbit Press")
        self.assertFalse(made.product["physical_prototype"])
        self.assertEqual(len(creator.prompts), 2)
        self.assertIn("top_grooves_mm", creator.prompts[0][0])
        self.assertIn("integral tactile seams", creator.prompts[0][0])
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
        self.assertIn("cad/FORMAT-LIMITATIONS.md", paths)
        self.assertIn("playtest/mechanical.json", paths)
        self.assertIn("playtest/print.json", paths)
        self.assertIn("playtest/motion.json", paths)
        self.assertIn("playtest/moving-machine-binding.json", paths)
        self.assertIn("assembled.stl", paths)
        self.assertIn("cad/product.stl", paths)

    def test_playtest_evidence_holds_have_no_make_score_or_tension_path(self):
        holds = [
            {
                "category": "game-balance",
                "finding": "The fixed opening still needs solved-position review.",
            },
            {
                "category": "seeded-simulation",
                "finding": "The seeded league has not run yet.",
            },
            {
                "category": "human-play",
                "finding": "No human session exists before Playtest.",
            },
            {
                "category": "slicing-and-supports",
                "finding": "No slicer profile or support receipt exists yet.",
            },
            {
                "category": "physical-fit-or-motion",
                "finding": "Physical fit and motion remain untested.",
            },
            {
                "category": "tactile-readability",
                "finding": "Hands-on tactile readability remains untested.",
            },
            {
                "category": "safety-or-durability",
                "finding": "Physical safety and durability remain untested.",
            },
            {
                "category": "physical-print",
                "finding": "No physical print exists yet.",
            },
            {
                "category": "customer-experience",
                "finding": "Customer delight is downstream evidence.",
            },
        ]
        worker, _, evaluator = self.worker(
            [make_action()],
            [verdict(100, playtest_holds=holds)],
        )
        made = worker(self.context("downstream-holds"))

        design = json.loads(
            (made.artifact_root / "cad" / "design.json").read_text(
                encoding="utf-8"
            )
        )
        reward = design["reward_loop"]["steps"][0]["reward"]
        self.assertEqual(reward["value"], 100)
        self.assertEqual(reward["hard_tensions"], [])
        self.assertTrue(all(value == 100 for value in reward["dimensions"].values()))
        self.assertTrue(
            any("not a Make retry" in item for item in reward["feedback"])
        )
        reward_prompt, reward_schema, _ = evaluator.prompts[0]
        self.assertIn("before Playtest", reward_prompt)
        self.assertIn("never as a deduction", reward_prompt)
        self.assertIn("solved openings", reward_prompt)
        self.assertNotIn("dimensions", reward_schema["properties"])
        self.assertNotIn("hard_tensions", reward_schema["properties"])
        self.assertEqual(
            set(reward_schema["required"]), set(reward_schema["properties"])
        )
        self.assertEqual(reward_schema, _REWARD_SCHEMA)

    def test_required_concept_omission_remains_a_make_hard_tension(self):
        finding = {
            "category": "wish-or-invent-omission",
            "blocking": False,
            "deductions": {
                "concept_fidelity": 1,
                "taste_fit": 0,
                "interaction": 0,
                "mechanical_coherence": 0,
                "manufacturing_review": 0,
            },
            "finding": "The action omits an explicitly required registration feature.",
            "change": "Add the required feature as real geometry.",
        }
        worker, _, _ = self.worker(
            [make_action()],
            [verdict(99, make_findings=[finding])],
            max_steps=1,
        )
        context = self.context("required-concept-omission")
        with self.assertRaises(WaitingFor) as caught:
            worker(context)
        self.assertEqual(
            caught.exception.needs[0].capability,
            "mechanical-design-target-score",
        )
        diagnostic = json.loads(
            (context.workspace / "diagnostics" / "make-reward-loop.failed.json").read_text(
                encoding="utf-8"
            )
        )
        tensions = diagnostic["steps"][0]["reward"]["hard_tensions"]
        self.assertEqual(len(tensions), 1)
        self.assertIn("wish-or-invent-omission", tensions[0])

    def test_shared_make_requires_at_least_two_mechanical_parts(self):
        self.assertEqual(_MAKE_SCHEMA["properties"]["parts"]["minItems"], 2)
        self.assertEqual(
            _MAKE_SCHEMA["properties"]["parts"]["items"]["properties"]["part_id"]["pattern"],
            "^[a-z][a-z0-9-]{0,62}$",
        )
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

    def test_assembly_coordinates_allow_negative_xy_but_print_coordinates_do_not(self):
        part_schema = _MAKE_SCHEMA["properties"]["parts"]["items"]
        assembly_schema = part_schema["properties"]["assembly_center_mm"][
            "properties"
        ]
        print_schema = part_schema["properties"]["print_center_mm"]["properties"]
        self.assertEqual(assembly_schema["x"]["minimum"], -220.0)
        self.assertEqual(assembly_schema["y"]["minimum"], -220.0)
        self.assertEqual(assembly_schema["z"]["minimum"], 0)
        self.assertEqual(print_schema["x"]["minimum"], 0)
        self.assertEqual(print_schema["y"]["minimum"], 0)

        action = make_action()
        action["parts"][0]["assembly_center_mm"].update({"x": -80, "y": -40})
        self.assertIs(_validate_action(action), action)
        action["parts"][0]["assembly_center_mm"]["x"] = -221
        with self.assertRaises(WaitingFor):
            _validate_action(action)

        action = make_action()
        action["parts"][0]["print_center_mm"]["x"] = -1
        with self.assertRaises(WaitingFor):
            _validate_action(action)

    def test_generated_assembly_placement_uses_true_part_center_in_z(self):
        source = LockedCadSkillBuilder._project_sources(make_action())[
            "product.step.py"
        ]
        self.assertIn("('base', (80.0, 80.0, -2.5), 0.0)", source)
        self.assertIn("('index-wheel', (80.0, 80.0, 5.0), 0.0)", source)
        self.assertIn("('marker', (122.0, 80.0, -4.0), 0.0)", source)

    def test_locked_box_top_grooves_generate_real_full_width_subtractions(self):
        action = make_action()
        action["parts"][0]["top_grooves_mm"] = [
            {"center_x": -8, "width": 2, "depth": 1},
            {"center_x": 8, "width": 2, "depth": 1},
        ]
        self.assertIs(_validate_action(action), action)

        first = LockedCadSkillBuilder._project_sources(action)
        second = LockedCadSkillBuilder._project_sources(action)
        self.assertEqual(first, second)
        self.assertIn('"top_grooves_mm": [', first["parameters.py"])
        source = first["parts.py"]
        self.assertIn('for groove in spec["top_grooves_mm"]', source)
        self.assertIn('float(groove["center_x"])', source)
        self.assertIn('float(size["y"]) + 2.0 * GROOVE_CUTTER_OVERTRAVEL_MM', source)
        self.assertIn("shape = shape - cutter", source)

        root = self.root / "grooved-project"
        LockedCadSkillBuilder()._write_project(root, action)
        product_spec = (root / "product_spec.md").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        self.assertIn("x=-8.00, width=2.00, depth=1.00", product_spec)
        self.assertIn("real subtractive cut across the box's full local Y width", product_spec)
        self.assertIn("locked `top_grooves_mm`", readme)

    def test_top_groove_validation_rejects_missing_malformed_unsafe_and_overlapping_cuts(self):
        cases = {}

        missing = make_action()
        missing["parts"][0].pop("top_grooves_mm")
        cases["missing-required-field"] = missing

        cylinder = make_action()
        cylinder["parts"][1]["top_grooves_mm"] = [
            {"center_x": 0, "width": 2, "depth": 1}
        ]
        cases["cylinder-cut"] = cylinder

        malformed = make_action()
        malformed["parts"][0]["top_grooves_mm"] = [
            {"center_x": 0, "width": 2, "depth": 1, "label": "fake"}
        ]
        cases["unknown-field"] = malformed

        outside = make_action()
        outside["parts"][0]["top_grooves_mm"] = [
            {"center_x": 23, "width": 2, "depth": 1}
        ]
        cases["outside-x"] = outside

        overlapping = make_action()
        overlapping["parts"][0]["top_grooves_mm"] = [
            {"center_x": 0, "width": 4, "depth": 1},
            {"center_x": 1, "width": 4, "depth": 1},
        ]
        cases["overlap"] = overlapping

        deep = make_action()
        deep["parts"][0]["top_grooves_mm"] = [
            {"center_x": 0, "width": 2, "depth": 4.3}
        ]
        cases["unsafe-floor"] = deep

        nonpositive = make_action()
        nonpositive["parts"][0]["top_grooves_mm"] = [
            {"center_x": 0, "width": 0, "depth": 1}
        ]
        cases["nonpositive"] = nonpositive

        for label, action in cases.items():
            with self.subTest(label=label), self.assertRaises(WaitingFor):
                _validate_action(action)

        part_schema = _MAKE_SCHEMA["properties"]["parts"]["items"]
        self.assertIn("top_grooves_mm", part_schema["required"])
        self.assertEqual(set(part_schema["required"]), set(part_schema["properties"]))
        groove_schema = part_schema["properties"]["top_grooves_mm"]
        self.assertEqual(groove_schema["maxItems"], 8)
        self.assertEqual(
            set(groove_schema["items"]["required"]),
            set(groove_schema["items"]["properties"]),
        )

    def test_failed_geometry_feedback_names_exact_deltas_and_unique_clash_pairs(self):
        worker, creator, _ = self.worker(
            [make_action("First"), make_action("Second")],
            [verdict(100), verdict(100)],
            cad_builder=DiagnosticCadBuilder(),
            max_steps=2,
        )
        with self.assertRaises(WaitingFor):
            worker(self.context("diagnostic-feedback"))
        retry_prompt = creator.prompts[1][0]
        self.assertIn(
            "CAD dimension mismatch for base: expected_mm=[48.0,36.0,5.0], "
            "measured_mm=[47.8,36.0,5.0], absolute_delta_mm=[0.2,0.0,0.0]",
            retry_prompt,
        )
        self.assertIn(
            "CAD interference pairs (2 unique): base <-> index-wheel, base <-> marker.",
            retry_prompt,
        )
        self.assertEqual(retry_prompt.count("base <-> index-wheel"), 1)

    def test_make_rejects_noncanonical_part_ids_before_cad(self):
        action = make_action()
        action["parts"][0]["part_id"] = "case_base"
        with self.assertRaises(WaitingFor):
            _validate_action(action)

    def test_disabled_lane_sections_accept_empty_inert_text(self):
        action = game_action()
        action["classic_spec"]["known_game"] = ""
        action["classic_spec"]["rules_reference"] = ""
        self.assertIs(_validate_action(action, lane="invented-games"), action)

        action["classic_spec"]["enabled"] = True
        action["classic_spec"]["rules_unchanged"] = True
        with self.assertRaises(WaitingFor):
            _validate_action(action)

    def test_active_game_requires_real_title_and_theme(self):
        action = game_action()
        action["game_spec"]["title"] = ""
        with self.assertRaises(WaitingFor):
            _validate_action(action, lane="invented-games")

    def test_game_schema_requires_explicit_rule_family_and_aligned_sweeps(self):
        game_schema = _make_schema_for_lane("invented-games")["properties"][
            "game_spec"
        ]
        self.assertEqual(set(game_schema["required"]), set(game_schema["properties"]))
        self.assertEqual(
            set(game_schema["properties"]["rule_kind"]["enum"]),
            {"shared-supply-take-away", "ordered-shore-sweep"},
        )
        malformed = shore_game_action()
        malformed["game_spec"].pop("token_sweep_values")
        with self.assertRaises(WaitingFor):
            _validate_action(malformed, lane="invented-games")

    def test_shore_sweep_contract_cannot_collapse_or_misbind_marks(self):
        contract = shore_sweep_contract()
        self.assertEqual(_invented_game_rule_kind(contract), "ordered-shore-sweep")

        collapsed = shore_game_action()
        collapsed["game_spec"]["rule_kind"] = "shared-supply-take-away"
        collapsed["game_spec"]["token_sweep_values"] = []
        with self.assertRaises(WaitingFor):
            _validate_invented_game_binding(collapsed, contract)

        misbound = shore_game_action()
        misbound["parts"][1]["top_grooves_mm"] = misbound["parts"][1][
            "top_grooves_mm"
        ][:1]
        with self.assertRaises(WaitingFor):
            _validate_invented_game_binding(misbound, contract)

        valid = shore_game_action()
        self.assertEqual(
            _validate_invented_game_binding(valid, contract),
            "ordered-shore-sweep",
        )

    def test_shore_sweep_seals_exact_order_rules_marks_and_contract(self):
        action = shore_game_action()
        worker, creator, _ = self.worker([action], [verdict(95)])
        context = self.shore_game_context()
        made = worker(context)
        rules = json.loads(
            (made.artifact_root / "game" / "rules.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(rules["protocol"], "workshop-finite-token-game-v2")
        self.assertEqual(rules["kind"], "ordered-shore-sweep")
        self.assertEqual(rules["seed_strategy"]["base_seed"], 20260825)
        self.assertEqual(rules["seed_strategy"]["prng"], "mulberry32")
        self.assertEqual(rules["invent_lane_contract"], shore_sweep_contract())
        self.assertEqual(
            rules["invent_lane_contract_sha256"],
            json_sha256(shore_sweep_contract()),
        )
        self.assertEqual(
            rules["ordered_tokens"],
            [
                {"part_id": part_id, "sweep": sweep}
                for part_id, sweep in zip(
                    action["game_spec"]["token_part_ids"],
                    action["game_spec"]["token_sweep_values"],
                )
            ],
        )
        self.assertEqual(
            rules["restoration_log_provenance"]["status"],
            "sealed-configuration",
        )
        self.assertIn(
            "Invent lane contract supplied no approved",
            rules["restoration_log_provenance"]["claim_scope"],
        )
        rule_text = (made.artifact_root / "game" / "RULES.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("North is the leftmost remaining token", rule_text)
        self.assertIn("Never combine shores, skip, or reorder", rule_text)
        self.assertIn("`signal-3` | 3", rule_text)
        self.assertIn('"required_game_rule_kind": "ordered-shore-sweep"', creator.prompts[0][0])
        self.assertIn("never collapse it", creator.prompts[0][0])

    def test_unconditional_make_text_is_nonempty_in_the_api_schema(self):
        self.assertEqual(_MAKE_SCHEMA["properties"]["title"]["pattern"], r"\S")
        self.assertEqual(
            _MAKE_SCHEMA["properties"]["parts"]["items"]["properties"]["name"]["pattern"],
            r"\S",
        )
        self.assertEqual(
            _MAKE_SCHEMA["properties"]["assembly"]["items"]["pattern"],
            r"\S",
        )

    def test_make_output_schema_has_no_optional_api_properties(self):
        for lane in (
            "classics-made-yours",
            "invented-games",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        ):
            with self.subTest(lane=lane):
                schema = _make_schema_for_lane(lane)
                self.assertEqual(
                    set(schema["required"]), set(schema["properties"])
                )
                self.assertEqual(
                    "moving_machine_binding" in schema["properties"],
                    lane == "moving-machines",
                )
                self.assertEqual(
                    schema["properties"]["classic_spec"]["properties"]["enabled"]["enum"],
                    [lane == "classics-made-yours"],
                )
                self.assertEqual(
                    schema["properties"]["classic_spec"]["properties"]["rules_unchanged"]["enum"],
                    [lane == "classics-made-yours"],
                )
                self.assertEqual(
                    schema["properties"]["game_spec"]["properties"]["enabled"]["enum"],
                    [lane == "invented-games"],
                )
                self.assertEqual(
                    schema["properties"]["motion_spec"]["properties"]["enabled"]["enum"],
                    [lane == "moving-machines"],
                )

    def test_make_rejects_stage_flags_from_the_wrong_lane(self):
        action = make_action()
        with self.assertRaises(WaitingFor):
            _validate_action(action, lane="classics-made-yours")

        action["motion_spec"] = {
            "enabled": False,
            "moving_part_id": "",
            "axis": "z",
            "sweep_degrees": 1,
            "minimum_aabb_clearance_mm": 0,
        }
        action.pop("moving_machine_binding")
        action["classic_spec"] = {
            "enabled": True,
            "known_game": "Chess",
            "rules_reference": "FIDE Laws of Chess",
            "rules_unchanged": True,
        }
        self.assertIs(
            _validate_action(action, lane="classics-made-yours"), action
        )

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
            [
                verdict(100, "Retry after FACTORY_PASSWORD=fixture-only-secret."),
                verdict(100, "Still below target."),
            ],
            max_steps=2,
        )
        context = self.context("failed-reward-diagnostic")
        with self.assertRaises(WaitingFor) as caught:
            worker(context)
        self.assertEqual(
            caught.exception.needs[0].capability,
            "mechanical-design-target-score",
        )
        self.assertFalse((context.workspace / "artifact").exists())
        diagnostic_path = (
            context.workspace / "diagnostics" / "make-reward-loop.failed.json"
        )
        self.assertTrue(diagnostic_path.is_file())
        self.assertLessEqual(diagnostic_path.stat().st_size, 64 * 1024)
        diagnostic_text = diagnostic_path.read_text(encoding="utf-8")
        self.assertNotIn("fixture-only-secret", diagnostic_text)
        self.assertNotIn("previous_action", diagnostic_text)
        self.assertNotIn('"inputs"', diagnostic_text)
        diagnostic = json.loads(diagnostic_text)
        self.assertEqual(diagnostic["kind"], "workshop.make.failed-reward-loop")
        self.assertFalse(diagnostic["reached_goal"])
        self.assertEqual(len(diagnostic["steps"]), 2)
        self.assertEqual(diagnostic["steps"][0]["reward"]["value"], 80)
        self.assertEqual(
            diagnostic["steps"][0]["reward"]["feedback"][0],
            "Retry after FACTORY_PASSWORD=<redacted>",
        )

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
        rules = json.loads(
            (made.artifact_root / "game" / "rules.json").read_text(
                encoding="utf-8"
            )
        )
        styles = ["optimizing", "social", "exploratory", "adversarial"]
        pairings = [(left, right) for left in styles for right in styles]
        request = {
            "protocol": "workshop-seeded-games-v1",
            "artifact_sha256": made.artifact_sha256,
            "requested_games": 1000,
            "base_seed": 260825,
            "seed_strategy": rules["seed_strategy"],
            "games": [
                {
                    "index": index,
                    "seed": 260825 + index,
                    "player_styles": list(pairings[index % len(pairings)]),
                    "first_seat": index % 2,
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
        self.assertEqual(rules["termination_bound_turns"], 7)
        self.assertIn("There are no ties", (made.artifact_root / "game" / "RULES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
