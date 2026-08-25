import unittest

from inventor_workshop.errors import ContractError
from inventor_workshop.reward_loop import RewardSignal, run_reward_loop


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


if __name__ == "__main__":
    unittest.main()
