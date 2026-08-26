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
                "needs": ["fixture stops before the host gate"],
                "proposed_transition": None,
            },
        },
        sort_keys=True,
    ),
    encoding="utf-8",
)
(run_root / "native-probe.json").write_text(
    json.dumps(
        {
            "arguments": sys.argv[1:],
            "factory_visible": "FACTORY_PASSWORD" in os.environ,
            "objective": wish["objective"],
            "prompt": prompt,
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
print(json.dumps({"type": "turn.completed", "usage": {}}))
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
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), redirect_stdout(
                output
            ), redirect_stderr(progress):
                exit_code = main(("wish", objective, "--json"))

            self.assertEqual(exit_code, 0, progress.getvalue())
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["wish"]["objective"], objective)
            self.assertEqual(receipt["wish"]["context"], {"source": "workshop-cli"})
            self.assertEqual(receipt["kind"], "native-agent-run")
            self.assertEqual(receipt["manager"], "codex")
            self.assertEqual(receipt["stage"], "match")
            self.assertEqual(receipt["publication"]["status"], "not-created")

            workspace = home / "toys" / receipt["product_id"]
            self.assertTrue((home / "state" / receipt["product_id"]).is_dir())
            observed = json.loads(
                (workspace / "native-probe.json").read_text(encoding="utf-8")
            )
            self.assertEqual(observed["objective"], objective)
            self.assertTrue(observed["product_agents"])
            self.assertTrue(observed["product_skill"])
            self.assertFalse(observed["factory_visible"])
            self.assertIn("--search", observed["arguments"])
            for feature in ("goals", "multi_agent"):
                feature_index = observed["arguments"].index(feature)
                self.assertEqual(
                    observed["arguments"][feature_index - 1], "--enable"
                )
            self.assertIn("--strict-config", observed["arguments"])
            self.assertNotIn("--sandbox", observed["arguments"])
            self.assertIn(
                'default_permissions="workshop-product-run"',
                observed["arguments"],
            )
            self.assertTrue(
                any(
                    argument.startswith(
                        "permissions.workshop-product-run.filesystem="
                    )
                    and '":root"="deny"' in argument
                    and json.dumps(str(workspace)) + '="write"' in argument
                    and json.dumps(str(workspace / "**/.env*")) + '="deny"'
                    in argument
                    for argument in observed["arguments"]
                )
            )
            self.assertIn(
                'project_root_markers=[".workshop-product-run-root"]',
                observed["arguments"],
            )
            self.assertIn("current match stage", observed["prompt"])
            self.assertNotIn(objective, observed["prompt"])
            self.assertFalse((workspace / "agent-outcome.json").exists())


if __name__ == "__main__":
    unittest.main()
