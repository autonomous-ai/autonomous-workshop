import json
import os
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import tomllib
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import workshop.runtime.codex as codex_runtime
from workshop.errors import ContractError
from workshop.runtime.codex import (
    CODEX_PERMISSION_PROFILE,
    DEFAULT_CODEX_TIMEOUT_SECONDS,
    MAX_CODEX_EVENT_BYTES,
    MAX_CODEX_MESSAGE_BYTES,
    MAX_CODEX_STDERR_BYTES,
    MINIMUM_CODEX_NATIVE_RUNTIME_VERSION,
    CodexFinalizedWithoutTerminalError,
    CodexInvocationError,
    CodexRecoverableInvocationError,
    CodexNativeSessionLauncher,
    codex_supports_native_workshop,
)


THREAD_ID = "12345678-1234-5678-9234-567812345678"
OTHER_THREAD_ID = "87654321-4321-6789-8234-567812345678"
WISH_SHA256 = "a" * 64
CONSTITUTION_SHA256 = "b" * 64
ROOT_MARKER = ".workshop-product-run-root"
TEST_CODEX_BINARY = str(Path("/bin/sh").resolve(strict=True))


def permission_arguments(root, binary=TEST_CODEX_BINARY):
    immutable = (
        ".agents",
        ".codex",
        ROOT_MARKER,
        "AGENTS.md",
        "STAGE.json",
        "VAULT.json",
        "WISH.json",
    )
    workspace_entries = [
        '"."="write"',
        *("%s=\"read\"" % json.dumps(relative) for relative in immutable),
        "%s=\"deny\"" % json.dumps("**/.env*"),
    ]
    executable = Path(sys.executable)
    resolved = executable.resolve(strict=True)
    runtime_paths = {executable, resolved}
    for name in (
        "python",
        "python3",
        "python%d.%d" % (sys.version_info.major, sys.version_info.minor),
    ):
        candidate = executable.parent / name
        try:
            if candidate.resolve(strict=True) == resolved:
                runtime_paths.add(candidate)
        except OSError:
            pass
    marker = executable.parent.parent / "pyvenv.cfg"
    if marker.is_file() and not marker.is_symlink():
        runtime_paths.add(executable.parent)
        runtime_paths.add(marker)
    for key in ("stdlib", "platstdlib", "purelib", "platlib"):
        value = sysconfig.get_path(key)
        if value:
            candidate = Path(value).resolve(strict=True)
            if candidate.is_dir():
                runtime_paths.add(candidate)
    library_dir = sysconfig.get_config_var("LIBDIR")
    library_name = sysconfig.get_config_var(
        "INSTSONAME"
    ) or sysconfig.get_config_var("LDLIBRARY")
    if library_dir and library_name:
        shared_library = Path(library_dir) / library_name
        try:
            resolved_library = shared_library.resolve(strict=True)
        except OSError:
            resolved_library = None
        if resolved_library is not None and resolved_library.is_file():
            runtime_paths.add(resolved_library)
    runtime_paths.add(Path(binary).resolve(strict=True))
    entries = [
        '":root"="deny"',
        '":minimal"="read"',
        "glob_scan_max_depth=8",
        '":workspace_roots"={%s}' % ",".join(workspace_entries),
        "%s=\"deny\"" % json.dumps(str(root.parent)),
        "%s=\"write\"" % json.dumps(str(root)),
    ]
    entries.extend(
        "%s=\"read\"" % json.dumps(str(path))
        for path in sorted(runtime_paths, key=lambda path: str(path))
    )
    entries.extend(
        "%s=\"read\"" % json.dumps(str(root / relative))
        for relative in immutable
    )
    entries.append(
        "%s=\"deny\"" % json.dumps(str(root / "**/.env*"))
    )
    return (
        "--config",
        'default_permissions="workshop-product-run"',
        "--config",
        'permissions.workshop-product-run.description="Isolated Autonomous Workshop product run"',
        "--config",
        "permissions.workshop-product-run.workspace_roots={%s=true}"
        % json.dumps(str(root)),
        "--config",
        "permissions.workshop-product-run.filesystem={%s}" % ",".join(entries),
        "--config",
        "permissions.workshop-product-run.network.enabled=false",
        "--config",
        'project_root_markers=[".workshop-product-run-root"]',
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
    def __init__(
        self,
        values,
        callbacks=None,
        stop_event=None,
        start_event=None,
        block_before_values=False,
        block_after_values=False,
        block_timeout=2.0,
    ):
        self.values = list(values)
        self.callbacks = dict(callbacks or {})
        self.stop_event = stop_event
        self.start_event = start_event
        self.block_before_values = block_before_values
        self.block_after_values = block_after_values
        self.block_timeout = block_timeout
        self._index = 0
        self._remainder = None
        self._started = False
        self.closed = False

    def close(self):
        self.closed = True

    def __iter__(self):
        while True:
            value = self.readline()
            if value in ("", b""):
                return
            yield value

    def readline(self, size=-1):
        if not self._started:
            self._started = True
            if self.start_event is not None:
                self.start_event.wait(timeout=2)
            if self.block_before_values and self.stop_event is not None:
                self.stop_event.wait(timeout=self.block_timeout)
                return ""
        if self._remainder is None:
            if self._index >= len(self.values):
                if self.block_after_values and self.stop_event is not None:
                    self.stop_event.wait(timeout=self.block_timeout)
                return ""
            callback = self.callbacks.get(self._index)
            if callback is not None:
                callback()
            self._remainder = self.values[self._index]
            self._index += 1
        value = self._remainder
        if size is not None and size >= 0 and len(value) > size:
            self._remainder = value[size:]
            return value[:size]
        self._remainder = None
        return value


class FakeProcess:
    def __init__(self, script):
        self.script = dict(script)
        self.stdin = RecordingInput()
        self._stopped = threading.Event()
        self.stdout = ScriptedStream(
            self.script.get("stdout", ()),
            callbacks=self.script.get("stdout_callbacks"),
            stop_event=(
                self._stopped
                if self.script.get("block_stdout")
                or self.script.get("block_stdout_after_values")
                else None
            ),
            start_event=self.script.get("stdout_start_event"),
            block_before_values=self.script.get("block_stdout", False),
            block_after_values=self.script.get("block_stdout_after_values", False),
            block_timeout=self.script.get("stdout_block_timeout", 2.0),
        )
        self.stderr = ScriptedStream(self.script.get("stderr", ()))
        self.returncode = None
        self.terminated = False
        self.killed = False
        self.wait_timeouts = []

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.wait_timeouts.append(timeout)
        if self.script.get("ignore_termination"):
            raise subprocess.TimeoutExpired("/fixture/codex", timeout)
        if (
            self.script.get("hang_until_terminated")
            and not self._stopped.is_set()
            and self.returncode is None
        ):
            raise subprocess.TimeoutExpired("/fixture/codex", timeout)
        if self.returncode is None:
            self.returncode = self.script.get("returncode", 0)
        return self.returncode

    def terminate(self):
        self.terminated = True
        if self.script.get("ignore_termination"):
            return
        self.returncode = -15
        self._stopped.set()

    def kill(self):
        self.killed = True
        if self.script.get("ignore_termination"):
            return
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
    def launcher(
        self,
        scripts,
        *,
        model="gpt-5.6-sol",
        effort="high",
        binary=TEST_CODEX_BINARY,
        timeout_seconds=30,
    ):
        factory = FakePopenFactory(scripts)
        return (
            CodexNativeSessionLauncher(
                model=model,
                reasoning_effort=effort,
                binary=binary,
                timeout_seconds=timeout_seconds,
                popen_factory=factory,
                cli_version="0.145.0",
            ),
            factory,
        )

    @staticmethod
    def start_events(*, message="complete", search=True, terminal=True):
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
        if terminal:
            values.append(event({"type": "turn.completed", "usage": {}}))
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
        activity_observer=None,
        finalization_marker=None,
    ):
        return launcher.start(
            product_id="wish-001",
            wish_sha256=WISH_SHA256,
            constitution_sha256=CONSTITUTION_SHA256,
            run_root=root,
            host_state_root=host_state_root or self.host_state(root),
            prompt=prompt,
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
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
                    TEST_CODEX_BINARY,
                    "--search",
                    "--enable",
                    "goals",
                    "--enable",
                    "multi_agent",
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
                    *permission_arguments(root),
                    "-C",
                    str(root),
                    "--model",
                    "gpt-5.6-sol",
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
            self.assertIs(call["start_new_session"], True)
            self.assertEqual(call["encoding"], "utf-8")
            self.assertEqual(call["errors"], "strict")
            self.assertEqual(call["env"]["TMPDIR"], str(root / ".tmp"))
            self.assertEqual(call["env"]["TMP"], str(root / ".tmp"))
            self.assertEqual(call["env"]["TEMP"], str(root / ".tmp"))
            self.assertEqual(call["env"]["PYTHONHASHSEED"], "0")
            self.assertEqual(call["env"]["PYTHONDONTWRITEBYTECODE"], "1")
            self.assertEqual(call["env"]["PYTHONNOUSERSITE"], "1")
            self.assertEqual(
                call["env"]["WORKSHOP_PYTHON"],
                str(Path(sys.executable).absolute()),
            )
            self.assertEqual(stat.S_IMODE((root / ".tmp").stat().st_mode), 0o700)
            self.assertNotIn(str(state_root), command)
            self.assertEqual(call["env"]["OPENAI_API_KEY"], "codex-auth")
            self.assertNotIn("FACTORY_PASSWORD", call["env"])
            self.assertNotIn("FACTORY_USERNAME", call["env"])
            filesystem_override = next(
                value
                for value in command
                if value.startswith(
                    "permissions.workshop-product-run.filesystem="
                )
            )
            filesystem = tomllib.loads(filesystem_override)["permissions"][
                "workshop-product-run"
            ]["filesystem"]
            self.assertEqual(filesystem[str(root)], "write")
            self.assertEqual(filesystem[str(root.parent)], "deny")
            self.assertEqual(filesystem[str(root / ".agents")], "read")
            self.assertEqual(filesystem[str(root / ".codex")], "read")
            self.assertEqual(filesystem[":root"], "deny")
            self.assertEqual(filesystem[":minimal"], "read")
            self.assertEqual(filesystem[":workspace_roots"]["."], "write")
            self.assertEqual(
                filesystem[":workspace_roots"][".agents"], "read"
            )
            self.assertEqual(
                filesystem[":workspace_roots"]["**/.env*"], "deny"
            )
            workspace_override = next(
                value
                for value in command
                if value.startswith(
                    "permissions.workshop-product-run.workspace_roots="
                )
            )
            workspace_roots = tomllib.loads(workspace_override)["permissions"][
                "workshop-product-run"
            ]["workspace_roots"]
            self.assertEqual(workspace_roots, {str(root): True})
            self.assertEqual(filesystem[str(Path(sys.executable))], "read")
            self.assertEqual(
                filesystem[str(Path(sys.executable).resolve(strict=True))], "read"
            )
            marker = Path(sys.executable).parent.parent / "pyvenv.cfg"
            if marker.is_file() and not marker.is_symlink():
                self.assertEqual(
                    filesystem[str(Path(sys.executable).parent)],
                    "read",
                )
            self.assertEqual(filesystem[TEST_CODEX_BINARY], "read")
            self.assertNotIn("/fixture/codex-home", filesystem)
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

    def test_terminal_usage_is_reduced_to_exact_bounded_token_counters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            completed = self.start_events(terminal=False)
            completed.append(
                event(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 11_288,
                            "cached_input_tokens": 8_960,
                            "cache_write_input_tokens": 0,
                            "output_tokens": 266,
                            "reasoning_output_tokens": 255,
                        },
                    }
                )
            )
            malformed = self.start_events(terminal=False)
            malformed.append(
                event(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 0,
                            "cache_write_input_tokens": 0,
                            "output_tokens": -1,
                            "reasoning_output_tokens": 3,
                        },
                    }
                )
            )
            launcher, unused_factory = self.launcher(
                [{"stdout": completed}, {"stdout": malformed}]
            )

            started = self.start(launcher, root)
            resumed = self.resume(launcher, root)

            self.assertEqual(started.token_count, 11_554)
            self.assertEqual(started.to_dict()["token_count"], 11_554)
            self.assertIsNone(resumed.token_count)
            self.assertNotIn("token_count", resumed.to_dict())

    def test_permission_profile_trusts_only_the_exact_codex_helper_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            root = container / "run"
            binary_dir = container / "codex-bin"
            root.mkdir()
            binary_dir.mkdir()
            target = binary_dir / "codex-real"
            target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            target.chmod(0o700)
            binary = binary_dir / "codex"
            binary.symlink_to(target)
            launcher, factory = self.launcher(
                [{"stdout": self.start_events()}],
                binary=str(binary),
            )

            self.start(launcher, root)

            command = factory.calls[0][0]
            self.assertEqual(launcher.binary, str(target))
            self.assertEqual(command[0], str(target))
            filesystem_override = next(
                value
                for value in command
                if value.startswith(
                    "permissions.workshop-product-run.filesystem="
                )
            )
            filesystem = tomllib.loads(filesystem_override)["permissions"][
                "workshop-product-run"
            ]["filesystem"]
            self.assertEqual(filesystem[str(target)], "read")
            self.assertNotIn(str(binary), filesystem)
            self.assertNotIn(str(binary_dir), filesystem)
            self.assertEqual(filesystem[str(container)], "deny")
            self.assertEqual(filesystem[str(root)], "write")
            self.assertFalse(
                any(
                    key.startswith(str(binary_dir)) and value == "write"
                    for key, value in filesystem.items()
                    if isinstance(key, str)
                )
            )
            policy = codex_runtime._codex_run_policy(root, str(binary))
            self.assertEqual(
                {item.path for item in policy.trusted_codex_runtime_paths},
                {str(target)},
            )

    def test_launcher_rejects_an_unsafe_codex_helper_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            cases = (root / "missing-codex", root / "non-executable-codex")
            cases[1].write_text("not executable\n", encoding="utf-8")
            cases[1].chmod(0o600)

            for binary in cases:
                with self.subTest(binary=binary), self.assertRaises(
                    CodexInvocationError
                ):
                    CodexNativeSessionLauncher(
                        binary=str(binary),
                        cli_version="0.145.0",
                    )

    def test_activity_observer_receives_only_coarse_host_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            private_sentinel = "FACTORY_PASSWORD=secret /private/run thread-identity"
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": [
                            event(
                                {
                                    "type": "thread.started",
                                    "thread_id": THREAD_ID,
                                }
                            ),
                            event({"type": "turn.started"}),
                            event(
                                {
                                    "type": "item.updated",
                                    "item": {
                                        "id": private_sentinel,
                                        "type": "reasoning",
                                        "text": private_sentinel,
                                    },
                                }
                            ),
                            event(
                                {
                                    "type": "item.started",
                                    "item": {
                                        "id": "tool-secret",
                                        "type": "command_execution",
                                        "command": private_sentinel,
                                    },
                                }
                            ),
                            event(
                                {
                                    "type": "item.started",
                                    "item": {
                                        "id": "agent-secret",
                                        "type": "collaboration_tool_call",
                                        "arguments": private_sentinel,
                                    },
                                }
                            ),
                            event(
                                {
                                    "type": "item.completed",
                                    "item": {
                                        "id": "message-secret",
                                        "type": "agent_message",
                                        "text": private_sentinel,
                                    },
                                }
                            ),
                            event({"type": "turn.completed", "usage": {}}),
                        ]
                    }
                ]
            )
            observed = []

            self.start(launcher, root, activity_observer=observed.append)

            self.assertEqual(
                observed,
                [
                    "starting",
                    "starting",
                    "reasoning",
                    "reasoning",
                    "tool",
                    "subagent",
                    "finalizing",
                    "completed",
                ],
            )
            rendered = json.dumps(observed)
            self.assertNotIn(private_sentinel, rendered)
            self.assertNotIn(THREAD_ID, rendered)

    def test_live_silent_process_emits_content_free_running_heartbeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            stdout_start = threading.Event()
            private_sentinel = (
                "FACTORY_PASSWORD=secret /private/run thread-identity"
            )
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout_start_event": stdout_start,
                        "stdout": self.start_events(
                            message=private_sentinel,
                            search=False,
                        ),
                    }
                ]
            )
            observed = []

            def observe(activity):
                observed.append(activity)
                if activity == "running":
                    stdout_start.set()

            with mock.patch.object(
                codex_runtime,
                "_CODEX_ACTIVITY_HEARTBEAT_SECONDS",
                0.01,
            ):
                outcome = self.start(
                    launcher,
                    root,
                    activity_observer=observe,
                )

            self.assertEqual(outcome.status, "completed")
            self.assertEqual(observed[0:2], ["starting", "running"])
            self.assertEqual(observed[-1], "completed")
            self.assertTrue(
                set(observed).issubset(
                    {"starting", "running", "finalizing", "completed"}
                )
            )
            rendered = json.dumps(observed)
            self.assertNotIn(private_sentinel, rendered)
            self.assertNotIn(THREAD_ID, rendered)

    def test_stuck_heartbeat_cannot_delay_or_overwrite_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            heartbeat_entered = threading.Event()
            release_heartbeat = threading.Event()
            heartbeat_returned = threading.Event()
            terminal_replayed = threading.Event()
            observed = []
            observed_lock = threading.Lock()
            callback_lock = threading.Lock()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout_start_event": heartbeat_entered,
                        "stdout": self.start_events(search=False),
                    }
                ]
            )

            def observe(activity):
                # A real sink may serialize its own filesystem updates. Hold
                # that lock while the heartbeat is deliberately stuck: a
                # concurrent terminal callback would wedge behind it.
                with callback_lock:
                    if activity == "running":
                        heartbeat_entered.set()
                        release_heartbeat.wait(timeout=2)
                        with observed_lock:
                            observed.append(activity)
                        heartbeat_returned.set()
                        return
                    with observed_lock:
                        observed.append(activity)
                        completed = observed.count("completed")
                    if completed >= 1:
                        terminal_replayed.set()

            with mock.patch.object(
                codex_runtime,
                "_CODEX_ACTIVITY_HEARTBEAT_SECONDS",
                0.01,
            ):
                outcome = self.start(
                    launcher,
                    root,
                    activity_observer=observe,
                )

            self.assertEqual(outcome.status, "completed")
            self.assertFalse(heartbeat_returned.is_set())

            release_heartbeat.set()
            self.assertTrue(heartbeat_returned.wait(timeout=1))
            self.assertTrue(terminal_replayed.wait(timeout=1))
            with observed_lock:
                self.assertEqual(observed[-1], "completed")

    def test_stuck_terminal_callback_cannot_delay_launcher_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            terminal_entered = threading.Event()
            release_terminal = threading.Event()
            terminal_returned = threading.Event()
            observed = []
            observed_lock = threading.Lock()
            launcher, unused_factory = self.launcher(
                [{"stdout": self.start_events(search=False)}]
            )

            def observe(activity):
                if activity == "completed":
                    terminal_entered.set()
                    release_terminal.wait(timeout=2)
                    with observed_lock:
                        observed.append(activity)
                    terminal_returned.set()
                    return
                with observed_lock:
                    observed.append(activity)

            outcome = self.start(
                launcher,
                root,
                activity_observer=observe,
            )

            self.assertEqual(outcome.status, "completed")
            self.assertTrue(terminal_entered.is_set())
            self.assertFalse(terminal_returned.is_set())

            release_terminal.set()
            self.assertTrue(terminal_returned.wait(timeout=1))
            with observed_lock:
                self.assertEqual(observed[-1], "completed")

    def test_activity_observer_failure_never_changes_turn_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [{"stdout": self.start_events()}]
            )

            def broken_observer(unused_activity):
                raise OSError("private progress disk is unavailable")

            outcome = self.start(
                launcher,
                root,
                activity_observer=broken_observer,
            )

            self.assertEqual(outcome.status, "completed")

    def test_malformed_item_type_cannot_make_progress_interrupt_a_turn(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
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
                                    "type": "item.started",
                                    "item": {"type": []},
                                }
                            ),
                            event({"type": "turn.completed", "usage": {}}),
                        ]
                    }
                ]
            )
            observed = []

            outcome = self.start(
                launcher,
                root,
                activity_observer=observed.append,
            )

            self.assertEqual(outcome.status, "completed")
            self.assertEqual(observed, ["starting", "starting", "completed"])

    def test_activity_observer_rejects_non_callable_values_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher([])

            with self.assertRaisesRegex(ContractError, "observer must be callable"):
                self.start(launcher, root, activity_observer="not-callable")

            self.assertEqual(factory.calls, [])

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
                            event({"type": "turn.completed", "usage": {}}),
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
                    TEST_CODEX_BINARY,
                    "--search",
                    "--enable",
                    "goals",
                    "--enable",
                    "multi_agent",
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
                    *permission_arguments(root),
                    "--model",
                    "gpt-5.6-sol",
                    THREAD_ID,
                    "-",
                ),
            )
            self.assertNotIn("--ephemeral", command)
            self.assertNotIn("--sandbox", command)
            serialized_command = "\n".join(command)
            self.assertIn(":workspace_roots", serialized_command)
            self.assertNotIn("extends=", serialized_command)
            self.assertIn(
                json.dumps(str(root)) + '=\"write\"', serialized_command
            )
            self.assertIn(
                json.dumps(str(root.parent)) + '=\"deny\"', serialized_command
            )
            self.assertIn(
                'project_root_markers=[".workshop-product-run-root"]',
                command,
            )
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

    def test_resume_accepts_only_the_exact_workshop_python_policy_predecessor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events(message="resumed")},
                ]
            )
            started = self.start(launcher, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            current_policy = codex_runtime._codex_run_policy(
                root,
                launcher.binary,
            )
            historical_policy = (
                codex_runtime._run_policy_before_venv_launcher_directory(
                    root,
                    current_policy,
                )
                or current_policy
            )
            predecessor_policy = (
                codex_runtime._run_policy_before_workshop_python(
                    historical_policy
                )
            )
            predecessor_runtime_sha256 = codex_runtime._runtime_config_sha256(
                launcher.cli_version,
                launcher.model,
                launcher.reasoning_effort,
                predecessor_policy,
            )
            payload["runtime_config_sha256"] = predecessor_runtime_sha256
            identity = {
                key: value
                for key, value in payload.items()
                if key != "checkpoint_sha256"
            }
            payload["checkpoint_sha256"] = codex_runtime._sha256_json(identity)
            checkpoint.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            os.chmod(checkpoint, 0o600)

            resumed = self.resume(launcher, root)

            self.assertEqual(len(factory.calls), 2)
            self.assertEqual(factory.calls[1][0][-2], THREAD_ID)
            self.assertEqual(
                factory.calls[1][1]["env"]["WORKSHOP_PYTHON"],
                str(Path(sys.executable).absolute()),
            )
            self.assertEqual(
                resumed.binding.runtime_config_sha256,
                started.binding.runtime_config_sha256,
            )
            self.assertEqual(
                resumed.binding.checkpoint_sha256,
                payload["checkpoint_sha256"],
            )

    def test_venv_policy_grants_launcher_directory_and_accepts_exact_predecessor(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            root = container / "run"
            venv = container / "trusted-venv"
            bin_dir = venv / "bin"
            root.mkdir()
            bin_dir.mkdir(parents=True)
            (venv / "pyvenv.cfg").write_text(
                "home = %s\ninclude-system-site-packages = false\n"
                % Path(sys.executable).resolve(strict=True).parent,
                encoding="utf-8",
            )
            launcher_path = bin_dir / "python3"
            launcher_path.symlink_to(Path(sys.executable).resolve(strict=True))
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events(message="resumed")},
                ]
            )
            with mock.patch.object(
                codex_runtime.sys,
                "executable",
                str(launcher_path),
            ):
                started = self.start(launcher, root)
                checkpoint = self.host_state(root) / "codex-session.json"
                payload = json.loads(checkpoint.read_text(encoding="utf-8"))
                current_policy = codex_runtime._codex_run_policy(
                    root,
                    launcher.binary,
                )
                current_paths = {
                    item.path for item in current_policy.trusted_python_runtime_paths
                }
                self.assertIn(str(bin_dir), current_paths)
                filesystem_override = next(
                    value
                    for value in factory.calls[0][0]
                    if value.startswith(
                        "permissions.workshop-product-run.filesystem="
                    )
                )
                filesystem = tomllib.loads(filesystem_override)["permissions"][
                    "workshop-product-run"
                ]["filesystem"]
                self.assertEqual(filesystem[str(bin_dir)], "read")
                self.assertEqual(
                    factory.calls[0][1]["env"]["WORKSHOP_PYTHON"],
                    str(launcher_path),
                )

                predecessor_policy = (
                    codex_runtime._run_policy_before_venv_launcher_directory(
                        root,
                        current_policy,
                    )
                )
                self.assertIsNotNone(predecessor_policy)
                predecessor_paths = {
                    item.path
                    for item in predecessor_policy.trusted_python_runtime_paths
                }
                self.assertEqual(
                    predecessor_paths,
                    current_paths - {str(bin_dir)},
                )
                predecessor_runtime_sha256 = (
                    codex_runtime._runtime_config_sha256(
                        launcher.cli_version,
                        launcher.model,
                        launcher.reasoning_effort,
                        predecessor_policy,
                    )
                )
                payload["runtime_config_sha256"] = predecessor_runtime_sha256
                identity = {
                    key: value
                    for key, value in payload.items()
                    if key != "checkpoint_sha256"
                }
                payload["checkpoint_sha256"] = codex_runtime._sha256_json(
                    identity
                )
                checkpoint.write_text(
                    json.dumps(payload, sort_keys=True, separators=(",", ":"))
                    + "\n",
                    encoding="utf-8",
                )
                os.chmod(checkpoint, 0o600)

                resumed = self.resume(launcher, root)

            self.assertEqual(len(factory.calls), 2)
            resumed_filesystem_override = next(
                value
                for value in factory.calls[1][0]
                if value.startswith(
                    "permissions.workshop-product-run.filesystem="
                )
            )
            resumed_filesystem = tomllib.loads(resumed_filesystem_override)[
                "permissions"
            ]["workshop-product-run"]["filesystem"]
            self.assertEqual(resumed_filesystem[str(bin_dir)], "read")
            self.assertEqual(
                resumed.binding.runtime_config_sha256,
                started.binding.runtime_config_sha256,
            )
            self.assertEqual(
                resumed.binding.checkpoint_sha256,
                payload["checkpoint_sha256"],
            )

    def test_resume_rejects_never_shipped_venv_feature_predecessors(self):
        marker = Path(sys.executable).parent.parent / "pyvenv.cfg"
        if not marker.is_file() or marker.is_symlink():
            self.skipTest("test runner is not using a PEP 405 virtual environment")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            self.start(launcher, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            original = json.loads(checkpoint.read_text(encoding="utf-8"))
            current_policy = codex_runtime._codex_run_policy(
                root,
                launcher.binary,
            )
            current_without_helper = (
                codex_runtime._run_policy_before_codex_fs_helper(
                    root,
                    current_policy,
                )
            )
            never_shipped = (
                (
                    codex_runtime._run_policy_before_workshop_python(
                        current_policy
                    ),
                    True,
                ),
                (current_without_helper, False),
                (
                    codex_runtime._run_policy_before_workshop_python(
                        current_without_helper
                    ),
                    False,
                ),
            )
            for policy, include_codex_runtime_paths in never_shipped:
                with self.subTest(policy=policy):
                    payload = dict(original)
                    payload["runtime_config_sha256"] = (
                        codex_runtime._runtime_config_sha256(
                            launcher.cli_version,
                            launcher.model,
                            launcher.reasoning_effort,
                            policy,
                            include_codex_runtime_paths=(
                                include_codex_runtime_paths
                            ),
                        )
                    )
                    identity = {
                        key: value
                        for key, value in payload.items()
                        if key != "checkpoint_sha256"
                    }
                    payload["checkpoint_sha256"] = (
                        codex_runtime._sha256_json(identity)
                    )
                    checkpoint.write_text(
                        json.dumps(
                            payload,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    os.chmod(checkpoint, 0o600)

                    with self.assertRaisesRegex(
                        ContractError,
                        "binding is invalid",
                    ):
                        self.resume(launcher, root)

            self.assertEqual(len(factory.calls), 1)

    def test_resume_accepts_exact_pre_codex_helper_policy_predecessor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events(message="resumed")},
                ]
            )
            self.start(launcher, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            current_policy = codex_runtime._codex_run_policy(
                root,
                launcher.binary,
            )
            historical_policy = (
                codex_runtime._run_policy_before_venv_launcher_directory(
                    root,
                    current_policy,
                )
                or current_policy
            )
            predecessor_policy = (
                codex_runtime._run_policy_before_codex_fs_helper(
                    root,
                    historical_policy,
                )
            )
            payload["runtime_config_sha256"] = (
                codex_runtime._runtime_config_sha256(
                    launcher.cli_version,
                    launcher.model,
                    launcher.reasoning_effort,
                    predecessor_policy,
                    include_codex_runtime_paths=False,
                )
            )
            identity = {
                key: value
                for key, value in payload.items()
                if key != "checkpoint_sha256"
            }
            payload["checkpoint_sha256"] = codex_runtime._sha256_json(identity)
            checkpoint.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            os.chmod(checkpoint, 0o600)

            resumed = self.resume(launcher, root)

            filesystem_override = next(
                value
                for value in factory.calls[1][0]
                if value.startswith(
                    "permissions.workshop-product-run.filesystem="
                )
            )
            filesystem = tomllib.loads(filesystem_override)["permissions"][
                "workshop-product-run"
            ]["filesystem"]
            self.assertEqual(filesystem[TEST_CODEX_BINARY], "read")
            self.assertEqual(len(factory.calls), 2)
            self.assertEqual(
                resumed.binding.checkpoint_sha256,
                payload["checkpoint_sha256"],
            )

    def test_resume_rejects_a_broader_predecessor_policy_downgrade(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            self.start(launcher, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            current_policy = codex_runtime._codex_run_policy(
                root,
                launcher.binary,
            )
            predecessor_policy = (
                codex_runtime._run_policy_before_workshop_python(current_policy)
            )
            broader_downgrade = replace(
                predecessor_policy,
                environment_overrides=tuple(
                    entry
                    for entry in predecessor_policy.environment_overrides
                    if entry[0] != "PYTHONHASHSEED"
                ),
            )
            payload["runtime_config_sha256"] = (
                codex_runtime._runtime_config_sha256(
                    launcher.cli_version,
                    launcher.model,
                    launcher.reasoning_effort,
                    broader_downgrade,
                )
            )
            identity = {
                key: value
                for key, value in payload.items()
                if key != "checkpoint_sha256"
            }
            payload["checkpoint_sha256"] = codex_runtime._sha256_json(identity)
            checkpoint.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            os.chmod(checkpoint, 0o600)

            with self.assertRaisesRegex(ContractError, "binding is invalid"):
                self.resume(launcher, root)

            self.assertEqual(len(factory.calls), 1)

    def test_rejects_product_temp_symlink_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            outside = root.parent / "outside-temp"
            outside.mkdir()
            (root / ".tmp").symlink_to(outside, target_is_directory=True)
            launcher, factory = self.launcher([{"stdout": self.start_events()}])

            with self.assertRaisesRegex(
                CodexInvocationError, "temp directory must be a real 0700"
            ):
                self.start(launcher, root)
            self.assertEqual(factory.calls, [])

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

    def test_runtime_identity_is_bound_to_the_exact_resolved_run_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary).resolve()
            first_root = container / "first"
            second_root = container / "second"
            first_root.mkdir()
            second_root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events()},
                ]
            )

            first = self.start(launcher, first_root)
            second = self.start(launcher, second_root)

            self.assertNotEqual(
                first.binding.runtime_config_sha256,
                second.binding.runtime_config_sha256,
            )

    def test_resume_rejects_changed_permission_environment_or_runtime_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            self.start(launcher, root)
            call_count = len(factory.calls)

            original_permissions = codex_runtime._permission_config_arguments

            def changed_permissions(
                run_root,
                trusted_python_paths,
                trusted_codex_paths,
            ):
                return (
                    *original_permissions(
                        run_root,
                        trusted_python_paths,
                        trusted_codex_paths,
                    ),
                    "--config",
                    'permissions.workshop-product-run.network.enabled=true',
                )

            identities = codex_runtime._python_runtime_permission_identities()
            changed_identity = replace(
                identities[0],
                inode=identities[0].inode + 1,
            )
            codex_identities = (
                codex_runtime._codex_runtime_permission_identities(
                    launcher.binary
                )
            )
            changed_codex_identity = replace(
                codex_identities[0],
                inode=codex_identities[0].inode + 1,
            )
            policy_changes = (
                mock.patch.object(
                    codex_runtime,
                    "_permission_config_arguments",
                    side_effect=changed_permissions,
                ),
                mock.patch.object(
                    codex_runtime,
                    "CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST",
                    codex_runtime.CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST[:-1],
                ),
                mock.patch.object(
                    codex_runtime,
                    "_CODEX_RUN_STATIC_ENVIRONMENT_OVERRIDES",
                    (
                        ("PYTHONHASHSEED", "1"),
                        ("PYTHONDONTWRITEBYTECODE", "1"),
                        ("PYTHONNOUSERSITE", "1"),
                    ),
                ),
                mock.patch.object(
                    codex_runtime,
                    "_python_runtime_permission_identities",
                    return_value=(changed_identity, *identities[1:]),
                ),
                mock.patch.object(
                    codex_runtime,
                    "_codex_runtime_permission_identities",
                    return_value=(
                        changed_codex_identity,
                        *codex_identities[1:],
                    ),
                ),
            )
            for index, policy_change in enumerate(policy_changes):
                with self.subTest(policy_change=index), policy_change:
                    with self.assertRaisesRegex(
                        ContractError, "binding is invalid"
                    ):
                        self.resume(launcher, root)

            self.assertEqual(len(factory.calls), call_count)

    def test_rotated_inherited_secret_does_not_change_runtime_policy_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events(message="resumed")},
                ]
            )
            common_environment = {
                "PATH": "/fixture/bin",
                "HOME": "/fixture/home",
                "CODEX_HOME": "/fixture/codex-home",
            }
            with mock.patch.dict(
                os.environ,
                {**common_environment, "OPENAI_API_KEY": "rotated-secret-one"},
                clear=True,
            ):
                started = self.start(launcher, root)
            with mock.patch.dict(
                os.environ,
                {**common_environment, "OPENAI_API_KEY": "rotated-secret-two"},
                clear=True,
            ):
                resumed = self.resume(launcher, root)

            self.assertEqual(
                started.binding.runtime_config_sha256,
                resumed.binding.runtime_config_sha256,
            )
            self.assertEqual(
                factory.calls[0][1]["env"]["OPENAI_API_KEY"],
                "rotated-secret-one",
            )
            self.assertEqual(
                factory.calls[1][1]["env"]["OPENAI_API_KEY"],
                "rotated-secret-two",
            )
            checkpoint = self.host_state(root) / "codex-session.json"
            checkpoint_text = checkpoint.read_text(encoding="utf-8")
            self.assertNotIn("rotated-secret-one", checkpoint_text)
            self.assertNotIn("rotated-secret-two", checkpoint_text)

    def test_resume_accepts_supported_in_place_cli_upgrade(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            factory = FakePopenFactory(
                [
                    {"stdout": self.start_events()},
                    {"stdout": self.start_events(message="resumed after upgrade")},
                ]
            )
            original = CodexNativeSessionLauncher(
                binary=TEST_CODEX_BINARY,
                popen_factory=factory,
                cli_version="0.145.0",
            )
            upgraded = CodexNativeSessionLauncher(
                binary=TEST_CODEX_BINARY,
                popen_factory=factory,
                cli_version="0.150.1",
            )

            started = self.start(original, root)
            checkpoint = self.host_state(root) / "codex-session.json"
            checkpoint_before = checkpoint.read_bytes()
            resumed = self.resume(upgraded, root)

            self.assertEqual(resumed.status, "completed")
            self.assertEqual(len(factory.calls), 2)
            self.assertIn("resume", factory.calls[1][0])
            self.assertIn(THREAD_ID, factory.calls[1][0])
            self.assertEqual(checkpoint.read_bytes(), checkpoint_before)
            self.assertEqual(
                resumed.binding.checkpoint_sha256,
                started.binding.checkpoint_sha256,
            )
            self.assertNotEqual(
                resumed.binding.runtime_config_sha256,
                started.binding.runtime_config_sha256,
            )

    def test_resume_rejects_cli_downgrade_and_major_upgrade(self):
        for original_version, resumed_version in (
            ("0.150.1", "0.145.0"),
            ("0.150.1", "1.0.0"),
        ):
            with self.subTest(
                original_version=original_version,
                resumed_version=resumed_version,
            ), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve() / "run"
                root.mkdir()
                factory = FakePopenFactory(
                    [
                        {"stdout": self.start_events()},
                        {"stdout": self.start_events(message="must not launch")},
                    ]
                )
                original = CodexNativeSessionLauncher(
                    binary=TEST_CODEX_BINARY,
                    popen_factory=factory,
                    cli_version=original_version,
                )
                changed = CodexNativeSessionLauncher(
                    binary=TEST_CODEX_BINARY,
                    popen_factory=factory,
                    cli_version=resumed_version,
                )

                self.start(original, root)
                with self.assertRaisesRegex(ContractError, "binding is invalid"):
                    self.resume(changed, root)

                self.assertEqual(len(factory.calls), 1)

    def test_native_runtime_version_requires_goals_and_subagents(self):
        self.assertEqual(MINIMUM_CODEX_NATIVE_RUNTIME_VERSION, (0, 145, 0))
        self.assertFalse(codex_supports_native_workshop("0.144.9"))
        self.assertTrue(codex_supports_native_workshop("0.145.0"))

    def test_native_turn_defaults_to_the_maximum_supported_hour(self):
        self.assertEqual(DEFAULT_CODEX_TIMEOUT_SECONDS, 3_600)
        launcher = CodexNativeSessionLauncher(
            binary=TEST_CODEX_BINARY,
            cli_version="0.145.0",
        )
        self.assertEqual(launcher.timeout_seconds, 3_600)
        with self.assertRaisesRegex(ValueError, "1 to 3,600"):
            CodexNativeSessionLauncher(
                binary=TEST_CODEX_BINARY,
                cli_version="0.145.0",
                timeout_seconds=3_601,
            )

    def test_finalization_marker_allows_bounded_goal_completion_grace(self):
        self.assertEqual(
            codex_runtime._CODEX_FINALIZATION_MARKER_GRACE_SECONDS,
            30.0,
        )
        self.assertLess(
            codex_runtime._CODEX_FINALIZATION_MARKER_GRACE_SECONDS,
            DEFAULT_CODEX_TIMEOUT_SECONDS,
        )

    def test_completed_turn_is_reaped_after_a_short_natural_exit_grace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(),
                        "hang_until_terminated": True,
                    }
                ]
            )

            outcome = self.start(launcher, root)

            process = factory.processes[0]
            self.assertEqual(outcome.status, "completed")
            self.assertTrue(process.terminated)
            self.assertFalse(process.killed)
            self.assertLessEqual(process.wait_timeouts[0], 0.25)
            self.assertTrue(process.stdin.closed)
            self.assertTrue(process.stdout.closed)
            self.assertTrue(process.stderr.closed)

    def test_keyboard_interrupt_reaps_process_and_preserves_exact_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()

            def interrupt_host():
                raise KeyboardInterrupt()

            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(),
                        "stdout_callbacks": {1: interrupt_host},
                        "hang_until_terminated": True,
                    },
                    {"stdout": self.start_events()},
                ]
            )

            with self.assertRaises(KeyboardInterrupt):
                self.start(launcher, root)

            self.assertTrue(factory.processes[0].terminated)
            checkpoint = self.host_state(root) / "codex-session.json"
            self.assertTrue(checkpoint.is_file())

            outcome = self.resume(launcher, root)

            self.assertEqual(outcome.status, "completed")
            self.assertIn("resume", factory.calls[1][0])
            self.assertIn(THREAD_ID, factory.calls[1][0])

    def test_system_exit_during_stream_setup_still_reaps_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [{"stdout": self.start_events(), "hang_until_terminated": True}]
            )

            with mock.patch.object(
                codex_runtime._NativeActivityReporter,
                "start",
                side_effect=SystemExit(7),
            ), self.assertRaises(SystemExit) as caught:
                self.start(launcher, root)

            self.assertEqual(caught.exception.code, 7)
            self.assertTrue(factory.processes[0].terminated)

    def test_agent_message_does_not_infer_turn_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"
            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "hang_until_terminated": True,
                    }
                ]
            )

            with self.assertRaisesRegex(
                CodexRecoverableInvocationError, "timed out"
            ):
                self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )

            self.assertTrue(factory.processes[0].terminated)

    def test_new_finalization_marker_reaps_missing_terminal_without_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"

            def finalize():
                marker.write_text("{}\n", encoding="utf-8")

            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stdout_callbacks": {2: finalize},
                        "block_stdout_after_values": True,
                        "hang_until_terminated": True,
                    }
                ]
            )

            with mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                0.05,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.005,
            ), self.assertRaisesRegex(
                CodexFinalizedWithoutTerminalError,
                "finalized without a terminal event",
            ) as caught:
                self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )

            self.assertNotIsInstance(
                caught.exception,
                CodexRecoverableInvocationError,
            )
            self.assertTrue(factory.processes[0].terminated)

    def test_finalization_marker_grace_cannot_extend_turn_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"

            def finalize():
                marker.write_text("{}\n", encoding="utf-8")

            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stdout_callbacks": {2: finalize},
                        "hang_until_terminated": True,
                    }
                ],
                timeout_seconds=1,
            )

            started_at = time.monotonic()
            with mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                2.0,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.005,
            ), self.assertRaises(CodexFinalizedWithoutTerminalError):
                self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )
            elapsed = time.monotonic() - started_at

            self.assertLess(elapsed, 1.5)
            self.assertTrue(factory.processes[0].terminated)

    def test_public_terminal_during_marker_grace_preserves_normal_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"

            def finalize_before_terminal():
                marker.write_text("{}\n", encoding="utf-8")
                time.sleep(0.03)

            launcher, factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(),
                        "stdout_callbacks": {3: finalize_before_terminal},
                    }
                ]
            )

            with mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                0.2,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.005,
            ):
                outcome = self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )

            self.assertEqual(outcome.status, "completed")
            self.assertFalse(factory.processes[0].terminated)

    def test_terminal_winning_expiry_arbitration_prevents_marker_reap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"
            guard = mock.Mock()
            guard.reap.return_value = True
            watch = codex_runtime._FinalizationMarkerWatch(
                marker,
                guard,
                time.monotonic() + 1.0,
            )
            identity_checked = threading.Event()
            release_identity = threading.Event()
            original_identity = watch._regular_identity

            def hold_after_identity_check():
                identity = original_identity()
                identity_checked.set()
                release_identity.wait(timeout=1)
                return identity

            with mock.patch.object(
                watch,
                "_regular_identity",
                side_effect=hold_after_identity_check,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                0.02,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.002,
            ):
                watch.start()
                marker.write_text("{}\n", encoding="utf-8")
                self.assertTrue(identity_checked.wait(timeout=1))
                watch.observe_turn_completed()
                release_identity.set()
                self.assertTrue(watch._resolved.wait(timeout=1))
                watch.close()

            guard.reap.assert_not_called()
            self.assertFalse(watch.triggered)

    def test_finalization_marker_cannot_claim_failed_process_quiescence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"

            def finalize():
                marker.write_text("{}\n", encoding="utf-8")

            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stdout_callbacks": {2: finalize},
                        "ignore_termination": True,
                    }
                ]
            )

            with mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                0.02,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.002,
            ), self.assertRaisesRegex(
                CodexInvocationError,
                "could not be terminated safely",
            ) as caught:
                self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )

            self.assertNotIsInstance(
                caught.exception,
                CodexFinalizedWithoutTerminalError,
            )

    def test_only_new_exact_regular_in_run_marker_can_trigger_reap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"
            marker.write_text("stale\n", encoding="utf-8")
            launcher, unused_factory = self.launcher(
                [{"stdout": self.start_events(terminal=False)}]
            )

            with self.assertRaisesRegex(
                CodexInvocationError,
                "did not complete",
            ) as caught:
                self.start(
                    launcher,
                    root,
                    finalization_marker=marker,
                )
            self.assertNotIsInstance(
                caught.exception,
                CodexFinalizedWithoutTerminalError,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            marker = root / "agent-outcome.json"
            outside = root.parent / "outside-agent-outcome.json"
            outside.write_text("outside\n", encoding="utf-8")

            def link_outside():
                marker.symlink_to(outside)

            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stdout_callbacks": {2: link_outside},
                        "block_stdout_after_values": True,
                        "stdout_block_timeout": 0.1,
                        "hang_until_terminated": True,
                    }
                ]
            )
            with mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_GRACE_SECONDS",
                0.02,
            ), mock.patch.object(
                codex_runtime,
                "_CODEX_FINALIZATION_MARKER_POLL_SECONDS",
                0.002,
            ), self.assertRaises(CodexInvocationError) as caught:
                self.start(launcher, root, finalization_marker=marker)
            self.assertNotIsInstance(
                caught.exception,
                CodexFinalizedWithoutTerminalError,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [{"stdout": self.start_events()}]
            )
            with self.assertRaisesRegex(
                ContractError,
                "exact in-run agent-outcome.json",
            ):
                self.start(
                    launcher,
                    root,
                    finalization_marker=root.parent / "agent-outcome.json",
                )
            self.assertEqual(factory.calls, [])

    def test_clean_process_exit_without_turn_completed_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "returncode": 0,
                    }
                ]
            )

            with self.assertRaisesRegex(
                CodexInvocationError, "did not complete"
            ):
                self.start(launcher, root)

    def test_missing_terminal_preserves_explicit_transient_category(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stderr": ["provider stream disconnected"],
                        "returncode": 0,
                    }
                ]
            )

            with self.assertRaisesRegex(
                CodexRecoverableInvocationError,
                "provider transport was interrupted",
            ):
                self.start(launcher, root)

    def test_unrelated_private_stderr_cannot_select_transport_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "stderr": [
                            "local file operation: resource temporarily unavailable\n",
                            "tool: provider stream disconnected\n",
                        ],
                        "returncode": 1,
                    }
                ]
            )

            with self.assertRaises(CodexInvocationError) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )

    def test_timeout_is_typed_and_preserves_the_exact_session_for_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, factory = self.launcher(
                [
                    {"stdout": self.start_events(terminal=False)},
                    {"stdout": self.start_events()},
                ]
            )

            with mock.patch(
                "workshop.runtime.codex.threading.Timer", ImmediateTimer
            ), self.assertRaises(CodexRecoverableInvocationError):
                self.start(launcher, root)

            timed_out_process = factory.processes[0]
            self.assertTrue(timed_out_process.stdin.closed)
            self.assertTrue(timed_out_process.stdout.closed)
            self.assertTrue(timed_out_process.stderr.closed)

            outcome = self.resume(launcher, root)

            self.assertEqual(outcome.status, "completed")
            self.assertEqual(len(factory.calls), 2)
            resume_command = factory.calls[1][0]
            self.assertIn("resume", resume_command)
            self.assertIn(THREAD_ID, resume_command)

    def test_timeout_is_not_recoverable_when_process_cannot_be_reaped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "ignore_termination": True,
                    }
                ]
            )

            with mock.patch(
                "workshop.runtime.codex.threading.Timer", ImmediateTimer
            ), self.assertRaisesRegex(
                CodexInvocationError, "could not be terminated safely"
            ) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )

    def test_process_supervisor_rejects_non_exception_error_types(self):
        class InvalidPsutil:
            Error = object
            NoSuchProcess = object

            @staticmethod
            def Process(unused_process_id):
                return None

            @staticmethod
            def process_iter(unused_attrs=()):
                return ()

        with mock.patch.object(
            codex_runtime.importlib,
            "import_module",
            return_value=InvalidPsutil,
        ):
            self.assertIsNone(codex_runtime._psutil_api())

    def test_process_session_rejects_a_reused_leader_before_signaling(self):
        class FakePsutilError(Exception):
            pass

        class FakeNoSuchProcess(FakePsutilError):
            pass

        candidate = mock.Mock()
        candidate.info = {"pid": 4_242}
        candidate.pid = 4_242
        candidate.create_time.return_value = 2_000.0
        fake_psutil = mock.Mock()
        fake_psutil.Error = FakePsutilError
        fake_psutil.NoSuchProcess = FakeNoSuchProcess
        fake_psutil.process_iter.return_value = (candidate,)
        identity = codex_runtime._ProcessSessionIdentity(4_242, 1_000.0)

        with mock.patch.object(
            codex_runtime,
            "_psutil_api",
            return_value=fake_psutil,
        ), mock.patch.object(
            codex_runtime.os,
            "getsid",
            return_value=4_242,
        ):
            self.assertIsNone(
                codex_runtime._signal_process_session(
                    identity,
                    signal.SIGTERM,
                )
            )

        candidate.send_signal.assert_not_called()

    @unittest.skipUnless(hasattr(os, "killpg"), "POSIX process groups required")
    def test_group_reap_kills_a_sigterm_ignoring_tool_descendant(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            child_ready = root / "child-ready"
            forbidden_late_write = root / "late-child-write"
            child_code = (
                "import signal,time\n"
                "from pathlib import Path\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "Path(%r).write_text('ready', encoding='utf-8')\n"
                "time.sleep(0.75)\n"
                "Path(%r).write_text('survived', encoding='utf-8')\n"
                % (str(child_ready), str(forbidden_late_write))
            )
            parent_code = (
                "import subprocess,time\n"
                "subprocess.Popen(%r)\n"
                "time.sleep(30)\n"
                % [sys.executable, "-c", child_code]
            )
            process = subprocess.Popen(
                [sys.executable, "-c", parent_code],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 5.0
                while not child_ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(child_ready.exists())
                process_group_id = codex_runtime._dedicated_process_group_id(
                    process
                )
                self.assertEqual(process_group_id, process.pid)

                self.assertTrue(
                    codex_runtime._terminate_safely(
                        process,
                        process_group_id=process_group_id,
                    )
                )
                time.sleep(1.0)

                self.assertIsNotNone(process.poll())
                self.assertFalse(forbidden_late_write.exists())
            finally:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=2)

    @unittest.skipUnless(
        hasattr(os, "setpgid") and hasattr(os, "getsid"),
        "POSIX process sessions required",
    )
    def test_session_reap_kills_helper_in_its_own_process_group(self):
        psutil = codex_runtime._psutil_api()
        if psutil is None:
            self.skipTest("process supervisor is unavailable")
        host_session_id = os.getsid(0)
        host_session_identity = codex_runtime._ProcessSessionIdentity(
            host_session_id,
            psutil.Process(host_session_id).create_time(),
        )
        if codex_runtime._process_session_members(host_session_identity) is None:
            self.skipTest("process-session enumeration is unavailable")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            child_ready = root / "child-ready"
            forbidden_late_write = root / "late-child-write"
            child_code = (
                "import os,signal,time\n"
                "from pathlib import Path\n"
                "os.setpgid(0, 0)\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "Path(%r).write_text(str(os.getpid()), encoding='utf-8')\n"
                "time.sleep(0.9)\n"
                "Path(%r).write_text('survived', encoding='utf-8')\n"
                % (str(child_ready), str(forbidden_late_write))
            )
            parent_code = (
                "import subprocess,time\n"
                "subprocess.Popen(%r)\n"
                "time.sleep(30)\n"
                % [sys.executable, "-c", child_code]
            )
            process = subprocess.Popen(
                [sys.executable, "-c", parent_code],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 5.0
                while not child_ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(child_ready.exists())
                child_pid = int(child_ready.read_text(encoding="utf-8"))
                process_group_id = codex_runtime._dedicated_process_group_id(
                    process
                )
                process_session_identity = (
                    codex_runtime._dedicated_process_session_identity(process)
                )
                self.assertEqual(process_group_id, process.pid)
                self.assertIsNotNone(process_session_identity)
                self.assertEqual(
                    process_session_identity.session_id,
                    process.pid,
                )
                self.assertEqual(os.getpgid(child_pid), child_pid)
                self.assertEqual(os.getsid(child_pid), process.pid)

                self.assertTrue(
                    codex_runtime._terminate_safely(
                        process,
                        process_group_id=process_group_id,
                        process_session_identity=process_session_identity,
                    )
                )
                time.sleep(1.0)

                self.assertIsNotNone(process.poll())
                self.assertFalse(forbidden_late_write.exists())
                self.assertEqual(
                    codex_runtime._process_session_members(
                        process_session_identity
                    ),
                    (),
                )
            finally:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=2)

    def test_timeout_does_not_hide_a_concurrent_event_contract_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [{"stdout": ["not-json\n"]}]
            )

            with mock.patch(
                "workshop.runtime.codex.threading.Timer", ImmediateTimer
            ), self.assertRaisesRegex(
                CodexInvocationError, "event stream was invalid"
            ) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )

    def test_unknown_incomplete_exit_is_not_recoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(terminal=False),
                        "returncode": 1,
                    }
                ]
            )

            with self.assertRaises(CodexInvocationError) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )

    def test_agent_message_cannot_select_the_recoverable_transport_category(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(
                            message="provider stream disconnected",
                            terminal=False,
                        ),
                        "returncode": 1,
                    }
                ]
            )

            with self.assertRaises(CodexInvocationError) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )

    def test_completed_turn_does_not_weaken_resume_thread_identity(self):
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
                                    "thread_id": OTHER_THREAD_ID,
                                }
                            ),
                            event({"type": "turn.completed", "usage": {}}),
                        ],
                        "hang_until_terminated": True,
                    },
                ]
            )
            self.start(launcher, root)

            with self.assertRaisesRegex(
                CodexInvocationError, "resumed a different native session"
            ):
                self.resume(launcher, root)

            self.assertTrue(factory.processes[1].terminated)

    def test_terminal_failure_events_fail_closed(self):
        for event_type in ("turn.failed", "error"):
            with self.subTest(
                event_type=event_type
            ), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve() / "run"
                root.mkdir()
                launcher, factory = self.launcher(
                    [
                        {
                            "stdout": [
                                event(
                                    {
                                        "type": "thread.started",
                                        "thread_id": THREAD_ID,
                                    }
                                ),
                                event({"type": event_type}),
                            ]
                        }
                    ]
                )

                with self.assertRaisesRegex(
                    CodexInvocationError, "reported a failed turn"
                ):
                    self.start(launcher, root)

                self.assertTrue(factory.processes[0].terminated)

    def test_explicit_transport_failure_events_preserve_recoverable_category(self):
        failures = (
            {
                "type": "turn.failed",
                "error": {
                    "message": (
                        "stream disconnected before completion: "
                        "response.completed was not received"
                    )
                },
            },
            {
                "type": "error",
                "message": "provider stream disconnected: upstream reset",
            },
        )
        for failure in failures:
            with self.subTest(
                event_type=failure["type"]
            ), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve() / "run"
                root.mkdir()
                launcher, factory = self.launcher(
                    [
                        {
                            "stdout": [
                                event(
                                    {
                                        "type": "thread.started",
                                        "thread_id": THREAD_ID,
                                    }
                                ),
                                event(failure),
                            ]
                        }
                    ]
                )

                with self.assertRaisesRegex(
                    CodexRecoverableInvocationError,
                    "provider transport was interrupted",
                ) as caught:
                    self.start(launcher, root)

                self.assertNotIn("upstream", str(caught.exception))
                self.assertNotIn("response.completed", str(caught.exception))
                self.assertTrue(factory.processes[0].terminated)

    def test_unanchored_failed_turn_message_cannot_select_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
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
                                    "type": "turn.failed",
                                    "error": {
                                        "message": (
                                            "tool failed\n"
                                            "provider stream disconnected"
                                        )
                                    },
                                }
                            ),
                        ]
                    }
                ]
            )

            with self.assertRaises(CodexInvocationError) as caught:
                self.start(launcher, root)

            self.assertNotIsInstance(
                caught.exception, CodexRecoverableInvocationError
            )
            self.assertNotIn("provider stream", str(caught.exception))

    def test_natural_nonzero_exit_after_completed_turn_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            launcher, unused_factory = self.launcher(
                [
                    {
                        "stdout": self.start_events(),
                        "returncode": 1,
                    }
                ]
            )

            with self.assertRaisesRegex(
                CodexInvocationError, "did not complete"
            ):
                self.start(launcher, root)

    def test_rejects_codex_versions_without_native_workshop_primitives(self):
        with self.assertRaisesRegex(
            CodexInvocationError, "0.145.0 or newer"
        ):
            CodexNativeSessionLauncher(
                binary=TEST_CODEX_BINARY,
                cli_version="0.144.9",
            )

    def test_long_valid_event_stream_is_reduced_without_a_cumulative_buffer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
            reasoning = event(
                {
                    "type": "item.updated",
                    "item": {
                        "id": "reasoning-large",
                        "type": "reasoning",
                        "text": "r" * (MAX_CODEX_EVENT_BYTES // 3),
                    },
                }
            )
            events = [
                event({"type": "thread.started", "thread_id": THREAD_ID}),
                reasoning,
                reasoning,
                reasoning,
                reasoning,
                event({"type": "turn.completed", "usage": {}}),
            ]
            self.assertGreater(
                sum(len(value.encode("utf-8")) for value in events),
                MAX_CODEX_EVENT_BYTES,
            )
            self.assertTrue(
                all(
                    len(value.encode("utf-8")) <= MAX_CODEX_EVENT_BYTES
                    for value in events
                )
            )
            launcher, unused_factory = self.launcher([{"stdout": events}])

            outcome = self.start(launcher, root)

            self.assertEqual(outcome.status, "completed")

    def test_oversized_event_records_are_discarded_and_the_turn_continues(self):
        oversized = event(
            {
                "type": "item.updated",
                "item": {
                    "id": "oversized-event",
                    "type": "reasoning",
                    "text": "x" * (3 * MAX_CODEX_EVENT_BYTES),
                },
            }
        )
        self.assertGreater(len(oversized.encode("utf-8")), MAX_CODEX_EVENT_BYTES)
        for stdout in (
            [
                event({"type": "thread.started", "thread_id": THREAD_ID}),
                oversized,
                event({"type": "turn.completed", "usage": {}}),
            ],
            [
                oversized,
                event({"type": "thread.started", "thread_id": THREAD_ID}),
                event({"type": "turn.completed", "usage": {}}),
                oversized.rstrip("\n"),
            ],
        ):
            with self.subTest(position=stdout.index(oversized)), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve() / "run"
                root.mkdir()
                launcher, unused_factory = self.launcher([{"stdout": stdout}])

                outcome = self.start(launcher, root)

                self.assertEqual(outcome.status, "completed")

    def test_bounds_timeout_and_failures_are_terminated_and_redacted(self):
        secret = "FACTORY_PASSWORD=never-show-this"
        cases = (
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
