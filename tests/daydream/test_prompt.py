import hashlib
import unittest

from workshop.daydream.contracts import DAYDREAM_IDEA_KIND
from workshop.daydream.prompt import (
    DAYDREAM_CONSTITUTION,
    DAYDREAM_CONSTITUTION_SHA256,
    build_daydream_prompt,
)
from workshop.daydream.seeds import DaydreamSeed
from workshop.errors import ContractError


class PromptTest(unittest.TestCase):
    def test_prompt_names_inventor_seed_files_and_constitution(self):
        seed = DaydreamSeed(moment="a bus stop in the cold", twist="it counts something")
        prompt = build_daydream_prompt(
            inventor_name="Pico Press",
            inventor_id="pico-press",
            seed=seed,
            notebook_count=3,
            prior_work_count=22,
            portfolio_count=7,
            observed_at="2026-09-02T10:15:00Z",
        )
        for expected in (
            "Pico Press",
            "pico-press",
            "a bus stop in the cold",
            "it counts something",
            "TASTE.md",
            ".codex/agents/pico-press.toml",
            ".agents/skills/",
            "PRIOR-WORK.md",
            "PORTFOLIO.md",
            "NOTEBOOK.md",
            "VAULT.md",
            "22 entries",
            "7 entries",
            "3 theses",
            "2026-09-02T10:15:00Z",
            "work/IDEA.json",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, prompt)
        self.assertTrue(prompt.endswith(DAYDREAM_CONSTITUTION))
        self.assertLess(len(prompt.encode("utf-8")), 1024 * 1024)

    def test_constitution_is_specific_and_its_identity_is_stable(self):
        self.assertEqual(
            DAYDREAM_CONSTITUTION_SHA256,
            hashlib.sha256(DAYDREAM_CONSTITUTION.encode("utf-8")).hexdigest(),
        )
        for expected in (
            DAYDREAM_IDEA_KIND,
            "work/IDEA.json",
            "TASTE.md",
            "PRIOR-WORK.md",
            "NOTEBOOK.md",
            "live web search",
            "at least four candidates",
            "at least three meaningfully",
            "Do not search\nbackward for evidence",
            "Drop it without apology",
            "Pre-commit thesis audit",
            "same\neight independent dimensions",
            "lucky frame",
            "reject a candidate that needs a higher route",
            "world_scan",
            "human_tension",
            "anti_generic_signature",
            "theme_strip_test",
            "kill_criteria",
            "prior_art",
            "taste_fit",
            "parts_estimate",
            "keywords",
            "12",
            "0.4 mm nozzle",
            "0.8 mm absolute minimum wall",
            "Electronics, batteries",
            "^[a-z0-9][a-z0-9-]{1,31}$",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, DAYDREAM_CONSTITUTION)

    def test_prompt_validates_its_inputs(self):
        seed = DaydreamSeed(moment="x", twist="y")
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="pico-press",
                seed=seed,
                notebook_count=-1,
                prior_work_count=0,
            )
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="pico-press",
                seed={"moment": "x", "twist": "y"},
                notebook_count=0,
                prior_work_count=0,
            )
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="Pico Press",
                seed=seed,
                notebook_count=0,
                prior_work_count=0,
            )


if __name__ == "__main__":
    unittest.main()


class GoalTest(unittest.TestCase):
    def test_constitution_makes_daydream_one_native_goal_with_a_finalizer(self):
        from workshop.daydream.prompt import DAYDREAM_CONSTITUTION

        self.assertIn("One native Goal", DAYDREAM_CONSTITUTION)
        self.assertIn("exactly one Goal named\n`Daydream`", DAYDREAM_CONSTITUTION)
        self.assertIn('"$WORKSHOP_PYTHON" finalize_daydream.py', DAYDREAM_CONSTITUTION)
        self.assertIn("writes `agent-outcome.json`", DAYDREAM_CONSTITUTION)
        self.assertIn("marker by hand", DAYDREAM_CONSTITUTION)
        self.assertIn("stop immediately", DAYDREAM_CONSTITUTION)


class RouteBudgetTest(unittest.TestCase):
    def _prompt(self, effort):
        from workshop.daydream.prompt import build_daydream_prompt
        from workshop.daydream.seeds import DaydreamSeed

        return build_daydream_prompt(
            inventor_name="Sample",
            inventor_id="sample",
            seed=DaydreamSeed(moment="a bus stop in the cold", twist="it counts something"),
            notebook_count=0,
            prior_work_count=0,
            effort=effort,
        )

    def test_route_budget_is_named_only_when_the_route_is_known(self):
        from workshop.daydream.prompt import ROUTE_BUDGETS

        self.assertIn(ROUTE_BUDGETS["spark"], self._prompt(None))
        for effort in ("spark", "forge", "quest"):
            with self.subTest(effort=effort):
                prompt = self._prompt(effort)
                self.assertIn(ROUTE_BUDGETS[effort], prompt)
                self.assertLess(prompt.index("Route budget"), prompt.index("work/IDEA.json"))
        self.assertIn("There is no separate Invent stage", self._prompt("spark"))

    def test_unknown_route_is_rejected(self):
        from workshop.errors import ContractError

        with self.assertRaises(ContractError):
            self._prompt("turbo")


class JudgeCalibrationTest(unittest.TestCase):
    def test_judge_requires_grounding_without_penalizing_novelty(self):
        from workshop.daydream.prompt import JUDGE_CONSTITUTION

        self.assertIn("contextual contradiction", JUDGE_CONSTITUTION)
        self.assertIn(
            "Do not require evidence that people already demand the exact novel",
            JUDGE_CONSTITUTION,
        )
        self.assertIn("do not substitute market familiarity", JUDGE_CONSTITUTION)
