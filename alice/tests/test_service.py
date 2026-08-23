import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from alice.service import (
    BoundedProcessRunner,
    HealthState,
    HealthStore,
    IdentityMismatch,
    ProcessResult,
    RuntimeIdentity,
    SourceCapture,
    ServiceError,
    ServiceRunner,
    WorkerAlreadyRunning,
    WorkerLock,
    _positive_float,
    _run_guard_tick,
    configured_tick_timeout_floor,
    effective_max_tick_seconds,
    load_env_file,
    materialize_execution_snapshot,
    message_hash,
    post_start_health_ok,
    probe_health,
    render_plists,
    resolve_runtime_identity,
    sanitized_environment,
    source_tree_sha256,
    verify_execution_snapshot,
    watchdog_receipt_ok,
)


SOURCE_SHA = "a" * 64
CONFIG_SHA = "b" * 64
POLICY_HASH = "c" * 64
BASE_TIME = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
IDENTITY = RuntimeIdentity(SOURCE_SHA, CONFIG_SHA, POLICY_HASH, "draft")


WATCHDOG_PATH = Path(__file__).resolve().parents[1] / "ops" / "watchdog.py"
WATCHDOG_SPEC = importlib.util.spec_from_file_location("alice_ops_watchdog", WATCHDOG_PATH)
assert WATCHDOG_SPEC is not None and WATCHDOG_SPEC.loader is not None
watchdog = importlib.util.module_from_spec(WATCHDOG_SPEC)
WATCHDOG_SPEC.loader.exec_module(watchdog)


class MutableClock:
    def __init__(self, value: datetime = BASE_TIME) -> None:
        self.value = value

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


def health_state(**overrides: object) -> HealthState:
    values: dict[str, object] = {
        "started_at": "2026-08-22T12:00:00.000Z",
        "heartbeat_at": "2026-08-22T12:00:10.000Z",
        "success_at": "2026-08-22T12:00:10.000Z",
        "failure_at": None,
        "tick_started_at": None,
        "consecutive_failures": 0,
        "source_tree_sha256": SOURCE_SHA,
        "config_sha256": CONFIG_SHA,
        "policy_hash": POLICY_HASH,
        "effect_mode": "draft",
        "pid": os.getpid(),
        "message_hash": message_hash("ok"),
    }
    values.update(overrides)
    return HealthState(**values)  # type: ignore[arg-type]


def process_result(code: int = 0, *, digest: str | None = None) -> ProcessResult:
    return ProcessResult(
        exit_code=code,
        digest=digest or message_hash(f"exit={code}"),
        stdout=b"",
        stderr=b"",
    )


class TickDeadlineTests(unittest.TestCase):
    def _config(self) -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "config" / "default.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_text2game_three_phase_deadline_is_derived_and_cannot_be_undercut(self) -> None:
        config = self._config()
        adapters = config["adapters"]
        self.assertIsInstance(adapters, dict)
        text2game = adapters["text2game"]  # type: ignore[index]
        self.assertIsInstance(text2game, dict)
        text2game["enabled"] = True  # type: ignore[index]
        text2game["timeout_seconds"] = 7_200  # type: ignore[index]
        text2game["shutdown_grace_seconds"] = 10  # type: ignore[index]

        floor = configured_tick_timeout_floor(config)
        self.assertEqual(floor, 22_230)
        self.assertEqual(effective_max_tick_seconds(None, config), floor)
        with self.assertRaisesRegex(ServiceError, "shorter than"):
            effective_max_tick_seconds(1_800, config)
        self.assertEqual(effective_max_tick_seconds(floor + 1, config), floor + 1)

    def test_rich_draft_and_vibe_polling_are_included_in_deadline_floor(self) -> None:
        config = self._config()
        adapters = config["adapters"]
        self.assertIsInstance(adapters, dict)
        page_builder = adapters["page_builder"]  # type: ignore[index]
        vibe = adapters["vibe"]  # type: ignore[index]
        self.assertIsInstance(page_builder, dict)
        self.assertIsInstance(vibe, dict)
        page_builder["enabled"] = True  # type: ignore[index]
        vibe["enabled"] = True  # type: ignore[index]

        floor = configured_tick_timeout_floor(config)
        expected_vibe = (
            (vibe["max_job_polls"] + vibe["max_page_polls"])  # type: ignore[index,operator]
            * vibe["poll_interval_seconds"]  # type: ignore[index,operator]
            + (6 * vibe["timeout_seconds"])  # type: ignore[index,operator]
            + 600
        )
        self.assertGreaterEqual(floor, expected_vibe)
        self.assertGreaterEqual(
            floor,
            page_builder["timeout_seconds"]  # type: ignore[index,operator]
            + (100 * page_builder["readback_timeout_seconds"]),  # type: ignore[index,operator]
        )


