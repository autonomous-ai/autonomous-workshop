import json
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.grok import (
    GrokNativeSessionLauncher,
    grok_subprocess_environment,
    grok_supports_native_workshop,
)


DIGEST = "a" * 64


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


class GrokNativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        self.run_root = root / "run"
        self.host_state = root / "state"
        self.run_root.mkdir(mode=0o700)
        self.host_state.mkdir(mode=0o700)

    def test_version_pin(self):
        self.assertTrue(grok_supports_native_workshop("1.0.5 (5115b46bc909)"))
        self.assertFalse(grok_supports_native_workshop("1.0.4"))

    def test_environment_drops_factory_credentials(self):
        environment = grok_subprocess_environment(
            {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "FACTORY_PASSWORD": "secret",
                "FACTORY_USERNAME": "svc",
            }
        )
        self.assertEqual(environment["HOME"], "/tmp/home")
        self.assertNotIn("FACTORY_PASSWORD", environment)
        self.assertNotIn("FACTORY_USERNAME", environment)

    def test_start_writes_session_checkpoint_and_classifies_activity(self):
        observed = []

        def popen(command, **kwargs):
            self.assertEqual(command[0], "/bin/grok")
            self.assertIn("--session-id", command)
            self.assertIn("-p", command)
            self.assertIn("--always-approve", command)
            self.assertIn("grok-4.6", command)
            self.assertEqual(kwargs["cwd"], str(self.run_root))
            self.assertNotIn("FACTORY_PASSWORD", kwargs["env"])
            self.assertIn("WORKSHOP_PYTHON", kwargs["env"])
            return _FakeProcess(
                [
                    json.dumps({"type": "thinking"}) + "\n",
                    json.dumps({"type": "tool_call"}) + "\n",
                ]
            )

        launcher = GrokNativeSessionLauncher(
            binary="/bin/grok",
            cli_version="1.0.5 (5115b46bc909)",
            popen_factory=popen,
            uuid_factory=lambda: "123e4567-e89b-12d3-a456-426614174000",
        )
        outcome = launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="Create one native Codex goal for the current invent stage.",
            activity_observer=observed.append,
        )
        checkpoint = self.host_state / "grok-session.json"
        self.assertTrue(checkpoint.is_file())
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(payload["session_id"], "123e4567-e89b-12d3-a456-426614174000")
        self.assertEqual(outcome.session_id, payload["session_id"])
        self.assertIn("reasoning", observed)
        self.assertIn("tool", observed)
        self.assertEqual(observed[0], "starting")
        self.assertEqual(observed[-1], "completed")

    def test_resume_uses_the_frozen_session_id(self):
        seen = {}

        def popen(command, **kwargs):
            seen["command"] = command
            return _FakeProcess([json.dumps({"type": "agent_message"}) + "\n"])

        launcher = GrokNativeSessionLauncher(
            binary="/bin/grok",
            cli_version="1.0.5",
            popen_factory=popen,
            uuid_factory=lambda: "123e4567-e89b-12d3-a456-426614174000",
        )
        started = launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="invent",
        )
        resumed = launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(resumed.session_id, started.session_id)
        self.assertIn("--resume", seen["command"])
        self.assertIn(started.session_id, seen["command"])

    def test_clean_exit_without_finalizer_is_recoverable(self):
        from workshop.runtime.grok import GrokRecoverableInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess([json.dumps({"type": "thinking"}) + "\n"])

        launcher = GrokNativeSessionLauncher(
            binary="/bin/grok",
            cli_version="1.0.5",
            popen_factory=popen,
            uuid_factory=lambda: "123e4567-e89b-12d3-a456-426614174000",
        )
        marker = self.run_root / "agent-outcome.json"
        with self.assertRaises(GrokRecoverableInvocationError):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
                finalization_marker=marker,
            )
        self.assertTrue((self.host_state / "grok-session.json").is_file())
