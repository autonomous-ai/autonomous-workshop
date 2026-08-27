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


def permission_arguments(root):
    immutable = (
        ".agents",
        ".codex",
        ROOT_MARKER,
        "AGENTS.md",
        "STAGE.json",
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
    ):
        self.values = list(values)
        self.callbacks = dict(callbacks or {})
        self.stop_event = stop_event
        self.start_event = start_event

    def __iter__(self):
        if self.start_event is not None:
            self.start_event.wait(timeout=2)
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
            start_event=self.script.get("stdout_start_event"),
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
    def launcher(self, scripts, *, model="gpt-5.6-sol", effort="high"):
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
    ):
        return launcher.start(
            product_id="wish-001",
            wish_sha256=WISH_SHA256,
            constitution_sha256=CONSTITUTION_SHA256,
            run_root=root,
            host_state_root=host_state_root or self.host_state(root),
            prompt=prompt,
            activity_observer=activity_observer,
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
                    "/fixture/codex",
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

            def changed_permissions(run_root, trusted_paths):
                return (
                    *original_permissions(run_root, trusted_paths),
                    "--config",
                    'permissions.workshop-product-run.network.enabled=true',
                )

            identities = codex_runtime._python_runtime_permission_identities()
            changed_identity = replace(
                identities[0],
                inode=identities[0].inode + 1,
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

    def test_native_runtime_version_requires_goals_and_subagents(self):
        self.assertEqual(MINIMUM_CODEX_NATIVE_RUNTIME_VERSION, (0, 145, 0))
        self.assertFalse(codex_supports_native_workshop("0.144.9"))
        self.assertTrue(codex_supports_native_workshop("0.145.0"))

    def test_native_turn_defaults_to_the_maximum_supported_hour(self):
        self.assertEqual(DEFAULT_CODEX_TIMEOUT_SECONDS, 3_600)
        launcher = CodexNativeSessionLauncher(
            binary="/fixture/codex",
            cli_version="0.145.0",
        )
        self.assertEqual(launcher.timeout_seconds, 3_600)
        with self.assertRaisesRegex(ValueError, "1 to 3,600"):
            CodexNativeSessionLauncher(
                binary="/fixture/codex",
                cli_version="0.145.0",
                timeout_seconds=3_601,
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

    def test_agent_message_does_not_infer_turn_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "run"
            root.mkdir()
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
                self.start(launcher, root)

            self.assertTrue(factory.processes[0].terminated)

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
                binary="/fixture/codex",
                cli_version="0.144.9",
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
