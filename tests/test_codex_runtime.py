import os
import unittest
from unittest import mock

from inventor_workshop.agent_instructions import RewardedInstructions
from inventor_workshop.agent_invent import CodexInventor
from inventor_workshop.agent_make import CodexMaker
from inventor_workshop.agent_playtest import LaneAwarePlaytester
from inventor_workshop.codex_runtime import (
    ALLOWED_WORKSHOP_MODELS,
    CodexStructuredRunner,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.semantic_manager import CodexSemanticManager


class CodexModelPolicyTest(unittest.TestCase):
    def test_only_terra_and_luna_are_accepted_by_the_shared_runner(self):
        self.assertEqual(
            ALLOWED_WORKSHOP_MODELS,
            frozenset(("gpt-5.6-terra", "gpt-5.6-luna")),
        )
        for model in sorted(ALLOWED_WORKSHOP_MODELS):
            with self.subTest(model=model), mock.patch(
                "inventor_workshop.codex_runtime.shutil.which", return_value=None
            ):
                selected = CodexStructuredRunner(
                    model=model,
                    reasoning_effort="low",
                )
            self.assertEqual(selected.model, model)

    def test_explicit_sol_or_arbitrary_model_is_rejected_before_subprocess(self):
        runner = mock.Mock(side_effect=AssertionError("must not launch Codex"))
        for model in ("gpt-5.6-sol", "gpt-5.5", "terra", "", None):
            with self.subTest(model=model), self.assertRaises(ContractError):
                CodexStructuredRunner(
                    model=model,
                    reasoning_effort="low",
                    binary="/not/run/codex",
                    runner=runner,
                )
        runner.assert_not_called()

    def test_every_stage_model_environment_rejects_sol(self):
        cases = (
            ("WORKSHOP_MANAGER_MODEL", CodexSemanticManager),
            ("WORKSHOP_INVENT_MODEL", CodexInventor),
            ("WORKSHOP_REWARD_MODEL", CodexInventor),
            ("WORKSHOP_MAKE_MODEL", CodexMaker),
            ("WORKSHOP_MAKE_REWARD_MODEL", CodexMaker),
            ("WORKSHOP_PLAYTEST_MODEL", LaneAwarePlaytester),
            ("WORKSHOP_INSTRUCTIONS_MODEL", RewardedInstructions),
            ("WORKSHOP_INSTRUCTIONS_REWARD_MODEL", RewardedInstructions),
        )
        for variable, constructor in cases:
            with self.subTest(variable=variable), mock.patch.dict(
                os.environ,
                {variable: "gpt-5.6-sol"},
                clear=True,
            ), mock.patch(
                "inventor_workshop.codex_runtime.shutil.which", return_value=None
            ), self.assertRaises(ContractError):
                constructor()


if __name__ == "__main__":
    unittest.main()
