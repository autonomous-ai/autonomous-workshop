from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.release.session_history import (
    MAX_HISTORY_TURNS,
    Redactor,
    SessionHistoryError,
    build_conversation,
    find_rollout,
    run_session_history,
    strip_harness_envelopes,
    thread_id_for_run,
)


THREAD = "01a069b6-5af7-7600-81b2-b158b9d2e7bc"
WORKSPACE = "/srv/workshop/runs/wish-1/workspace"


def _item(ordinal, payload, timestamp="2026-09-03T23:59:%02d.000Z"):
    return {
        "timestamp": timestamp % min(ordinal, 59) if "%" in timestamp else timestamp,
        "ordinal": ordinal,
        "type": "response_item",
        "payload": payload,
    }


def sample_rollout(thread=THREAD, extra=()):
    records = [
        {"timestamp": "2026-09-03T23:59:13.000Z", "ordinal": 0, "type": "session_meta",
         "payload": {"id": thread, "cwd": WORKSPACE, "cli_version": "0.150.0"}},
        {"timestamp": "2026-09-03T23:59:14.000Z", "ordinal": 1, "type": "turn_context", "payload": {"model": "x"}},
        _item(2, {"type": "message", "id": "msg_banner", "role": "user",
                  "content": [{"type": "input_text", "text": "<recommended_plugins>\nAirtable\n</recommended_plugins>"}]}),
        _item(3, {"type": "message", "id": "msg_dev", "role": "developer",
                  "content": [{"type": "input_text", "text": "<multi_agent_mode>off</multi_agent_mode>"}]}),
        _item(4, {"type": "message", "id": "msg_goal", "role": "user",
                  "content": [{"type": "input_text", "text": "<environment_context>cwd</environment_context>Follow STAGE.json and make the toy."}]}),
        _item(5, {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "gAAAA"}),
        _item(6, {"type": "message", "id": "msg_a1", "role": "assistant",
                  "content": [{"type": "output_text", "text": "Reading the stage packet in %s/STAGE.json." % WORKSPACE}]}),
        _item(7, {"type": "custom_tool_call", "id": "ctc_1", "status": "completed", "call_id": "call_1", "name": "exec",
                  "input": 'const r = await tools.exec_command({ cmd: "cat STAGE.json\\n/opt/tools/bin/python x.py", workdir: "%s" });' % WORKSPACE}),
        _item(8, {"type": "custom_tool_call_output", "id": "ctco_1", "call_id": "call_1",
                  "output": [{"type": "input_text", "text": "Output:"},
                             {"type": "input_text", "text": json.dumps({"stage": "make"}) + " from /etc/hostname"}]}),
        _item(9, {"type": "function_call", "id": "fc_spawn", "call_id": "call_spawn", "name": "spawn_agent", "namespace": "collaboration",
                  "arguments": json.dumps({"message": "gAAAAencrypted"})}),
        _item(10, {"type": "function_call_output", "id": "fco_spawn", "call_id": "call_spawn",
                   "output": json.dumps({"task_name": "/root/pico"})}),
        _item(11, {"type": "function_call", "id": "fc_2", "call_id": "call_2", "name": "read_file",
                   "arguments": json.dumps({"path": WORKSPACE + "/product.json"})}),
        _item(12, {"type": "function_call_output", "id": "fco_2", "call_id": "call_2",
                   "output": "token " + "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" + " leaked"}),
        _item(13, {"type": "agent_message", "id": "amsg_1", "author": "/root/pico", "recipient": "/root",
                   "content": [{"type": "encrypted_content", "encrypted_content": "gAAA"}]}),
        _item(14, {"type": "message", "id": "msg_a2", "role": "assistant",
                   "content": [{"type": "output_text", "text": "Done. Key " + "sk-ant-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123" + " was never here."}]}),
        {"timestamp": "2026-09-04T00:00:00.000Z", "ordinal": 15, "type": "event_msg", "payload": {"type": "token_count"}},
        *extra,
    ]
    return "\n".join(json.dumps(record) for record in records) + "\n"


class SessionHistoryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.sessions = self.root / "sessions" / "2026" / "09" / "03"
        self.sessions.mkdir(parents=True)
        self.rollout = self.sessions / ("rollout-2026-09-03T23-59-13-%s.jsonl" % THREAD)
        self.rollout.write_text(sample_rollout(), encoding="utf-8")

    def _lines(self, content):
        return [json.loads(line) for line in content.splitlines()]

    def test_rollout_projects_into_claude_code_shaped_turns(self):
        content = build_conversation(
            self.rollout, opener_text="A press-to-turn owl.", opener_uuid="wish-abc",
            workspace_root=Path(WORKSPACE),
        )

        lines = self._lines(content)
        kinds = [
            (entry["type"], entry["message"]["content"] if isinstance(entry["message"]["content"], str) else entry["message"]["content"][0]["type"])
            for entry in lines
        ]
        self.assertEqual(kinds[0], ("user", "A press-to-turn owl."))
        self.assertEqual(lines[0]["uuid"], "wish-abc")
        self.assertEqual(lines[0]["timestamp"], "2026-09-03T23:59:02.000Z")
        self.assertEqual(kinds[1], ("user", "Follow STAGE.json and make the toy."))
        self.assertEqual(lines[1]["uuid"], "msg_goal")
        self.assertEqual(kinds[2][0], "assistant")
        self.assertEqual(
            lines[2]["message"]["content"],
            [{"type": "text", "text": "Reading the stage packet in <workspace>/STAGE.json."}],
        )
        tool_use = lines[3]["message"]["content"][0]
        self.assertEqual(tool_use["type"], "tool_use")
        self.assertEqual((tool_use["id"], tool_use["name"]), ("call_1", "exec"))
        self.assertIn("<workspace>", tool_use["input"]["raw"])
        self.assertIn("<host> x.py", tool_use["input"]["raw"])
        self.assertNotIn("/opt/tools", tool_use["input"]["raw"])
        result = lines[4]["message"]["content"][0]
        self.assertEqual((lines[4]["type"], result["type"], result["tool_use_id"]), ("user", "tool_result", "call_1"))
        self.assertIn("from <host>", result["content"])
        self.assertEqual(lines[4]["uuid"], "ctco_1")
        read_call = lines[5]["message"]["content"][0]
        self.assertEqual(read_call["name"], "read_file")
        self.assertEqual(read_call["input"], {"path": "<workspace>/product.json"})
        self.assertEqual(
            lines[6]["message"]["content"][0]["content"],
            "[output withheld: matched the secret scanner]",
        )
        self.assertEqual(len(lines), 7)
        text = content.decode("utf-8")
        for forbidden in ("recommended_plugins", "multi_agent_mode", "spawn_agent", "encrypted", "ghp_", "sk-ant-", "/root/", "/etc/"):
            self.assertNotIn(forbidden, text)
        for line in content.splitlines():
            entry = json.loads(line)
            self.assertEqual(set(entry), {"type", "uuid", "timestamp", "message"})

    def test_turn_cap_matches_the_factory_limit(self):
        extra = [
            _item(100 + index, {"type": "message", "id": "msg_%d" % index, "role": "user",
                                "content": [{"type": "input_text", "text": "Goal %d" % index}]},
                  timestamp="2026-09-04T00:01:00.000Z")
            for index in range(MAX_HISTORY_TURNS + 20)
        ]
        self.rollout.write_text(sample_rollout(extra=extra), encoding="utf-8")

        content = build_conversation(self.rollout, opener_text="o", opener_uuid="u")

        turns = [
            entry for entry in self._lines(content)
            if entry["type"] == "user" and isinstance(entry["message"]["content"], str)
        ]
        self.assertEqual(len(turns), MAX_HISTORY_TURNS)

    def test_find_rollout_verifies_session_metadata(self):
        decoy = self.sessions / ("rollout-2026-09-03T00-00-00-%s.jsonl" % THREAD)
        decoy.write_text(sample_rollout(thread="00000000-0000-0000-0000-000000000000"), encoding="utf-8")
        self.rollout.rename(self.sessions / ("rollout-2026-09-03T23-59-14-%s.jsonl" % THREAD))

        found = find_rollout(THREAD, self.root / "sessions")

        self.assertEqual(found.name, "rollout-2026-09-03T23-59-14-%s.jsonl" % THREAD)
        self.assertIsNone(find_rollout("11111111-1111-1111-1111-111111111111", self.root / "sessions"))
        with self.assertRaises(ContractError):
            find_rollout("../etc", self.root / "sessions")

    def test_run_history_reads_the_thread_from_host_state(self):
        host_state = self.root / "state"
        host_state.mkdir(mode=0o700)
        (host_state / "codex-session.json").write_text(json.dumps({"thread_id": THREAD}), encoding="utf-8")
        self.assertEqual(thread_id_for_run(host_state), THREAD)

        content = run_session_history(
            host_state, workspace_root=Path(WORKSPACE), opener_text="Wish", opener_uuid="w",
            sessions_root=self.root / "sessions",
        )

        self.assertIsNotNone(content)
        self.assertEqual(self._lines(content)[0]["message"]["content"], "Wish")
        (host_state / "codex-session.json").write_text("{}", encoding="utf-8")
        self.assertIsNone(thread_id_for_run(host_state))
        self.assertIsNone(
            run_session_history(host_state, workspace_root=Path(WORKSPACE), opener_text="Wish", opener_uuid="w", sessions_root=self.root / "sessions")
        )

    def test_empty_rollout_and_helpers(self):
        self.rollout.write_text("", encoding="utf-8")
        with self.assertRaises(SessionHistoryError):
            build_conversation(self.rollout, opener_text="o", opener_uuid="u")
        with self.assertRaises(ContractError):
            build_conversation(self.rollout, opener_text=" ", opener_uuid="u")
        self.assertEqual(strip_harness_envelopes("<a>x</a><b>y</b>real"), "real")
        self.assertEqual(strip_harness_envelopes("plain <a>x</a>"), "plain <a>x</a>")
        redactor = Redactor("/ws/run")
        self.assertEqual(redactor.path_text("see /ws/run/a.py and /var/log/x"), "see <workspace>/a.py and <host>")
        self.assertIsNone(redactor.clean("-----BEGIN " + "RSA PRIVATE KEY-----"))


if __name__ == "__main__":
    unittest.main()
