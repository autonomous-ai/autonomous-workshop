import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ContractError
from inventor_workshop.reward_loop import (
    RewardLoopBinding,
    RewardSignal,
    json_sha256,
    run_reward_loop,
)


SHA = "a" * 64


class RewardLoopTest(unittest.TestCase):
    def signal(self, value, goal=80):
        return RewardSignal(
            value,
            goal,
            {"fit": value},
            ("Improve the fit." if value < goal else "Goal reached.",),
            "fixture-reward",
            "1.0.0",
            SHA,
        )

    def binding(self, initial_state, *, max_steps=1, inputs=None):
        inputs = inputs or {"wish": "exact wish"}
        return RewardLoopBinding(
            "invent",
            json_sha256(inputs),
            json_sha256(initial_state),
            80,
            max_steps,
            20,
            "fixture-creator",
            "1.0.0",
            "b" * 64,
            "fixture-reward",
            "1.0.0",
            SHA,
        )

    def test_state_action_reward_loop_stops_only_at_the_goal(self):
        def observe(state, step):
            return {"attempt": step, "value": state["value"]}

        def act(observation, step):
            return {"proposal": observation["value"] + step}

        def environment(state, action, step):
            del state, action
            value = 60 if step == 1 else 88
            return {"value": value}, self.signal(value)

        result = run_reward_loop(
            {"value": 0},
            observe=observe,
            act=act,
            environment=environment,
            goal=80,
            max_steps=3,
        )
        self.assertTrue(result.reached_goal)
        self.assertEqual(len(result.steps), 2)
        self.assertEqual(result.reward.value, 88)
        self.assertEqual(len(result.steps[0].action_sha256), 64)

    def test_budget_exhaustion_never_lowers_the_goal(self):
        result = run_reward_loop(
            {"value": 0},
            observe=lambda state, step: {"step": step},
            act=lambda observation, step: {"attempt": step},
            environment=lambda state, action, step: (
                {"value": step},
                self.signal(79),
            ),
            goal=80,
            max_steps=2,
        )
        self.assertFalse(result.reached_goal)
        self.assertEqual(result.reward.goal, 80)
        self.assertEqual(len(result.steps), 2)

    def test_environment_cannot_change_the_goal(self):
        with self.assertRaisesRegex(ContractError, "changed the goal"):
            run_reward_loop(
                {"value": 0},
                observe=lambda state, step: {"step": step},
                act=lambda observation, step: {"attempt": step},
                environment=lambda state, action, step: (
                    {"value": 1},
                    self.signal(90, goal=90),
                ),
                goal=80,
                max_steps=1,
            )

    def test_durable_resume_appends_without_rerunning_accepted_actions_or_rewards(self):
        initial = {"value": 0}
        creator_steps = []
        evaluator_steps = []

        def act(observation, step):
            creator_steps.append(step)
            return {"proposal": observation["value"] + step}

        def environment(state, action, step):
            del state, action
            evaluator_steps.append(step)
            value = 70 if step == 1 else 90
            return {"value": value}, self.signal(value)

        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "reward-loops" / "invent"
            binding = self.binding(initial)
            first = run_reward_loop(
                initial,
                observe=lambda state, step: {"value": state["value"], "step": step},
                act=act,
                environment=environment,
                goal=80,
                max_steps=1,
                journal_path=journal,
                binding=binding,
            )
            resumed = run_reward_loop(
                initial,
                observe=lambda state, step: {"value": state["value"], "step": step},
                act=act,
                environment=environment,
                goal=80,
                max_steps=1,
                journal_path=journal,
                binding=binding,
            )

            self.assertFalse(first.reached_goal)
            self.assertTrue(resumed.reached_goal)
            self.assertEqual(creator_steps, [1, 2])
            self.assertEqual(evaluator_steps, [1, 2])
            self.assertEqual([item.step for item in resumed.steps], [1, 2])
            records = sorted((journal / "steps").glob("[0-9]*.json"))
            self.assertEqual(len(records), 2)
            sealed = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(sealed["observation"], {"step": 1, "value": 0})
            self.assertEqual(sealed["action"], {"proposal": 1})
            self.assertEqual(sealed["next_state"], {"value": 70})
            self.assertEqual(sealed["reward"]["feedback"], ["Improve the fit."])
            manifest = json.loads(
                (journal / "binding.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["binding"]["creator"]["identity"], "fixture-creator"
            )
            self.assertEqual(
                manifest["binding"]["evaluator"]["identity"], "fixture-reward"
            )

    def test_crash_resumes_from_last_completely_sealed_step(self):
        initial = {"value": 0}
        calls = []
        crash = {"once": True}

        def environment(state, action, step):
            del state, action
            calls.append(("reward", step))
            if step == 2 and crash["once"]:
                crash["once"] = False
                raise RuntimeError("power loss before seal")
            value = 90 if step == 3 else 70
            return {"value": value}, self.signal(value)

        def act(observation, step):
            del observation
            calls.append(("action", step))
            return {"proposal": step}

        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "reward-loops" / "invent"
            binding = self.binding(initial, max_steps=3)
            with self.assertRaisesRegex(RuntimeError, "power loss"):
                run_reward_loop(
                    initial,
                    observe=lambda state, step: {"state": state["value"], "step": step},
                    act=act,
                    environment=environment,
                    goal=80,
                    max_steps=3,
                    journal_path=journal,
                    binding=binding,
                )
            result = run_reward_loop(
                initial,
                observe=lambda state, step: {"state": state["value"], "step": step},
                act=act,
                environment=environment,
                goal=80,
                max_steps=3,
                journal_path=journal,
                binding=binding,
            )

            self.assertTrue(result.reached_goal)
            self.assertEqual(calls.count(("action", 1)), 1)
            self.assertEqual(calls.count(("reward", 1)), 1)
            self.assertEqual(calls.count(("action", 2)), 2)
            self.assertEqual([item.step for item in result.steps], [1, 2, 3])

    def test_tamper_and_context_swap_fail_before_new_work(self):
        initial = {"value": 0}
        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "reward-loops" / "invent"
            binding = self.binding(initial)
            run_reward_loop(
                initial,
                observe=lambda state, step: {"step": step},
                act=lambda observation, step: {"attempt": step},
                environment=lambda state, action, step: (
                    {"value": 70},
                    self.signal(70),
                ),
                goal=80,
                max_steps=1,
                journal_path=journal,
                binding=binding,
            )
            step_path = next((journal / "steps").glob("[0-9]*.json"))
            step_path.write_bytes(step_path.read_bytes() + b" ")
            calls = []
            with self.assertRaisesRegex(ContractError, "content address"):
                run_reward_loop(
                    initial,
                    observe=lambda state, step: {"step": step},
                    act=lambda observation, step: calls.append(step) or {"attempt": step},
                    environment=lambda state, action, step: (
                        {"value": 90},
                        self.signal(90),
                    ),
                    goal=80,
                    max_steps=1,
                    journal_path=journal,
                    binding=binding,
                )
            self.assertEqual(calls, [])

        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "reward-loops" / "invent"
            binding = self.binding(initial)
            run_reward_loop(
                initial,
                observe=lambda state, step: {"step": step},
                act=lambda observation, step: {"attempt": step},
                environment=lambda state, action, step: (
                    {"value": 70},
                    self.signal(70),
                ),
                goal=80,
                max_steps=1,
                journal_path=journal,
                binding=binding,
            )
            swapped = {"value": 999}
            with self.assertRaisesRegex(ContractError, "another initial state"):
                run_reward_loop(
                    swapped,
                    observe=lambda state, step: {"step": step},
                    act=lambda observation, step: {"attempt": step},
                    environment=lambda state, action, step: (
                        {"value": 90},
                        self.signal(90),
                    ),
                    goal=80,
                    max_steps=1,
                    journal_path=journal,
                    binding=binding,
                )

    def test_symlinked_journal_or_step_is_never_followed(self):
        initial = {"value": 0}
        binding = self.binding(initial)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            journal = root / "journal"
            journal.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ContractError, "regular directory"):
                run_reward_loop(
                    initial,
                    observe=lambda state, step: {"step": step},
                    act=lambda observation, step: {"attempt": step},
                    environment=lambda state, action, step: (
                        {"value": 90},
                        self.signal(90),
                    ),
                    goal=80,
                    max_steps=1,
                    journal_path=journal,
                    binding=binding,
                )

        with tempfile.TemporaryDirectory() as temporary:
            journal = Path(temporary) / "reward-loops" / "invent"
            run_reward_loop(
                initial,
                observe=lambda state, step: {"step": step},
                act=lambda observation, step: {"attempt": step},
                environment=lambda state, action, step: (
                    {"value": 70},
                    self.signal(70),
                ),
                goal=80,
                max_steps=1,
                journal_path=journal,
                binding=binding,
            )
            step = next((journal / "steps").glob("[0-9]*.json"))
            backup = step.with_suffix(".backup")
            step.rename(backup)
            step.symlink_to(backup.name)
            with self.assertRaises(ContractError):
                run_reward_loop(
                    initial,
                    observe=lambda state, step: {"step": step},
                    act=lambda observation, step: {"attempt": step},
                    environment=lambda state, action, step: (
                        {"value": 90},
                        self.signal(90),
                    ),
                    goal=80,
                    max_steps=1,
                    journal_path=journal,
                    binding=binding,
                )


if __name__ == "__main__":
    unittest.main()
