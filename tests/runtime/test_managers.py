import json
import sys
import unittest

from pathlib import PurePosixPath

from workshop.errors import ContractError
from workshop.match.native import InventorRosterEntry
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.claude import ClaudeNativeSessionLauncher
from workshop.runtime.grok import GrokNativeSessionLauncher
from workshop.runtime.managers import (
    DEFAULT_MANAGER_ID,
    MANAGER_PROJECT_KIND,
    SUPPORTED_REASONING_EFFORTS,
    manager_launcher,
    manager_project_bytes,
    manager_runtime_selection,
    manager_spec,
    parse_manager_project_bytes,
)


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

    def test_every_manager_reads_the_roster_from_the_codex_agent_directory(self):
        # The host materializes one roster at .codex/agents/<id>.toml for every
        # Manager (workflow.agent_run), so every spec projects that same path.
        materialized = (PurePosixPath(".codex/agents") / ("alice" + ".toml")).as_posix()
        roster_entry = InventorRosterEntry(
            inventor_id="alice",
            agent_path=".codex/agents/alice.toml",
            agent_sha256="a" * 64,
            source_manifest_sha256="b" * 64,
            taste_sha256="c" * 64,
        )
        for manager_id in ("codex", "claude", "grok"):
            with self.subTest(manager=manager_id):
                spec = manager_spec(manager_id)
                self.assertEqual(spec.agent_directory, ".codex/agents")
                self.assertEqual(spec.agent_suffix, ".toml")
                self.assertEqual(spec.agent_path("alice"), materialized)
                self.assertEqual(spec.agent_path("alice"), roster_entry.agent_path)
                payload = json.loads(manager_project_bytes(spec))
                self.assertEqual(payload["agent_directory"], ".codex/agents")
                self.assertEqual(payload["agent_suffix"], ".toml")

    def test_manager_project_bytes_are_canonical(self):
        payload = json.loads(manager_project_bytes(manager_spec("codex")))
        self.assertEqual(payload["kind"], MANAGER_PROJECT_KIND)
        self.assertEqual(payload["manager_id"], "codex")
        self.assertEqual(payload["agent_directory"], ".codex/agents")
        self.assertEqual(payload["model"], "gpt-5.6-sol")
        self.assertEqual(payload["reasoning_effort"], "medium")

    def test_runtime_selection_resolves_agent_defaults_and_model_aliases(self):
        codex = manager_runtime_selection("codex")
        self.assertEqual(codex.model, "gpt-5.6-sol")
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
        self.assertEqual(observed, 44)

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
        self.assertEqual(observed + 1, 21)

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
