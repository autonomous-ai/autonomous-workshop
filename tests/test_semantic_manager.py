import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import WaitingFor
from inventor_workshop.make import Wish, generate_wish_id
from inventor_workshop.manager import WorkshopManager
from inventor_workshop.semantic_manager import (
    DEFAULT_MANAGER_MODEL,
    CodexSemanticManager,
)


ROOT = Path(__file__).resolve().parents[1]


class StructuredRunner:
    """Write deterministic structured CLI results without making model calls."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, command, **kwargs):
        output = Path(command[command.index("--output-last-message") + 1])
        schema = Path(command[command.index("--output-schema") + 1])
        prompt = kwargs["input"]
        self.calls.append(
            {
                "command": tuple(command),
                "prompt": prompt,
                "schema": json.loads(schema.read_text(encoding="utf-8")),
            }
        )
        result = self.outputs.pop(0)
        if callable(result):
            result = result(prompt)
        output.write_text(json.dumps(result), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def judge_result(prompt, *, tie=False, stale=False):
    data = json.loads(prompt.split("FINALIST DATA:\n", 1)[1])
    scores = {"bob": 97, "eve": 62, "ivy": 55}
    assessments = []
    for finalist in data["finalists"]:
        inventor_id = finalist["id"]
        accepted = inventor_id == "bob"
        tensions = [] if accepted else ["Its full Taste puts this play pattern out of scope."]
        score = scores.get(inventor_id, 50)
        if tie and inventor_id in ("bob", "eve"):
            accepted = True
            tensions = []
            score = 90
        digest = finalist["taste"]["sha256"]
        if stale and inventor_id == "bob":
            digest = "0" * 64
        assessments.append(
            {
                "inventor_id": inventor_id,
                "taste_sha256": digest,
                "score": score,
                "accepted": accepted,
                "explanation": "%s was evaluated from the complete Taste." % inventor_id,
                "tensions": tensions,
            }
        )
    return {
        "selected_inventor_id": "bob",
        "assessments": assessments,
    }


class SemanticManagerTest(unittest.TestCase):
    def semantic_manager(self, runner, *, model=DEFAULT_MANAGER_MODEL):
        semantic = CodexSemanticManager(
            binary="/fixture/codex",
            model=model,
            runner=runner,
            cli_version="2.3.4",
        )
        manager = WorkshopManager(
            root=ROOT,
            retriever=semantic.retrieve,
            judge=semantic.judge,
            judge_identity=semantic.judge_identity,
            judge_version=semantic.judge_version,
            judge_config_sha256=semantic.judge_config_sha256,
        )
        return semantic, manager

    @staticmethod
    def wish():
        return Wish.create(
            "wish-fixture",
            "I wish for a wind-up version of my dog that walks across my desk.",
        )

    def assert_waits_for(self, expected_capability, outputs):
        runner = StructuredRunner(outputs)
        _, manager = self.semantic_manager(runner)
        with self.assertRaises(WaitingFor) as raised:
            manager.assign(self.wish(), playtest_rounds=4)
        self.assertEqual(
            tuple(item.capability for item in raised.exception.needs),
            (expected_capability,),
        )
        return runner

    def test_generated_wish_id_is_opaque_and_deterministic_when_seeded(self):
        identifier = generate_wish_id(
            moment=datetime(2026, 8, 25, 7, 30, 5, tzinfo=timezone.utc),
            token="abc123ef",
        )
        self.assertEqual(identifier, "wish-20260825-073005-abc123ef")
        self.assertNotIn("dog", identifier)

    def test_shortlists_descriptions_then_judges_complete_tastes(self):
        runner = StructuredRunner(
            [
                {
                    "inventor_ids": ["eve", "bob", "ivy"],
                    "rationale": (
                        "Eve shares the dog theme, while Bob owns purposeful motion; "
                        "their complete boundaries must decide it."
                    ),
                },
                judge_result,
            ]
        )
        semantic, manager = self.semantic_manager(runner)
        assignment = manager.assign(self.wish(), playtest_rounds=4)

        self.assertEqual(assignment.inventor_id, "bob")
        self.assertEqual(assignment.decision.fit.score, 97)
        self.assertEqual(
            assignment.decision.context.shortlist.inventor_ids,
            ("eve", "bob", "ivy"),
        )
        self.assertEqual(len(runner.calls), 2)
        shortlist_call, judge_call = runner.calls

        self.assertIn("one-line descriptions", shortlist_call["prompt"])
        self.assertIn("Do not choose the winner yet", shortlist_call["prompt"])
        retrieval_data = json.loads(shortlist_call["prompt"].split("DATA:\n", 1)[1])
        for card in retrieval_data["catalog_page"]["cards"]:
            self.assertIn("description", card)
            self.assertNotIn("taste", card)
            self.assertNotIn("content", card)
        self.assertEqual(
            shortlist_call["schema"]["required"],
            ["inventor_ids", "rationale"],
        )

        self.assertIn("complete exact TASTE.md", judge_call["prompt"])
        finalist_data = json.loads(
            judge_call["prompt"].split("FINALIST DATA:\n", 1)[1]
        )
        self.assertEqual(
            tuple(item["id"] for item in finalist_data["finalists"]),
            ("eve", "bob", "ivy"),
        )
        for finalist in finalist_data["finalists"]:
            expected_taste = (
                ROOT / "inventors" / finalist["id"] / "TASTE.md"
            ).read_text(encoding="utf-8")
            self.assertEqual(finalist["taste"]["content"], expected_taste)
            self.assertEqual(len(finalist["taste"]["sha256"]), 64)
        self.assertEqual(
            judge_call["schema"]["required"],
            ["selected_inventor_id", "assessments"],
        )

        for call in runner.calls:
            command = call["command"]
            self.assertEqual(
                command[command.index("--model") + 1],
                DEFAULT_MANAGER_MODEL,
            )
            self.assertNotIn("sol", command)

        receipt = assignment.decision.audit_receipt()
        self.assertEqual(len(receipt["shortlist"]["cards"]), 3)
        self.assertEqual(len(receipt["finalists_sha256"]), 64)
        self.assertEqual(
            receipt["judge"]["config_sha256"], semantic.judge_config_sha256
        )
        self.assertEqual(
            receipt["selected"]["taste_sha256"], assignment.taste_sha256
        )
        self.assertEqual(len(receipt["selected"]["taste_sha256"]), 64)

    def test_shortlist_must_contain_multiple_known_distinct_candidates(self):
        invalid_outputs = (
            {"inventor_ids": ["bob"], "rationale": "Premature winner."},
            {
                "inventor_ids": ["bob", "bob"],
                "rationale": "Duplicate finalist.",
            },
            {
                "inventor_ids": ["bob", "not-in-the-catalog"],
                "rationale": "Unknown finalist.",
            },
        )
        for output in invalid_outputs:
            with self.subTest(output=output):
                runner = self.assert_waits_for(
                    "semantic-inventor-retriever",
                    [output],
                )
                self.assertEqual(len(runner.calls), 1)

    def test_full_taste_judge_rejects_stale_hashes_and_incomplete_assessments(self):
        shortlist = {
            "inventor_ids": ["bob", "eve", "ivy"],
            "rationale": "Three finalists need their complete Tastes compared.",
        }

        def incomplete(prompt):
            payload = judge_result(prompt)
            payload["assessments"].pop()
            return payload

        for output in (lambda prompt: judge_result(prompt, stale=True), incomplete):
            with self.subTest(output=output):
                runner = self.assert_waits_for(
                    "semantic-taste-judge",
                    [shortlist, output],
                )
                self.assertEqual(len(runner.calls), 2)

    def test_full_taste_judge_fails_closed_on_an_ambiguous_winner(self):
        runner = self.assert_waits_for(
            "semantic-taste-judge",
            [
                {
                    "inventor_ids": ["bob", "eve"],
                    "rationale": "Both deserve a complete-Taste comparison.",
                },
                lambda prompt: judge_result(prompt, tie=True),
            ],
        )
        self.assertEqual(len(runner.calls), 2)
        self.assertIn("uniquely highest score", runner.calls[1]["prompt"])

    def test_all_rejected_tastes_use_the_managers_no_fit_path(self):
        def no_fit(prompt):
            payload = judge_result(prompt)
            payload["selected_inventor_id"] = ""
            for assessment in payload["assessments"]:
                assessment["accepted"] = False
                assessment["tensions"] = [
                    "Its complete Taste has a hard boundary against this Wish."
                ]
            return payload

        runner = self.assert_waits_for(
            "inventor-fit",
            [
                {
                    "inventor_ids": ["bob", "eve"],
                    "rationale": "Both need a complete-Taste comparison.",
                },
                no_fit,
            ],
        )
        self.assertEqual(len(runner.calls), 2)
        self.assertIn("return an empty selected_inventor_id", runner.calls[1]["prompt"])

    def test_manager_models_are_limited_to_terra_or_luna(self):
        runner = StructuredRunner([])
        terra = CodexSemanticManager(
            binary="/fixture/codex",
            runner=runner,
            cli_version="2.3.4",
        )
        luna = CodexSemanticManager(
            binary="/fixture/codex",
            model="gpt-5.6-luna",
            runner=runner,
            cli_version="2.3.4",
        )
        self.assertEqual(terra.model, "gpt-5.6-terra")
        self.assertEqual(luna.model, "gpt-5.6-luna")
        self.assertIn(terra.model, terra.retriever_version)
        self.assertIn(luna.model, luna.retriever_version)
        self.assertNotEqual(terra.retriever_version, luna.retriever_version)
        with self.assertRaisesRegex(ContractError, "terra or gpt-5.6-luna"):
            CodexSemanticManager(
                binary="/fixture/codex",
                model="gpt-5.6-sol",
                runner=runner,
                cli_version="2.3.4",
            )


if __name__ == "__main__":
    unittest.main()
