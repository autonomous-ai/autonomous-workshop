import hashlib
import json
import tempfile
import unittest
from pathlib import Path

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

    def context(self, lane, suffix="one"):
        artifact = self.root / ("artifact-" + suffix)
        artifact.mkdir()
        (artifact / "rules.md").write_text(
            "Every legal turn advances one marker. The first to seven wins.\n",
            encoding="utf-8",
        )
        (artifact / "toy.step").write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
        (artifact / "toy.stl").write_text("solid toy\nendsolid toy\n", encoding="utf-8")
        (artifact / "simulator.py").write_text(
            "# Exact deterministic simulator source used by the test adapter.\n",
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
        for capability in context.blueprint.required_capabilities("playtest"):
            if capability not in DETERMINISTIC_CAPABILITIES:
                continue
            source = "rules.md" if capability == "classic-rules-test" else (
                "toy.stl" if capability == "print-test" else "toy.step"
            )

            def check(received, capability=capability, source=source):
                passed = capability != failing
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
                    "method_class": "deterministic-digital-check",
                    "source_refs": [source],
                    "observations": ["The exact sealed source passed a deterministic fixture."],
                    "metrics": {"checked": 1, "failures": 0 if passed else 1},
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
            games.append(
                {
                    "index": game["index"],
                    "seed": seed,
                    "player_styles": game["player_styles"],
                    "completed": True,
                    "turns": 7 + seed % 19,
                    "outcome": "first" if seed % 2 else "second",
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
            {"motion-test", "mechanical-test", "print-test"},
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

    def test_agent_make_game_runs_through_all_default_playtest_adapters(self):
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
            creator=FakeEvaluator(action), evaluator=FakeEvaluator(make_verdict())
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
        result = LaneAwarePlaytester(
            evaluator=FakeEvaluator(review_batch(model_capabilities))
        )(playtest_context)
        self.assertTrue(result.passed)
        simulation = {
            item.playtest_id: item for item in result.evidence.results
        }["game-simulation"]
        self.assertEqual(simulation.evidence["completed_games"], 1_000)
        self.assertEqual(
            simulation.evidence["simulator"]["source_path"], "game/simulate.py"
        )


if __name__ == "__main__":
    unittest.main()
