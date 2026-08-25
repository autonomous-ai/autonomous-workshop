import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.agent_instructions import RewardedInstructions
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.codex_runtime import CodexInvocationError
from inventor_workshop.errors import AmbiguousEffectError
from inventor_workshop.jobs import InstructionsContext, Made, Playtested, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


CONFIG_SHA256 = "c" * 64
_DEFAULT_SITE_WRITER = object()


def action(opening):
    return {
        "opening": opening,
        "before_you_begin": ["Place the board between both players."],
        "steps": [
            {"title": "Choose", "body": "Secretly choose one cap."},
            {"title": "Commit", "body": "Place it on the board."},
            {"title": "Reveal", "body": "Reveal both choices together."},
        ],
        "care_and_safety": [
            "Keep the small caps away from children under three."
        ],
        "page_use": "Choose one cap, commit, and reveal together.",
    }


def verdict(score, feedback):
    return {
        "dimensions": {
            "evidence_truth": score,
            "clarity": score,
            "completeness": score,
            "usability": score,
            "workshop_tone": score,
            "factory_handoff": score,
        },
        "feedback": [feedback],
        "hard_tensions": [],
        "assessment": feedback,
    }


class FakeCodex:
    cli_version = "9.8.7"
    reasoning_effort = "medium"

    def __init__(self, model, outputs):
        self.model = model
        self.outputs = list(outputs)
        self.prompts = []

    def invoke(self, *, prompt, schema, workspace):
        self.prompts.append((prompt, schema, workspace))
        return self.outputs.pop(0)


class RewardedInstructionsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Alice\n"
            "description: Familiar games made into personal objects.\n"
            "---\n"
            "# Alice\n\nKeep the rules exact and make the object magical.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.wish = Wish.create("pocket-duel", "A surprising pocket duel")
        self.blueprint = ToyBlueprint.for_lane("classics-made-yours")
        product = self.root / "product"
        product.mkdir()
        (product / "board.step").write_text(
            "ISO-10303-21; exact product bytes\n", encoding="utf-8"
        )
        self.made = Made.from_root(
            product,
            {
                "title": "Pocket Duel",
                "summary": "A tiny bluffing game with a satisfying reveal.",
                "lane": "classics-made-yours",
                "instructions": "Choose, commit, and reveal.",
                "components": ["board", "six caps"],
                "limitations": ["Contains small parts."],
            },
        )
        evidence = self.root / "evidence"
        result_file = evidence / "league.json"
        evidence.mkdir()
        result_file.write_text('{"completed":1000}\n', encoding="utf-8")
        evidence_manifest = build_artifact_manifest(
            evidence, created_at="content-addressed"
        )
        result = PlaytestResult.create(
            "gameplay-league",
            True,
            self.made.artifact_sha256,
            {
                "evidence_class": "ai-simulation",
                "claims": ["1,000 seeded AI games completed."],
            },
            "workshop-gameplay-league",
            "1.0.0",
            CONFIG_SHA256,
            "league.json",
            hashlib.sha256(result_file.read_bytes()).hexdigest(),
        )
        self.playtested = Playtested(
            Playtest(
                self.made.artifact_manifest,
                (result,),
                evidence_manifest=evidence_manifest,
            )
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, name="instructions"):
        return InstructionsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.root / name,
        )

    def durable_context(self, name="instructions"):
        return InstructionsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.root / name,
            reward_journal=(
                self.root / "reward-journals" / name
            ).absolute(),
        )

    @staticmethod
    def site_writer(context, sealed_root, sealed_manifest):
        del sealed_root
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-pocket-duel",
            slug="pocket-duel",
            owner_id="owner-alice",
            root_id="design-pocket-duel",
            current_history_id="history-1",
            published_history_id=None,
            status="draft",
            project_url="https://cdn.autonomous.ai/projects/history-1/",
            observed_at="2026-08-25T12:00:00+00:00",
            details={
                "instructions_sha256": sealed_manifest.artifact_sha256,
                "page_url": "https://www.autonomous.ai/factory/product/pocket-duel",
            },
        )

    def worker(
        self,
        creator_outputs,
        reward_outputs,
        site_writer=_DEFAULT_SITE_WRITER,
        **changes,
    ):
        creator = FakeCodex("gpt-5.6-terra", creator_outputs)
        evaluator = FakeCodex("gpt-5.6-luna", reward_outputs)
        evaluator.reasoning_effort = "low"
        selected_site_writer = (
            self.site_writer
            if site_writer is _DEFAULT_SITE_WRITER
            else site_writer
        )
        return (
            RewardedInstructions(
                selected_site_writer,
                creator=creator,
                evaluator=evaluator,
                **changes,
            ),
            creator,
            evaluator,
        )

    def test_manual_improves_until_fixed_reward_goal_then_seals_factory_facts(self):
        worker, creator, evaluator = self.worker(
            [action("A first attempt."), action("A tiny duel with one bright reveal.")],
            [verdict(82, "Make the opening feel more specific."), verdict(94, "Ready.")],
        )
        instructions = worker(self.context())
        self.assertEqual(len(creator.prompts), 2)
        self.assertEqual(len(evaluator.prompts), 2)
        self.assertIn("previous_reward", creator.prompts[1][0])
        page = json.loads((instructions.root / "product.json").read_text())
        self.assertEqual(page["how_to_play"], "Choose one cap, commit, and reveal together.")
        self.assertEqual(page["what_arrives"], ["board", "six caps"])
        self.assertFalse({"images", "use_case", "story_blocks"} & set(page))
        reward = json.loads(
            (instructions.root / "instructions-reward.json").read_text()
        )
        self.assertEqual(reward["goal"], 90)
        self.assertTrue(reward["result"]["reached_goal"])
        self.assertEqual(reward["result"]["steps"][-1]["reward"]["value"], 94)
        manual = (instructions.root / "INSTRUCTIONS.md").read_text()
        self.assertIn("## Before you begin", manual)
        self.assertIn("## How to play", manual)
        self.assertIn("## What's in the box", manual)
        self.assertIn("## Care and safety", manual)
        self.assertTrue(instructions.site_receipt.is_verified_draft)

    def test_durable_instructions_automatically_runs_later_batch_to_goal(self):
        worker, creator, evaluator = self.worker(
            [action("First sealed manual."), action("Improved sealed manual.")],
            [
                verdict(82, "Make the opening more specific."),
                verdict(94, "Ready."),
            ],
            max_steps=1,
        )
        context = self.durable_context("automatic-batch")

        instructions = worker(context)

        self.assertTrue(instructions.site_receipt.is_verified_draft)
        self.assertEqual(len(creator.prompts), 2)
        self.assertEqual(len(evaluator.prompts), 2)
        self.assertIn("First sealed manual.", creator.prompts[1][0])
        self.assertIn("Make the opening more specific.", creator.prompts[1][0])
        records = sorted(
            (context.reward_journal / "steps").glob("[0-9]*.json")
        )
        self.assertEqual(len(records), 2)
        binding = json.loads(
            (context.reward_journal / "binding.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            binding["binding"]["creator"]["identity"],
            "codex-instructions-policy",
        )
        self.assertEqual(
            binding["binding"]["evaluator"]["identity"],
            "codex-instructions-reward",
        )
        self.assertIn("made_manifest", binding["initial_state"]["inputs"])
        self.assertIn("playtest", binding["initial_state"]["inputs"])

    def test_durable_instructions_worker_interruption_resumes_sealed_step(self):
        class CreatorThatStopsAfterOne(FakeCodex):
            def invoke(self, *, prompt, schema, workspace):
                if self.prompts:
                    self.prompts.append((prompt, schema, workspace))
                    raise CodexInvocationError("fixture interruption")
                return super().invoke(
                    prompt=prompt, schema=schema, workspace=workspace
                )

        first_creator = CreatorThatStopsAfterOne(
            "gpt-5.6-terra", [action("Sealed before interruption.")]
        )
        first_evaluator = FakeCodex(
            "gpt-5.6-luna",
            [verdict(82, "Continue improving this exact manual.")],
        )
        first_evaluator.reasoning_effort = "low"
        first_worker = RewardedInstructions(
            self.site_writer,
            creator=first_creator,
            evaluator=first_evaluator,
            max_steps=1,
        )
        context = self.durable_context("interrupted")

        with self.assertRaises(WaitingFor) as interrupted:
            first_worker(context)
        self.assertEqual(
            interrupted.exception.needs[0].capability,
            "codex-instructions",
        )
        self.assertFalse(context.workspace.exists())

        resumed_worker, resumed_creator, resumed_evaluator = self.worker(
            [action("Recovered exact manual.")],
            [verdict(94, "Ready.")],
            max_steps=1,
        )
        instructions = resumed_worker(context)

        self.assertTrue(instructions.site_receipt.is_verified_draft)
        self.assertEqual(len(first_evaluator.prompts), 1)
        self.assertEqual(len(resumed_creator.prompts), 1)
        self.assertEqual(len(resumed_evaluator.prompts), 1)
        self.assertIn("Sealed before interruption.", resumed_creator.prompts[0][0])
        self.assertIn(
            "Continue improving this exact manual.",
            resumed_creator.prompts[0][0],
        )
        self.assertEqual(
            len(list((context.reward_journal / "steps").glob("[0-9]*.json"))),
            2,
        )

    def test_goal_exhaustion_never_lowers_goal_or_seals_a_partial_manual(self):
        worker, _, _ = self.worker(
            [action("Attempt one."), action("Attempt two.")],
            [verdict(84, "Improve."), verdict(89, "Still short.")],
            goal=90,
            max_steps=2,
        )
        context = self.context("short")
        with self.assertRaises(WaitingFor) as raised:
            worker(context)
        self.assertEqual(raised.exception.needs[0].capability, "instructions-target-score")
        self.assertFalse(context.workspace.exists())

    def test_site_ambiguity_resumes_sealed_bytes_without_rerunning_models(self):
        def ambiguous(context, sealed_root, sealed_manifest):
            del context, sealed_root, sealed_manifest
            raise AmbiguousEffectError("provider outcome unknown")

        worker, creator, evaluator = self.worker(
            [action("A clear little duel.")],
            [verdict(95, "Ready.")],
            site_writer=ambiguous,
        )
        context = self.context("resume")
        with self.assertRaises(WaitingFor) as raised:
            worker(context)
        self.assertEqual(raised.exception.needs[0].capability, "site-reconciliation")
        manifest_before = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        ).artifact_sha256
        worker.site_writer = self.site_writer
        resumed = worker.resume(context)
        self.assertEqual(len(creator.prompts), 1)
        self.assertEqual(len(evaluator.prompts), 1)
        self.assertEqual(resumed.instructions_sha256, manifest_before)

    def test_missing_factory_credentials_waits_after_seal_then_resumes_exact_bytes(self):
        worker, creator, evaluator = self.worker(
            [action("A clear little duel.")],
            [verdict(95, "Ready.")],
            site_writer=None,
        )
        context = self.context("factory-wait")

        with self.assertRaises(WaitingFor) as raised:
            worker(context)

        self.assertEqual(raised.exception.needs[0].capability, "site-page")
        self.assertTrue((context.workspace / "INSTRUCTIONS.md").is_file())
        self.assertTrue((context.workspace / "product.json").is_file())
        self.assertTrue((context.workspace / "instructions-reward.json").is_file())
        sealed_before = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        ).artifact_sha256

        credentialed_worker, resume_creator, resume_evaluator = self.worker(
            [],
            [],
            site_writer=self.site_writer,
        )
        resumed = credentialed_worker.resume(context)

        self.assertEqual(len(creator.prompts), 1)
        self.assertEqual(len(evaluator.prompts), 1)
        self.assertEqual(len(resume_creator.prompts), 0)
        self.assertEqual(len(resume_evaluator.prompts), 0)
        self.assertEqual(resumed.instructions_sha256, sealed_before)


if __name__ == "__main__":
    unittest.main()
