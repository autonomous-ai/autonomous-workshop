import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.make import make_round_guard
from workshop.make.make_round_guard import (
    NONCE_TABLE_NAME,
    decide,
    make_round_calls,
)

SCRIPT = '"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round'
COMPONENT = SCRIPT + " cad --component part_wing.step.py --nozzle 0.4"


def _event(command, agent_type=None, *, key="command", tool="Bash"):
    event = {
        "session_id": "s-1",
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {key: command, "timeout": 600000},
        "tool_use_id": "t-1",
    }
    if agent_type is not None:
        event["agent_type"] = agent_type
        event["agent_id"] = "a-1"
    return event


class _Issuer:
    def __init__(self):
        self.issued = []

    def __call__(self, event, component):
        nonce = "%032x" % (len(self.issued) + 1)
        self.issued.append((nonce, component, event.get("agent_type")))
        return nonce


def _decision(output):
    return output["hookSpecificOutput"]["permissionDecision"]


class MakeRoundCallsTest(unittest.TestCase):
    def test_finds_the_interpreter_and_direct_forms(self):
        self.assertEqual(
            make_round_calls(COMPONENT),
            [["cad", "--component", "part_wing.step.py", "--nozzle", "0.4"]],
        )
        self.assertEqual(
            make_round_calls("cd /w && ./.agents/skills/make-round/scripts/make_round cad"),
            [["cad"]],
        )
        self.assertEqual(
            make_round_calls("timeout 900 python3 -u scripts/make_round cad --json"),
            [["cad", "--json"]],
        )
        self.assertEqual(
            make_round_calls("bash -lc '%s'" % COMPONENT.replace('"', "")),
            [["cad", "--component", "part_wing.step.py", "--nozzle", "0.4"]],
        )

    def test_reading_the_script_is_not_a_call(self):
        self.assertEqual(make_round_calls("sed -n 1,40p scripts/make_round"), [])
        self.assertEqual(make_round_calls("grep -n SHAPE scripts/make_round"), [])

    def test_unparseable_command_is_reported(self):
        self.assertIsNone(make_round_calls("python3 scripts/make_round 'cad"))


class DecideTest(unittest.TestCase):
    def test_unrelated_commands_and_tools_pass_unchanged(self):
        issuer = _Issuer()
        self.assertIsNone(decide(_event("ls -la"), issue=issuer))
        self.assertIsNone(
            decide({"tool_name": "spawn_agent", "tool_input": {"message": "x"}}, issue=issuer)
        )
        self.assertIsNone(decide(_event("sed -n 1p scripts/make_round"), issue=issuer))
        self.assertEqual(issuer.issued, [])

    def test_worker_component_round_gets_one_fresh_nonce(self):
        issuer = _Issuer()
        output = decide(_event(COMPONENT, "component-worker"), issue=issuer)
        self.assertEqual(_decision(output), "allow")
        updated = output["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["timeout"], 600000)
        nonce = issuer.issued[0][0]
        self.assertEqual(issuer.issued, [(nonce, "part_wing.step.py", "component-worker")])
        self.assertEqual(
            updated["command"],
            SCRIPT + " --worker-nonce %s cad --component part_wing.step.py --nozzle 0.4" % nonce,
        )

    def test_codex_cmd_key_is_rewritten_in_place(self):
        issuer = _Issuer()
        output = decide(_event(COMPONENT, "component-worker", key="cmd"), issue=issuer)
        self.assertIn("--worker-nonce", output["hookSpecificOutput"]["updatedInput"]["cmd"])

    def test_root_and_other_agents_cannot_run_a_component_round(self):
        for agent_type in (None, "rowan-vale", "component-reviewer", "general-purpose"):
            issuer = _Issuer()
            output = decide(_event(COMPONENT, agent_type), issue=issuer)
            self.assertEqual(_decision(output), "deny", agent_type)
            self.assertIn("component-worker", output["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertEqual(issuer.issued, [])

    def test_review_record_and_assembly_rounds_are_root_only(self):
        review = COMPONENT + " --record-review review.json"
        assembly = SCRIPT + " cad --require-component-passes"
        visual = SCRIPT + " cad --record-visual feedback.json --full"
        for command in (review, assembly, visual):
            self.assertIsNone(decide(_event(command), issue=_Issuer()), command)
            for agent_type in ("component-worker", "rowan-vale"):
                output = decide(_event(command, agent_type), issue=_Issuer())
                self.assertEqual(_decision(output), "deny", (command, agent_type))

    def test_a_caller_supplied_nonce_is_refused(self):
        for agent_type in (None, "component-worker"):
            output = decide(
                _event(COMPONENT + " --worker-nonce " + "0" * 32, agent_type), issue=_Issuer()
            )
            self.assertEqual(_decision(output), "deny")

    def test_two_calls_or_an_unparseable_call_are_refused(self):
        twice = COMPONENT + " && " + COMPONENT
        output = decide(_event(twice, "component-worker"), issue=_Issuer())
        self.assertEqual(_decision(output), "deny")
        output = decide(_event("python3 scripts/make_round 'cad", "component-worker"), issue=_Issuer())
        self.assertEqual(_decision(output), "deny")

    def test_self_check_and_help_run_for_anyone(self):
        for flag in ("--self-check", "--help"):
            self.assertIsNone(decide(_event(SCRIPT + " " + flag, "rowan-vale"), issue=_Issuer()))


class HookProcessTest(unittest.TestCase):
    def test_script_appends_the_issued_nonce_beside_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "make_round_guard.py"
            script.write_bytes(Path(make_round_guard.__file__).read_bytes())
            completed = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps(_event(COMPONENT, "component-worker")),
                capture_output=True, text=True, check=True,
            )
            output = json.loads(completed.stdout)
            records = [
                json.loads(line)
                for line in (Path(directory) / NONCE_TABLE_NAME).read_text().splitlines()
            ]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["component"], "part_wing.step.py")
            self.assertEqual(records[0]["agent_type"], "component-worker")
            self.assertIn(
                "--worker-nonce %s " % records[0]["nonce"],
                output["hookSpecificOutput"]["updatedInput"]["command"],
            )

    def test_script_denies_when_the_input_is_not_json(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "make_round_guard.py"
            script.write_bytes(Path(make_round_guard.__file__).read_bytes())
            completed = subprocess.run(
                [sys.executable, str(script)], input="not json",
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(_decision(json.loads(completed.stdout)), "deny")


if __name__ == "__main__":
    unittest.main()
