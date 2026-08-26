import json
import os
import stat
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

from workshop.errors import ContractError
from workshop.runtime.grok import (
    GROK_ALLOWED_TOOLS,
    GROK_GOAL_RESUME_PROMPT,
    GROK_GOAL_STATUS_PROMPT,
    PINNED_GROK_NATIVE_RUNTIME_VERSION,
    GrokInvocationError,
    GrokNativeSessionLauncher,
    grok_supports_native_workshop,
)
from workshop.runtime.managers import NativeManagerInvocationError
from workshop.runtime.project_boundary import (
    PRODUCT_RUN_ROOT_MARKER,
    PRODUCT_RUN_ROOT_MARKER_BYTES,
)


SESSION_ID = "d8a9fcdd-e7d8-4ab8-b8ca-9140129a4567"
OTHER_SESSION_ID = "08129530-0760-47d9-8647-a8c9e9c96ced"
WISH_SHA256 = "1" * 64
CONSTITUTION_SHA256 = "2" * 64
MATCH_CHECKPOINT_SHA256 = "3" * 64
INVENT_CHECKPOINT_SHA256 = "4" * 64
START_GOAL = "/goal Complete Match and run the exact stage finalizer."
INVENT_GOAL = "/goal Complete Invent and run the exact stage finalizer."


def event(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def available_commands_event(*, session_id=SESSION_ID, tools=None, commands=None):
    return {
        "type": "available_commands",
        "sessionId": session_id,
        "tools": list(GROK_ALLOWED_TOOLS) if tools is None else tools,
        "commands": ["/goal"] if commands is None else commands,
    }


def end_event(*, session_id=SESSION_ID, request_id="request-1"):
    return {
        "type": "end",
        "sessionId": session_id,
        "requestId": request_id,
        "stopReason": "end_turn",
    }


def successful_primary_stream(*, session_id=SESSION_ID, tools=None):
    return [
        event(available_commands_event(session_id=session_id, tools=tools)),
        event(
            {
                "type": "text",
                "sessionId": session_id,
                "data": "Stage proposal finalized.",
            }
        ),
        event(end_event(session_id=session_id)),
    ]


def successful_status_stream(*, session_id=SESSION_ID, status="Complete"):
    return [
        event(available_commands_event(session_id=session_id)),
        event(
            {
                "type": "text",
                "sessionId": session_id,
                "data": "Status: %s | Phase: finalizer" % status,
            }
        ),
        event(end_event(session_id=session_id, request_id="status-request")),
    ]


class FakeProcess:
    def __init__(self, script, *, pid=842_424):
        self.stdin = None
        self.stdout = iter(script.get("stdout", ()))
        self.stderr = iter(script.get("stderr", ()))
        self.pid = pid
        self.returncode = script.get("returncode", 0)
        self.killed = False

    def wait(self, timeout=None):
        return self.returncode

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
        if not self.scripts:
            raise AssertionError("unexpected Grok process launch")
        script = self.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        process = FakeProcess(script)
        self.processes.append(process)
        return process


class FakeVersionRunner:
    def __init__(self, version=PINNED_GROK_NATIVE_RUNTIME_VERSION):
        self.version = version
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"currentVersion": self.version}) + "\n",
            stderr="",
        )


class FakeGitRunner:
    def __init__(self, run_root):
        self.run_root = run_root
        self.initialized = False
        self.calls = []

    def __call__(self, command, **kwargs):
        command = list(command)
        self.calls.append((command, kwargs))
        if "rev-parse" in command:
            if self.initialized:
                return SimpleNamespace(
                    returncode=0,
                    stdout=str(self.run_root) + "\n",
                    stderr="",
                )
            return SimpleNamespace(returncode=128, stdout="", stderr="not a repository")
        if "init" in command:
            (self.run_root / ".git").mkdir(mode=0o700)
            self.initialized = True
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError("unexpected git command: %r" % command)


