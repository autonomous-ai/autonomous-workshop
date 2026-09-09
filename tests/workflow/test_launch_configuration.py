import unittest
from types import SimpleNamespace
from unittest import mock

from workshop.errors import ContractError
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.managers import ManagerModelSelection
from workshop.workflow.budgets import (
    BUDGETS_CAPABILITY_PATH, BUDGETS_V1_CAPABILITY_PATH, uses_command_budget,
)
from workshop.workflow.native_run import _budgeted_turn_launcher, _native_launcher
from workshop.workflow.effort import DEEP_ECONOMICS_CAPABILITY_PATH, SPARK_ECONOMICS_CAPABILITY_PATH


class LaunchConfigurationTest(unittest.TestCase):
    def checkpoint(self, *, capability=BUDGETS_CAPABILITY_PATH, effort="forge", stage="make"):
        return SimpleNamespace(
            manager_id="codex", effort=effort, stage=stage,
            input_sha256s={capability: "a" * 64,
                          DEEP_ECONOMICS_CAPABILITY_PATH: "b" * 64,
                          SPARK_ECONOMICS_CAPABILITY_PATH: "c" * 64},
        )

    def launcher(self, **kwargs):
        kwargs.setdefault("binary", "/bin/echo")
        kwargs.setdefault("cli_version", "0.153.0")
        return CodexNativeSessionLauncher(**kwargs)

    def test_budget_preserves_proof_boundary_and_gateway_configuration(self):
        original = self.launcher(
            model="gpt-6-astra", reasoning_effort="medium", timeout_seconds=960,
            model_provider="openrouter", model_provider_base_url="https://openrouter.ai/api/v1",
            auto_compact_token_limit=64000,
        )
        bounded = _budgeted_turn_launcher(self.checkpoint(), original, 3600)
        self.assertEqual(bounded.timeout_seconds, 960)
        for name in ("model", "reasoning_effort", "model_provider", "model_provider_base_url",
                     "auto_compact_token_limit", "binary", "cli_version"):
            self.assertEqual(getattr(bounded, name), getattr(original, name), name)
        self.assertEqual(bounded.runtime_profile_sha256, "a" * 64)
        self.assertEqual(_budgeted_turn_launcher(self.checkpoint(), original, 600).timeout_seconds, 600)

    def test_v1_retains_its_historical_timeout_policy(self):
        checkpoint = self.checkpoint(capability=BUDGETS_V1_CAPABILITY_PATH)
        self.assertTrue(uses_command_budget(checkpoint.input_sha256s))
        bounded = _budgeted_turn_launcher(checkpoint, self.launcher(timeout_seconds=960), 3600)
        self.assertEqual(bounded.timeout_seconds, 3600)

    def test_spark_v2_has_twenty_minute_turns(self):
        checkpoint = self.checkpoint(effort="spark")
        self.assertEqual(_budgeted_turn_launcher(checkpoint, self.launcher(), 3600).timeout_seconds, 1200)

    def test_unmarked_run_is_not_reprofiled(self):
        checkpoint = SimpleNamespace(manager_id="codex", input_sha256s={})
        original = self.launcher()
        self.assertIs(_budgeted_turn_launcher(checkpoint, original, 600), original)

    def test_astra_medium_reaches_every_spark_stage_after_budgeting(self):
        for stage in ("make", "release"):
            checkpoint = self.checkpoint(effort="spark", stage=stage)
            with mock.patch("workshop.workflow.native_run.CodexNativeSessionLauncher", side_effect=self.launcher):
                selected = _native_launcher(checkpoint, model_selection=ManagerModelSelection(
                    model="gpt-6-astra", reasoning_effort="medium"))
            bounded = _budgeted_turn_launcher(checkpoint, selected, 3600)
            self.assertEqual((bounded.model, bounded.reasoning_effort), ("gpt-6-astra", "medium"))
            self.assertEqual(bounded.timeout_seconds, 1200)
            self.assertIsNone(bounded.model_provider)

    def test_invalid_or_unsupported_reasoning_fails(self):
        for value in ("", "ultra", True):
            with self.assertRaises(ContractError):
                ManagerModelSelection(reasoning_effort=value)
        self.assertFalse(ManagerModelSelection(reasoning_effort="medium").empty)
        checkpoint = self.checkpoint()
        checkpoint.manager_id = "claude"
        with self.assertRaisesRegex(ContractError, "only.*Codex"):
            _native_launcher(checkpoint, model_selection=ManagerModelSelection(reasoning_effort="medium"))
