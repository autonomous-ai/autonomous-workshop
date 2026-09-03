import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.daydream.support import (
    build_thesis_v3_verdict_dict,
    inventor_bundle,
    sample_thesis_v3_dict,
)
from tests.invent.fake_gamevault import FakeGameVaultTransport
from workshop.daydream.contracts import Idea
from workshop.daydream.notebook import NotebookEntry
from workshop.daydream.native import (
    daydream_paths,
    run_daydream,
    wish_from_daydream,
)
from workshop.errors import ContractError


FIRST_MOMENT = datetime(2026, 9, 2, 10, 15, 0, tzinfo=timezone.utc)
SECOND_MOMENT = datetime(2026, 9, 2, 10, 16, 0, tzinfo=timezone.utc)
FIRST_ID = "daydream-20260902-101500-00000001"
SECOND_ID = "daydream-20260902-101600-00000002"


def _repaired_thesis():
    raw = copy.deepcopy(sample_thesis_v3_dict())
    raw["title"] = "Rung Chorus"
    raw["one_liner"] = (
        "Tilt a pocket rail and hear three captive beads answer in a staggered rhythm."
    )
    raw["opportunity"]["world_scan"]["observed_at"] = "2026-09-02T10:16:00Z"
    for item in raw["prior_art"]:
        item["observed_at"] = "2026-09-02T10:16:00Z"
    raw["opportunity"]["physical_opportunity"] = (
        "Turn passive waiting into a handheld, repeatable rhythm whose three "
        "thresholds can be seen and heard separately."
    )
    raw["experience"].update(
        {
            "physical_form": "A pocket rail with three separately visible captive beads.",
            "action": "Tilt the rail through one slow quarter turn.",
            "response": "Three captive beads release at visibly different thresholds.",
            "payoff": "Their separated catches compose a repeatable three-beat answer.",
            "anti_generic_signature": (
                "One tilt produces three visibly separated releases and three "
                "distinct catches."
            ),
            "theme_strip_test": (
                "With every decorative reference removed, the unequal visible "
                "releases and three-beat catch remain the entire reason to use it."
            ),
            "invent_freedom": (
                "Invent may choose rail profile, bead geometry, and catch mechanism "
                "while preserving three independently observable thresholds."
            ),
        }
    )
    raw["proof"] = {
        "mode": "acoustic",
        "observable": (
            "One fixed-view sequence must show three non-overlapping release moments "
            "and correlate each one with its own catch sound."
        ),
        "kill_criteria": [
            "Any two beads release in the same observable interval.",
            "A listener cannot match each catch to a separately visible bead release.",
        ],
    }
    raw["keywords"] = ["rail", "captive-beads", "tilt", "three-beat"]
    return raw


class _Outcome:
    def __init__(self, product_id, *, used_web_search):
        self.product_id = product_id
        self.used_web_search = used_web_search

    def to_dict(self):
        return {
            "status": "completed",
            "product_id": self.product_id,
            "used_web_search": self.used_web_search,
        }


