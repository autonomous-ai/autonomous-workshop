import json
import os
import stat
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError
from workshop.runtime.claude import (
    CLAUDE_ALLOWED_TOOLS,
    CLAUDE_GOAL_CONTINUATION_PROMPT,
    MAX_CLAUDE_EVENT_BYTES,
    ClaudeInvocationError,
    ClaudeNativeSessionLauncher,
    claude_subprocess_environment,
    claude_supports_native_workshop,
)
from workshop.runtime.managers import NativeManagerInvocationError


SESSION_ID = "d8a9fcdd-e7d8-4ab8-b8ca-9140129a4567"
OTHER_SESSION_ID = "08129530-0760-47d9-8647-a8c9e9c96ced"
WISH_SHA256 = "1" * 64
CONSTITUTION_SHA256 = "2" * 64
MATCH_CHECKPOINT_SHA256 = "3" * 64
INVENT_CHECKPOINT_SHA256 = "4" * 64
START_GOAL = "/goal Complete Match and run the finalizer."
RESUME_GOAL = "/goal Continue with the current immutable stage."
PLUGIN_NAME = "autonomous-workshop"
PLUGIN_AGENT = "%s:peter" % PLUGIN_NAME
PLUGIN_SKILL = "%s:autonomous-workshop" % PLUGIN_NAME
CLAUDE_2_1_BUNDLED_SKILLS = (
    "deep-research",
    "dataviz",
    "update-config",
    "verify",
    "debug",
    "code-review",
    "simplify",
    "batch",
    "fewer-permission-prompts",
    "doctor",
    "loop",
    "claude-api",
    "run",
    "run-skill-generator",
)
CLAUDE_2_1_OTHER_SLASH_COMMANDS = (
    "agents",
    "auto-mode-setup",
    "autocompact",
    "clear",
    "color",
    "compact",
    "config",
    "context",
    "effort",
    "fast",
    "heapdump",
    "init",
    "mcp",
    "model",
    "__remote-workflow",
    "workflow-launch-exec",
    "reload-skills",
    "rename",
    "security-review",
    "usage",
    "insights",
    "recap",
    "goal",
    "team-onboarding",
)
MISSING = object()


def event(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def init_event(
    root,
    *,
    session_id=SESSION_ID,
    version="2.1.246",
    model="claude-opus-5",
    permission_mode="dontAsk",
    mcp_servers=None,
    tools=None,
    agents=None,
    skills=None,
    slash_commands=None,
    plugins=None,
    api_key_source="ANTHROPIC_API_KEY",
    plugin_errors=MISSING,
    mcp_server_errors=MISSING,
):
    value = {
        "type": "system",
        "subtype": "init",
        "cwd": str(root),
        "session_id": session_id,
        "claude_code_version": version,
        "model": model,
        "permissionMode": permission_mode,
        "mcp_servers": [] if mcp_servers is None else mcp_servers,
        "tools": (
            ["Task", "Bash", "Edit", "Skill", "WebFetch", "WebSearch", "Write"]
            if tools is None
            else tools
        ),
        "agents": [PLUGIN_AGENT] if agents is None else agents,
        "skills": (
            [CLAUDE_2_1_BUNDLED_SKILLS[0], PLUGIN_SKILL]
            + list(CLAUDE_2_1_BUNDLED_SKILLS[1:])
            if skills is None
            else skills
        ),
        "slash_commands": (
            [CLAUDE_2_1_BUNDLED_SKILLS[0], PLUGIN_SKILL]
            + list(CLAUDE_2_1_BUNDLED_SKILLS[1:])
            + list(CLAUDE_2_1_OTHER_SLASH_COMMANDS)
            if slash_commands is None
            else slash_commands
        ),
        "apiKeySource": api_key_source,
        "plugins": (
            [
                {
                    "name": PLUGIN_NAME,
                    "path": str(root / ".claude"),
                    "source": "%s@inline" % PLUGIN_NAME,
                    "version": "1.0.0",
                }
            ]
            if plugins is None
            else plugins
        ),
    }
    if plugin_errors is not MISSING:
        value["plugin_errors"] = plugin_errors
    if mcp_server_errors is not MISSING:
        value["mcp_server_errors"] = mcp_server_errors
    return value


def result_event(
    *,
    session_id=SESSION_ID,
    subtype="success",
    is_error=False,
    stop_reason="end_turn",
    terminal_reason=MISSING,
    permission_denials=MISSING,
    result="stage proposal finalized",
):
    value = {
        "type": "result",
        "subtype": subtype,
        "is_error": is_error,
        "result": result,
    }
    if session_id is not MISSING:
        value["session_id"] = session_id
    if stop_reason is not MISSING:
        value["stop_reason"] = stop_reason
    if terminal_reason is not MISSING:
        value["terminal_reason"] = terminal_reason
    if permission_denials is not MISSING:
        value["permission_denials"] = permission_denials
    return value


def goal_activation_event(prompt=START_GOAL, *, session_id=SESSION_ID):
    return {
        "type": "assistant",
        "parent_tool_use_id": None,
        "session_id": session_id,
        "message": {
            "container": None,
            "context_management": None,
            "diagnostics": None,
            "model": "<synthetic>",
            "role": "assistant",
            "stop_details": None,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "type": "message",
            "content": [
                {
                    "type": "text",
                    "text": "Goal set: " + prompt.removeprefix("/goal "),
                }
            ],
        },
    }


def success_stream(
    root,
    *,
    goal_prompt=START_GOAL,
    search=False,
    task_alias=True,
):
    tools = [
        "Task" if task_alias else "Agent",
        "Bash",
        "Edit",
        "Skill",
        "WebFetch",
        "WebSearch",
        "Write",
    ]
    values = [event(init_event(root, tools=tools))]
    if goal_prompt is not None:
        values.append(event(goal_activation_event(goal_prompt)))
    if search:
        values.append(
            event(
                {
                    "type": "assistant",
                    "session_id": SESSION_ID,
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "WebSearch",
                                "input": {"query": "toy hinges"},
                            },
                            {"type": "text", "text": "research complete"},
                        ]
                    },
                }
            )
        )
    values.append(event(result_event()))
    return values