class EnvironmentTests(unittest.TestCase):
    def test_strict_env_is_not_merged_with_inherited_alice_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alice.env"
            path.write_text(
                "ALICE_FACTORY_TOKEN='file-secret'\nALICE_POLL_SECONDS=19\n",
                encoding="utf-8",
            )
            path.chmod(0o600)
            before = dict(os.environ)
            os.environ["ALICE_FACTORY_TOKEN"] = "inherited-secret"
            os.environ["ALICE_EFFECT_MODE"] = "live"
            try:
                loaded = load_env_file(path.resolve())
                child = sanitized_environment(loaded)
            finally:
                os.environ.clear()
                os.environ.update(before)

            self.assertEqual(child["ALICE_FACTORY_TOKEN"], "file-secret")
            self.assertNotIn("ALICE_EFFECT_MODE", child)
            self.assertEqual(loaded["ALICE_POLL_SECONDS"], "19")

    def test_env_rejects_permissions_symlinks_and_process_injection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "alice.env"
            path.write_text("TOKEN=value\n", encoding="utf-8")
            path.chmod(0o640)
            with self.assertRaisesRegex(ServiceError, "exactly 0600"):
                load_env_file(path.resolve())

            path.chmod(0o600)
            linked = root / "linked.env"
            linked.symlink_to(path)
            with self.assertRaisesRegex(ServiceError, "symlink"):
                load_env_file(linked.absolute())

            path.write_text("PYTHONPATH=/attacker\n", encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaisesRegex(ServiceError, "unsafe"):
                load_env_file(path.resolve())
            for assignment in (
                "PYTHONWARNINGS=ignore\n",
                "GIT_CONFIG_COUNT=1\n",
                "PATH=/attacker\n",
                "HOME=/attacker\n",
            ):
                path.write_text(assignment, encoding="utf-8")
                path.chmod(0o600)
                with self.subTest(assignment=assignment), self.assertRaisesRegex(
                    ServiceError, "unsafe"
                ):
                    load_env_file(path.resolve())

    def test_env_parse_error_does_not_repeat_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secret = "do-not-repeat-this-secret"
            path = Path(directory) / "alice.env"
            path.write_text(f"BAD NAME={secret}\n", encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaises(ServiceError) as caught:
                load_env_file(path.resolve())
            self.assertNotIn(secret, str(caught.exception))


class ProcessBoundaryTests(unittest.TestCase):
    def test_child_environment_is_sanitized_and_output_is_only_captured(self) -> None:
        environment = sanitized_environment({"FROM_ENV_FILE": "yes"})
        inherited_name = "ALICE_INHERITED_SHOULD_NOT_CROSS"
        previous = os.environ.get(inherited_name)
        os.environ[inherited_name] = "secret"
        try:
            result = BoundedProcessRunner(
                timeout_seconds=5,
                term_grace_seconds=0.2,
                max_output_bytes=1024,
            ).run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import os; print(os.getenv('FROM_ENV_FILE')); "
                        f"print(os.getenv('{inherited_name}', 'missing'))"
                    ),
                ],
                environment=environment,
                cwd=Path(tempfile.gettempdir()).resolve(),
            )
        finally:
            if previous is None:
                os.environ.pop(inherited_name, None)
            else:
                os.environ[inherited_name] = previous
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.decode().splitlines(), ["yes", "missing"])

    def test_timeout_terms_then_kills_the_owned_group_and_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            pid_file = root / "child.pid"
            script = root / "hang.py"
            script.write_text(
                "import os, signal, subprocess, sys, time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "child = subprocess.Popen([sys.executable, '-c', "
                "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'])\n"
                "open(sys.argv[1], 'w').write(str(child.pid))\n"
                "while True: time.sleep(1)\n",
                encoding="utf-8",
            )
            result = BoundedProcessRunner(
                timeout_seconds=0.25,
                term_grace_seconds=0.1,
                max_output_bytes=1024,
            ).run(
                [sys.executable, str(script), str(pid_file)],
                environment=sanitized_environment({}),
                cwd=root,
            )
            self.assertTrue(result.timed_out)
            self.assertFalse(result.ok)
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 2
            still_running = True
            while time.monotonic() < deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    still_running = False
                    break
                time.sleep(0.05)
            self.assertFalse(still_running)

    def test_output_overflow_stops_child_without_persisting_output(self) -> None:
        result = BoundedProcessRunner(
            timeout_seconds=5,
            term_grace_seconds=0.1,
            max_output_bytes=128,
        ).run(
            [sys.executable, "-c", "import sys,time; sys.stdout.write('x'*1000000); sys.stdout.flush(); time.sleep(5)"],
            environment=sanitized_environment({}),
            cwd=Path(tempfile.gettempdir()).resolve(),
        )
        self.assertTrue(result.output_overflow)
        self.assertFalse(result.ok)
        self.assertLessEqual(len(result.stdout) + len(result.stderr), 128)

    def test_exited_leader_cannot_leave_pipe_holding_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            pid_file = root / "descendant.pid"
            script = root / "exit-with-child.py"
            script.write_text(
                "import subprocess,sys\n"
                "child=subprocess.Popen([sys.executable,'-c',"
                "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'])\n"
                "open(sys.argv[1],'w').write(str(child.pid))\n",
                encoding="utf-8",
            )
            result = BoundedProcessRunner(
                timeout_seconds=0.3,
                term_grace_seconds=0.1,
                max_output_bytes=1024,
            ).run(
                [sys.executable, str(script), str(pid_file)],
                environment=sanitized_environment({}),
                cwd=root,
            )
            self.assertTrue(result.timed_out)
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail("pipe-holding descendant survived the process-group bound")

    def test_long_running_child_emits_progress_heartbeats(self) -> None:
        callbacks: list[float] = []
        result = BoundedProcessRunner(
            timeout_seconds=2,
            term_grace_seconds=0.1,
            max_output_bytes=1024,
            poll_seconds=0.01,
        ).run(
            [sys.executable, "-c", "import time; time.sleep(.22)"],
            environment=sanitized_environment({}),
            cwd=Path(tempfile.gettempdir()).resolve(),
            progress_callback=lambda: callbacks.append(time.monotonic()),
            progress_interval_seconds=0.05,
        )
        self.assertTrue(result.ok)
        self.assertGreaterEqual(len(callbacks), 3)

    def test_guardian_kills_tick_group_when_worker_control_pipe_closes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            release = root / "release"
            release.mkdir()
            pid_file = root / "tick-child.pid"
            script = root / "guarded-tick.py"
            script.write_text(
                "import signal,subprocess,sys,time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "child=subprocess.Popen([sys.executable,'-c',"
                "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'])\n"
                "open(sys.argv[1],'w').write(str(child.pid))\n"
                "while True: time.sleep(1)\n",
                encoding="utf-8",
            )
            read_fd, write_fd = os.pipe()

            def sever_worker() -> None:
                deadline = time.monotonic() + 2
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                os.close(write_fd)

            closer = threading.Thread(target=sever_worker, daemon=True)
            closer.start()
            args = SimpleNamespace(
                release_root=str(release),
                resolved_config=str(release / ".alice-resolved-config.json"),
                root=str(root),
                control_fd=read_fd,
                expected_source_tree_sha256=SOURCE_SHA,
                expected_config_sha256=CONFIG_SHA,
                expected_policy_hash=POLICY_HASH,
                expected_effect_mode="draft",
                max_tick_seconds=5.0,
                term_grace_seconds=0.1,
                max_output_bytes=1024,
            )
            with patch("alice.service.verify_execution_snapshot"), patch(
                "alice.service._isolated_module_argv",
                return_value=[sys.executable, str(script), str(pid_file)],
            ), redirect_stdout(StringIO()):
                self.assertNotEqual(_run_guard_tick(args), 0)
            closer.join(timeout=1)
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail("guardian left its tick descendant alive after worker EOF")


class IdentityTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_source_tree_hash_covers_every_tracked_file_and_requires_clean_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            alice = root / "alice"
            alice.mkdir()
            (alice / "a.py").write_text("one\n", encoding="utf-8")
            (alice / "nested").mkdir()
            (alice / "nested" / "b.json").write_text("{}\n", encoding="utf-8")
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "alice@example.invalid")
            self._git(root, "config", "user.name", "Alice Test")
            self._git(root, "add", "alice")
            self._git(root, "commit", "-qm", "fixture")
            environment = sanitized_environment({})

            first = source_tree_sha256(alice, environment)
            self.assertEqual(len(first), 64)
            (alice / "nested" / "b.json").write_text('{"changed":true}\n', encoding="utf-8")
            with self.assertRaisesRegex(ServiceError, "not clean"):
                source_tree_sha256(alice, environment)
            self._git(root, "checkout", "--", "alice/nested/b.json")
            (alice / "untracked.txt").write_text("new\n", encoding="utf-8")
            with self.assertRaisesRegex(ServiceError, "not clean"):
                source_tree_sha256(alice, environment)

    def test_resolved_config_hash_uses_env_file_values_not_inherited_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = root / "config.json"
            config.write_text("{}\n", encoding="utf-8")
            before = dict(os.environ)
            os.environ["ALICE_POLL_SECONDS"] = "999"
            try:
                with patch(
                    "alice.service.source_tree_sha256", return_value=SOURCE_SHA
                ), patch(
                    "alice.service._capture_source_tree",
                    return_value=SourceCapture((), SOURCE_SHA),
                ):
                    first = resolve_runtime_identity(
                        config=config,
                        root=root,
                        source_root=Path(__file__).resolve().parents[1],
                        environment=sanitized_environment({"ALICE_POLL_SECONDS": "17"}),
                    )
                    second = resolve_runtime_identity(
                        config=config,
                        root=root,
                        source_root=Path(__file__).resolve().parents[1],
                        environment=sanitized_environment({"ALICE_POLL_SECONDS": "18"}),
                    )
            finally:
                os.environ.clear()
                os.environ.update(before)
            self.assertNotEqual(first.config_sha256, second.config_sha256)
            self.assertEqual(first.source_tree_sha256, SOURCE_SHA)

    def test_nonfinite_value_is_rejected_in_args_and_canonical_config(self) -> None:
        for value in ("nan", "inf", "-inf"):
            with self.subTest(value=value), self.assertRaises(Exception):
                _positive_float(value)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = root / "config.json"
            config.write_text('{"unknown":{"value":NaN}}\n', encoding="utf-8")
            with patch("alice.service.source_tree_sha256", return_value=SOURCE_SHA):
                with self.assertRaisesRegex(ServiceError, "canonical finite JSON"):
                    resolve_runtime_identity(
                        config=config,
                        root=root,
                        source_root=Path(__file__).resolve().parents[1],
                        environment=sanitized_environment({}),
                    )

    def test_execution_snapshot_seals_exact_source_and_resolved_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory).resolve()
            source = repository / "source"
            runtime = repository / "runtime"
            source.mkdir()
            tracked = source / "a.py"
            tracked.write_text("PINNED = 1\n", encoding="utf-8")
            config = repository / "operator.json"
            config.write_text("{}\n", encoding="utf-8")
            self._git(repository, "init", "-q")
            self._git(repository, "config", "user.email", "alice@example.invalid")
            self._git(repository, "config", "user.name", "Alice Test")
            self._git(repository, "add", "source")
            self._git(repository, "commit", "-qm", "fixture")

            snapshot, identity = materialize_execution_snapshot(
                config=config,
                root=runtime,
                source_root=source,
                environment=sanitized_environment({}),
            )
            self.assertEqual(
                (snapshot.root / "a.py").read_text(encoding="utf-8"),
                "PINNED = 1\n",
            )
            self.assertEqual(stat.S_IMODE(snapshot.root.stat().st_mode), 0o500)
            verify_execution_snapshot(
                snapshot, root=runtime, expected_identity=identity
            )

            tracked.write_text("PINNED = 2\n", encoding="utf-8")
            config.write_text('{"runtime":{"effect_mode":"live"}}\n', encoding="utf-8")
            # Mutable input drift is fatal to a new identity check but cannot
            # alter the already-sealed bytes a tick executes.
            verify_execution_snapshot(
                snapshot, root=runtime, expected_identity=identity
            )
            with self.assertRaisesRegex(ServiceError, "not clean"):
                resolve_runtime_identity(
                    config=config,
                    root=runtime,
                    source_root=source,
                    environment=sanitized_environment({}),
                )


class HealthAndRunnerTests(unittest.TestCase):
    def test_health_is_atomic_owner_only_strict_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "service" / "health.json").resolve()
            store = HealthStore(path)
            secret = "never-persist-this"
            store.write(health_state(message_hash=message_hash(secret)))
            store.write(health_state(heartbeat_at="2026-08-22T12:00:20.000Z"))
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn(secret, raw)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(list(path.parent.glob(".health.json.*.tmp")), [])
            self.assertEqual(store.read().identity, IDENTITY)
            payload = json.loads(raw)
            payload["raw_message"] = secret
            path.write_text(json.dumps(payload), encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaisesRegex(ServiceError, "unexpected or missing"):
                store.read()

    def test_health_and_lock_reject_nonprivate_runtime_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve() / "service"
            parent.mkdir(mode=0o755)
            parent.chmod(0o755)
            with self.assertRaisesRegex(ServiceError, "owner-only directory"):
                HealthStore(parent / "health.json").write(health_state())
            with self.assertRaisesRegex(ServiceError, "owner-only directory"):
                WorkerLock(parent / "worker.lock").acquire()

    def test_probe_detects_stale_failure_overlong_and_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = HealthStore((Path(directory) / "health.json").resolve())
            store.write(
                health_state(
                    heartbeat_at="2026-08-22T11:50:00.000Z",
                    tick_started_at="2026-08-22T11:40:00.000Z",
                    consecutive_failures=3,
                )
            )
            other = RuntimeIdentity("d" * 64, CONFIG_SHA, POLICY_HASH, "draft")
            result = probe_health(
                store,
                stale_seconds=60,
                max_consecutive_failures=3,
                max_tick_seconds=300,
                expected_identity=other,
                now=BASE_TIME,
            )
            self.assertEqual(
                set(result.problems),
                {"stale_heartbeat", "repeated_failures", "overlong_tick", "identity_mismatch"},
            )

    def test_post_start_proof_accepts_a_long_active_first_tick(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            store = HealthStore(root / "health.json")
            state = health_state(
                started_at="2026-08-22T12:00:00.000Z",
                heartbeat_at="2026-08-22T12:09:55.000Z",
                success_at=None,
                tick_started_at="2026-08-22T12:00:01.000Z",
                consecutive_failures=3,
            )
            store.write(state)
            result = probe_health(
                store,
                stale_seconds=90,
                max_consecutive_failures=3,
                max_tick_seconds=3600,
                expected_identity=IDENTITY,
                now=BASE_TIME + timedelta(seconds=600),
            )
            self.assertTrue(result.ok)
            receipt = root / "watchdog-health.json"
            watchdog.write_receipt(
                receipt,
                expected=IDENTITY.to_dict(),
                healthy=True,
                action="none",
                digest=message_hash("healthy"),
                now=BASE_TIME + timedelta(seconds=595),
            )
            self.assertTrue(
                post_start_health_ok(
                    result,
                    expected_identity=IDENTITY,
                    watchdog_state=receipt,
                    started_after_epoch=BASE_TIME.timestamp(),
                    maximum_age_seconds=90,
                    now=BASE_TIME + timedelta(seconds=600),
                )
            )
            store.write(
                health_state(
                    started_at="2026-08-22T12:00:00.000Z",
                    heartbeat_at="2026-08-22T12:09:55.000Z",
                    success_at=None,
                    tick_started_at=None,
                    consecutive_failures=0,
                )
            )
            not_started = probe_health(
                store,
                stale_seconds=90,
                max_consecutive_failures=3,
                max_tick_seconds=3600,
                expected_identity=IDENTITY,
                now=BASE_TIME + timedelta(seconds=600),
            )
            self.assertFalse(
                post_start_health_ok(
                    not_started,
                    expected_identity=IDENTITY,
                    watchdog_state=receipt,
                    started_after_epoch=BASE_TIME.timestamp(),
                    maximum_age_seconds=90,
                    now=BASE_TIME + timedelta(seconds=600),
                )
            )
            receipt.unlink()
            self.assertFalse(
                post_start_health_ok(
                    result,
                    expected_identity=IDENTITY,
                    watchdog_state=receipt,
                    started_after_epoch=BASE_TIME.timestamp(),
                    maximum_age_seconds=90,
                    now=BASE_TIME + timedelta(seconds=85),
                )
            )

    def test_second_worker_lock_is_nonblocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "worker.lock").resolve()
            first = WorkerLock(path)
            second = WorkerLock(path)
            first.acquire()
            try:
                with self.assertRaises(WorkerAlreadyRunning):
                    second.acquire()
            finally:
                first.release()
            second.acquire()
            second.release()

    def test_failure_accounting_and_success_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outcomes = iter([process_result(3), process_result(1), process_result(0)])
            store = HealthStore((Path(directory) / "health.json").resolve())
            runner = ServiceRunner(
                health_store=store,
                expected_identity=IDENTITY,
                identity_resolver=lambda: IDENTITY,
                tick_executor=lambda _stop, _progress: next(outcomes),
                clock=MutableClock(),
            )
            self.assertFalse(runner.run_tick().ok)
            self.assertFalse(runner.run_tick().ok)
            self.assertEqual(store.read().consecutive_failures, 2)
            self.assertTrue(runner.run_tick().ok)
            self.assertEqual(store.read().consecutive_failures, 0)

    def test_progress_heartbeat_keeps_tick_started_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = HealthStore((Path(directory) / "health.json").resolve())
            observed: list[HealthState] = []

            def execute(_stop, progress):
                progress()
                observed.append(store.read())
                progress()
                observed.append(store.read())
                return process_result(0)

            runner = ServiceRunner(
                health_store=store,
                expected_identity=IDENTITY,
                identity_resolver=lambda: IDENTITY,
                tick_executor=execute,
                clock=MutableClock(),
            )
            self.assertTrue(runner.run_tick().ok)
            self.assertTrue(all(state.tick_started_at for state in observed))
            self.assertLess(observed[0].heartbeat_at, observed[1].heartbeat_at)

    def test_source_or_config_mutation_before_or_after_tick_is_fatal(self) -> None:
        changed = RuntimeIdentity("d" * 64, CONFIG_SHA, POLICY_HASH, "draft")
        for identities, expected_calls in (
            ([IDENTITY, changed], 0),
            ([IDENTITY, IDENTITY, changed], 1),
        ):
            with self.subTest(stage=len(identities)), tempfile.TemporaryDirectory() as directory:
                sequence = iter(identities)
                calls = 0

                def execute(_stop, _progress):
                    nonlocal calls
                    calls += 1
                    return process_result(0)

                runner = ServiceRunner(
                    health_store=HealthStore((Path(directory) / "health.json").resolve()),
                    expected_identity=IDENTITY,
                    identity_resolver=lambda: next(sequence),
                    tick_executor=execute,
                    clock=MutableClock(),
                )
                result = runner.run_tick()
                self.assertTrue(result.fatal)
                self.assertEqual(result.exit_code, 78)
                self.assertEqual(calls, expected_calls)


class WatchdogTests(unittest.TestCase):
    def test_watchdog_recovers_exact_launchd_label_and_never_uses_health_pid(self) -> None:
        calls: list[list[str]] = []

        def command(argv, **_kwargs):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0)

        target = f"gui/{os.getuid()}/ai.autonomous.alice.worker"
        watchdog.recover_launchd_target(target, command=command, sleeper=lambda _seconds: None)
        self.assertEqual(
            calls,
            [
                ["/bin/launchctl", "print", target],
                ["/bin/launchctl", "kill", "SIGTERM", target],
                ["/bin/launchctl", "kickstart", "-k", target],
            ],
        )
        with self.assertRaises(watchdog.WatchdogError):
            watchdog.recover_launchd_target(
                f"gui/{os.getuid()}/unrelated.service",
                command=command,
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(len(calls), 3)

    def test_watchdog_health_and_alert_rate_are_identity_bound(self) -> None:
        health = health_state().to_dict()
        expected = IDENTITY.to_dict()
        self.assertEqual(
            watchdog.health_problems(
                health,
                expected=expected,
                stale_seconds=60,
                max_tick_seconds=300,
                max_consecutive_failures=3,
                now=BASE_TIME + timedelta(seconds=20),
            ),
            (),
        )
        changed = dict(expected)
        changed["config_sha256"] = "d" * 64
        self.assertIn(
            "identity_mismatch",
            watchdog.health_problems(
                health,
                expected=changed,
                stale_seconds=60,
                max_tick_seconds=300,
                max_consecutive_failures=3,
                now=BASE_TIME + timedelta(seconds=20),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            rate = (Path(directory) / "rate.json").resolve()
            self.assertTrue(watchdog.alert_due(rate, now_epoch=1000, interval_seconds=900))
            watchdog.mark_alert(rate, now_epoch=1000, digest="e" * 64)
            self.assertFalse(watchdog.alert_due(rate, now_epoch=1500, interval_seconds=900))
            self.assertTrue(watchdog.alert_due(rate, now_epoch=1900, interval_seconds=900))
            self.assertEqual(stat.S_IMODE(rate.stat().st_mode), 0o600)
            script = Path(directory) / "watchdog.py"
            script.write_text("# installed\n", encoding="utf-8")
            installed_at = script.stat().st_mtime
            self.assertTrue(
                watchdog.in_startup_grace(
                    script, now_epoch=installed_at + 30, grace_seconds=120
                )
            )
            self.assertFalse(
                watchdog.in_startup_grace(
                    script, now_epoch=installed_at + 121, grace_seconds=120
                )
            )

    def test_watchdog_allows_a_fresh_bounded_recovery_tick(self) -> None:
        health = health_state(
            heartbeat_at="2026-08-22T12:01:20.000Z",
            success_at=None,
            tick_started_at="2026-08-22T12:00:01.000Z",
            consecutive_failures=3,
        ).to_dict()
        self.assertEqual(
            watchdog.health_problems(
                health,
                expected=IDENTITY.to_dict(),
                stale_seconds=90,
                max_tick_seconds=600,
                max_consecutive_failures=3,
                now=BASE_TIME + timedelta(seconds=85),
            ),
            (),
        )
        stale = watchdog.health_problems(
            health,
            expected=IDENTITY.to_dict(),
            stale_seconds=30,
            max_tick_seconds=600,
            max_consecutive_failures=3,
            now=BASE_TIME + timedelta(seconds=120),
        )
        self.assertEqual(set(stale), {"stale_heartbeat", "repeated_failures"})
        health["heartbeat_at"] = "2026-08-22T12:11:00.000Z"
        overlong = watchdog.health_problems(
            health,
            expected=IDENTITY.to_dict(),
            stale_seconds=90,
            max_tick_seconds=600,
            max_consecutive_failures=3,
            now=BASE_TIME + timedelta(seconds=660),
        )
        self.assertEqual(set(overlong), {"overlong_tick", "repeated_failures"})

    def test_watchdog_writes_fresh_identity_bound_owner_only_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            receipt = root / "watchdog-health.json"
            watchdog.write_receipt(
                receipt,
                expected=IDENTITY.to_dict(),
                healthy=True,
                action="none",
                digest=message_hash("healthy"),
                now=BASE_TIME,
            )
            self.assertEqual(stat.S_IMODE(receipt.stat().st_mode), 0o600)
            self.assertTrue(
                watchdog_receipt_ok(
                    receipt,
                    expected_identity=IDENTITY,
                    not_before_epoch=BASE_TIME.timestamp() - 1,
                    maximum_age_seconds=60,
                    now=BASE_TIME + timedelta(seconds=10),
                )
            )
            self.assertFalse(
                watchdog_receipt_ok(
                    receipt,
                    expected_identity=RuntimeIdentity(
                        "d" * 64, CONFIG_SHA, POLICY_HASH, "draft"
                    ),
                )
            )

            health = root / "health.json"
            HealthStore(health).write(
                health_state(heartbeat_at=datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ).replace("+00:00", "Z"))
            )
            env_file = root / "alice.env"
            env_file.write_text("", encoding="utf-8")
            env_file.chmod(0o600)
            self.assertEqual(
                watchdog.main(
                    [
                        "--state",
                        str(health),
                        "--env-file",
                        str(env_file),
                        "--rate-state",
                        str(root / "alert-rate.json"),
                        "--watchdog-state",
                        str(receipt),
                        "--launchd-target",
                        f"gui/{os.getuid()}/ai.autonomous.alice.worker",
                        "--expected-source-tree-sha256",
                        SOURCE_SHA,
                        "--expected-config-sha256",
                        CONFIG_SHA,
                        "--expected-policy-hash",
                        POLICY_HASH,
                        "--expected-effect-mode",
                        "draft",
                    ]
                ),
                0,
            )

    def test_webhook_requires_clean_https_and_does_not_put_token_in_payload(self) -> None:
        captured = {}

        class Response:
            def read(self, _limit):
                return b"ok"

            def close(self):
                return None

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return Response()

        secret = "webhook-bearer-secret"
        self.assertTrue(
            watchdog.send_webhook(
                {
                    "ALICE_ALERT_WEBHOOK_URL": "https://alerts.example.invalid/alice",
                    "ALICE_ALERT_BEARER_TOKEN": secret,
                },
                {"service": "alice", "message_hash": "f" * 64},
                opener=opener,
            )
        )
        self.assertNotIn(secret, captured["request"].data.decode())
        with self.assertRaises(watchdog.WatchdogError):
            watchdog.send_webhook(
                {"ALICE_ALERT_WEBHOOK_URL": "http://alerts.example.invalid/alice"},
                {"service": "alice"},
                opener=opener,
            )


class LaunchdArtifactTests(unittest.TestCase):
    def test_rendered_jobs_pin_identity_use_independent_watchdog_and_suppress_logs(self) -> None:
        alice_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            worker = root / "worker.plist"
            watcher = root / "watchdog.plist"
            render_plists(
                worker_template=alice_root / "ops" / "ai.autonomous.alice.worker.plist.in",
                watchdog_template=alice_root / "ops" / "ai.autonomous.alice.watchdog.plist.in",
                worker_output=worker,
                watchdog_output=watcher,
                python=Path(sys.executable).resolve(),
                watchdog_script=root / "watchdog.py",
                watchdog_python=Path("/usr/bin/python3"),
                config=root / "config.json",
                env_file=root / "alice.env",
                root=root,
                state=root / "health.json",
                lock=root / "worker.lock",
                rate_state=root / "alert-rate.json",
                watchdog_state=root / "watchdog-health.json",
                source_root=alice_root,
                identity=IDENTITY,
                poll_seconds=30,
                stale_seconds=300,
                max_tick_seconds=1800,
                term_grace_seconds=10,
                max_consecutive_failures=3,
                watchdog_interval=60,
                alert_interval_seconds=900,
                startup_grace_seconds=120,
                launchd_target=f"gui/{os.getuid()}/ai.autonomous.alice.worker",
            )
            worker_text = worker.read_text(encoding="utf-8")
            watcher_text = watcher.read_text(encoding="utf-8")
            combined = worker_text + watcher_text
            self.assertNotRegex(combined, r"__[A-Z0-9_]+__")
            self.assertIn(SOURCE_SHA, combined)
            self.assertIn(CONFIG_SHA, combined)
            self.assertIn(POLICY_HASH, combined)
            self.assertIn(str(root / "watchdog.py"), watcher_text)
            self.assertIn("/usr/bin/python3", watcher_text)
            self.assertIn(str(root / "watchdog-health.json"), watcher_text)
            self.assertIn("--heartbeat-seconds", worker_text)
            self.assertIn("<key>AbandonProcessGroup</key>", worker_text)
            self.assertIn("<string>-I</string>", worker_text)
            self.assertNotIn("<string>-m</string>", worker_text)
            self.assertIn("/var/service/releases/", worker_text)
            self.assertNotIn("alice.service</string>\n    <string>probe", watcher_text)
            self.assertGreaterEqual(combined.count("<string>/dev/null</string>"), 4)

    def test_install_script_has_post_start_health_verification_and_rollback(self) -> None:
        install = (Path(__file__).resolve().parents[1] / "ops" / "install.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("wait-healthy", install)
        self.assertIn("--watchdog-state", install)
        self.assertIn("/usr/bin/python3", install)
        self.assertIn("launchctl print \"$WORKER_TARGET\"", install)
        self.assertIn("launchctl print \"$WATCHDOG_TARGET\"", install)
        self.assertIn("trap 'rollback 143' TERM", install)
        self.assertIn("prior jobs were restored", install)
        self.assertIn("runtime state was retained", install)

    @unittest.skipUnless(Path("/bin/zsh").exists(), "macOS installer behavior")
    def test_failed_post_start_health_check_rolls_back_jobs_but_keeps_runtime(self) -> None:
        alice_root = Path(__file__).resolve().parents[1]
        installer = alice_root / "ops" / "install.sh"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fake_bin = root / "bin"
            fake_bin.mkdir()
            launch_state = root / "launch-state"
            launch_state.mkdir()
            launch_log = root / "launch.log"
            home = root / "home"
            home.mkdir()
            config = root / "config.json"
            config.write_text("{}\n", encoding="utf-8")
            env_file = root / "alice.env"
            secret = "installer-secret-must-not-echo"
            env_file.write_text(f"ALICE_FACTORY_TOKEN={secret}\n", encoding="utf-8")
            env_file.chmod(0o600)
            runtime_service = root / "runtime" / "var" / "service"
            runtime_service.mkdir(parents=True)
            durable_sentinel = runtime_service / "durable-state.sentinel"
            durable_sentinel.write_text("retain\n", encoding="utf-8")

            fake_python = fake_bin / "python"
            fake_python.write_text(
                "#!/bin/zsh\n"
                "if [[ \"${1:-}\" == '-c' ]]; then exit 0; fi\n"
                "if [[ \"${1:-}\" == '-m' && \"${2:-}\" == 'alice.service' ]]; then\n"
                "  command=\"${3:-}\"; shift 3\n"
                "  if [[ \"$command\" == 'render-plists' ]]; then\n"
                "    worker=''; watcher=''\n"
                "    while (( $# > 0 )); do\n"
                "      case \"$1\" in\n"
                "        --worker-output) worker=\"$2\"; shift 2;;\n"
                "        --watchdog-output) watcher=\"$2\"; shift 2;;\n"
                "        *) shift;;\n"
                "      esac\n"
                "    done\n"
                "    print '<plist/>' > \"$worker\"; print '<plist/>' > \"$watcher\"; exit 0\n"
                "  fi\n"
                "  [[ \"$command\" == 'wait-healthy' ]] && exit 2\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            (fake_bin / "git").write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")
            (fake_bin / "plutil").write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")
            for command in (fake_bin / "git", fake_bin / "plutil"):
                command.chmod(0o755)
            launchctl = fake_bin / "launchctl"
            launchctl.write_text(
                "#!/bin/zsh\n"
                "print -r -- \"$*\" >> \"$FAKE_LAUNCH_LOG\"\n"
                "case \"${1:-}\" in\n"
                "  print)\n"
                "    [[ \"$2\" == *watchdog* ]] && marker=watchdog || marker=worker\n"
                "    [[ -f \"$FAKE_LAUNCH_STATE/$marker\" ]] && exit 0 || exit 1;;\n"
                "  bootstrap)\n"
                "    [[ \"$3\" == *watchdog* ]] && marker=watchdog || marker=worker\n"
                "    : > \"$FAKE_LAUNCH_STATE/$marker\"; exit 0;;\n"
                "  bootout)\n"
                "    [[ \"$2\" == *watchdog* ]] && marker=watchdog || marker=worker\n"
                "    rm -f \"$FAKE_LAUNCH_STATE/$marker\"; exit 0;;\n"
                "  enable|kickstart) exit 0;;\n"
                "esac\n"
                "exit 1\n",
                encoding="utf-8",
            )
            launchctl.chmod(0o755)
            environment = {
                "PATH": f"{fake_bin}:/usr/bin:/bin",
                "HOME": str(home),
                "TMPDIR": str(root),
                "FAKE_LAUNCH_LOG": str(launch_log),
                "FAKE_LAUNCH_STATE": str(launch_state),
                "ALICE_SERVICE_OFFLINE_TEST": "1",
            }

            result = subprocess.run(
                [
                    "/bin/zsh",
                    str(installer),
                    "--config",
                    str(config),
                    "--env-file",
                    str(env_file),
                    "--root",
                    str(root / "runtime"),
                    "--python",
                    str(fake_python),
                    "--offline-test-tool-dir",
                    str(fake_bin),
                ],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(secret, result.stdout + result.stderr)
            agents = home / "Library" / "LaunchAgents"
            self.assertFalse((agents / "ai.autonomous.alice.worker.plist").exists())
            self.assertFalse((agents / "ai.autonomous.alice.watchdog.plist").exists())
            self.assertTrue(durable_sentinel.exists())
            self.assertFalse((runtime_service / "watchdog.py").exists())
            log = launch_log.read_text(encoding="utf-8")
            self.assertIn("bootstrap", log)
            self.assertIn("bootout", log)
            self.assertFalse((launch_state / "worker").exists())
            self.assertFalse((launch_state / "watchdog").exists())

    @unittest.skipUnless(Path("/bin/zsh").exists(), "macOS launchd script behavior")
    def test_status_and_uninstall_refuse_false_success(self) -> None:
        alice_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fake_bin = root / "bin"
            fake_bin.mkdir()
            home = root / "home"
            home.mkdir()
            python = fake_bin / "python"
            python.write_text("#!/bin/zsh\nexit 0\n", encoding="utf-8")
            python.chmod(0o755)
            launchctl = fake_bin / "launchctl"
            launchctl.write_text(
                "#!/bin/zsh\n"
                "[[ \"${1:-}\" == 'print' ]] && exit ${FAKE_PRINT_CODE:-1}\n"
                "exit 0\n",
                encoding="utf-8",
            )
            launchctl.chmod(0o755)
            config = root / "config.json"
            config.write_text("{}\n", encoding="utf-8")
            env_file = root / "alice.env"
            env_file.write_text("", encoding="utf-8")
            env_file.chmod(0o600)
            environment = {
                "PATH": f"{fake_bin}:/usr/bin:/bin",
                "HOME": str(home),
                "FAKE_PRINT_CODE": "1",
                "ALICE_SERVICE_OFFLINE_TEST": "1",
                "ALICE_SERVICE_OFFLINE_TOOL_DIR": str(fake_bin),
            }
            status = subprocess.run(
                [
                    "/bin/zsh",
                    str(alice_root / "ops" / "status.sh"),
                    "--config",
                    str(config),
                    "--env-file",
                    str(env_file),
                    "--root",
                    str(root),
                    "--python",
                    str(python),
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status.returncode, 2)
            self.assertIn("not loaded", status.stderr)

            # A lying bootout that leaves the label visible must not be reported
            # as a successful uninstall.
            environment["FAKE_PRINT_CODE"] = "0"
            uninstall = subprocess.run(
                ["/bin/zsh", str(alice_root / "ops" / "uninstall.sh")],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(uninstall.returncode, 2)
            self.assertIn("still loaded", uninstall.stderr)


if __name__ == "__main__":
    unittest.main()
