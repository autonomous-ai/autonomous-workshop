import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import psutil

from cli.main import main
from workshop.workflow.effort import SPARK_V4_AUTO_COMPACT_TOKEN_LIMIT
from tests.invent.fake_gamevault import install_fake_gamevault


class WorkshopWishNativeSubprocessTest(unittest.TestCase):
    def test_wish_launches_native_codex_in_materialized_product_run(self):
        install_fake_gamevault(self)
        def fixture_session_members(session_identity):
            session_id = session_identity.session_id
            try:
                member = psutil.Process(session_id)
                if os.getsid(member.pid) != session_id:
                    return ()
                if member.create_time() != session_identity.leader_create_time:
                    return None
            except (OSError, psutil.Error):
                return ()
            return (member,)

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
    print("codex-cli 0.153.4")
    raise SystemExit(0)

run_root = Path.cwd()
# A token-budget run reads its own usage back out of the native rollout, so
# the fixture leaves one behind under CODEX_HOME the way codex exec does.
import datetime
import uuid

codex_home = Path(os.environ["CODEX_HOME"])
codex_home.mkdir(parents=True, exist_ok=True)
identity = codex_home / "fixture-thread.json"
if identity.is_file():
    # A resumed turn must report the session it was bound to, not a new one.
    bound = json.loads(identity.read_text(encoding="utf-8"))
    thread_id, day = bound["thread_id"], bound["day"]
else:
    now = datetime.datetime.now(datetime.timezone.utc)
    thread_id = str(uuid.UUID(int=(
        (int(now.timestamp() * 1000) << 80) | (7 << 76) | (0x2 << 62) | 0x123456789ABCDEF
    )))
    day = now.strftime("%Y/%m/%d")
    identity.write_text(
        json.dumps({"thread_id": thread_id, "day": day}), encoding="utf-8"
    )
sessions = codex_home / "sessions" / day
sessions.mkdir(parents=True, exist_ok=True)
rollout_path = sessions / ("rollout-" + thread_id + ".jsonl")
# codex exec resets its counters per process, so every turn appends its own
# task whose first request is its own baseline (total == last).
turn = len([line for line in rollout_path.read_text(encoding="utf-8").splitlines()
            if "task_started" in line]) + 1 if rollout_path.is_file() else 1
counters = {
    "input_tokens": 1200 * turn,
    "cached_input_tokens": 0,
    "cache_write_input_tokens": 0,
    "output_tokens": 340 * turn,
    "reasoning_output_tokens": 0,
}
records = []
if not rollout_path.is_file():
    records.append({"type": "session_meta", "payload": {
        "id": thread_id, "cwd": str(run_root), "cli_version": "0.153.4"}})
records.extend((
    {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
    {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-%d" % turn}},
    {"type": "event_msg", "payload": {"type": "token_count", "info": {
        "total_token_usage": counters, "last_token_usage": counters}}},
))
with rollout_path.open("a", encoding="utf-8") as stream:
    for record in records:
        stream.write(json.dumps(record, sort_keys=True) + chr(10))
wish = json.loads((run_root / "WISH.json").read_text(encoding="utf-8"))
stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
prompt = sys.stdin.read()
selection = stage["inputs"]["workshop_selection"]
if selection["status"] == "pending":
    # Spark's setup boundary wants the selection marker, not a proposal. A
    # premature agent-outcome.json here is exactly what the host discards.
    roster = stage["inputs"]["inventor_roster"]["inventors"]
    (run_root / selection["marker_path"]).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "autonomous-workshop.inventor-selection-ready",
                "product_id": selection["product_id"],
                "checkpoint_sha256": selection["checkpoint_sha256"],
                "wish_sha256": selection["wish_sha256"],
                "inventor_roster_sha256": selection["inventor_roster_sha256"],
                "selected_inventor_id": roster[0]["inventor_id"],
                "ranking": [
                    {"inventor_id": item["inventor_id"], "rationale": "fixture ranking"}
                    for item in roster
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"type": "thread.started", "thread_id": thread_id}))
    print(json.dumps({"type": "turn.completed", "usage": {}}))
    raise SystemExit(0)
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
print(json.dumps({"type": "thread.started", "thread_id": thread_id}))
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
                "CODEX_HOME": str(root / "codex-home"),
                "FACTORY_PASSWORD": "must-not-reach-native-codex",
                "PATH": os.environ.get("PATH", os.defpath),
                "HOME": os.environ.get("HOME", str(root)),
            }
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.runtime.codex._process_session_members",
                side_effect=fixture_session_members,
            ), redirect_stdout(
                output
            ), redirect_stderr(progress):
                exit_code = main(("wish", objective, "--json"))

            self.assertEqual(exit_code, 0, progress.getvalue())
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["wish"]["objective"], objective)
            self.assertEqual(receipt["wish"]["context"], {"source": "workshop-cli"})
            self.assertEqual(receipt["kind"], "native-agent-run")
            self.assertEqual(receipt["stage"], "make")
            self.assertEqual(receipt["workflow"], "spark")
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertIn(
                "Native Codex: reported progress for the current stage.",
                progress.getvalue(),
            )
            self.assertNotIn("finalizing the current stage", progress.getvalue())
            self.assertIn(
                "Native Codex: turn complete; Workshop is verifying it.",
                progress.getvalue(),
            )
            self.assertNotIn("fixture complete", progress.getvalue())

            workspace = home / "runs" / receipt["product_id"] / "workspace"
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
            self.assertIn(
                "model_auto_compact_token_limit=%d" % SPARK_V4_AUTO_COMPACT_TOKEN_LIMIT,
                observed["arguments"],
            )
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
            self.assertIn("current make stage", observed["prompt"])
            self.assertNotIn(objective, observed["prompt"])
            self.assertFalse((workspace / "agent-outcome.json").exists())


if __name__ == "__main__":
    unittest.main()