class RecordingInput:
    def __init__(self, *, write_error=None):
        self.value = ""
        self.closed = False
        self.write_error = write_error

    def write(self, value):
        if self.write_error is not None:
            raise self.write_error
        self.value += value

    def flush(self):
        return None

    def close(self):
        self.closed = True


class ScriptedStream:
    def __init__(self, values, callbacks=None):
        self.values = list(values)
        self.callbacks = list(callbacks or [])

    def __iter__(self):
        for index, value in enumerate(self.values):
            if index < len(self.callbacks) and self.callbacks[index] is not None:
                self.callbacks[index]()
            yield value


class FakeProcess:
    def __init__(self, script, *, pid=424242):
        self.stdin = RecordingInput(write_error=script.get("stdin_write_error"))
        self.stdout = ScriptedStream(
            script.get("stdout", []),
            callbacks=script.get("stdout_callbacks"),
        )
        self.stderr = ScriptedStream(script.get("stderr", []))
        self.pid = pid
        self.returncode = script.get("returncode", 0)
        self.wait_timeout = script.get("wait_timeout", False)
        self.wait_error = script.get("wait_error")
        self.terminated = False
        self.killed = False

    def poll(self):
        if self.terminated or self.killed:
            return self.returncode
        return None

    def wait(self, timeout=None):
        if self.wait_error is not None and not (self.terminated or self.killed):
            raise self.wait_error
        if self.wait_timeout and not (self.terminated or self.killed):
            raise subprocess.TimeoutExpired("claude", timeout)
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.killed = True
        self.returncode = -9


class FakePopenFactory:
    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.calls = []
        self.processes = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), kwargs))
        script = self.scripts.pop(0)
        if isinstance(script, Exception):
            raise script
        process = FakeProcess(script)
        self.processes.append(process)
        return process


class ImmediateTimer:
    def __init__(self, unused_interval, callback):
        self.callback = callback

    def start(self):
        self.callback()

    def cancel(self):
        return None


class ClaudeNativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.auth_environment = mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-claude-api-key"}, clear=False
        )
        self.auth_environment.start()
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.run_root = self.base / "toy"
        self.run_root.mkdir()
        self.host_state_root = self.base / "state"
        self.host_state_root.mkdir(mode=0o700)
        os.chmod(self.host_state_root, 0o700)
        self._materialize_plugin(self.run_root)

    def tearDown(self):
        self.temporary.cleanup()
        self.auth_environment.stop()

    @staticmethod
    def _materialize_plugin(root):
        (root / "AGENTS.md").write_text(
            "# Workshop Manager\nRead STAGE.json and finalize one stage.\n",
            encoding="utf-8",
        )
        (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        manifest = root / ".claude" / ".claude-plugin"
        agents = root / ".claude" / "agents"
        skills = root / ".claude" / "skills" / "autonomous-workshop"
        manifest.mkdir(parents=True, exist_ok=True)
        agents.mkdir(parents=True, exist_ok=True)
        skills.mkdir(parents=True, exist_ok=True)
        (manifest / "plugin.json").write_text(
            json.dumps(
                {
                    "name": PLUGIN_NAME,
                    "description": "Host-projected Workshop runtime",
                    "version": "1.0.0",
                    "author": {"name": "Autonomous Workshop"},
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (agents / "peter.md").write_text(
            "---\nname: peter\ndescription: Invents toys\n---\n\nUse exact Taste.\n",
            encoding="utf-8",
        )
        (skills / "SKILL.md").write_text(
            "---\nname: autonomous-workshop\ndescription: Run one stage\n---\n\n"
            "Finalize the current stage.\n",
            encoding="utf-8",
        )

    def launcher(self, scripts, **overrides):
        factory = FakePopenFactory(scripts)
        launcher = ClaudeNativeSessionLauncher(
            binary="/opt/claude",
            cli_version=overrides.pop("cli_version", "2.1.246"),
            popen_factory=factory,
            uuid_factory=overrides.pop(
                "uuid_factory", lambda: uuid.UUID(SESSION_ID)
            ),
            **overrides,
        )
        return launcher, factory

    def start(self, launcher, **overrides):
        values = {
            "product_id": "toy-1",
            "wish_sha256": WISH_SHA256,
            "constitution_sha256": CONSTITUTION_SHA256,
            "run_root": self.run_root,
            "host_state_root": self.host_state_root,
            "prompt": START_GOAL,
            "goal_stage": "match",
            "goal_checkpoint_sha256": MATCH_CHECKPOINT_SHA256,
        }
        values.update(overrides)
        return launcher.start(**values)

    def resume(self, launcher, **overrides):
        values = {
            "product_id": "toy-1",
            "wish_sha256": WISH_SHA256,
            "constitution_sha256": CONSTITUTION_SHA256,
            "run_root": self.run_root,
            "host_state_root": self.host_state_root,
            "prompt": RESUME_GOAL,
            "goal_stage": "invent",
            "goal_checkpoint_sha256": INVENT_CHECKPOINT_SHA256,
        }
        values.update(overrides)
        return launcher.resume(**values)

    def acknowledge(self, launcher, **overrides):
        values = {
            "product_id": "toy-1",
            "wish_sha256": WISH_SHA256,
            "constitution_sha256": CONSTITUTION_SHA256,
            "run_root": self.run_root,
            "host_state_root": self.host_state_root,
            "prompt": START_GOAL,
            "goal_stage": "match",
            "goal_checkpoint_sha256": MATCH_CHECKPOINT_SHA256,
        }
        values.update(overrides)
        return launcher.acknowledge_goal(**values)

    def disposition(self, launcher, **overrides):
        values = {
            "product_id": "toy-1",
            "wish_sha256": WISH_SHA256,
            "constitution_sha256": CONSTITUTION_SHA256,
            "run_root": self.run_root,
            "host_state_root": self.host_state_root,
            "prompt": START_GOAL,
            "goal_stage": "match",
            "goal_checkpoint_sha256": MATCH_CHECKPOINT_SHA256,
        }
        values.update(overrides)
        return launcher.goal_disposition(**values)

    def clear_checkpoints(self):
        for name in ("claude-session.json", "claude-goal.json"):
            (self.host_state_root / name).unlink(missing_ok=True)

    def test_start_uses_exact_cli_policy_and_private_host_generated_session(self):
        checkpoint = self.host_state_root / "claude-session.json"

        def assert_checkpoint_precedes_init():
            self.assertTrue(checkpoint.is_file())
            self.assertEqual(stat.S_IMODE(checkpoint.stat().st_mode), 0o600)
            self.assertEqual(json.loads(checkpoint.read_text())["session_id"], SESSION_ID)
            goal = self.host_state_root / "claude-goal.json"
            self.assertTrue(goal.is_file())
            self.assertEqual(stat.S_IMODE(goal.stat().st_mode), 0o600)
            self.assertEqual(json.loads(goal.read_text())["status"], "prepared")

        stream = success_stream(self.run_root, search=True, task_alias=True)
        launcher, factory = self.launcher(
            [
                {
                    "stdout": stream,
                    "stdout_callbacks": [assert_checkpoint_precedes_init],
                }
            ]
        )
        with mock.patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "claude-secret",
                "FACTORY_API_KEY": "factory-secret",
                "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
                "AWS_SECRET_ACCESS_KEY": "cloud-secret",
                "HOME": "/ambient/home/must-not-be-inherited",
            },
            clear=False,
        ):
            outcome = self.start(launcher)

        self.assertTrue(outcome.used_web_search)
        public = json.dumps(outcome.to_dict(), sort_keys=True)
        self.assertNotIn(SESSION_ID, public)
        self.assertNotIn("claude-secret", public)
        command, kwargs = factory.calls[0]
        self.assertEqual(command[0], "/opt/claude")
        self.assertNotIn("--bare", command)
        self.assertIn("-p", command)
        self.assertEqual(command[command.index("--input-format") + 1], "text")
        self.assertEqual(
            command[command.index("--output-format") + 1], "stream-json"
        )
        self.assertIn("--verbose", command)
        self.assertEqual(command[command.index("--model") + 1], "claude-opus-5")
        self.assertEqual(command[command.index("--effort") + 1], "high")
        self.assertEqual(command[command.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(command[command.index("--setting-sources") + 1], "")
        self.assertEqual(command[command.index("--agents") + 1], "{}")
        self.assertEqual(
            command[command.index("--mcp-config") + 1], '{"mcpServers":{}}'
        )
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(
            command[command.index("--plugin-dir") + 1],
            str(self.run_root / ".claude"),
        )
        self.assertEqual(
            command[command.index("--append-system-prompt-file") + 1],
            str(self.run_root / "AGENTS.md"),
        )
        available_tools = command[command.index("--tools") + 1].split(",")
        self.assertEqual(set(available_tools), set(CLAUDE_ALLOWED_TOOLS))
        self.assertTrue({"Edit", "Write", "Bash"} <= set(available_tools))
        self.assertTrue({"Read", "Glob", "Grep"}.isdisjoint(available_tools))
        allowed_start = command.index("--allowedTools") + 1
        allowed_end = command.index("--agents")
        allowed_tools = command[allowed_start:allowed_end]
        absolute_root = "/" + self.run_root.as_posix() + "/**"
        self.assertIn("Edit(%s)" % absolute_root, allowed_tools)
        self.assertIn("Write(%s)" % absolute_root, allowed_tools)
        self.assertNotIn("Edit", allowed_tools)
        self.assertNotIn("Write", allowed_tools)
        self.assertEqual(command[command.index("--session-id") + 1], SESSION_ID)
        self.assertNotIn("--resume", command)
        self.assertEqual(kwargs["cwd"], str(self.run_root))
        if os.name == "posix":
            self.assertIs(kwargs["start_new_session"], True)
        self.assertEqual(factory.processes[0].stdin.value, START_GOAL)
        environment = kwargs["env"]
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "claude-secret")
        private_home = self.host_state_root / "claude-home"
        private_config = self.host_state_root / "claude-config"
        private_claude_temp = self.host_state_root / "claude-tmp"
        self.assertEqual(environment["HOME"], str(private_home))
        self.assertEqual(environment["CLAUDE_CONFIG_DIR"], str(private_config))
        self.assertEqual(environment["CLAUDE_CODE_TMPDIR"], str(private_claude_temp))
        for private in (private_home, private_config, private_claude_temp):
            self.assertTrue(private.is_dir())
            self.assertFalse(private.is_symlink())
            self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
        self.assertNotIn("FACTORY_API_KEY", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertEqual(environment["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"], "0")
        self.assertEqual(environment["CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS"], "1")
        settings = json.loads(command[command.index("--settings") + 1])
        self.assertIs(settings["autoMemoryEnabled"], False)
        self.assertEqual(settings["cleanupPeriodDays"], 36_500)
        self.assertNotIn("disableAllHooks", settings)
        sandbox = settings["sandbox"]
        self.assertIs(sandbox["enabled"], True)
        self.assertIs(sandbox["failIfUnavailable"], True)
        self.assertIs(sandbox["allowUnsandboxedCommands"], False)
        self.assertEqual(sandbox["excludedCommands"], [])
        self.assertEqual(sandbox["filesystem"]["denyRead"], ["/"])
        allowed_reads = set(sandbox["filesystem"]["allowRead"])
        self.assertIn(str(self.run_root), allowed_reads)
        for value in (
            "/bin",
            "/usr/bin",
            "/usr/lib",
            "/lib",
            "/lib64",
            "/System/Library",
            "/Library/Apple",
        ):
            path = Path(value)
            if path.exists() or path.is_symlink():
                self.assertIn(value, allowed_reads)
                self.assertIn(str(path.resolve(strict=True)), allowed_reads)
        self.assertNotIn(str(self.base), allowed_reads)
        self.assertEqual(sandbox["network"]["allowedDomains"], [])
        self.assertEqual(sandbox["network"]["deniedDomains"], ["*"])
        credential_names = {
            row["name"] for row in sandbox["credentials"]["envVars"]
        }
        self.assertEqual(
            credential_names,
            {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"},
        )
        self.assertTrue(
            all(row["mode"] == "deny" for row in sandbox["credentials"]["envVars"])
        )
        self.assertEqual(settings["permissions"]["allow"], allowed_tools)
        self.assertTrue(
            {"Read", "Glob", "Grep", "Edit", "Write"}.isdisjoint(
                settings["permissions"]["allow"]
            )
        )
        self.assertTrue(issubclass(ClaudeInvocationError, NativeManagerInvocationError))
        goal_state = json.loads(
            (self.host_state_root / "claude-goal.json").read_text(encoding="utf-8")
        )
        self.assertEqual(goal_state["status"], "returned")
        self.assertEqual(goal_state["stage"], "match")
        self.assertEqual(
            goal_state["stage_checkpoint_sha256"], MATCH_CHECKPOINT_SHA256
        )

    def test_resume_repeats_policy_and_uses_only_exact_private_session(self):
        launcher, factory = self.launcher(
            [
                {"stdout": success_stream(self.run_root)},
                {"stdout": success_stream(self.run_root, goal_prompt=RESUME_GOAL)},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)
        resumed = self.resume(launcher)
        start_command = factory.calls[0][0]
        resume_command = factory.calls[1][0]
        self.assertNotIn("--session-id", resume_command)
        self.assertEqual(
            resume_command[resume_command.index("--resume") + 1], SESSION_ID
        )
        self.assertEqual(
            start_command[: start_command.index("--session-id")],
            resume_command[: resume_command.index("--resume")],
        )
        resume_settings = json.loads(
            resume_command[resume_command.index("--settings") + 1]
        )
        self.assertEqual(resume_settings["cleanupPeriodDays"], 36_500)
        self.assertNotIn("disableAllHooks", resume_settings)
        self.assertNotIn(SESSION_ID, json.dumps(resumed.to_dict(), sort_keys=True))
        self.assertEqual(factory.processes[1].stdin.value, RESUME_GOAL)

    def test_start_popen_failure_rolls_back_unsubmitted_checkpoints(self):
        launcher, factory = self.launcher(
            [
                OSError("exec failed"),
                {"stdout": success_stream(self.run_root)},
            ]
        )

        with self.assertRaisesRegex(ClaudeInvocationError, "could not be launched"):
            self.start(launcher)

        self.assertFalse((self.host_state_root / "claude-session.json").exists())
        self.assertFalse((self.host_state_root / "claude-goal.json").exists())
        self.start(launcher)
        self.assertEqual(len(factory.calls), 2)

    def test_bootstrap_recovers_a_crash_after_the_goal_half_is_durable(self):
        launcher, factory = self.launcher(
            [{"stdout": success_stream(self.run_root)}]
        )
        from workshop.runtime import claude as claude_runtime

        original_write = claude_runtime._write_private_checkpoint

        def crash_after_goal(path, value):
            original_write(path, value)
            if path.name == "claude-goal.json":
                raise KeyboardInterrupt()

        with (
            mock.patch(
                "workshop.runtime.claude._write_private_checkpoint",
                side_effect=crash_after_goal,
            ),
            mock.patch(
                "workshop.runtime.claude._rollback_unlaunched_checkpoints"
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                self.start(launcher)

        self.assertFalse((self.host_state_root / "claude-session.json").exists())
        self.assertTrue((self.host_state_root / "claude-goal.json").is_file())
        self.start(launcher)
        self.assertEqual(len(factory.calls), 1)

    def test_bootstrap_second_write_failure_rolls_back_both_halves(self):
        launcher, factory = self.launcher([])
        from workshop.runtime import claude as claude_runtime

        original_write = claude_runtime._write_private_checkpoint

        def fail_session_commit(path, value):
            if path.name == "claude-session.json":
                raise ClaudeInvocationError("injected session commit failure")
            original_write(path, value)

        with mock.patch(
            "workshop.runtime.claude._write_private_checkpoint",
            side_effect=fail_session_commit,
        ):
            with self.assertRaisesRegex(
                ClaudeInvocationError,
                "session commit failure",
            ):
                self.start(launcher)

        self.assertFalse((self.host_state_root / "claude-session.json").exists())
        self.assertFalse((self.host_state_root / "claude-goal.json").exists())
        self.assertEqual(factory.calls, [])

    def test_completed_goal_popen_failure_restores_completed_attempt(self):
        launcher, factory = self.launcher(
            [
                {"stdout": success_stream(self.run_root)},
                OSError("exec failed"),
                {"stdout": success_stream(self.run_root, goal_prompt=RESUME_GOAL)},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)
        path = self.host_state_root / "claude-goal.json"
        completed = json.loads(path.read_text(encoding="utf-8"))

        with self.assertRaisesRegex(ClaudeInvocationError, "could not be launched"):
            self.resume(launcher)

        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), completed)
        self.resume(launcher)
        self.assertEqual(factory.processes[1].stdin.value, RESUME_GOAL)
        self.assertNotEqual(
            factory.processes[1].stdin.value,
            CLAUDE_GOAL_CONTINUATION_PROMPT,
        )

    def test_completed_goal_delivery_interruption_stays_prepared(self):
        launcher, factory = self.launcher(
            [
                {"stdout": success_stream(self.run_root)},
                {"stdin_write_error": BrokenPipeError("delivery interrupted")},
                {"stdout": success_stream(self.run_root, goal_prompt=RESUME_GOAL)},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)

        with self.assertRaisesRegex(ClaudeInvocationError, "receive its prompt"):
            self.resume(launcher)

        path = self.host_state_root / "claude-goal.json"
        prepared = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(prepared["stage"], "invent")
        self.assertEqual(prepared["attempt"], 2)
        with self.assertRaisesRegex(ContractError, "cannot be resumed safely"):
            self.resume(launcher)
        with self.assertRaisesRegex(ContractError, "prepared attempt"):
            self.acknowledge(
                launcher,
                prompt=RESUME_GOAL,
                goal_stage="invent",
                goal_checkpoint_sha256=INVENT_CHECKPOINT_SHA256,
            )
        self.assertEqual(len(factory.calls), 2)

    def test_returned_goal_retry_starts_a_new_native_goal(self):
        launcher, factory = self.launcher(
            [
                {"stdout": success_stream(self.run_root)},
                {"stdout": success_stream(self.run_root)},
            ]
        )
        self.start(launcher)
        path = self.host_state_root / "claude-goal.json"
        returned = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(returned["status"], "returned")

        self.resume(
            launcher,
            prompt=START_GOAL,
            goal_stage="match",
            goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
        )

        self.assertEqual(factory.processes[1].stdin.value, START_GOAL)
        self.assertNotEqual(
            factory.processes[1].stdin.value,
            CLAUDE_GOAL_CONTINUATION_PROMPT,
        )
        retried = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(retried["status"], "returned")
        self.assertEqual(retried["attempt"], 2)

    def test_resume_continues_an_interrupted_active_goal_without_replacing_it(self):
        launcher, factory = self.launcher(
            [
                {
                    "stdout": [
                        event(init_event(self.run_root)),
                        event(goal_activation_event()),
                    ]
                },
                {"stdout": success_stream(self.run_root, goal_prompt=None)},
            ]
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "did not complete"):
            self.start(launcher)
        checkpoint = self.host_state_root / "claude-goal.json"
        active = json.loads(checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(active["status"], "active")
        self.assertEqual(active["attempt"], 1)
        with self.assertRaisesRegex(ContractError, "attested terminal return"):
            self.acknowledge(launcher)
        self.assertEqual(
            json.loads(checkpoint.read_text(encoding="utf-8")),
            active,
        )

        self.resume(
            launcher,
            prompt=START_GOAL,
            goal_stage="match",
            goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
        )

        self.assertEqual(
            factory.processes[1].stdin.value,
            CLAUDE_GOAL_CONTINUATION_PROMPT,
        )
        self.assertFalse(factory.processes[1].stdin.value.startswith("/goal "))
        returned = json.loads(checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(returned["status"], "returned")
        self.acknowledge(launcher)
        completed = json.loads(checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["attempt"], 1)

    def test_resume_does_not_replace_an_interrupted_goal_with_a_new_stage(self):
        launcher, factory = self.launcher(
            [
                {
                    "stdout": [
                        event(init_event(self.run_root)),
                        event(goal_activation_event()),
                    ]
                }
            ]
        )
        with self.assertRaises(ClaudeInvocationError):
            self.start(launcher)

        with self.assertRaisesRegex(ContractError, "interrupted active Goal"):
            self.resume(launcher)
        self.assertEqual(len(factory.calls), 1)

    def test_completed_goal_can_start_a_new_epoch_with_the_same_condition(self):
        launcher, factory = self.launcher(
            [
                {"stdout": success_stream(self.run_root)},
                {"stdout": success_stream(self.run_root)},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)
        self.resume(
            launcher,
            prompt=START_GOAL,
            goal_stage="match",
            goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
        )

        self.assertEqual(factory.processes[1].stdin.value, START_GOAL)
        checkpoint = json.loads(
            (self.host_state_root / "claude-goal.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(checkpoint["status"], "returned")
        self.assertEqual(checkpoint["attempt"], 2)
        self.acknowledge(launcher)
        checkpoint = json.loads(
            (self.host_state_root / "claude-goal.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(checkpoint["status"], "completed")
        self.assertEqual(checkpoint["attempt"], 2)

    def test_goal_acknowledgement_is_exact_and_idempotent(self):
        launcher, unused_factory = self.launcher(
            [{"stdout": success_stream(self.run_root)}]
        )
        self.start(launcher)
        with self.assertRaisesRegex(ContractError, "acknowledgement"):
            self.acknowledge(
                launcher,
                goal_checkpoint_sha256=INVENT_CHECKPOINT_SHA256,
            )
        path = self.host_state_root / "claude-goal.json"
        self.assertEqual(json.loads(path.read_text())["status"], "returned")

        self.acknowledge(launcher)
        completed = json.loads(path.read_text())
        self.acknowledge(launcher)
        self.assertEqual(json.loads(path.read_text()), completed)
        self.assertEqual(completed["status"], "completed")

    def test_goal_disposition_reads_only_the_exact_bound_sidecar(self):
        launcher, factory = self.launcher(
            [
                {
                    "stdout": [
                        event(init_event(self.run_root)),
                        event(goal_activation_event()),
                    ]
                },
                {"stdout": success_stream(self.run_root, goal_prompt=None)},
            ]
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "did not complete"):
            self.start(launcher)
        self.assertEqual(self.disposition(launcher), "active")
        self.assertEqual(len(factory.calls), 1)

        self.resume(
            launcher,
            prompt=START_GOAL,
            goal_stage="match",
            goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
        )
        self.assertEqual(self.disposition(launcher), "returned")
        self.acknowledge(launcher)
        self.assertEqual(self.disposition(launcher), "completed")
        with self.assertRaisesRegex(ContractError, "disposition"):
            self.disposition(
                launcher,
                goal_checkpoint_sha256=INVENT_CHECKPOINT_SHA256,
            )
        self.assertEqual(len(factory.calls), 2)

    def test_goal_disposition_reports_ambiguous_prepared_delivery(self):
        launcher, factory = self.launcher(
            [{"stdin_write_error": BrokenPipeError("delivery interrupted")}]
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "receive its prompt"):
            self.start(launcher)
        self.assertEqual(self.disposition(launcher), "prepared")
        self.assertEqual(len(factory.calls), 1)

    def test_start_requires_the_native_noninteractive_goal_command(self):
        launcher, factory = self.launcher([])
        with self.assertRaisesRegex(ContractError, "invoke /goal"):
            self.start(launcher, prompt="Complete Match without native Goal control.")
        self.assertEqual(factory.calls, [])

    def test_start_requires_isolated_api_auth_before_persisting_a_session(self):
        launcher, factory = self.launcher([])
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ClaudeInvocationError, "ANTHROPIC_API_KEY"):
                self.start(launcher)
        self.assertEqual(factory.calls, [])
        self.assertFalse((self.host_state_root / "claude-session.json").exists())

    def test_version_floor_and_probe_environment_are_fail_closed(self):
        self.assertFalse(claude_supports_native_workshop("2.1.245"))
        self.assertTrue(claude_supports_native_workshop("2.1.246"))
        self.assertTrue(claude_supports_native_workshop("2.1.246+native.1"))
        self.assertFalse(claude_supports_native_workshop("2.1"))
        with self.assertRaisesRegex(ClaudeInvocationError, "2.1.246"):
            ClaudeNativeSessionLauncher(binary="claude", cli_version="2.1.245")

        calls = []

        def version_runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, "2.1.246 (Claude Code)\n", "")

        with mock.patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "allowed-auth",
                "FACTORY_TOKEN": "forbidden-effect",
                "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
            },
            clear=False,
        ):
            launcher = ClaudeNativeSessionLauncher(
                binary="claude",
                version_runner=version_runner,
            )
        self.assertEqual(launcher.cli_version, "2.1.246")
        environment = calls[0][1]["env"]
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "allowed-auth")
        self.assertNotIn("ANTHROPIC_AUTH_TOKEN", environment)
        self.assertNotIn("FACTORY_TOKEN", environment)
        self.assertNotIn("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", environment)

    def test_init_attestation_rejects_every_authority_mismatch(self):
        cases = {
            "session": {"session_id": OTHER_SESSION_ID},
            "version": {"version": "2.1.247"},
            "model": {"model": "claude-sonnet-5"},
            "permission": {"permission_mode": "acceptEdits"},
            "authentication": {"api_key_source": "CLAUDE_CODE_OAUTH_TOKEN"},
            "mcp": {"mcp_servers": [{"name": "ambient"}]},
            "tools": {"tools": ["Read"]},
            "agents": {"agents": ["ambient:agent"]},
            "skills": {"skills": ["ambient:skill"]},
            "standalone skill": {
                "skills": [PLUGIN_SKILL, "ambient:standalone-skill"]
            },
            "missing Goal command": {"slash_commands": [PLUGIN_SKILL]},
            "plugins": {
                "plugins": [
                    {"name": PLUGIN_NAME, "path": str(self.run_root / ".claude")},
                    {"name": "ambient", "path": "/tmp/ambient"},
                ]
            },
            "plugin error": {
                "plugin_errors": [
                    {"plugin": PLUGIN_NAME, "type": "load", "message": "failed"}
                ]
            },
            "MCP error": {
                "mcp_server_errors": [{"name": "ambient", "message": "failed"}]
            },
        }
        for label, overrides in cases.items():
            with self.subTest(label=label):
                self.clear_checkpoints()
                values = [
                    event(init_event(self.run_root, **overrides)),
                    event(result_event()),
                ]
                launcher, factory = self.launcher([{"stdout": values}])
                with self.assertRaises(ClaudeInvocationError):
                    self.start(launcher)
                self.assertEqual(len(factory.calls), 1)

        self.clear_checkpoints()
        launcher, unused_factory = self.launcher(
            [{"stdout": [event(result_event())]}]
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "initialization"):
            self.start(launcher)

    def test_goal_activation_requires_exact_synthetic_acknowledgement(self):
        wrong_model = goal_activation_event()
        wrong_model["message"]["model"] = "claude-opus-5"
        extra_content = goal_activation_event()
        extra_content["message"]["content"].append(
            {"type": "text", "text": "extra"}
        )
        cases = (
            None,
            goal_activation_event(RESUME_GOAL),
            goal_activation_event(session_id=OTHER_SESSION_ID),
            wrong_model,
            extra_content,
        )
        for acknowledgement in cases:
            with self.subTest(acknowledgement=acknowledgement):
                self.clear_checkpoints()
                values = [event(init_event(self.run_root))]
                if acknowledgement is not None:
                    values.append(event(acknowledgement))
                values.append(event(result_event()))
                launcher, factory = self.launcher([{"stdout": values}])

                with self.assertRaisesRegex(
                    ClaudeInvocationError,
                    "Goal activation|different native session",
                ):
                    self.start(launcher)

                prepared = json.loads(
                    (self.host_state_root / "claude-goal.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(prepared["status"], "prepared")
                self.assertEqual(len(factory.calls), 1)

    def test_result_attestation_rejects_failures_missing_and_trailing_events(self):
        initialized = event(init_event(self.run_root))
        activated = event(goal_activation_event())
        cases = (
            [initialized, activated],
            [initialized, activated, event(result_event(is_error=True))],
            [initialized, activated, event(result_event(subtype="error"))],
            [
                initialized,
                activated,
                event(result_event(stop_reason=MISSING)),
            ],
            [
                initialized,
                activated,
                event(result_event(stop_reason="deferred_tool_use")),
            ],
            [
                initialized,
                activated,
                event(result_event(permission_denials=[{"tool": "Bash"}])),
            ],
            [
                initialized,
                activated,
                event(result_event(session_id=OTHER_SESSION_ID)),
            ],
            [
                initialized,
                activated,
                event(result_event(session_id=MISSING)),
            ],
            [
                initialized,
                activated,
                event(result_event()),
                event({"type": "system", "subtype": "status"}),
            ],
        )
        for values in cases:
            with self.subTest(events=len(values)):
                self.clear_checkpoints()
                launcher, unused_factory = self.launcher([{"stdout": values}])
                with self.assertRaises(ClaudeInvocationError):
                    self.start(launcher)

        self.clear_checkpoints()
        launcher, unused_factory = self.launcher(
            [
                {
                    "stdout": [
                        event(init_event(self.run_root)),
                        event(goal_activation_event()),
                        event(
                            result_event(
                                stop_reason=None,
                                terminal_reason="completed",
                                permission_denials=[],
                            )
                        ),
                    ]
                }
            ]
        )
        self.start(launcher)

    def test_result_is_not_returned_until_stream_and_exit_are_fully_attested(self):
        terminal_stream = success_stream(self.run_root)
        cases = (
            {
                "stdout": terminal_stream
                + [event({"type": "system", "subtype": "status"})],
            },
            {
                "stdout": terminal_stream,
                "returncode": 1,
            },
        )
        for script in cases:
            with self.subTest(script=tuple(sorted(script))):
                self.clear_checkpoints()
                launcher, factory = self.launcher([script])
                with self.assertRaises(ClaudeInvocationError):
                    self.start(launcher)
                state = json.loads(
                    (self.host_state_root / "claude-goal.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(state["status"], "active")
                self.assertEqual(len(factory.calls), 1)

    def test_resume_rejects_tampered_binding_wrong_root_and_plugin_change(self):
        launcher, factory = self.launcher([{"stdout": success_stream(self.run_root)}])
        self.start(launcher)
        checkpoint = self.host_state_root / "claude-session.json"
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        payload["session_id"] = OTHER_SESSION_ID
        checkpoint.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        os.chmod(checkpoint, 0o600)
        with self.assertRaisesRegex(ContractError, "binding"):
            self.resume(launcher)
        self.assertEqual(len(factory.calls), 1)

        self.clear_checkpoints()
        launcher, factory = self.launcher([{"stdout": success_stream(self.run_root)}])
        self.start(launcher)
        (self.run_root / ".claude" / "skills" / "autonomous-workshop" / "SKILL.md").write_text(
            "---\nname: autonomous-workshop\n---\nchanged\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContractError, "binding"):
            self.resume(launcher)
        self.assertEqual(len(factory.calls), 1)

        copied_root = self.base / "copied-toy"
        copied_root.mkdir()
        self._materialize_plugin(copied_root)
        with self.assertRaises(ContractError):
            self.resume(launcher, run_root=copied_root)

    def test_resume_rejects_tampered_goal_state(self):
        launcher, factory = self.launcher(
            [{"stdout": success_stream(self.run_root)}]
        )
        self.start(launcher)
        checkpoint = self.host_state_root / "claude-goal.json"
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        payload["status"] = "completed"
        checkpoint.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        os.chmod(checkpoint, 0o600)

        with self.assertRaisesRegex(ContractError, "Goal checkpoint"):
            self.resume(
                launcher,
                prompt=START_GOAL,
                goal_stage="match",
                goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
            )
        self.assertEqual(len(factory.calls), 1)

    def test_resume_fails_closed_when_goal_state_is_missing(self):
        launcher, factory = self.launcher(
            [{"stdout": success_stream(self.run_root)}]
        )
        self.start(launcher)
        (self.host_state_root / "claude-goal.json").unlink()

        with self.assertRaisesRegex(ContractError, "cannot be resumed safely"):
            self.resume(
                launcher,
                prompt=START_GOAL,
                goal_stage="match",
                goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
            )
        self.assertEqual(len(factory.calls), 1)

    def test_resume_rejects_changed_appended_agents_instructions(self):
        launcher, factory = self.launcher(
            [{"stdout": success_stream(self.run_root)}]
        )
        self.start(launcher)
        (self.run_root / "AGENTS.md").write_text(
            "# Changed authority\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContractError, "binding"):
            self.resume(launcher)
        self.assertEqual(len(factory.calls), 1)

    def test_plugin_projection_rejects_noncanonical_manifest_and_symlink(self):
        manifest = self.run_root / ".claude" / ".claude-plugin" / "plugin.json"
        manifest.write_text('{"name":"other"}\n', encoding="utf-8")
        launcher, factory = self.launcher([])
        with self.assertRaisesRegex(ContractError, "manifest"):
            self.start(launcher)
        self.assertEqual(factory.calls, [])

        self._materialize_plugin(self.run_root)
        agent = self.run_root / ".claude" / "agents" / "peter.md"
        agent.unlink()
        agent.symlink_to(self.run_root / "CLAUDE.md")
        launcher, factory = self.launcher([])
        with self.assertRaisesRegex(ContractError, "symlink"):
            self.start(launcher)
        self.assertEqual(factory.calls, [])

    def test_checkpoint_and_root_privacy_contracts_fail_before_launch(self):
        launcher, factory = self.launcher([])
        os.chmod(self.host_state_root, 0o755)
        with self.assertRaisesRegex(ContractError, "0700"):
            self.start(launcher)
        self.assertEqual(factory.calls, [])
        os.chmod(self.host_state_root, 0o700)

        checkpoint = self.host_state_root / "claude-session.json"
        checkpoint.write_text("{}\n", encoding="utf-8")
        os.chmod(checkpoint, 0o644)
        with self.assertRaisesRegex(ContractError, "resume"):
            self.start(launcher)
        with self.assertRaisesRegex(ContractError, "0600"):
            self.resume(launcher)

    def test_private_claude_state_rejects_preseed_symlink_mode_and_path_change(self):
        home = self.host_state_root / "claude-home"
        home.mkdir(mode=0o700)
        (home / "settings.json").write_text("{}\n", encoding="utf-8")
        launcher, factory = self.launcher([])
        with self.assertRaisesRegex(ClaudeInvocationError, "empty before first launch"):
            self.start(launcher)
        self.assertEqual(factory.calls, [])

        (home / "settings.json").unlink()
        os.chmod(home, 0o755)
        with self.assertRaisesRegex(ClaudeInvocationError, "0700"):
            self.start(launcher)
        os.chmod(home, 0o700)

        config = self.host_state_root / "claude-config"
        target = self.base / "attacker-config"
        target.mkdir(mode=0o700)
        config.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ClaudeInvocationError, "real 0700"):
            self.start(launcher)
        config.unlink()

        from workshop.runtime import claude as claude_runtime

        original_private_run_temp = claude_runtime._private_run_temp

        def replace_bound_home(run_root):
            private_temp = original_private_run_temp(run_root)
            moved = self.host_state_root / "replaced-claude-home"
            home.rename(moved)
            home.mkdir(mode=0o700)
            return private_temp

        with mock.patch(
            "workshop.runtime.claude._private_run_temp",
            side_effect=replace_bound_home,
        ):
            with self.assertRaisesRegex(ClaudeInvocationError, "changed after policy"):
                self.start(launcher)
        self.assertEqual(factory.calls, [])

    def test_bounds_timeout_and_invalid_stream_terminate_the_process_group(self):
        oversized = "x" * (MAX_CLAUDE_EVENT_BYTES + 1)
        launcher, factory = self.launcher([{"stdout": [oversized]}])
        with mock.patch("workshop.runtime.claude.os.killpg") as killpg:
            with self.assertRaisesRegex(ClaudeInvocationError, "safe size"):
                self.start(launcher)
        if os.name == "posix":
            killpg.assert_called()

        self.clear_checkpoints()
        launcher, factory = self.launcher([{"stdout": [], "wait_timeout": True}])
        with (
            mock.patch("workshop.runtime.claude.threading.Timer", ImmediateTimer),
            mock.patch("workshop.runtime.claude.os.killpg") as killpg,
        ):
            with self.assertRaisesRegex(ClaudeInvocationError, "timed out"):
                self.start(launcher)
        if os.name == "posix":
            killpg.assert_called()

    def test_control_flow_interrupts_always_reap_the_process_group(self):
        for interruption in (KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(interruption=type(interruption).__name__):
                self.clear_checkpoints()

                def interrupt():
                    raise interruption

                launcher, factory = self.launcher(
                    [
                        {
                            "stdout": success_stream(self.run_root),
                            "stdout_callbacks": [interrupt],
                        }
                    ]
                )
                with mock.patch("workshop.runtime.claude.os.killpg") as killpg:
                    with self.assertRaises(type(interruption)):
                        self.start(launcher)
                if os.name == "posix":
                    killpg.assert_called()
                else:  # pragma: no cover - exercised on Windows CI
                    self.assertTrue(factory.processes[0].terminated)

    def test_control_flow_interrupt_while_waiting_reaps_the_process_group(self):
        launcher, factory = self.launcher(
            [
                {
                    "stdout": success_stream(self.run_root),
                    "wait_error": KeyboardInterrupt(),
                }
            ]
        )
        with mock.patch("workshop.runtime.claude.os.killpg") as killpg:
            with self.assertRaises(KeyboardInterrupt):
                self.start(launcher)
        if os.name == "posix":
            killpg.assert_called()
        else:  # pragma: no cover - exercised on Windows CI
            self.assertTrue(factory.processes[0].terminated)

    def test_environment_allowlist_rejects_arbitrary_expansion(self):
        source = {
            "HOME": "/safe/home",
            "ANTHROPIC_API_KEY": "auth",
            "ANTHROPIC_AUTH_TOKEN": "not-supported-in-isolated-mode",
            "CLAUDE_CODE_OAUTH_TOKEN": "not-supported-in-isolated-mode",
            "FACTORY_API_KEY": "effect",
            "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
        }
        self.assertEqual(
            claude_subprocess_environment(source),
            {"ANTHROPIC_API_KEY": "auth"},
        )
        with self.assertRaises(ValueError):
            claude_subprocess_environment(source, allowlist=("FACTORY_API_KEY",))
        with self.assertRaises(ValueError):
            claude_subprocess_environment(
                source,
                allowlist=("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB",),
            )


if __name__ == "__main__":
    unittest.main()
