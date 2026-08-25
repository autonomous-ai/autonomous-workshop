import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_playtest import (
    DEFAULT_GAME_COUNT,
    DEFAULT_PLAYTEST_GOAL,
    DETERMINISTIC_CAPABILITIES,
    GAME_STYLES,
    LaneAwarePlaytester,
)
from inventor_workshop.agent_make import CodexMaker
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.jobs import Invented, Made, MakeContext, PlaytestContext, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.playtest_release import playtest_release_needs
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


CHECK_CONFIG_SHA256 = "d" * 64


class FakeEvaluator:
    cli_version = "9.8.7"
    model = "gpt-5.6-terra"
    reasoning_effort = "low"

    def __init__(self, output):
        self.output = output
        self.calls = []

    def invoke(self, *, prompt, schema, workspace):
        self.calls.append((prompt, schema, workspace))
        return self.output


def make_verdict(score=92):
    return {
        "dimensions": {
            "concept_fidelity": score,
            "taste_fit": score,
            "interaction": score,
            "mechanical_coherence": score,
            "manufacturing_review": score,
        },
        "feedback": ["Ready for the narrow digital MVP."],
        "hard_tensions": [],
        "assessment": "Ready for the narrow digital MVP.",
    }


def review_batch(capabilities, score=92, failing=None):
    reviews = []
    for capability in capabilities:
        findings = []
        if capability == failing:
            findings = [
                {
                    "code": "edge-catches",
                    "area": "handling",
                    "severity": "improve",
                    "finding": "The exposed edge catches during the simulated reset.",
                    "change": "Round the edge and increase the reset clearance.",
                    "evidence_refs": ["toy.step"],
                }
            ]
        reviews.append(
            {
                "capability": capability,
                "dimensions": {
                    "wish_fit": score,
                    "play_clarity": score,
                    "functional_confidence": score,
                    "robustness": score,
                    "distinctiveness": score,
                    "evidence_quality": score,
                },
                "observations": ["The exact sealed revision was reviewed by four AI-player roles."],
                "findings": findings,
                "hard_tensions": [],
            }
        )
    return {"reviews": reviews}


class AgentPlaytestTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Specific grown-up toys with one surprising interaction.\n"
            "---\n"
            "# Taste\n\nMake the Wish structural. Never fake physical proof.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(self.inventor)

    def tearDown(self):
        self.temporary.cleanup()

    def test_default_capability_registry_is_not_an_explicit_moving_override(self):
        default = LaneAwarePlaytester(evaluator=FakeEvaluator({"reviews": []}))
        partial = LaneAwarePlaytester(
            evaluator=FakeEvaluator({"reviews": []}),
            capability_checks={"print-test": lambda unused: {}},
        )

        self.assertEqual(default._explicit_capability_names, frozenset())
        self.assertEqual(
            partial._explicit_capability_names, frozenset({"print-test"})
        )

    def context(self, lane, suffix="one"):
        artifact = self.root / ("artifact-" + suffix)
        artifact.mkdir()
        (artifact / "rules.md").write_text(
            "Every legal turn advances one marker. The first to seven wins.\n",
            encoding="utf-8",
        )
        (artifact / "game-rules.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "setup": "Put seven markers in a shared supply.",
                    "legal_action": "Take one marker per legal turn.",
                    "terminal": "The first player to seven wins.",
                }
            ),
            encoding="utf-8",
        )
        (artifact / "toy.step").write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
        (artifact / "toy.stl").write_text("solid toy\nendsolid toy\n", encoding="utf-8")
        (artifact / "simulator.py").write_text(
            "# Exact deterministic simulator source used by the test adapter.\n",
            encoding="utf-8",
        )
        (artifact / "slicer-receipt.json").write_text(
            json.dumps({"slicer": "fixture", "version": "2.9.6", "errors": 0}),
            encoding="utf-8",
        )
        (artifact / "motion-receipt.json").write_text(
            json.dumps({"states": 37, "continuous_sweep": True, "failures": 0}),
            encoding="utf-8",
        )
        (artifact / "mechanical-receipt.json").write_text(
            json.dumps(
                {
                    "parts_checked": 2,
                    "tolerance_cases": 3,
                    "assembly_paths": 1,
                    "load_cases": 2,
                    "failures": 0,
                }
            ),
            encoding="utf-8",
        )
        made = Made.from_root(
            artifact,
            {
                "title": "Seven Steps",
                "summary": "A compact challenge with one surprising reset.",
                "lane": lane,
                "components": ["board", "markers"],
            },
        )
        return PlaytestContext(
            Wish.create("wish-" + suffix, "Make me a surprising pocket challenge"),
            self.taste,
            ToyBlueprint.for_lane(lane),
            1,
            made,
            (self.root / ("playtest-" + suffix)).absolute(),
            2,
        )

    @staticmethod
    def digital_checks(context, *, failing=None):
        checks = {}
        sealed_paths = {
            entry.path for entry in context.made.artifact_manifest.entries
        }
        for capability in context.blueprint.required_capabilities("playtest"):
            if capability not in DETERMINISTIC_CAPABILITIES:
                continue
            source = "rules.md" if capability == "classic-rules-test" else (
                ("toy.stl" if "toy.stl" in sealed_paths else "assembled.stl")
                if capability == "print-test"
                else ("toy.step" if "toy.step" in sealed_paths else "assembled.step")
            )

            def check(received, capability=capability, source=source):
                passed = capability != failing
                source_refs = [source]
                method_class = "deterministic-digital-check"
                metrics = {"checked": 1, "failures": 0 if passed else 1}
                inventory = {
                    entry.path: entry.sha256
                    for entry in received.made.artifact_manifest.entries
                }
                if capability == "print-test" and passed:
                    method_class = "deterministic-exact-slicer-profile"
                    receipt = {
                        "schema_version": 1,
                        "slicer": "PrusaSlicer",
                        "slicer_version": "2.9.6",
                        "profiles": {
                            "printer": {
                                "name": "printer.ini",
                                "origin": "test-pinned",
                                "bytes": 10,
                                "sha256": "1" * 64,
                            },
                            "process": {
                                "name": "process.ini",
                                "origin": "test-pinned",
                                "bytes": 11,
                                "sha256": "2" * 64,
                            },
                            "filament": {
                                "name": "filament.ini",
                                "origin": "test-pinned",
                                "bytes": 12,
                                "sha256": "3" * 64,
                            },
                        },
                        "parts": [
                            {
                                "input_ref": source,
                                "input_sha256": inventory[source],
                                "command": [
                                    "PrusaSlicer",
                                    "--export-gcode",
                                    source,
                                ],
                                "returncode": 0,
                                "stdout": "sliced",
                                "stderr": "",
                                "gcode_bytes": 100,
                                "gcode_sha256": "4" * 64,
                                "gcode_metrics": {"estimated_print_time": "4m"},
                            }
                        ],
                    }
                    receipt_sha256 = hashlib.sha256(
                        json.dumps(
                            receipt,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).hexdigest()
                    metrics.update(
                        {
                            "profiles_checked": 3,
                            "parts_sliced": 1,
                            "slicer_errors": 0,
                            "slicer_receipt": receipt,
                            "slicer_receipt_sha256": receipt_sha256,
                        }
                    )
                if capability == "motion-test" and passed:
                    source_refs.append("motion-receipt.json")
                    method_class = "deterministic-kinematic-simulation"
                    metrics.update(
                        {
                            "states_tested": 37,
                            "continuous_sweep": True,
                            "collisions": 0,
                            "tolerance_cases_tested": 3,
                            "load_cases_tested": 2,
                            "failures": 0,
                            "motion_receipt_ref": "motion-receipt.json",
                            "motion_receipt_sha256": inventory["motion-receipt.json"],
                        }
                    )
                if capability == "mechanical-test" and passed:
                    method_class = "deterministic-mechanical-verification"
                    mechanical_measurements = {
                        "brep_valid": True,
                        "interference_cases": 2,
                        "fit_cases": 3,
                        "assembly_paths_tested": 1,
                        "motion_cases": 1,
                        "load_cases": 2,
                        "failure_modes_tested": 2,
                        "forbidden_intersections": 0,
                        "fit_failures": 0,
                        "assembly_failures": 0,
                        "motion_failures": 0,
                        "load_failures": 0,
                        "unresolved_critical_failures": 0,
                    }
                    mechanical_receipt = {
                        "schema_version": 1,
                        "kind": "workshop.digital-mechanical-simulation",
                        "artifact_sha256": received.made.artifact_sha256,
                        "claim_scope": "Deterministic test fixture only.",
                        "source_sha256": {source: inventory[source]},
                        "plan": {"kind": "fixture"},
                        "fit_cases": [{"passed": True}],
                        "assembly_motion_manifest": {"conditions": [{}]},
                        "assembly_motion_result": {
                            "results": [{"status": "pass"}]
                        },
                        "load_cases": [{"passed": True}],
                        "measurements": mechanical_measurements,
                        "not_proven": ["physical fit"],
                    }
                    mechanical_receipt_sha256 = hashlib.sha256(
                        json.dumps(
                            mechanical_receipt,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).hexdigest()
                    metrics.update(
                        {
                            **mechanical_measurements,
                            "parts_checked": 2,
                            "tolerance_cases_tested": 3,
                            "assembly_paths_checked": 1,
                            "load_cases_tested": 2,
                            "failures": 0,
                            "mechanical_receipt": mechanical_receipt,
                            "mechanical_receipt_sha256": mechanical_receipt_sha256,
                        }
                    )
                findings = []
                if not passed:
                    findings.append(
                        {
                            "code": "digital-check-failed",
                            "area": capability,
                            "severity": "block",
                            "finding": "The deterministic checker found a failing measurement.",
                            "change": "Repair the exact geometry and rerun this checker.",
                            "evidence_refs": [source],
                        }
                    )
                return {
                    "artifact_sha256": received.made.artifact_sha256,
                    "capability": capability,
                    "passed": passed,
                    "checker": "test-digital-checker",
                    "checker_version": "1.2.3",
                    "config_sha256": CHECK_CONFIG_SHA256,
                    "method_class": method_class,
                    "source_refs": source_refs,
                    "observations": ["The exact sealed source passed a deterministic fixture."],
                    "metrics": metrics,
                    "findings": findings,
                }

            checks[capability] = check
        return checks

    @staticmethod
    def simulator(context, plan):
        source_sha256 = {
            entry.path: entry.sha256 for entry in context.made.artifact_manifest.entries
        }["simulator.py"]
        games = []
        # This loop is the executable simulation boundary in the fixture: it
        # produces exactly one independently seeded trace for every plan item.
        for game in plan["games"]:
            seed = game["seed"]
            winner = (game["index"] // 4) % 2
            games.append(
                {
                    "index": game["index"],
                    "seed": seed,
                    "player_styles": game["player_styles"],
                    "completed": True,
                    "turns": 7 + seed % 19,
                    "outcome": json.dumps(
                        {
                            "winner": winner,
                            "winner_style": game["player_styles"][winner],
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "issues": [],
                }
            )
        return {
            "protocol": plan["protocol"],
            "artifact_sha256": context.made.artifact_sha256,
            "simulator": "seven-steps-simulator",
            "simulator_version": "1.0.0",
            "source_path": "simulator.py",
            "source_sha256": source_sha256,
            "games": games,
        }

    def test_lane_policy_requires_real_digital_adapters_before_model_review(self):
        context = self.context("moving-machines")
        evaluator = FakeEvaluator({"reviews": []})
        with self.assertRaises(WaitingFor) as caught:
            LaneAwarePlaytester(evaluator=evaluator, capability_checks={})(context)
        self.assertEqual(
            {need.capability for need in caught.exception.needs},
            {"motion-test", "mechanical-test"},
        )
        self.assertTrue(
            all("Workshop-owned" in need.instructions for need in caught.exception.needs)
        )
        self.assertEqual(evaluator.calls, [])

    def test_passing_evidence_is_bound_to_exact_make_and_fixed_goal(self):
        context = self.context("moving-machines")
        capabilities = tuple(
            item
            for item in context.blueprint.required_capabilities("playtest")
            if item != "game-simulation"
        )
        evaluator = FakeEvaluator(review_batch(capabilities))
        result = LaneAwarePlaytester(
            evaluator=evaluator,
            capability_checks=self.digital_checks(context),
        )(context)
        self.assertTrue(result.passed)
        self.assertEqual(
            [item.playtest_id for item in result.evidence.results],
            list(context.blueprint.required_capabilities("playtest")),
        )
        for item in result.evidence.results:
            self.assertEqual(item.artifact_sha256, context.made.artifact_sha256)
            self.assertEqual(item.evidence["reward"]["goal"], DEFAULT_PLAYTEST_GOAL)
            evidence_path = context.workspace / item.evidence_ref
            self.assertEqual(
                hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                item.evidence_sha256,
            )
        self.assertEqual(
            build_artifact_manifest(
                context.workspace, created_at="content-addressed"
            ).to_dict(),
            result.evidence.evidence_manifest.to_dict(),
        )
        self.assertIn("never replace or override a failed check", evaluator.calls[0][0])
        release_needs = playtest_release_needs(
            context.blueprint, context.made, result, context.workspace
        )
        self.assertNotIn(
            "mechanical-test", {need.capability for need in release_needs}
        )
        self.assertTrue(
            (context.workspace / "receipts" / "mechanical-test.json").is_file()
        )

    def test_failed_digital_check_cannot_be_overridden_by_high_model_reward(self):
        context = self.context("moving-machines")
        capabilities = context.blueprint.required_capabilities("playtest")
        evaluator = FakeEvaluator(review_batch(capabilities, score=99))
        result = LaneAwarePlaytester(
            evaluator=evaluator,
            capability_checks=self.digital_checks(context, failing="mechanical-test"),
        )(context)
        by_id = {item.playtest_id: item for item in result.evidence.results}
        self.assertFalse(result.passed)
        self.assertFalse(by_id["mechanical-test"].passed)
        self.assertLess(
            by_id["mechanical-test"].evidence["reward"]["value"],
            DEFAULT_PLAYTEST_GOAL,
        )
        self.assertEqual(result.feedback[0].change, "Repair the exact geometry and rerun this checker.")

    def test_invented_game_never_uses_a_model_claim_as_1000_game_evidence(self):
        context = self.context("invented-games")
        capabilities = tuple(
            item
            for item in context.blueprint.required_capabilities("playtest")
            if item != "game-simulation"
        )
        evaluator = FakeEvaluator(review_batch(capabilities))
        with self.assertRaises(WaitingFor) as caught:
            LaneAwarePlaytester(
                evaluator=evaluator,
                capability_checks=self.digital_checks(context),
                game_simulator=None,
            )(context)
        self.assertEqual(caught.exception.needs[0].capability, "game-simulation")
        self.assertEqual(evaluator.calls, [])

    def test_shared_lane_proof_gaps_wait_before_ai_scores_can_claim_release(self):
        for index, (lane, capability) in enumerate(
            (
                ("classics-made-yours", "classic-rules-test"),
                ("holdable-science", "science-test"),
                ("little-worlds", "world-test"),
            )
        ):
            with self.subTest(lane=lane):
                context = self.context(lane, "proof-gap-%d" % index)
                evaluator = FakeEvaluator({"reviews": []})
                with self.assertRaises(WaitingFor) as caught:
                    LaneAwarePlaytester(
                        evaluator=evaluator,
                    )(context)
                self.assertIn(
                    capability,
                    {need.capability for need in caught.exception.needs},
                )
                self.assertEqual(evaluator.calls, [])

    def test_invented_game_passes_only_after_1000_full_seeded_traces(self):
        context = self.context("invented-games")
        capabilities = tuple(
            item
            for item in context.blueprint.required_capabilities("playtest")
            if item != "game-simulation"
        )
        result = LaneAwarePlaytester(
            evaluator=FakeEvaluator(review_batch(capabilities)),
            capability_checks=self.digital_checks(context),
            game_simulator=self.simulator,
        )(context)
        by_id = {item.playtest_id: item for item in result.evidence.results}
        simulation = by_id["game-simulation"]
        self.assertTrue(result.passed)
        self.assertEqual(simulation.evidence["completed_games"], DEFAULT_GAME_COUNT)
        self.assertEqual(simulation.evidence["terminated_games"], DEFAULT_GAME_COUNT)
        self.assertEqual(set(simulation.evidence["player_styles"]), set(GAME_STYLES))
        trace = json.loads(
            (context.workspace / simulation.evidence["trace_ref"]).read_text(encoding="utf-8")
        )
        self.assertEqual(len(trace["games"]), DEFAULT_GAME_COUNT)
        self.assertEqual(
            [item["seed"] for item in trace["games"]],
            list(range(trace["games"][0]["seed"], trace["games"][0]["seed"] + DEFAULT_GAME_COUNT)),
        )
        release_needs = playtest_release_needs(
            context.blueprint, context.made, result, context.workspace
        )
        self.assertNotIn(
            "game-simulation", {need.capability for need in release_needs}
        )

    def test_aggregate_game_claim_without_traces_fails_closed(self):
        context = self.context("invented-games")
        capabilities = tuple(
            item
            for item in context.blueprint.required_capabilities("playtest")
            if item != "game-simulation"
        )

        def aggregate_only(received, plan):
            return {
                "protocol": plan["protocol"],
                "artifact_sha256": received.made.artifact_sha256,
                "completed_games": 1_000,
                "executable": True,
                "player_styles": list(GAME_STYLES),
            }

        with self.assertRaises(WaitingFor) as caught:
            LaneAwarePlaytester(
                evaluator=FakeEvaluator(review_batch(capabilities)),
                capability_checks=self.digital_checks(context),
                game_simulator=aggregate_only,
            )(context)
        self.assertEqual(caught.exception.needs[0].capability, "game-simulation")

    def test_default_playtest_waits_when_locked_cad_runtime_is_absent(self):
        from tests.test_agent_make import FakeCadBuilder

        wish = Wish.create("default-seven", "A seven-token strategy game for my studio")
        blueprint = ToyBlueprint.for_lane("invented-games")
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept={"title": "Seven Sparks", "summary": "A finite take-away game."},
            score=91,
            target_score=85,
        )
        parts = []
        for index in range(7):
            parts.append(
                {
                    "part_id": "spark-%d" % (index + 1),
                    "name": "spark %d" % (index + 1),
                    "purpose": "One token in the finite shared supply.",
                    "shape": "cylinder",
                    "size_mm": {"x": 12, "y": 12, "z": 4},
                    "print_center_mm": {"x": 14 + index * 18, "y": 18},
                    "print_rotation_deg": 0,
                    "assembly_center_mm": {"x": 14 + index * 18, "y": 80, "z": 0},
                    "assembly_rotation_deg": 0,
                    "material": "PLA",
                }
            )
        action = {
            "title": "Seven Sparks",
            "summary": "A seven-token strategy game shaped by a studio memory.",
            "interaction": "Take one to three sparks and try to claim the last.",
            "mechanical_principle": "Seven separate tactile counters form a finite shared state.",
            "assembly": ["Place all seven sparks in the shared supply."],
            "instructions": "Take one to three sparks. The player taking the last wins.",
            "parts": parts,
            "classic_spec": {
                "enabled": False,
                "known_game": "not applicable",
                "rules_reference": "not applicable",
                "rules_unchanged": False,
            },
            "game_spec": {
                "enabled": True,
                "title": "Seven Sparks",
                "starting_tokens": 7,
                "max_take": 3,
                "last_take_wins": True,
                "theme": "Seven sparks from the first studio.",
                "token_part_ids": [part["part_id"] for part in parts],
            },
            "motion_spec": {
                "enabled": False,
                "moving_part_id": "",
                "axis": "z",
                "sweep_degrees": 1,
                "minimum_aabb_clearance_mm": 0,
            },
            "design_limitations": ["This is a constrained primitive-geometry MVP."],
        }
        maker = CodexMaker(
            creator=FakeEvaluator(action),
            evaluator=FakeEvaluator(make_verdict()),
            cad_builder=FakeCadBuilder(),
        )
        made = maker(
            MakeContext(
                wish,
                self.taste,
                blueprint,
                invented,
                1,
                (self.root / "default-game-make").absolute(),
                (),
                2,
                "leo",
            )
        )
        playtest_context = PlaytestContext(
            wish,
            self.taste,
            blueprint,
            1,
            made,
            (self.root / "default-game-playtest").absolute(),
            2,
        )
        model_capabilities = tuple(
            item
            for item in blueprint.required_capabilities("playtest")
            if item != "game-simulation"
        )
        with self.assertRaises(WaitingFor) as caught:
            with mock.patch.dict(
                os.environ,
                {"WORKSHOP_CAD_PYTHON": "/missing/workshop-cad-python"},
            ):
                LaneAwarePlaytester(
                    evaluator=FakeEvaluator(review_batch(model_capabilities))
                )(playtest_context)
        self.assertEqual(caught.exception.needs[0].capability, "cad-skill-runtime")

    def test_partial_print_override_keeps_shared_moving_make_and_playtest(self):
        from inventor_workshop.moving_machine import WorkshopMovingMachineVerifier
        from tests.test_agent_make import FakeCadBuilder, make_action
        from tests.test_moving_machine import PassingMotionBuilder

        wish = Wish.create(
            "shared-orbit",
            "A hand-turned anniversary orbit that moves on my desk",
            constraints={"lane": "moving-machines"},
        )
        blueprint = ToyBlueprint.for_lane("moving-machines")
        lane_contract = {
            "schema_version": 1,
            "lane": "moving-machines",
            "kinematic_model": {
                "input_motion": "A person turns the wheel by hand.",
                "transmission": ["The rigid wheel turns directly about Z."],
                "output_motion": "The visible wheel completes one revolution.",
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
                    "effect": "The wheel stalls or its primitive section shears.",
                    "mitigation": "Preserve swept clearance and the checked shear section.",
                }
            ],
        }
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept={
                "title": "Shared Orbit",
                "summary": "One bounded rigid orbit.",
                "lane_contract": lane_contract,
            },
            score=92,
            target_score=85,
        )
        made = CodexMaker(
            creator=FakeEvaluator(make_action("Shared Orbit")),
            evaluator=FakeEvaluator(make_verdict()),
            cad_builder=FakeCadBuilder(),
        )(
            MakeContext(
                wish,
                self.taste,
                blueprint,
                invented,
                1,
                (self.root / "shared-moving-make").absolute(),
                (),
                2,
                "bob",
            )
        )
        context = PlaytestContext(
            wish,
            self.taste,
            blueprint,
            1,
            made,
            (self.root / "shared-moving-playtest").absolute(),
            2,
        )
        def exact_print_check(received):
            source = "assembled.stl"
            inventory = {
                entry.path: entry.sha256
                for entry in received.made.artifact_manifest.entries
            }
            receipt = {
                "schema_version": 1,
                "slicer": "PrusaSlicer",
                "slicer_version": "2.9.6",
                "profiles": {
                    "printer": {"name": "printer.ini", "origin": "test-pinned", "bytes": 10, "sha256": "1" * 64},
                    "process": {"name": "process.ini", "origin": "test-pinned", "bytes": 11, "sha256": "2" * 64},
                    "filament": {"name": "filament.ini", "origin": "test-pinned", "bytes": 12, "sha256": "3" * 64},
                },
                "parts": [
                    {
                        "input_ref": source,
                        "input_sha256": inventory[source],
                        "command": ["PrusaSlicer", "--export-gcode", source],
                        "returncode": 0,
                        "stdout": "sliced",
                        "stderr": "",
                        "gcode_bytes": 100,
                        "gcode_sha256": "4" * 64,
                        "gcode_metrics": {"estimated_print_time": "4m"},
                    }
                ],
            }
            return {
                "artifact_sha256": received.made.artifact_sha256,
                "capability": "print-test",
                "passed": True,
                "checker": "test-pinned-prusa",
                "checker_version": "1.0.0",
                "config_sha256": CHECK_CONFIG_SHA256,
                "method_class": "deterministic-exact-slicer-profile",
                "source_refs": [source],
                "observations": ["Sliced the exact sealed assembly fixture."],
                "metrics": {
                    "profiles_checked": 3,
                    "parts_sliced": 1,
                    "slicer_errors": 0,
                    "slicer_receipt": receipt,
                    "slicer_receipt_sha256": hashlib.sha256(
                        json.dumps(
                            receipt,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).hexdigest(),
                },
                "findings": [],
            }

        capabilities = blueprint.required_capabilities("playtest")
        result = LaneAwarePlaytester(
            evaluator=FakeEvaluator(review_batch(capabilities)),
            capability_checks={"print-test": exact_print_check},
            moving_machine_verifier=WorkshopMovingMachineVerifier(
                cad_builder=PassingMotionBuilder()
            ),
        )(context)

        self.assertTrue(result.passed)
        by_id = {item.playtest_id: item for item in result.evidence.results}
        self.assertEqual(
            by_id["motion-test"].evidence["deterministic_check"]["checker"],
            "workshop-primitive-moving-machine",
        )
        self.assertIn("release_proof", by_id["mechanical-test"].evidence)
        self.assertIn("release_proof", by_id["motion-test"].evidence)
        self.assertTrue(
            (context.workspace / "receipts" / "moving-machine-mechanical.json").is_file()
        )

        classic_wish = Wish.create(
            "shared-checkers",
            "Checkers pieces shaped by the five jobs in my studio",
            constraints={"lane": "classics-made-yours"},
        )
        classic_blueprint = ToyBlueprint.for_lane("classics-made-yours")
        classic_action = make_action("Five-Job Checkers")
        classic_action["motion_spec"] = {
            "enabled": False,
            "moving_part_id": "",
            "axis": "z",
            "sweep_degrees": 1,
            "minimum_aabb_clearance_mm": 0,
        }
        classic_action.pop("moving_machine_binding")
        classic_action["classic_spec"] = {
            "enabled": True,
            "known_game": "checkers",
            "rules_reference": "https://wcdf.net/rules/rules_of_checkers_english.pdf",
            "rules_unchanged": True,
        }
        classic_invented = Invented(
            wish_sha256=json_sha256(classic_wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=classic_blueprint.lane,
            concept={
                "title": "Five-Job Checkers",
                "summary": "Unchanged checkers with studio-shaped pieces.",
                "lane_contract": {
                    "schema_version": 1,
                    "lane": "classics-made-yours",
                    "known_game": "checkers",
                    "rules_preserved": True,
                    "rules_preservation": {
                        "canonical_ruleset": "WCDF English draughts rules (2012)",
                        "preserved_invariants": [
                            "mandatory captures",
                            "promotion on the far rank",
                            "no legal move loses",
                        ],
                        "allowed_physical_changes": [
                            "piece silhouettes and surface storytelling"
                        ],
                    },
                    "personalization_map": [
                        {
                            "wish_detail": "the five studio jobs",
                            "physical_feature": "distinct job-shaped piece bodies",
                            "rules_effect": "none",
                        }
                    ],
                },
            },
            score=93,
            target_score=85,
        )
        classic_made = CodexMaker(
            creator=FakeEvaluator(classic_action),
            evaluator=FakeEvaluator(make_verdict()),
            cad_builder=FakeCadBuilder(),
        )(
            MakeContext(
                classic_wish,
                self.taste,
                classic_blueprint,
                classic_invented,
                1,
                (self.root / "shared-classic-make").absolute(),
                (),
                2,
                "alice",
            )
        )
        classic_context = PlaytestContext(
            classic_wish,
            self.taste,
            classic_blueprint,
            1,
            classic_made,
            (self.root / "shared-classic-playtest").absolute(),
            2,
        )
        classic_checks = self.digital_checks(classic_context)
        classic_checks.pop("classic-rules-test")
        classic_capabilities = classic_blueprint.required_capabilities("playtest")
        classic_result = LaneAwarePlaytester(
            evaluator=FakeEvaluator(review_batch(classic_capabilities)),
            capability_checks=classic_checks,
        )(classic_context)

        self.assertTrue(classic_result.passed)
        classic_by_id = {
            item.playtest_id: item for item in classic_result.evidence.results
        }
        self.assertEqual(
            classic_by_id["classic-rules-test"].evidence["deterministic_check"][
                "checker"
            ],
            "workshop-pinned-checkers-conformance",
        )
        self.assertIn(
            "release_proof",
            classic_by_id["classic-rules-test"].evidence,
        )
        self.assertTrue(
            (
                classic_context.workspace
                / "release"
                / "classic-rules-test"
                / "reference-rules.json"
            ).is_file()
        )

        rejected_context = PlaytestContext(
            classic_wish,
            self.taste,
            classic_blueprint,
            1,
            classic_made,
            (self.root / "rejected-classic-playtest").absolute(),
            2,
        )
        rejected_checks = self.digital_checks(rejected_context)
        rejected_checks.pop("classic-rules-test")
        rejected = LaneAwarePlaytester(
            evaluator=FakeEvaluator(
                review_batch(
                    classic_capabilities, failing="classic-rules-test"
                )
            ),
            capability_checks=rejected_checks,
        )(rejected_context)
        self.assertFalse(rejected.passed)
        self.assertFalse(
            (
                rejected_context.workspace
                / "release"
                / "classic-rules-test"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
