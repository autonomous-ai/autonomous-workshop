import json
import os
import stat
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError
from workshop.runtime.codex import (
    CODEX_PERMISSION_PROFILE,
    MAX_CODEX_EVENT_BYTES,
    MAX_CODEX_MESSAGE_BYTES,
    MAX_CODEX_STDERR_BYTES,
    CodexInvocationError,
    CodexNativeSessionLauncher,
)


THREAD_ID = "12345678-1234-5678-9234-567812345678"
WISH_SHA256 = "a" * 64
CONSTITUTION_SHA256 = "b" * 64
PERMISSION_ARGUMENTS = (
    "--config",
    'default_permissions="workshop-product-run"',
    "--config",
    'permissions.workshop-product-run.description="Isolated Autonomous Workshop product run"',
    "--config",
    'permissions.workshop-product-run.extends=":workspace"',
    "--config",
    'permissions.workshop-product-run.filesystem={":root"="deny",'
    '":minimal"="read",glob_scan_max_depth=8,":workspace_roots"='
    '{"."="write","**/.env*"="deny"}}',
    "--config",
    "permissions.workshop-product-run.network.enabled=false",
)


def event(value):
    return json.dumps(value, sort_keys=True) + "\n"


class RecordingInput:
    def __init__(self):
        self.value = ""
        self.closed = False

    def write(self, value):
        self.value += value
        return len(value)

    def flush(self):
        return None

    def close(self):
        self.closed = True


class ScriptedStream:
    def __init__(self, values, callbacks=None, stop_event=None):
        self.values = list(values)
        self.callbacks = dict(callbacks or {})
        self.stop_event = stop_event

    def __iter__(self):
        if self.stop_event is not None:
            self.stop_event.wait(timeout=2)
            return
        for index, value in enumerate(self.values):
            callback = self.callbacks.get(index)
            if callback is not None:
                callback()
            yield value


class FakeProcess:
    def __init__(self, script):
        self.script = dict(script)
        self.stdin = RecordingInput()
        self._stopped = threading.Event()
        self.stdout = ScriptedStream(
            self.script.get("stdout", ()),
            callbacks=self.script.get("stdout_callbacks"),
            stop_event=self._stopped if self.script.get("block_stdout") else None,
        )
        self.stderr = ScriptedStream(self.script.get("stderr", ()))
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        del timeout
        if self.returncode is None:
            self.returncode = self.script.get("returncode", 0)
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15
        self._stopped.set()

    def kill(self):
        self.killed = True
        self.returncode = -9
        self._stopped.set()


class FakePopenFactory:
    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.calls = []
        self.processes = []

    def __call__(self, command, **kwargs):
        process = FakeProcess(self.scripts.pop(0))
        self.calls.append((tuple(command), dict(kwargs)))
        self.processes.append(process)
        return process


class ImmediateTimer:
    def __init__(self, unused_interval, callback):
        self.callback = callback
        self.daemon = False

    def start(self):
        self.callback()

    def cancel(self):
        return None


