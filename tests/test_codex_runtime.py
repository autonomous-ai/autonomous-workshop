import json
import os
import subprocess
import unittest
from pathlib import Path
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


class EnvironmentRecordingRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((tuple(command), dict(kwargs.get("env", {}))))
        if "--version" in command:
            return subprocess.CompletedProcess(command, 0, "codex-cli 2.3.4\n", "")
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps({"ok": True}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")


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

    def test_codex_and_manager_probes_and_calls_receive_only_codex_auth(self):
        parent_environment = {
            "PATH": "/fixture/bin:/usr/bin",
            "HOME": "/fixture/home",
            "CODEX_HOME": "/fixture/codex-home",
            "OPENAI_API_KEY": "fixture-codex-auth",
            "CODEX_API_KEY": "fixture-codex-api-auth",
            "FACTORY_USERNAME": "alice",
            "FACTORY_PASSWORD": "must-not-reach-codex",
            "WORKSHOP_SHOP_TOKEN": "must-not-reach-codex",
            "AWS_SECRET_ACCESS_KEY": "must-not-reach-codex",
            "GITHUB_TOKEN": "must-not-reach-codex",
        }
        structured_runner = EnvironmentRecordingRunner()
        manager_runner = EnvironmentRecordingRunner()
        with mock.patch.dict(os.environ, parent_environment, clear=True):
            structured = CodexStructuredRunner(
                model="gpt-5.6-terra",
                reasoning_effort="low",
                binary="/fixture/codex",
                runner=structured_runner,
            )
            self.assertEqual(
                structured.invoke(
                    prompt="fixture",
                    schema={"type": "object", "additionalProperties": True},
                ),
                {"ok": True},
            )
            manager = CodexSemanticManager(
                binary="/fixture/codex",
                runner=manager_runner,
            )
            self.assertEqual(
                manager._invoke(
                    prompt="fixture",
                    schema={"type": "object", "additionalProperties": True},
                    capability="semantic-inventor-retriever",
                ),
                {"ok": True},
            )

        for calls in (structured_runner.calls, manager_runner.calls):
            self.assertEqual(len(calls), 2)
            self.assertIn("--version", calls[0][0])
            for unused_command, environment in calls:
                self.assertEqual(environment["HOME"], "/fixture/home")
                self.assertEqual(environment["CODEX_HOME"], "/fixture/codex-home")
                self.assertEqual(environment["OPENAI_API_KEY"], "fixture-codex-auth")
                self.assertEqual(environment["CODEX_API_KEY"], "fixture-codex-api-auth")
                for forbidden in (
                    "FACTORY_USERNAME",
                    "FACTORY_PASSWORD",
                    "WORKSHOP_SHOP_TOKEN",
                    "AWS_SECRET_ACCESS_KEY",
                    "GITHUB_TOKEN",
                ):
                    self.assertNotIn(forbidden, environment)


if __name__ == "__main__":
    unittest.main()
