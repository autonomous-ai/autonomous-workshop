import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from cli.main import main


class WorkshopWishNativeSubprocessTest(unittest.TestCase):
    def test_wish_launches_native_codex_in_materialized_product_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            fake_codex = root / "fake-codex"
            repository = Path(__file__).resolve().parents[2]
            catalog = root / "inventors"
            catalog.mkdir()
            for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
                destination = catalog / inventor_id
                destination.mkdir()
                for filename in ("inventor.json", "TASTE.md"):
                    (destination / filename).write_bytes(
                        (repository / "inventors" / inventor_id / filename).read_bytes()
                    )
            fake_codex.write_text(
                """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.145.0")
    raise SystemExit(0)

run_root = Path.cwd()
wish = json.loads((run_root / "WISH.json").read_text(encoding="utf-8"))
stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
prompt = sys.stdin.read()
(run_root / "agent-outcome.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": stage["checkpoint_sha256"],
            "subject_sha256": stage["subject_sha256"],
            "outcome": {
                "schema_version": 1,
                "stage": stage["stage"],
                "status": "waiting",
                "artifacts": [],
                "needs": ["fixture stops after one native turn"],
                "proposed_transition": None,
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ) + "\\n",
    encoding="utf-8",
)
(run_root / "native-probe.json").write_text(
    json.dumps(
        {
            "arguments": sys.argv[1:],
            "factory_visible": "FACTORY_PASSWORD" in os.environ,
            "objective": wish["objective"],
            "prompt": prompt,
            "stage": stage,
            "product_agents": (run_root / "AGENTS.md").is_file(),
            "product_skill": (
                run_root
                / ".agents"
                / "skills"
                / "autonomous-workshop"
                / "SKILL.md"
            ).is_file(),
        },
        sort_keys=True,
    ),
    encoding="utf-8",
)
print(json.dumps({"type": "thread.started", "thread_id": "12345678-1234-5678-9234-567812345678"}))
print(json.dumps({"type": "item.completed", "item": {"id": "message-1", "type": "agent_message", "text": "fixture complete"}}))
""",
                encoding="utf-8",
            )
            fake_codex.chmod(0o700)

            output = StringIO()
            progress = StringIO()
            objective = "a moonlit chess set shaped by Linh's mountain memories"
            environment = {
                "WORKSHOP_HOME": str(home),
                "WORKSHOP_CODEX_BIN": str(fake_codex),
                "FACTORY_PASSWORD": "must-not-reach-native-codex",
                "PATH": os.environ.get("PATH", os.defpath),
                "HOME": os.environ.get("HOME", str(root)),
            }
            with mock.patch.dict(os.environ, environment, clear=True), redirect_stdout(
                output
            ), redirect_stderr(progress), mock.patch(
                "cli.native_run._product_run_catalog_root", return_value=catalog
            ):
                exit_code = main(("wish", objective, "--json"))

            self.assertEqual(exit_code, 0, progress.getvalue())
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["wish"]["objective"], objective)
            self.assertEqual(receipt["wish"]["context"], {"source": "workshop-cli"})
            self.assertEqual(receipt["kind"], "native-agent-run")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "match")
            self.assertEqual(receipt["native_turns"], 1)
            self.assertEqual(receipt["publication"]["status"], "not-created")

            workspace = home / "runs" / receipt["product_id"] / "workspace"
            observed = json.loads(
                (workspace / "native-probe.json").read_text(encoding="utf-8")
            )
            self.assertEqual(observed["objective"], objective)
            self.assertTrue(observed["product_agents"])
            self.assertTrue(observed["product_skill"])
            self.assertFalse(observed["factory_visible"])
            self.assertIn("--search", observed["arguments"])
            self.assertIn("workspace-write", observed["arguments"])
            self.assertIn("current match stage", observed["prompt"])
            self.assertNotIn(objective, observed["prompt"])
            self.assertEqual(observed["stage"]["stage"], "match")
            self.assertRegex(
                observed["stage"]["checkpoint_sha256"], r"^[0-9a-f]{64}$"
            )
            self.assertRegex(
                observed["stage"]["subject_sha256"], r"^[0-9a-f]{64}$"
            )
            self.assertFalse((workspace / "agent-outcome.json").exists())


if __name__ == "__main__":
    unittest.main()
