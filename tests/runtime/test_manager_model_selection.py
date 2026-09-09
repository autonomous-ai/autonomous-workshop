"""Launch-time model selection shared by every Manager adapter."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from workshop.errors import ContractError
from workshop.runtime.claude import (
    ClaudeInvocationError,
    ClaudeNativeSessionLauncher,
)
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.execution import (
    CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST,
    codex_subprocess_environment,
)
from workshop.runtime.grok import GrokNativeSessionLauncher
from workshop.runtime.managers import (
    ManagerModelSelection,
    manager_model,
    manager_provider_base_url,
    manager_provider_id,
)


class _Policy:
    permission_config_arguments = ()


class ManagerModelValidationTest(unittest.TestCase):
    def test_accepts_vendor_qualified_and_suffixed_routes(self) -> None:
        for value in (
            "gpt-5.6-sol",
            "claude-fable-5",
            "opus",
            "anthropic/claude-sonnet-4.5",
            "meta-llama/llama-4:free",
            "~anthropic/claude-sonnet-latest",
        ):
            self.assertEqual(manager_model(value), value)

    def test_rejects_argv_and_shell_hostile_values(self) -> None:
        for value in ("", "-m", "--model", "a b", "x" * 129, "$(id)", "a;b", None, 5):
            with self.assertRaises(ContractError):
                manager_model(value)

    def test_provider_base_url_requires_https_or_loopback(self) -> None:
        self.assertTrue(manager_provider_base_url("https://openrouter.ai/api/v1"))
        self.assertTrue(manager_provider_base_url("http://localhost:8080/v1"))
        for value in ("http://example.com", "ftp://x", "javascript:x", "", "https://"):
            with self.assertRaises(ContractError):
                manager_provider_base_url(value)

    def test_provider_id_is_a_bounded_config_key_segment(self) -> None:
        self.assertEqual(manager_provider_id("openrouter"), "openrouter")
        for value in ("", "Open", "9x", "a.b", "x" * 33):
            with self.assertRaises(ContractError):
                manager_provider_id(value)

    def test_selection_requires_provider_for_a_base_url(self) -> None:
        self.assertTrue(ManagerModelSelection().empty)
        self.assertFalse(ManagerModelSelection(model="opus").empty)
        with self.assertRaises(ContractError):
            ManagerModelSelection(provider_base_url="https://openrouter.ai/api/v1")


class CodexModelSelectionTest(unittest.TestCase):
    def _launcher(self, **kwargs) -> CodexNativeSessionLauncher:
        return CodexNativeSessionLauncher(
            binary="/bin/echo", cli_version="0.145.0", **kwargs
        )

    def test_non_default_model_reaches_argv(self) -> None:
        command = self._launcher(model="gpt-5.6-luna")._start_command(
            Path("/tmp/run"), _Policy()
        )
        self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-luna")

    def test_provider_override_is_explicit_in_both_commands(self) -> None:
        launcher = self._launcher(
            model="anthropic/claude-sonnet-4.5",
            model_provider="openrouter",
            model_provider_base_url="https://openrouter.ai/api/v1",
        )
        for command in (
            launcher._start_command(Path("/tmp/run"), _Policy()),
            launcher._resume_command("thread-1", Path("/tmp/run"), _Policy()),
        ):
            self.assertIn("model_provider=openrouter", command)
            self.assertIn(
                'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"',
                command,
            )
            self.assertIn(
                'model_providers.openrouter.env_key="OPENROUTER_API_KEY"', command
            )
            self.assertEqual(
                command[command.index("--model") + 1],
                "anthropic/claude-sonnet-4.5",
            )

    def test_default_run_declares_no_provider(self) -> None:
        command = self._launcher()._start_command(Path("/tmp/run"), _Policy())
        self.assertFalse([a for a in command if a.startswith("model_provider")])

    def test_base_url_without_provider_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            self._launcher(model_provider_base_url="https://openrouter.ai/api/v1")


class ClaudeModelSelectionTest(unittest.TestCase):
    def _command(self, **kwargs) -> list[str]:
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/echo", cli_version="2.1.259", **kwargs
        )
        return list(
            launcher._command(Path("/tmp/run"), prompt="hi", session_id=None)
        )

    def test_model_is_passed_when_selected(self) -> None:
        command = self._command(model="opus")
        self.assertEqual(command[command.index("--model") + 1], "opus")

    def test_cli_default_is_preserved_when_unset(self) -> None:
        self.assertNotIn("--model", self._command())

    def test_harness_flags_survive_a_model_choice(self) -> None:
        command = self._command(model="anthropic/claude-sonnet-4.5")
        for flag in ("--print", "--verbose", "--output-format", "--permission-mode"):
            self.assertIn(flag, command)


class GrokModelSelectionTest(unittest.TestCase):
    def test_model_is_no_longer_pinned_to_one_name(self) -> None:
        launcher = GrokNativeSessionLauncher(
            model="grok-5", binary="/bin/echo", cli_version="1.0.5"
        )
        self.assertEqual(launcher.model, "grok-5")

    def test_invalid_model_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            GrokNativeSessionLauncher(
                model="--dangerous", binary="/bin/echo", cli_version="1.0.5"
            )


class ClaudeGatewayEnvironmentTest(unittest.TestCase):
    """Claude Code reaches an Anthropic-protocol gateway through env, not argv."""

    def _launcher(self, **kwargs) -> ClaudeNativeSessionLauncher:
        return ClaudeNativeSessionLauncher(
            binary="/bin/echo", cli_version="2.1.259", **kwargs
        )

    def test_gateway_sets_base_url_token_and_blanks_the_vendor_key(self) -> None:
        launcher = self._launcher(
            model="~anthropic/claude-sonnet-latest",
            model_provider_base_url="https://openrouter.ai/api",
        )
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "sk-or-token", "ANTHROPIC_API_KEY": "vendor"},
                clear=False,
            ):
                environment = launcher._run_environment(Path(directory))
        self.assertEqual(environment["ANTHROPIC_BASE_URL"], "https://openrouter.ai/api")
        self.assertEqual(environment["ANTHROPIC_AUTH_TOKEN"], "sk-or-token")
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "")

    def test_gateway_without_a_key_fails_loudly(self) -> None:
        launcher = self._launcher(
            model_provider_base_url="https://openrouter.ai/api"
        )
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ClaudeInvocationError):
                    launcher._run_environment(Path(directory))

    def test_default_run_declares_no_gateway(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = self._launcher()._run_environment(Path(directory))
        self.assertNotIn("ANTHROPIC_BASE_URL", environment)

    def test_factory_values_never_reach_a_gateway_run(self) -> None:
        launcher = self._launcher(model_provider_base_url="https://openrouter.ai/api")
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "sk-or-token", "FACTORY_PASSWORD": "secret"},
                clear=False,
            ):
                environment = launcher._run_environment(Path(directory))
        self.assertNotIn("FACTORY_PASSWORD", environment)


class GatewayCredentialIsolationTest(unittest.TestCase):
    def test_gateway_key_is_forwarded_but_factory_values_are_not(self) -> None:
        environment = codex_subprocess_environment(
            {
                "PATH": "/usr/bin",
                "OPENROUTER_API_KEY": "gateway-token",
                "FACTORY_USERNAME": "service-account",
                "FACTORY_PASSWORD": "secret",
                "AWS_SECRET_ACCESS_KEY": "unrelated",
            }
        )
        self.assertEqual(environment["OPENROUTER_API_KEY"], "gateway-token")
        self.assertNotIn("FACTORY_USERNAME", environment)
        self.assertNotIn("FACTORY_PASSWORD", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)

    def test_gateway_key_is_an_explicit_allowlist_entry(self) -> None:
        self.assertIn("OPENROUTER_API_KEY", CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST)


if __name__ == "__main__":
    unittest.main()


class ProviderIsCodexOnlyTest(unittest.TestCase):
    """A gateway may only be selected for the Manager that can honour it."""

    def _checkpoint(self, manager_id: str):
        from workshop.workflow.agent_run import AgentRunCheckpoint

        return AgentRunCheckpoint(
            product_id="wish-one",
            stage="match",
            status="waiting",
            revision=1,
            round_index=0,
            max_rounds=4,
            wish_sha256="0" * 64,
            run_root_sha256="1" * 64,
            host_state_root_sha256="2" * 64,
            checkpoint_sha256="3" * 64,
            input_sha256s={},
            inventor_roster=(),
            stage_artifacts={},
            invalidated_stages=(),
            manager_id=manager_id,
        )

    def test_grok_rejects_a_gateway_instead_of_ignoring_it(self) -> None:
        from workshop.workflow.native_run import _native_launcher

        with self.assertRaises(ContractError) as raised:
            _native_launcher(
                self._checkpoint("grok"),
                model_selection=ManagerModelSelection(
                    model="grok-5",
                    provider="openrouter",
                    provider_base_url="https://openrouter.ai/api/v1",
                ),
            )
        self.assertIn("--model-provider", str(raised.exception))

    def test_claude_carries_the_gateway_into_its_launcher(self) -> None:
        from workshop.workflow.native_run import _native_launcher

        launcher = _native_launcher(
            self._checkpoint("claude"),
            model_selection=ManagerModelSelection(
                model="~anthropic/claude-sonnet-latest",
                provider="openrouter",
                provider_base_url="https://openrouter.ai/api",
            ),
        )
        self.assertEqual(launcher.model_provider_base_url, "https://openrouter.ai/api")
        self.assertEqual(launcher.model, "~anthropic/claude-sonnet-latest")
