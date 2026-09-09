import json
import runpy
import os
import tempfile
import unittest
from pathlib import Path

from workshop.workflow.agent_run import AgentRun
from workshop.workflow.native_run import (
    PORTABLE_MANAGER_CAPABILITY_PATH, native_stage_prompt,
)
from workshop.runtime.managers import manager_spec
from workshop.errors import ContractError


ROOT = Path(__file__).resolve().parents[2]


class PortableStageObjectiveTest(unittest.TestCase):
    def test_each_manager_materializes_the_self_contained_runtime_reference(self):
        for manager in ("codex", "claude", "grok"):
            with self.subTest(manager=manager), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                run = AgentRun.create(
                    root / "run", root / "state", product_id="wish-portable",
                    wish_bytes=json.dumps({"schema_version": 1, "product_id": "wish-portable",
                        "objective": "a sword", "constraints": {}, "context": {}}, sort_keys=True, separators=(",", ":")).encode(),
                    product_run_constitution_source=ROOT / ".agents/product-run/AGENTS.md",
                    skill_root=ROOT / ".agents/product-run/.agents/skills/autonomous-workshop",
                    effort="spark", manager_id=manager,
                )
                self.assertIn(PORTABLE_MANAGER_CAPABILITY_PATH, run.snapshot().input_sha256s)
                self.assertEqual((root / "run" / PORTABLE_MANAGER_CAPABILITY_PATH).read_bytes(),
                    (ROOT / ".agents/product-run" / PORTABLE_MANAGER_CAPABILITY_PATH).read_bytes())
                metadata = json.loads((root / "run/MANAGER.json").read_text())
                self.assertEqual(metadata["agent_directory"], manager_spec(manager).agent_directory)

    def test_portable_prompt_is_opt_in_and_invalid_stage_still_fails(self):
        legacy = native_stage_prompt("make")
        portable = native_stage_prompt("make", portable_manager=True)
        self.assertNotEqual(legacy, portable)
        self.assertIn("native Goal", legacy)
        self.assertIn("manager-runtime-v1.md", portable)
        claude = native_stage_prompt("make", portable_manager=True, manager_id="claude")
        self.assertIn("other Managers use their native session", claude)
        self.assertNotIn("Create one native Goal", claude)
        self.assertEqual(native_stage_prompt("make", manager_id="claude"), legacy)
        with self.assertRaises(ContractError):
            native_stage_prompt("publish", portable_manager=True)


class ClaudeRealRosterTest(unittest.TestCase):
    def test_real_roster_materializes_validates_and_rejects_mutation(self):
        from workshop.errors import StateConflict
        from workshop.runtime.agent_assets import parse_inventor_custom_agent_bytes
        from workshop.match.native import InventorRoster, InventorRosterEntry
        proposal = runpy.run_path(str(ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            run = AgentRun.create(
                root / "run", root / "state", product_id="wish-claude-roster",
                wish_bytes=json.dumps({"schema_version": 1, "product_id": "wish-claude-roster",
                    "objective": "a sword", "constraints": {}, "context": {}}, sort_keys=True, separators=(",", ":")).encode(),
                product_run_constitution_source=ROOT / ".agents/product-run/AGENTS.md",
                skill_root=ROOT / ".agents/product-run/.agents/skills/autonomous-workshop",
                inventor_source_root=ROOT / "inventors", effort="spark", manager_id="claude",
            )
            checkpoint = run.snapshot()
            self.assertGreater(len(checkpoint.inventor_roster), 0)
            self.assertFalse((run.run_root / ".codex/agents").exists())
            entries = []
            for item in checkpoint.inventor_roster:
                path = run.run_root / item["agent_path"]
                self.assertTrue(item["agent_path"].startswith(".claude/agents/"))
                binding = parse_inventor_custom_agent_bytes(path.read_bytes())
                self.assertEqual(binding.to_host_dict(), dict(item))
                entries.append(InventorRosterEntry(**{key: item[key] for key in
                    ("inventor_id", "agent_path", "agent_sha256", "source_manifest_sha256", "taste_sha256")}))
            roster = InventorRoster(tuple(entries))
            proposal["_validate_roster"](roster.to_dict())
            path = run.run_root / checkpoint.inventor_roster[0]["agent_path"]
            original = path.read_bytes()
            os.chmod(path, 0o600)
            path.write_bytes(original + b"tamper")
            with self.assertRaises(StateConflict):
                run.snapshot()
            path.write_bytes(original)
            os.chmod(path, 0o400)
            run.snapshot()
