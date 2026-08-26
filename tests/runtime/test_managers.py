import json
import unittest

from workshop.errors import ContractError
from workshop.runtime.managers import (
    CLAUDE_PLUGIN_MANIFEST_PATH,
    DEFAULT_MANAGER_ID,
    ManagerRuntimeSpec,
    SUPPORTED_MANAGER_IDS,
    manager_spec,
    manager_support_files,
    parse_manager_project_bytes,
)


class ManagerRegistryTest(unittest.TestCase):
    def test_registry_has_stable_default_and_runtime_native_layouts(self):
        self.assertEqual(DEFAULT_MANAGER_ID, "codex")
        self.assertEqual(SUPPORTED_MANAGER_IDS, ("codex", "claude"))

        codex = manager_spec()
        self.assertEqual(codex.agent_path("alice"), ".codex/agents/alice.toml")
        self.assertEqual(
            codex.skill_path("alice-inventor"),
            ".agents/skills/alice-inventor/SKILL.md",
        )
        self.assertEqual(codex.session_checkpoint_name, "codex-session.json")

        claude = manager_spec("claude")
        self.assertEqual(claude.agent_path("alice"), ".claude/agents/alice.md")
        self.assertEqual(
            claude.skill_path("alice-inventor"),
            ".claude/skills/alice-inventor/SKILL.md",
        )
        self.assertEqual(claude.instruction_entrypoint, "CLAUDE.md")
        self.assertEqual(claude.agent_namespace, "autonomous-workshop")
        self.assertEqual(claude.session_checkpoint_name, "claude-session.json")

    def test_manager_project_binding_is_canonical_and_closed(self):
        for manager_id in SUPPORTED_MANAGER_IDS:
            spec = manager_spec(manager_id)
            self.assertEqual(parse_manager_project_bytes(spec.project_bytes()), spec)
            value = json.loads(spec.project_bytes())
            value["manager"] = "unregistered"
            tampered = json.dumps(
                value, sort_keys=True, separators=(",", ":")
            ).encode("utf-8") + b"\n"
            with self.assertRaisesRegex(ContractError, "unsupported"):
                parse_manager_project_bytes(tampered)

        with self.assertRaisesRegex(ContractError, "unsupported"):
            manager_spec("grok")

    def test_claude_support_tree_is_one_strict_namespaced_plugin(self):
        self.assertEqual(manager_support_files("codex"), ())
        support = dict(manager_support_files("claude"))
        self.assertEqual(set(support), {CLAUDE_PLUGIN_MANIFEST_PATH})
        manifest = json.loads(support[CLAUDE_PLUGIN_MANIFEST_PATH])
        self.assertEqual(
            manifest,
            {
                "author": {"name": "Autonomous Workshop"},
                "description": "Host-projected Workshop runtime",
                "name": "autonomous-workshop",
                "version": "1.0.0",
            },
        )

    def test_public_path_contracts_reject_non_text_without_leaking_type_errors(self):
        with self.assertRaises(ContractError):
            manager_spec().skill_path("alice-inventor", object())
        with self.assertRaises(ContractError):
            ManagerRuntimeSpec(
                manager_id="broken",
                display_name="Broken",
                agent_directory=object(),
                agent_suffix=".md",
                skill_directory=".broken/skills",
                instruction_entrypoint="BROKEN.md",
                session_checkpoint_name="broken-session.json",
            )


if __name__ == "__main__":
    unittest.main()
