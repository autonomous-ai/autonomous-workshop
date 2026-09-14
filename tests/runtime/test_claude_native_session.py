import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.managers import MAX_NATIVE_TURN_SECONDS
from workshop.runtime.claude import (
    DEFAULT_CLAUDE_TIMEOUT_SECONDS,
    ClaudeNativeSessionLauncher,
    claude_subprocess_environment,
    claude_supports_native_workshop,
)


DIGEST = "b" * 64


class _FakeStdout:
    def __init__(self, lines):
        self._lines = list(lines)

    def __iter__(self):
        return iter(self._lines)


class _FakeProcess:
    def __init__(self, lines, returncode=0):
        self.stdout = _FakeStdout(lines)
        self.stderr = _FakeStdout([])
        self.returncode = returncode

    def wait(self, timeout=None):
        del timeout
        return self.returncode

    def kill(self):
        self.returncode = -9


class ClaudeNativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        self.run_root = root / "run"
        self.host_state = root / "state"
        self.run_root.mkdir(mode=0o700)
        self.host_state.mkdir(mode=0o700)

    def test_version_pin(self):
        self.assertTrue(claude_supports_native_workshop("2.1.0"))
        self.assertFalse(claude_supports_native_workshop("1.9.0"))

    def test_environment_drops_factory_credentials(self):
        environment = claude_subprocess_environment(
            {"PATH": "/usr/bin", "HOME": "/tmp/home", "FACTORY_PASSWORD": "secret"}
        )
        self.assertNotIn("FACTORY_PASSWORD", environment)

    def test_turn_boundary_accepts_a_longer_turn_and_an_untimed_one(self):
        """Only an explicit request may exceed the historical one-hour default."""

        self.assertEqual(DEFAULT_CLAUDE_TIMEOUT_SECONDS, 3_600)
        default = ClaudeNativeSessionLauncher(
            binary="/bin/claude", cli_version="2.0.0"
        )
        self.assertEqual(default.timeout_seconds, 3_600)
        longer = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            timeout_seconds=MAX_NATIVE_TURN_SECONDS,
        )
        self.assertEqual(longer.timeout_seconds, MAX_NATIVE_TURN_SECONDS)
        untimed = ClaudeNativeSessionLauncher(
            binary="/bin/claude", cli_version="2.0.0", timeout_seconds=None
        )
        self.assertIsNone(untimed.timeout_seconds)
        for invalid in (MAX_NATIVE_TURN_SECONDS + 1, 0, -1, 60.0, "3600"):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                ValueError, "1 to %d or None" % MAX_NATIVE_TURN_SECONDS
            ):
                ClaudeNativeSessionLauncher(
                    binary="/bin/claude",
                    cli_version="2.0.0",
                    timeout_seconds=invalid,
                )

    def test_an_untimed_turn_never_arms_a_process_deadline(self):
        """An untimed launcher must wait without a timeout, not with a huge one."""

        waits = []

        class _RecordingProcess(_FakeProcess):
            def wait(self, timeout=None):
                waits.append(timeout)
                return self.returncode

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            timeout_seconds=None,
            popen_factory=lambda command, **kwargs: _RecordingProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-untimed",
                        }
                    )
                    + "\n",
                ]
            ),
            uuid_factory=lambda: "initial-session-id",
        )
        launcher.start(
            product_id="wish-untimed",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(waits, [None])

    def test_start_and_resume_preserve_session_identity(self):
        seen = {}

        def popen(command, **kwargs):
            seen.setdefault("commands", []).append(command)
            self.assertEqual(kwargs["cwd"], str(self.run_root))
            self.assertIn("WORKSHOP_PYTHON", kwargs["env"])
            self.assertNotIn("FACTORY_PASSWORD", kwargs["env"])
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                    json.dumps({"type": "tool_use"}) + "\n",
                ]
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        started = launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="invent",
        )
        self.assertEqual(started.session_id, "claude-session-one")
        resumed = launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(resumed.session_id, "claude-session-one")
        self.assertIn("--print", seen["commands"][0])
        self.assertIn("--verbose", seen["commands"][0])
        self.assertIn("acceptEdits", seen["commands"][0])
        self.assertIn("--resume", seen["commands"][1])
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["session_id"], "claude-session-one")

    def test_selected_opus_model_and_effort_are_bound_and_reused(self):
        commands = []

        def popen(command, **kwargs):
            del kwargs
            commands.append(command)
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n"
                ]
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            model="claude-opus-5",
            reasoning_effort="high",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="invent",
        )
        launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        for command in commands:
            self.assertIn("--model", command)
            self.assertEqual(command[command.index("--model") + 1], "claude-opus-5")
            self.assertIn("--effort", command)
            self.assertEqual(command[command.index("--effort") + 1], "high")
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["model"], "claude-opus-5")
        self.assertEqual(payload["reasoning_effort"], "high")

        changed = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            model="claude-sonnet-5",
            reasoning_effort="high",
            popen_factory=popen,
        )
        with self.assertRaisesRegex(ContractError, "runtime binding"):
            changed.resume(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )
        self.assertEqual(len(commands), 2)

    def test_every_supported_effort_reaches_claude_command(self):
        observed = 0
        for effort in ("low", "medium", "high", "xhigh"):
            observed += 1
            with self.subTest(effort=effort):
                launcher = ClaudeNativeSessionLauncher(
                    binary="/bin/claude",
                    cli_version="2.0.0",
                    model="claude-opus-5",
                    reasoning_effort=effort,
                )
                command = launcher._command(
                    self.run_root, "invent", session_id=None
                )
                self.assertEqual(
                    command[command.index("--model") + 1], "claude-opus-5"
                )
                self.assertEqual(command[command.index("--effort") + 1], effort)
        self.assertEqual(observed, 4)

    def test_clean_exit_without_finalizer_is_recoverable(self):
        from workshop.runtime.claude import ClaudeRecoverableInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess([json.dumps({"type": "assistant"}) + "\n"])

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        marker = self.run_root / "agent-outcome.json"
        with self.assertRaises(ClaudeRecoverableInvocationError):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
                finalization_marker=marker,
            )

    def test_rate_limit_is_a_hard_session_failure(self):
        from workshop.runtime.claude import ClaudeInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "rate_limit_event",
                            "rate_limit_info": {"status": "rejected"},
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                    json.dumps({"is_error": True, "session_id": "claude-session-one"})
                    + "\n",
                ],
                returncode=1,
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "weekly limit"):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )
