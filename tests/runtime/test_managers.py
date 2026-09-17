import json
import sys
import unittest

from workshop.errors import ContractError
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.claude import ClaudeNativeSessionLauncher
from workshop.runtime.grok import GrokNativeSessionLauncher
from workshop.runtime.managers import (
    DEFAULT_MANAGER_ID,
    MANAGER_PROJECT_KIND,
    MAX_NATIVE_TOKEN_COUNT,
    NATIVE_TOKEN_USAGE_FIELDS,
    SUPPORTED_REASONING_EFFORTS,
    manager_launcher,
    manager_project_bytes,
    manager_runtime_selection,
    manager_spec,
    native_token_usage_fields,
    parse_manager_project_bytes,
    validate_native_token_usage,
)


_NO_USAGE = {name: None for name in NATIVE_TOKEN_USAGE_FIELDS}


class NativeTokenUsageContractTest(unittest.TestCase):
    """One per-turn usage contract shared by every Manager adapter."""

    def test_projection_reports_only_what_was_measured(self):
        self.assertEqual(
            NATIVE_TOKEN_USAGE_FIELDS,
            (
                "input_tokens",
                "cached_input_tokens",
                "cache_write_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            ),
        )
        self.assertEqual(native_token_usage_fields(**_NO_USAGE), {})
        self.assertEqual(
            native_token_usage_fields(
                **{**_NO_USAGE, "input_tokens": 42, "output_tokens": 7}
            ),
            {"input_tokens": 42, "output_tokens": 7},
        )
        self.assertEqual(
            native_token_usage_fields(
                input_tokens=80,
                cached_input_tokens=60,
                cache_write_input_tokens=5,
                output_tokens=20,
                reasoning_output_tokens=12,
            ),
            {
                "input_tokens": 80,
                "cached_input_tokens": 60,
                "cache_write_input_tokens": 5,
                "output_tokens": 20,
                "reasoning_output_tokens": 12,
            },
        )

    def test_validation_fails_closed_on_every_inconsistent_shape(self):
        full = {
            "input_tokens": 80,
            "cached_input_tokens": 60,
            "cache_write_input_tokens": 5,
            "output_tokens": 20,
            "reasoning_output_tokens": 12,
        }
        for label in ("Codex native session", "Claude native session"):
            validate_native_token_usage(**_NO_USAGE, label=label)
            validate_native_token_usage(
                **{**_NO_USAGE, "input_tokens": 0, "output_tokens": 0}, label=label
            )
            validate_native_token_usage(**full, label=label)
        cases = (
            ({"input_tokens": 1}, "token usage is incomplete"),
            ({"output_tokens": 1}, "token usage is incomplete"),
            ({**full, "reasoning_output_tokens": None}, "token detail is incomplete"),
            (
                {
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "reasoning_output_tokens": 0,
                },
                "token detail lacks usage",
            ),
            ({"input_tokens": -1, "output_tokens": 0}, "token usage is invalid"),
            ({"input_tokens": True, "output_tokens": 0}, "token usage is invalid"),
            ({"input_tokens": 1.5, "output_tokens": 0}, "token usage is invalid"),
            (
                {"input_tokens": MAX_NATIVE_TOKEN_COUNT + 1, "output_tokens": 0},
                "token usage is invalid",
            ),
            ({**full, "cached_input_tokens": 81}, "token detail is invalid"),
            ({**full, "cache_write_input_tokens": 81}, "token detail is invalid"),
            ({**full, "reasoning_output_tokens": 21}, "token detail is invalid"),
        )
        observed = 0
        for overrides, message in cases:
            observed += 1
            with self.subTest(overrides=overrides), self.assertRaisesRegex(
                ContractError, "^Grok native session " + message + "$"
            ):
                validate_native_token_usage(
                    **{**_NO_USAGE, **overrides}, label="Grok native session"
                )
        self.assertEqual(observed, len(cases))


class ManagerRegistryTest(unittest.TestCase):
    def test_default_manager_is_codex(self):
        spec = manager_spec(DEFAULT_MANAGER_ID)
        self.assertEqual(spec.manager_id, "codex")
        self.assertEqual(spec.session_checkpoint_name, "codex-session.json")
        self.assertFalse(spec.experimental)

    def test_unknown_manager_fails_closed(self):
        with self.assertRaises(ContractError):
            manager_spec("not-a-runtime")

    def test_codex_launcher_matches_the_frozen_spec(self):
        launcher = manager_launcher(
            "codex", cli_version="0.145.0", binary=sys.executable
        )
        self.assertIsInstance(launcher, CodexNativeSessionLauncher)
        self.assertEqual(launcher.manager_id, "codex")
        self.assertEqual(launcher.session_checkpoint_name, "codex-session.json")

    def test_grok_and_claude_launchers_are_experimental(self):
        grok = manager_spec("grok")
        claude = manager_spec("claude")
        self.assertTrue(grok.experimental)
        self.assertTrue(claude.experimental)
        self.assertEqual(grok.session_checkpoint_name, "grok-session.json")
        self.assertEqual(claude.session_checkpoint_name, "claude-session.json")
        self.assertIsInstance(
            manager_launcher("grok", cli_version="1.0.5", binary=sys.executable),
            GrokNativeSessionLauncher,
        )
        self.assertIsInstance(
            manager_launcher("claude", cli_version="2.0.0", binary=sys.executable),
            ClaudeNativeSessionLauncher,
        )

    def test_manager_project_bytes_are_canonical(self):
        payload = json.loads(manager_project_bytes(manager_spec("codex")))
        self.assertEqual(payload["kind"], MANAGER_PROJECT_KIND)
        self.assertEqual(payload["manager_id"], "codex")
        self.assertEqual(payload["agent_directory"], ".codex/agents")
        self.assertEqual(payload["model"], "gpt-6-astra")
        self.assertEqual(payload["reasoning_effort"], "medium")

    def test_runtime_selection_resolves_agent_defaults_and_model_aliases(self):
        codex = manager_runtime_selection("codex")
        self.assertEqual(codex.model, "gpt-6-astra")
        self.assertEqual(codex.reasoning_effort, "medium")
        astra = manager_runtime_selection(
            "codex", model="astra", reasoning_effort="high"
        )
        self.assertEqual(astra.model, "gpt-6-astra")
        claude = manager_runtime_selection("claude")
        self.assertEqual(claude.model, "claude-opus-5")
        self.assertEqual(claude.reasoning_effort, "medium")

    def test_astra_uses_medium_unless_explicitly_overridden(self):
        self.assertEqual(manager_runtime_selection("codex", model="astra").reasoning_effort, "medium")
        for agent in ("codex", "claude"):
            with self.subTest(agent=agent):
                frozen = manager_project_bytes(manager_runtime_selection(agent, reasoning_effort="high"))
                self.assertEqual(parse_manager_project_bytes(frozen)[2], "high")

    def test_runtime_selection_rejects_unsupported_agent_controls(self):
        with self.assertRaisesRegex(ContractError, "Codex model"):
            manager_runtime_selection("codex", model="unknown")
        with self.assertRaisesRegex(ContractError, "reasoning-effort"):
            manager_runtime_selection("grok", reasoning_effort="high")

    def test_every_declared_model_spelling_and_effort_resolves_canonically(self):
        codex_models = {
            "astra": "gpt-6-astra",
            "sol": "gpt-5.6-sol",
            "terra": "gpt-5.6-terra",
            "luna": "gpt-5.6-luna",
            "gpt-6-astra": "gpt-6-astra",
            "gpt-5.6-sol": "gpt-5.6-sol",
            "gpt-5.6-terra": "gpt-5.6-terra",
            "gpt-5.6-luna": "gpt-5.6-luna",
        }
        claude_models = {
            "opus": "claude-opus-5",
            "opus-5": "claude-opus-5",
            "claude-opus-5": "claude-opus-5",
        }
        observed = 0
        for agent, models in (
            ("codex", codex_models),
            ("claude", claude_models),
        ):
            for model_argument, canonical_model in models.items():
                for effort in SUPPORTED_REASONING_EFFORTS:
                    if effort == "ultra" and (agent != "codex" or canonical_model != "gpt-6-astra"):
                        with self.assertRaises(ContractError):
                            manager_runtime_selection(agent, model=model_argument, reasoning_effort=effort)
                        continue
                    observed += 1
                    with self.subTest(
                        agent=agent, model=model_argument, effort=effort
                    ):
                        selection = manager_runtime_selection(
                            agent,
                            model=model_argument,
                            reasoning_effort=effort,
                        )
                        self.assertEqual(selection.model, canonical_model)
                        self.assertEqual(selection.reasoning_effort, effort)
        self.assertEqual(observed, 46)

    def test_every_canonical_runtime_selection_round_trips_manager_project(self):
        canonical_models = {
            "codex": (
                "gpt-6-astra",
                "gpt-5.6-sol",
                "gpt-5.6-terra",
                "gpt-5.6-luna",
            ),
            "claude": ("claude-opus-5",),
        }
        observed = 0
        for agent, models in canonical_models.items():
            for model in models:
                for effort in SUPPORTED_REASONING_EFFORTS:
                    if effort == "ultra" and (agent != "codex" or model != "gpt-6-astra"):
                        continue
                    observed += 1
                    with self.subTest(agent=agent, model=model, effort=effort):
                        selection = manager_runtime_selection(
                            agent, model=model, reasoning_effort=effort
                        )
                        parsed_spec, parsed_model, parsed_effort = (
                            parse_manager_project_bytes(
                                manager_project_bytes(selection)
                            )
                        )
                        self.assertEqual(parsed_spec.manager_id, agent)
                        self.assertEqual(parsed_model, model)
                        self.assertEqual(parsed_effort, effort)

        grok = manager_runtime_selection("grok", model="grok-4.6")
        parsed_spec, parsed_model, parsed_effort = parse_manager_project_bytes(
            manager_project_bytes(grok)
        )
        self.assertEqual(parsed_spec.manager_id, "grok")
        self.assertEqual(parsed_model, "grok-4.6")
        self.assertIsNone(parsed_effort)
        self.assertEqual(observed + 1, 22)

    def test_every_effort_is_rejected_for_agent_without_effort_control(self):
        for effort in SUPPORTED_REASONING_EFFORTS:
            with self.subTest(effort=effort), self.assertRaisesRegex(
                ContractError, "reasoning-effort"
            ):
                manager_runtime_selection(
                    "grok", model="grok-4.6", reasoning_effort=effort
                )

    def test_manager_project_parser_preserves_schema_one_as_legacy(self):
        spec = manager_spec("codex")
        source = json.dumps(
            {
                "schema_version": 1,
                "kind": MANAGER_PROJECT_KIND,
                "manager_id": spec.manager_id,
                "display_name": spec.display_name,
                "agent_directory": spec.agent_directory,
                "agent_suffix": spec.agent_suffix,
                "experimental": spec.experimental,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        parsed, model, effort = parse_manager_project_bytes(source)
        self.assertEqual(parsed.manager_id, "codex")
        self.assertIsNone(model)
        self.assertIsNone(effort)


class ManagerCheckpointResumeTest(unittest.TestCase):
    def test_missing_manager_id_defaults_to_codex(self):
        from workshop.workflow.agent_run import AgentRunCheckpoint

        checkpoint = AgentRunCheckpoint(
            product_id="wish-one",
            stage="make",
            status="active",
            revision=1,
            round_index=1,
            max_rounds=4,
            wish_sha256="a" * 64,
            run_root_sha256="b" * 64,
            host_state_root_sha256="c" * 64,
            checkpoint_sha256="d" * 64,
            input_sha256s={},
            inventor_roster=(),
            stage_artifacts={},
            invalidated_stages=(),
        )
        self.assertEqual(checkpoint.manager_id, "codex")
