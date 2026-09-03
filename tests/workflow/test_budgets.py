import unittest

from workshop.errors import ContractError
from workshop.workflow.budgets import (
    BUDGETS_CAPABILITY_PATH,
    MAX_TURN_SECONDS,
    MIN_TURN_SECONDS,
    RUN_BUDGET_SECONDS,
    STEP_BUDGET_SECONDS,
    CommandBudget,
    uses_command_budget,
)


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class CommandBudgetTest(unittest.TestCase):
    def test_defaults_are_one_hour_per_step_and_three_hours_per_command(self):
        budget = CommandBudget()
        self.assertEqual(budget.step_seconds, 60 * 60)
        self.assertEqual(budget.run_seconds, 3 * 60 * 60)
        self.assertEqual(STEP_BUDGET_SECONDS, 3_600)
        self.assertEqual(RUN_BUDGET_SECONDS, 10_800)
        self.assertEqual(budget.turn_timeout_seconds("make"), MAX_TURN_SECONDS)
        self.assertIsNone(budget.exhausted("make"))
        self.assertEqual(budget.to_dict()["run"], {"used_seconds": 0, "limit_seconds": 10_800})
        self.assertEqual(budget.to_dict()["steps"], {})

    def test_a_turn_never_outlives_its_step_or_the_run(self):
        budget = CommandBudget()
        budget.spend("make", 40 * 60)
        self.assertEqual(budget.turn_timeout_seconds("make"), 20 * 60)
        # A different step still has its own full hour, bounded by the run.
        self.assertEqual(budget.turn_timeout_seconds("release"), MAX_TURN_SECONDS)
        budget.spend("invent", 60 * 60)
        budget.spend("playtest", 55 * 60)
        # 40 + 60 + 55 = 155 minutes of 180 leaves 25 for any step.
        self.assertEqual(budget.turn_timeout_seconds("release"), 25 * 60)

    def test_a_step_clock_and_the_run_clock_each_end_the_command(self):
        budget = CommandBudget()
        budget.spend("make", STEP_BUDGET_SECONDS - 30)
        self.assertEqual(budget.exhausted("make"), "step")
        self.assertIsNone(budget.exhausted("release"))
        message = budget.exhausted_message("make", "step", "wish-1")
        self.assertIn("Make used its 60-minute budget (59 minutes spent)", message)
        self.assertIn("workshop resume wish-1", message)

        budget = CommandBudget()
        budget.spend("make", RUN_BUDGET_SECONDS - 10)
        self.assertEqual(budget.exhausted("release"), "run")
        message = budget.exhausted_message("release", "run", "wish-2")
        self.assertIn("This run used its 180-minute budget", message)

    def test_a_turn_timeout_never_falls_below_the_floor(self):
        budget = CommandBudget()
        budget.spend("make", STEP_BUDGET_SECONDS - 5)
        self.assertEqual(budget.turn_timeout_seconds("make"), MIN_TURN_SECONDS)

    def test_spend_since_measures_the_injected_clock(self):
        clock = _Clock()
        budget = CommandBudget(clock=clock)
        mark = budget.started()
        clock.advance(90.5)
        self.assertAlmostEqual(budget.spend_since("make", mark), 90.5)
        self.assertAlmostEqual(budget.spent("make"), 90.5)
        self.assertAlmostEqual(budget.spent_total, 90.5)
        # A clock that goes backwards never credits time.
        mark = budget.started()
        clock.advance(-10)
        self.assertEqual(budget.spend_since("make", mark), 0.0)
        self.assertEqual(budget.to_dict()["steps"]["make"]["used_seconds"], 90)

    def test_contract_is_strict(self):
        for kwargs in (
            {"step_seconds": 0},
            {"step_seconds": 25 * 60 * 60},
            {"run_seconds": 0},
            {"step_seconds": 2 * 60 * 60, "run_seconds": 60 * 60},
            {"clock": "tick"},
            {"step_seconds": 60.0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ContractError):
                CommandBudget(**kwargs)
        with self.assertRaises(ContractError):
            CommandBudget().spend("make", -1)

    def test_capability_path_selects_the_model(self):
        self.assertTrue(uses_command_budget({BUDGETS_CAPABILITY_PATH: "a" * 64}))
        self.assertFalse(uses_command_budget({}))
        self.assertFalse(
            uses_command_budget(
                {".agents/skills/autonomous-workshop/references/spark-economics-v3.md": "a" * 64}
            )
        )


if __name__ == "__main__":
    unittest.main()