def inspect_payload(root):
    return {
        "grokVersion": "1.0.5",
        "channel": "unknown",
        "cwd": str(root),
        "projectRoot": str(root) + os.sep,
        "projectTrusted": False,
        "projectInstructions": [
            {
                "fileType": "agents_md",
                "path": str(root / "AGENTS.md"),
                "scope": "project",
            }
        ],
        "permissions": {
            "sources": [],
            "loaded": 0,
            "skipped": [],
            "mcpServerAllowlist": [],
            "marketplaceAllowlist": [],
            "managedSettingsExists": False,
            "managedSettingsActive": False,
        },
        "loginPolicy": {
            "disableApiKeyAuth": False,
            "apiKeyAuthDisabled": False,
            "forceLoginTeamUuid": None,
        },
        "hooks": [],
        "skills": [
            {
                "name": "autonomous-workshop",
                "source": {
                    "type": "project",
                    "path": str(
                        root
                        / ".grok"
                        / "skills"
                        / "autonomous-workshop"
                        / "SKILL.md"
                    ),
                },
                "userInvocable": True,
            }
        ],
        "agents": [
            {
                "name": "general-purpose",
                "source": {"type": "builtin"},
            },
            {
                "name": "peter",
                "source": {
                    "type": "project",
                    "path": str(root / ".grok" / "agents" / "peter.md"),
                },
            }
        ],
        "plugins": [],
        "marketplaces": [],
        "mcpServers": [],
        "lspServers": [],
        "configSources": {
            "layers": [
                {
                    "role": "user",
                    "path": str(root.parent / "state" / "grok-home" / "config.toml"),
                }
            ]
        },
        "externalCompat": {},
        "configWarnings": [],
        "mcpConfigProblems": [],
    }


class FakeInspectRunner:
    def __init__(self, run_root, payloads=None):
        self.run_root = run_root
        self.payloads = list(payloads or ())
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), kwargs))
        payload = self.payloads.pop(0) if self.payloads else inspect_payload(self.run_root)
        if isinstance(payload, BaseException):
            raise payload
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
            stderr="",
        )


class GrokNativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.run_root = self.base / "toy"
        self.run_root.mkdir()
        self.host_state_root = self.base / "state"
        self.host_state_root.mkdir(mode=0o700)
        os.chmod(self.host_state_root, 0o700)
        self._materialize_projection(self.run_root)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _materialize_projection(root):
        (root / PRODUCT_RUN_ROOT_MARKER).write_bytes(PRODUCT_RUN_ROOT_MARKER_BYTES)
        (root / "AGENTS.md").write_text(
            "# Workshop Manager\nRead STAGE.json and finalize one stage.\n",
            encoding="utf-8",
        )
        (root / "MANAGER.json").write_text(
            '{"manager_id":"grok","schema_version":1}\n', encoding="utf-8"
        )
        (root / "WISH.json").write_text(
            '{"kind":"wish","text":"Make a toy"}\n', encoding="utf-8"
        )
        (root / "STAGE.json").write_text(
            '{"stage":"match"}\n', encoding="utf-8"
        )
        agents = root / ".grok" / "agents"
        skill = root / ".grok" / "skills" / "autonomous-workshop"
        agents.mkdir(parents=True)
        skill.mkdir(parents=True)
        (agents / "peter.md").write_text(
            "---\nname: peter\ndescription: Invents toys\n---\nUse exact Taste.\n",
            encoding="utf-8",
        )
        (skill / "SKILL.md").write_text(
            "---\nname: autonomous-workshop\ndescription: Run one stage\n---\n"
            "Finalize the current stage.\n",
            encoding="utf-8",
        )

    def launcher(self, scripts, *, payloads=None, version=None, **overrides):
        factory = FakePopenFactory(scripts)
        version_runner = FakeVersionRunner(
            PINNED_GROK_NATIVE_RUNTIME_VERSION if version is None else version
        )
        inspect_runner = FakeInspectRunner(self.run_root, payloads=payloads)
        git_runner = FakeGitRunner(self.run_root)
        launcher = GrokNativeSessionLauncher(
            binary="/opt/grok",
            popen_factory=factory,
            version_runner=version_runner,
            inspect_runner=inspect_runner,
            git_runner=git_runner,
            uuid_factory=lambda: uuid.UUID(SESSION_ID),
            environment_source=overrides.pop(
                "environment_source",
                {
                    "PATH": "/usr/bin:/bin",
                    "XAI_API_KEY": "xai-test-secret",
                    "FACTORY_API_KEY": "factory-secret",
                    "AWS_SECRET_ACCESS_KEY": "cloud-secret",
                    "HOME": "/ambient/home",
                    "LANG": "C.UTF-8",
                },
            ),
            **overrides,
        )
        return launcher, factory, version_runner, inspect_runner, git_runner

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
            "prompt": INVENT_GOAL,
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

    def test_start_attests_exact_cli_session_policy_environment_and_goal_return(self):
        launcher, factory, version_runner, inspect_runner, git_runner = self.launcher(
            [
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
            ]
        )

        outcome = self.start(launcher)

        self.assertFalse(outcome.used_web_search)
        public = json.dumps(outcome.to_dict(), sort_keys=True)
        self.assertNotIn(SESSION_ID, public)
        self.assertNotIn("xai-test-secret", public)
        self.assertTrue(issubclass(GrokInvocationError, NativeManagerInvocationError))
        self.assertEqual(len(factory.calls), 2)
        primary, primary_kwargs = factory.calls[0]
        status, status_kwargs = factory.calls[1]
        self.assertEqual(primary[0], "/opt/grok")
        self.assertEqual(primary[primary.index("--model") + 1], "grok-build")
        self.assertEqual(
            primary[primary.index("--output-format") + 1], "streaming-json"
        )
        self.assertEqual(
            primary[primary.index("--tools") + 1], ",".join(GROK_ALLOWED_TOOLS)
        )
        self.assertIn("--disable-web-search", primary)
        self.assertNotIn("--verbatim", primary)
        self.assertEqual(primary[primary.index("--session-id") + 1], SESSION_ID)
        self.assertNotIn("--resume", primary)
        self.assertEqual(primary[primary.index("-p") + 1], START_GOAL)
        self.assertNotIn("--session-id", status)
        self.assertEqual(status[status.index("--resume") + 1], SESSION_ID)
        self.assertEqual(status[status.index("-p") + 1], GROK_GOAL_STATUS_PROMPT)
        self.assertEqual(primary_kwargs["cwd"], str(self.run_root))
        self.assertEqual(status_kwargs["cwd"], str(self.run_root))
        if os.name == "posix":
            self.assertIs(primary_kwargs["start_new_session"], True)
        environment = primary_kwargs["env"]
        self.assertEqual(environment["XAI_API_KEY"], "xai-test-secret")
        self.assertEqual(
            environment["HOME"], str(self.host_state_root / "grok-neutral-home")
        )
        self.assertEqual(
            environment["GROK_HOME"], str(self.host_state_root / "grok-home")
        )
        self.assertEqual(environment["GROK_DISABLE_AUTOUPDATER"], "1")
        self.assertNotIn("FACTORY_API_KEY", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        for private_name in (
            "grok-home",
            "grok-neutral-home",
            "grok-policy",
            "grok-tmp",
        ):
            private = self.host_state_root / private_name
            self.assertTrue(private.is_dir())
            self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
        for path in (
            self.host_state_root / "grok-home" / "config.toml",
            self.host_state_root / "grok-home" / "sandbox.toml",
            self.host_state_root / "grok-policy" / "workshop-manager.md",
            self.host_state_root / "grok-session.json",
            self.host_state_root / "grok-goal.json",
        ):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        config = (self.host_state_root / "grok-home" / "config.toml").read_text(
            encoding="utf-8"
        )
        sandbox = (self.host_state_root / "grok-home" / "sandbox.toml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("XAI_API_KEY", config)
        self.assertIn(str(self.host_state_root / "grok-home"), sandbox)
        self.assertIn(str(self.host_state_root / "grok-neutral-home"), sandbox)
        self.assertNotIn("XAI_API_KEY", version_runner.calls[0][1]["env"])
        self.assertNotIn("XAI_API_KEY", inspect_runner.calls[0][1]["env"])
        self.assertNotIn("XAI_API_KEY", git_runner.calls[0][1]["env"])
        self.assertEqual(self.disposition(launcher), "returned")
        self.acknowledge(launcher)
        self.assertEqual(self.disposition(launcher), "completed")
        self.acknowledge(launcher)
        self.assertEqual(self.disposition(launcher), "completed")

    def test_resume_uses_same_session_and_new_goal_after_completed_stage(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)

        self.resume(launcher)

        self.assertEqual(len(factory.calls), 4)
        start_command = factory.calls[0][0]
        resume_command = factory.calls[2][0]
        status_command = factory.calls[3][0]
        self.assertEqual(start_command[start_command.index("--session-id") + 1], SESSION_ID)
        self.assertNotIn("--session-id", resume_command)
        self.assertEqual(resume_command[resume_command.index("--resume") + 1], SESSION_ID)
        self.assertEqual(resume_command[resume_command.index("-p") + 1], INVENT_GOAL)
        self.assertEqual(status_command[status_command.index("--resume") + 1], SESSION_ID)
        self.assertEqual(
            status_command[status_command.index("-p") + 1], GROK_GOAL_STATUS_PROMPT
        )
        goal = json.loads(
            (self.host_state_root / "grok-goal.json").read_text(encoding="utf-8")
        )
        self.assertEqual(goal["status"], "returned")
        self.assertEqual(goal["stage"], "invent")
        self.assertEqual(goal["attempt"], 2)

    def test_interrupted_active_goal_resumes_with_native_goal_resume(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {
                    "stdout": [
                        event(available_commands_event()),
                        event({"type": "text", "data": "Still working"}),
                    ]
                },
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
            ]
        )
        with self.assertRaisesRegex(GrokInvocationError, "did not complete"):
            self.start(launcher)
        self.assertEqual(self.disposition(launcher), "active")

        self.resume(
            launcher,
            prompt=START_GOAL,
            goal_stage="match",
            goal_checkpoint_sha256=MATCH_CHECKPOINT_SHA256,
        )

        continued = factory.calls[1][0]
        self.assertEqual(continued[continued.index("--resume") + 1], SESSION_ID)
        self.assertEqual(
            continued[continued.index("-p") + 1], GROK_GOAL_RESUME_PROMPT
        )
        self.assertEqual(
            factory.calls[2][0][factory.calls[2][0].index("-p") + 1],
            GROK_GOAL_STATUS_PROMPT,
        )
        self.assertEqual(self.disposition(launcher), "returned")
        self.acknowledge(launcher)
        self.assertEqual(self.disposition(launcher), "completed")

    def test_exact_pinned_version_is_required_and_probe_is_scrubbed(self):
        self.assertTrue(grok_supports_native_workshop(PINNED_GROK_NATIVE_RUNTIME_VERSION))
        self.assertFalse(grok_supports_native_workshop("1.0.5"))
        self.assertFalse(grok_supports_native_workshop("1.0.6 (different-build)"))

        with self.assertRaisesRegex(GrokInvocationError, "exact Grok Build"):
            self.launcher([], version="1.0.5")

    def test_wrong_terminal_session_is_rejected_and_goal_stays_active(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {
                    "stdout": [
                        event(available_commands_event()),
                        event(end_event(session_id=OTHER_SESSION_ID)),
                    ]
                }
            ]
        )

        with self.assertRaisesRegex(GrokInvocationError, "different native session"):
            self.start(launcher)

        self.assertEqual(self.disposition(launcher), "active")
        self.assertEqual(len(factory.calls), 1)

    def test_live_tool_roster_must_match_the_host_allowlist_exactly(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {
                    "stdout": successful_primary_stream(
                        tools=list(GROK_ALLOWED_TOOLS[:-1])
                    )
                }
            ]
        )

        with self.assertRaisesRegex(GrokInvocationError, "tool roster"):
            self.start(launcher)

        self.assertEqual(self.disposition(launcher), "active")
        self.assertEqual(len(factory.calls), 1)

    def test_incomplete_goal_status_is_rejected_and_goal_stays_active(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream(status="Active")},
            ]
        )

        with self.assertRaisesRegex(GrokInvocationError, "Complete status"):
            self.start(launcher)

        self.assertEqual(self.disposition(launcher), "active")
        self.assertEqual(len(factory.calls), 2)

    def test_start_spawn_failure_rolls_back_unsubmitted_checkpoints(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [OSError("exec failed")]
        )

        with self.assertRaisesRegex(GrokInvocationError, "could not be launched"):
            self.start(launcher)

        self.assertFalse((self.host_state_root / "grok-session.json").exists())
        self.assertFalse((self.host_state_root / "grok-goal.json").exists())
        self.assertEqual(len(factory.calls), 1)

    def test_tampered_private_policy_is_rejected_before_resume(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
            ]
        )
        self.start(launcher)
        self.acknowledge(launcher)
        policy = self.host_state_root / "grok-policy" / "workshop-manager.md"
        policy.write_text(policy.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

        with self.assertRaisesRegex(ContractError, "differs from its host projection"):
            self.resume(launcher)

        self.assertEqual(len(factory.calls), 2)

    def test_inspect_forbidden_runtime_surface_is_rejected_before_launch(self):
        payload = inspect_payload(self.run_root)
        payload["mcpServers"] = [{"name": "ambient", "status": "connected"}]
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [], payloads=[payload]
        )

        with self.assertRaisesRegex(GrokInvocationError, "forbidden mcpServers"):
            self.start(launcher)

        self.assertEqual(factory.calls, [])
        self.assertFalse((self.host_state_root / "grok-session.json").exists())

    def test_inspect_rejects_ambient_configuration_sources(self):
        payload = inspect_payload(self.run_root)
        payload["configSources"] = [
            {"scope": "user", "path": "/ambient/home/.grok/config.toml"}
        ]
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [], payloads=[payload]
        )

        with self.assertRaises(GrokInvocationError):
            self.start(launcher)

        self.assertEqual(factory.calls, [])

    def test_inspect_rejects_project_assets_outside_the_private_run(self):
        payload = inspect_payload(self.run_root)
        payload["skills"][0]["source"]["path"] = "/ambient/alice/SKILL.md"
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [], payloads=[payload]
        )

        with self.assertRaisesRegex(GrokInvocationError, "unexpected project skills"):
            self.start(launcher)

        self.assertEqual(factory.calls, [])

    def test_root_immutable_files_receive_exact_file_denies(self):
        launcher, factory, unused_version, unused_inspect, unused_git = self.launcher(
            [
                {"stdout": successful_primary_stream()},
                {"stdout": successful_status_stream()},
            ]
        )

        self.start(launcher)

        command = factory.calls[0][0]
        deny_values = [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "--deny"
        ]
        for path in (
            PRODUCT_RUN_ROOT_MARKER,
            "AGENTS.md",
            "MANAGER.json",
            "STAGE.json",
            "WISH.json",
        ):
            self.assertIn("Edit(%s)" % path, deny_values)
        self.assertIn("Edit(.grok/**)", deny_values)
        self.assertIn("Edit(.git/**)", deny_values)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
