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
    manager_launcher,
    manager_project_bytes,
    manager_spec,
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

    def test_manager_project_bytes_are_canonical(self):
        payload = json.loads(manager_project_bytes(manager_spec("codex")))
        self.assertEqual(payload["kind"], MANAGER_PROJECT_KIND)
        self.assertEqual(payload["manager_id"], "codex")
        self.assertEqual(payload["agent_directory"], ".codex/agents")


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