class _ScriptedNativeRuntime:
    def __init__(self, test, ideas, decisions):
        self.test = test
        self.ideas = list(ideas)
        self.decisions = list(decisions)
        self.current_decision = None
        self.daydream_notebooks = []
        self.daydream_prompts = []

    def factory(self, manager_id, **launcher_options):
        self.test.assertEqual(manager_id, "codex")
        self.test.assertIn("timeout_seconds", launcher_options)
        return self

    def start(self, **arguments):
        run_root = Path(arguments["run_root"])
        if run_root.name == "judge-workspace":
            return self._judge(arguments, run_root)
        return self._dream(arguments, run_root)

    def _dream(self, arguments, run_root):
        self.test.assertTrue((run_root / "VAULT.json").is_file())
        self.test.assertTrue(
            (run_root / ".agents/skills/sample-inventor/SKILL.md").is_file()
        )
        self.test.assertTrue(
            (run_root / ".agents/skills/design-vault/vault_tools.py").is_file()
        )
        self.daydream_notebooks.append(
            (run_root / "NOTEBOOK.md").read_text(encoding="utf-8")
        )
        self.daydream_prompts.append(arguments["prompt"])
        idea = self.ideas.pop(0)
        notebook_path = run_root.parent.parent / "NOTEBOOK.jsonl"
        if notebook_path.is_file():
            lines = [line for line in notebook_path.read_text(encoding="utf-8").splitlines() if line]
            prior = NotebookEntry.parse(json.loads(lines[-1]))
            idea["learning"] = [
                {
                    "daydream_id": prior.daydream_id,
                    "memory_sha256": prior.sha256,
                    "disposition": "repaired",
                    "response": (
                        "Make each release independently visible and bind every "
                        "catch sound to that visible event, directly repairing the "
                        "Judge's proof-observable failure."
                    ),
                }
            ]
        self.current_decision = self.decisions.pop(0)
        (run_root / "work/IDEA.json").write_text(
            json.dumps(idea, ensure_ascii=False), encoding="utf-8"
        )
        self._finalize(run_root, role="inventor")
        return _Outcome(arguments["product_id"], used_web_search=True)

    def _judge(self, arguments, run_root):
        idea = json.loads((run_root / "IDEA.json").read_text(encoding="utf-8"))
        verdict = build_thesis_v3_verdict_dict(
            self.current_decision,
            daydream_id=arguments["product_id"].removesuffix("-judge"),
            idea_sha256=Idea.parse(idea).sha256,
            taste_sha256=hashlib.sha256(
                (run_root / "TASTE.md").read_bytes()
            ).hexdigest(),
            route="forge",
        )
        (run_root / "work/VERDICT.json").write_text(
            json.dumps(verdict, ensure_ascii=False), encoding="utf-8"
        )
        self._finalize(run_root, role="judge")
        return _Outcome(arguments["product_id"], used_web_search=False)

    def _finalize(self, run_root, *, role):
        result = subprocess.run(
            [
                sys.executable,
                str(run_root / "finalize_daydream.py"),
                "--run-root",
                str(run_root),
                "--role",
                role,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.test.assertEqual(result.returncode, 0, result.stderr)


class DaydreamLearningLoopEndToEndTest(unittest.TestCase):
    def test_judge_advice_drives_a_second_accepted_thesis(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "home"
            sources = root / "sources"
            catalog = root / "catalog"
            catalog.mkdir()
            inventor_bundle(sources)
            runtime = _ScriptedNativeRuntime(
                self,
                (sample_thesis_v3_dict(), _repaired_thesis()),
                ("dream-again", "build"),
            )
            vault = FakeGameVaultTransport().vault()

            rejected = run_daydream(
                "sample",
                source_root=sources,
                repository_root=catalog,
                home=home,
                launcher_factory=runtime.factory,
                moment=FIRST_MOMENT,
                daydream_id=FIRST_ID,
                effort="forge",
                vault_loader=lambda: vault,
            )
            self.assertEqual(rejected.verdict.decision, "dream-again")
            with self.assertRaisesRegex(ContractError, "Judge-accepted"):
                wish_from_daydream(rejected)

            accepted = run_daydream(
                "sample",
                source_root=sources,
                repository_root=catalog,
                home=home,
                launcher_factory=runtime.factory,
                moment=SECOND_MOMENT,
                daydream_id=SECOND_ID,
                effort="forge",
                vault_loader=lambda: vault,
            )
            self.assertEqual(accepted.verdict.decision, "build")
            wish = wish_from_daydream(accepted, wish_id="wish-repaired-thesis")
            self.assertEqual(wish.context["daydream_id"], SECOND_ID)
            self.assertEqual(wish.context["route"], "forge")
            self.assertEqual(wish.context["provenance_sha256"], accepted.provenance.sha256)

            second_memory = runtime.daydream_notebooks[1]
            self.assertIn("Judge prediction: dream-again", second_memory)
            self.assertIn("proof_observable", second_memory)
            self.assertIn(
                "make the unequal catch sequence independently observable",
                second_memory,
            )
            self.assertIn("Anti-generic signature", second_memory)
            self.assertIn("live web search", runtime.daydream_prompts[1])
            self.assertTrue(
                daydream_paths("sample", SECOND_ID, home=home).host_state.joinpath(
                    "PROVENANCE.json"
                ).is_file()
            )
            self.assertEqual(runtime.ideas, [])
            self.assertEqual(runtime.decisions, [])


if __name__ == "__main__":
    unittest.main()