class CodexNativeSessionTest(unittest.TestCase):
    def launcher(self, scripts, *, model="gpt-5.6-terra", effort="high"):
        factory = FakePopenFactory(scripts)
        return (
            CodexNativeSessionLauncher(
                model=model,
                reasoning_effort=effort,
                binary="/fixture/codex",
                timeout_seconds=30,
                popen_factory=factory,
                cli_version="0.145.0",
            ),
            factory,
        )

    @staticmethod
    def start_events(*, message="complete", search=True):
        values = [event({"type": "thread.started", "thread_id": THREAD_ID})]
        if search:
            values.append(
                event(
                    {
                        "type": "item.completed",
                        "item": {"id": "search-1", "type": "web_search"},
                    }
                )
            )
        values.append(
            event(
                {
                    "type": "item.completed",
                    "item": {"id": "message-1", "type": "agent_message", "text": message},
                }
            )
        )
        return values

    @staticmethod
    def host_state(root, *, name=None):
        state = root.parent / (name or (root.name + "-host-state"))
        state.mkdir(mode=0o700, exist_ok=True)
        os.chmod(state, 0o700)
        return state

    def start(
        self,
        launcher,
        root,
        *,
        host_state_root=None,
        prompt="run this exact Wish",
    ):
        return launcher.start(
            product_id="wish-001",
            wish_sha256=WISH_SHA256,
            constitution_sha256=CONSTITUTION_SHA256,
            run_root=root,
            host_state_root=host_state_root or self.host_state(root),
            prompt=prompt,
        )

    def resume(self, launcher, root, **overrides):
        values = {
            "product_id": "wish-001",
            "wish_sha256": WISH_SHA256,
            "constitution_sha256": CONSTITUTION_SHA256,
            "run_root": root,
            "host_state_root": self.host_state(root),
            "prompt": "continue from durable evidence",
        }
        values.update(overrides)
        return launcher.resume(**values)

    def test_start_streams_exact_native_command_and_checkpoints_before_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            state_root = self.host_state(root)
            checkpoint = state_root / "codex-session.json"
            observations = []

            def observe_early_checkpoint():
                observations.append(
                    (
                        checkpoint.is_file(),
                        stat.S_IMODE(checkpoint.stat().st_mode),
                    )
                )

            script = {
                "stdout": self.start_events(
                    message="run this exact Wish FACTORY_PASSWORD=secret"
                ),
                # This callback runs immediately before the second event is
                # yielded, after thread.started has been processed.
                "stdout_callbacks": {1: observe_early_checkpoint},
            }
            launcher, factory = self.launcher([script])
            parent_environment = {
                "PATH": "/fixture/bin",
                "HOME": "/fixture/home",
                "CODEX_HOME": "/fixture/codex-home",
                "OPENAI_API_KEY": "codex-auth",
                "FACTORY_PASSWORD": "must-not-reach-codex",
                "FACTORY_USERNAME": "must-not-reach-codex",
            }
            with mock.patch.dict(os.environ, parent_environment, clear=True):
                outcome = self.start(
                    launcher, root, host_state_root=state_root
                )

            self.assertEqual(observations, [(True, 0o600)])
            command, call = factory.calls[0]
            self.assertEqual(
                command,
                (
                    "/fixture/codex",
                    "--search",
                    "--ask-for-approval",
                    "never",
                    "exec",
                    "--ignore-user-config",
                    "--skip-git-repo-check",
                    "--strict-config",
                    "--color",
                    "never",
                    "--json",
                    "--config",
                    'model_reasoning_effort="high"',
                    *PERMISSION_ARGUMENTS,
                    "-C",
                    str(root),
                    "--model",
                    "gpt-5.6-terra",
                    "-",
                ),
            )
            for forbidden in (
                "--ephemeral",
                "--output-schema",
                "--ignore-rules",
                "danger-full-access",
                "--sandbox",
                "--dangerously-bypass-approvals-and-sandbox",
            ):
                self.assertNotIn(forbidden, command)
            self.assertNotIn("run this exact Wish", command)
            self.assertEqual(factory.processes[0].stdin.value, "run this exact Wish")
            self.assertEqual(call["cwd"], str(root))
            self.assertNotIn(str(state_root), command)
            self.assertEqual(call["env"]["OPENAI_API_KEY"], "codex-auth")
            self.assertNotIn("FACTORY_PASSWORD", call["env"])
            self.assertNotIn("FACTORY_USERNAME", call["env"])
            self.assertTrue(outcome.used_web_search)
            public = json.dumps(outcome.to_dict(), sort_keys=True)
            self.assertNotIn(THREAD_ID, public)
            self.assertNotIn("run this exact Wish", public)
            self.assertNotIn("FACTORY_PASSWORD", public)
            self.assertNotIn(str(state_root), public)
            self.assertNotIn("message", outcome.to_dict())
            private = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(private["thread_id"], THREAD_ID)
            self.assertEqual(private["wish_sha256"], WISH_SHA256)
            self.assertEqual(
                private["constitution_sha256"], CONSTITUTION_SHA256
            )

    def test_resume_uses_the_exact_private_thread_and_redacts_it_publicly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {
                        "stdout": [
                            event(
                                {
                                    "type": "thread.started",
                                    "thread_id": THREAD_ID,
                                }
                            ),
                            event(
                                {
                                    "type": "item.completed",
                                    "item": {
                                        "id": "message-2",
                                        "type": "agent_message",
                                        "text": "resumed",
                                    },
                                }
                            ),
                        ]
                    },
                ]
            )
            started = self.start(launcher, root)
            resumed = self.resume(launcher, root)

            command = factory.calls[1][0]
            self.assertEqual(
                command,
                (
                    "/fixture/codex",
                    "--search",
                    "--ask-for-approval",
                    "never",
                    "-C",
                    str(root),
                    "exec",
                    "resume",
                    "--ignore-user-config",
                    "--skip-git-repo-check",
                    "--strict-config",
                    "--json",
                    "--config",
                    'model_reasoning_effort="high"',
                    *PERMISSION_ARGUMENTS,
                    "--model",
                    "gpt-5.6-terra",
                    THREAD_ID,
                    "-",
                ),
            )
            self.assertNotIn("--ephemeral", command)
            self.assertNotIn("--sandbox", command)
            self.assertEqual(private_profile := json.loads(
                (self.host_state(root) / "codex-session.json").read_text(encoding="utf-8")
            )["permission_profile"], CODEX_PERMISSION_PROFILE)
            self.assertEqual(private_profile, "workshop-product-run")
            self.assertEqual(resumed.status, "completed")
            self.assertEqual(
                resumed.binding.checkpoint_sha256,
                started.binding.checkpoint_sha256,
            )
            self.assertNotIn(THREAD_ID, json.dumps(resumed.to_dict()))

    def test_resume_rejects_wrong_or_tampered_bindings_without_launching(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher([{"stdout": self.start_events()}])
            self.start(launcher, root)
            call_count = len(factory.calls)

            for field, value in (
                ("wish_sha256", "c" * 64),
                ("constitution_sha256", "d" * 64),
            ):
                with self.subTest(field=field), self.assertRaisesRegex(
                    ContractError, "binding is invalid"
                ):
                    self.resume(launcher, root, **{field: value})
            self.assertEqual(len(factory.calls), call_count)

            checkpoint = self.host_state(root) / "codex-session.json"
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            payload["product_id"] = "wish-tampered"
            checkpoint.write_text(json.dumps(payload), encoding="utf-8")
            os.chmod(checkpoint, 0o600)
            with self.assertRaisesRegex(ContractError, "binding is invalid"):
                self.resume(launcher, root)
            self.assertEqual(len(factory.calls), call_count)

    def test_resume_rejects_symlink_and_copied_checkpoint_for_wrong_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            root = container / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            self.start(launcher, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            source = checkpoint.read_bytes()

            real = checkpoint.parent / "real-session.json"
            checkpoint.rename(real)
            checkpoint.symlink_to(real)
            with self.assertRaisesRegex(ContractError, "regular private file"):
                self.resume(launcher, root)

            other = container / "other-run"
            other.mkdir()
            other_state = self.host_state(other)
            copied = other_state / "codex-session.json"
            copied.write_bytes(source)
            os.chmod(copied, 0o600)
            with self.assertRaisesRegex(ContractError, "binding is invalid"):
                self.resume(launcher, other)

            alternate_state = self.host_state(root, name="alternate-host-state")
            alternate_checkpoint = alternate_state / "codex-session.json"
            alternate_checkpoint.write_bytes(source)
            os.chmod(alternate_checkpoint, 0o600)
            with self.assertRaisesRegex(ContractError, "binding is invalid"):
                self.resume(
                    launcher, root, host_state_root=alternate_state
                )

    def test_rejects_overlapping_or_unsafe_host_state_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            root = container / "run"
            root.mkdir()
            launcher, factory = self.launcher([])

            nested = root / "host-state"
            nested.mkdir(mode=0o700)
            with self.assertRaisesRegex(ContractError, "must not overlap"):
                self.start(launcher, root, host_state_root=nested)

            broader = container / "broader"
            broader.mkdir(mode=0o700)
            nested_run = broader / "run"
            nested_run.mkdir()
            with self.assertRaisesRegex(ContractError, "must not overlap"):
                self.start(launcher, nested_run, host_state_root=broader)

            real_state = self.host_state(root, name="real-host-state")
            linked_state = container / "linked-host-state"
            linked_state.symlink_to(real_state, target_is_directory=True)
            with self.assertRaisesRegex(ContractError, "must not be a symlink"):
                self.start(launcher, root, host_state_root=linked_state)

            unsafe_state = self.host_state(root, name="unsafe-host-state")
            os.chmod(unsafe_state, 0o755)
            with self.assertRaisesRegex(ContractError, "permissions must be 0700"):
                self.start(launcher, root, host_state_root=unsafe_state)

            self.assertEqual(factory.calls, [])

    def test_resume_rejects_missing_checkpoint_and_changed_runtime_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            missing = container / "missing"
            missing.mkdir()
            launcher, unused_factory = self.launcher([])
            with self.assertRaisesRegex(ContractError, "checkpoint is missing"):
                self.resume(launcher, missing)

            root = container / "run"
            root.mkdir()
            starter, unused_starter_factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            self.start(starter, root)
            changed, changed_factory = self.launcher(
                [], model="gpt-5.6-luna", effort="low"
            )
            with self.assertRaisesRegex(ContractError, "binding is invalid"):
                self.resume(changed, root)
            self.assertEqual(changed_factory.calls, [])

    def test_rejects_codex_versions_without_permission_profiles(self):
        with self.assertRaisesRegex(
            CodexInvocationError, "0.138.0 or newer"
        ):
            CodexNativeSessionLauncher(
                binary="/fixture/codex",
                cli_version="0.137.9",
            )

    def test_bounds_timeout_and_failures_are_terminated_and_redacted(self):
        secret = "FACTORY_PASSWORD=never-show-this"
        cases = (
            (
                {"stdout": ["x" * (MAX_CODEX_EVENT_BYTES + 1)]},
                "event stream",
            ),
            (
                {
                    "stdout": self.start_events(),
                    "stderr": ["x" * (MAX_CODEX_STDERR_BYTES + 1)],
                },
                "diagnostic stream",
            ),
            (
                {
                    "stdout": [
                        event(
                            {"type": "thread.started", "thread_id": THREAD_ID}
                        ),
                        event(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "message-large",
                                    "type": "agent_message",
                                    "text": "m" * (MAX_CODEX_MESSAGE_BYTES + 1),
                                },
                            }
                        ),
                    ]
                },
                "message exceeded",
            ),
            (
                {
                    "stdout": [
                        event(
                            {"type": "thread.started", "thread_id": THREAD_ID}
                        )
                    ],
                    "stderr": [secret],
                    "returncode": 1,
                },
                "did not complete",
            ),
        )
        for script, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve() / "run"
                root.mkdir()
                launcher, factory = self.launcher([script])
                with self.assertRaisesRegex((CodexInvocationError, ContractError), message) as caught:
                    self.start(launcher, root, prompt="private prompt sentinel")
                rendered = str(caught.exception)
                self.assertNotIn(THREAD_ID, rendered)
                self.assertNotIn("private prompt sentinel", rendered)
                self.assertNotIn("FACTORY_PASSWORD", rendered)
                self.assertTrue(
                    factory.processes[0].terminated
                    or factory.processes[0].returncode is not None
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher([{"block_stdout": True}])
            with mock.patch(
                "workshop.runtime.codex.threading.Timer", ImmediateTimer
            ), self.assertRaisesRegex(CodexInvocationError, "timed out"):
                self.start(launcher, root, prompt="private prompt sentinel")
            self.assertTrue(factory.processes[0].terminated)


if __name__ == "__main__":
    unittest.main()
