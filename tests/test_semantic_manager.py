import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from inventor_workshop.make import Wish, generate_wish_id
from inventor_workshop.manager import WorkshopManager
from inventor_workshop.semantic_manager import (
    DEFAULT_MANAGER_MODEL,
    CodexSemanticManager,
)


ROOT = Path(__file__).resolve().parents[1]


class SemanticManagerTest(unittest.TestCase):
    def test_generated_wish_id_is_opaque_and_deterministic_when_seeded(self):
        identifier = generate_wish_id(
            moment=datetime(2026, 8, 25, 7, 30, 5, tzinfo=timezone.utc),
            token="abc123ef",
        )
        self.assertEqual(identifier, "wish-20260825-073005-abc123ef")
        self.assertNotIn("dog", identifier)

    def test_small_model_matches_only_compact_descriptions(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            if command[-1] == "--version":
                return SimpleNamespace(returncode=0, stdout="codex-cli 2.3.4\n")
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text(
                json.dumps(
                    {
                        "inventor_id": "bob",
                        "score": 96,
                        "explanation": (
                            "Bob makes movement the magic through a printable mechanism."
                        ),
                    }
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        semantic = CodexSemanticManager(runner=runner)
        manager = WorkshopManager(
            root=ROOT,
            retriever=semantic.retrieve,
            judge=semantic.judge,
            judge_identity=semantic.judge_identity,
            judge_version=semantic.judge_version,
            judge_config_sha256=semantic.judge_config_sha256,
        )
        assignment = manager.assign(
            Wish.create(
                "wish-fixture",
                "I wish for a wind-up version of my dog that walks across my desk.",
            ),
            playtest_rounds=4,
        )
        self.assertEqual(assignment.inventor_id, "bob")
        self.assertEqual(assignment.decision.fit.score, 96)
        self.assertEqual(len(calls), 2)
        invocation, options = calls[1]
        self.assertIn("--model", invocation)
        self.assertEqual(invocation[invocation.index("--model") + 1], DEFAULT_MANAGER_MODEL)
        prompt = options["input"]
        self.assertIn("compact Taste names and descriptions", prompt)
        self.assertNotIn("# Bob's Taste", prompt)
        self.assertNotIn("## North star", prompt)


if __name__ == "__main__":
    unittest.main()
